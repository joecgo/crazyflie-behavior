"""The rescue landing behavior (ADR-0038), with hand-built snapshots and a stand-in for the safety layer."""

import logging
from dataclasses import replace

import pytest

from crazyflie_behavior.behaviors.rescue_landing import LANDING_TIME_LIMIT, RescueLanding
from crazyflie_behavior.geometry import Vector3
from crazyflie_behavior.safety.requests import CommandRequest, Land, Verdict
from crazyflie_behavior.snapshot import DroneStatus, RangeReading, RangeReadings, Snapshot, Stamped

ON_THE_FLOOR = DroneStatus(
    is_armed=True, is_flying=False, is_crashed=False, is_tumbled=False, can_arm=False, is_locked=False
)
FLYING = replace(ON_THE_FLOOR, is_flying=True)


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


def snapshot(time: float, status: DroneStatus) -> Snapshot:
    def fresh[T](value: T) -> Stamped[T]:
        return Stamped(value, arrival_time=time, drone_time=None)

    return Snapshot(
        time=time,
        dt=0.05,
        position_estimate=fresh(Vector3(0.0, 0.0, 0.4)),
        velocity_estimate=fresh(Vector3.ZERO),
        velocity_uncertainty=fresh(0.01),
        range_readings=RangeReadings(None, None, None, None, None, fresh(RangeReading.at_distance(0.4))),
        battery_voltage=fresh(4.0),
        drone_status=fresh(status),
        is_in_initial_climb=False,
    )


def test_it_requests_the_landing_once_then_waits_while_the_drone_reports_flying() -> None:
    safety_layer = SafetyLayerStandIn()
    rescue_landing = RescueLanding()

    assert not rescue_landing.tick(snapshot(0.0, FLYING), safety_layer)
    assert not rescue_landing.tick(snapshot(0.05, FLYING), safety_layer)
    assert not rescue_landing.tick(snapshot(0.10, FLYING), safety_layer)

    assert safety_layer.requests == [Land()]


def test_it_is_done_once_the_drone_no_longer_reports_flying(caplog: pytest.LogCaptureFixture) -> None:
    safety_layer = SafetyLayerStandIn()
    rescue_landing = RescueLanding()
    rescue_landing.tick(snapshot(0.0, FLYING), safety_layer)

    with caplog.at_level(logging.INFO):
        is_done = rescue_landing.tick(snapshot(0.05, ON_THE_FLOOR), safety_layer)

    assert is_done
    assert not rescue_landing.has_failed
    assert "Done." in caplog.text


def test_a_refused_landing_ends_it_with_an_error_naming_the_reason(caplog: pytest.LogCaptureFixture) -> None:
    safety_layer = SafetyLayerStandIn(refuse_with="the flight is over")
    rescue_landing = RescueLanding()

    with caplog.at_level(logging.ERROR):
        is_done = rescue_landing.tick(snapshot(0.0, FLYING), safety_layer)

    assert is_done
    assert rescue_landing.has_failed
    assert "Land() was refused: the flight is over" in caplog.text
    assert safety_layer.requests == [Land()]  # it doesn't ask again


def test_a_drone_that_keeps_reporting_flying_ends_it_after_the_time_limit(caplog: pytest.LogCaptureFixture) -> None:
    safety_layer = SafetyLayerStandIn()
    rescue_landing = RescueLanding()
    rescue_landing.tick(snapshot(0.0, FLYING), safety_layer)

    assert not rescue_landing.tick(snapshot(LANDING_TIME_LIMIT - 0.05, FLYING), safety_layer)
    with caplog.at_level(logging.ERROR):
        is_done = rescue_landing.tick(snapshot(LANDING_TIME_LIMIT + 0.05, FLYING), safety_layer)

    assert is_done
    assert rescue_landing.has_failed
    assert "still reports flying" in caplog.text


def test_a_tick_without_a_drone_status_is_a_bug_the_safety_pre_check_rules_out() -> None:
    no_status = replace(snapshot(0.0, FLYING), drone_status=None)

    with pytest.raises(RuntimeError, match="without a drone status"):
        RescueLanding().tick(no_status, SafetyLayerStandIn())
