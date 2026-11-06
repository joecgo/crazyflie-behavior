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
from unittest.mock import MagicMock

import pytest

from crazyflie_behavior.drone.crazyflie import adapter as adapter_module
from crazyflie_behavior.drone.crazyflie.adapter import CrazyflieAdapter
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
    "down": {"range.zrange": 20.0},
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
        """What happened, in order: "start <block>" and "reset estimator"."""
        self.reset_estimator = MagicMock(side_effect=self._record_the_reset)
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

    def _record_the_reset(self, *_arguments: object) -> None:
        self.events.append("reset estimator")

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
    monkeypatch.setattr(adapter_module, "reset_estimator", fake.reset_estimator)
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

    fake_cflib.reset_estimator.assert_called_once_with(fake_cflib.link)
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

    readings = adapter._telemetry.snapshot(0.0).range_readings
    for reading in (readings.front, readings.back, readings.left, readings.right, readings.up):
        assert reading is not None
        assert reading.value.status is RangeStatus.INVALID


def test_the_older_flow_deck_counts_too(adapter: CrazyflieAdapter, fake_cflib: FakeCflib) -> None:
    del fake_cflib.parameters["deck.bcFlow2"]  # firmware without the v2 parameter
    fake_cflib.parameters["deck.bcFlow"] = "1"

    adapter.connect()

    fake_cflib.reset_estimator.assert_called_once()


def test_without_a_flow_deck_it_refuses_to_fly_and_closes_only_the_radio_link(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib
) -> None:
    fake_cflib.parameters["deck.bcFlow2"] = "0"

    with pytest.raises(RuntimeError, match="Flow deck"):
        adapter.connect()

    assert_only_the_radio_link_closed(fake_cflib)
    fake_cflib.reset_estimator.assert_not_called()


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
    for name in ("LINK_TIME_LIMIT", "PARAMETERS_TIME_LIMIT", "POSITION_ESTIMATE_TIME_LIMIT"):
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


@pytest.mark.usefixtures("short_time_limits")
def test_settling_the_position_estimate_has_a_time_limit_then_closes_the_link(
    fake_cflib: FakeCflib, blocking_step: BlockingStep
) -> None:
    fake_cflib.reset_estimator.side_effect = blocking_step

    with pytest.raises(TimeoutError, match="Check the Flow deck can see the floor"):
        real_time_adapter().connect()

    fake_cflib.link.close_link.assert_called_once()


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
    fake_cflib.reset_estimator.side_effect = TimeoutError("estimate never settled")

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
    adapter.take_snapshot(0.05)

    # The old landing would have stopped the motors or sent a go_to to an armed drone on the floor.
    assert fake_cflib.link.cf.high_level_commander.mock_calls == []


# --- Connecting to a flying drone (ADR-0038) --------------------------------------

FLYING = float(1 << adapter_module.BIT_IS_FLYING)
"""A `supervisor.info` value whose flying bit is set."""


def test_the_state_log_block_starts_before_the_estimate_reset(adapter: CrazyflieAdapter, fake_cflib: FakeCflib) -> None:
    adapter.connect()

    assert fake_cflib.events.index("start state") < fake_cflib.events.index("reset estimator")


def test_a_flying_drone_is_refused_before_the_estimate_reset_and_without_a_zero_thrust_setpoint(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib
) -> None:
    fake_cflib.samples["state"]["supervisor.info"] = FLYING

    with pytest.raises(RuntimeError, match=r"still flying: run the rescue landing, or wait .* if it just landed"):
        adapter.connect()

    fake_cflib.reset_estimator.assert_not_called()
    assert_only_the_radio_link_closed(fake_cflib)


def test_a_status_that_never_arrives_is_a_time_limit_error_that_closes_only_the_radio_link(
    fake_cflib: FakeCflib,
) -> None:
    fake_cflib.silent_blocks.add("state")
    adapter = CrazyflieAdapter(BoundedSimClock(fake_cflib, start=10.0))

    with pytest.raises(TimeoutError, match=r"Waiting for the drone's status took longer than 3 s\. Check"):
        adapter.connect()

    fake_cflib.reset_estimator.assert_not_called()
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

    def reset_the_estimate(*_arguments: object) -> None:
        fake_cflib.samples["state"]["stateEstimate.x"] = 0.0

    fake_cflib.reset_estimator.side_effect = reset_the_estimate

    adapter.connect()

    position_estimate = adapter._telemetry.snapshot(0.0).position_estimate
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

    fake_cflib.reset_estimator.assert_not_called()
    fake_cflib.link.close_link.assert_not_called()
    assert "Taking over the flight" in caplog.text


def test_taking_over_keeps_the_position_the_drone_already_reported(
    taking_over_adapter: CrazyflieAdapter, fake_cflib: FakeCflib
) -> None:
    fake_cflib.samples["state"]["stateEstimate.z"] = 0.4
    fake_cflib.samples["state"]["supervisor.info"] = FLYING

    taking_over_adapter.connect()

    position_estimate = taking_over_adapter._telemetry.snapshot(0.0).position_estimate
    assert position_estimate is not None
    assert position_estimate.value.z == pytest.approx(0.4)


def test_after_taking_over_land_runs_the_normal_landing_not_just_a_motor_stop(
    taking_over_adapter: CrazyflieAdapter, fake_cflib: FakeCflib
) -> None:
    fake_cflib.samples["state"]["stateEstimate.z"] = 0.4
    fake_cflib.samples["state"]["supervisor.info"] = FLYING
    taking_over_adapter.connect()

    taking_over_adapter.land()

    commander = fake_cflib.link.cf.high_level_commander
    commander.go_to.assert_called_once_with(
        0.0, 0.0, 0.0, adapter_module.DEFAULT_YAW_RAD, pytest.approx(0.4 / adapter_module.VERTICAL_SPEED)
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
    taking_over_adapter.connect()

    taking_over_adapter.disconnect()

    commander = fake_cflib.link.cf.high_level_commander
    commander.go_to.assert_called()  # the landing
    commander.stop.assert_called()  # the motors, once touchdown was confirmed
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
