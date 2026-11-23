"""Each program records its run (ADR-0088): its name, adapter and arguments, and what each tick saw."""

import signal
from collections.abc import Callable
from pathlib import Path

import pytest

from crazyflie_behavior.drone.interface import DroneInterface
from crazyflie_behavior.programs import bench, failsafe, hover, rescue_landing
from crazyflie_behavior.programs.bench import BenchTickStep
from crazyflie_behavior.recording.encoding import Recording, read_recording
from crazyflie_behavior.recording.recorder import Recorder
from crazyflie_behavior.timing.clock import Clock, SimClock

GIVE_UP_AFTER_TICKS = 100
"""The bench tick step below reports done after this many ticks, so a broken stop request fails instead of hanging."""


class InterruptSignalOnThirdTick(BenchTickStep):
    """The bench tick step, with the interrupt signal on its third tick: the bench runs until one."""

    def __init__(self, drone: DroneInterface, recorder: Recorder | None = None) -> None:
        super().__init__(drone, recorder)
        self._ticks_run = 0

    def run(self, time: float, dt: float) -> bool:
        done = super().run(time, dt)
        self._ticks_run += 1
        if self._ticks_run == 3:
            signal.raise_signal(signal.SIGINT)
        return done or self._ticks_run >= GIVE_UP_AFTER_TICKS


def the_recording(tmp_path: Path) -> Recording:
    [path] = (tmp_path / "recordings").glob("*.jsonl")
    return read_recording(path)


@pytest.mark.parametrize(
    ("main", "arguments", "program_name"),
    [
        (hover.main, ["--hover-seconds", "0.1"], "hover"),
        (failsafe.main, ["--fault-at", "hover"], "failsafe"),
        (rescue_landing.main, [], "rescue_landing"),
    ],
    ids=["hover", "failsafe", "rescue landing"],
)
def test_each_flying_program_records_its_run_with_every_snapshot_and_request(
    main: Callable[..., int],
    arguments: list[str],
    program_name: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    sim_clock: Clock,
) -> None:
    monkeypatch.chdir(tmp_path)

    main(arguments, clock=sim_clock)

    recording = the_recording(tmp_path)
    assert recording.header.program == program_name
    assert recording.header.adapter == "mock"
    assert recording.header.arguments == tuple(arguments)
    assert recording.ticks
    assert all(tick.snapshot is not None for tick in recording.ticks)
    assert any(tick.requests for tick in recording.ticks)
    assert recording.last_line is not None


def test_the_bench_program_records_its_run_with_every_snapshot_and_no_requests(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, sim_clock: SimClock
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(bench, "BenchTickStep", InterruptSignalOnThirdTick)

    assert bench.main([], clock=sim_clock) == 0

    recording = the_recording(tmp_path)
    assert recording.header.program == "bench"
    assert recording.header.adapter == "mock"
    assert recording.header.arguments == ()
    assert len(recording.ticks) == 4  # the stop request ends the run on the next tick
    assert all(tick.snapshot is not None and tick.requests == () for tick in recording.ticks)
    assert recording.last_line is not None
