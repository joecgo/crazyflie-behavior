"""The bench program (ADR-0028)."""

import logging
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

from crazyflie_behavior.drone.crazyflie.adapter import CrazyflieAdapter
from crazyflie_behavior.drone.interface import DroneInterface
from crazyflie_behavior.drone.mock_adapter import MockAdapter
from crazyflie_behavior.programs import bench as bench_module
from crazyflie_behavior.programs.bench import (
    BenchTickStep,
    main,
    make_drone,
    snapshot_summary,
)
from crazyflie_behavior.snapshot import RangeDirection, RangeReading, RangeReadings, Snapshot
from crazyflie_behavior.timing.clock import SimClock

BENCH_LOGGER = "crazyflie_behavior.programs.bench"
TICK_PERIOD = 0.25
"""Quarter-second ticks keep every time exact in binary."""
GIVE_UP_AFTER_TICKS = 100
"""A fake that would otherwise tick forever reports done after this many ticks."""


def connected_mock(clock: SimClock) -> MockAdapter:
    drone = MockAdapter(clock)
    drone.connect()
    return drone


def run_ticks(tick_step: BenchTickStep, clock: SimClock, tick_count: int) -> None:
    for _ in range(tick_count):
        tick_step.run(clock.now(), TICK_PERIOD)
        clock.advance(TICK_PERIOD)


def the_log_file_text(log_directory: Path) -> str:
    log_files = list(log_directory.glob("*.log"))
    assert len(log_files) == 1
    return log_files[0].read_text(encoding="utf-8")


def wait_for_log_line(log_directory: Path, text: str, timeout: float) -> None:
    """Wait, in real time, until a log file in the directory contains `text`."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        for log_file in log_directory.glob("*.log"):
            if text in log_file.read_text(encoding="utf-8"):
                return
        time.sleep(0.05)
    pytest.fail(f"No log line with {text!r} within {timeout} s")


# --- The bench tick step ----------------------------------------------------------


def test_the_bench_tick_step_never_commands_the_drone() -> None:
    clock = SimClock()
    drone = connected_mock(clock)

    run_ticks(BenchTickStep(drone), clock, tick_count=40)

    assert drone.command_log == ["connect"]


def test_every_snapshot_goes_to_the_log_at_debug_level(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG, logger=BENCH_LOGGER)
    clock = SimClock()

    run_ticks(BenchTickStep(connected_mock(clock)), clock, tick_count=3)

    debug_messages = [r.getMessage() for r in caplog.records if r.levelno == logging.DEBUG]
    assert len(debug_messages) == 3
    assert all(message.startswith("Snapshot: Snapshot(") for message in debug_messages)


def test_the_console_gets_a_summary_once_a_second(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger=BENCH_LOGGER)
    clock = SimClock()

    # Ticks at 0, 0.25, ..., 2.0 s: summaries at 0, 1 and 2 s.
    run_ticks(BenchTickStep(connected_mock(clock)), clock, tick_count=9)

    assert len([r for r in caplog.records if r.levelno == logging.INFO]) == 3


# --- The summary ----------------------------------------------------------------


def test_the_summary_shows_each_value_and_how_old_it_is() -> None:
    clock = SimClock(start=10.0)
    drone = connected_mock(clock)
    clock.advance(0.125)
    drone.set_range_reading(RangeDirection.DOWN, RangeReading.at_distance(0.03))
    drone.stop_telemetry()  # nothing more arrives
    clock.advance(0.125)

    summary = snapshot_summary(drone.take_snapshot(clock.now(), 0.25))

    assert "position 0.00, 0.00, 0.00 m (250 ms old)" in summary
    assert "velocity 0.00, 0.00, 0.00 m/s (250 ms old)" in summary
    assert "battery 4.00 V (250 ms old)" in summary
    assert "status armed no, flying no, crashed no, tumbled no" in summary
    assert "front out of range (250 ms old)" in summary
    assert "down 0.03 m (125 ms old)" in summary


def test_the_summary_says_when_a_value_has_not_arrived_yet() -> None:
    no_readings = RangeReadings(None, None, None, None, None, None)
    snapshot = Snapshot(
        time=0.0,
        dt=0.0,
        position_estimate=None,
        velocity_estimate=None,
        range_readings=no_readings,
        battery_voltage=None,
        drone_status=None,
    )

    summary = snapshot_summary(snapshot)

    assert "position no reading yet" in summary
    assert "battery no reading yet" in summary
    assert "down no reading yet" in summary


def test_the_summary_covers_every_range_direction() -> None:
    clock = SimClock()

    summary = snapshot_summary(connected_mock(clock).take_snapshot(clock.now(), 0.0))

    for direction in RangeDirection:
        assert f"| {direction.value} out of range" in summary


def test_the_summary_marks_an_invalid_range_reading() -> None:
    clock = SimClock()
    drone = connected_mock(clock)
    drone.set_range_reading(RangeDirection.UP, RangeReading.invalid())

    summary = snapshot_summary(drone.take_snapshot(clock.now(), 0.0))

    assert "up invalid" in summary


# --- The program ------------------------------------------------------------------


def test_the_mock_adapter_is_the_default_and_the_crazyflie_needs_the_flag() -> None:
    clock = SimClock()

    assert isinstance(make_drone(use_crazyflie=False, clock=clock), MockAdapter)
    assert isinstance(make_drone(use_crazyflie=True, clock=clock), CrazyflieAdapter)


class CtrlCOnThirdTick(BenchTickStep):
    """The bench tick step, with Ctrl+C pressed on its third tick."""

    def __init__(self, drone: DroneInterface) -> None:
        super().__init__(drone)
        self._ticks_run = 0

    def run(self, time: float, dt: float) -> bool:
        done = super().run(time, dt)
        self._ticks_run += 1
        if self._ticks_run == 3:
            signal.raise_signal(signal.SIGINT)
        return done or self._ticks_run >= GIVE_UP_AFTER_TICKS


def test_the_bench_program_runs_with_the_mock_adapter_until_ctrl_c(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(bench_module, "BenchTickStep", CtrlCOnThirdTick)

    try:
        exit_code = main([])
    except KeyboardInterrupt:
        pytest.fail("Ctrl+C raised KeyboardInterrupt instead of making a stop request")

    assert exit_code == 0
    log_text = the_log_file_text(tmp_path / "logs")
    assert "Bench program, the mock adapter" in log_text
    assert "Snapshot: Snapshot(" in log_text  # the debug lines reach the file
    assert "Ctrl+C made the stop request" in log_text
    assert "Tick loop summary: ticks: 3" in log_text


def test_ctrl_c_while_connecting_ends_the_bench_program_with_exit_code_130(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    def interrupted(*_arguments: object) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(bench_module, "run_tick_loop", interrupted)

    assert main([]) == 130
    assert "stopped before the tick loop started" in the_log_file_text(tmp_path / "logs")


def test_an_error_that_ctrl_c_interrupted_still_goes_to_the_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    def interrupted_while_failing(*_arguments: object) -> None:
        try:
            raise RuntimeError("Flow deck not detected")
        except RuntimeError as error:
            raise KeyboardInterrupt from error

    monkeypatch.setattr(bench_module, "run_tick_loop", interrupted_while_failing)

    assert main([]) == 130
    assert "Flow deck not detected" in the_log_file_text(tmp_path / "logs")


def test_an_error_ends_the_bench_program_with_exit_code_1_and_goes_to_the_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    def broken(*_arguments: object) -> None:
        raise RuntimeError("the radio is gone")

    monkeypatch.setattr(bench_module, "run_tick_loop", broken)

    assert main([]) == 1
    log_text = the_log_file_text(tmp_path / "logs")
    assert "The bench program stopped with an error" in log_text
    assert "the radio is gone" in log_text


@pytest.mark.skipif(
    sys.platform == "win32", reason="sending Ctrl+C to another process works differently on Windows"
)
def test_the_bench_program_runs_as_a_program_and_stops_on_ctrl_c(tmp_path: Path) -> None:
    program = subprocess.Popen(
        [sys.executable, "-m", "crazyflie_behavior.programs.bench"],
        cwd=tmp_path,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        wait_for_log_line(tmp_path / "logs", "Tick loop starting", timeout=20.0)
        program.send_signal(signal.SIGINT)
        exit_code = program.wait(timeout=20.0)
    finally:
        if program.poll() is None:
            program.kill()

    assert exit_code == 0
    log_text = the_log_file_text(tmp_path / "logs")
    assert "Snapshot: Snapshot(" in log_text  # debug lines reach the file when run as a program
    assert "Ctrl+C made the stop request" in log_text
    assert "Tick loop summary" in log_text
