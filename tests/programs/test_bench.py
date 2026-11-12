"""The bench program (ADR-0028)."""

import logging
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

from crazyflie_behavior.drone.interface import DroneInterface
from crazyflie_behavior.drone.mock_adapter import MockAdapter
from crazyflie_behavior.programs import bench as bench_module
from crazyflie_behavior.programs.bench import BenchTickStep, main, snapshot_summary
from crazyflie_behavior.snapshot import RangeDirection, RangeReading, RangeReadings, Snapshot
from crazyflie_behavior.timing.clock import Clock, SimClock

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


class UpdateRecordingMock(MockAdapter):
    def __init__(self, clock: SimClock) -> None:
        super().__init__(clock)
        self.updated_with: list[Snapshot] = []
        self.snapshots: list[Snapshot] = []

    def take_snapshot(self, dt: float) -> Snapshot:
        self.snapshots.append(super().take_snapshot(dt))
        return self.snapshots[-1]

    def update_take_off_and_landing(self, snapshot: Snapshot) -> None:
        self.updated_with.append(snapshot)
        super().update_take_off_and_landing(snapshot)


def test_the_bench_tick_step_updates_take_off_and_landing_with_each_snapshot() -> None:
    # As every tick step does (ADR-0055); on the bench there is nothing to update.
    clock = SimClock()
    drone = UpdateRecordingMock(clock)
    drone.connect()

    run_ticks(BenchTickStep(drone), clock, tick_count=3)

    assert len(drone.updated_with) == 3
    assert drone.updated_with == drone.snapshots


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

    summary = snapshot_summary(drone.take_snapshot(0.25))

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
        velocity_uncertainty=None,
        range_readings=no_readings,
        battery_voltage=None,
        drone_status=None,
        is_in_initial_climb=False,
        may_be_flying=False,
    )

    summary = snapshot_summary(snapshot)

    assert "position no reading yet" in summary
    assert "battery no reading yet" in summary
    assert "down no reading yet" in summary


def test_the_summary_covers_every_range_direction() -> None:
    clock = SimClock()

    summary = snapshot_summary(connected_mock(clock).take_snapshot(0.0))

    for direction in RangeDirection:
        assert f"| {direction.value} " in summary
    assert "| down 0.02 m" in summary  # the mock's floor reading (ADR-0052); the others are clear


def test_the_summary_marks_an_invalid_range_reading() -> None:
    clock = SimClock()
    drone = connected_mock(clock)
    drone.set_range_reading(RangeDirection.UP, RangeReading.invalid())

    summary = snapshot_summary(drone.take_snapshot(0.0))

    assert "up invalid" in summary


# --- The program ------------------------------------------------------------------


class InterruptSignalOnThirdTick(BenchTickStep):
    """The bench tick step, with the interrupt signal sent on its third tick."""

    def __init__(self, drone: DroneInterface) -> None:
        super().__init__(drone)
        self._ticks_run = 0

    def run(self, time: float, dt: float) -> bool:
        done = super().run(time, dt)
        self._ticks_run += 1
        if self._ticks_run == 3:
            signal.raise_signal(signal.SIGINT)
        return done or self._ticks_run >= GIVE_UP_AFTER_TICKS


def test_the_bench_program_runs_with_the_mock_adapter_until_the_interrupt_signal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(bench_module, "BenchTickStep", InterruptSignalOnThirdTick)

    try:
        exit_code = main([])
    except KeyboardInterrupt:
        pytest.fail("The interrupt signal raised KeyboardInterrupt instead of making a stop request")

    assert exit_code == 0
    log_text = the_log_file_text(tmp_path / "logs")
    assert "Bench program, the mock adapter" in log_text
    assert "Snapshot: Snapshot(" in log_text  # the debug lines reach the file
    assert "The interrupt signal made the stop request" in log_text
    assert "Tick loop summary: ticks: 3" in log_text


@pytest.mark.parametrize(("arguments", "expected"), [([], False), (["--take-off-log"], True)])
def test_the_take_off_log_option_reaches_make_drone_and_the_description(
    arguments: list[str], expected: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With it, the Crazyflie adapter runs the take-off block at connect: the Bench measures its load (ADR-0063)."""
    take_off_logs: list[bool] = []
    descriptions: list[str] = []

    def make_mock_adapter(use_crazyflie: bool, clock: Clock, *, take_off_log: bool) -> DroneInterface:
        take_off_logs.append(take_off_log)
        return MockAdapter(clock)

    def record_the_description(program_name: str, description: str, *_rest: object) -> int:
        descriptions.append(description)
        return 0

    monkeypatch.setattr(bench_module, "make_drone", make_mock_adapter)
    monkeypatch.setattr(bench_module, "run_program", record_the_description)

    assert main(arguments) == 0
    assert take_off_logs == [expected]
    assert descriptions[0].endswith(", with the take-off block (the mock adapter has none)") == expected


@pytest.mark.skipif(
    sys.platform == "win32", reason="sending the interrupt signal to another process works differently on Windows"
)
def test_the_bench_program_runs_as_a_program_and_stops_on_the_interrupt_signal(tmp_path: Path) -> None:
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
    assert "The interrupt signal made the stop request" in log_text
    assert "Tick loop summary" in log_text
