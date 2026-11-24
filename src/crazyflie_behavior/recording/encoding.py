"""A recording's format: each record type to and from JSON, and reading a recording back (ADR-0034, ADR-0087).

A recording is a header line, one line per tick and a last line. Each line's JSON keys are its record's field
names, plus `kind`, which says which line it is. A float that isn't finite is the string "nan", "inf" or
"-inf", never null, which means missing (ADR-0087). The file holds standard JSON only.
"""

import json
import math
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from crazyflie_behavior.geometry import Vector3
from crazyflie_behavior.safety.requests import (
    Arm,
    Chirp,
    CommandRequest,
    Hover,
    Land,
    MoveTo,
    ResetEstimate,
    SetVelocity,
    Silence,
    TakeOff,
    Tone,
    Verdict,
)
from crazyflie_behavior.safety.safety_layer import FlightEndReason, ReplacedRequest
from crazyflie_behavior.snapshot import DroneStatus, RangeReading, RangeReadings, RangeStatus, Snapshot, Stamped

FORMAT_VERSION = 1
"""Every change to the format bumps it (ADR-0034). A reader refuses a version newer than it knows."""

type Json = bool | int | float | str | list[Json] | dict[str, Json] | None
"""A value `json` writes and reads back as it was. Its floats are finite: `encode_float` turns the rest into strings."""

_NON_FINITE_FLOATS = {"nan": math.nan, "inf": math.inf, "-inf": -math.inf}

_FLIGHT_END_REASONS = {
    FlightEndReason.PRE_CHECK_FAILED: "pre_check_failed",
    FlightEndReason.STOP_REQUEST: "stop_request",
    FlightEndReason.BEHAVIOR_DONE_IN_FLIGHT: "behavior_done_in_flight",
}
"""Each flight end reason's name in a recording. Its value is a sentence for the log, free to change."""


@dataclass(frozen=True, slots=True)
class CodeVersion:
    """Which code ran: its git commit, and whether the files matched it (ADR-0088)."""

    commit: str | None
    """None when git couldn't tell."""
    is_tree_clean: bool | None
    """False when any file differs from the commit, untracked files included. None when git couldn't tell."""


@dataclass(frozen=True, slots=True)
class RecordingHeader:
    """A recording's first line (ADR-0034, ADR-0088)."""

    format_version: int
    code_version: CodeVersion
    program: str
    adapter: str
    """The adapter the run used: "crazyflie" or "mock"."""
    arguments: tuple[str, ...]
    """The program's command-line arguments, as given. With a clean commit, they fix every setting."""


@dataclass(frozen=True, slots=True)
class RequestAndVerdict:
    """A behavior's command request, and the safety layer's verdict on it."""

    request: CommandRequest
    verdict: Verdict


@dataclass(frozen=True, slots=True)
class RecordedTick:
    """One tick's line: the snapshot, the command requests and their verdicts, the events and the timing."""

    tick_number: int
    """Counted from 0, as in the text log's tick lines."""
    snapshot: Snapshot | None
    """None when the tick step raised before it had a snapshot."""
    requests: tuple[RequestAndVerdict, ...]
    pre_check_failures: tuple[str, ...]
    """Why the safety pre-check failed, on the tick it failed."""
    replaced_requests: tuple[ReplacedRequest, ...]
    flight_end_reason: FlightEndReason | None
    """Only on the tick the flight end was set (glossary: Event)."""
    lateness: float
    work_time: float


@dataclass(frozen=True, slots=True)
class RecordedError:
    """The error that ended a run."""

    type_name: str
    """Its class, such as ConnectionError for a lost link (ADR-0084)."""
    message: str


@dataclass(frozen=True, slots=True)
class LastLine:
    """A recording's last line: how the run ended (ADR-0087)."""

    error: RecordedError | None
    """None when the run ended normally."""


@dataclass(frozen=True, slots=True)
class Recording:
    """A recording, read back (glossary: Recording)."""

    header: RecordingHeader
    ticks: tuple[RecordedTick, ...]
    last_line: LastLine | None
    """None when the file has no last line, as after a crash."""


# --- Values ------------------------------------------------------------------------------


def encode_float(value: float) -> Json:
    """A float, or "nan", "inf" or "-inf" for one that isn't finite (ADR-0087)."""
    if math.isnan(value):
        return "nan"
    if math.isinf(value):
        return "inf" if value > 0.0 else "-inf"
    return value


def decode_float(value: object) -> float:
    if isinstance(value, bool):
        raise ValueError(f"Not a float: {value!r}")
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str) and value in _NON_FINITE_FLOATS:
        return _NON_FINITE_FLOATS[value]
    raise ValueError(f"Not a float: {value!r}")


def _encode_optional_float(value: float | None) -> Json:
    return None if value is None else encode_float(value)


def _decode_optional_float(value: object) -> float | None:
    return None if value is None else decode_float(value)


def _decode_bool(value: object) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"Not a bool: {value!r}")
    return value


def _decode_int(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"Not an integer: {value!r}")
    return value


def _decode_str(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError(f"Not a string: {value!r}")
    return value


def _decode_list(value: object) -> list[object]:
    if not isinstance(value, list):
        raise ValueError(f"Not a list: {value!r}")
    return cast(list[object], value)


def _object(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"Not a JSON object: {value!r}")
    return cast(dict[str, object], value)


def _fields(value: object, *names: str) -> dict[str, object]:
    """A JSON object's fields, which must be exactly `names`: a missing or unknown one is an error."""
    fields = _object(value)
    if set(fields) != set(names):
        raise ValueError(f"Expected the fields {sorted(names)}, got {sorted(fields)}")
    return fields


def encode_vector3(vector: Vector3) -> dict[str, Json]:
    return {"x": encode_float(vector.x), "y": encode_float(vector.y), "z": encode_float(vector.z)}


def decode_vector3(value: object) -> Vector3:
    fields = _fields(value, "x", "y", "z")
    return Vector3(decode_float(fields["x"]), decode_float(fields["y"]), decode_float(fields["z"]))


# --- The snapshot ------------------------------------------------------------------------


def _encode_stamped[T](stamped: Stamped[T] | None, encode_value: Callable[[T], Json]) -> Json:
    if stamped is None:
        return None
    return {
        "value": encode_value(stamped.value),
        "arrival_time": encode_float(stamped.arrival_time),
        "drone_time": _encode_optional_float(stamped.drone_time),
    }


def _decode_stamped[T](value: object, decode_value: Callable[[object], T]) -> Stamped[T] | None:
    if value is None:
        return None
    fields = _fields(value, "value", "arrival_time", "drone_time")
    return Stamped(
        decode_value(fields["value"]),
        decode_float(fields["arrival_time"]),
        _decode_optional_float(fields["drone_time"]),
    )


def _encode_range_reading(reading: RangeReading) -> Json:
    return {"status": reading.status.value, "distance": _encode_optional_float(reading.distance)}


def _decode_range_reading(value: object) -> RangeReading:
    fields = _fields(value, "status", "distance")
    return RangeReading(RangeStatus(_decode_str(fields["status"])), _decode_optional_float(fields["distance"]))


def _encode_range_readings(readings: RangeReadings) -> Json:
    return {
        "front": _encode_stamped(readings.front, _encode_range_reading),
        "back": _encode_stamped(readings.back, _encode_range_reading),
        "left": _encode_stamped(readings.left, _encode_range_reading),
        "right": _encode_stamped(readings.right, _encode_range_reading),
        "up": _encode_stamped(readings.up, _encode_range_reading),
        "down": _encode_stamped(readings.down, _encode_range_reading),
    }


def _decode_range_readings(value: object) -> RangeReadings:
    fields = _fields(value, "front", "back", "left", "right", "up", "down")
    return RangeReadings(
        front=_decode_stamped(fields["front"], _decode_range_reading),
        back=_decode_stamped(fields["back"], _decode_range_reading),
        left=_decode_stamped(fields["left"], _decode_range_reading),
        right=_decode_stamped(fields["right"], _decode_range_reading),
        up=_decode_stamped(fields["up"], _decode_range_reading),
        down=_decode_stamped(fields["down"], _decode_range_reading),
    )


def _encode_drone_status(status: DroneStatus) -> Json:
    return {
        "is_armed": status.is_armed,
        "is_flying": status.is_flying,
        "is_crashed": status.is_crashed,
        "is_tumbled": status.is_tumbled,
        "can_arm": status.can_arm,
        "is_locked": status.is_locked,
    }


def _decode_drone_status(value: object) -> DroneStatus:
    fields = _fields(value, "is_armed", "is_flying", "is_crashed", "is_tumbled", "can_arm", "is_locked")
    return DroneStatus(
        is_armed=_decode_bool(fields["is_armed"]),
        is_flying=_decode_bool(fields["is_flying"]),
        is_crashed=_decode_bool(fields["is_crashed"]),
        is_tumbled=_decode_bool(fields["is_tumbled"]),
        can_arm=_decode_bool(fields["can_arm"]),
        is_locked=_decode_bool(fields["is_locked"]),
    )


def encode_snapshot(snapshot: Snapshot) -> dict[str, Json]:
    return {
        "time": encode_float(snapshot.time),
        "dt": encode_float(snapshot.dt),
        "position_estimate": _encode_stamped(snapshot.position_estimate, encode_vector3),
        "velocity_estimate": _encode_stamped(snapshot.velocity_estimate, encode_vector3),
        "velocity_uncertainty": _encode_stamped(snapshot.velocity_uncertainty, encode_float),
        "range_readings": _encode_range_readings(snapshot.range_readings),
        "battery_voltage": _encode_stamped(snapshot.battery_voltage, encode_float),
        "previous_battery_voltage": _encode_stamped(snapshot.previous_battery_voltage, encode_float),
        "drone_status": _encode_stamped(snapshot.drone_status, _encode_drone_status),
        "is_in_initial_climb": snapshot.is_in_initial_climb,
        "may_be_flying": snapshot.may_be_flying,
    }


def decode_snapshot(value: object) -> Snapshot:
    fields = _fields(
        value,
        "time",
        "dt",
        "position_estimate",
        "velocity_estimate",
        "velocity_uncertainty",
        "range_readings",
        "battery_voltage",
        "previous_battery_voltage",
        "drone_status",
        "is_in_initial_climb",
        "may_be_flying",
    )
    return Snapshot(
        time=decode_float(fields["time"]),
        dt=decode_float(fields["dt"]),
        position_estimate=_decode_stamped(fields["position_estimate"], decode_vector3),
        velocity_estimate=_decode_stamped(fields["velocity_estimate"], decode_vector3),
        velocity_uncertainty=_decode_stamped(fields["velocity_uncertainty"], decode_float),
        range_readings=_decode_range_readings(fields["range_readings"]),
        battery_voltage=_decode_stamped(fields["battery_voltage"], decode_float),
        previous_battery_voltage=_decode_stamped(fields["previous_battery_voltage"], decode_float),
        drone_status=_decode_stamped(fields["drone_status"], _decode_drone_status),
        is_in_initial_climb=_decode_bool(fields["is_in_initial_climb"]),
        may_be_flying=_decode_bool(fields["may_be_flying"]),
    )


# --- Command requests, verdicts and events -----------------------------------------------


def encode_request(command_request: CommandRequest) -> dict[str, Json]:
    """A command request, with its type's name in `type`."""
    match command_request:
        case Arm():
            return {"type": "arm"}
        case TakeOff(height=height):
            return {"type": "take_off", "height": encode_float(height)}
        case Hover():
            return {"type": "hover"}
        case Land():
            return {"type": "land"}
        case SetVelocity(velocity=velocity):
            return {"type": "set_velocity", "velocity": encode_vector3(velocity)}
        case MoveTo(position=position, duration=duration):
            return {"type": "move_to", "position": encode_vector3(position), "duration": encode_float(duration)}
        case Chirp():
            return {"type": "chirp"}
        case Tone(pitch=pitch):
            return {"type": "tone", "pitch": encode_float(pitch)}
        case Silence():
            return {"type": "silence"}
        case ResetEstimate():
            return {"type": "reset_estimate"}


def decode_request(value: object) -> CommandRequest:
    match _object(value).get("type"):
        case "arm":
            _fields(value, "type")
            return Arm()
        case "take_off":
            return TakeOff(decode_float(_fields(value, "type", "height")["height"]))
        case "hover":
            _fields(value, "type")
            return Hover()
        case "land":
            _fields(value, "type")
            return Land()
        case "set_velocity":
            return SetVelocity(decode_vector3(_fields(value, "type", "velocity")["velocity"]))
        case "move_to":
            fields = _fields(value, "type", "position", "duration")
            return MoveTo(decode_vector3(fields["position"]), decode_float(fields["duration"]))
        case "chirp":
            _fields(value, "type")
            return Chirp()
        case "tone":
            return Tone(decode_float(_fields(value, "type", "pitch")["pitch"]))
        case "silence":
            _fields(value, "type")
            return Silence()
        case "reset_estimate":
            _fields(value, "type")
            return ResetEstimate()
        case _:
            raise ValueError(f"Not a command request: {value!r}")


def _encode_request_and_verdict(answered: RequestAndVerdict) -> Json:
    verdict = answered.verdict
    return {
        "request": encode_request(answered.request),
        "verdict": {"is_approved": verdict.is_approved, "reason": verdict.reason},
    }


def _decode_request_and_verdict(value: object) -> RequestAndVerdict:
    fields = _fields(value, "request", "verdict")
    verdict = _fields(fields["verdict"], "is_approved", "reason")
    return RequestAndVerdict(
        decode_request(fields["request"]),
        Verdict(_decode_bool(verdict["is_approved"]), _decode_str(verdict["reason"])),
    )


def _encode_replaced_request(replaced_request: ReplacedRequest) -> Json:
    return {
        "slot": replaced_request.slot,
        "replaced": encode_request(replaced_request.replaced),
        "replaced_by": encode_request(replaced_request.replaced_by),
    }


def _decode_replaced_request(value: object) -> ReplacedRequest:
    fields = _fields(value, "slot", "replaced", "replaced_by")
    return ReplacedRequest(
        _decode_str(fields["slot"]),
        decode_request(fields["replaced"]),
        decode_request(fields["replaced_by"]),
    )


def _decode_flight_end_reason(value: object) -> FlightEndReason | None:
    if value is None:
        return None
    for reason, name in _FLIGHT_END_REASONS.items():
        if value == name:
            return reason
    raise ValueError(f"Not a flight end reason: {value!r}")


# --- Lines -------------------------------------------------------------------------------


def encode_header(header: RecordingHeader) -> dict[str, Json]:
    code_version = header.code_version
    return {
        "kind": "header",
        "format_version": header.format_version,
        "code_version": {"commit": code_version.commit, "is_tree_clean": code_version.is_tree_clean},
        "program": header.program,
        "adapter": header.adapter,
        "arguments": [argument for argument in header.arguments],
    }


def decode_header(value: object) -> RecordingHeader:
    fields = _fields(value, "kind", "format_version", "code_version", "program", "adapter", "arguments")
    code_version = _fields(fields["code_version"], "commit", "is_tree_clean")
    commit = code_version["commit"]
    is_tree_clean = code_version["is_tree_clean"]
    return RecordingHeader(
        format_version=_decode_int(fields["format_version"]),
        code_version=CodeVersion(
            None if commit is None else _decode_str(commit),
            None if is_tree_clean is None else _decode_bool(is_tree_clean),
        ),
        program=_decode_str(fields["program"]),
        adapter=_decode_str(fields["adapter"]),
        arguments=tuple(_decode_str(argument) for argument in _decode_list(fields["arguments"])),
    )


def encode_tick(tick: RecordedTick) -> dict[str, Json]:
    reason = tick.flight_end_reason
    return {
        "kind": "tick",
        "tick_number": tick.tick_number,
        "snapshot": None if tick.snapshot is None else encode_snapshot(tick.snapshot),
        "requests": [_encode_request_and_verdict(answered) for answered in tick.requests],
        "pre_check_failures": [failure for failure in tick.pre_check_failures],
        "replaced_requests": [_encode_replaced_request(replaced) for replaced in tick.replaced_requests],
        "flight_end_reason": None if reason is None else _FLIGHT_END_REASONS[reason],
        "lateness": encode_float(tick.lateness),
        "work_time": encode_float(tick.work_time),
    }


def decode_tick(value: object) -> RecordedTick:
    fields = _fields(
        value,
        "kind",
        "tick_number",
        "snapshot",
        "requests",
        "pre_check_failures",
        "replaced_requests",
        "flight_end_reason",
        "lateness",
        "work_time",
    )
    snapshot = fields["snapshot"]
    return RecordedTick(
        tick_number=_decode_int(fields["tick_number"]),
        snapshot=None if snapshot is None else decode_snapshot(snapshot),
        requests=tuple(_decode_request_and_verdict(answered) for answered in _decode_list(fields["requests"])),
        pre_check_failures=tuple(_decode_str(failure) for failure in _decode_list(fields["pre_check_failures"])),
        replaced_requests=tuple(
            _decode_replaced_request(replaced) for replaced in _decode_list(fields["replaced_requests"])
        ),
        flight_end_reason=_decode_flight_end_reason(fields["flight_end_reason"]),
        lateness=decode_float(fields["lateness"]),
        work_time=decode_float(fields["work_time"]),
    )


def encode_last_line(last_line: LastLine) -> dict[str, Json]:
    error = last_line.error
    return {
        "kind": "last_line",
        "error": None if error is None else {"type_name": error.type_name, "message": error.message},
    }


def decode_last_line(value: object) -> LastLine:
    error = _fields(value, "kind", "error")["error"]
    if error is None:
        return LastLine(None)
    fields = _fields(error, "type_name", "message")
    return LastLine(RecordedError(_decode_str(fields["type_name"]), _decode_str(fields["message"])))


# --- Reading -----------------------------------------------------------------------------


def _refuse_non_standard_constant(constant: str) -> object:
    raise ValueError(f"Not standard JSON: {constant}")


def _parse_line(line: str) -> dict[str, object]:
    value: object = json.loads(line, parse_constant=_refuse_non_standard_constant)
    if not isinstance(value, dict):
        raise ValueError(f"A recording's line is a JSON object: {line[:80]!r}")
    return cast(dict[str, object], value)


def read_recording(path: Path) -> Recording:
    """Read a recording back. Raises ValueError for a format version newer than `FORMAT_VERSION`, or a bad line.

    A final line that isn't whole JSON was cut off, by a crash or a failed write, and is left out.
    """
    lines = [line for line in path.read_text(encoding="utf-8").split("\n") if line]
    if not lines:
        raise ValueError(f"No header: {path}")
    first = _parse_line(lines[0])
    if first.get("kind") != "header":
        raise ValueError(f"A recording starts with its header: {path}")
    format_version = _decode_int(first.get("format_version"))
    if format_version > FORMAT_VERSION:
        raise ValueError(f"Format version {format_version} is newer than this code reads ({FORMAT_VERSION}): {path}")
    header = decode_header(first)
    ticks: list[RecordedTick] = []
    last_line: LastLine | None = None
    for index, line in enumerate(lines[1:], start=1):
        try:
            fields = _parse_line(line)
        except json.JSONDecodeError:
            if index == len(lines) - 1:
                break  # cut off
            raise
        if last_line is not None:
            raise ValueError(f"A line after the last line: {path}")
        kind = fields.get("kind")
        if kind == "tick":
            ticks.append(decode_tick(fields))
        elif kind == "last_line":
            last_line = decode_last_line(fields)
        else:
            raise ValueError(f"Not a recording's line: kind {kind!r} in {path}")
    return Recording(header, tuple(ticks), last_line)
