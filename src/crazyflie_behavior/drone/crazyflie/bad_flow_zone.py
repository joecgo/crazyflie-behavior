"""Crossing the bad-flow zone level (ADR-0048, ADR-0056, ADR-0077): its numbers and the flow check.

This module doesn't import cflib, so it's type-checked strictly and unit-tested without a drone.
"""

from crazyflie_behavior.drone.crazyflie.touchdown import MAX_READING_AGE
from crazyflie_behavior.drone.interface import FLOW_VELOCITY_UNCERTAINTY
from crazyflie_behavior.snapshot import Snapshot

INITIAL_CLIMB_SPEED = 0.4
"""Meters per second: up in the level initial climb (ADR-0070, ADR-0077)."""

# PLACEHOLDERS, to verify in flight (ADR-0048, ADR-0077).
FINAL_DESCENT_SPEED = 0.3
"""Meters per second: down in the level final descent (ADR-0072)."""
FINAL_DESCENT_HEIGHT = 0.15
"""Meters, by the down range: the initial climb ends here and the final descent starts here. Take-off
targets must be above it."""
INITIAL_CLIMB_TIME_LIMIT = 1.5
"""Seconds from the take-off to the end of the initial climb, or the drone lands."""


def has_fresh_flow(snapshot: Snapshot, now: float) -> bool:
    """A fresh velocity uncertainty from 0 to under FLOW_VELOCITY_UNCERTAINTY (ADR-0060, ADR-0077).

    Missing, stale, negative or not finite is no flow.
    """
    uncertainty = snapshot.velocity_uncertainty
    # False for NaN and for either infinity, so only a finite value can pass.
    return (
        uncertainty is not None
        and uncertainty.age(now) <= MAX_READING_AGE
        and 0.0 <= uncertainty.value < FLOW_VELOCITY_UNCERTAINTY
    )
