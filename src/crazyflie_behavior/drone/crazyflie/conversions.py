"""Conversions between cflib's units and data and this project's (ADR-0004).

The project is SI inside; cflib uses millimeters, millisecond timestamps and
degrees in places. Conversions happen here, in one place, as plain functions
that can be unit-tested without a drone (ADR-0010). This module doesn't import
cflib, so it's type-checked strictly.
"""

import math

from crazyflie_behavior.snapshot import RangeReading

OUT_OF_RANGE_THRESHOLD_MM = 8000
"""Raw range readings at or above this mean "nothing in range". Matches
cflib.utils.multiranger. VERIFY at the bench: that sensor errors don't also
report as large values, which would turn "unknown" into "clear"."""


def range_reading_from_mm(range_mm: int) -> RangeReading:
    """Convert a raw range sensor value in millimeters into a range reading."""
    if range_mm >= OUT_OF_RANGE_THRESHOLD_MM:
        return RangeReading.out_of_range()
    return RangeReading.at_distance(range_mm / 1000.0)


LOG_TIMESTAMP_RANGE_MS = 1 << 24
"""cflib unpacks log timestamps as 24 bits, so they restart at zero every
16,777,216 ms: about 4.7 hours of drone uptime."""


def drone_time_from_timestamp(timestamp_ms: int, previous_drone_time: float | None) -> float:
    """Convert a log packet timestamp into seconds on the drone's clock.

    Keeps counting up across the 24-bit wrap instead of jumping back to zero,
    using the previous drone time as the reference. A jump of more than half
    the range is a wrap; anything smaller is an ordinary out-of-order packet.
    Milliseconds since boot per the firmware: VERIFY at the bench.
    """
    if previous_drone_time is None:
        return timestamp_ms / 1000.0
    previous_ms = round(previous_drone_time * 1000.0)
    wraps = previous_ms // LOG_TIMESTAMP_RANGE_MS
    drone_time_ms = wraps * LOG_TIMESTAMP_RANGE_MS + timestamp_ms
    half_range_ms = LOG_TIMESTAMP_RANGE_MS // 2
    if drone_time_ms < previous_ms - half_range_ms:
        drone_time_ms += LOG_TIMESTAMP_RANGE_MS  # the counter wrapped
    elif drone_time_ms > previous_ms + half_range_ms:
        drone_time_ms -= LOG_TIMESTAMP_RANGE_MS  # a late packet from before the wrap
    return drone_time_ms / 1000.0


def yaw_rate_deg_per_s(yaw_rate_rad_per_s: float) -> float:
    """cflib's velocity setpoints take yaw rate in degrees per second."""
    return math.degrees(yaw_rate_rad_per_s)


def move_duration(distance: float, speed: float, minimum: float) -> float:
    """How long a move should take, in seconds.

    cflib's high-level commander takes a duration, not a speed. The minimum
    stops a tiny distance from becoming a near-instant, violent move.
    """
    if speed <= 0.0:
        raise ValueError(f"Speed must be positive: {speed}")
    return max(abs(distance) / speed, minimum)
