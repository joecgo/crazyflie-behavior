"""The Crazyflie adapter's connect(), against a fake cflib.

pytest's monkeypatch swaps the adapter's cflib classes for fakes for one test,
then puts the real ones back.
"""

# pyright: reportPrivateUsage=false

import copy
import logging
import math
import signal
import threading
import time
from collections.abc import Callable, Generator
from typing import cast
from unittest.mock import MagicMock

import pytest

from crazyflie_behavior.drone.crazyflie import adapter as adapter_module
from crazyflie_behavior.drone.crazyflie.adapter import CrazyflieAdapter
from crazyflie_behavior.drone.crazyflie.bad_flow_zone import MAX_FINAL_DESCENT_HEIGHT
from crazyflie_behavior.drone.crazyflie.time_limit import WAIT_SLICE
from crazyflie_behavior.drone.interface import FLOOR_MAX_SPEED
from crazyflie_behavior.geometry import Vector3
from crazyflie_behavior.snapshot import RangeStatus
from crazyflie_behavior.timing.clock import RealClock, SimClock

FIRST_SAMPLES: dict[str, dict[str, float]] = {
    "state": {
        "stateEstimate.x": 0.0,
        "stateEstimate.y": 0.0,
        "stateEstimate.z": 0.0,
        "stateEstimate.vx": 0.0,
        "stateEstimate.vy": 0.0,
        "stateEstimate.vz": 0.0,
        "supervisor.info": 0.0,
    },
    "battery": {"pm.vbat": 4.0},
    "down": {"range.zrange": 20.0, "kalman.varPX": 1e-4, "kalman.varPY": 1e-4},
    "diagnostic": {
        "stateEstimate.roll": 0.0,
        "stateEstimate.pitch": 0.0,
        "stateEstimate.yaw": 0.0,
        "motor.m1": 0.0,
        "motor.m2": 0.0,
        "motor.m3": 0.0,
        "motor.m4": 0.0,
        "motion.squal": 80.0,
        "motion.shutter": 3000.0,
        "pm.vbatMV": 4000.0,
    },
    "multiranger": {
        "range.front": 8000.0,
        "range.back": 8000.0,
        "range.left": 8000.0,
        "range.right": 8000.0,
        "range.up": 8000.0,
    },
}
"""Each log block's first sample, as cflib delivers it."""


class FakeCflib:
    """Stands in for cflib during connect(): records what the adapter asked for.

    Each log block sends one sample when it starts, like a drone's first
    packet: at once, after `first_sample_delay` seconds, or never for blocks
    in `silent_blocks`. A real drone keeps streaming, and connect() relies on
    that after it swaps the telemetry buffer (ADR-0038): `stream_samples()`
    sends every started block's sample again, and with a delay the blocks keep
    streaming on a thread.
    """

    def __init__(self) -> None:
        self.link = MagicMock()
        """The SyncCrazyflie: open_link, close_link, and the Crazyflie as .cf."""
        self.radio_link = self.link.cf.link
        """The Crazyflie's radio link: closing it is what a safe link close does (ADR-0038)."""
        self.parameters = {"deck.bcFlow2": "1", "deck.bcMultiranger": "0"}
        """Parameter values as cflib returns them (strings). Missing means the
        firmware doesn't know the parameter, so cflib raises KeyError."""
        self.link.cf.param.get_value.side_effect = self.get_parameter
        self.events: list[str] = []
        """What happened, in order: "start <block>" and "reset estimate"."""
        self.link.cf.param.set_value.side_effect = self._record_a_parameter_write
        self.reset_estimate_error: BaseException | None = None
        """Raised by the estimate reset's parameter write, when set."""
        self.on_reset_estimate: Callable[[], None] | None = None
        """Called by the estimate reset's parameter write, when set: what the drone does then."""
        self.thrust_base_error: BaseException | None = None
        """Raised by the thrust base's parameter write, when set."""
        self.reports_written_values = True
        """Whether the drone reports each written value back, as it does when a write arrives."""
        self.parameter_callbacks: dict[str, list[Callable[[str, str], None]]] = {}
        """Update callbacks by parameter name, called with each value the drone reports, as text."""
        self.link.cf.param.add_update_callback.side_effect = self._add_parameter_callback
        self.samples = copy.deepcopy(FIRST_SAMPLES)
        """Each block's sample. A test can change one before it's sent."""
        self.log_block_names: list[str] = []
        self.log_block_periods_ms: dict[str, int] = {}
        self.silent_blocks: set[str] = set()
        self.first_sample_delay = 0.0
        """Seconds; above zero, the blocks stream from a thread after this delay."""
        self._started_blocks: dict[str, tuple[MagicMock, list[Callable[[int, dict[str, float], object], None]]]] = {}
        self._stopped = threading.Event()

    def get_parameter(self, name: str) -> str:
        return self.parameters[name]

    @property
    def reset_count(self) -> int:
        return self.events.count("reset estimate")

    def report_parameter(self, name: str, value: str) -> None:
        """The drone reports a parameter's value."""
        for callback in self.parameter_callbacks.get(name, []):
            callback(name, value)

    def _add_parameter_callback(self, group: str, name: str, cb: Callable[[str, str], None]) -> None:
        self.parameter_callbacks.setdefault(f"{group}.{name}", []).append(cb)

    def _record_a_parameter_write(self, name: str, value: object) -> None:
        if name == "kalman.resetEstimation":
            if self.reset_estimate_error is not None:
                raise self.reset_estimate_error
            assert value == 1
            self.events.append("reset estimate")
            if self.on_reset_estimate is not None:
                self.on_reset_estimate()
        elif name == "posCtlPid.thrustBase":
            if self.thrust_base_error is not None:
                raise self.thrust_base_error
            self.events.append(f"write thrust base {value}")
        if self.reports_written_values:
            self.report_parameter(name, str(value))

    def make_log_block(self, name: str, period_in_ms: int) -> MagicMock:
        self.log_block_names.append(name)
        self.log_block_periods_ms[name] = period_in_ms
        block = MagicMock()
        callbacks: list[Callable[[int, dict[str, float], object], None]] = []
        block.data_received_cb.add_callback.side_effect = callbacks.append
        block.start.side_effect = lambda: self._start_block(name, block, callbacks)
        block.stop.side_effect = lambda: self._started_blocks.pop(name, None)
        return block

    def stream_samples(self) -> None:
        """Send every started block's sample again, as a streaming drone does."""
        for name in list(self._started_blocks):
            self._send(name)

    def stop(self) -> None:
        self._stopped.set()

    def _send(self, name: str) -> None:
        block, callbacks = self._started_blocks[name]
        for callback in callbacks:
            callback(1000, self.samples[name], block)

    def _start_block(
        self,
        name: str,
        block: MagicMock,
        callbacks: list[Callable[[int, dict[str, float], object], None]],
    ) -> None:
        self.events.append(f"start {name}")
        if name in self.silent_blocks:
            return
        self._started_blocks[name] = (block, callbacks)
        if self.first_sample_delay > 0.0:

            def stream_after_the_delay() -> None:
                self._stopped.wait(self.first_sample_delay)
                while not self._stopped.is_set():
                    self._send(name)
                    self._stopped.wait(0.02)

            threading.Thread(target=stream_after_the_delay, daemon=True).start()
        else:
            self._send(name)


class StreamingSimClock(SimClock):
    """A sim clock that has the fake drone stream whenever the adapter waits, as a real drone would."""

    def __init__(self, fake_cflib: FakeCflib, start: float) -> None:
        super().__init__(start)
        self._fake_cflib = fake_cflib

    def sleep_until(self, deadline: float) -> None:
        self._fake_cflib.stream_samples()
        super().sleep_until(deadline)


@pytest.fixture
def fake_cflib(monkeypatch: pytest.MonkeyPatch) -> Generator[FakeCflib]:
    fake = FakeCflib()
    monkeypatch.setattr(adapter_module, "_drivers_initialized", True)
    monkeypatch.setattr(adapter_module, "SyncCrazyflie", MagicMock(return_value=fake.link))
    monkeypatch.setattr(adapter_module, "Crazyflie", MagicMock())
    monkeypatch.setattr(adapter_module, "LogConfig", fake.make_log_block)
    yield fake
    fake.stop()  # ends the streaming threads


def assert_only_the_radio_link_closed(fake_cflib: FakeCflib) -> None:
    """The drone may be flying, so no zero-thrust setpoint (cflib's close_link sends it) (ADR-0038)."""
    fake_cflib.radio_link.close.assert_called_once()
    fake_cflib.link.close_link.assert_not_called()
    fake_cflib.link.cf.close_link.assert_not_called()
    fake_cflib.link.cf.commander.send_setpoint.assert_not_called()


@pytest.fixture
def adapter(fake_cflib: FakeCflib) -> CrazyflieAdapter:
    return CrazyflieAdapter(StreamingSimClock(fake_cflib, start=10.0))


def test_connecting_resets_the_estimate_and_starts_telemetry(adapter: CrazyflieAdapter, fake_cflib: FakeCflib) -> None:
    adapter.connect()

    assert fake_cflib.reset_count == 1
    assert fake_cflib.log_block_names == ["state", "battery", "down", "diagnostic"]
    fake_cflib.link.close_link.assert_not_called()


def test_connecting_logs_that_the_drone_arms_itself(
    adapter: CrazyflieAdapter,
    fake_cflib: FakeCflib,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_cflib.samples["state"]["supervisor.info"] = float(1 << adapter_module.BIT_IS_AUTO_ARMED)

    with caplog.at_level(logging.INFO, logger=adapter_module.logger.name):
        adapter.connect()

    assert [r.getMessage() for r in caplog.records if "arms itself" in r.getMessage()] == [
        "The drone arms itself (auto-arming is on): a disarm won't last."
    ]


def test_connecting_logs_that_the_drone_does_not_arm_itself(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO, logger=adapter_module.logger.name):
        adapter.connect()

    assert [r.getMessage() for r in caplog.records if "arm itself" in r.getMessage()] == [
        "The drone doesn't arm itself: it needs an arm request before it can fly."
    ]


def buzzer_deck_logs(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [r.getMessage() for r in caplog.records if "Buzzer deck" in r.getMessage()]


def test_connecting_logs_a_buzzer_deck(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib, caplog: pytest.LogCaptureFixture
) -> None:
    fake_cflib.parameters["deck.bcBuzzer"] = "1"

    with caplog.at_level(logging.INFO, logger=adapter_module.logger.name):
        adapter.connect()

    assert buzzer_deck_logs(caplog) == ["Buzzer deck detected."]


@pytest.mark.parametrize("deck_parameter", ["0", None], ids=["not attached", "unknown to the firmware"])
def test_connecting_without_a_buzzer_deck_logs_that_buzzer_commands_make_no_sound(
    deck_parameter: str | None, adapter: CrazyflieAdapter, fake_cflib: FakeCflib, caplog: pytest.LogCaptureFixture
) -> None:
    """Flying doesn't need the buzzer, so the connect goes on (ADR-0053)."""
    if deck_parameter is not None:
        fake_cflib.parameters["deck.bcBuzzer"] = deck_parameter

    with caplog.at_level(logging.INFO, logger=adapter_module.logger.name):
        adapter.connect()

    assert buzzer_deck_logs(caplog) == ["No Buzzer deck: buzzer commands will make no sound."]
    fake_cflib.link.close_link.assert_not_called()


def test_connecting_again_warns_again_about_a_buzzer_command_on_a_closed_link(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib, caplog: pytest.LogCaptureFixture
) -> None:
    """The once-per-streak warning starts over with each connection."""
    caplog.set_level(logging.WARNING, logger=adapter_module.logger.name)
    adapter.connect()
    fake_cflib.link.cf.link = None  # the link is lost
    adapter.chirp()
    fake_cflib.link.cf.link = fake_cflib.radio_link
    adapter.connect()
    fake_cflib.link.cf.link = None  # and lost again before any buzzer command

    adapter.chirp()

    assert [r.getMessage() for r in caplog.records if "Buzzer command" in r.getMessage()] == [
        "Buzzer command not sent: the link is closed. Warned once per streak."
    ] * 2


def test_a_multi_ranger_adds_its_own_log_block(adapter: CrazyflieAdapter, fake_cflib: FakeCflib) -> None:
    fake_cflib.parameters["deck.bcMultiranger"] = "1"

    adapter.connect()

    assert "multiranger" in fake_cflib.log_block_names


def test_connect_does_not_wait_for_the_diagnostic_block(adapter: CrazyflieAdapter, fake_cflib: FakeCflib) -> None:
    # It's for the debug log only, not telemetry (ADR-0050).
    fake_cflib.silent_blocks.add("diagnostic")

    adapter.connect()

    assert adapter._telemetry.missing_values() == []
    assert fake_cflib.log_block_periods_ms["diagnostic"] == 100


def test_the_diagnostic_block_carries_the_battery_voltage(adapter: CrazyflieAdapter, fake_cflib: FakeCflib) -> None:
    """10 times a second, for the debug log only (ADR-0053)."""
    adapter.connect()

    diagnostic_block = adapter._log_configs[fake_cflib.log_block_names.index("diagnostic")]
    add_variable = cast(MagicMock, cast(MagicMock, diagnostic_block).add_variable)
    variables: list[str] = [added.args[0] for added in add_variable.call_args_list]
    assert "pm.vbatMV" in variables


def test_log_periods_are_ones_the_firmware_accepts(adapter: CrazyflieAdapter, fake_cflib: FakeCflib) -> None:
    fake_cflib.parameters["deck.bcMultiranger"] = "1"

    adapter.connect()

    for period_ms in fake_cflib.log_block_periods_ms.values():
        assert 10 <= period_ms <= 2540  # the firmware counts periods in 10 ms steps
        assert period_ms % 10 == 0
    # The firmware reads the Multi-ranger every 100 ms (ADR-0022); faster only repeats.
    assert fake_cflib.log_block_periods_ms["multiranger"] >= 100


def test_without_a_multi_ranger_its_directions_read_invalid_never_clear(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib
) -> None:
    adapter.connect()

    readings = adapter._telemetry.snapshot(0.0, is_in_initial_climb=False, may_be_flying=False).range_readings
    for reading in (readings.front, readings.back, readings.left, readings.right, readings.up):
        assert reading is not None
        assert reading.value.status is RangeStatus.INVALID


def test_the_older_flow_deck_counts_too(adapter: CrazyflieAdapter, fake_cflib: FakeCflib) -> None:
    del fake_cflib.parameters["deck.bcFlow2"]  # firmware without the v2 parameter
    fake_cflib.parameters["deck.bcFlow"] = "1"

    adapter.connect()

    assert fake_cflib.reset_count == 1


def test_without_a_flow_deck_it_refuses_to_fly_and_closes_only_the_radio_link(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib
) -> None:
    fake_cflib.parameters["deck.bcFlow2"] = "0"

    with pytest.raises(RuntimeError, match="Flow deck"):
        adapter.connect()

    assert_only_the_radio_link_closed(fake_cflib)
    assert fake_cflib.reset_count == 0


class BlockingStep:
    """A fake cflib call that blocks like a stuck wait, until the test releases it.

    It can send the interrupt signal first: a real one arrives while cflib waits.
    """

    def __init__(self, send_interrupt_signal: bool = False) -> None:
        self.release = threading.Event()
        self._send_interrupt_signal = send_interrupt_signal

    def __call__(self, *_arguments: object) -> None:
        if self._send_interrupt_signal:
            signal.raise_signal(signal.SIGINT)
        self.release.wait(timeout=10.0)


@pytest.fixture
def blocking_step() -> Generator[BlockingStep]:
    step = BlockingStep()
    yield step
    step.release.set()  # let the abandoned helper thread finish


@pytest.fixture
def interrupt_signal_step() -> Generator[BlockingStep]:
    step = BlockingStep(send_interrupt_signal=True)
    yield step
    step.release.set()


@pytest.fixture
def short_time_limits(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("LINK_TIME_LIMIT", "PARAMETERS_TIME_LIMIT"):
        monkeypatch.setattr(adapter_module, name, 0.2)


def real_time_adapter() -> CrazyflieAdapter:
    # Time limits count on the injected clock, and a stuck step needs real time to pass.
    return CrazyflieAdapter(RealClock())


@pytest.mark.usefixtures("short_time_limits")
def test_opening_the_link_has_a_time_limit_then_stops_the_connection_under_way_without_a_setpoint(
    fake_cflib: FakeCflib, blocking_step: BlockingStep
) -> None:
    fake_cflib.link.open_link.side_effect = blocking_step

    with pytest.raises(TimeoutError, match=r"Opening the link took longer than 0\.2 s\. Check the"):
        real_time_adapter().connect()

    assert_only_the_radio_link_closed(fake_cflib)


@pytest.mark.usefixtures("short_time_limits")
def test_reading_the_parameters_has_a_time_limit_then_closes_only_the_radio_link(
    fake_cflib: FakeCflib, blocking_step: BlockingStep
) -> None:
    fake_cflib.link.wait_for_params.side_effect = blocking_step

    with pytest.raises(TimeoutError, match=r"Reading the parameters took longer than 0\.2 s"):
        real_time_adapter().connect()

    assert_only_the_radio_link_closed(fake_cflib)


def test_connecting_resets_the_estimate_without_waiting_for_it_to_settle(fake_cflib: FakeCflib) -> None:
    clock = StreamingSimClock(fake_cflib, start=10.0)
    # The velocity uncertainty never settles, as on a dark floor (ADR-0054).
    fake_cflib.samples["down"]["kalman.varPX"] = 1.0

    CrazyflieAdapter(clock).connect()

    assert fake_cflib.reset_count == 1
    assert clock.now() - 10.0 <= WAIT_SLICE  # one wait for the first telemetry after the reset, no more


def test_the_estimate_reset_logs_the_estimate_it_erases(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib, caplog: pytest.LogCaptureFixture
) -> None:
    fake_cflib.samples["state"]["stateEstimate.x"] = -87.0

    def stream_the_reset_estimate() -> None:
        fake_cflib.samples["state"]["stateEstimate.x"] = 0.0
        fake_cflib.stream_samples()

    fake_cflib.on_reset_estimate = stream_the_reset_estimate  # telemetry from after the reset, during the write

    with caplog.at_level(logging.INFO):
        adapter.connect()

    [record] = [record for record in caplog.records if record.getMessage().startswith("Estimate reset")]
    assert record.levelno == logging.INFO
    assert "position (-87.000, 0.000, 0.000) m" in record.getMessage()


@pytest.mark.parametrize(
    ("speed", "level"), [(FLOOR_MAX_SPEED * 0.99, logging.INFO), (FLOOR_MAX_SPEED, logging.WARNING)]
)
def test_the_estimate_reset_warns_unless_the_estimate_it_erases_was_under_the_floor_speed_limit(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib, caplog: pytest.LogCaptureFixture, speed: float, level: int
) -> None:
    fake_cflib.samples["state"]["stateEstimate.vy"] = speed

    with caplog.at_level(logging.INFO):
        adapter.connect()

    [record] = [record for record in caplog.records if record.getMessage().startswith("Estimate reset")]
    assert record.levelno == level
    assert ("implausible" in record.getMessage()) == (level == logging.WARNING)


def test_the_interrupt_signal_while_the_link_opens_gets_through_and_stops_the_connection_under_way(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib, interrupt_signal_step: BlockingStep
) -> None:
    fake_cflib.link.open_link.side_effect = interrupt_signal_step

    with pytest.raises(KeyboardInterrupt):
        adapter.connect()

    assert_only_the_radio_link_closed(fake_cflib)


def test_the_interrupt_signal_while_reading_the_parameters_gets_through_and_closes_only_the_radio_link(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib, interrupt_signal_step: BlockingStep
) -> None:
    fake_cflib.link.wait_for_params.side_effect = interrupt_signal_step

    with pytest.raises(KeyboardInterrupt):
        adapter.connect()

    assert_only_the_radio_link_closed(fake_cflib)


def test_a_connect_that_fails_on_its_own_is_left_to_cflib_to_close(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib
) -> None:
    fake_cflib.link.open_link.side_effect = Exception("Couldn't find a Crazyflie")

    with pytest.raises(Exception, match="Couldn't find a Crazyflie"):
        adapter.connect()

    # cflib's open_link closes the link itself before raising.
    fake_cflib.link.cf.close_link.assert_not_called()


def test_any_failing_setup_step_closes_the_link(adapter: CrazyflieAdapter, fake_cflib: FakeCflib) -> None:
    fake_cflib.reset_estimate_error = TimeoutError("parameter write failed")

    with pytest.raises(TimeoutError):
        adapter.connect()

    fake_cflib.link.close_link.assert_called_once()


def test_a_missing_log_variable_says_to_update_the_firmware(adapter: CrazyflieAdapter, fake_cflib: FakeCflib) -> None:
    fake_cflib.link.cf.log.add_config.side_effect = KeyError("Variable supervisor.info not in TOC")

    with pytest.raises(RuntimeError, match="Update the firmware"):
        adapter.connect()

    assert_only_the_radio_link_closed(fake_cflib)


def test_connect_returns_only_once_every_telemetry_value_has_arrived(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib
) -> None:
    adapter.connect()

    assert adapter._telemetry.missing_values() == []


def test_connect_waits_for_telemetry_that_arrives_late(fake_cflib: FakeCflib) -> None:
    fake_cflib.first_sample_delay = 0.3
    adapter = real_time_adapter()
    started = time.perf_counter()

    adapter.connect()

    assert adapter._telemetry.missing_values() == []
    # Noticed soon after arriving, not only when the 3 s limit ends the wait.
    assert time.perf_counter() - started < 2.0


class BoundedSimClock(StreamingSimClock):
    """A sim clock that fails the test instead of letting a broken wait loop forever."""

    MAX_SLEEPS = 1000

    def __init__(self, fake_cflib: FakeCflib, start: float) -> None:
        super().__init__(fake_cflib, start)
        self._sleeps = 0

    def sleep_until(self, deadline: float) -> None:
        self._sleeps += 1
        if self._sleeps > self.MAX_SLEEPS:
            raise AssertionError("still waiting after 1000 sleeps: the wait never ends")
        super().sleep_until(deadline)


def test_a_value_that_never_arrives_has_a_time_limit_then_closes_the_link(
    fake_cflib: FakeCflib,
) -> None:
    fake_cflib.silent_blocks.add("battery")
    adapter = CrazyflieAdapter(BoundedSimClock(fake_cflib, start=10.0))

    with pytest.raises(TimeoutError, match=r"Still missing: battery voltage\. Check"):
        adapter.connect()

    fake_cflib.link.close_link.assert_called_once()


def test_the_interrupt_signal_while_waiting_for_telemetry_gets_through_and_closes_the_link(
    fake_cflib: FakeCflib,
) -> None:
    fake_cflib.silent_blocks.add("battery")
    adapter = real_time_adapter()
    send_interrupt_signal = threading.Timer(0.2, signal.raise_signal, [signal.SIGINT])
    send_interrupt_signal.start()

    started = time.perf_counter()
    try:
        with pytest.raises(KeyboardInterrupt):
            adapter.connect()  # waits up to 3 s for the battery
        assert time.perf_counter() - started < 2.0  # at once, not when the 3 s limit ends it
    finally:
        # If connect() returned early, a later interrupt signal would stop the whole run.
        send_interrupt_signal.cancel()
        send_interrupt_signal.join()
    fake_cflib.link.close_link.assert_called_once()


def test_connecting_again_waits_for_new_telemetry_not_the_last_connections(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib
) -> None:
    adapter.connect()
    adapter.disconnect()
    fake_cflib.silent_blocks.add("battery")

    with pytest.raises(TimeoutError, match="Still missing: battery voltage"):
        adapter.connect()


def test_connecting_again_drops_a_landing_left_from_the_last_connection(fake_cflib: FakeCflib) -> None:
    clock = StreamingSimClock(fake_cflib, start=10.0)
    adapter = CrazyflieAdapter(clock)
    adapter.connect()
    adapter.take_off(0.5)
    adapter.land()  # a landing under way
    adapter._shut_down_link()  # the connection ends without finishing it, as when the landing at disconnect fails
    adapter.connect()  # a drone on the floor
    fake_cflib.link.cf.high_level_commander.reset_mock()

    clock.advance(60.0)  # long past the old landing's time limits
    adapter.update_take_off_and_landing(adapter.take_snapshot(0.05))

    # The old landing would have stopped the motors or sent a go_to to an armed drone on the floor.
    assert fake_cflib.link.cf.high_level_commander.mock_calls == []


# --- Connecting to a flying drone (ADR-0038) --------------------------------------

FLYING = float(1 << adapter_module.BIT_IS_FLYING)
"""A `supervisor.info` value whose flying bit is set."""


def test_the_state_log_block_starts_before_the_estimate_reset(adapter: CrazyflieAdapter, fake_cflib: FakeCflib) -> None:
    adapter.connect()

    assert fake_cflib.events.index("start state") < fake_cflib.events.index("reset estimate")


def test_a_flying_drone_is_refused_before_the_estimate_reset_and_without_a_zero_thrust_setpoint(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib
) -> None:
    fake_cflib.samples["state"]["supervisor.info"] = FLYING

    with pytest.raises(RuntimeError, match=r"still flying: run the rescue landing, or wait .* if it just landed"):
        adapter.connect()

    assert fake_cflib.reset_count == 0
    assert_only_the_radio_link_closed(fake_cflib)


def test_a_status_that_never_arrives_is_a_time_limit_error_that_closes_only_the_radio_link(
    fake_cflib: FakeCflib,
) -> None:
    fake_cflib.silent_blocks.add("state")
    adapter = CrazyflieAdapter(BoundedSimClock(fake_cflib, start=10.0))

    with pytest.raises(TimeoutError, match=r"Waiting for the drone's status took longer than 3 s\. Check"):
        adapter.connect()

    assert fake_cflib.reset_count == 0
    assert_only_the_radio_link_closed(fake_cflib)


def test_a_drone_on_the_floor_is_connected_and_a_later_failure_closes_the_link_normally(
    fake_cflib: FakeCflib,
) -> None:
    fake_cflib.silent_blocks.add("battery")
    adapter = CrazyflieAdapter(BoundedSimClock(fake_cflib, start=10.0))

    with pytest.raises(TimeoutError, match="Still missing: battery voltage"):
        adapter.connect()

    fake_cflib.link.close_link.assert_called_once()  # the drone is known to be on the floor


def test_telemetry_from_before_the_estimate_reset_is_not_used(adapter: CrazyflieAdapter, fake_cflib: FakeCflib) -> None:
    fake_cflib.samples["state"]["stateEstimate.x"] = 5.0  # where the drone thought it was before the reset

    def reset_the_estimate() -> None:
        fake_cflib.samples["state"]["stateEstimate.x"] = 0.0

    fake_cflib.on_reset_estimate = reset_the_estimate

    adapter.connect()

    position_estimate = adapter.take_snapshot(0.0).position_estimate
    assert position_estimate is not None
    assert position_estimate.value.x == 0.0


@pytest.fixture
def taking_over_adapter(fake_cflib: FakeCflib) -> CrazyflieAdapter:
    return CrazyflieAdapter(StreamingSimClock(fake_cflib, start=10.0), take_over_flight=True)


def test_taking_over_accepts_a_flying_drone_and_never_resets_its_estimate(
    taking_over_adapter: CrazyflieAdapter, fake_cflib: FakeCflib, caplog: pytest.LogCaptureFixture
) -> None:
    fake_cflib.samples["state"]["supervisor.info"] = FLYING

    with caplog.at_level(logging.WARNING, logger=adapter_module.logger.name):
        taking_over_adapter.connect()

    assert fake_cflib.reset_count == 0
    fake_cflib.link.close_link.assert_not_called()
    assert "Taking over the flight" in caplog.text


def test_taking_over_keeps_the_position_the_drone_already_reported(
    taking_over_adapter: CrazyflieAdapter, fake_cflib: FakeCflib
) -> None:
    fake_cflib.samples["state"]["stateEstimate.z"] = 0.4
    fake_cflib.samples["state"]["supervisor.info"] = FLYING

    taking_over_adapter.connect()

    position_estimate = taking_over_adapter._telemetry.snapshot(
        0.0, is_in_initial_climb=False, may_be_flying=False
    ).position_estimate
    assert position_estimate is not None
    assert position_estimate.value.z == pytest.approx(0.4)


def test_after_taking_over_land_runs_the_normal_landing_to_the_cap_not_just_a_motor_stop(
    taking_over_adapter: CrazyflieAdapter, fake_cflib: FakeCflib
) -> None:
    # No take-off of ours, so no settle height: the final descent height is the cap (ADR-0056).
    fake_cflib.samples["state"]["stateEstimate.z"] = 0.6
    fake_cflib.samples["state"]["supervisor.info"] = FLYING
    fake_cflib.samples["down"]["range.zrange"] = 600.0
    taking_over_adapter.connect()

    taking_over_adapter.land()

    commander = fake_cflib.link.cf.high_level_commander
    commander.go_to.assert_called_once_with(
        0.0,
        0.0,
        MAX_FINAL_DESCENT_HEIGHT,
        adapter_module.DEFAULT_YAW_RAD,
        pytest.approx((0.6 - MAX_FINAL_DESCENT_HEIGHT) / adapter_module.VERTICAL_SPEED),
    )
    commander.stop.assert_not_called()


def test_taking_over_a_drone_that_reports_it_is_on_the_floor_only_stops_the_motors(
    taking_over_adapter: CrazyflieAdapter, fake_cflib: FakeCflib
) -> None:
    # A land request must not spin up the motors of an armed drone our code knows is on the floor (ADR-0039).
    fake_cflib.samples["state"]["supervisor.info"] = float(1 << adapter_module.BIT_IS_ARMED)
    taking_over_adapter.connect()

    taking_over_adapter.land()

    commander = fake_cflib.link.cf.high_level_commander
    commander.go_to.assert_not_called()
    commander.stop.assert_called_once()


def test_disconnecting_after_taking_over_lands_the_drone_then_closes_the_link(
    taking_over_adapter: CrazyflieAdapter, fake_cflib: FakeCflib
) -> None:
    fake_cflib.samples["state"]["stateEstimate.z"] = 0.4
    fake_cflib.samples["state"]["supervisor.info"] = FLYING
    fake_cflib.samples["down"]["range.zrange"] = 400.0
    taking_over_adapter.connect()

    taking_over_adapter.disconnect()

    commander = fake_cflib.link.cf.high_level_commander
    commander.go_to.assert_called()  # the landing approach
    commander.stop.assert_called()  # the motors, at the final descent's time limit: the fake's down range never changes
    fake_cflib.link.close_link.assert_called_once()


def test_a_failure_while_connecting_to_take_over_closes_only_the_radio_link(fake_cflib: FakeCflib) -> None:
    fake_cflib.silent_blocks.add("battery")
    fake_cflib.samples["state"]["supervisor.info"] = FLYING
    adapter = CrazyflieAdapter(BoundedSimClock(fake_cflib, start=10.0), take_over_flight=True)

    with pytest.raises(TimeoutError, match="Still missing: battery voltage"):
        adapter.connect()

    assert_only_the_radio_link_closed(fake_cflib)


@pytest.mark.parametrize("estimate_variable", ["stateEstimate.z", "stateEstimate.vz"])
def test_taking_over_a_drone_with_no_finite_estimate_points_to_the_emergency_stop(
    fake_cflib: FakeCflib, estimate_variable: str
) -> None:
    # A flying drone with a NaN estimate can't follow our landings, which are position commands (ADR-0045).
    fake_cflib.samples["state"][estimate_variable] = math.nan
    fake_cflib.samples["state"]["supervisor.info"] = FLYING
    adapter = CrazyflieAdapter(BoundedSimClock(fake_cflib, start=10.0), take_over_flight=True)

    with pytest.raises(
        TimeoutError, match=r"estimate\. If the drone is in the air, it can't land under control.*emergency_stop\.py"
    ):
        adapter.connect()

    assert_only_the_radio_link_closed(fake_cflib)


def test_a_normal_connect_with_no_finite_estimate_does_not_point_to_the_emergency_stop(fake_cflib: FakeCflib) -> None:
    # A normal connect has already refused a flying drone, so this one is on the floor: only a take-over
    # points to the emergency stop (ADR-0045).
    fake_cflib.samples["state"]["stateEstimate.z"] = math.nan
    adapter = CrazyflieAdapter(BoundedSimClock(fake_cflib, start=10.0))

    with pytest.raises(TimeoutError, match="Still missing: position estimate") as error:
        adapter.connect()

    assert "emergency_stop" not in str(error.value)


def test_a_take_over_that_misses_other_telemetry_says_to_check_the_crazyflie_is_in_range(fake_cflib: FakeCflib) -> None:
    fake_cflib.silent_blocks.add("battery")
    fake_cflib.samples["state"]["supervisor.info"] = FLYING
    adapter = CrazyflieAdapter(BoundedSimClock(fake_cflib, start=10.0), take_over_flight=True)

    with pytest.raises(TimeoutError, match="Check the Crazyflie is in range") as error:
        adapter.connect()

    assert "emergency_stop" not in str(error.value)


class ValueArrivesAtTheDeadlineClock(BoundedSimClock):
    """A missing value arrives the moment the first-telemetry wait reads the clock at its deadline: after the
    wait's last check, before its error message is written. `arrive` writes the value."""

    def __init__(self, fake_cflib: FakeCflib, start: float, arrive: Callable[[CrazyflieAdapter], None]) -> None:
        super().__init__(fake_cflib, start)
        self.adapter: CrazyflieAdapter | None = None
        self._arrive = arrive
        self._wait_started_at: float | None = None
        self._has_arrived = False

    def now(self) -> float:
        now = super().now()
        if self.adapter is None or self._has_arrived or "start battery" not in self._fake_cflib.events:
            return now
        if self._wait_started_at is None:
            # The first clock reading after the battery block starts. Simulated time doesn't move between
            # then and the start of the wait, so it is the wait's start time.
            self._wait_started_at = now
        elif now >= self._wait_started_at + adapter_module.FIRST_TELEMETRY_TIME_LIMIT:
            self._has_arrived = True  # set first: the write reads the clock too
            self._arrive(self.adapter)
        return now


def test_the_time_limit_message_names_what_was_missing_when_the_wait_ran_out(fake_cflib: FakeCflib) -> None:
    fake_cflib.silent_blocks.add("battery")
    clock = ValueArrivesAtTheDeadlineClock(
        fake_cflib, 10.0, lambda adapter: adapter._telemetry.write_battery_voltage(4.0, drone_time=None)
    )
    adapter = CrazyflieAdapter(clock)
    clock.adapter = adapter

    with pytest.raises(TimeoutError, match=r"Still missing: battery voltage\. "):
        adapter.connect()

    assert adapter._telemetry.missing_values() == []  # it did arrive, after the check that timed out


def test_an_estimate_arriving_after_a_take_over_times_out_still_points_to_the_emergency_stop(
    fake_cflib: FakeCflib,
) -> None:
    # The advice follows the check that timed out, not a finite estimate that turned up a moment later (ADR-0045).
    fake_cflib.samples["state"]["stateEstimate.z"] = math.nan
    fake_cflib.samples["state"]["supervisor.info"] = FLYING
    clock = ValueArrivesAtTheDeadlineClock(
        fake_cflib, 10.0, lambda adapter: adapter._telemetry.write_position_estimate(Vector3(0.0, 0.0, 0.3), None)
    )
    adapter = CrazyflieAdapter(clock, take_over_flight=True)
    clock.adapter = adapter

    with pytest.raises(TimeoutError, match=r"Still missing: position estimate\. If the drone is in the air"):
        adapter.connect()

    assert adapter._telemetry.missing_values() == []
    assert_only_the_radio_link_closed(fake_cflib)


def test_connecting_again_waits_for_a_new_status_not_the_last_connections(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib
) -> None:
    adapter.connect()
    adapter.disconnect()
    fake_cflib.silent_blocks.add("state")
    second_adapter = CrazyflieAdapter(BoundedSimClock(fake_cflib, start=10.0))
    second_adapter._latest_status_bitfield = 0  # as if left from an earlier connection

    with pytest.raises(TimeoutError, match="Waiting for the drone's status"):
        second_adapter.connect()


# --- The thrust base (ADR-0061) -----------------------------------------------------

UNCONFIRMED_TAKE_OFF_WARNING = "Taking off without a confirmed thrust base: the climb may be slow."


def thrust_base_writes(fake_cflib: FakeCflib) -> list[str]:
    return [event for event in fake_cflib.events if event.startswith("write thrust base")]


def thrust_base_logs(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [record.getMessage() for record in caplog.records if "thrust base" in record.getMessage().lower()]


def take_off_logs(adapter: CrazyflieAdapter, caplog: pytest.LogCaptureFixture) -> list[str]:
    """Take off from the floor, and return what the adapter logged about the thrust base meanwhile."""
    caplog.clear()
    with caplog.at_level(logging.WARNING, logger=adapter_module.logger.name):
        adapter.take_off(1.0)
    return thrust_base_logs(caplog)


def test_connecting_writes_the_thrust_base(adapter: CrazyflieAdapter, fake_cflib: FakeCflib) -> None:
    adapter.connect()

    assert thrust_base_writes(fake_cflib) == [f"write thrust base {adapter_module.THRUST_BASE}"]


def test_a_flying_drone_is_refused_without_a_thrust_base_write(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib
) -> None:
    fake_cflib.samples["state"]["supervisor.info"] = FLYING

    with pytest.raises(RuntimeError, match="still flying"):
        adapter.connect()

    assert thrust_base_writes(fake_cflib) == []


@pytest.mark.parametrize("status", [FLYING, 0.0], ids=["flying", "on the floor"])
def test_taking_over_leaves_the_thrust_base_as_it_is(
    taking_over_adapter: CrazyflieAdapter, fake_cflib: FakeCflib, caplog: pytest.LogCaptureFixture, status: float
) -> None:
    fake_cflib.samples["state"]["supervisor.info"] = status

    with caplog.at_level(logging.INFO, logger=adapter_module.logger.name):
        taking_over_adapter.connect()

    assert thrust_base_writes(fake_cflib) == []
    assert thrust_base_logs(caplog) == ["Thrust base left as it is: the drone may be flying."]


@pytest.mark.parametrize(
    ("value", "level", "message"),
    [
        (
            str(adapter_module.THRUST_BASE),
            logging.INFO,
            f"Thrust base confirmed: the drone reports {adapter_module.THRUST_BASE}.",
        ),
        (
            "36000",
            logging.WARNING,
            f"Thrust base not confirmed: the drone reports 36000, not {adapter_module.THRUST_BASE}.",
        ),
    ],
    ids=["the written value", "another value"],
)
def test_each_thrust_base_report_is_logged_with_whether_it_confirms_the_write(
    adapter: CrazyflieAdapter,
    fake_cflib: FakeCflib,
    caplog: pytest.LogCaptureFixture,
    value: str,
    level: int,
    message: str,
) -> None:
    fake_cflib.reports_written_values = False
    adapter.connect()
    caplog.clear()

    with caplog.at_level(logging.INFO, logger=adapter_module.logger.name):
        fake_cflib.report_parameter("posCtlPid.thrustBase", value)

    assert [(record.levelno, record.getMessage()) for record in caplog.records] == [(level, message)]


def test_a_take_off_after_the_drone_confirmed_the_thrust_base_does_not_warn(
    adapter: CrazyflieAdapter, caplog: pytest.LogCaptureFixture
) -> None:
    adapter.connect()

    assert take_off_logs(adapter, caplog) == []


def test_a_take_off_warns_when_the_drone_has_not_confirmed_the_thrust_base(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib, caplog: pytest.LogCaptureFixture
) -> None:
    fake_cflib.reports_written_values = False  # the write, or the drone's report of it, was lost
    adapter.connect()

    assert take_off_logs(adapter, caplog) == [UNCONFIRMED_TAKE_OFF_WARNING]
    assert adapter._is_in_initial_climb  # only a log line: it never refuses


@pytest.mark.parametrize("reports_the_write", [False, True], ids=["instead of the write", "after the write"])
def test_a_report_of_the_old_thrust_base_is_not_a_confirmation(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib, caplog: pytest.LogCaptureFixture, reports_the_write: bool
) -> None:
    """Only the latest report counts, and only THRUST_BASE confirms: a parameter read can report the old value."""
    fake_cflib.reports_written_values = reports_the_write
    adapter.connect()
    fake_cflib.report_parameter("posCtlPid.thrustBase", "36000")

    assert take_off_logs(adapter, caplog) == [UNCONFIRMED_TAKE_OFF_WARNING]


@pytest.mark.parametrize(
    "error",
    [KeyError("posCtlPid.thrustBase not in param TOC"), AttributeError("posCtlPid.thrustBase is read-only!")],
    ids=["missing", "read-only"],
)
def test_a_thrust_base_the_firmware_cannot_write_is_warned_and_the_drone_still_flies(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib, caplog: pytest.LogCaptureFixture, error: Exception
) -> None:
    """A missing write never stops a flight (ADR-0061)."""
    fake_cflib.thrust_base_error = error

    with caplog.at_level(logging.WARNING, logger=adapter_module.logger.name):
        adapter.connect()

    assert thrust_base_logs(caplog) == ["Thrust base not sent: the firmware can't write it."]
    assert take_off_logs(adapter, caplog) == [UNCONFIRMED_TAKE_OFF_WARNING]
    assert adapter._is_in_initial_climb


def test_a_thrust_base_write_after_the_link_is_lost_says_the_link_is_closed(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib, caplog: pytest.LogCaptureFixture
) -> None:
    def lose_the_link() -> None:
        fake_cflib.link.cf.link = None
        # cflib forgets the parameter list once the link is lost.
        fake_cflib.thrust_base_error = KeyError("posCtlPid.thrustBase not in param TOC")

    fake_cflib.on_reset_estimate = lose_the_link  # the write just before the thrust base's

    with caplog.at_level(logging.WARNING, logger=adapter_module.logger.name):
        adapter.connect()

    assert thrust_base_logs(caplog) == ["Thrust base not sent: the link is closed."]


def test_connecting_again_needs_a_new_report_of_the_thrust_base(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib, caplog: pytest.LogCaptureFixture
) -> None:
    adapter.connect()  # the drone reports the thrust base
    adapter.disconnect()
    fake_cflib.reports_written_values = False
    adapter.connect()

    assert take_off_logs(adapter, caplog) == [UNCONFIRMED_TAKE_OFF_WARNING]


def test_the_thrust_base_report_never_raises_on_cflibs_receive_thread(adapter: CrazyflieAdapter) -> None:
    """An exception there would block every later parameter write in cflib."""
    adapter._on_thrust_base_reported("posCtlPid.thrustBase", "not a number")

    assert not adapter._is_thrust_base_confirmed
