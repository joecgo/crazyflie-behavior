"""The bad-flow zone's settle check and final descent height (ADR-0048, ADR-0056)."""

import pytest

from crazyflie_behavior.drone.crazyflie.bad_flow_zone import (
    MAX_FINAL_DESCENT_HEIGHT,
    MIN_FINAL_DESCENT_HEIGHT,
    SETTLE_CAP_HEIGHT,
    SETTLE_HOLD,
    SETTLE_MARGIN,
    SETTLE_MIN_DOWN_RANGE,
    SETTLE_SPEED,
    SettleDetector,
    final_descent_height,
)
from crazyflie_behavior.geometry import Vector3
from crazyflie_behavior.snapshot import RangeReading, RangeReadings, Snapshot, Stamped

TICK = 0.05
SLOW = SETTLE_SPEED / 2
FAST = SETTLE_SPEED * 2
HOLD_TICKS = round(SETTLE_HOLD / TICK)
"""Ticks from the reading that starts the hold to the one that completes it."""


def snapshot_at(
    time: float,
    down: float | None,
    speed: float | None = SLOW,
    *,
    velocity_arrived: float | None = None,
) -> Snapshot:
    """A snapshot at `time`: a down range of `down` meters and a horizontal speed estimate, both fresh.

    None leaves a value missing. `velocity_arrived`: when the velocity estimate arrived; None means at `time`.
    """
    arrived = time if velocity_arrived is None else velocity_arrived
    return Snapshot(
        time=time,
        dt=TICK,
        position_estimate=None,
        velocity_estimate=None if speed is None else Stamped(Vector3(0.6 * speed, 0.8 * speed, 0.2), arrived, None),
        range_readings=RangeReadings(
            front=None,
            back=None,
            left=None,
            right=None,
            up=None,
            down=None if down is None else Stamped(RangeReading.at_distance(down), time, None),
        ),
        battery_voltage=None,
        drone_status=None,
    )


def observe_ticks(detector: SettleDetector, start: float, down: float, ticks: int, speed: float = SLOW) -> float:
    """Observe `ticks` snapshots, one per tick from `start`, all at `down`. Returns the last one's time."""
    time = start
    for tick in range(ticks):
        time = start + tick * TICK
        detector.observe(snapshot_at(time, down, speed), time)
    return time


# --- The final descent height ---------------------------------------------------------


def test_the_final_descent_height_is_the_settle_height_plus_the_margin() -> None:
    assert final_descent_height(0.2) == pytest.approx(0.2 + SETTLE_MARGIN)


def test_the_final_descent_height_is_never_below_the_minimum() -> None:
    assert final_descent_height(0.05) == MIN_FINAL_DESCENT_HEIGHT


def test_the_final_descent_height_is_never_above_the_cap() -> None:
    assert final_descent_height(0.4) == MAX_FINAL_DESCENT_HEIGHT


def test_without_a_settle_height_the_final_descent_height_is_the_cap() -> None:
    assert final_descent_height(None) == MAX_FINAL_DESCENT_HEIGHT


# --- The settle check -----------------------------------------------------------------


def test_a_slow_speed_held_long_enough_gives_the_down_range_where_the_hold_started() -> None:
    detector = SettleDetector()
    detector.observe(snapshot_at(0.0, 0.12), 0.0)

    for tick in range(1, HOLD_TICKS + 1):
        detector.observe(snapshot_at(tick * TICK, 0.12 + 0.01 * tick), tick * TICK)

    assert detector.settle_height == pytest.approx(0.12)


def test_a_hold_shorter_than_the_settle_hold_gives_no_settle_height() -> None:
    detector = SettleDetector()

    observe_ticks(detector, 0.0, 0.15, HOLD_TICKS)  # one tick short

    assert detector.settle_height is None


def test_a_fast_reading_restarts_the_hold() -> None:
    detector = SettleDetector()
    observe_ticks(detector, 0.0, 0.15, HOLD_TICKS)
    detector.observe(snapshot_at(HOLD_TICKS * TICK, 0.16, FAST), HOLD_TICKS * TICK)

    observe_ticks(detector, (HOLD_TICKS + 1) * TICK, 0.17, HOLD_TICKS)

    assert detector.settle_height is None


@pytest.mark.parametrize(
    ("down", "speed"),
    [(None, SLOW), (0.15, None)],
    ids=["no down range", "no speed estimate"],
)
def test_a_missing_reading_restarts_the_hold(down: float | None, speed: float | None) -> None:
    detector = SettleDetector()
    observe_ticks(detector, 0.0, 0.15, HOLD_TICKS)
    detector.observe(snapshot_at(HOLD_TICKS * TICK, down, speed), HOLD_TICKS * TICK)

    observe_ticks(detector, (HOLD_TICKS + 1) * TICK, 0.17, HOLD_TICKS)

    assert detector.settle_height is None


def test_the_hold_never_starts_at_or_below_the_floor_guard() -> None:
    # Sitting still before lift-off, the speed estimate is low too (ADR-0056).
    detector = SettleDetector()

    observe_ticks(detector, 0.0, SETTLE_MIN_DOWN_RANGE, 3 * HOLD_TICKS)

    assert detector.settle_height is None


def test_the_hold_is_timed_by_the_speed_estimates_arrival_not_by_the_clock() -> None:
    # The same reading in every snapshot: no new evidence that the speed stays low.
    detector = SettleDetector()

    for tick in range(3 * HOLD_TICKS):
        detector.observe(snapshot_at(tick * TICK, 0.15, velocity_arrived=0.0), tick * TICK)

    assert detector.settle_height is None


def test_a_stale_speed_estimate_restarts_the_hold() -> None:
    detector = SettleDetector()
    observe_ticks(detector, 0.0, 0.15, HOLD_TICKS)
    detector.observe(snapshot_at(10.0, 0.16, velocity_arrived=(HOLD_TICKS - 1) * TICK), 10.0)

    observe_ticks(detector, 10.0 + TICK, 0.17, HOLD_TICKS)

    assert detector.settle_height is None


def test_a_speed_unsettled_above_the_cap_height_trips_the_cap() -> None:
    detector = SettleDetector()

    observe_ticks(detector, 0.0, SETTLE_CAP_HEIGHT + 0.01, 1, speed=FAST)

    assert detector.is_cap_tripped
    assert detector.settle_height is None


def test_the_cap_does_not_trip_at_the_cap_height() -> None:
    detector = SettleDetector()

    observe_ticks(detector, 0.0, SETTLE_CAP_HEIGHT, 1, speed=FAST)

    assert not detector.is_cap_tripped


def test_a_hold_started_at_or_below_the_cap_height_may_settle_above_it() -> None:
    detector = SettleDetector()
    detector.observe(snapshot_at(0.0, SETTLE_CAP_HEIGHT), 0.0)

    for tick in range(1, HOLD_TICKS + 1):
        detector.observe(snapshot_at(tick * TICK, SETTLE_CAP_HEIGHT + 0.01 * tick), tick * TICK)

    assert not detector.is_cap_tripped
    assert detector.settle_height == pytest.approx(SETTLE_CAP_HEIGHT)


def test_a_hold_started_above_the_cap_height_trips_the_cap() -> None:
    detector = SettleDetector()

    observe_ticks(detector, 0.0, SETTLE_CAP_HEIGHT + 0.01, 1, speed=SLOW)

    assert detector.is_cap_tripped


def test_once_decided_the_settle_height_stays() -> None:
    detector = SettleDetector()
    observe_ticks(detector, 0.0, 0.15, HOLD_TICKS + 1)

    observe_ticks(detector, 1.0, 0.4, 5, speed=FAST)

    assert detector.settle_height == pytest.approx(0.15)
    assert not detector.is_cap_tripped
