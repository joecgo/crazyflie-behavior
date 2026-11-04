"""The failsafe program (ADR-0041), on the mock adapter and the real clock, with the hovers patched short."""

from pathlib import Path

import pytest

from crazyflie_behavior.behaviors import failsafe_test as failsafe_test_module
from crazyflie_behavior.drone.interface import DroneInterface
from crazyflie_behavior.drone.mock_adapter import MockAdapter
from crazyflie_behavior.geometry import Vector3
from crazyflie_behavior.programs import failsafe as failsafe_module
from crazyflie_behavior.programs import failsafe_fault as failsafe_fault_module
from crazyflie_behavior.programs.failsafe import main
from crazyflie_behavior.timing.clock import Clock

SHORT_HOVER = 0.2
"""Seconds of hovering before the fault, in place of the 3 s a field test uses."""


class LandingFailsMockAdapter(MockAdapter):
    """A mock drone whose landing in `disconnect()` fails, as when the Crazyflie adapter's landing raises."""

    def disconnect(self) -> None:
        super().disconnect()
        raise RuntimeError("the landing failed")


class MockAdapterMaker:
    """Stands in for `make_drone`: builds the mock adapter and keeps it for the test to inspect."""

    def __init__(self) -> None:
        self.mock_adapter: MockAdapter | None = None
        self.adapter_class: type[MockAdapter] = MockAdapter
        self.battery_voltage: float | None = None
        """If set, the mock drone starts with this battery voltage in place of a charged one."""

    def __call__(self, use_crazyflie: bool, clock: Clock) -> DroneInterface:
        assert not use_crazyflie
        self.mock_adapter = self.adapter_class(clock)
        if self.battery_voltage is not None:
            self.mock_adapter.set_battery_voltage(self.battery_voltage)
        return self.mock_adapter

    @property
    def adapter(self) -> MockAdapter:
        assert self.mock_adapter is not None
        return self.mock_adapter


@pytest.fixture
def mock_adapter_maker(monkeypatch: pytest.MonkeyPatch) -> MockAdapterMaker:
    mock_adapter_maker = MockAdapterMaker()
    monkeypatch.setattr(failsafe_module, "make_drone", mock_adapter_maker)
    monkeypatch.setattr(failsafe_fault_module, "HOVER_DURATION_BEFORE_FAULT", SHORT_HOVER)
    return mock_adapter_maker


def the_log_file_text(log_directory: Path) -> str:
    log_files = list(log_directory.glob("*.log"))
    assert len(log_files) == 1
    return log_files[0].read_text(encoding="utf-8")


def assert_landed_with_the_motors_off(mock_adapter: MockAdapter) -> None:
    snapshot = mock_adapter.take_snapshot(0.0, 0.0)
    assert snapshot.drone_status is not None
    assert snapshot.position_estimate is not None
    assert not snapshot.drone_status.value.is_flying
    assert snapshot.position_estimate.value.z == 0.0
    assert snapshot.velocity_estimate is not None
    assert snapshot.velocity_estimate.value == Vector3.ZERO


@pytest.mark.parametrize(("height", "test_name"), [("0.1", "Failsafe low"), ("0.5", "Failsafe high")])
def test_the_failsafe_lands_the_drone_after_the_forged_low_battery(
    height: str, test_name: str, mock_adapter_maker: MockAdapterMaker, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["--height-meters", height])

    assert exit_code == 0
    log_text = the_log_file_text(tmp_path / "logs")
    assert f"Failsafe program, the mock adapter, {test_name} ({height} m)" in log_text
    assert f"Sending TakeOff(height={height})" in log_text
    assert log_text.count("FAULT INJECTED: battery voltage forged") == 1
    assert "Safety pre-check failed: battery at 3.20 V (land below 3.40 V). Landing." in log_text
    assert "Sending Land()" in log_text
    assert "Failsafe test failed" not in log_text
    assert mock_adapter_maker.adapter.command_log.count("land") >= 1
    assert_landed_with_the_motors_off(mock_adapter_maker.adapter)


def test_the_failsafe_is_the_real_one_so_the_forged_battery_is_the_only_thing_that_fails(
    mock_adapter_maker: MockAdapterMaker, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    main(["--height-meters", "0.5"])

    log_text = the_log_file_text(tmp_path / "logs")
    pre_check_lines = [line for line in log_text.splitlines() if "Safety pre-check failed" in line]
    assert len(pre_check_lines) == 1
    assert "; " not in pre_check_lines[0]  # one failure, not several


def test_a_fault_that_never_takes_effect_lands_normally_and_fails_the_test(
    mock_adapter_maker: MockAdapterMaker, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A fault that never takes effect (a drone that injects nothing) must fail the test: the time limit lands it."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(failsafe_fault_module, "HOVER_DURATION_BEFORE_FAULT", 1000.0)
    monkeypatch.setattr(failsafe_test_module, "HOVER_TIME_LIMIT", 0.3)

    exit_code = main(["--height-meters", "0.5"])

    assert exit_code == 1
    log_text = the_log_file_text(tmp_path / "logs")
    assert "FAULT INJECTED" not in log_text
    assert "Failsafe test failed: the failsafe didn't land the drone within 0.3 s of hovering" in log_text
    assert "Sending Land()" in log_text  # the normal landing
    assert "Safety pre-check failed" not in log_text
    assert_landed_with_the_motors_off(mock_adapter_maker.adapter)


def test_a_real_fault_before_the_forged_one_does_not_pass_the_test(
    mock_adapter_maker: MockAdapterMaker, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The failsafe fires, but not for the injected fault, so it proves nothing about that one."""
    monkeypatch.chdir(tmp_path)
    mock_adapter_maker.battery_voltage = 3.0  # really low from the start

    exit_code = main(["--height-meters", "0.5"])

    assert exit_code == 1
    log_text = the_log_file_text(tmp_path / "logs")
    assert "Safety pre-check failed: battery at 3.00 V" in log_text
    assert "FAULT INJECTED" not in log_text


@pytest.mark.parametrize("height", ["0.3", "0", "1.0", "abc"])
def test_only_the_two_failsafe_heights_are_accepted(height: str, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as stopped:
        main(["--height-meters", height])

    assert stopped.value.code == 2  # argparse's exit code for a usage error
    assert "--height-meters" in capsys.readouterr().err


def test_the_height_is_required(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as stopped:
        main([])

    assert stopped.value.code == 2
    assert "--height-meters" in capsys.readouterr().err


def test_a_landing_that_fails_in_disconnect_makes_the_exit_code_1_even_though_the_failsafe_fired(
    mock_adapter_maker: MockAdapterMaker, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exit code 0 includes `disconnect()` returning (ADR-0041): the failsafe firing is not enough."""
    monkeypatch.chdir(tmp_path)
    mock_adapter_maker.adapter_class = LandingFailsMockAdapter

    exit_code = main(["--height-meters", "0.5"])

    assert exit_code == 1
    log_text = the_log_file_text(tmp_path / "logs")
    assert "FAULT INJECTED: battery voltage forged" in log_text  # the failsafe did fire
    assert "the landing failed" in log_text
