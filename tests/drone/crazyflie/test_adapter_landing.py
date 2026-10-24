"""The Crazyflie adapter's landing (ADR-0012, ADR-0019), against a fake cflib.

The fake records every call the adapter makes, so these tests check what the
adapter would send to a real drone, without one.
"""

# The adapter has no seam for a fake connection, so the tests set its private
# fields directly.
# pyright: reportPrivateUsage=false

from unittest.mock import MagicMock

import pytest

from crazyflie_behavior.drone.crazyflie.adapter import CrazyflieAdapter
from crazyflie_behavior.drone.crazyflie.touchdown import (
    FINAL_DESCENT_MARGIN,
    FINAL_DESCENT_SPEED,
    HEIGHT_IF_UNKNOWN,
    TOUCHDOWN_HOLD,
)
from crazyflie_behavior.snapshot import RangeDirection, RangeReading
from crazyflie_behavior.timing.clock import SimClock

TICK = 0.05
START = 10.0
TIME_LIMIT = 100.0
"""Simulated seconds after which a test fails instead of waiting forever."""


class BoundedSimClock(SimClock):
    """A sim clock that fails the test if a loop keeps waiting past TIME_LIMIT."""

    def sleep_until(self, deadline: float) -> None:
        if deadline > START + TIME_LIMIT:
            raise AssertionError(f"still waiting at t={deadline:.1f} s: the motors never stopped")
        super().sleep_until(deadline)


@pytest.fixture
def clock() -> SimClock:
    return BoundedSimClock(start=START)


@pytest.fixture
def fake_link() -> MagicMock:
    return MagicMock()


@pytest.fixture
def adapter(clock: SimClock, fake_link: MagicMock) -> CrazyflieAdapter:
    adapter = CrazyflieAdapter(clock)
    adapter._sync_crazyflie = fake_link
    adapter.take_off(1.0)
    return adapter


def motors_stopped(fake_link: MagicMock) -> bool:
    return fake_link.cf.high_level_commander.stop.called


def read_down(adapter: CrazyflieAdapter, reading: RangeReading) -> None:
    adapter._telemetry.write_range_readings({RangeDirection.DOWN: reading}, None)


def tick(adapter: CrazyflieAdapter, clock: SimClock, down: RangeReading | None = None) -> None:
    """One tick: optionally a new down reading arrives, then a snapshot is taken."""
    clock.advance(TICK)
    if down is not None:
        read_down(adapter, down)
    adapter.take_snapshot(clock.now(), TICK)


def tick_for(
    adapter: CrazyflieAdapter, clock: SimClock, seconds: float, down: RangeReading
) -> None:
    for _ in range(round(seconds / TICK)):
        tick(adapter, clock, down)


def final_descent_moves(fake_link: MagicMock) -> list[object]:
    return [
        call
        for call in fake_link.cf.high_level_commander.go_to.call_args_list
        if call.kwargs.get("relative")
    ]


def land_and_wait_for_the_planned_landing(adapter: CrazyflieAdapter, clock: SimClock) -> None:
    adapter.land()
    assert adapter._landing_finishes_at is not None
    clock.sleep_until(adapter._landing_finishes_at)


def test_a_down_range_that_stays_low_stops_the_motors(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    land_and_wait_for_the_planned_landing(adapter, clock)

    tick_for(adapter, clock, TOUCHDOWN_HOLD + TICK, RangeReading.at_distance(0.02))

    assert motors_stopped(fake_link)


def test_one_low_reading_does_not_stop_the_motors(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    land_and_wait_for_the_planned_landing(adapter, clock)

    tick(adapter, clock, RangeReading.at_distance(0.02))
    tick_for(adapter, clock, TOUCHDOWN_HOLD, RangeReading.at_distance(0.6))

    assert not motors_stopped(fake_link)


def test_the_motors_keep_running_before_the_planned_landing_is_over(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    adapter.land()

    tick_for(adapter, clock, TOUCHDOWN_HOLD + TICK, RangeReading.at_distance(0.02))

    assert not motors_stopped(fake_link)


def test_an_unconfirmed_touchdown_starts_one_slow_descent_without_streaming(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    land_and_wait_for_the_planned_landing(adapter, clock)

    tick_for(adapter, clock, 1.0, RangeReading.at_distance(0.6))

    assert not motors_stopped(fake_link)
    moves = final_descent_moves(fake_link)
    assert len(moves) == 1
    _, _, z, _, duration = moves[0].args  # type: ignore[attr-defined]
    assert z == pytest.approx(-FINAL_DESCENT_SPEED * duration)
    fake_link.cf.commander.send_velocity_world_setpoint.assert_not_called()


def test_a_failed_down_sensor_still_stops_the_motors_after_the_time_limit(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    land_and_wait_for_the_planned_landing(adapter, clock)
    final_descent_starts = clock.now()
    limit = HEIGHT_IF_UNKNOWN / FINAL_DESCENT_SPEED + FINAL_DESCENT_MARGIN

    while not motors_stopped(fake_link):
        tick(adapter, clock, RangeReading.invalid())

    assert clock.now() >= final_descent_starts + limit


def test_a_short_outlier_does_not_shorten_the_time_limit(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    adapter.land()
    assert adapter._landing_finishes_at is not None
    tick_for(
        adapter,
        clock,
        adapter._landing_finishes_at - clock.now() - TICK,
        RangeReading.at_distance(0.9),
    )
    tick(adapter, clock, RangeReading.at_distance(0.1))  # an outlier, as the final descent starts
    final_descent_starts = clock.now()

    while not motors_stopped(fake_link):
        tick(adapter, clock, RangeReading.invalid())

    assert clock.now() >= final_descent_starts + 0.9 / FINAL_DESCENT_SPEED


def test_the_final_descent_ends_when_the_floor_is_reached(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    land_and_wait_for_the_planned_landing(adapter, clock)
    tick_for(adapter, clock, 1.0, RangeReading.at_distance(0.3))
    assert not motors_stopped(fake_link)

    tick_for(adapter, clock, TOUCHDOWN_HOLD + TICK, RangeReading.at_distance(0.03))

    assert motors_stopped(fake_link)


def test_shutdown_with_a_failed_down_sensor_lands_and_closes_the_link(
    adapter: CrazyflieAdapter, fake_link: MagicMock
) -> None:
    read_down(adapter, RangeReading.invalid())

    adapter.disconnect()

    assert motors_stopped(fake_link)
    fake_link.close_link.assert_called_once()


def test_shutdown_during_a_landing_does_not_restart_it(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    land_and_wait_for_the_planned_landing(adapter, clock)
    tick(adapter, clock, RangeReading.at_distance(0.6))

    adapter.disconnect()

    fake_link.cf.high_level_commander.land.assert_called_once()
    assert len(final_descent_moves(fake_link)) == 1
    assert motors_stopped(fake_link)


def test_a_new_command_cancels_the_landing(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    land_and_wait_for_the_planned_landing(adapter, clock)
    adapter.hover()

    tick_for(adapter, clock, TOUCHDOWN_HOLD + TICK, RangeReading.at_distance(0.02))

    assert not motors_stopped(fake_link)
