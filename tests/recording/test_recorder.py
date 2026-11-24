"""The recorder (ADR-0034, ADR-0087, ADR-0088): one run's recording, and errors that never stop a flight."""

import errno
import io
import logging
import math
import re
from collections.abc import Callable
from pathlib import Path

import pytest

from crazyflie_behavior.geometry import Vector3
from crazyflie_behavior.recording import recorder as recorder_module
from crazyflie_behavior.recording.encoding import (
    FORMAT_VERSION,
    CodeVersion,
    Json,
    LastLine,
    RecordedError,
    RecordedTick,
    RecordingHeader,
    RequestAndVerdict,
    read_recording,
)
from crazyflie_behavior.recording.recorder import Recorder, code_version_from_git_status, read_code_version
from crazyflie_behavior.safety.requests import Arm, Hover, Land, TakeOff, Verdict
from crazyflie_behavior.safety.safety_layer import FlightEndReason, ReplacedRequest, SafetyEvents
from crazyflie_behavior.snapshot import RangeReading, RangeReadings, Snapshot, Stamped

RECORDER_LOGGER = "crazyflie_behavior.recording.recorder"
CODE_VERSION = CodeVersion("0123abc", True)
NO_EVENTS = SafetyEvents(pre_check_failures=(), replaced_requests=())


def snapshot_at(time: float) -> Snapshot:
    """A snapshot of a drone on the floor, taken at `time`."""
    return Snapshot(
        time=time,
        dt=0.05,
        position_estimate=Stamped(Vector3.ZERO, arrival_time=time, drone_time=None),
        velocity_estimate=Stamped(Vector3.ZERO, arrival_time=time, drone_time=None),
        velocity_uncertainty=None,
        range_readings=RangeReadings(
            front=None,
            back=None,
            left=None,
            right=None,
            up=None,
            down=Stamped(RangeReading.at_distance(0.01), arrival_time=time, drone_time=None),
        ),
        battery_voltage=Stamped(4.0, arrival_time=time, drone_time=None),
        previous_battery_voltage=None,
        drone_status=None,
        is_in_initial_climb=False,
        may_be_flying=False,
    )


def started_recorder(path: Path) -> Recorder:
    recorder = Recorder("mock", ["--hover-seconds", "0.1"])
    recorder.start(path, "hover", CODE_VERSION)
    return recorder


def record_ticks(recorder: Recorder, count: int) -> None:
    """Hand over and write `count` ticks, each with one request, as the tick step and the tick loop do."""
    for tick_number in range(count):
        recorder.record_request(Hover(), Verdict.approved())
        recorder.record_tick(snapshot_at(tick_number * 0.05), NO_EVENTS, None)
        recorder.write_tick(0.0, 0.002)


def records_at(caplog: pytest.LogCaptureFixture, level: int) -> list[logging.LogRecord]:
    return [record for record in caplog.records if record.name == RECORDER_LOGGER and record.levelno == level]


# --- Recording a run ------------------------------------------------------------------


def test_a_run_reads_back_as_it_was_recorded(tmp_path: Path) -> None:
    path = tmp_path / "recordings" / "run.jsonl"
    recorder = started_recorder(path)
    replaced = SafetyEvents(pre_check_failures=(), replaced_requests=(ReplacedRequest("movement", Hover(), Land()),))
    pre_check_failed = SafetyEvents(pre_check_failures=("battery at 3.10 V (land below 3.20 V)",), replaced_requests=())

    recorder.record_request(Hover(), Verdict.approved())
    recorder.record_request(Land(), Verdict.approved())
    recorder.record_tick(snapshot_at(0.0), replaced, None)
    recorder.write_tick(0.001, 0.002)
    recorder.record_tick(snapshot_at(0.05), pre_check_failed, FlightEndReason.PRE_CHECK_FAILED)
    recorder.write_tick(0.0005, 0.003)
    recorder.finish(None)

    recording = read_recording(path)
    assert recording.header == RecordingHeader(
        FORMAT_VERSION, CODE_VERSION, "hover", "mock", ("--hover-seconds", "0.1")
    )
    assert recording.ticks == (
        RecordedTick(
            tick_number=0,
            snapshot=snapshot_at(0.0),
            requests=(RequestAndVerdict(Hover(), Verdict.approved()), RequestAndVerdict(Land(), Verdict.approved())),
            pre_check_failures=(),
            replaced_requests=replaced.replaced_requests,
            flight_end_reason=None,
            lateness=0.001,
            work_time=0.002,
        ),
        RecordedTick(
            tick_number=1,
            snapshot=snapshot_at(0.05),
            requests=(),
            pre_check_failures=pre_check_failed.pre_check_failures,
            replaced_requests=(),
            flight_end_reason=FlightEndReason.PRE_CHECK_FAILED,
            lateness=0.0005,
            work_time=0.003,
        ),
    )
    assert recording.last_line == LastLine(None)
    assert not recorder.is_recording


def test_a_refused_request_is_recorded_with_its_reason(tmp_path: Path) -> None:
    path = tmp_path / "run.jsonl"
    recorder = started_recorder(path)

    recorder.record_request(Arm(), Verdict.approved())
    recorder.record_request(TakeOff(0.4), Verdict.refused("the drone isn't armed"))
    recorder.record_tick(snapshot_at(0.0), NO_EVENTS, None)
    recorder.write_tick(0.0, 0.002)
    recorder.finish(None)

    [tick] = read_recording(path).ticks
    assert tick.requests == (
        RequestAndVerdict(Arm(), Verdict.approved()),
        RequestAndVerdict(TakeOff(0.4), Verdict.refused("the drone isn't armed")),
    )


def test_each_line_is_on_disk_once_its_tick_is_written(tmp_path: Path) -> None:
    """One write and a flush per line, so a crash loses at most the tick under way (ADR-0088)."""
    path = tmp_path / "run.jsonl"
    recorder = started_recorder(path)

    record_ticks(recorder, 2)
    recording = read_recording(path)  # while the recorder still has it open
    recorder.finish(None)

    assert [tick.tick_number for tick in recording.ticks] == [0, 1]
    assert recording.last_line is None


def test_each_line_ends_with_a_line_feed_alone_on_every_platform(tmp_path: Path) -> None:
    path = tmp_path / "run.jsonl"
    recorder = started_recorder(path)

    record_ticks(recorder, 1)
    recorder.finish(None)

    data = path.read_bytes()
    assert data.count(b"\n") == 3
    assert b"\r" not in data


def test_the_flight_end_reason_is_recorded_only_on_the_tick_it_was_set(tmp_path: Path) -> None:
    """It's an event (glossary: Event), though the safety layer reports it on every tick after."""
    path = tmp_path / "run.jsonl"
    recorder = started_recorder(path)

    for tick_number, flight_end_reason in enumerate([None, FlightEndReason.STOP_REQUEST, FlightEndReason.STOP_REQUEST]):
        recorder.record_tick(snapshot_at(tick_number * 0.05), NO_EVENTS, flight_end_reason)
        recorder.write_tick(0.0, 0.002)
    recorder.finish(None)

    assert [tick.flight_end_reason for tick in read_recording(path).ticks] == [
        None,
        FlightEndReason.STOP_REQUEST,
        None,
    ]


def test_a_tick_with_no_snapshot_handed_over_gets_its_timing_only(tmp_path: Path) -> None:
    """As when taking the snapshot raised: the tick loop still measured that tick."""
    path = tmp_path / "run.jsonl"
    recorder = started_recorder(path)

    record_ticks(recorder, 1)
    recorder.write_tick(0.001, 0.25)
    recorder.finish(RuntimeError("the snapshot broke"))

    assert read_recording(path).ticks[1] == RecordedTick(1, None, (), (), (), None, 0.001, 0.25)


def test_the_last_line_names_the_error_that_ended_the_run(tmp_path: Path) -> None:
    path = tmp_path / "run.jsonl"
    recorder = started_recorder(path)

    recorder.finish(ConnectionError("Too many packets lost"))

    assert read_recording(path).last_line == LastLine(RecordedError("ConnectionError", "Too many packets lost"))


def test_after_the_last_line_nothing_more_is_recorded(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    path = tmp_path / "run.jsonl"
    recorder = started_recorder(path)

    recorder.finish(None)
    record_ticks(recorder, 1)
    recorder.finish(None)

    assert read_recording(path).ticks == ()  # the reader refuses a line after the last line
    assert records_at(caplog, logging.ERROR) == []


# --- Errors never stop a flight (ADR-0088) ------------------------------------------


class DiskFullFile(io.StringIO):
    """A file on a disk with room for `lines_that_fit` lines: every write after them fails."""

    def __init__(self, lines_that_fit: int) -> None:
        super().__init__()
        self.lines: list[str] = []
        self._lines_that_fit = lines_that_fit

    def write(self, text: str, /) -> int:
        if len(self.lines) == self._lines_that_fit:
            raise OSError(errno.ENOSPC, "No space left on device")
        self.lines.append(text)
        return len(text)


def a_file_with_room_for(monkeypatch: pytest.MonkeyPatch, lines: int) -> DiskFullFile:
    """The file the recorder opens next."""
    file = DiskFullFile(lines)

    def open_it(_path: Path) -> DiskFullFile:
        return file

    monkeypatch.setattr(recorder_module, "_open_new_file", open_it)
    return file


def test_the_last_line_closes_the_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    file = a_file_with_room_for(monkeypatch, lines=10)
    recorder = started_recorder(tmp_path / "run.jsonl")

    recorder.finish(None)

    assert file.closed
    assert len(file.lines) == 2


def test_the_log_says_when_the_recording_finished_and_only_then(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO, logger=RECORDER_LOGGER)
    finished = started_recorder(tmp_path / "finished.jsonl")
    a_file_with_room_for(monkeypatch, lines=1)  # the header's
    failed = started_recorder(tmp_path / "failed.jsonl")

    finished.finish(None)
    failed.finish(None)

    assert [record.getMessage() for record in records_at(caplog, logging.INFO)].count("Recording finished") == 1


def test_a_write_error_is_logged_once_with_its_stack_trace_and_stops_the_recording_without_raising(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    disk = a_file_with_room_for(monkeypatch, lines=1)  # the header's
    recorder = started_recorder(tmp_path / "run.jsonl")

    record_ticks(recorder, 3)
    recorder.finish(None)

    [error] = records_at(caplog, logging.ERROR)
    assert error.getMessage() == "Couldn't write tick 0 to the recording. Recording stopped; the flight goes on."
    assert error.exc_info is not None
    assert not recorder.is_recording
    assert disk.closed
    assert len(disk.lines) == 1


def encode_tick_that_raises(tick: RecordedTick) -> dict[str, Json]:
    raise KeyError("a flight end reason with no name")


def encode_tick_that_misses_a_float(tick: RecordedTick) -> dict[str, Json]:
    return {"kind": "tick", "lateness": math.nan}


@pytest.mark.parametrize(
    "encode_tick_with_a_bug",
    [encode_tick_that_raises, encode_tick_that_misses_a_float],
    ids=["raises", "misses a float that isn't finite"],
)
def test_an_encoding_bug_is_logged_once_with_its_stack_trace_and_stops_the_recording_without_raising(
    encode_tick_with_a_bug: Callable[[RecordedTick], dict[str, Json]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A bug in the recording code mustn't end a flight either, nor leave a line that isn't standard JSON."""
    monkeypatch.setattr(recorder_module, "encode_tick", encode_tick_with_a_bug)
    path = tmp_path / "run.jsonl"
    recorder = started_recorder(path)

    record_ticks(recorder, 3)
    recorder.finish(None)

    [error] = records_at(caplog, logging.ERROR)
    assert error.getMessage() == "Couldn't write tick 0 to the recording. Recording stopped; the flight goes on."
    assert error.exc_info is not None
    assert not recorder.is_recording
    recording = read_recording(path)
    assert recording.ticks == ()
    assert recording.last_line is None


def test_a_recording_that_cant_start_is_logged_and_the_run_goes_on_without_one(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """As when a second run starts in the same second: never write into another run's recording."""
    path = tmp_path / "run.jsonl"
    path.write_text("another run's recording\n", encoding="utf-8")

    recorder = started_recorder(path)
    record_ticks(recorder, 1)
    recorder.finish(None)

    [error] = records_at(caplog, logging.ERROR)
    assert error.getMessage() == f"Couldn't start the recording at {path}. The flight goes on without one."
    assert error.exc_info is not None
    assert not recorder.is_recording
    assert path.read_text(encoding="utf-8") == "another run's recording\n"


def test_a_header_that_cant_be_written_is_logged_and_the_run_goes_on_without_a_recording(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    file = a_file_with_room_for(monkeypatch, lines=0)
    path = tmp_path / "run.jsonl"

    recorder = started_recorder(path)
    record_ticks(recorder, 1)
    recorder.finish(None)

    [error] = records_at(caplog, logging.ERROR)
    assert error.getMessage() == f"Couldn't start the recording at {path}. The flight goes on without one."
    assert not recorder.is_recording
    assert file.closed


# --- The code version (ADR-0088) --------------------------------------------------------

BRANCH_LINES = "# branch.oid 0123abc\n# branch.head main\n# branch.upstream origin/main\n# branch.ab +0 -0\n"


@pytest.mark.parametrize(
    ("status", "code_version"),
    [
        (BRANCH_LINES, CodeVersion("0123abc", True)),
        (BRANCH_LINES + "1 .M N... 100644 100644 100644 1111111 1111111 src/a.py\n", CodeVersion("0123abc", False)),
        (BRANCH_LINES + "? drafts/notes.md\n", CodeVersion("0123abc", False)),
        ("# branch.oid (initial)\n# branch.head main\n", CodeVersion(None, True)),
    ],
    ids=["clean", "a changed file", "an untracked file", "no commit yet"],
)
def test_the_code_version_comes_from_git_status(status: str, code_version: CodeVersion) -> None:
    assert code_version_from_git_status(status) == code_version


def test_git_gives_the_commit_from_the_codes_own_folder_wherever_the_program_runs_from(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))  # no repository around the working folder

    code_version = read_code_version()

    assert code_version.commit is not None
    assert re.fullmatch("[0-9a-f]{40,64}", code_version.commit)
    assert code_version.is_tree_clean is not None
    assert records_at(caplog, logging.WARNING) == []


def test_outside_a_repository_there_is_no_commit_and_one_warning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))  # so no folder above counts

    assert read_code_version(tmp_path) == CodeVersion(None, None)
    [warning] = records_at(caplog, logging.WARNING)
    assert warning.getMessage().startswith("Git couldn't read the commit, so the recording has none: ")
    assert "not a git repository" in warning.getMessage()


def test_without_git_there_is_no_commit_and_one_warning(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setenv("PATH", "")

    assert read_code_version() == CodeVersion(None, None)
    [warning] = records_at(caplog, logging.WARNING)
    assert warning.getMessage() == "Couldn't run git: the recording has no commit"
    assert warning.exc_info is not None


def test_a_git_slower_than_its_time_limit_gives_no_commit_and_one_warning(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr(recorder_module, "GIT_TIME_LIMIT", 1e-6)

    assert read_code_version() == CodeVersion(None, None)
    [warning] = records_at(caplog, logging.WARNING)
    assert warning.getMessage() == "Couldn't run git: the recording has no commit"
