"""A recording's format (ADR-0034, ADR-0087): each record to JSON and back, reading a recording, the golden file."""

import dataclasses
import json
import math
import typing
from pathlib import Path

import pytest

from crazyflie_behavior.geometry import Vector3
from crazyflie_behavior.recording.encoding import (
    FORMAT_VERSION,
    CodeVersion,
    Json,
    LastLine,
    RecordedError,
    RecordedTick,
    Recording,
    RecordingHeader,
    RequestAndVerdict,
    decode_float,
    decode_header,
    decode_last_line,
    decode_request,
    decode_snapshot,
    decode_tick,
    encode_float,
    encode_header,
    encode_last_line,
    encode_request,
    encode_snapshot,
    encode_tick,
    read_recording,
)
from crazyflie_behavior.recording.recorder import Recorder
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
from crazyflie_behavior.safety.safety_layer import FlightEndReason, ReplacedRequest, SafetyEvents
from crazyflie_behavior.snapshot import DroneStatus, RangeReading, RangeReadings, RangeStatus, Snapshot, Stamped

COMMAND_REQUESTS: list[CommandRequest] = [
    Arm(),
    TakeOff(0.4),
    Hover(),
    Land(),
    SetVelocity(Vector3(0.25, -0.5, 0.0)),
    MoveTo(Vector3(1.5, -0.25, 0.4), 2.0),
    Chirp(),
    Tone(440.0),
    Silence(),
    ResetEstimate(),
]
"""One of each command request type."""


def as_line(value: Json) -> str:
    """A value as the recorder writes it: standard JSON only, on one line with no spaces."""
    return json.dumps(value, allow_nan=False, separators=(",", ":"))


def through_json(value: Json) -> object:
    """A value as it comes back from a file."""
    return json.loads(as_line(value))


def full_snapshot() -> Snapshot:
    """A snapshot with every field set, each range status and both kinds of drone time."""
    return Snapshot(
        time=12.5,
        dt=0.05,
        position_estimate=Stamped(Vector3(0.125, -0.5, 0.4), arrival_time=12.48, drone_time=4.25),
        velocity_estimate=Stamped(Vector3(0.01, 0.02, -0.03), arrival_time=12.48, drone_time=4.25),
        velocity_uncertainty=Stamped(0.012, arrival_time=12.47, drone_time=None),
        range_readings=RangeReadings(
            front=Stamped(RangeReading.at_distance(1.25), arrival_time=12.46, drone_time=4.2),
            back=Stamped(RangeReading.out_of_range(), arrival_time=12.46, drone_time=4.2),
            left=Stamped(RangeReading.invalid(), arrival_time=12.46, drone_time=4.2),
            right=None,
            up=Stamped(RangeReading.at_distance(0.0), arrival_time=12.46, drone_time=None),
            down=Stamped(RangeReading.at_distance(0.41), arrival_time=12.49, drone_time=4.3),
        ),
        battery_voltage=Stamped(3.92, arrival_time=12.0, drone_time=None),
        previous_battery_voltage=Stamped(3.93, arrival_time=11.0, drone_time=None),
        drone_status=Stamped(
            DroneStatus(
                is_armed=True, is_flying=True, is_crashed=False, is_tumbled=False, can_arm=False, is_locked=False
            ),
            arrival_time=12.45,
            drone_time=4.2,
        ),
        is_in_initial_climb=False,
        may_be_flying=True,
    )


def full_tick(flight_end_reason: FlightEndReason | None = FlightEndReason.BEHAVIOR_DONE_IN_FLIGHT) -> RecordedTick:
    """A tick with every field set."""
    return RecordedTick(
        tick_number=7,
        snapshot=full_snapshot(),
        requests=(
            RequestAndVerdict(Hover(), Verdict.approved()),
            RequestAndVerdict(SetVelocity(Vector3(0.5, 0.0, 0.0)), Verdict.refused("no speed envelope yet")),
        ),
        pre_check_failures=("battery at 3.10 V (land below 3.20 V)",),
        replaced_requests=(ReplacedRequest("movement", Hover(), Land()),),
        flight_end_reason=flight_end_reason,
        lateness=0.0005,
        work_time=0.0021,
    )


def command_request_types(alias: object = CommandRequest) -> set[type]:
    """Every class in a type alias's union, through the aliases inside it."""
    if isinstance(alias, typing.TypeAliasType):
        return command_request_types(alias.__value__)
    arguments = typing.get_args(alias)
    if not arguments:
        assert isinstance(alias, type)
        return {alias}
    classes: set[type] = set()
    for argument in arguments:
        classes |= command_request_types(argument)
    return classes


def keys_that_arent_field_names(record: object, encoded: object, where: str) -> list[str]:
    """Where a record's JSON keys, but `kind` and `type`, aren't its field names, through every record inside it."""
    if dataclasses.is_dataclass(record) and not isinstance(record, type):
        assert isinstance(encoded, dict), where
        encoded_fields = typing.cast(dict[str, object], encoded)
        names = {field.name for field in dataclasses.fields(record)}
        keys = set(encoded_fields) - {"kind", "type"}
        problems = [] if keys == names else [f"{where}: keys {sorted(keys)}, fields {sorted(names)}"]
        for name in sorted(names & keys):
            problems += keys_that_arent_field_names(getattr(record, name), encoded_fields[name], f"{where}.{name}")
        return problems
    if isinstance(record, tuple):
        assert isinstance(encoded, list), where
        items = typing.cast(list[object], encoded)
        record_items = typing.cast(tuple[object, ...], record)
        return [
            problem
            for index, (item, encoded_item) in enumerate(zip(record_items, items, strict=True))
            for problem in keys_that_arent_field_names(item, encoded_item, f"{where}[{index}]")
        ]
    return []


def write_lines(path: Path, *lines: str) -> Path:
    path.write_text("".join(line + "\n" for line in lines), encoding="utf-8", newline="\n")
    return path


HEADER = RecordingHeader(FORMAT_VERSION, CodeVersion("0123abc", True), "hover", "mock", ("--chirp",))
HEADER_LINE = as_line(encode_header(HEADER))
TICK_LINE = as_line(encode_tick(full_tick()))
LAST_LINE = as_line(encode_last_line(LastLine(None)))


# --- Each record, to JSON and back ---------------------------------------------------


def test_a_snapshot_with_every_field_set_comes_back_the_same() -> None:
    snapshot = full_snapshot()

    assert decode_snapshot(through_json(encode_snapshot(snapshot))) == snapshot


@pytest.mark.parametrize(("value", "text"), [(math.nan, "nan"), (math.inf, "inf"), (-math.inf, "-inf")])
def test_a_float_that_isnt_finite_is_written_as_a_string(value: float, text: str) -> None:
    """Standard JSON has no such numbers, and null means missing (ADR-0087)."""
    assert encode_float(value) == text


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf], ids=["nan", "inf", "-inf"])
def test_a_float_that_isnt_finite_comes_back_as_that_float_not_as_missing(value: float) -> None:
    snapshot = dataclasses.replace(full_snapshot(), battery_voltage=Stamped(value, arrival_time=12.0, drone_time=None))

    battery_voltage = decode_snapshot(through_json(encode_snapshot(snapshot))).battery_voltage

    assert battery_voltage is not None
    if math.isnan(value):
        assert math.isnan(battery_voltage.value)
    else:
        assert battery_voltage.value == value


def test_a_missing_value_comes_back_missing() -> None:
    snapshot = dataclasses.replace(full_snapshot(), battery_voltage=None, position_estimate=None)

    assert decode_snapshot(through_json(encode_snapshot(snapshot))) == snapshot


def test_every_command_request_type_has_an_example_here() -> None:
    """A new request type fails here until it has an example, so the next test covers its encoding."""
    assert {type(command_request) for command_request in COMMAND_REQUESTS} == command_request_types()


@pytest.mark.parametrize(
    "command_request", COMMAND_REQUESTS, ids=[type(request).__name__ for request in COMMAND_REQUESTS]
)
def test_each_command_request_comes_back_the_same(command_request: CommandRequest) -> None:
    assert decode_request(through_json(encode_request(command_request))) == command_request


@pytest.mark.parametrize("flight_end_reason", [*FlightEndReason, None], ids=str)
def test_a_tick_with_every_field_set_comes_back_the_same_whatever_its_flight_end_reason(
    flight_end_reason: FlightEndReason | None,
) -> None:
    tick = full_tick(flight_end_reason)

    assert decode_tick(through_json(encode_tick(tick))) == tick


@pytest.mark.parametrize(
    "header",
    [HEADER, RecordingHeader(FORMAT_VERSION, CodeVersion(None, None), "bench", "crazyflie", ())],
    ids=["with a commit", "without git"],
)
def test_a_header_comes_back_the_same(header: RecordingHeader) -> None:
    assert decode_header(through_json(encode_header(header))) == header


@pytest.mark.parametrize(
    "last_line",
    [LastLine(None), LastLine(RecordedError("ConnectionError", "the link is lost"))],
    ids=["normal end", "error"],
)
def test_a_last_line_comes_back_the_same(last_line: LastLine) -> None:
    assert decode_last_line(through_json(encode_last_line(last_line))) == last_line


def test_each_lines_json_keys_are_its_records_field_names() -> None:
    """So a field added to a record, even one with a default, can't be left out of its recording."""
    last_line = LastLine(RecordedError("ConnectionError", "the link is lost"))
    lines: list[tuple[object, Json]] = [
        (HEADER, encode_header(HEADER)),
        (full_tick(), encode_tick(full_tick())),
        (last_line, encode_last_line(last_line)),
        *[(command_request, encode_request(command_request)) for command_request in COMMAND_REQUESTS],
    ]

    problems = [problem for record, encoded in lines for problem in keys_that_arent_field_names(record, encoded, "")]

    assert problems == []


# --- What the decoder refuses ---------------------------------------------------------


@pytest.mark.parametrize(
    "value", [True, None, "1.0", "NaN", [1.0]], ids=["bool", "null", "number as text", "NaN", "list"]
)
def test_a_float_must_be_a_number_or_one_of_the_three_strings(value: object) -> None:
    with pytest.raises(ValueError, match="Not a float"):
        decode_float(value)


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ({"type": "fly_away"}, "Not a command request"),
        ({"height": 0.4}, "Not a command request"),
        ({"type": "take_off"}, "Expected the fields"),
        ({"type": "hover", "height": 0.4}, "Expected the fields"),
        (["hover"], "Not a JSON object"),
    ],
    ids=["unknown type", "no type", "missing field", "unknown field", "not an object"],
)
def test_the_decoder_refuses_a_command_request_that_isnt_one(value: object, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        decode_request(value)


def test_the_decoder_refuses_a_snapshot_with_a_field_missing_or_unknown() -> None:
    encoded = encode_snapshot(full_snapshot())
    missing = {key: value for key, value in encoded.items() if key != "dt"}
    unknown = {**encoded, "altitude": 0.4}

    for value in (missing, unknown):
        with pytest.raises(ValueError, match="Expected the fields"):
            decode_snapshot(value)


# --- Reading a recording ----------------------------------------------------------------


def test_a_recording_reads_back_line_by_line(tmp_path: Path) -> None:
    path = write_lines(tmp_path / "run.jsonl", HEADER_LINE, TICK_LINE, TICK_LINE, LAST_LINE)

    recording = read_recording(path)

    assert recording.header == HEADER
    assert recording.ticks == (full_tick(), full_tick())
    assert recording.last_line == LastLine(None)


def test_a_cut_off_final_line_is_left_out_and_the_rest_reads_back(tmp_path: Path) -> None:
    """As after a crash or a failed write: the recording has no last line."""
    path = write_lines(tmp_path / "run.jsonl", HEADER_LINE, TICK_LINE, TICK_LINE[: len(TICK_LINE) // 2])

    recording = read_recording(path)

    assert recording.ticks == (full_tick(),)
    assert recording.last_line is None


def test_a_recording_with_a_newer_format_version_is_refused(tmp_path: Path) -> None:
    newer = dataclasses.replace(HEADER, format_version=FORMAT_VERSION + 1)
    path = write_lines(tmp_path / "run.jsonl", as_line(encode_header(newer)), LAST_LINE)

    with pytest.raises(ValueError, match="newer"):
        read_recording(path)


@pytest.mark.parametrize(
    ("lines", "message"),
    [
        ((), "No header"),
        ((TICK_LINE, LAST_LINE), "starts with its header"),
        ((HEADER_LINE, TICK_LINE[:40], TICK_LINE, LAST_LINE), None),
        ((HEADER_LINE, TICK_LINE.replace('"lateness":0.0005', '"lateness":NaN'), LAST_LINE), "Not standard JSON"),
        ((HEADER_LINE, TICK_LINE.replace('"work_time":0.0021', '"work_time":Infinity')), "Not standard JSON"),
        ((HEADER_LINE, LAST_LINE, TICK_LINE), "after the last line"),
        ((HEADER_LINE, '{"kind":"event"}', LAST_LINE), "Not a recording's line"),
    ],
    ids=[
        "empty",
        "no header",
        "a cut-off line before the end",
        "a bare NaN",
        "a bare Infinity, even on the final line",
        "a line after the last line",
        "an unknown kind of line",
    ],
)
def test_a_recording_that_breaks_the_format_is_refused(
    tmp_path: Path, lines: tuple[str, ...], message: str | None
) -> None:
    path = write_lines(tmp_path / "run.jsonl", *lines)

    with pytest.raises(ValueError, match=message):
        read_recording(path)


# --- The golden file (ADR-0089) -------------------------------------------------------

GOLDEN_FOLDER = Path(__file__).parent / "golden"
GOLDEN_FILE = GOLDEN_FOLDER / f"format_v{FORMAT_VERSION}.jsonl"

GOLDEN_HEADER = RecordingHeader(
    format_version=FORMAT_VERSION,
    code_version=CodeVersion("5d41402abc4b2a76b9719d911017c592ab3f00d1", is_tree_clean=False),
    program="hover",
    adapter="crazyflie",
    arguments=("--crazyflie", "--hover-seconds", "2.5"),
)

GOLDEN_SNAPSHOT = Snapshot(
    time=31.25,
    dt=0.05,
    position_estimate=Stamped(Vector3(0.25, -0.125, 0.5), arrival_time=31.23, drone_time=18.5),
    velocity_estimate=Stamped(Vector3(0.03, -0.01, 0.002), arrival_time=31.23, drone_time=18.5),
    velocity_uncertainty=Stamped(0.0125, arrival_time=31.22, drone_time=None),
    range_readings=RangeReadings(
        front=Stamped(RangeReading.at_distance(1.75), arrival_time=31.21, drone_time=18.45),
        back=Stamped(RangeReading.out_of_range(), arrival_time=31.21, drone_time=18.45),
        left=Stamped(RangeReading.invalid(), arrival_time=31.21, drone_time=18.45),
        right=None,
        up=Stamped(RangeReading.at_distance(0.0), arrival_time=31.21, drone_time=None),
        down=Stamped(RangeReading.at_distance(0.5), arrival_time=31.24, drone_time=18.55),
    ),
    battery_voltage=Stamped(3.87, arrival_time=31.0, drone_time=None),
    previous_battery_voltage=Stamped(3.88, arrival_time=30.0, drone_time=None),
    drone_status=Stamped(
        DroneStatus(is_armed=True, is_flying=True, is_crashed=False, is_tumbled=False, can_arm=False, is_locked=False),
        arrival_time=31.2,
        drone_time=18.4,
    ),
    is_in_initial_climb=False,
    may_be_flying=True,
)
"""Every field set, each range status and both kinds of drone time."""

GOLDEN_SNAPSHOT_MISSING_OR_NON_FINITE = Snapshot(
    time=31.3,
    dt=0.05,
    position_estimate=Stamped(Vector3(math.nan, 0.25, 0.5), arrival_time=31.28, drone_time=18.55),
    velocity_estimate=Stamped(Vector3(0.0, 0.0, -math.inf), arrival_time=31.28, drone_time=18.55),
    velocity_uncertainty=Stamped(math.inf, arrival_time=31.27, drone_time=None),
    range_readings=RangeReadings(front=None, back=None, left=None, right=None, up=None, down=None),
    battery_voltage=None,
    previous_battery_voltage=None,
    drone_status=None,
    is_in_initial_climb=True,
    may_be_flying=False,
)
"""Missing values, and each float that isn't finite."""

GOLDEN_TICKS = (
    RecordedTick(
        tick_number=0,
        snapshot=None,
        requests=(),
        pre_check_failures=(),
        replaced_requests=(),
        flight_end_reason=None,
        lateness=0.0,
        work_time=0.0031,
    ),
    RecordedTick(
        tick_number=1,
        snapshot=GOLDEN_SNAPSHOT,
        requests=(
            RequestAndVerdict(Arm(), Verdict.approved()),
            RequestAndVerdict(TakeOff(0.5), Verdict.approved()),
            RequestAndVerdict(Hover(), Verdict.approved()),
            RequestAndVerdict(SetVelocity(Vector3(0.25, 0.0, -0.125)), Verdict.refused("no speed envelope yet")),
            RequestAndVerdict(MoveTo(Vector3(1.0, -0.5, 0.5), 2.5), Verdict.approved()),
            RequestAndVerdict(Land(), Verdict.approved()),
            RequestAndVerdict(Chirp(), Verdict.approved()),
            RequestAndVerdict(Tone(523.25), Verdict.approved()),
            RequestAndVerdict(Silence(), Verdict.approved()),
            RequestAndVerdict(ResetEstimate(), Verdict.refused("may be flying: tilted 35°")),
        ),
        pre_check_failures=(),
        replaced_requests=(
            ReplacedRequest("movement", Hover(), MoveTo(Vector3(1.0, -0.5, 0.5), 2.5)),
            ReplacedRequest("buzzer", Chirp(), Tone(523.25)),
        ),
        flight_end_reason=None,
        lateness=0.0004,
        work_time=0.0027,
    ),
    RecordedTick(
        tick_number=2,
        snapshot=GOLDEN_SNAPSHOT_MISSING_OR_NON_FINITE,
        requests=(),
        pre_check_failures=("no drone status", "the position estimate isn't finite"),
        replaced_requests=(ReplacedRequest("movement", Hover(), Land()),),
        flight_end_reason=FlightEndReason.PRE_CHECK_FAILED,
        lateness=0.0125,
        work_time=0.0019,
    ),
    RecordedTick(3, GOLDEN_SNAPSHOT, (), (), (), FlightEndReason.STOP_REQUEST, lateness=0.0, work_time=0.0022),
    RecordedTick(
        4, GOLDEN_SNAPSHOT, (), (), (), FlightEndReason.BEHAVIOR_DONE_IN_FLIGHT, lateness=0.0, work_time=0.0024
    ),
)
"""Every kind of tick line. Not a real run: a run records one flight end reason, and this holds each one."""

GOLDEN_LAST_LINE = LastLine(RecordedError("ConnectionError", "the link is lost"))

GOLDEN_RECORDING = Recording(GOLDEN_HEADER, GOLDEN_TICKS, GOLDEN_LAST_LINE)
"""The golden file's data (glossary: Golden file)."""


def golden_text() -> str:
    """The golden file's data as today's code writes it: a new format version's golden file is this, written once."""
    lines = [
        encode_header(GOLDEN_HEADER),
        *(encode_tick(tick) for tick in GOLDEN_TICKS),
        encode_last_line(GOLDEN_LAST_LINE),
    ]
    return "".join(as_line(line) + "\n" for line in lines)


def golden_lines() -> list[str]:
    return GOLDEN_FILE.read_bytes().decode("utf-8").split("\n")


def test_the_only_golden_file_is_the_current_format_versions() -> None:
    """After a format change, a golden file the new code writes replaces the old one (ADR-0089)."""
    assert sorted(path.name for path in GOLDEN_FOLDER.iterdir()) == [GOLDEN_FILE.name]


def test_the_golden_file_reads_back_as_its_data() -> None:
    # NaN never equals itself, so the records are compared by their repr, which writes it as nan.
    assert repr(read_recording(GOLDEN_FILE)) == repr(GOLDEN_RECORDING)


def test_todays_code_writes_the_golden_files_data_byte_for_byte() -> None:
    """A failure here is a format change: bump FORMAT_VERSION, and replace the golden file (ADR-0089)."""
    assert golden_lines() == golden_text().split("\n")


def test_the_recorder_writes_the_golden_files_lines_byte_for_byte(tmp_path: Path) -> None:
    """All but ticks 3 and 4, since a run records only its first flight end reason."""
    path = tmp_path / "run.jsonl"
    recorder = Recorder(GOLDEN_HEADER.adapter, GOLDEN_HEADER.arguments)
    recorder.start(path, GOLDEN_HEADER.program, GOLDEN_HEADER.code_version)
    for tick in GOLDEN_TICKS[:3]:
        for answered in tick.requests:
            recorder.record_request(answered.request, answered.verdict)
        if tick.snapshot is not None:
            events = SafetyEvents(tick.pre_check_failures, tick.replaced_requests)
            recorder.record_tick(tick.snapshot, events, tick.flight_end_reason)
        recorder.write_tick(tick.lateness, tick.work_time)
    recorder.finish(ConnectionError("the link is lost"))

    lines = golden_lines()
    assert path.read_bytes().decode("utf-8").split("\n") == lines[:4] + lines[-2:]


def test_the_golden_files_data_has_each_command_request_type_flight_end_reason_and_range_status() -> None:
    """So a new one can't be left out of the golden file."""
    range_readings = [tick.snapshot.range_readings for tick in GOLDEN_TICKS if tick.snapshot is not None]
    range_statuses = {
        reading.value.status
        for readings in range_readings
        for reading in (readings.front, readings.back, readings.left, readings.right, readings.up, readings.down)
        if reading is not None
    }

    assert {type(answered.request) for tick in GOLDEN_TICKS for answered in tick.requests} == command_request_types()
    assert {tick.flight_end_reason for tick in GOLDEN_TICKS} == {*FlightEndReason, None}
    assert range_statuses == set(RangeStatus)
