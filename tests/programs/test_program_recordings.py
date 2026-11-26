"""Each program records its run (ADR-0088): its name, adapter and arguments, and what each tick saw."""

from collections.abc import Callable
from pathlib import Path

import pytest

from crazyflie_behavior.programs import bench, failsafe, hover, rescue_landing
from crazyflie_behavior.recording.encoding import Recording, read_recording
from crazyflie_behavior.timing.clock import Clock, SimClock


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


@pytest.mark.usefixtures("bench_interrupted_on_its_third_tick")
def test_the_bench_program_records_its_run_with_every_snapshot_and_no_requests(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, sim_clock: SimClock
) -> None:
    monkeypatch.chdir(tmp_path)

    assert bench.main([], clock=sim_clock) == 0

    recording = the_recording(tmp_path)
    assert recording.header.program == "bench"
    assert recording.header.adapter == "mock"
    assert recording.header.arguments == ()
    assert len(recording.ticks) == 4  # the stop request ends the run on the next tick
    assert all(tick.snapshot is not None and tick.requests == () for tick in recording.ticks)
    assert recording.last_line is not None
