"""The safety layer (ADR-0030): pre-check, judging, sending."""

import logging
import math
from collections.abc import Callable
from dataclasses import replace

import pytest

from crazyflie_behavior.drone.interface import FLOOR_MAX_SPEED, FLOW_VELOCITY_UNCERTAINTY, TOUCHDOWN_DOWN_RANGE
from crazyflie_behavior.drone.mock_adapter import MockAdapter
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
from crazyflie_behavior.safety.safety_layer import (
    BATTERY_STALE_AFTER,
    LOW_BATTERY_VOLTAGE,
    STALE_AFTER,
    TAKE_OFF_BATTERY_VOLTAGE,
    TAKE_OFF_MAX_DISTANCE_FROM_RESET_POINT,
    SafetyLayer,
    in_flight_velocity_uncertainty_limit,
    judge,
    safety_pre_check,
)
from crazyflie_behavior.snapshot import (
    DroneStatus,
    RangeReading,
    RangeReadings,
    Snapshot,
    Stamped,
)
from crazyflie_behavior.timing.clock import SimClock

SAFETY_LOGGER = "crazyflie_behavior.safety.safety_layer"
NOW = 10.0
"""The tick's time in every hand-built snapshot."""

ON_THE_FLOOR = DroneStatus(
    is_armed=False, is_flying=False, is_crashed=False, is_tumbled=False, can_arm=True, is_locked=False
)
ARMED = replace(ON_THE_FLOOR, is_armed=True)
FLYING = replace(ARMED, is_flying=True)


def stamped[T](value: T, age: float) -> Stamped[T]:
    return Stamped(value, arrival_time=NOW - age, drone_time=None)


def snapshot(
    status: DroneStatus = ON_THE_FLOOR,
    *,
    position_age: float = 0.0,
    status_age: float = 0.0,
    down_age: float = 0.0,
    battery_voltage: float = 4.0,
    battery_age: float = 0.0,
    previous_battery_voltage: float | None = None,
    velocity_uncertainty: float = 0.01,
    velocity_uncertainty_age: float = 0.0,
    is_in_initial_climb: bool = False,
    may_be_flying: bool | None = None,
) -> Snapshot:
    """A hand-built snapshot: everything fresh and the battery charged, unless asked otherwise.

    The previous battery reading, if any, arrived a second before the latest.

    `may_be_flying` follows the status unless set.
    """
    height = 0.5 if status.is_flying else 0.0
    return Snapshot(
        time=NOW,
        dt=0.05,
        position_estimate=stamped(Vector3(0.0, 0.0, height), position_age),
        velocity_estimate=stamped(Vector3.ZERO, position_age),
        velocity_uncertainty=stamped(velocity_uncertainty, velocity_uncertainty_age),
        range_readings=RangeReadings(
            front=None,
            back=None,
            left=None,
            right=None,
            up=None,
            down=stamped(RangeReading.at_distance(height), down_age),
        ),
        battery_voltage=stamped(battery_voltage, battery_age),
        previous_battery_voltage=(
            None if previous_battery_voltage is None else stamped(previous_battery_voltage, battery_age + 1.0)
        ),
        drone_status=stamped(status, status_age),
        is_in_initial_climb=is_in_initial_climb,
        may_be_flying=status.is_flying if may_be_flying is None else may_be_flying,
    )


class RecordingDrone(MockAdapter):
    """The mock adapter, also recording each take-off height it's sent."""

    def __init__(self) -> None:
        super().__init__(SimClock())
        self.take_off_heights: list[float] = []

    def take_off(self, height: float) -> None:
        self.take_off_heights.append(height)
        super().take_off(height)


def warnings_in(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]


# --- The safety pre-check ---------------------------------------------------------


def test_a_fresh_snapshot_with_a_charged_battery_passes() -> None:
    assert safety_pre_check(snapshot(FLYING)) == []


SNAPSHOT_WITH_AGE: dict[str, Callable[[float], Snapshot]] = {
    "position estimate": lambda age: snapshot(position_age=age),
    "drone status": lambda age: snapshot(status_age=age),
    "down range": lambda age: snapshot(down_age=age),
    "battery voltage": lambda age: snapshot(battery_age=age),
}
"""A snapshot where only the named value is `age` seconds old."""


@pytest.mark.parametrize(
    ("name", "limit"),
    [
        ("position estimate", STALE_AFTER),
        ("drone status", STALE_AFTER),
        ("down range", STALE_AFTER),
        ("battery voltage", BATTERY_STALE_AFTER),
    ],
)
def test_a_value_is_fresh_at_its_limit_and_stale_past_it(name: str, limit: float) -> None:
    snapshot_with_age = SNAPSHOT_WITH_AGE[name]

    failures = safety_pre_check(snapshot_with_age(limit + 0.25))

    assert safety_pre_check(snapshot_with_age(limit)) == []
    assert len(failures) == 1
    assert failures[0].startswith(f"{name} is ")


@pytest.mark.parametrize("missing", ["position_estimate", "drone_status", "battery_voltage", "down_range"])
def test_a_value_that_has_not_arrived_fails(missing: str) -> None:
    fresh = snapshot()
    if missing == "down_range":
        incomplete = replace(fresh, range_readings=replace(fresh.range_readings, down=None))
    else:
        incomplete = replace(fresh, **{missing: None})

    assert safety_pre_check(incomplete) == [f"no {missing.replace('_', ' ')} yet"]


def test_a_failure_says_what_and_by_how_much() -> None:
    assert safety_pre_check(snapshot(position_age=0.5)) == ["position estimate is 0.50 s old (stale after 0.25 s)"]


def test_a_value_that_arrived_just_after_the_tick_time_is_fresh() -> None:
    assert safety_pre_check(snapshot(position_age=-0.01)) == []


def test_a_battery_below_the_landing_voltage_fails() -> None:
    assert safety_pre_check(snapshot(battery_voltage=LOW_BATTERY_VOLTAGE)) == []
    assert safety_pre_check(snapshot(battery_voltage=LOW_BATTERY_VOLTAGE - 0.01)) == [
        "battery at 3.19 V (land below 3.20 V)"
    ]


# A low reading needs a low one before it (ADR-0069). The one-reading test above has no previous reading.


def test_two_battery_readings_in_a_row_below_the_low_battery_limit_fail() -> None:
    low = LOW_BATTERY_VOLTAGE - 0.01

    assert safety_pre_check(snapshot(battery_voltage=low, previous_battery_voltage=low)) == [
        "battery at 3.19 V (land below 3.20 V)"
    ]


def test_one_low_battery_reading_after_one_at_the_limit_passes() -> None:
    low = LOW_BATTERY_VOLTAGE - 0.01

    assert safety_pre_check(snapshot(battery_voltage=low, previous_battery_voltage=LOW_BATTERY_VOLTAGE)) == []


def test_a_battery_reading_at_the_limit_after_a_low_one_passes() -> None:
    previous_low = LOW_BATTERY_VOLTAGE - 0.01

    assert safety_pre_check(snapshot(battery_voltage=LOW_BATTERY_VOLTAGE, previous_battery_voltage=previous_low)) == []


@pytest.mark.parametrize("previous", [math.nan, math.inf])
def test_a_previous_battery_reading_that_isnt_finite_counts_as_low(previous: float) -> None:
    low = LOW_BATTERY_VOLTAGE - 0.01

    assert safety_pre_check(snapshot(battery_voltage=low, previous_battery_voltage=previous)) == [
        "battery at 3.19 V (land below 3.20 V)"
    ]
    assert safety_pre_check(snapshot(battery_voltage=LOW_BATTERY_VOLTAGE, previous_battery_voltage=previous)) == []


@pytest.mark.parametrize("voltage", [math.nan, math.inf])
def test_a_battery_voltage_that_isnt_finite_fails(voltage: float) -> None:
    assert safety_pre_check(snapshot(battery_voltage=voltage)) == [f"battery voltage isn't finite: {voltage} V"]


@pytest.mark.parametrize(
    "position",
    [Vector3(math.nan, 0.0, 0.5), Vector3(0.0, math.inf, 0.5), Vector3(0.0, 0.0, -math.inf)],
)
def test_a_position_estimate_that_isnt_finite_fails(position: Vector3) -> None:
    fresh = snapshot(FLYING)
    broken = replace(fresh, position_estimate=stamped(position, 0.0))

    failures = safety_pre_check(broken)

    assert len(failures) == 1
    assert failures[0].startswith("position estimate isn't finite: (")


def test_a_crashed_drone_fails() -> None:
    assert safety_pre_check(snapshot(replace(FLYING, is_crashed=True))) == ["the drone reports a crash"]


def test_a_tumbled_drone_fails() -> None:
    assert safety_pre_check(snapshot(replace(FLYING, is_tumbled=True))) == ["the drone reports it has tumbled"]


def test_every_failure_is_reported_not_just_the_first() -> None:
    failures = safety_pre_check(snapshot(position_age=1.0, battery_voltage=3.0))

    assert len(failures) == 2


# --- Judging command requests ------------------------------------------------------


def test_arming_is_approved_on_the_floor_only() -> None:
    assert judge(Arm(), snapshot(ON_THE_FLOOR)).is_approved
    assert not judge(Arm(), snapshot(FLYING)).is_approved


def test_taking_off_needs_an_armed_drone_on_the_floor() -> None:
    assert judge(TakeOff(0.5), snapshot(ARMED)).is_approved
    assert judge(TakeOff(0.5), snapshot(ON_THE_FLOOR)).reason == "the drone isn't armed"
    assert judge(TakeOff(0.5), snapshot(FLYING)).reason == "the drone is already flying"


def test_a_take_off_is_approved_at_the_take_off_voltage_and_refused_below_it() -> None:
    assert judge(TakeOff(0.5), snapshot(ARMED, battery_voltage=TAKE_OFF_BATTERY_VOLTAGE)).is_approved
    assert judge(TakeOff(0.5), snapshot(ARMED, battery_voltage=TAKE_OFF_BATTERY_VOLTAGE - 0.01)).reason == (
        "battery at 3.61 V (take off from 3.62 V)"
    )


def test_a_take_off_is_judged_on_the_latest_battery_reading_alone() -> None:
    below = TAKE_OFF_BATTERY_VOLTAGE - 0.01
    after_a_low_one = snapshot(ARMED, battery_voltage=TAKE_OFF_BATTERY_VOLTAGE, previous_battery_voltage=below)
    after_a_high_one = snapshot(ARMED, battery_voltage=below, previous_battery_voltage=TAKE_OFF_BATTERY_VOLTAGE)

    assert judge(TakeOff(0.5), after_a_low_one).is_approved
    assert judge(TakeOff(0.5), after_a_high_one).reason == "battery at 3.61 V (take off from 3.62 V)"


def test_a_take_off_is_refused_without_a_battery_voltage() -> None:
    no_battery = replace(snapshot(ARMED), battery_voltage=None)

    assert judge(TakeOff(0.5), no_battery).reason == "no battery voltage yet"


@pytest.mark.parametrize("voltage", [math.nan, math.inf])
def test_a_take_off_is_refused_on_a_battery_voltage_that_isnt_finite(voltage: float) -> None:
    assert judge(TakeOff(0.5), snapshot(ARMED, battery_voltage=voltage)).reason == (
        f"battery voltage isn't finite: {voltage} V"
    )


@pytest.mark.parametrize("command_request", [Arm(), Hover(), Land()])
def test_only_a_take_off_is_judged_on_the_battery_voltage(command_request: CommandRequest) -> None:
    """A landing must never wait for a charged battery."""
    status = ON_THE_FLOOR if isinstance(command_request, Arm) else FLYING

    assert judge(command_request, snapshot(status, battery_voltage=LOW_BATTERY_VOLTAGE - 0.5)).is_approved


@pytest.mark.parametrize("command_request", [Hover(), Land()])
@pytest.mark.parametrize("status", [ON_THE_FLOOR, ARMED, FLYING], ids=["on the floor", "armed", "flying"])
def test_hovering_and_landing_are_approved_whatever_the_drone_status_says(
    command_request: CommandRequest, status: DroneStatus
) -> None:
    """The adapter decides whether the drone may be flying (ADR-0039): the status lags a take-off."""
    assert judge(command_request, snapshot(status)).is_approved


@pytest.mark.parametrize("command_request", [SetVelocity(Vector3(0.1, 0.0, 0.0)), MoveTo(Vector3(1.0, 0.0, 0.5), 2.0)])
def test_velocity_and_fast_mode_are_refused_until_the_speed_envelope_exists(
    command_request: CommandRequest,
) -> None:
    verdict = judge(command_request, snapshot(FLYING))

    assert not verdict.is_approved
    assert "speed envelope" in verdict.reason


def test_arming_and_taking_off_are_refused_without_a_drone_status() -> None:
    no_status = replace(snapshot(FLYING), drone_status=None)

    assert judge(Arm(), no_status).reason == "no drone status yet"
    assert judge(TakeOff(0.5), no_status).reason == "no drone status yet"


@pytest.mark.parametrize("command_request", [Hover(), Land()])
def test_hovering_and_landing_are_approved_without_a_drone_status(command_request: CommandRequest) -> None:
    """Approved whatever the status, even a missing one: the adapter decides if the drone may be flying (ADR-0039)."""
    no_status = replace(snapshot(FLYING), drone_status=None)

    assert judge(command_request, no_status).is_approved


# --- Sending -----------------------------------------------------------------------


def test_an_approved_request_is_sent_at_the_end_of_the_tick() -> None:
    drone = RecordingDrone()
    safety_layer = SafetyLayer(drone)
    safety_layer.pre_check(snapshot(ON_THE_FLOOR))

    assert safety_layer.request(Arm()).is_approved
    assert drone.command_log == []
    safety_layer.send()

    assert drone.command_log == ["arm"]


def test_a_take_off_is_sent_with_its_height() -> None:
    drone = RecordingDrone()
    safety_layer = SafetyLayer(drone)
    safety_layer.pre_check(snapshot(ARMED))

    safety_layer.request(TakeOff(0.75))
    safety_layer.send()

    assert drone.take_off_heights == [0.75]


@pytest.mark.parametrize(("command_request", "command"), [(Hover(), "hover"), (Land(), "land")])
def test_hover_and_land_are_sent_as_themselves(command_request: CommandRequest, command: str) -> None:
    drone = RecordingDrone()
    safety_layer = SafetyLayer(drone)
    safety_layer.pre_check(snapshot(FLYING))

    safety_layer.request(command_request)
    safety_layer.send()

    assert drone.command_log == [command]


def test_each_command_is_sent_once() -> None:
    drone = RecordingDrone()
    safety_layer = SafetyLayer(drone)
    safety_layer.pre_check(snapshot(ON_THE_FLOOR))
    safety_layer.request(Arm())
    safety_layer.send()

    safety_layer.pre_check(snapshot(ARMED))
    safety_layer.send()

    assert drone.command_log == ["arm"]


def test_a_refused_request_sends_nothing() -> None:
    drone = RecordingDrone()
    safety_layer = SafetyLayer(drone)
    safety_layer.pre_check(snapshot(ON_THE_FLOOR))

    assert not safety_layer.request(TakeOff(0.5)).is_approved  # not armed
    safety_layer.send()

    assert drone.command_log == []


def test_a_request_before_any_pre_check_is_refused() -> None:
    assert not SafetyLayer(RecordingDrone()).request(Arm()).is_approved


# --- The movement slot -----------------------------------------------------------


def test_a_later_request_in_the_same_tick_replaces_the_earlier_with_a_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger=SAFETY_LOGGER)
    drone = RecordingDrone()
    safety_layer = SafetyLayer(drone)
    safety_layer.pre_check(snapshot(FLYING))

    safety_layer.request(Hover())
    safety_layer.request(Land())
    safety_layer.send()

    assert drone.command_log == ["land"]
    assert len(warnings_in(caplog)) == 1
    assert "Land() replaces Hover()" in warnings_in(caplog)[0]


def test_replacements_warn_once_per_streak_and_every_one_is_logged_at_debug(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger=SAFETY_LOGGER)
    safety_layer = SafetyLayer(RecordingDrone())

    def tick(replacements: int) -> None:
        safety_layer.pre_check(snapshot(FLYING))
        safety_layer.request(Hover())
        for _ in range(replacements):
            safety_layer.request(Hover())
        safety_layer.send()

    tick(replacements=2)  # a streak starts: one warning
    tick(replacements=1)  # the streak goes on
    tick(replacements=0)  # the streak ends
    tick(replacements=1)  # a new streak: a new warning

    debug_lines = [r for r in caplog.records if r.levelno == logging.DEBUG]
    assert len(warnings_in(caplog)) == 2
    assert len([r for r in debug_lines if "replaces" in r.getMessage()]) == 4


# --- The buzzer slot (ADR-0053) -----------------------------------------------------

BUZZER_REQUESTS: list[CommandRequest] = [Chirp(), Tone(440.0), Silence()]


@pytest.mark.parametrize("command_request", BUZZER_REQUESTS)
@pytest.mark.parametrize("status", [ON_THE_FLOOR, ARMED, FLYING], ids=["on the floor", "armed", "flying"])
def test_buzzer_requests_are_approved_whatever_the_drone_status_says(
    command_request: CommandRequest, status: DroneStatus
) -> None:
    """Nothing in the buzzer path moves the drone."""
    assert judge(command_request, snapshot(status)).is_approved


@pytest.mark.parametrize("command_request", BUZZER_REQUESTS)
def test_buzzer_requests_are_approved_without_a_drone_status_or_a_charged_battery(
    command_request: CommandRequest,
) -> None:
    low_battery_and_no_status = replace(snapshot(battery_voltage=LOW_BATTERY_VOLTAGE - 0.5), drone_status=None)

    assert judge(command_request, low_battery_and_no_status).is_approved


class BuzzerRecordingDrone(RecordingDrone):
    """Also records every command in one list, buzzer commands with their pitch."""

    def __init__(self) -> None:
        super().__init__()
        self.commands: list[str] = []

    def land(self) -> None:
        self.commands.append("land")
        super().land()

    def chirp(self) -> None:
        self.commands.append("chirp")
        super().chirp()

    def play_tone(self, pitch: float) -> None:
        self.commands.append(f"play_tone {pitch}")
        super().play_tone(pitch)

    def silence(self) -> None:
        self.commands.append("silence")
        super().silence()


@pytest.mark.parametrize(
    ("command_request", "command"),
    [(Chirp(), "chirp"), (Tone(523.25), "play_tone 523.25"), (Silence(), "silence")],
)
def test_a_buzzer_request_is_sent_at_the_end_of_the_tick(command_request: CommandRequest, command: str) -> None:
    drone = BuzzerRecordingDrone()
    safety_layer = SafetyLayer(drone)
    safety_layer.pre_check(snapshot(FLYING))

    assert safety_layer.request(command_request).is_approved
    assert drone.commands == []
    safety_layer.send()

    assert drone.commands == [command]


def test_a_movement_and_a_buzzer_request_in_one_tick_are_both_sent_movement_first(
    caplog: pytest.LogCaptureFixture,
) -> None:
    drone = BuzzerRecordingDrone()
    safety_layer = SafetyLayer(drone)
    safety_layer.pre_check(snapshot(FLYING))

    safety_layer.request(Chirp())
    safety_layer.request(Land())
    safety_layer.send()

    assert drone.commands == ["land", "chirp"]
    assert warnings_in(caplog) == []


def test_a_later_buzzer_request_in_the_same_tick_replaces_the_earlier_with_a_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger=SAFETY_LOGGER)
    drone = BuzzerRecordingDrone()
    safety_layer = SafetyLayer(drone)
    safety_layer.pre_check(snapshot(ON_THE_FLOOR))

    safety_layer.request(Tone(440.0))
    safety_layer.request(Silence())
    safety_layer.send()

    assert drone.commands == ["silence"]
    assert len(warnings_in(caplog)) == 1
    assert "Two buzzer requests in one tick: Silence() replaces Tone(pitch=440.0)" in warnings_in(caplog)[0]


def test_each_slot_has_its_own_replacement_streak(caplog: pytest.LogCaptureFixture) -> None:
    """A movement streak going on doesn't hide the start of a buzzer streak."""
    safety_layer = SafetyLayer(BuzzerRecordingDrone())

    safety_layer.pre_check(snapshot(FLYING))
    safety_layer.request(Hover())
    safety_layer.request(Hover())  # a movement streak starts
    safety_layer.send()
    safety_layer.pre_check(snapshot(FLYING))
    safety_layer.request(Hover())
    safety_layer.request(Hover())  # the movement streak goes on
    safety_layer.request(Chirp())
    safety_layer.request(Chirp())  # a buzzer streak starts
    safety_layer.send()

    assert [message.split(":")[0] for message in warnings_in(caplog)] == [
        "Two movement requests in one tick",
        "Two buzzer requests in one tick",
    ]


def test_after_the_failsafe_buzzer_requests_are_refused_too() -> None:
    drone = BuzzerRecordingDrone()
    safety_layer = SafetyLayer(drone)
    safety_layer.pre_check(snapshot(FLYING, position_age=1.0))
    safety_layer.send()

    safety_layer.pre_check(snapshot(FLYING))
    verdict = safety_layer.request(Chirp())
    safety_layer.send()

    assert verdict.reason == "the flight is over: the safety pre-check failed"
    assert drone.commands == ["land"]


# --- The failsafe ------------------------------------------------------------------


def test_a_failed_pre_check_lands_a_flying_drone_and_skips_behaviors(
    caplog: pytest.LogCaptureFixture,
) -> None:
    drone = RecordingDrone()
    safety_layer = SafetyLayer(drone)

    behaviors_may_run = safety_layer.pre_check(snapshot(FLYING, battery_voltage=3.1))
    safety_layer.send()

    assert not behaviors_may_run
    assert drone.command_log == ["land"]
    assert safety_layer.pre_check_has_failed
    assert warnings_in(caplog) == ["Safety pre-check failed: battery at 3.10 V (land below 3.20 V). Landing."]


def test_the_failsafe_lands_on_a_stale_drone_status_that_says_flying() -> None:
    drone = RecordingDrone()
    safety_layer = SafetyLayer(drone)

    safety_layer.pre_check(snapshot(FLYING, status_age=1.0))
    safety_layer.send()

    assert drone.command_log == ["land"]


@pytest.mark.parametrize("status", [ON_THE_FLOOR, ARMED, FLYING], ids=["on the floor", "armed", "flying"])
def test_the_failsafe_always_lands_and_leaves_whether_the_drone_may_be_flying_to_the_adapter(
    status: DroneStatus, caplog: pytest.LogCaptureFixture
) -> None:
    """The status lags a take-off by about a second, so it can't gate the landing (ADR-0039)."""
    drone = RecordingDrone()
    safety_layer = SafetyLayer(drone)

    safety_layer.pre_check(snapshot(status, position_age=1.0))
    safety_layer.send()

    assert drone.command_log == ["land"]
    assert safety_layer.pre_check_has_failed
    assert warnings_in(caplog) == [
        "Safety pre-check failed: position estimate is 1.00 s old (stale after 0.25 s). Landing."
    ]


def test_the_failsafe_lands_without_any_drone_status() -> None:
    drone = RecordingDrone()
    safety_layer = SafetyLayer(drone)

    safety_layer.pre_check(replace(snapshot(FLYING), drone_status=None))
    safety_layer.send()

    assert drone.command_log == ["land"]


def test_after_the_failsafe_the_flight_never_resumes() -> None:
    drone = RecordingDrone()
    safety_layer = SafetyLayer(drone)
    safety_layer.pre_check(snapshot(FLYING, position_age=1.0))
    safety_layer.send()

    behaviors_may_run = safety_layer.pre_check(snapshot(FLYING))  # fresh again
    verdict = safety_layer.request(Hover())
    safety_layer.send()

    assert not behaviors_may_run
    assert verdict.reason == "the flight is over: the safety pre-check failed"
    assert drone.command_log == ["land"]  # the failsafe's landing, sent once


# --- The velocity uncertainty and the estimate reset (ADR-0054) -----------------------

NO_FLOW = FLOW_VELOCITY_UNCERTAINTY * 3
"""Meters per second: a velocity uncertainty without flow."""


def with_estimate(base: Snapshot, *, position: Vector3 = Vector3.ZERO, velocity: Vector3 = Vector3.ZERO) -> Snapshot:
    assert base.position_estimate is not None
    assert base.velocity_estimate is not None
    return replace(
        base,
        position_estimate=replace(base.position_estimate, value=position),
        velocity_estimate=replace(base.velocity_estimate, value=velocity),
    )


def with_down_range(base: Snapshot, reading: RangeReading) -> Snapshot:
    down = base.range_readings.down
    assert down is not None
    return replace(base, range_readings=replace(base.range_readings, down=replace(down, value=reading)))


@pytest.mark.parametrize(
    ("height", "limit"),
    [(-0.1, 0.03), (0.0, 0.03), (0.2, 0.03), (0.3, 0.03), (0.4, 0.04), (0.5, 0.05), (1.0, 0.1), (3.0, 0.1)],
)
def test_the_in_flight_limit_is_0_03_up_to_0_3_m_then_grows_with_height_to_0_1_at_1_m(
    height: float, limit: float
) -> None:
    """ADR-0064."""
    assert in_flight_velocity_uncertainty_limit(height) == pytest.approx(limit)


@pytest.mark.parametrize("height", [None, math.nan, math.inf, -math.inf])
def test_an_unknown_height_gets_the_strictest_in_flight_limit(height: float | None) -> None:
    assert in_flight_velocity_uncertainty_limit(height) == 0.03


def test_in_flight_a_velocity_uncertainty_not_under_the_limit_at_its_height_fails() -> None:
    at_half_a_meter = snapshot(FLYING)  # the limit is 0.05 here
    low_down = with_estimate(snapshot(FLYING, velocity_uncertainty=0.03), position=Vector3(0.0, 0.0, 0.2))

    assert safety_pre_check(replace(at_half_a_meter, velocity_uncertainty=stamped(0.04, 0.0))) == []
    assert safety_pre_check(replace(at_half_a_meter, velocity_uncertainty=stamped(0.0499, 0.0))) == []
    [at_the_limit] = safety_pre_check(replace(at_half_a_meter, velocity_uncertainty=stamped(0.05, 0.0)))
    assert at_the_limit == "velocity uncertainty 0.050 m/s in flight, must be under 0.05 at 0.50 m: no flow"
    [low_down_at_the_limit] = safety_pre_check(low_down)
    assert low_down_at_the_limit == "velocity uncertainty 0.030 m/s in flight, must be under 0.03 at 0.20 m: no flow"


def test_in_flight_with_a_missing_stale_or_non_finite_height_the_strictest_limit_applies() -> None:
    """Each of these fails the pre-check anyway; the message shows the limit used (ADR-0064)."""
    hovering = snapshot(FLYING, velocity_uncertainty=0.04)  # under the limit at 0.5 m
    missing = replace(hovering, position_estimate=None)
    stale = snapshot(FLYING, velocity_uncertainty=0.04, position_age=STALE_AFTER + 0.01)
    not_finite = with_estimate(hovering, position=Vector3(0.0, 0.0, math.nan))

    for unknown_height in (missing, stale, not_finite):
        failures = safety_pre_check(unknown_height)
        assert "velocity uncertainty 0.040 m/s in flight, must be under 0.03 at an unknown height: no flow" in failures
        assert len(failures) == 2  # the position estimate's own failure, too


def test_the_take_off_rule_keeps_its_flow_threshold_whatever_the_height() -> None:
    """Only the in-flight check's limit grows with height (ADR-0064): 0.04 is no flow for a take-off."""
    away_from_the_reset_point = Vector3(0.0, TAKE_OFF_MAX_DISTANCE_FROM_RESET_POINT + 0.01, 0.5)
    with_flow = with_estimate(
        snapshot(ARMED, velocity_uncertainty=FLOW_VELOCITY_UNCERTAINTY * 0.99), position=away_from_the_reset_point
    )
    without_flow = with_estimate(snapshot(ARMED, velocity_uncertainty=0.04), position=away_from_the_reset_point)

    assert not judge(TakeOff(1.0), with_flow).is_approved  # with flow, the estimate is checked
    assert judge(TakeOff(1.0), without_flow).is_approved  # without, it isn't


@pytest.mark.parametrize("uncertainty", [math.nan, math.inf])
def test_in_flight_a_velocity_uncertainty_that_isnt_finite_fails(uncertainty: float) -> None:
    assert safety_pre_check(snapshot(FLYING, velocity_uncertainty=uncertainty)) != []


def test_in_flight_a_missing_or_stale_velocity_uncertainty_fails() -> None:
    missing = replace(snapshot(FLYING), velocity_uncertainty=None)
    stale = snapshot(FLYING, velocity_uncertainty_age=STALE_AFTER + 0.01)

    assert safety_pre_check(missing) == ["no velocity uncertainty yet"]
    assert "velocity uncertainty is" in safety_pre_check(stale)[0]


def test_on_the_floor_the_pre_check_ignores_the_velocity_uncertainty() -> None:
    dark_floor = snapshot(ARMED, velocity_uncertainty=NO_FLOW)

    assert safety_pre_check(dark_floor) == []
    assert safety_pre_check(replace(dark_floor, velocity_uncertainty=None)) == []


def test_after_the_motors_stop_the_pre_check_ignores_the_velocity_uncertainty() -> None:
    # The drone status says flying for 2 s after the motors stop; "may be flying" doesn't (ADR-0060).
    landed_on_a_dark_floor = snapshot(FLYING, velocity_uncertainty=NO_FLOW, may_be_flying=False)

    assert safety_pre_check(landed_on_a_dark_floor) == []


def test_while_the_drone_may_be_flying_the_pre_check_checks_the_velocity_uncertainty_whatever_the_status() -> None:
    assert safety_pre_check(snapshot(ARMED, velocity_uncertainty=NO_FLOW, may_be_flying=True)) != []


def test_during_the_initial_climb_the_pre_check_ignores_the_velocity_uncertainty() -> None:
    climbing_without_flow = snapshot(FLYING, velocity_uncertainty=NO_FLOW, is_in_initial_climb=True)

    assert safety_pre_check(climbing_without_flow) == []


def test_a_take_off_is_refused_unless_the_down_range_reads_the_floor() -> None:
    above_the_floor = with_down_range(snapshot(ARMED), RangeReading.at_distance(TOUCHDOWN_DOWN_RANGE + 0.01))
    no_distance = with_down_range(snapshot(ARMED), RangeReading.out_of_range())

    assert judge(TakeOff(1.0), with_down_range(snapshot(ARMED), RangeReading.at_distance(TOUCHDOWN_DOWN_RANGE)))
    for refused in (above_the_floor, no_distance):
        verdict = judge(TakeOff(1.0), refused)
        assert not verdict.is_approved
        assert "doesn't read the floor" in verdict.reason


def test_with_flow_a_take_off_is_refused_when_the_estimate_moves() -> None:
    moving = Vector3(FLOOR_MAX_SPEED * 0.6, FLOOR_MAX_SPEED * 0.8, 0.0)  # exactly the limit
    nearly = Vector3(FLOOR_MAX_SPEED * 0.9, 0.0, 0.0)

    assert judge(TakeOff(1.0), with_estimate(snapshot(ARMED), velocity=nearly)).is_approved
    verdict = judge(TakeOff(1.0), with_estimate(snapshot(ARMED), velocity=moving))
    assert not verdict.is_approved
    assert "moving" in verdict.reason


def test_with_flow_a_take_off_is_refused_away_from_the_reset_point() -> None:
    limit = TAKE_OFF_MAX_DISTANCE_FROM_RESET_POINT
    at_the_limit = Vector3(limit * 0.6, -limit * 0.8, 0.02)
    past_it = Vector3(0.0, limit + 0.01, 0.0)

    assert judge(TakeOff(1.0), with_estimate(snapshot(ARMED), position=at_the_limit)).is_approved
    verdict = judge(TakeOff(1.0), with_estimate(snapshot(ARMED), position=past_it))
    assert not verdict.is_approved
    assert "reset point" in verdict.reason


def test_without_flow_a_take_off_goes_ahead_whatever_the_estimate() -> None:
    runaway = with_estimate(
        snapshot(ARMED, velocity_uncertainty=NO_FLOW), position=Vector3(-87.0, 3.0, 0.0), velocity=Vector3(1.0, 0, 0)
    )

    assert judge(TakeOff(1.0), runaway).is_approved


def test_a_take_off_is_refused_without_a_fresh_velocity_uncertainty() -> None:
    missing = replace(snapshot(ARMED), velocity_uncertainty=None)
    stale = snapshot(ARMED, velocity_uncertainty_age=STALE_AFTER + 0.01)
    not_a_number = snapshot(ARMED, velocity_uncertainty=math.nan)

    for refused in (missing, stale, not_a_number):
        assert judge(TakeOff(1.0), refused) == Verdict.refused("no fresh velocity uncertainty")


def test_an_estimate_reset_is_approved_only_on_the_floor() -> None:
    assert judge(ResetEstimate(), snapshot(ARMED, velocity_uncertainty=NO_FLOW)).is_approved
    assert not judge(ResetEstimate(), snapshot(FLYING)).is_approved
    lifted = with_down_range(snapshot(ON_THE_FLOOR), RangeReading.at_distance(0.3))
    assert not judge(ResetEstimate(), lifted).is_approved


def test_an_approved_estimate_reset_is_sent_after_the_slots_commands_and_takes_no_slot() -> None:
    drone = RecordingDrone()
    drone.connect()
    safety_layer = SafetyLayer(drone)
    safety_layer.pre_check(snapshot(ON_THE_FLOOR))

    safety_layer.request(ResetEstimate())
    safety_layer.request(Arm())
    safety_layer.request(Chirp())
    safety_layer.send()

    assert drone.command_log[-3:] == ["arm", "chirp", "reset_estimate"]


def test_a_refused_estimate_reset_is_not_sent() -> None:
    drone = RecordingDrone()
    safety_layer = SafetyLayer(drone)
    safety_layer.pre_check(snapshot(FLYING))

    assert not safety_layer.request(ResetEstimate()).is_approved
    safety_layer.send()

    assert "reset_estimate" not in drone.command_log


def test_an_estimate_reset_is_sent_once_per_approval() -> None:
    drone = RecordingDrone()
    safety_layer = SafetyLayer(drone)
    safety_layer.pre_check(snapshot(ON_THE_FLOOR))
    safety_layer.request(ResetEstimate())
    safety_layer.send()
    safety_layer.pre_check(snapshot(ON_THE_FLOOR))
    safety_layer.send()

    assert drone.command_log.count("reset_estimate") == 1
