"""The propeller test script, against a fake Crazyflie.

tools/ isn't a package that project code or tests import, so the script is
loaded from its path.
"""

import importlib.util
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock

import pytest

from crazyflie_behavior.drone.crazyflie.adapter import DEFAULT_URI

SCRIPT = Path(__file__).resolve().parents[2] / "tools" / "propeller_test.py"
TIME_LIMIT = 0.05


def load_script() -> ModuleType:
    specification = importlib.util.spec_from_file_location("propeller_test", SCRIPT)
    assert specification is not None
    assert specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


class FakeLogConfig:
    """A log block that sends `first_count` when started, and later counts on request."""

    def __init__(self, first_count: int | None) -> None:
        self.first_count = first_count
        self.variables: list[tuple[str, str]] = []
        self.callbacks: list[Callable[[int, dict[str, int], object], None]] = []
        self.data_received_cb = MagicMock()
        self.data_received_cb.add_callback.side_effect = self.callbacks.append
        self.is_started = False

    def add_variable(self, name: str, fetch_as: str) -> None:
        self.variables.append((name, fetch_as))

    def start(self) -> None:
        self.is_started = True
        if self.first_count is not None:
            self.send(self.first_count)

    def stop(self) -> None:
        self.is_started = False

    def send(self, count: int) -> None:
        for callback in self.callbacks:
            callback(0, {"health.motorTestCount": count}, self)


class FakeDrone:
    """Stands in for cflib's connection; `on_start_test` sets what the drone does when the test starts."""

    def __init__(self, script: ModuleType, monkeypatch: pytest.MonkeyPatch) -> None:
        self.first_count: int | None = 3
        self.blocks: list[FakeLogConfig] = []
        self.console_callbacks: list[Callable[[str], None]] = []
        self.crazyflie = MagicMock()
        self.crazyflie.console.receivedChar.add_callback.side_effect = self.console_callbacks.append
        sync_crazyflie = MagicMock()
        sync_crazyflie.__enter__.return_value.cf = self.crazyflie
        self.sync_crazyflie_class = MagicMock(return_value=sync_crazyflie)
        monkeypatch.setattr(script.cflib.crtp, "init_drivers", MagicMock())
        monkeypatch.setattr(script, "SyncCrazyflie", self.sync_crazyflie_class)
        monkeypatch.setattr(script, "Crazyflie", MagicMock())
        monkeypatch.setattr(script, "LogConfig", self._log_config)

    def _log_config(self, name: str, period_in_ms: int) -> FakeLogConfig:
        block = FakeLogConfig(self.first_count)
        self.blocks.append(block)
        return block

    @property
    def block(self) -> FakeLogConfig:
        assert len(self.blocks) == 1
        return self.blocks[0]

    def on_start_test(self, action: Callable[[], None]) -> None:
        def set_value(_name: str, _value: int) -> None:
            action()

        self.crazyflie.param.set_value.side_effect = set_value

    def print_console(self, text: str) -> None:
        for callback in self.console_callbacks:
            callback(text)


@pytest.fixture
def script() -> ModuleType:
    return load_script()


@pytest.fixture
def drone(script: ModuleType, monkeypatch: pytest.MonkeyPatch) -> FakeDrone:
    return FakeDrone(script, monkeypatch)


def run(script: ModuleType, uri: str = DEFAULT_URI) -> bool:
    result: bool = script.run_propeller_test(uri, time_limit=TIME_LIMIT, console_wait=0.0)
    return result


def test_it_starts_the_test_and_reports_its_end_when_the_count_goes_up(script: ModuleType, drone: FakeDrone) -> None:
    drone.on_start_test(lambda: drone.block.send(4))

    assert run(script) is True
    drone.crazyflie.param.set_value.assert_called_once_with("health.startPropTest", 1)
    assert drone.block.variables == [("health.motorTestCount", "uint16_t")]
    assert not drone.block.is_started


def test_it_reports_no_end_while_the_count_stays_the_same(script: ModuleType, drone: FakeDrone) -> None:
    drone.on_start_test(lambda: drone.block.send(3))

    assert run(script) is False


def test_it_starts_nothing_until_it_has_the_count_from_before_the_test(script: ModuleType, drone: FakeDrone) -> None:
    drone.first_count = None

    assert run(script) is False
    drone.crazyflie.param.set_value.assert_not_called()


def test_it_prints_the_drones_console(script: ModuleType, drone: FakeDrone, capsys: pytest.CaptureFixture[str]) -> None:
    def end_with_a_result() -> None:
        drone.print_console("Motor M1 variance X+Y: 1.23 (Z:0.45), voltage sag:0.10\n")
        drone.block.send(4)

    drone.on_start_test(end_with_a_result)

    run(script)

    assert "Motor M1 variance X+Y: 1.23" in capsys.readouterr().out


def test_it_connects_to_the_uri_it_was_given(script: ModuleType, drone: FakeDrone) -> None:
    drone.on_start_test(lambda: drone.block.send(4))

    run(script, "radio://0/90/2M/E7E7E7E7E8")

    assert drone.sync_crazyflie_class.call_args.args == ("radio://0/90/2M/E7E7E7E7E8",)


def test_its_default_uri_is_the_adapters(script: ModuleType) -> None:
    assert script.DEFAULT_URI == DEFAULT_URI


def test_main_exits_1_and_says_why_when_the_test_does_not_end(
    script: ModuleType, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(script, "run_propeller_test", MagicMock(return_value=False))

    assert script.main([]) == 1
    assert "didn't end" in capsys.readouterr().err


def test_main_exits_0_when_the_test_ends(script: ModuleType, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(script, "run_propeller_test", MagicMock(return_value=True))

    assert script.main([]) == 0
