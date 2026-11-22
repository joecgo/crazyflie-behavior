"""The flow check at the end of the initial climb (ADR-0077)."""

import math

import pytest

from crazyflie_behavior.drone.crazyflie.bad_flow_zone import has_fresh_flow
from crazyflie_behavior.drone.interface import FLOW_VELOCITY_UNCERTAINTY, STALE_AFTER
from crazyflie_behavior.snapshot import RangeReadings, Snapshot, Stamped

NOW = 10.0
WITH_FLOW = FLOW_VELOCITY_UNCERTAINTY / 3
"""Meters per second: a velocity uncertainty with flow arriving."""


def snapshot_with(velocity_uncertainty: float | None, arrived: float = NOW) -> Snapshot:
    """A snapshot at NOW with only a velocity uncertainty, which arrived at `arrived`. None leaves it missing."""
    return Snapshot(
        time=NOW,
        dt=0.05,
        position_estimate=None,
        velocity_estimate=None,
        velocity_uncertainty=None if velocity_uncertainty is None else Stamped(velocity_uncertainty, arrived, None),
        range_readings=RangeReadings(front=None, back=None, left=None, right=None, up=None, down=None),
        battery_voltage=None,
        previous_battery_voltage=None,
        drone_status=None,
        is_in_initial_climb=True,
        may_be_flying=True,
    )


def test_a_fresh_low_velocity_uncertainty_is_flow() -> None:
    assert has_fresh_flow(snapshot_with(WITH_FLOW), NOW)


def test_a_velocity_uncertainty_of_zero_is_flow() -> None:
    assert has_fresh_flow(snapshot_with(0.0), NOW)


def test_a_velocity_uncertainty_just_under_the_threshold_is_flow() -> None:
    # The largest float below the threshold, so any lower threshold fails this.
    assert has_fresh_flow(snapshot_with(math.nextafter(FLOW_VELOCITY_UNCERTAINTY, 0.0)), NOW)


def test_a_velocity_uncertainty_at_its_age_limit_is_still_fresh() -> None:
    assert has_fresh_flow(snapshot_with(WITH_FLOW, arrived=NOW - STALE_AFTER), NOW)


@pytest.mark.parametrize(
    ("velocity_uncertainty", "arrived"),
    [
        (None, NOW),
        (WITH_FLOW, NOW - STALE_AFTER - 0.01),
        (math.nan, NOW),
        (math.inf, NOW),
        (-math.inf, NOW),
        (-WITH_FLOW, NOW),
        (FLOW_VELOCITY_UNCERTAINTY, NOW),
        (0.5, NOW),
    ],
    ids=["missing", "stale", "NaN", "infinite", "minus infinity", "negative", "at the threshold", "high"],
)
def test_a_velocity_uncertainty_that_is_missing_stale_negative_not_finite_or_high_is_no_flow(
    velocity_uncertainty: float | None, arrived: float
) -> None:
    assert not has_fresh_flow(snapshot_with(velocity_uncertainty, arrived), NOW)
