import math

import pytest

from crazyflie_behavior.drone.crazyflie.conversions import (
    drone_time_from_timestamp,
    move_duration,
    range_reading_from_mm,
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
    assert drone_time_from_timestamp(1500) == 1.5


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
