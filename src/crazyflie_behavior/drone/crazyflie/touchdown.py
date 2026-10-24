"""Deciding whether a landing has really touched down (ADR-0012, ADR-0019).

The Crazyflie adapter stops the motors only once touchdown is confirmed, so a
landing planned from a stale or drifted height estimate can't cut the motors
in mid-air. If touchdown isn't confirmed when the planned landing is over, the
drone keeps descending slowly (the final descent) until it is, or until a time
limit says it must be on the floor. This module doesn't import cflib, so it's
type-checked strictly and unit-tested without a drone.
"""

from crazyflie_behavior.snapshot import RangeStatus, Snapshot, Stamped

# PLACEHOLDERS, to VERIFY at the bench (ADR-0012, ADR-0019).
TOUCHDOWN_DOWN_RANGE = 0.05
"""Meters. A down range at or below this means the drone is resting on something."""
TOUCHDOWN_HOLD = 0.3
"""Seconds the down range must stay at or below TOUCHDOWN_DOWN_RANGE to confirm
touchdown, so one noisy reading can't."""
MAX_READING_AGE = 0.5
"""Seconds. Older telemetry doesn't count."""
RECENT_WINDOW = 1.0
"""Seconds of down range history used to set the final descent's time limit."""
FINAL_DESCENT_SPEED = 0.1
"""Meters per second, downward, while touchdown isn't confirmed."""
FINAL_DESCENT_MARGIN = 2.0
"""Seconds added to the final descent's time limit."""
HEIGHT_IF_UNKNOWN = 2.0
"""Meters. The most the drone could be above the floor (about the ceiling),
assumed when its height is unknown."""


def fresh_down_distance(snapshot: Snapshot, now: float) -> Stamped[float] | None:
    """The down range's distance, if it's a fresh distance reading."""
    down = snapshot.range_readings.down
    if (
        down is None
        or down.age(now) > MAX_READING_AGE
        or down.value.status is not RangeStatus.DISTANCE
        or down.value.distance is None
    ):
        return None
    return Stamped(down.value.distance, down.arrival_time, down.drone_time)


def final_descent_deadline(start: float, highest_recent_distance: float | None) -> float:
    """When the final descent must be over: by then the drone is on the floor.

    Set once, when the final descent starts, from the highest recent down range
    (so a short outlier can't shorten it), or HEIGHT_IF_UNKNOWN without one.
    """
    height = HEIGHT_IF_UNKNOWN if highest_recent_distance is None else highest_recent_distance
    return start + height / FINAL_DESCENT_SPEED + FINAL_DESCENT_MARGIN


class TouchdownDetector:
    """Watches the down range during one landing.

    It remembers readings across ticks, so it's an ordinary class, not a
    dataclass (ADR-0018). Give it every snapshot from the start of the landing.
    """

    def __init__(self) -> None:
        self._recent_down_readings: list[Stamped[float]] = []
        self._low_since: float | None = None

    def observe(self, snapshot: Snapshot, now: float) -> None:
        reading = fresh_down_distance(snapshot, now)
        if reading is None:
            self._low_since = None  # a missing, stale or invalid reading breaks the hold
        else:
            if (
                not self._recent_down_readings
                or self._recent_down_readings[-1].arrival_time != reading.arrival_time
            ):
                self._recent_down_readings.append(reading)
            if reading.value > TOUCHDOWN_DOWN_RANGE:
                self._low_since = None
            elif self._low_since is None:
                self._low_since = reading.arrival_time
        self._recent_down_readings = [
            r for r in self._recent_down_readings if now - r.arrival_time <= RECENT_WINDOW
        ]

    def touchdown_confirmed(self, now: float) -> bool:
        """True once the down range has stayed low for TOUCHDOWN_HOLD."""
        return self._low_since is not None and now - self._low_since >= TOUCHDOWN_HOLD

    def highest_recent_distance(self) -> float | None:
        """The highest down range in the last RECENT_WINDOW, if any."""
        return max((r.value for r in self._recent_down_readings), default=None)
