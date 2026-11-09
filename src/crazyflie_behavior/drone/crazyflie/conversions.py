"""Conversions between cflib's units and data and this project's (ADR-0004).

The project is SI inside; cflib uses millimeters, millisecond timestamps and
degrees in places. Conversions happen here, in one place, as plain functions
that can be unit-tested without a drone (ADR-0010). This module doesn't import
cflib, so it's type-checked strictly.
"""

import math
import struct

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


def velocity_uncertainty_from_variances(variance_px: float, variance_py: float) -> float:
    """The velocity uncertainty in m/s from `kalman.varPX` and `varPY` in m²/s² (ADR-0054).

    NaN when either variance isn't finite or is negative.
    """
    variances = (variance_px, variance_py)
    if not all(math.isfinite(variance) and variance >= 0.0 for variance in variances):
        return math.nan
    return math.sqrt(max(variances))


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


def battery_voltage_from_mv(voltage_mv: int) -> float:
    """Convert a battery voltage in millivolts into volts."""
    return voltage_mv / 1000.0


SOUND_FREQUENCY_LIMIT = 0xFFFF
"""Hertz: the highest pitch the firmware's tone parameter holds (16 bits)."""


def sound_frequency_from_pitch(pitch: float) -> int:
    """Convert a tone's pitch in hertz into the firmware's whole hertz."""
    if not 1.0 <= pitch <= SOUND_FREQUENCY_LIMIT:  # false for NaN too
        raise ValueError(f"The buzzer can't play a pitch of {pitch} Hz")
    return round(pitch)


def yaw_rate_deg_per_s(yaw_rate_rad_per_s: float) -> float:
    """cflib's velocity setpoints take yaw rate in degrees per second."""
    return math.degrees(yaw_rate_rad_per_s)


ALT_HOLD_SETPOINT_TYPE = 4
"""The firmware's altHold setpoint type (ADR-0056)."""


def alt_hold_packet_data(vertical_speed: float) -> bytes:
    """A level altHold setpoint's packet data: roll and pitch 0, no yaw rate (ADR-0048).

    `vertical_speed` is in meters per second, up. cflib has no method for this setpoint;
    the layout is the firmware's (ADR-0056).
    """
    return struct.pack("<Bffff", ALT_HOLD_SETPOINT_TYPE, 0.0, 0.0, 0.0, vertical_speed)


def move_duration(distance: float, speed: float, minimum: float) -> float:
    """How long a move should take, in seconds.

    cflib's high-level commander takes a duration, not a speed. The minimum
    stops a tiny distance from becoming a near-instant, violent move.
    """
    if speed <= 0.0:
        raise ValueError(f"Speed must be positive: {speed}")
    return max(abs(distance) / speed, minimum)
