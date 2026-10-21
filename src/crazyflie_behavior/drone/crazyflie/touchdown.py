"""Deciding whether a landing has really touched down (ADR-0012).

The Crazyflie adapter stops the motors only once touchdown is confirmed, so a
landing planned from a stale or drifted height estimate can't cut the motors
in mid-air. This module doesn't import cflib, so it's type-checked strictly and
unit-tested without a drone.
"""

from crazyflie_behavior.snapshot import RangeStatus, Snapshot

# PLACEHOLDERS, to VERIFY at the bench (ADR-0012).
TOUCHDOWN_DOWN_RANGE = 0.05
"""Meters. A down range at or below this means the drone is resting on something."""
TOUCHDOWN_HEIGHT = 0.05
"""Meters. The backup check: a position estimate at or below this height."""
MAX_READING_AGE = 0.5
"""Seconds. Older telemetry doesn't count as confirmation."""


def touchdown_confirmed(snapshot: Snapshot, now: float) -> bool:
    """True if the snapshot shows the drone resting on a surface.

    The down range sensor decides when it has a fresh reading: it measures the
    gap directly and doesn't drift. Only when it has nothing usable (missing,
    stale or invalid) does the position estimate's height stand in.
    """
    down = snapshot.range_readings.down
    if down is not None and down.age(now) <= MAX_READING_AGE:
        if down.value.status is RangeStatus.DISTANCE and down.value.distance is not None:
            return down.value.distance <= TOUCHDOWN_DOWN_RANGE
        if down.value.status is RangeStatus.OUT_OF_RANGE:
            return False  # nothing within range below: clearly still in the air

    position = snapshot.position_estimate
    return (
        position is not None
        and position.age(now) <= MAX_READING_AGE
        and position.value.z <= TOUCHDOWN_HEIGHT
    )
