"""The hover program (ADR-0030). It runs on the real clock, so the hovers are short."""

import subprocess
import sys
from pathlib import Path

import pytest

from crazyflie_behavior.behaviors import hover_test as hover_test_module
from crazyflie_behavior.behaviors.hover_test import TAKE_OFF_HEIGHT, note_pitch
from crazyflie_behavior.drone.interface import DroneInterface
from crazyflie_behavior.drone.mock_adapter import MockAdapter
from crazyflie_behavior.programs import hover as hover_module
from crazyflie_behavior.programs.hover import main
from crazyflie_behavior.safety.safety_layer import LOW_BATTERY_VOLTAGE
from crazyflie_behavior.snapshot import Snapshot
from crazyflie_behavior.timing.clock import Clock


def the_log_file_text(log_directory: Path) -> str:
    log_files = list(log_directory.glob("*.log"))
    assert len(log_files) == 1
    return log_files[0].read_text(encoding="utf-8")


def test_the_hover_program_flies_the_hover_test_on_the_mock_adapter(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["--hover-seconds", "0.1"])

    assert exit_code == 0
    log_text = the_log_file_text(tmp_path / "logs")
    assert "Hover program, the mock adapter, hovering 0.1 s, climbing at 0.2 m/s" in log_text
    assert "Sending Arm()" in log_text
    assert "Sending TakeOff(height=0.5)" in log_text
    assert "Hovering for 0.1 s" in log_text
    assert "Sending Land()" in log_text
    assert "Hover test: landed. Done." in log_text
    assert "Snapshot: Snapshot(" in log_text  # every snapshot reaches the file
    assert "Tick loop summary" in log_text
    assert "Chirp()" not in log_text  # chirps are off by default


def test_with_chirp_the_buzzer_commands_reach_the_drone(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """On the real clock, so the waits are shortened. "Charge" keeps its length."""
    monkeypatch.chdir(tmp_path)
    for wait in ("FLOOR_CHIRP_WAIT", "LANDED_CHIRP_DELAY", "CHARGE_WAIT", "SILENCE_HOLD"):
        monkeypatch.setattr(hover_test_module, wait, 0.1)
    drones: list[MockAdapter] = []

    def make_mock_adapter(
        use_crazyflie: bool, clock: Clock, *, initial_climb_speed: float, take_off_log: bool
    ) -> DroneInterface:
        drone = MockAdapter(clock, initial_climb_speed=initial_climb_speed)
        drones.append(drone)
        return drone

    monkeypatch.setattr(hover_module, "make_drone", make_mock_adapter)

    exit_code = main(["--hover-seconds", "0.1", "--chirp"])

    assert exit_code == 0
    (drone,) = drones
    buzzer_commands = [command for command in drone.command_log if command in {"chirp", "play_tone", "silence"}]
    # A slow tick may skip a short note, but never the first or the last.
    assert buzzer_commands[:2] == ["chirp", "chirp"]  # on the floor and after landing: the hover is too short for more
    assert set(buzzer_commands[2:-1]) == {"play_tone"}
    assert buzzer_commands[-1] == "silence"
    assert drone.tone_pitches[0] == pytest.approx(note_pitch("G", 4))
    assert drone.tone_pitches[-1] == pytest.approx(note_pitch("G", 5))
    log_text = the_log_file_text(tmp_path / "logs")
    assert "Hover program, the mock adapter, hovering 0.1 s, climbing at 0.2 m/s, with chirps" in log_text
    assert "Hover test: done." in log_text


class SaggingBatteryMockAdapter(MockAdapter):
    """A mock drone whose battery reads below the safety pre-check's limit from the take-off height on."""

    def take_snapshot(self, dt: float) -> Snapshot:
        snapshot = super().take_snapshot(dt)
        position = snapshot.position_estimate
        if position is not None and position.value.z >= TAKE_OFF_HEIGHT:
            self.set_battery_voltage(LOW_BATTERY_VOLTAGE - 0.1)
        return snapshot


def test_a_hover_the_safety_layer_cut_short_exits_with_1(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """ADR-0062, with no line of its own in the log (ADR-0066)."""
    monkeypatch.chdir(tmp_path)

    def make_sagging_drone(
        use_crazyflie: bool, clock: Clock, *, initial_climb_speed: float, take_off_log: bool
    ) -> DroneInterface:
        return SaggingBatteryMockAdapter(clock, initial_climb_speed=initial_climb_speed)

    monkeypatch.setattr(hover_module, "make_drone", make_sagging_drone)

    exit_code = main(["--hover-seconds", "5"])

    assert exit_code == 1
    log_text = the_log_file_text(tmp_path / "logs")
    assert "Safety pre-check failed: battery at" in log_text
    assert "Hover test: hovered" not in log_text
    assert "Hover test failed" not in log_text


class InterruptedWhileConnectingMockAdapter(MockAdapter):
    def connect(self) -> None:
        raise KeyboardInterrupt


class FailingDisconnectMockAdapter(MockAdapter):
    def disconnect(self) -> None:
        super().disconnect()
        raise RuntimeError("made-up disconnect failure")


def test_the_interrupt_signal_while_connecting_still_exits_with_130(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Though the hover test never ran, so it has failed (ADR-0062)."""
    monkeypatch.chdir(tmp_path)

    def make_drone(
        use_crazyflie: bool, clock: Clock, *, initial_climb_speed: float, take_off_log: bool
    ) -> DroneInterface:
        return InterruptedWhileConnectingMockAdapter(clock, initial_climb_speed=initial_climb_speed)

    monkeypatch.setattr(hover_module, "make_drone", make_drone)

    assert main(["--hover-seconds", "0"]) == 130


def test_an_error_after_a_full_hover_still_exits_with_1(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Though the hover test passed (ADR-0062)."""
    monkeypatch.chdir(tmp_path)

    def make_drone(
        use_crazyflie: bool, clock: Clock, *, initial_climb_speed: float, take_off_log: bool
    ) -> DroneInterface:
        return FailingDisconnectMockAdapter(clock, initial_climb_speed=initial_climb_speed)

    monkeypatch.setattr(hover_module, "make_drone", make_drone)

    exit_code = main(["--hover-seconds", "0"])

    assert exit_code == 1
    log_text = the_log_file_text(tmp_path / "logs")
    assert "Hover test: landed. Done." in log_text
    assert "made-up disconnect failure" in log_text


@pytest.mark.parametrize("hover_seconds", ["-1", "nan", "inf"])
def test_a_hover_time_that_is_negative_or_endless_is_refused(
    hover_seconds: str, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as stopped:
        main(["--hover-seconds", hover_seconds])

    assert stopped.value.code == 2  # argparse's exit code for a usage error
    assert "--hover-seconds: Hover duration must be zero or more" in capsys.readouterr().err


def test_the_hover_program_runs_as_a_program(tmp_path: Path) -> None:
    finished = subprocess.run(
        [sys.executable, "-m", "crazyflie_behavior.programs.hover", "--hover-seconds", "0"],
        cwd=tmp_path,
        capture_output=True,
        timeout=60.0,
        check=False,
    )

    assert finished.returncode == 0
    assert "Hover test: landed. Done." in the_log_file_text(tmp_path / "logs")


def test_climb_speed_reaches_the_drone_and_the_log(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    climb_speeds: list[float] = []

    def make_mock_adapter(
        use_crazyflie: bool, clock: Clock, *, initial_climb_speed: float, take_off_log: bool
    ) -> DroneInterface:
        climb_speeds.append(initial_climb_speed)
        return MockAdapter(clock, initial_climb_speed=initial_climb_speed)

    monkeypatch.setattr(hover_module, "make_drone", make_mock_adapter)

    exit_code = main(["--hover-seconds", "0", "--climb-speed", "0.4"])

    assert exit_code == 0
    assert climb_speeds == [0.4]
    assert "climbing at 0.4 m/s" in the_log_file_text(tmp_path / "logs")


@pytest.mark.parametrize(("arguments", "expected"), [([], False), (["--take-off-log"], True)])
def test_the_take_off_log_option_reaches_make_drone_and_the_description(
    arguments: list[str], expected: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    take_off_logs: list[bool] = []
    descriptions: list[str] = []

    def make_mock_adapter(
        use_crazyflie: bool, clock: Clock, *, initial_climb_speed: float, take_off_log: bool
    ) -> DroneInterface:
        take_off_logs.append(take_off_log)
        return MockAdapter(clock, initial_climb_speed=initial_climb_speed)

    def record_the_description(program_name: str, description: str, *_rest: object) -> int:
        descriptions.append(description)
        return 0

    monkeypatch.setattr(hover_module, "make_drone", make_mock_adapter)
    monkeypatch.setattr(hover_module, "run_program", record_the_description)

    main(arguments)

    assert take_off_logs == [expected]
    assert descriptions[0].endswith(", with the take-off block (the mock adapter has none)") == expected


@pytest.mark.parametrize("climb_speed", ["0.05", "0.5", "nan"])
def test_a_climb_speed_outside_the_range_is_refused(climb_speed: str, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as stopped:
        main(["--climb-speed", climb_speed])

    assert stopped.value.code == 2
    assert "--climb-speed: The initial climb speed must be 0.1-0.4 m/s" in capsys.readouterr().err
