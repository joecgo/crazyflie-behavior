import dataclasses

import pytest

from crazyflie_behavior.snapshot import (
    RangeReading,
    RangeReadingKind,
    RangeReadings,
    Snapshot,
    Stamped,
)


def test_a_stamped_value_knows_its_age() -> None:
    stamped = Stamped(value=1.25, arrival_time=10.0, drone_time=3.0)

    assert stamped.age(now=10.5) == pytest.approx(0.5)


def test_range_readings_come_in_three_kinds() -> None:
    assert RangeReading.at_distance(0.4) == RangeReading(RangeReadingKind.DISTANCE, 0.4)
    assert RangeReading.out_of_range().kind is RangeReadingKind.OUT_OF_RANGE
    assert RangeReading.invalid().kind is RangeReadingKind.INVALID


def test_only_distance_readings_carry_a_distance() -> None:
    with pytest.raises(ValueError, match="can't have distance"):
        RangeReading(RangeReadingKind.DISTANCE, None)
    with pytest.raises(ValueError, match="can't have distance"):
        RangeReading(RangeReadingKind.OUT_OF_RANGE, 2.0)


def test_distances_cannot_be_negative() -> None:
    with pytest.raises(ValueError, match="negative"):
        RangeReading.at_distance(-0.1)


def test_a_snapshot_cannot_be_modified() -> None:
    no_ranges = RangeReadings(None, None, None, None, None, None)
    snapshot = Snapshot(
        time=1.0,
        dt=0.05,
        position_estimate=None,
        velocity_estimate=None,
        range_readings=no_ranges,
        battery_voltage=None,
        drone_status=None,
    )
    field_name = "dt"

    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(snapshot, field_name, 1.0)
