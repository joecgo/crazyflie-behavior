"""The hover program (ADR-0030). It runs on the real clock, so the hovers are short."""

import subprocess
import sys
from pathlib import Path

import pytest

from crazyflie_behavior.behaviors import hover_test as hover_test_module
from crazyflie_behavior.behaviors.hover_test import note_pitch
from crazyflie_behavior.drone.interface import DroneInterface
from crazyflie_behavior.drone.mock_adapter import MockAdapter
from crazyflie_behavior.programs import hover as hover_module
from crazyflie_behavior.programs.hover import main
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

    def make_mock_adapter(use_crazyflie: bool, clock: Clock, *, initial_climb_speed: float) -> DroneInterface:
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

    def make_mock_adapter(use_crazyflie: bool, clock: Clock, *, initial_climb_speed: float) -> DroneInterface:
        climb_speeds.append(initial_climb_speed)
        return MockAdapter(clock, initial_climb_speed=initial_climb_speed)

    monkeypatch.setattr(hover_module, "make_drone", make_mock_adapter)

    exit_code = main(["--hover-seconds", "0", "--climb-speed", "0.4"])

    assert exit_code == 0
    assert climb_speeds == [0.4]
    assert "climbing at 0.4 m/s" in the_log_file_text(tmp_path / "logs")


@pytest.mark.parametrize("climb_speed", ["0.05", "0.5", "nan"])
def test_a_climb_speed_outside_the_range_is_refused(climb_speed: str, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as stopped:
        main(["--climb-speed", climb_speed])

    assert stopped.value.code == 2
    assert "--climb-speed: The initial climb speed must be 0.1-0.4 m/s" in capsys.readouterr().err
