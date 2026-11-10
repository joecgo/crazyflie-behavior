"""The failsafe test (ADR-0041), with hand-built snapshots and a stand-in for the safety layer."""

import logging
import math
from dataclasses import replace

import pytest

from crazyflie_behavior.behaviors.failsafe_test import (
    HEIGHT_TOLERANCE,
    HOVER_TIME_LIMIT,
    FailsafeTest,
    is_at_take_off_height,
)
from crazyflie_behavior.behaviors.hover_test import ARM_TIME_LIMIT, TAKE_OFF_TIME_LIMIT
from crazyflie_behavior.geometry import Vector3
from crazyflie_behavior.safety.requests import Arm, CommandRequest, Land, TakeOff, Verdict
from crazyflie_behavior.snapshot import DroneStatus, RangeReading, RangeReadings, Snapshot, Stamped

HEIGHT = 0.5

ON_THE_FLOOR = DroneStatus(
    is_armed=False, is_flying=False, is_crashed=False, is_tumbled=False, can_arm=True, is_locked=False
)
ARMED = replace(ON_THE_FLOOR, is_armed=True)
FLYING = replace(ARMED, is_flying=True)


class SafetyLayerStandIn:
    """Records every command request and approves it, unless told to refuse."""

    def __init__(self, refuse_with: str | None = None) -> None:
        self.requests: list[CommandRequest] = []
        self._refuse_with = refuse_with

    def __call__(self, command_request: CommandRequest) -> Verdict:
        self.requests.append(command_request)
        if self._refuse_with is not None:
            return Verdict.refused(self._refuse_with)
        return Verdict.approved()


def snapshot(time: float, status: DroneStatus, height: float = 0.0) -> Snapshot:
    def fresh[T](value: T) -> Stamped[T]:
        return Stamped(value, arrival_time=time, drone_time=None)

    return Snapshot(
        time=time,
        dt=0.05,
        position_estimate=fresh(Vector3(0.0, 0.0, height)),
        velocity_estimate=fresh(Vector3.ZERO),
        velocity_uncertainty=fresh(0.01),
        range_readings=RangeReadings(None, None, None, None, None, fresh(RangeReading.at_distance(height))),
        battery_voltage=fresh(4.0),
        drone_status=fresh(status),
        is_in_initial_climb=False,
        may_be_flying=status.is_flying,
    )


def hovering_test(safety_layer: SafetyLayerStandIn) -> FailsafeTest:
    """A failsafe test that armed at 0 s, took off at 0.25 s and reached the height at 0.5 s."""
    failsafe_test = FailsafeTest(HEIGHT)
    failsafe_test.tick(snapshot(0.0, ON_THE_FLOOR), safety_layer)
    failsafe_test.tick(snapshot(0.25, ARMED), safety_layer)
    failsafe_test.tick(snapshot(0.5, FLYING, HEIGHT), safety_layer)
    safety_layer.requests.clear()
    return failsafe_test


# --- The sequence -------------------------------------------------------------------


def test_it_arms_takes_off_to_the_height_and_hovers() -> None:
    safety_layer = SafetyLayerStandIn()
    failsafe_test = FailsafeTest(HEIGHT)

    done = [
        failsafe_test.tick(snapshot(0.0, ON_THE_FLOOR), safety_layer),
        failsafe_test.tick(snapshot(0.25, ARMED), safety_layer),
        failsafe_test.tick(snapshot(0.5, FLYING, HEIGHT), safety_layer),
        failsafe_test.tick(snapshot(0.75, FLYING, HEIGHT), safety_layer),
    ]

    assert safety_layer.requests == [Arm(), TakeOff(HEIGHT)]
    assert done == [False, False, False, False]
    assert not failsafe_test.has_failed


def test_it_takes_off_to_the_height_it_was_given() -> None:
    safety_layer = SafetyLayerStandIn()
    failsafe_test = FailsafeTest(0.1)
    failsafe_test.tick(snapshot(0.0, ON_THE_FLOOR), safety_layer)

    failsafe_test.tick(snapshot(0.25, ARMED), safety_layer)

    assert safety_layer.requests == [Arm(), TakeOff(0.1)]


def test_hovering_never_ends_by_itself_before_the_time_limit() -> None:
    """The failsafe ends the flight: the safety layer skips the behavior from then on (ADR-0026)."""
    safety_layer = SafetyLayerStandIn()
    failsafe_test = hovering_test(safety_layer)

    done = failsafe_test.tick(snapshot(0.5 + HOVER_TIME_LIMIT - 0.05, FLYING, HEIGHT), safety_layer)

    assert not done
    assert safety_layer.requests == []
    assert not failsafe_test.has_failed


@pytest.mark.parametrize("height", [0.1, 0.5])
def test_the_floor_is_not_the_take_off_height_even_for_the_low_one(height: float) -> None:
    assert is_at_take_off_height(height, height)
    assert not is_at_take_off_height(0.0, height)
    assert not is_at_take_off_height(2 * height, height)


@pytest.mark.parametrize("height", [0.1, 0.5])
def test_within_the_height_tolerance_of_the_take_off_height_counts_as_there(height: float) -> None:
    assert is_at_take_off_height(height + HEIGHT_TOLERANCE - 0.001, height)
    assert is_at_take_off_height(height - HEIGHT_TOLERANCE + 0.001, height)
    assert not is_at_take_off_height(height + HEIGHT_TOLERANCE + 0.001, height)
    assert not is_at_take_off_height(height - HEIGHT_TOLERANCE - 0.001, height)


@pytest.mark.parametrize("height", [0.0, -0.1, math.nan, math.inf])
def test_a_take_off_height_that_isnt_a_positive_number_is_refused(height: float) -> None:
    with pytest.raises(ValueError, match="Take-off height must be a positive number"):
        FailsafeTest(height)


# --- When the fault never takes effect -------------------------------------------------


def test_a_fault_that_never_takes_effect_lands_the_drone_normally_and_fails_the_test(
    caplog: pytest.LogCaptureFixture,
) -> None:
    safety_layer = SafetyLayerStandIn()
    failsafe_test = hovering_test(safety_layer)

    with caplog.at_level(logging.ERROR):
        done = failsafe_test.tick(snapshot(0.5 + HOVER_TIME_LIMIT + 0.05, FLYING, HEIGHT), safety_layer)

    assert not done  # it waits for the landing
    assert safety_layer.requests == [Land()]
    assert failsafe_test.has_failed
    assert f"didn't land the drone within {HOVER_TIME_LIMIT:g} s of hovering. Landing" in caplog.text


def test_after_the_normal_landing_it_reports_done() -> None:
    safety_layer = SafetyLayerStandIn()
    failsafe_test = hovering_test(safety_layer)
    failsafe_test.tick(snapshot(0.5 + HOVER_TIME_LIMIT + 0.05, FLYING, HEIGHT), safety_layer)

    still_flying = failsafe_test.tick(snapshot(11.0, FLYING, 0.2), safety_layer)
    landed = failsafe_test.tick(snapshot(11.05, ARMED, 0.0), safety_layer)

    assert not still_flying
    assert landed


# --- Failures (ADR-0033: it stops at its first refused request) -------------------------


def test_a_refused_request_ends_the_test_with_an_error_naming_the_reason(caplog: pytest.LogCaptureFixture) -> None:
    safety_layer = SafetyLayerStandIn(refuse_with="the drone is already flying")

    with caplog.at_level(logging.ERROR):
        done = FailsafeTest(HEIGHT).tick(snapshot(0.0, FLYING, HEIGHT), safety_layer)

    assert done
    assert "Arm() was refused: the drone is already flying" in caplog.text


def test_arming_too_slowly_ends_the_test_at_once(caplog: pytest.LogCaptureFixture) -> None:
    safety_layer = SafetyLayerStandIn()
    failsafe_test = FailsafeTest(HEIGHT)
    failsafe_test.tick(snapshot(0.0, ON_THE_FLOOR), safety_layer)

    with caplog.at_level(logging.ERROR):
        done = failsafe_test.tick(snapshot(ARM_TIME_LIMIT + 0.1, ON_THE_FLOOR), safety_layer)

    assert done
    assert failsafe_test.has_failed
    assert safety_layer.requests == [Arm()]  # nothing flies, so no landing
    assert "didn't report armed" in caplog.text


def test_a_take_off_that_doesnt_reach_the_height_lands_first(caplog: pytest.LogCaptureFixture) -> None:
    safety_layer = SafetyLayerStandIn()
    failsafe_test = FailsafeTest(HEIGHT)
    failsafe_test.tick(snapshot(0.0, ON_THE_FLOOR), safety_layer)
    failsafe_test.tick(snapshot(0.25, ARMED), safety_layer)

    with caplog.at_level(logging.ERROR):
        done = failsafe_test.tick(snapshot(0.25 + TAKE_OFF_TIME_LIMIT + 0.1, FLYING, 0.2), safety_layer)

    assert not done  # it waits for the landing
    assert failsafe_test.has_failed
    assert safety_layer.requests == [Arm(), TakeOff(HEIGHT), Land()]
    assert "not at 0.50 m" in caplog.text


def test_a_tick_without_a_drone_status_or_position_is_a_bug_the_safety_pre_check_rules_out() -> None:
    no_status = replace(snapshot(0.0, ON_THE_FLOOR), drone_status=None)

    with pytest.raises(RuntimeError, match="without a drone status or position"):
        FailsafeTest(HEIGHT).tick(no_status, SafetyLayerStandIn())
