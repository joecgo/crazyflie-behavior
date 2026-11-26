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
from crazyflie_behavior.drone.crazyflie import link as link_module
from crazyflie_behavior.drone.crazyflie import log_blocks as log_blocks_module
from crazyflie_behavior.drone.crazyflie.adapter import TAKE_OFF_BLOCK_DURATION, CrazyflieAdapter
from crazyflie_behavior.drone.crazyflie.bad_flow_zone import FINAL_DESCENT_HEIGHT
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
    "controller": {
        "pid_attitude.roll_outI": 0.0,
        "pid_attitude.pitch_outI": 0.0,
        "pid_rate.roll_outI": 0.0,
        "pid_rate.pitch_outI": 0.0,
        "controller.cmd_roll": 0.0,
        "controller.cmd_pitch": 0.0,
        "controller.roll": 0.0,
        "controller.pitch": 0.0,
        "gyro.x": 0.0,
        "gyro.y": 0.0,
    },
    "take_off": {
        "stateEstimate.roll": 0.0,
        "stateEstimate.pitch": 0.0,
        "stateEstimate.yaw": 0.0,
        "motor.m1": 0.0,
        "motor.m2": 0.0,
        "motor.m3": 0.0,
        "motor.m4": 0.0,
    },
}
"""Each log block's first sample, as cflib delivers it."""
PAST_EVERY_TIME_LIMIT = 3600.0
"""Seconds: longer than any time limit of connect()."""
LOST_LINK_ERROR = "The radio link to the drone was lost: Too many packets lost"
"""The adapter's error for the fake's lost link."""


def cflib_mock_class(before_each_call: Callable[[], None]) -> type[MagicMock]:
    """A MagicMock class whose mocks, their attributes and return values included, run `before_each_call` first on
    every call, magic methods such as `bool()` too."""

    class CflibMock(MagicMock):
        def __call__(self, *args: object, **kwargs: object) -> object:
            before_each_call()
            return super().__call__(*args, **kwargs)

    return CflibMock


class FakeCflib:
    """Stands in for cflib during connect(): records what the adapter asked for.

    Each log block sends one sample when it starts, like a drone's first
    packet: at once, after `first_sample_delay` seconds, or never for blocks
    in `silent_blocks`. A real drone keeps streaming, and connect() relies on
    that after it swaps the telemetry buffer (ADR-0038): `stream_samples()`
    sends every started block's sample again, and with a delay the blocks keep
    streaming on a thread. A block's `started` is True from its start, as if the
    drone confirmed it at once, until its stop; silent blocks never confirm.

    `lose_the_link()` loses the link the way cflib does, at any moment or just
    before a given call (ADR-0095).
    """

    def __init__(self) -> None:
        self.is_link_lost = False
        self._calls_made = 0
        self._lose_the_link_before: int | None = None
        """The index in `link.mock_calls` of the call the link is lost just before, when set."""
        self.lost_at: int | None = None
        """The index in `link.mock_calls` of the call the link was lost just before, once lost that way."""
        self._clock: SimClock | None = None
        """The sim clock a cflib wait that never ends lets time pass on, after a lost link."""
        self._added_block_ids: set[int] = set()
        """The `id()` of each log block cflib added. A block passed to `add_config` after a lost link isn't here:
        cflib leaves it without a Crazyflie."""
        self._mock_class = cflib_mock_class(self._before_each_call)
        self.link = self._mock_class()
        """The SyncCrazyflie: open_link, close_link, and the Crazyflie as .cf. Its `mock_calls` holds every cflib call,
        the log blocks' included, in order."""
        self.radio_link = self.link.cf.link
        """The Crazyflie's radio link: closing it is what a safe link close does (ADR-0038)."""
        self.sync_crazyflie_class = MagicMock(return_value=self.link)
        """cflib's SyncCrazyflie class: called with the URI and the Crazyflie, it returns `link`."""
        self.crazyflie_class = MagicMock()
        """cflib's Crazyflie class: called with the cache directory."""
        self.parameters = {"deck.bcFlow2": "1", "deck.bcMultiranger": "0"}
        """Parameter values as cflib returns them (strings). Missing means the
        firmware doesn't know the parameter, so cflib raises KeyError."""
        self.link.cf.param.get_value.side_effect = self.get_parameter
        self.link.wait_for_params.side_effect = self._wait_for_params
        self.link.cf.log.add_config.side_effect = self._add_config
        self.events: list[str] = []
        """What happened, in order: "start <block>", "stop <block>", "reset estimate" and "write thrust base"."""
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
        if self.is_link_lost:
            raise KeyError(name)  # cflib empties the values once the link is lost (facts register)
        return self.parameters[name]

    def lose_the_link(self) -> None:
        """Lose the link the way cflib does (facts register): the link goes to None, the parameters and log blocks
        stop working, then the disconnected callbacks run, and the connection_lost ones last."""
        uri = "radio://0/80/2M/E7E7E7E7E7"
        self.link.cf.link = None
        self.is_link_lost = True
        for call in self.link.cf.disconnected.add_callback.call_args_list:
            call.args[0](uri)
        for call in self.link.cf.connection_lost.add_callback.call_args_list:
            call.args[0](uri, "Too many packets lost")

    def lose_the_link_before_call(self, index: int, clock: SimClock) -> None:
        """Lose the link just before the call at `index` in `link.mock_calls`. A cflib wait that never ends after it
        lets time pass on `clock`, past every time limit."""
        self._lose_the_link_before = index
        self._clock = clock

    def _before_each_call(self) -> None:
        if self._calls_made == self._lose_the_link_before:
            self.lost_at = len(self.link.mock_calls)  # the index of the call about to be made
            self.lose_the_link()
        self._calls_made += 1

    def _wait_for_params(self) -> None:
        if self.is_link_lost:
            # cflib's wait never ends once the link is lost (facts register).
            if self._clock is None:
                # pytest.fail gets through connect()'s cleanup, which reports an AssertionError as the lost link.
                pytest.fail("lose_the_link_before_call() sets the clock")
            self._clock.advance(PAST_EVERY_TIME_LIMIT)
            self._stopped.wait(timeout=10.0)

    def _add_config(self, block: MagicMock) -> None:
        if not self.is_link_lost:  # cflib adds no block once the link is lost (facts register)
            self._added_block_ids.add(id(block))

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
        if self.is_link_lost:
            raise KeyError(name)  # cflib empties the parameter list once the link is lost (facts register)
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
        block = self._mock_class()
        self.link.attach_mock(block, f"log_block_{name}")  # its calls land in link.mock_calls, in order with the rest
        block.started = False
        callbacks: list[Callable[[int, dict[str, float], object], None]] = []
        block.data_received_cb.add_callback.side_effect = callbacks.append
        block.start.side_effect = lambda: self._start_block(name, block, callbacks)
        block.stop.side_effect = lambda: self._stop_block(name, block)
        return block

    def stream_samples(self) -> None:
        """Send every started block's sample again, as a streaming drone does."""
        for name in list(self._started_blocks):
            self._send(name)

    def stop(self) -> None:
        self._stopped.set()

    def _stop_block(self, name: str, block: MagicMock) -> None:
        if self.is_link_lost:
            return  # cflib's stop does nothing once the link is lost (facts register)
        self.events.append(f"stop {name}")
        block.started = False
        self._started_blocks.pop(name, None)

    def _send(self, name: str) -> None:
        if self.is_link_lost:
            return  # no packet arrives once the link is lost
        block, callbacks = self._started_blocks[name]
        for callback in callbacks:
            callback(1000, self.samples[name], block)

    def _start_block(
        self,
        name: str,
        block: MagicMock,
        callbacks: list[Callable[[int, dict[str, float], object], None]],
    ) -> None:
        if id(block) not in self._added_block_ids:
            # cflib's block has no Crazyflie until it's added (facts register).
            raise AttributeError("'NoneType' object has no attribute 'link'")
        if self.is_link_lost:
            return  # cflib's start does nothing once the link is lost (facts register)
        self.events.append(f"start {name}")
        if name in self.silent_blocks:
            return
        block.started = True
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


def install_fake_cflib(monkeypatch: pytest.MonkeyPatch) -> FakeCflib:
    """A fake cflib in place of the adapter's cflib classes, until `monkeypatch` puts them back."""
    fake = FakeCflib()
    monkeypatch.setattr(link_module, "_drivers_initialized", True)
    monkeypatch.setattr(link_module, "SyncCrazyflie", fake.sync_crazyflie_class)
    monkeypatch.setattr(link_module, "Crazyflie", fake.crazyflie_class)
    monkeypatch.setattr(log_blocks_module, "LogConfig", fake.make_log_block)
    return fake


@pytest.fixture
def fake_cflib(monkeypatch: pytest.MonkeyPatch) -> Generator[FakeCflib]:
    fake = install_fake_cflib(monkeypatch)
    yield fake
    fake.stop()  # ends the streaming threads and the waits that never end


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
    # The controller block too (ADR-0063); the take-off block only with the take-off log.
    assert fake_cflib.log_block_names == ["state", "battery", "down", "diagnostic", "controller"]
    fake_cflib.link.close_link.assert_not_called()


def test_connecting_opens_the_link_to_the_uri_with_the_cache_directory(fake_cflib: FakeCflib) -> None:
    clock = StreamingSimClock(fake_cflib, start=10.0)

    CrazyflieAdapter(clock, uri="radio://0/90/2M/E7E7E7E7E8", cache_directory="./test-cache").connect()

    fake_cflib.crazyflie_class.assert_called_once_with(rw_cache="./test-cache")
    fake_cflib.sync_crazyflie_class.assert_called_once_with(
        "radio://0/90/2M/E7E7E7E7E8", cf=fake_cflib.crazyflie_class.return_value
    )


def test_connecting_logs_that_the_drone_arms_itself(
    adapter: CrazyflieAdapter,
    fake_cflib: FakeCflib,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_cflib.samples["state"]["supervisor.info"] = float(1 << adapter_module.BIT_IS_AUTO_ARMED)

    with caplog.at_level(logging.INFO, logger=adapter_module.__package__):
        adapter.connect()

    assert [r.getMessage() for r in caplog.records if "arms itself" in r.getMessage()] == [
        "The drone arms itself (auto-arming is on): a disarm won't last."
    ]


def test_connecting_logs_that_the_drone_does_not_arm_itself(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO, logger=adapter_module.__package__):
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

    with caplog.at_level(logging.INFO, logger=adapter_module.__package__):
        adapter.connect()

    assert buzzer_deck_logs(caplog) == ["Buzzer deck detected."]


@pytest.mark.parametrize("deck_parameter", ["0", None], ids=["not attached", "unknown to the firmware"])
def test_connecting_without_a_buzzer_deck_logs_that_buzzer_commands_make_no_sound(
    deck_parameter: str | None, adapter: CrazyflieAdapter, fake_cflib: FakeCflib, caplog: pytest.LogCaptureFixture
) -> None:
    """Flying doesn't need the buzzer, so the connect goes on (ADR-0053)."""
    if deck_parameter is not None:
        fake_cflib.parameters["deck.bcBuzzer"] = deck_parameter

    with caplog.at_level(logging.INFO, logger=adapter_module.__package__):
        adapter.connect()

    assert buzzer_deck_logs(caplog) == ["No Buzzer deck: buzzer commands will make no sound."]
    fake_cflib.link.close_link.assert_not_called()


def test_connecting_again_warns_again_about_a_buzzer_command_on_a_closed_link(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib, caplog: pytest.LogCaptureFixture
) -> None:
    """The once-per-streak warning starts over with each connection."""
    caplog.set_level(logging.WARNING, logger=adapter_module.__package__)
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


def test_log_periods_are_ones_the_firmware_accepts(fake_cflib: FakeCflib) -> None:
    fake_cflib.parameters["deck.bcMultiranger"] = "1"
    adapter = CrazyflieAdapter(StreamingSimClock(fake_cflib, start=10.0), take_off_log=True)  # every block

    adapter.connect()

    assert set(fake_cflib.log_block_periods_ms) == {*FIRST_SAMPLES}
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


def test_a_disconnect_after_a_failed_connect_does_nothing(adapter: CrazyflieAdapter, fake_cflib: FakeCflib) -> None:
    # The start-up calls disconnect() in a `finally`, also after connect() raised and closed the link.
    fake_cflib.parameters["deck.bcFlow2"] = "0"
    with pytest.raises(RuntimeError, match="Flow deck"):
        adapter.connect()
    calls_after_the_connect = list(fake_cflib.link.mock_calls)

    adapter.disconnect()

    assert fake_cflib.link.mock_calls == calls_after_the_connect


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
        monkeypatch.setattr(link_module, name, 0.2)


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
def test_the_time_limit_itself_stops_the_connection_under_way_before_connect_cleans_up(
    fake_cflib: FakeCflib, blocking_step: BlockingStep, monkeypatch: pytest.MonkeyPatch
) -> None:
    # connect()'s cleanup closes only the radio link too: this checks that the time limit closed it first.
    fake_cflib.link.open_link.side_effect = blocking_step
    adapter = real_time_adapter()
    radio_link_closes_at_the_cleanup: list[int] = []
    close_link = adapter._close_link

    def record_then_close_the_link() -> None:
        radio_link_closes_at_the_cleanup.append(fake_cflib.radio_link.close.call_count)
        close_link()

    monkeypatch.setattr(adapter, "_close_link", record_then_close_the_link)

    with pytest.raises(TimeoutError, match="Opening the link"):
        adapter.connect()

    assert radio_link_closes_at_the_cleanup == [1]
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

    with caplog.at_level(logging.WARNING, logger=adapter_module.__package__):
        taking_over_adapter.connect()

    assert fake_cflib.reset_count == 0
    fake_cflib.link.close_link.assert_not_called()
    assert "Taking over the flight" in caplog.text


def test_taking_over_starts_no_diagnostic_or_controller_block(
    taking_over_adapter: CrazyflieAdapter, fake_cflib: FakeCflib
) -> None:
    """The drone may be flying: a missing debug-only variable mustn't fail the connect (ADR-0067)."""
    fake_cflib.samples["state"]["supervisor.info"] = FLYING
    fake_cflib.parameters["deck.bcMultiranger"] = "1"

    taking_over_adapter.connect()

    assert fake_cflib.log_block_names == ["state", "battery", "down", "multiranger"]


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


def test_after_taking_over_land_runs_the_normal_landing_not_just_a_motor_stop(
    taking_over_adapter: CrazyflieAdapter, fake_cflib: FakeCflib
) -> None:
    # A taken-over flight lands from the same final descent height as every other landing (ADR-0077).
    fake_cflib.samples["state"]["stateEstimate.z"] = 0.6
    fake_cflib.samples["state"]["supervisor.info"] = FLYING
    fake_cflib.samples["down"]["range.zrange"] = 600.0
    taking_over_adapter.connect()
    aim = FINAL_DESCENT_HEIGHT - adapter_module.LANDING_APPROACH_AIM_BELOW

    taking_over_adapter.land()

    commander = fake_cflib.link.cf.high_level_commander
    commander.go_to.assert_called_once_with(
        0.0,
        0.0,
        pytest.approx(aim),
        adapter_module.DEFAULT_YAW_RAD,
        pytest.approx((0.6 - aim) / adapter_module.VERTICAL_SPEED),
    )
    commander.stop.assert_not_called()


def test_after_connecting_a_landing_hands_over_from_the_velocity_setpoints_before_it(
    taking_over_adapter: CrazyflieAdapter, fake_cflib: FakeCflib
) -> None:
    """The landing approach goes through the commands `connect()` built, which know the stream to hand over from
    (ADR-0056, ADR-0093)."""
    fake_cflib.samples["state"]["stateEstimate.z"] = 0.6
    fake_cflib.samples["state"]["supervisor.info"] = FLYING
    fake_cflib.samples["down"]["range.zrange"] = 600.0
    taking_over_adapter.connect()

    taking_over_adapter.set_velocity(Vector3(0.1, 0.0, 0.0))
    taking_over_adapter.land()

    calls = [name for name, _, _ in fake_cflib.link.mock_calls]
    assert calls[calls.index("cf.commander.send_velocity_world_setpoint") :] == [
        "cf.commander.send_velocity_world_setpoint",
        "cf.high_level_commander.go_to",  # the landing approach
        "cf.commander.send_notify_setpoint_stop",  # the release, after the move that takes over
    ]


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
    with caplog.at_level(logging.WARNING, logger=adapter_module.__package__):
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

    with caplog.at_level(logging.INFO, logger=adapter_module.__package__):
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

    with caplog.at_level(logging.INFO, logger=adapter_module.__package__):
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

    with caplog.at_level(logging.WARNING, logger=adapter_module.__package__):
        adapter.connect()

    assert thrust_base_logs(caplog) == ["Thrust base not sent: the firmware can't write it."]
    assert take_off_logs(adapter, caplog) == [UNCONFIRMED_TAKE_OFF_WARNING]
    assert adapter._is_in_initial_climb


def test_a_thrust_base_write_after_the_link_is_lost_says_the_link_is_closed(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib, caplog: pytest.LogCaptureFixture
) -> None:
    fake_cflib.on_reset_estimate = fake_cflib.lose_the_link  # the write just before the thrust base's

    with (
        caplog.at_level(logging.WARNING, logger=adapter_module.__package__),
        pytest.raises(ConnectionError, match=LOST_LINK_ERROR),
    ):
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


# --- The controller block and the take-off block (ADR-0063, ADR-0065) -------------------

TICK = 0.05


def variables_fetched(block: object) -> list[tuple[str, str | None]]:
    """Each variable added to a fake log block, with the type it's fetched as."""
    add_variable = cast(MagicMock, cast(MagicMock, block).add_variable)
    return [(added.args[0], added.args[1]) for added in add_variable.call_args_list]


def test_connect_does_not_wait_for_the_controller_block(adapter: CrazyflieAdapter, fake_cflib: FakeCflib) -> None:
    # It's for the debug log only, not telemetry (ADR-0063).
    fake_cflib.silent_blocks.add("controller")

    adapter.connect()

    assert adapter._telemetry.missing_values() == []
    assert fake_cflib.log_block_periods_ms["controller"] == 100


def test_only_the_controller_block_fetches_its_variables_as_fp16(fake_cflib: FakeCflib) -> None:
    """10 floats in 20 bytes (ADR-0063); every other variable comes as the type the drone stores."""
    fake_cflib.parameters["deck.bcMultiranger"] = "1"
    adapter = CrazyflieAdapter(StreamingSimClock(fake_cflib, start=10.0), take_off_log=True)

    adapter.connect()

    for name, block in zip(fake_cflib.log_block_names, adapter._log_configs, strict=True):
        fetched_as = {fetch_as for _, fetch_as in variables_fetched(block)}
        assert fetched_as == ({"FP16"} if name == "controller" else {None}), name


def test_with_every_block_the_drones_limits_hold(fake_cflib: FakeCflib) -> None:
    """The firmware takes up to 16 log blocks and 128 variables, and cflib raises past either."""
    fake_cflib.parameters["deck.bcMultiranger"] = "1"
    adapter = CrazyflieAdapter(StreamingSimClock(fake_cflib, start=10.0), take_off_log=True)

    adapter.connect()

    assert len(adapter._log_configs) <= 16
    assert sum(len(variables_fetched(block)) for block in adapter._log_configs) <= 128


def connected_with_the_take_off_log(fake_cflib: FakeCflib) -> tuple[CrazyflieAdapter, StreamingSimClock, float]:
    """A connected adapter with the take-off log, its clock, and when the take-off block's run from connect ends."""
    clock = StreamingSimClock(fake_cflib, start=10.0)
    adapter = CrazyflieAdapter(clock, take_off_log=True)
    adapter.connect()
    return adapter, clock, clock.now() + TAKE_OFF_BLOCK_DURATION


def tick_at(adapter: CrazyflieAdapter, clock: SimClock, time: float) -> None:
    """The take-off and landing update of a tick at `time`."""
    clock.sleep_until(time)
    adapter.update_take_off_and_landing(adapter.take_snapshot(TICK))


def take_off_block_events(fake_cflib: FakeCflib) -> list[str]:
    return [event for event in fake_cflib.events if event in {"start take_off", "stop take_off"}]


def test_with_the_take_off_log_the_take_off_block_is_created_last_in_connect(
    fake_cflib: FakeCflib, monkeypatch: pytest.MonkeyPatch
) -> None:
    """After the wait for the first telemetry, so its run falls in the first ticks (ADR-0065)."""
    adapter = CrazyflieAdapter(StreamingSimClock(fake_cflib, start=10.0), take_off_log=True)
    wait_for_first_telemetry = adapter._wait_for_first_telemetry

    def recorded_wait() -> None:
        wait_for_first_telemetry()
        fake_cflib.events.append("first telemetry")

    monkeypatch.setattr(adapter, "_wait_for_first_telemetry", recorded_wait)

    adapter.connect()

    assert fake_cflib.log_block_names[-1] == "take_off"
    assert fake_cflib.events[-2:] == ["first telemetry", "start take_off"]
    assert fake_cflib.log_block_periods_ms["take_off"] == 10


def test_the_tick_stops_the_take_off_block_once_its_run_from_connect_is_over(fake_cflib: FakeCflib) -> None:
    """The run counts from the create request (ADR-0065)."""
    adapter, clock, run_ends = connected_with_the_take_off_log(fake_cflib)

    tick_at(adapter, clock, run_ends - TICK)
    events_before_the_end = take_off_block_events(fake_cflib)
    tick_at(adapter, clock, run_ends)
    events_at_the_end = take_off_block_events(fake_cflib)
    tick_at(adapter, clock, run_ends + TICK)

    assert events_before_the_end == ["start take_off"]
    assert events_at_the_end == ["start take_off", "stop take_off"]
    assert take_off_block_events(fake_cflib) == ["start take_off", "stop take_off"]  # once


def test_the_take_off_block_is_never_stopped_before_the_drone_confirms_its_start(fake_cflib: FakeCflib) -> None:
    """cflib sends the start only once the drone confirms the create: a stop sent earlier would arrive first."""
    fake_cflib.silent_blocks.add("take_off")  # no confirmation
    adapter, clock, run_ends = connected_with_the_take_off_log(fake_cflib)
    block = cast(MagicMock, adapter._log_configs[fake_cflib.log_block_names.index("take_off")])

    tick_at(adapter, clock, run_ends)
    tick_at(adapter, clock, run_ends + 1.0)
    events_while_unconfirmed = take_off_block_events(fake_cflib)
    block.started = True  # the drone confirms it at last
    tick_at(adapter, clock, run_ends + 1.0 + TICK)

    assert events_while_unconfirmed == ["start take_off"]
    assert take_off_block_events(fake_cflib) == ["start take_off", "stop take_off"]


def test_a_take_off_while_the_take_off_block_runs_restarts_its_run_with_no_packet(fake_cflib: FakeCflib) -> None:
    adapter, clock, run_ends = connected_with_the_take_off_log(fake_cflib)
    clock.sleep_until(run_ends - 1.0)

    adapter.take_off(0.5)
    tick_at(adapter, clock, run_ends)  # the run from connect alone would stop here
    tick_at(adapter, clock, run_ends + 1.0 - TICK)
    events_before_the_end = take_off_block_events(fake_cflib)
    tick_at(adapter, clock, run_ends + 1.0)

    assert events_before_the_end == ["start take_off"]  # only the create's
    assert take_off_block_events(fake_cflib) == ["start take_off", "stop take_off"]


def test_a_take_off_after_the_run_starts_the_take_off_block_again_after_its_own_commands(
    fake_cflib: FakeCflib,
) -> None:
    """One start packet, after the initial climb's first setpoint: the drone kept the block (ADR-0065)."""
    adapter, clock, run_ends = connected_with_the_take_off_log(fake_cflib)
    tick_at(adapter, clock, run_ends)  # stops it

    def record_the_packet(packet: object) -> None:
        fake_cflib.events.append("send packet")

    fake_cflib.link.cf.send_packet.side_effect = record_the_packet
    take_off_time = run_ends + 3.0
    clock.sleep_until(take_off_time)

    adapter.take_off(0.5)
    events_of_the_take_off = fake_cflib.events[-2:]
    tick_at(adapter, clock, take_off_time + TAKE_OFF_BLOCK_DURATION - TICK)
    events_before_the_end = take_off_block_events(fake_cflib)
    tick_at(adapter, clock, take_off_time + TAKE_OFF_BLOCK_DURATION)

    assert events_of_the_take_off == ["send packet", "start take_off"]
    assert events_before_the_end == ["start take_off", "stop take_off", "start take_off"]
    assert take_off_block_events(fake_cflib) == ["start take_off", "stop take_off"] * 2


@pytest.mark.parametrize("is_confirmed", [True, False], ids=["start confirmed", "start not confirmed"])
def test_disconnecting_stops_the_take_off_block_before_its_landing(fake_cflib: FakeCflib, is_confirmed: bool) -> None:
    """The landing doesn't tick, so nothing else would stop the block while it lands (ADR-0065)."""
    fake_cflib.samples["state"]["stateEstimate.z"] = 0.4
    fake_cflib.samples["state"]["supervisor.info"] = FLYING
    fake_cflib.samples["down"]["range.zrange"] = 400.0
    if not is_confirmed:
        fake_cflib.silent_blocks.add("take_off")
    adapter = CrazyflieAdapter(StreamingSimClock(fake_cflib, start=10.0), take_over_flight=True, take_off_log=True)
    adapter.connect()

    def record_the_landing_approach(*arguments: object, **keywords: object) -> None:
        fake_cflib.events.append("landing approach")

    fake_cflib.link.cf.high_level_commander.go_to.side_effect = record_the_landing_approach
    events_before = len(fake_cflib.events)

    adapter.disconnect()

    assert fake_cflib.events[events_before : events_before + 2] == ["stop take_off", "landing approach"]


# --- A lost link (ADR-0084) -----------------------------------------------------------


def test_connect_listens_for_a_lost_link_before_the_link_opens(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib
) -> None:
    adapter.connect()

    calls = [name for name, _, _ in fake_cflib.link.mock_calls]
    assert calls.index("cf.connection_lost.add_callback") < calls.index("open_link")


def test_a_lost_link_is_logged_once_as_an_error_and_the_next_call_raises(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib, caplog: pytest.LogCaptureFixture
) -> None:
    adapter.connect()

    with caplog.at_level(logging.ERROR, logger=adapter_module.__package__):
        fake_cflib.lose_the_link()

    assert [record.getMessage() for record in caplog.records if record.levelno >= logging.ERROR] == [LOST_LINK_ERROR]
    with pytest.raises(ConnectionError, match=LOST_LINK_ERROR):
        adapter.take_snapshot(0.05)


# --- A link lost while connecting (ADR-0095) ------------------------------------------


def adapter_with_every_block(fake_cflib: FakeCflib, clock: SimClock) -> CrazyflieAdapter:
    """An adapter whose connect makes every cflib call it can: with the Multi-ranger's block and the take-off block."""
    fake_cflib.parameters["deck.bcMultiranger"] = "1"
    return CrazyflieAdapter(clock, take_off_log=True)


def described_call(name: str, args: tuple[object, ...], kwargs: dict[str, object]) -> str:
    """A cflib call as `name(arguments)`, with `...` for arguments that are mocks or callbacks."""
    if kwargs or not all(isinstance(arg, str | int | float | None) for arg in args):
        return f"{name}(...)"
    return f"{name}({', '.join(repr(arg) for arg in args)})"


def list_the_cflib_calls_once_the_link_is_open() -> list[tuple[int, str]] | Exception:
    """Each cflib call a connect with every block makes once the link is open, against the fake: its index in
    `link.mock_calls`, and the call. Or the error that stopped the listing."""
    with pytest.MonkeyPatch.context() as monkeypatch:
        fake = install_fake_cflib(monkeypatch)
        try:
            adapter_with_every_block(fake, StreamingSimClock(fake, start=10.0)).connect()
            calls = [described_call(name, args, kwargs) for name, args, kwargs in fake.link.mock_calls]
            after_the_link_opens = calls.index("open_link()") + 1
        except Exception as error:  # noqa: BLE001  # raised again by test_a_connect_with_every_block_is_listed
            return error
        finally:
            fake.stop()
    return list(enumerate(calls))[after_the_link_opens:]


LISTED_CALLS = list_the_cflib_calls_once_the_link_is_open()
"""Listed when the tests are collected, so a new cflib call in connect() is covered with no new test. An error while
listing fails one test, not the whole run's collection."""
CALLS_ONCE_THE_LINK_IS_OPEN = [] if isinstance(LISTED_CALLS, Exception) else LISTED_CALLS


def test_a_connect_with_every_block_is_listed() -> None:
    """Without the list, the next test has no cases."""
    if isinstance(LISTED_CALLS, Exception):
        raise LISTED_CALLS


def call_index(call: str) -> int:
    """The index of the first of CALLS_ONCE_THE_LINK_IS_OPEN that is `call`."""
    return next(index for index, listed in CALLS_ONCE_THE_LINK_IS_OPEN if listed == call)


@pytest.mark.parametrize(
    ("lost_before", "call"),
    CALLS_ONCE_THE_LINK_IS_OPEN,
    ids=[f"{index} {call}" for index, call in CALLS_ONCE_THE_LINK_IS_OPEN],
)
def test_a_link_lost_before_any_cflib_call_of_connect_once_the_link_is_open_ends_the_run_with_the_lost_links_error(
    fake_cflib: FakeCflib, monkeypatch: pytest.MonkeyPatch, lost_before: int, call: str
) -> None:
    """connect() raises it, after the link close (ADR-0095). A loss after its last step that would notice it is raised
    by the first snapshot instead (ADR-0086)."""
    clock = StreamingSimClock(fake_cflib, start=10.0)
    adapter = adapter_with_every_block(fake_cflib, clock)
    fake_cflib.lose_the_link_before_call(lost_before, clock)
    close_link = adapter._close_link
    was_raised_at_each_close: list[bool] = []

    def record_then_close_the_link() -> None:
        was_raised_at_each_close.append(adapter._link.is_lost_link_raised)
        close_link()

    monkeypatch.setattr(adapter, "_close_link", record_then_close_the_link)
    has_connected = False

    def connect_then_take_the_first_snapshot() -> None:
        nonlocal has_connected
        adapter.connect()
        has_connected = True
        adapter.take_snapshot(TICK)

    with pytest.raises(ConnectionError, match=LOST_LINK_ERROR) as raised:
        connect_then_take_the_first_snapshot()

    assert fake_cflib.lost_at == lost_before  # the fake's count of calls agrees with link.mock_calls
    name, args, kwargs = fake_cflib.link.mock_calls[lost_before]
    assert described_call(name, args, kwargs) == call  # so the link was lost just before the call its ID names
    assert has_connected or adapter._sync_crazyflie is None  # connect() raised it only after the link close
    # The cleanup's own raise comes while handling the step's error, and never before the link close.
    assert raised.value.__context__ is None or was_raised_at_each_close == [False]


@pytest.mark.parametrize(
    ("lost_before", "step_error"),
    [
        ("wait_for_params()", TimeoutError),  # the wait never ends, so its time limit ends it (ADR-0029)
        ("cf.param.get_value('deck.bcFlow2')", RuntimeError),  # the Flow deck check reads it as no deck
        ("cf.log.add_config(...)", AttributeError),  # the state block isn't added, so its start raises
    ],
    ids=["reading the parameters", "the Flow deck check", "the first log block"],
)
def test_the_lost_links_error_from_connect_is_raised_while_handling_the_failed_steps_error(
    fake_cflib: FakeCflib, lost_before: str, step_error: type[Exception]
) -> None:
    """So the traceback shows the step's error first, and not as the lost link's cause (ADR-0095)."""
    clock = StreamingSimClock(fake_cflib, start=10.0)
    adapter = adapter_with_every_block(fake_cflib, clock)
    fake_cflib.lose_the_link_before_call(call_index(lost_before), clock)

    with pytest.raises(ConnectionError, match=LOST_LINK_ERROR) as raised:
        adapter.connect()

    assert isinstance(raised.value.__context__, step_error)
    assert raised.value.__cause__ is None
    assert not raised.value.__suppress_context__


def test_a_lost_link_that_a_wait_of_connect_raises_is_passed_on_as_it_is(fake_cflib: FakeCflib) -> None:
    """Not raised a second time while handling the first (ADR-0095)."""
    clock = StreamingSimClock(fake_cflib, start=10.0)
    adapter = adapter_with_every_block(fake_cflib, clock)
    # The state block is added, so its start does nothing, and the wait for the drone's status raises.
    fake_cflib.lose_the_link_before_call(call_index("log_block_state.start()"), clock)

    with pytest.raises(ConnectionError, match=LOST_LINK_ERROR) as raised:
        adapter.connect()

    assert raised.value.__context__ is None


def test_the_interrupt_signal_after_a_lost_link_gets_through_and_closes_the_link(fake_cflib: FakeCflib) -> None:
    """Never replaced by the lost link's error (ADR-0094, ADR-0095)."""
    clock = StreamingSimClock(fake_cflib, start=10.0)
    adapter = adapter_with_every_block(fake_cflib, clock)
    fake_cflib.lose_the_link_before_call(call_index("cf.param.get_value('deck.bcFlow2')"), clock)
    fake_cflib.link.cf.param.get_value.side_effect = KeyboardInterrupt  # it arrives during the Flow deck check

    with pytest.raises(KeyboardInterrupt):
        adapter.connect()

    assert adapter._link.is_lost
    assert adapter._sync_crazyflie is None
