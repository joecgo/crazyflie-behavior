import math

import pytest

from crazyflie_behavior.drone.crazyflie.conversions import (
    LOG_TIMESTAMP_RANGE_MS,
    SOUND_FREQUENCY_LIMIT,
    battery_voltage_from_mv,
    drone_time_from_timestamp,
    move_duration,
    range_reading_from_mm,
    sound_frequency_from_pitch,
    yaw_rate_deg_per_s,
)
from crazyflie_behavior.snapshot import RangeReading


def test_range_millimeters_become_meters() -> None:
    assert range_reading_from_mm(250) == RangeReading.at_distance(0.25)
    assert range_reading_from_mm(7999) == RangeReading.at_distance(7.999)


def test_large_range_values_mean_nothing_in_range() -> None:
    assert range_reading_from_mm(8000) == RangeReading.out_of_range()
    assert range_reading_from_mm(65535) == RangeReading.out_of_range()


def test_log_timestamps_become_seconds() -> None:
    assert drone_time_from_timestamp(1500, previous_drone_time=None) == 1.5
    assert drone_time_from_timestamp(1550, previous_drone_time=1.5) == 1.55


def test_drone_time_keeps_counting_up_across_the_24_bit_wrap() -> None:
    just_before_wrap = (LOG_TIMESTAMP_RANGE_MS - 10) / 1000.0

    drone_time = drone_time_from_timestamp(5, previous_drone_time=just_before_wrap)

    assert drone_time == (LOG_TIMESTAMP_RANGE_MS + 5) / 1000.0


def test_slightly_out_of_order_packets_are_not_mistaken_for_a_wrap() -> None:
    assert drone_time_from_timestamp(9990, previous_drone_time=10.0) == 9.99


def test_a_late_packet_from_before_the_wrap_stays_before_it() -> None:
    just_after_wrap = (LOG_TIMESTAMP_RANGE_MS + 5) / 1000.0

    drone_time = drone_time_from_timestamp(LOG_TIMESTAMP_RANGE_MS - 3, previous_drone_time=just_after_wrap)

    assert drone_time == (LOG_TIMESTAMP_RANGE_MS - 3) / 1000.0


def test_yaw_rate_radians_become_degrees_for_cflib() -> None:
    assert yaw_rate_deg_per_s(math.pi) == pytest.approx(180.0)


def test_move_duration_is_distance_over_speed() -> None:
    assert move_duration(distance=1.0, speed=0.5, minimum=0.5) == 2.0


def test_move_duration_never_goes_below_the_minimum() -> None:
    assert move_duration(distance=0.01, speed=1.0, minimum=0.5) == 0.5


def test_move_duration_uses_distance_either_way() -> None:
    assert move_duration(distance=-1.0, speed=0.5, minimum=0.0) == 2.0


def test_move_duration_rejects_a_non_positive_speed() -> None:
    with pytest.raises(ValueError, match="Speed"):
        move_duration(distance=1.0, speed=0.0, minimum=0.5)


def test_battery_millivolts_become_volts() -> None:
    assert battery_voltage_from_mv(3871) == pytest.approx(3.871)


def test_a_tone_pitch_becomes_whole_hertz_for_the_firmware() -> None:
    assert sound_frequency_from_pitch(391.995) == 392
    assert sound_frequency_from_pitch(523.25) == 523


def test_the_lowest_and_highest_whole_hertz_the_firmware_holds_are_allowed() -> None:
    assert sound_frequency_from_pitch(1.0) == 1
    assert sound_frequency_from_pitch(SOUND_FREQUENCY_LIMIT) == 65535


@pytest.mark.parametrize("pitch", [0.5, SOUND_FREQUENCY_LIMIT + 0.5, math.nan, math.inf])
def test_a_pitch_the_firmware_cant_hold_is_a_bug(pitch: float) -> None:
    with pytest.raises(ValueError, match="The buzzer can't play"):
        sound_frequency_from_pitch(pitch)
