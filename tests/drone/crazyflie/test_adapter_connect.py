"""The Crazyflie adapter's connect(), against a fake cflib.

pytest's monkeypatch swaps the adapter's cflib classes for fakes for one test,
then puts the real ones back.
"""

# pyright: reportPrivateUsage=false

import signal
import threading
import time
from collections.abc import Callable, Generator
from unittest.mock import MagicMock

import pytest

from crazyflie_behavior.drone.crazyflie import adapter as adapter_module
from crazyflie_behavior.drone.crazyflie.adapter import CrazyflieAdapter
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
    in `silent_blocks`.
    """

    def __init__(self) -> None:
        self.link = MagicMock()
        """The SyncCrazyflie: open_link, close_link, and the Crazyflie as .cf."""
        self.parameters = {"deck.bcFlow2": "1", "deck.bcMultiranger": "0"}
        """Parameter values as cflib returns them (strings). Missing means the
        firmware doesn't know the parameter, so cflib raises KeyError."""
        self.link.cf.param.get_value.side_effect = self.get_parameter
        self.reset_estimator = MagicMock()
        self.log_block_names: list[str] = []
        self.log_block_periods_ms: dict[str, int] = {}
        self.silent_blocks: set[str] = set()
        self.first_sample_delay = 0.0
        """Seconds; above zero, the first samples arrive on a timer thread."""

    def get_parameter(self, name: str) -> str:
        return self.parameters[name]

    def make_log_block(self, name: str, period_in_ms: int) -> MagicMock:
        self.log_block_names.append(name)
        self.log_block_periods_ms[name] = period_in_ms
        block = MagicMock()
        callbacks: list[Callable[[int, dict[str, float], object], None]] = []
        block.data_received_cb.add_callback.side_effect = callbacks.append
        block.start.side_effect = lambda: self._send_first_sample(name, block, callbacks)
        return block

    def _send_first_sample(
        self,
        name: str,
        block: MagicMock,
        callbacks: list[Callable[[int, dict[str, float], object], None]],
    ) -> None:
        if name in self.silent_blocks:
            return

        def send() -> None:
            for callback in callbacks:
                callback(1000, FIRST_SAMPLES[name], block)

        if self.first_sample_delay > 0.0:
            timer = threading.Timer(self.first_sample_delay, send)
            timer.daemon = True
            timer.start()
        else:
            send()


@pytest.fixture
def fake_cflib(monkeypatch: pytest.MonkeyPatch) -> FakeCflib:
    fake = FakeCflib()
    monkeypatch.setattr(adapter_module, "_drivers_initialized", True)
    monkeypatch.setattr(adapter_module, "SyncCrazyflie", MagicMock(return_value=fake.link))
    monkeypatch.setattr(adapter_module, "Crazyflie", MagicMock())
    monkeypatch.setattr(adapter_module, "reset_estimator", fake.reset_estimator)
    monkeypatch.setattr(adapter_module, "LogConfig", fake.make_log_block)
    return fake


@pytest.fixture
def adapter() -> CrazyflieAdapter:
    return CrazyflieAdapter(SimClock(start=10.0))


def test_connecting_resets_the_estimate_and_starts_telemetry(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib
) -> None:
    adapter.connect()

    fake_cflib.reset_estimator.assert_called_once_with(fake_cflib.link)
    assert fake_cflib.log_block_names == ["state", "battery", "down"]
    fake_cflib.link.close_link.assert_not_called()


def test_a_multi_ranger_adds_its_own_log_block(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib
) -> None:
    fake_cflib.parameters["deck.bcMultiranger"] = "1"

    adapter.connect()

    assert "multiranger" in fake_cflib.log_block_names


def test_log_periods_are_ones_the_firmware_accepts(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib
) -> None:
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

    readings = adapter._telemetry.snapshot(10.0, 0.0).range_readings
    for reading in (readings.front, readings.back, readings.left, readings.right, readings.up):
        assert reading is not None
        assert reading.value.status is RangeStatus.INVALID


def test_the_older_flow_deck_counts_too(adapter: CrazyflieAdapter, fake_cflib: FakeCflib) -> None:
    del fake_cflib.parameters["deck.bcFlow2"]  # firmware without the v2 parameter
    fake_cflib.parameters["deck.bcFlow"] = "1"

    adapter.connect()

    fake_cflib.reset_estimator.assert_called_once()


def test_without_a_flow_deck_it_refuses_to_fly_and_closes_the_link(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib
) -> None:
    fake_cflib.parameters["deck.bcFlow2"] = "0"

    with pytest.raises(RuntimeError, match="Flow deck"):
        adapter.connect()

    fake_cflib.link.close_link.assert_called_once()
    fake_cflib.reset_estimator.assert_not_called()


class BlockingStep:
    """A fake cflib call that blocks like a stuck wait, until the test releases it.

    It can press Ctrl+C first: a real press arrives while cflib waits.
    """

    def __init__(self, press_ctrl_c: bool = False) -> None:
        self.release = threading.Event()
        self._press_ctrl_c = press_ctrl_c

    def __call__(self, *_arguments: object) -> None:
        if self._press_ctrl_c:
            signal.raise_signal(signal.SIGINT)
        self.release.wait(timeout=10.0)


@pytest.fixture
def blocking_step() -> Generator[BlockingStep]:
    step = BlockingStep()
    yield step
    step.release.set()  # let the abandoned helper thread finish


@pytest.fixture
def ctrl_c_step() -> Generator[BlockingStep]:
    step = BlockingStep(press_ctrl_c=True)
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
def test_opening_the_link_has_a_time_limit_then_stops_the_connection_under_way(
    fake_cflib: FakeCflib, blocking_step: BlockingStep
) -> None:
    fake_cflib.link.open_link.side_effect = blocking_step

    with pytest.raises(TimeoutError, match=r"Opening the link took longer than 0\.2 s\. Check the"):
        real_time_adapter().connect()

    fake_cflib.link.cf.close_link.assert_called_once()


@pytest.mark.usefixtures("short_time_limits")
def test_reading_the_parameters_has_a_time_limit_then_closes_the_link(
    fake_cflib: FakeCflib, blocking_step: BlockingStep
) -> None:
    fake_cflib.link.wait_for_params.side_effect = blocking_step

    with pytest.raises(TimeoutError, match=r"Reading the parameters took longer than 0\.2 s"):
        real_time_adapter().connect()

    fake_cflib.link.close_link.assert_called_once()


@pytest.mark.usefixtures("short_time_limits")
def test_settling_the_position_estimate_has_a_time_limit_then_closes_the_link(
    fake_cflib: FakeCflib, blocking_step: BlockingStep
) -> None:
    fake_cflib.reset_estimator.side_effect = blocking_step

    with pytest.raises(TimeoutError, match="Check the Flow deck can see the floor"):
        real_time_adapter().connect()

    fake_cflib.link.close_link.assert_called_once()


def test_ctrl_c_while_the_link_opens_gets_through_and_stops_the_connection_under_way(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib, ctrl_c_step: BlockingStep
) -> None:
    fake_cflib.link.open_link.side_effect = ctrl_c_step

    with pytest.raises(KeyboardInterrupt):
        adapter.connect()

    fake_cflib.link.cf.close_link.assert_called_once()


def test_ctrl_c_while_reading_the_parameters_gets_through_and_closes_the_link(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib, ctrl_c_step: BlockingStep
) -> None:
    fake_cflib.link.wait_for_params.side_effect = ctrl_c_step

    with pytest.raises(KeyboardInterrupt):
        adapter.connect()

    fake_cflib.link.close_link.assert_called_once()


def test_a_connect_that_fails_on_its_own_is_left_to_cflib_to_close(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib
) -> None:
    fake_cflib.link.open_link.side_effect = Exception("Couldn't find a Crazyflie")

    with pytest.raises(Exception, match="Couldn't find a Crazyflie"):
        adapter.connect()

    # cflib's open_link closes the link itself before raising.
    fake_cflib.link.cf.close_link.assert_not_called()


def test_any_failing_setup_step_closes_the_link(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib
) -> None:
    fake_cflib.reset_estimator.side_effect = TimeoutError("estimate never settled")

    with pytest.raises(TimeoutError):
        adapter.connect()

    fake_cflib.link.close_link.assert_called_once()


def test_a_missing_log_variable_says_to_update_the_firmware(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib
) -> None:
    fake_cflib.link.cf.log.add_config.side_effect = KeyError("Variable supervisor.info not in TOC")

    with pytest.raises(RuntimeError, match="Update the firmware"):
        adapter.connect()

    fake_cflib.link.close_link.assert_called_once()


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


class BoundedSimClock(SimClock):
    """A sim clock that fails the test instead of letting a broken wait loop forever."""

    MAX_SLEEPS = 1000

    def __init__(self, start: float) -> None:
        super().__init__(start)
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
    adapter = CrazyflieAdapter(BoundedSimClock(start=10.0))

    with pytest.raises(TimeoutError, match=r"Still missing: battery voltage\. Check"):
        adapter.connect()

    fake_cflib.link.close_link.assert_called_once()


def test_ctrl_c_while_waiting_for_telemetry_gets_through_and_closes_the_link(
    fake_cflib: FakeCflib,
) -> None:
    fake_cflib.silent_blocks.add("battery")
    adapter = real_time_adapter()
    press_ctrl_c = threading.Timer(0.2, signal.raise_signal, [signal.SIGINT])
    press_ctrl_c.start()

    started = time.perf_counter()
    try:
        with pytest.raises(KeyboardInterrupt):
            adapter.connect()  # waits up to 3 s for the battery
        assert time.perf_counter() - started < 2.0  # at once, not when the 3 s limit ends it
    finally:
        # If connect() returned early, a later Ctrl+C would stop the whole run.
        press_ctrl_c.cancel()
        press_ctrl_c.join()
    fake_cflib.link.close_link.assert_called_once()


def test_connecting_again_waits_for_new_telemetry_not_the_last_session_s(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib
) -> None:
    adapter.connect()
    adapter.disconnect()
    fake_cflib.silent_blocks.add("battery")

    with pytest.raises(TimeoutError, match="Still missing: battery voltage"):
        adapter.connect()
