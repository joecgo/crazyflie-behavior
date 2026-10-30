"""The hover program (ADR-0030). It runs on the real clock, so the hovers are short."""

import subprocess
import sys
from pathlib import Path

import pytest

from crazyflie_behavior.programs.hover import main


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
    assert "Hover program, the mock adapter, hovering 0.1 s" in log_text
    assert "Sending Arm()" in log_text
    assert "Sending TakeOff(height=0.5)" in log_text
    assert "Hovering for 0.1 s" in log_text
    assert "Sending Land()" in log_text
    assert "Hover test: landed. Done." in log_text
    assert "Snapshot: Snapshot(" in log_text  # every snapshot reaches the file
    assert "Tick loop summary" in log_text


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
