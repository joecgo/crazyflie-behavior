"""The snapshot: one consistent, read-only picture of the drone's world per tick.

The tick loop copies the telemetry buffer into a snapshot at the start of each
tick; every behavior in that tick reads the same snapshot (ADR-0007). Every
telemetry value is stamped, so its age can always be checked.

The snapshot is a frozen dataclass, so nothing can modify it after it's taken.
That choice is provisional (ADR-0010, backlog: frozen dataclasses).
"""

from dataclasses import dataclass
from enum import Enum

from crazyflie_behavior.geometry import Vector3


@dataclass(frozen=True, slots=True)
class Stamped[T]:
    """A telemetry value with its arrival time and the drone's timestamp.

    Staleness checks use `arrival_time`, which is on the PC's clock. The
    drone's timestamp is kept for latency measurement, recording and replay.
    """

    value: T
    arrival_time: float
    """When the value arrived on the PC, in seconds on the injected clock."""
    drone_time: float | None
    """When the drone measured it, in seconds on the drone's clock. None if the
    source doesn't provide a timestamp."""

    def age(self, now: float) -> float:
        """Seconds since this value arrived on the PC."""
        return now - self.arrival_time


class RangeStatus(Enum):
    """Whether a range reading is a distance, out of range or invalid (glossary: Range status)."""

    DISTANCE = "distance"
    """Something was detected at a known distance."""
    OUT_OF_RANGE = "out_of_range"
    """Nothing within the sensor's range: clear."""
    INVALID = "invalid"
    """No valid reading: unknown. Never treat this as clear."""


@dataclass(frozen=True, slots=True)
class RangeReading:
    """The distance a range sensor measures in one direction."""

    status: RangeStatus
    distance: float | None
    """Meters to the detected surface. Set only when `status` is DISTANCE."""

    def __post_init__(self) -> None:
        has_distance = self.distance is not None
        if (self.status is RangeStatus.DISTANCE) != has_distance:
            raise ValueError(f"A {self.status.value} reading can't have distance={self.distance}")
        if self.distance is not None and self.distance < 0.0:
            raise ValueError(f"Distance can't be negative: {self.distance}")

    @classmethod
    def at_distance(cls, distance: float) -> "RangeReading":
        return cls(RangeStatus.DISTANCE, distance)

    @classmethod
    def out_of_range(cls) -> "RangeReading":
        return cls(RangeStatus.OUT_OF_RANGE, None)

    @classmethod
    def invalid(cls) -> "RangeReading":
        return cls(RangeStatus.INVALID, None)


class RangeDirection(Enum):
    """The six named directions a range reading can point (ADR-0008).

    Directions are relative to the drone. Yaw is held fixed (ADR-0008), so they
    line up with the world frame: FRONT is +x, LEFT is +y, UP is +z.
    """

    FRONT = "front"
    BACK = "back"
    LEFT = "left"
    RIGHT = "right"
    UP = "up"
    DOWN = "down"


@dataclass(frozen=True, slots=True)
class RangeReadings:
    """The six range readings in a snapshot. None means no reading has arrived yet."""

    front: Stamped[RangeReading] | None
    back: Stamped[RangeReading] | None
    left: Stamped[RangeReading] | None
    right: Stamped[RangeReading] | None
    up: Stamped[RangeReading] | None
    down: Stamped[RangeReading] | None
    """Distance to whatever is below. Altitude comes from the position estimate."""


@dataclass(frozen=True, slots=True)
class DroneStatus:
    """The drone's state flags, as the drone reports them."""

    is_armed: bool
    is_flying: bool
    is_crashed: bool
    is_tumbled: bool


@dataclass(frozen=True, slots=True)
class Snapshot:
    """Everything a behavior knows about the drone for one tick.

    Telemetry fields are None until their first value arrives.
    """

    time: float
    """The tick's time in seconds. Behaviors read time here, never from a clock
    (ADR-0009)."""
    dt: float
    """Seconds since the previous tick."""
    position_estimate: Stamped[Vector3] | None
    """The drone's estimated position: world frame, meters. It drifts."""
    velocity_estimate: Stamped[Vector3] | None
    """The drone's estimated velocity: world frame, meters per second."""
    range_readings: RangeReadings
    battery_voltage: Stamped[float] | None
    """Battery voltage in volts."""
    drone_status: Stamped[DroneStatus] | None
