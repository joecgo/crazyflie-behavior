"""Crossing the bad-flow zone level (ADR-0048, ADR-0056): its numbers and the settle check.

This module doesn't import cflib, so it's type-checked strictly and unit-tested without a drone.
"""

import math

from crazyflie_behavior.drone.crazyflie.touchdown import MAX_READING_AGE, fresh_down_distance
from crazyflie_behavior.drone.interface import FLOW_VELOCITY_UNCERTAINTY
from crazyflie_behavior.snapshot import Snapshot

# PLACEHOLDERS, to verify in flight (ADR-0048, ADR-0056).
LEVEL_VERTICAL_SPEED = 0.2
"""Meters per second: up in the initial climb, down in the level final descent."""
SETTLE_SPEED = 0.15
"""Meters per second. A horizontal speed estimate under this counts as settled, with the velocity
uncertainty under FLOW_VELOCITY_UNCERTAINTY (ADR-0054)."""
SETTLE_HOLD = 0.2
"""Seconds the horizontal speed estimate must stay under SETTLE_SPEED."""
SETTLE_MIN_DOWN_RANGE = 0.10
"""Meters. The settle hold starts only above this down range: below it the firmware's flow model is
wrong in any light."""
SETTLE_MARGIN = 0.05
"""Meters from the settle height up to the final descent height."""
MIN_FINAL_DESCENT_HEIGHT = 0.15
"""Meters."""
MAX_FINAL_DESCENT_HEIGHT = 0.30
"""Meters: the cap. A take-off target at or below it is refused."""

SETTLE_CAP_HEIGHT = MAX_FINAL_DESCENT_HEIGHT - SETTLE_MARGIN
"""Meters. If the speed hasn't settled by this down range, the drone lands at once."""
INITIAL_CLIMB_TIME_LIMIT = MAX_FINAL_DESCENT_HEIGHT / LEVEL_VERTICAL_SPEED + 1.0
"""Seconds from the take-off to the end of the initial climb, or the drone lands."""


def final_descent_height(settle_height: float | None) -> float:
    """Meters, by the down range. Without a settle height (a taken-over flight), the cap."""
    if settle_height is None:
        return MAX_FINAL_DESCENT_HEIGHT
    return min(max(MIN_FINAL_DESCENT_HEIGHT, settle_height + SETTLE_MARGIN), MAX_FINAL_DESCENT_HEIGHT)


class SettleDetector:
    """Watches one initial climb for the settle height. Give it every snapshot from the take-off.

    The hold is timed by the velocity estimate's arrival times, so a reading
    repeated in two snapshots doesn't stretch it.
    """

    def __init__(self) -> None:
        self._hold_started_at: float | None = None
        """The arrival time of the velocity estimate that started the hold."""
        self._hold_start_height = 0.0
        """Meters: the down range when the hold started. Meaningful while it holds."""
        self._settle_height: float | None = None
        self._is_cap_tripped = False

    @property
    def settle_height(self) -> float | None:
        """Meters: the down range where the hold started, once it has held for SETTLE_HOLD."""
        return self._settle_height

    @property
    def is_cap_tripped(self) -> bool:
        """True once the down range is above SETTLE_CAP_HEIGHT with no hold started at or below it."""
        return self._is_cap_tripped

    def observe(self, snapshot: Snapshot, now: float) -> None:
        if self._settle_height is not None or self._is_cap_tripped:
            return  # decided
        down = fresh_down_distance(snapshot, now)
        velocity = snapshot.velocity_estimate
        uncertainty = snapshot.velocity_uncertainty
        if (
            down is None
            or velocity is None
            or velocity.age(now) > MAX_READING_AGE
            or uncertainty is None
            or uncertainty.age(now) > MAX_READING_AGE
        ):
            self._hold_started_at = None  # a missing or stale reading breaks the hold
            return
        horizontal_speed = math.hypot(velocity.value.x, velocity.value.y)
        # Without flow, a runaway speed can pass under SETTLE_SPEED by chance (ADR-0054).
        # The comparison is false for NaN too.
        has_flow = uncertainty.value < FLOW_VELOCITY_UNCERTAINTY
        if horizontal_speed >= SETTLE_SPEED or not has_flow or down.value <= SETTLE_MIN_DOWN_RANGE:
            self._hold_started_at = None
        elif self._hold_started_at is None:
            self._hold_started_at = velocity.arrival_time
            self._hold_start_height = down.value
        elif velocity.arrival_time - self._hold_started_at >= SETTLE_HOLD:
            self._settle_height = self._hold_start_height
            return
        hold_can_settle_in_time = self._hold_started_at is not None and self._hold_start_height <= SETTLE_CAP_HEIGHT
        if down.value > SETTLE_CAP_HEIGHT and not hold_can_settle_in_time:
            self._is_cap_tripped = True
