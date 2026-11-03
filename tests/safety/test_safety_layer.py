"""The minimal safety layer for First flight (ADR-0030): pre-check, judging, sending."""

import logging
import math
from collections.abc import Callable
from dataclasses import replace

import pytest

from crazyflie_behavior.drone.mock_adapter import MockAdapter
from crazyflie_behavior.geometry import Vector3
from crazyflie_behavior.loop.tick_loop import TICK_RATE
from crazyflie_behavior.safety.requests import (
    Arm,
    CommandRequest,
    Hover,
    Land,
    MoveTo,
    SetVelocity,
    TakeOff,
)
from crazyflie_behavior.safety.safety_layer import (
    BATTERY_STALE_AFTER,
    LOW_BATTERY_VOLTAGE,
    MAX_NEGATIVE_AGE,
    STALE_AFTER,
    SafetyLayer,
    judge,
    safety_pre_check,
    values_from_the_future,
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

ON_THE_FLOOR = DroneStatus(is_armed=False, is_flying=False, is_crashed=False, is_tumbled=False)
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
) -> Snapshot:
    """A hand-built snapshot: everything fresh and the battery charged, unless asked otherwise."""
    height = 0.5 if status.is_flying else 0.0
    return Snapshot(
        time=NOW,
        dt=0.05,
        position_estimate=stamped(Vector3(0.0, 0.0, height), position_age),
        velocity_estimate=stamped(Vector3.ZERO, position_age),
        range_readings=RangeReadings(
            front=None,
            back=None,
            left=None,
            right=None,
            up=None,
            down=stamped(RangeReading.at_distance(height), down_age),
        ),
        battery_voltage=stamped(battery_voltage, battery_age),
        drone_status=stamped(status, status_age),
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
        "battery at 3.39 V (land below 3.40 V)"
    ]


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


# --- Values from the future (ADR-0042) ---------------------------------------------


def test_the_largest_negative_age_that_counts_as_normal_is_one_tick_period() -> None:
    # A copy of the tick period, not an import (the safety layer doesn't depend on the loop package).
    assert pytest.approx(1.0 / TICK_RATE) == MAX_NEGATIVE_AGE


def test_a_slightly_negative_age_passes_the_pre_check_without_a_warning(caplog: pytest.LogCaptureFixture) -> None:
    safety_layer = SafetyLayer(RecordingDrone())

    with caplog.at_level(logging.WARNING, logger=SAFETY_LOGGER):
        results = [safety_layer.pre_check(snapshot(FLYING, position_age=-0.01)) for _ in range(3)]

    assert results == [True, True, True]
    assert warnings_in(caplog) == []


def test_the_warning_starts_just_past_one_tick_period_not_just_inside_it(caplog: pytest.LogCaptureFixture) -> None:
    safety_layer = SafetyLayer(RecordingDrone())

    with caplog.at_level(logging.WARNING, logger=SAFETY_LOGGER):
        safety_layer.pre_check(snapshot(FLYING, position_age=-MAX_NEGATIVE_AGE + 0.01))
        assert warnings_in(caplog) == []
        safety_layer.pre_check(snapshot(FLYING, position_age=-MAX_NEGATIVE_AGE - 0.01))

    assert len(warnings_in(caplog)) == 1


def test_a_large_negative_age_passes_the_pre_check_and_warns_once_per_streak(
    caplog: pytest.LogCaptureFixture,
) -> None:
    safety_layer = SafetyLayer(RecordingDrone())

    with caplog.at_level(logging.WARNING, logger=SAFETY_LOGGER):
        streak = [safety_layer.pre_check(snapshot(FLYING, position_age=-1.0)) for _ in range(4)]
        assert len(warnings_in(caplog)) == 1
        safety_layer.pre_check(snapshot(FLYING))  # a normal age ends the streak
        safety_layer.pre_check(snapshot(FLYING, position_age=-1.0))  # and a new one starts

    assert streak == [True, True, True, True]  # the warning never fails the pre-check
    assert not safety_layer.pre_check_has_failed
    assert len(warnings_in(caplog)) == 2
    assert "position estimate arrived 1.00 s after the tick's time" in warnings_in(caplog)[0]


def test_each_value_has_its_own_streak(caplog: pytest.LogCaptureFixture) -> None:
    safety_layer = SafetyLayer(RecordingDrone())

    with caplog.at_level(logging.WARNING, logger=SAFETY_LOGGER):
        safety_layer.pre_check(snapshot(FLYING, position_age=-1.0))
        safety_layer.pre_check(snapshot(FLYING, position_age=-1.0, battery_age=-1.0))
        safety_layer.pre_check(snapshot(FLYING, position_age=-1.0, battery_age=-1.0))

    assert len(warnings_in(caplog)) == 2
    assert "position estimate" in warnings_in(caplog)[0]
    assert "battery voltage" in warnings_in(caplog)[1]


def test_the_values_from_the_future_are_found_by_name_with_their_ages() -> None:
    found = values_from_the_future(snapshot(FLYING, position_age=-1.0, down_age=-0.01, status_age=-0.5))

    assert found == {"position estimate": pytest.approx(-1.0), "drone status": pytest.approx(-0.5)}


# --- Judging command requests ------------------------------------------------------


def test_arming_is_approved_on_the_floor_only() -> None:
    assert judge(Arm(), snapshot(ON_THE_FLOOR)).is_approved
    assert not judge(Arm(), snapshot(FLYING)).is_approved


def test_taking_off_needs_an_armed_drone_on_the_floor() -> None:
    assert judge(TakeOff(0.5), snapshot(ARMED)).is_approved
    assert judge(TakeOff(0.5), snapshot(ON_THE_FLOOR)).reason == "the drone isn't armed"
    assert judge(TakeOff(0.5), snapshot(FLYING)).reason == "the drone is already flying"


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
    """A missing status counts as flying: hover and land fly when unsure (ADR-0039)."""
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


# --- The failsafe ------------------------------------------------------------------


def test_a_failed_pre_check_lands_a_flying_drone_and_skips_behaviors(
    caplog: pytest.LogCaptureFixture,
) -> None:
    drone = RecordingDrone()
    safety_layer = SafetyLayer(drone)

    behaviors_may_run = safety_layer.pre_check(snapshot(FLYING, battery_voltage=3.3))
    safety_layer.send()

    assert not behaviors_may_run
    assert drone.command_log == ["land"]
    assert safety_layer.pre_check_has_failed
    assert warnings_in(caplog) == ["Safety pre-check failed: battery at 3.30 V (land below 3.40 V). Landing."]


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
