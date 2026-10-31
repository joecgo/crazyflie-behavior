"""The Crazyflie adapter's landing (ADR-0012, ADR-0019, ADR-0032), against a fake cflib.

The fake records every call the adapter makes, so these tests check what the
adapter would send to a real drone, without one.
"""

# The adapter has no seam for a fake connection, so the tests set its private
# fields directly.
# pyright: reportPrivateUsage=false

from unittest.mock import MagicMock

import pytest

from crazyflie_behavior.drone.crazyflie.adapter import (
    DEFAULT_YAW_RAD,
    TAKE_OFF_STATUS_GRACE,
    VERTICAL_SPEED,
    CrazyflieAdapter,
)
from crazyflie_behavior.drone.crazyflie.touchdown import (
    FINAL_DESCENT_MARGIN,
    FINAL_DESCENT_SPEED,
    HEIGHT_IF_UNKNOWN,
    TOUCHDOWN_HOLD,
)
from crazyflie_behavior.geometry import Vector3
from crazyflie_behavior.snapshot import DroneStatus, RangeDirection, RangeReading
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


FLYING = DroneStatus(is_armed=True, is_flying=True, is_crashed=False, is_tumbled=False)
ON_THE_FLOOR = DroneStatus(is_armed=True, is_flying=False, is_crashed=False, is_tumbled=False)


@pytest.fixture
def adapter(clock: SimClock, fake_link: MagicMock) -> CrazyflieAdapter:
    """A connected adapter whose drone took off and is flying at 1.0 m."""
    adapter = CrazyflieAdapter(clock)
    adapter._sync_crazyflie = fake_link
    adapter.take_off(1.0)
    adapter._telemetry.write_estimates_and_status(
        Vector3(0.5, -0.25, 1.0), Vector3.ZERO, FLYING, None
    )
    return adapter


def report_status(adapter: CrazyflieAdapter, status: DroneStatus) -> None:
    adapter._telemetry.write_drone_status(status, None)


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
    """The final descent: a relative, constant-speed go_to."""
    return [
        call
        for call in fake_link.cf.high_level_commander.go_to.call_args_list
        if call.kwargs.get("relative") and call.kwargs.get("linear")
    ]


def landing_moves(fake_link: MagicMock) -> list[object]:
    """The planned landing: a smooth go_to down (not constant speed)."""
    return [
        call
        for call in fake_link.cf.high_level_commander.go_to.call_args_list
        if not call.kwargs.get("linear")
    ]


def land_and_wait_for_the_planned_landing(adapter: CrazyflieAdapter, clock: SimClock) -> None:
    adapter.land()
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

    assert len(landing_moves(fake_link)) == 1
    assert len(final_descent_moves(fake_link)) == 1
    assert motors_stopped(fake_link)


def test_a_new_command_cancels_the_landing(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    land_and_wait_for_the_planned_landing(adapter, clock)
    adapter.hover()

    tick_for(adapter, clock, TOUCHDOWN_HOLD + TICK, RangeReading.at_distance(0.02))

    assert not motors_stopped(fake_link)


def test_landing_is_a_go_to_down_to_the_floor_not_the_firmware_landing(
    adapter: CrazyflieAdapter, fake_link: MagicMock
) -> None:
    # The firmware's landing switches the motors off when it ends (ADR-0032).
    adapter.land()

    fake_link.cf.high_level_commander.land.assert_not_called()
    fake_link.cf.high_level_commander.go_to.assert_called_once_with(
        0.5, -0.25, 0.0, DEFAULT_YAW_RAD, pytest.approx(1.0 / VERTICAL_SPEED)
    )


def test_without_a_position_estimate_the_landing_goes_straight_down(
    clock: SimClock, fake_link: MagicMock
) -> None:
    adapter = CrazyflieAdapter(clock)
    adapter._sync_crazyflie = fake_link
    adapter.take_off(1.0)

    adapter.land()

    fake_link.cf.high_level_commander.go_to.assert_called_once_with(
        0.0,
        0.0,
        -HEIGHT_IF_UNKNOWN,
        DEFAULT_YAW_RAD,
        pytest.approx(HEIGHT_IF_UNKNOWN / VERTICAL_SPEED),
        relative=True,
    )


def test_land_on_the_floor_just_stops_the_motors(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    # A take-off the drone never acted on: armed, but still on the floor.
    clock.advance(TAKE_OFF_STATUS_GRACE + TICK)
    report_status(adapter, ON_THE_FLOOR)

    adapter.land()

    fake_link.cf.high_level_commander.go_to.assert_not_called()
    assert motors_stopped(fake_link)


def test_land_right_after_a_take_off_lands_before_the_status_shows_flying(
    adapter: CrazyflieAdapter, fake_link: MagicMock
) -> None:
    report_status(adapter, ON_THE_FLOOR)  # the status lags a few ticks behind

    adapter.land()

    assert len(landing_moves(fake_link)) == 1


def test_shutdown_after_a_take_off_that_never_flew_stops_the_motors_without_landing(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    clock.advance(TAKE_OFF_STATUS_GRACE + TICK)
    report_status(adapter, ON_THE_FLOOR)

    adapter.disconnect()

    fake_link.cf.high_level_commander.go_to.assert_not_called()
    assert motors_stopped(fake_link)
    fake_link.close_link.assert_called_once()


def test_shutdown_after_our_own_stop_does_not_land_again(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    land_and_wait_for_the_planned_landing(adapter, clock)
    tick_for(adapter, clock, TOUCHDOWN_HOLD + TICK, RangeReading.at_distance(0.02))
    assert motors_stopped(fake_link)
    # The supervisor keeps saying flying for 2 s after the motors stop.
    report_status(adapter, FLYING)

    adapter.disconnect()

    assert len(landing_moves(fake_link)) == 1  # only the first landing
    fake_link.close_link.assert_called_once()


def test_land_after_our_own_stop_does_not_land_again(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    land_and_wait_for_the_planned_landing(adapter, clock)
    tick_for(adapter, clock, TOUCHDOWN_HOLD + TICK, RangeReading.at_distance(0.02))
    assert motors_stopped(fake_link)
    # The supervisor keeps saying flying for 2 s after the motors stop, but a
    # move down now would spin the motors up on the floor.
    report_status(adapter, FLYING)

    adapter.land()

    assert len(landing_moves(fake_link)) == 1  # only the first landing


def test_an_old_on_the_floor_status_counts_as_unknown_so_it_lands(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    # The status stream stalled before the take-off showed in it. The drone may
    # be flying: landing is safe, stopping the motors could drop it.
    report_status(adapter, ON_THE_FLOOR)
    clock.advance(TAKE_OFF_STATUS_GRACE + TICK)

    adapter.land()

    assert len(landing_moves(fake_link)) == 1
    assert not motors_stopped(fake_link)
