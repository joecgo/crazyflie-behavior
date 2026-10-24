import pytest

from crazyflie_behavior.drone.crazyflie.touchdown import (
    FINAL_DESCENT_MARGIN,
    FINAL_DESCENT_SPEED,
    HEIGHT_IF_UNKNOWN,
    RECENT_WINDOW,
    TOUCHDOWN_HOLD,
    TouchdownDetector,
    final_descent_deadline,
    fresh_down_distance,
)
from crazyflie_behavior.geometry import Vector3
from crazyflie_behavior.snapshot import RangeReading, RangeReadings, Snapshot, Stamped

NOW = 100.0
FRESH = NOW - 0.05
STALE = NOW - 5.0


def snapshot_with(
    down: RangeReading | None = None,
    down_arrived: float = FRESH,
    height: float | None = None,
    height_arrived: float = FRESH,
) -> Snapshot:
    return Snapshot(
        time=NOW,
        dt=0.05,
        position_estimate=(
            None if height is None else Stamped(Vector3(0.0, 0.0, height), height_arrived, None)
        ),
        velocity_estimate=None,
        range_readings=RangeReadings(
            front=None,
            back=None,
            left=None,
            right=None,
            up=None,
            down=None if down is None else Stamped(down, down_arrived, None),
        ),
        battery_voltage=None,
        drone_status=None,
    )


def low_reading_at(time: float) -> Snapshot:
    return snapshot_with(down=RangeReading.at_distance(0.02), down_arrived=time)


def test_a_fresh_distance_is_read() -> None:
    reading = fresh_down_distance(snapshot_with(down=RangeReading.at_distance(0.6)), NOW)

    assert reading is not None
    assert reading.value == 0.6


@pytest.mark.parametrize(
    "snapshot",
    [
        snapshot_with(),
        snapshot_with(down=RangeReading.invalid()),
        snapshot_with(down=RangeReading.out_of_range()),
        snapshot_with(down=RangeReading.at_distance(0.02), down_arrived=STALE),
    ],
    ids=["missing", "invalid", "out of range", "stale"],
)
def test_anything_but_a_fresh_distance_is_no_reading(snapshot: Snapshot) -> None:
    assert fresh_down_distance(snapshot, NOW) is None


def test_one_low_reading_does_not_confirm_touchdown() -> None:
    detector = TouchdownDetector()

    detector.observe(low_reading_at(FRESH), NOW)

    assert not detector.touchdown_confirmed(NOW)


def test_a_down_range_that_stays_low_confirms_touchdown() -> None:
    detector = TouchdownDetector()
    detector.observe(low_reading_at(NOW), NOW)
    later = NOW + TOUCHDOWN_HOLD + 0.01

    detector.observe(low_reading_at(later), later)

    assert detector.touchdown_confirmed(later)


@pytest.mark.parametrize(
    "interruption",
    [RangeReading.at_distance(0.6), RangeReading.invalid(), RangeReading.out_of_range()],
    ids=["high", "invalid", "out of range"],
)
def test_any_other_reading_restarts_the_hold(interruption: RangeReading) -> None:
    detector = TouchdownDetector()
    detector.observe(low_reading_at(NOW), NOW)
    middle = NOW + TOUCHDOWN_HOLD / 2
    detector.observe(snapshot_with(down=interruption, down_arrived=middle), middle)
    later = NOW + TOUCHDOWN_HOLD + 0.01

    detector.observe(low_reading_at(later), later)

    assert not detector.touchdown_confirmed(later)


def test_a_height_estimate_alone_never_confirms() -> None:
    # ADR-0019: the height estimate comes mostly from the down sensor, so it
    # can't stand in when the sensor fails.
    detector = TouchdownDetector()
    for step in range(20):
        time = NOW + step * 0.05
        detector.observe(
            snapshot_with(down=RangeReading.invalid(), height=0.0, height_arrived=time), time
        )

    assert not detector.touchdown_confirmed(NOW + 1.0)


def test_the_highest_recent_distance_ignores_short_outliers() -> None:
    detector = TouchdownDetector()
    for time, distance in [(NOW, 0.9), (NOW + 0.05, 0.1), (NOW + 0.1, 0.85)]:
        detector.observe(
            snapshot_with(down=RangeReading.at_distance(distance), down_arrived=time), time
        )

    assert detector.highest_recent_distance() == 0.9


def test_old_readings_leave_the_recent_window() -> None:
    detector = TouchdownDetector()
    detector.observe(snapshot_with(down=RangeReading.at_distance(0.9), down_arrived=NOW), NOW)
    later = NOW + RECENT_WINDOW + 0.1

    detector.observe(snapshot_with(down=RangeReading.at_distance(0.3), down_arrived=later), later)

    assert detector.highest_recent_distance() == 0.3


def test_no_readings_means_no_recent_distance() -> None:
    assert TouchdownDetector().highest_recent_distance() is None


def test_the_final_descent_deadline_comes_from_the_recent_distance() -> None:
    expected = NOW + 0.6 / FINAL_DESCENT_SPEED + FINAL_DESCENT_MARGIN

    assert final_descent_deadline(NOW, 0.6) == pytest.approx(expected)


def test_without_a_recent_distance_the_deadline_assumes_the_highest_height() -> None:
    expected = NOW + HEIGHT_IF_UNKNOWN / FINAL_DESCENT_SPEED + FINAL_DESCENT_MARGIN

    assert final_descent_deadline(NOW, None) == pytest.approx(expected)
