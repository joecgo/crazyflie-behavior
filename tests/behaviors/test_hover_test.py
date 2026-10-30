"""The hover test (ADR-0030), with hand-built snapshots and a stand-in for the safety layer."""

import logging
import math
from dataclasses import replace

import pytest

from crazyflie_behavior.behaviors.hover_test import (
    ARM_TIME_LIMIT,
    TAKE_OFF_HEIGHT,
    TAKE_OFF_TIME_LIMIT,
    HoverTest,
)
from crazyflie_behavior.geometry import Vector3
from crazyflie_behavior.safety.requests import Arm, CommandRequest, Land, TakeOff, Verdict
from crazyflie_behavior.snapshot import DroneStatus, RangeReading, RangeReadings, Snapshot, Stamped

HOVER_DURATION = 2.0

ON_THE_FLOOR = DroneStatus(is_armed=False, is_flying=False, is_crashed=False, is_tumbled=False)
ARMED = replace(ON_THE_FLOOR, is_armed=True)
FLYING = replace(ARMED, is_flying=True)


class SafetyLayerStandIn:
    """Records every command request and approves it, unless told to refuse."""

    def __init__(self, refuse_with: str | None = None) -> None:
        self.requests: list[CommandRequest] = []
        self._refuse_with = refuse_with

    def __call__(self, request: CommandRequest) -> Verdict:
        self.requests.append(request)
        if self._refuse_with is not None:
            return Verdict.refused(self._refuse_with)
        return Verdict.approved()


def snapshot(time: float, status: DroneStatus, height: float = 0.0) -> Snapshot:
    """A fresh snapshot at `time`, with the drone at `height`."""

    def fresh[T](value: T) -> Stamped[T]:
        return Stamped(value, arrival_time=time, drone_time=None)

    return Snapshot(
        time=time,
        dt=0.05,
        position_estimate=fresh(Vector3(0.0, 0.0, height)),
        velocity_estimate=fresh(Vector3.ZERO),
        range_readings=RangeReadings(
            None, None, None, None, None, fresh(RangeReading.at_distance(height))
        ),
        battery_voltage=fresh(4.0),
        drone_status=fresh(status),
    )


def hovering_test(safety_layer: SafetyLayerStandIn) -> HoverTest:
    """A hover test that armed at 0 s, took off at 0.25 s and reached the height at 0.5 s."""
    hover_test = HoverTest(HOVER_DURATION)
    hover_test.tick(snapshot(0.0, ON_THE_FLOOR), safety_layer)
    hover_test.tick(snapshot(0.25, ARMED), safety_layer)
    hover_test.tick(snapshot(0.5, FLYING, TAKE_OFF_HEIGHT), safety_layer)
    return hover_test


def errors_in(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [r.getMessage() for r in caplog.records if r.levelno == logging.ERROR]


def test_it_asks_to_arm_first() -> None:
    safety_layer = SafetyLayerStandIn()

    HoverTest().tick(snapshot(0.0, ON_THE_FLOOR), safety_layer)

    assert safety_layer.requests == [Arm()]


def test_it_takes_off_only_once_the_drone_reports_armed() -> None:
    safety_layer = SafetyLayerStandIn()
    hover_test = HoverTest()
    hover_test.tick(snapshot(0.0, ON_THE_FLOOR), safety_layer)

    hover_test.tick(snapshot(0.25, ON_THE_FLOOR), safety_layer)  # arming hasn't shown yet
    requests_before_armed = list(safety_layer.requests)
    hover_test.tick(snapshot(0.5, ARMED), safety_layer)

    assert requests_before_armed == [Arm()]
    assert safety_layer.requests == [Arm(), TakeOff(TAKE_OFF_HEIGHT)]


def test_it_stops_if_the_drone_never_reports_armed(caplog: pytest.LogCaptureFixture) -> None:
    safety_layer = SafetyLayerStandIn()
    hover_test = HoverTest()
    hover_test.tick(snapshot(0.0, ON_THE_FLOOR), safety_layer)

    still_waiting = hover_test.tick(snapshot(ARM_TIME_LIMIT, ON_THE_FLOOR), safety_layer)
    is_done = hover_test.tick(snapshot(ARM_TIME_LIMIT + 0.25, ON_THE_FLOOR), safety_layer)

    assert not still_waiting
    assert is_done
    assert safety_layer.requests == [Arm()]
    assert errors_in(caplog) == ["Hover test failed: the drone didn't report armed within 2 s"]


def test_it_starts_hovering_once_close_to_the_take_off_height() -> None:
    safety_layer = SafetyLayerStandIn()
    hover_test = HoverTest(hover_duration=0.0)
    hover_test.tick(snapshot(0.0, ON_THE_FLOOR), safety_layer)
    hover_test.tick(snapshot(0.25, ARMED), safety_layer)

    hover_test.tick(snapshot(0.5, FLYING, height=0.375), safety_layer)  # 0.125 m short
    hover_test.tick(snapshot(0.75, FLYING, height=0.4375), safety_layer)  # close enough
    requests_when_it_got_there = list(safety_layer.requests)
    hover_test.tick(snapshot(1.0, FLYING, height=0.5), safety_layer)

    assert requests_when_it_got_there == [Arm(), TakeOff(TAKE_OFF_HEIGHT)]
    assert safety_layer.requests[-1] == Land()  # hovered for 0 s, so it lands


def test_it_hovers_for_the_hover_duration_then_lands() -> None:
    safety_layer = SafetyLayerStandIn()
    hover_test = hovering_test(safety_layer)  # hovering since 0.5 s

    hover_test.tick(snapshot(0.5 + HOVER_DURATION - 0.25, FLYING, 0.5), safety_layer)
    requests_before_the_end = list(safety_layer.requests)
    hover_test.tick(snapshot(0.5 + HOVER_DURATION, FLYING, 0.5), safety_layer)

    assert Land() not in requests_before_the_end
    assert safety_layer.requests[-1] == Land()


def test_it_is_done_once_the_drone_reports_it_landed() -> None:
    safety_layer = SafetyLayerStandIn()
    hover_test = hovering_test(safety_layer)
    hover_test.tick(snapshot(3.0, FLYING, 0.5), safety_layer)  # lands

    still_landing = hover_test.tick(snapshot(3.25, FLYING, 0.25), safety_layer)
    is_done = hover_test.tick(snapshot(3.5, ARMED, 0.0), safety_layer)

    assert not still_landing
    assert is_done
    assert safety_layer.requests == [Arm(), TakeOff(TAKE_OFF_HEIGHT), Land()]


def test_it_lands_if_the_take_off_does_not_reach_the_height_in_time(
    caplog: pytest.LogCaptureFixture,
) -> None:
    safety_layer = SafetyLayerStandIn()
    hover_test = HoverTest()
    hover_test.tick(snapshot(0.0, ON_THE_FLOOR), safety_layer)
    hover_test.tick(snapshot(0.25, ARMED), safety_layer)  # take-off starts

    hover_test.tick(snapshot(0.25 + TAKE_OFF_TIME_LIMIT, FLYING, 0.25), safety_layer)
    requests_at_the_limit = list(safety_layer.requests)
    hover_test.tick(snapshot(0.5 + TAKE_OFF_TIME_LIMIT, FLYING, 0.25), safety_layer)

    assert Land() not in requests_at_the_limit
    assert safety_layer.requests[-1] == Land()
    assert "not at 0.50 m after 5 s (at 0.25 m). Landing." in caplog.text


def test_a_refused_request_ends_the_hover_test(caplog: pytest.LogCaptureFixture) -> None:
    safety_layer = SafetyLayerStandIn(refuse_with="the drone is already flying")

    is_done = HoverTest().tick(snapshot(0.0, ON_THE_FLOOR), safety_layer)

    assert is_done
    assert errors_in(caplog) == [
        "Hover test failed: Arm() was refused: the drone is already flying"
    ]


def test_it_makes_each_request_once() -> None:
    safety_layer = SafetyLayerStandIn()
    hover_test = hovering_test(safety_layer)

    for tick_number in range(40):  # 10 s of quarter-second ticks: hover, land, done
        time = 0.75 + tick_number * 0.25
        status, height = (FLYING, 0.5) if time < 3.0 else (ARMED, 0.0)
        hover_test.tick(snapshot(time, status, height), safety_layer)

    assert safety_layer.requests == [Arm(), TakeOff(TAKE_OFF_HEIGHT), Land()]


@pytest.mark.parametrize("hover_duration", [-1.0, math.nan, math.inf])
def test_a_hover_duration_that_is_negative_or_endless_is_a_bug(hover_duration: float) -> None:
    with pytest.raises(ValueError, match="Hover duration"):
        HoverTest(hover_duration)
