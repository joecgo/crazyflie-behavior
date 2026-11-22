import pytest

from crazyflie_behavior.drone.crazyflie.touchdown import (
    FINAL_DESCENT_MARGIN,
    HEIGHT_IF_UNKNOWN,
    RECENT_WINDOW,
    SLOW_DESCENT_SPEED,
    TOUCHDOWN_HOLD,
    TouchdownDetector,
    final_descent_deadline,
    fresh_down_distance,
)
from crazyflie_behavior.drone.interface import STALE_AFTER, TOUCHDOWN_DOWN_RANGE
from crazyflie_behavior.geometry import Vector3
from crazyflie_behavior.snapshot import RangeReading, RangeReadings, Snapshot, Stamped

NOW = 100.0
FRESH = NOW - 0.05
STALE = NOW - STALE_AFTER - 0.01


def snapshot_with(
    down: RangeReading | None = None,
    down_arrived: float = FRESH,
    height: float | None = None,
    height_arrived: float = FRESH,
) -> Snapshot:
    return Snapshot(
        time=NOW,
        dt=0.05,
        position_estimate=(None if height is None else Stamped(Vector3(0.0, 0.0, height), height_arrived, None)),
        velocity_estimate=None,
        velocity_uncertainty=None,
        range_readings=RangeReadings(
            front=None,
            back=None,
            left=None,
            right=None,
            up=None,
            down=None if down is None else Stamped(down, down_arrived, None),
        ),
        battery_voltage=None,
        previous_battery_voltage=None,
        drone_status=None,
        is_in_initial_climb=False,
        may_be_flying=False,
    )


def low_reading_at(time: float) -> Snapshot:
    return snapshot_with(down=RangeReading.at_distance(0.02), down_arrived=time)


def down_reading_at(distance: float, time: float) -> Snapshot:
    return snapshot_with(down=RangeReading.at_distance(distance), down_arrived=time)


def test_a_fresh_distance_is_read() -> None:
    reading = fresh_down_distance(snapshot_with(down=RangeReading.at_distance(0.6)), NOW)

    assert reading is not None
    assert reading.value == 0.6


def test_a_distance_at_its_age_limit_is_still_fresh() -> None:
    # Touchdown's age limit is STALE_AFTER, like every other reading's (ADR-0081).
    snapshot = snapshot_with(down=RangeReading.at_distance(0.6), down_arrived=NOW - STALE_AFTER)

    assert fresh_down_distance(snapshot, NOW) is not None


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


# The limit tests below are timed from 0.0, so each subtraction comes out exact.


def test_touchdown_is_confirmed_at_exactly_the_hold() -> None:
    detector = TouchdownDetector()
    detector.observe(low_reading_at(0.0), 0.0)

    detector.observe(low_reading_at(TOUCHDOWN_HOLD), TOUCHDOWN_HOLD)

    assert detector.touchdown_confirmed(TOUCHDOWN_HOLD)


def test_touchdown_is_not_confirmed_just_before_the_hold() -> None:
    detector = TouchdownDetector()
    detector.observe(low_reading_at(0.0), 0.0)
    just_before = TOUCHDOWN_HOLD - 0.01

    detector.observe(low_reading_at(just_before), just_before)

    assert not detector.touchdown_confirmed(just_before)


def test_a_down_range_of_exactly_the_touchdown_down_range_is_low() -> None:
    detector = TouchdownDetector()
    detector.observe(down_reading_at(TOUCHDOWN_DOWN_RANGE, 0.0), 0.0)

    detector.observe(down_reading_at(TOUCHDOWN_DOWN_RANGE, TOUCHDOWN_HOLD), TOUCHDOWN_HOLD)

    assert detector.touchdown_confirmed(TOUCHDOWN_HOLD)


def test_a_down_range_1_mm_over_the_touchdown_down_range_is_high() -> None:
    detector = TouchdownDetector()
    detector.observe(down_reading_at(TOUCHDOWN_DOWN_RANGE + 0.001, 0.0), 0.0)

    detector.observe(down_reading_at(TOUCHDOWN_DOWN_RANGE + 0.001, TOUCHDOWN_HOLD), TOUCHDOWN_HOLD)

    assert not detector.touchdown_confirmed(TOUCHDOWN_HOLD)


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
        detector.observe(snapshot_with(down=RangeReading.invalid(), height=0.0, height_arrived=time), time)

    assert not detector.touchdown_confirmed(NOW + 1.0)


def test_the_highest_recent_distance_ignores_short_outliers() -> None:
    detector = TouchdownDetector()
    for time, distance in [(NOW, 0.9), (NOW + 0.05, 0.1), (NOW + 0.1, 0.85)]:
        detector.observe(snapshot_with(down=RangeReading.at_distance(distance), down_arrived=time), time)

    assert detector.highest_recent_distance() == 0.9


def test_old_readings_leave_the_recent_window() -> None:
    detector = TouchdownDetector()
    detector.observe(snapshot_with(down=RangeReading.at_distance(0.9), down_arrived=NOW), NOW)
    later = NOW + RECENT_WINDOW + 0.1

    detector.observe(snapshot_with(down=RangeReading.at_distance(0.3), down_arrived=later), later)

    assert detector.highest_recent_distance() == 0.3


def test_a_reading_exactly_the_recent_window_old_is_kept() -> None:
    detector = TouchdownDetector()
    detector.observe(down_reading_at(0.9, 0.0), 0.0)

    detector.observe(down_reading_at(0.3, RECENT_WINDOW), RECENT_WINDOW)

    assert detector.highest_recent_distance() == 0.9


def test_a_reading_just_older_than_the_recent_window_is_dropped() -> None:
    detector = TouchdownDetector()
    detector.observe(down_reading_at(0.9, 0.0), 0.0)
    just_after = RECENT_WINDOW + 0.01

    detector.observe(down_reading_at(0.3, just_after), just_after)

    assert detector.highest_recent_distance() == 0.3


def test_no_readings_means_no_recent_distance() -> None:
    assert TouchdownDetector().highest_recent_distance() is None


def test_the_final_descent_deadline_comes_from_the_recent_distance_at_the_descent_speed() -> None:
    expected = NOW + 0.6 / 0.25 + FINAL_DESCENT_MARGIN

    assert final_descent_deadline(NOW, 0.6, speed=0.25) == pytest.approx(expected)


def test_without_a_recent_distance_the_deadline_assumes_the_highest_height() -> None:
    expected = NOW + HEIGHT_IF_UNKNOWN / SLOW_DESCENT_SPEED + FINAL_DESCENT_MARGIN

    assert final_descent_deadline(NOW, None, SLOW_DESCENT_SPEED) == pytest.approx(expected)
