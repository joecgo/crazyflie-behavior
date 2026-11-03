"""The rescue landing program (ADR-0038). It runs on the real clock, on the mock adapter."""

import subprocess
import sys
from pathlib import Path

import pytest

from crazyflie_behavior.programs.rescue_landing import main


def the_log_file_text(log_directory: Path) -> str:
    log_files = list(log_directory.glob("*.log"))
    assert len(log_files) == 1
    return log_files[0].read_text(encoding="utf-8")


def test_the_rescue_landing_program_lands_the_hovering_mock_drone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main([])

    assert exit_code == 0
    log_text = the_log_file_text(tmp_path / "logs")
    assert "Rescue landing program, the mock adapter" in log_text
    assert "Sending Land()" in log_text
    assert "Rescue landing: the drone reports it's no longer flying. Done." in log_text
    assert "Sending Arm()" not in log_text  # it never arms or takes off
    assert "Sending TakeOff" not in log_text


def test_the_rescue_landing_program_runs_as_a_program(tmp_path: Path) -> None:
    finished = subprocess.run(
        [sys.executable, "-m", "crazyflie_behavior.programs.rescue_landing"],
        cwd=tmp_path,
        capture_output=True,
        timeout=60.0,
        check=False,
    )

    assert finished.returncode == 0
    assert "Done." in the_log_file_text(tmp_path / "logs")
