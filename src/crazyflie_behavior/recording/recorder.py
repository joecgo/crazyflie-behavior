"""The recorder: writes one run's recording (ADR-0034, ADR-0087, ADR-0088).

The program starts it and has it write the last line. The tick step hands it each tick's command requests
with their verdicts, then the snapshot and the events. The tick loop's `on_tick_measured` makes it write the
tick's line with the tick's timing. Everything runs on the tick's thread, one write and a flush per line.

It never raises: its first error is logged with the stack trace, recording stops, and the flight goes on
(ADR-0020, ADR-0088).
"""

import json
import logging
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

from crazyflie_behavior.recording.encoding import (
    FORMAT_VERSION,
    CodeVersion,
    Json,
    LastLine,
    RecordedError,
    RecordedTick,
    RecordingHeader,
    RequestAndVerdict,
    encode_header,
    encode_last_line,
    encode_tick,
)
from crazyflie_behavior.safety.requests import CommandRequest, Verdict
from crazyflie_behavior.safety.safety_layer import FlightEndReason, SafetyEvents
from crazyflie_behavior.snapshot import Snapshot

logger = logging.getLogger(__name__)

GIT_TIME_LIMIT = 5.0
"""Seconds to wait for git at start-up. Past it, the recording has no commit."""

_SOURCE_FOLDER = Path(__file__).resolve().parent
"""Where git looks for the commit: the code's own folder, wherever the program runs from."""


def read_code_version(folder: Path = _SOURCE_FOLDER) -> CodeVersion:
    """The git commit and whether the tree is clean, from one git call before connecting (ADR-0088).

    Without git, outside a repository or after `GIT_TIME_LIMIT`, both are None and the log warns.
    """
    try:
        result = subprocess.run(
            ["git", "--no-optional-locks", "status", "--porcelain=v2", "--branch"],
            cwd=folder,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=GIT_TIME_LIMIT,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        logger.warning("Couldn't run git: the recording has no commit", exc_info=True)
        return CodeVersion(None, None)
    if result.returncode != 0:
        logger.warning("Git couldn't read the commit, so the recording has none: %s", result.stderr.strip())
        return CodeVersion(None, None)
    return code_version_from_git_status(result.stdout)


def code_version_from_git_status(status: str) -> CodeVersion:
    """From `git status --porcelain=v2 --branch`: a `# branch.oid` line, then one line per changed or untracked file."""
    commit: str | None = None
    is_tree_clean = True
    for line in status.splitlines():
        if line.startswith("# branch.oid "):
            object_name = line.removeprefix("# branch.oid ")
            commit = None if object_name == "(initial)" else object_name  # "(initial)": no commit yet
        elif line and not line.startswith("#"):
            is_tree_clean = False
    return CodeVersion(commit, is_tree_clean)


def _open_new_file(path: Path) -> TextIO:
    """A new file only, so a second run in the same second can't write into the first one's recording."""
    return path.open("x", encoding="utf-8", newline="\n")


@dataclass(frozen=True, slots=True)
class _TickStepPart:
    """What the tick step hands over once its tick is done: the line's snapshot and events."""

    snapshot: Snapshot
    events: SafetyEvents
    flight_end_reason: FlightEndReason | None


class Recorder:
    """Writes one run's recording: the header, a line per tick and the last line (glossary: Recorder).

    Records nothing until `start()`, and nothing after `finish()` or an error.
    """

    def __init__(self, adapter: str, arguments: Sequence[str]) -> None:
        """`adapter` and the program's command-line `arguments`, as given, go in the header."""
        self._adapter = adapter
        self._arguments = tuple(arguments)
        self._file: TextIO | None = None
        self._tick_number = 0
        self._requests: list[RequestAndVerdict] = []
        self._tick_step_part: _TickStepPart | None = None
        self._is_flight_end_recorded = False

    @property
    def is_recording(self) -> bool:
        """Whether lines still go to the file: from `start()` until `finish()` or an error."""
        return self._file is not None

    def start(self, path: Path, program: str, code_version: CodeVersion) -> None:
        """Create the recording at `path` and write its header."""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            self._file = _open_new_file(path)
            self._write(
                encode_header(RecordingHeader(FORMAT_VERSION, code_version, program, self._adapter, self._arguments))
            )
        except Exception:
            logger.exception("Couldn't start the recording at %s. The flight goes on without one.", path)
            self._stop()
            return
        logger.info("Recording to %s", path)

    def record_request(self, command_request: CommandRequest, verdict: Verdict) -> None:
        """Keep a command request and its verdict for this tick's line."""
        if self._file is None:
            return
        try:
            self._requests.append(RequestAndVerdict(command_request, verdict))
        except Exception:
            logger.exception("Couldn't record a command request. Recording stopped; the flight goes on.")
            self._stop()

    def record_tick(self, snapshot: Snapshot, events: SafetyEvents, flight_end_reason: FlightEndReason | None) -> None:
        """Keep the tick step's part of this tick's line: its snapshot, and its events once it's done."""
        if self._file is None:
            return
        try:
            self._tick_step_part = _TickStepPart(snapshot, events, flight_end_reason)
        except Exception:
            logger.exception("Couldn't record a tick. Recording stopped; the flight goes on.")
            self._stop()

    def write_tick(self, lateness: float, work_time: float) -> None:
        """Write this tick's line, with the timing: the tick loop's `on_tick_measured` (ADR-0088).

        A tick with no snapshot handed over, as when taking the snapshot raised, gets a line with the timing only.
        """
        part, self._tick_step_part = self._tick_step_part, None
        requests, self._requests = tuple(self._requests), []
        tick_number = self._tick_number
        self._tick_number += 1
        if self._file is None:
            return
        try:
            # The flight end is an event: recorded on the tick it was set, not on every tick after.
            flight_end_reason = None
            if part is not None and part.flight_end_reason is not None and not self._is_flight_end_recorded:
                flight_end_reason = part.flight_end_reason
                self._is_flight_end_recorded = True
            tick = RecordedTick(
                tick_number=tick_number,
                snapshot=None if part is None else part.snapshot,
                requests=requests,
                pre_check_failures=() if part is None else part.events.pre_check_failures,
                replaced_requests=() if part is None else part.events.replaced_requests,
                flight_end_reason=flight_end_reason,
                lateness=lateness,
                work_time=work_time,
            )
            self._write(encode_tick(tick))
        except Exception:
            logger.exception(
                "Couldn't write tick %d to the recording. Recording stopped; the flight goes on.", tick_number
            )
            self._stop()

    def finish(self, error: BaseException | None) -> None:
        """Write the last line, saying how the run ended, and close the recording (ADR-0087)."""
        if self._file is None:
            return
        try:
            recorded_error = None if error is None else RecordedError(type(error).__name__, str(error))
            self._write(encode_last_line(LastLine(recorded_error)))
            file, self._file = self._file, None
            file.close()
        except Exception:
            logger.exception("Couldn't finish the recording")
            self._stop()

    def _write(self, line: dict[str, Json]) -> None:
        if self._file is None:
            return
        # allow_nan=False: a float that isn't finite and isn't encoded as a string is a bug, never a bare NaN.
        self._file.write(json.dumps(line, allow_nan=False, separators=(",", ":")) + "\n")
        self._file.flush()

    def _stop(self) -> None:
        """Stop recording after an error, closing what's left of the file."""
        file, self._file = self._file, None
        if file is None:
            return
        try:
            file.close()
        except Exception:
            logger.debug("Closing the recording failed too", exc_info=True)
