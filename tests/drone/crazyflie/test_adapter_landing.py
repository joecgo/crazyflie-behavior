"""The Crazyflie adapter's landing (ADR-0012, ADR-0019, ADR-0032, ADR-0048), against a fake cflib.

The fake records every call the adapter makes, so these tests check what the
adapter would send to a real drone, without one.
"""

# The adapter has no seam for a fake connection, so the tests set its private
# fields directly.
# pyright: reportPrivateUsage=false

import logging
import math
import struct
from collections.abc import Callable
from unittest.mock import MagicMock

import pytest

from crazyflie_behavior.drone.crazyflie import adapter as adapter_module
from crazyflie_behavior.drone.crazyflie.adapter import (
    DEFAULT_YAW_RAD,
    LANDING_APPROACH_AIM_BELOW,
    LANDING_APPROACH_BACKUP,
    LAST_RESORT_LANDING_DURATION,
    MIN_MOVE_DURATION,
    NOT_FLYING_TIME_LIMIT,
    SILENCE_CONFIRMATION_TIME_LIMIT,
    TAKE_OFF_STATUS_GRACE,
    VERTICAL_SPEED,
    CrazyflieAdapter,
)
from crazyflie_behavior.drone.crazyflie.bad_flow_zone import (
    FINAL_DESCENT_HEIGHT,
    FINAL_DESCENT_SPEED,
    INITIAL_CLIMB_SPEED,
)
from crazyflie_behavior.drone.crazyflie.time_limit import WAIT_SLICE
from crazyflie_behavior.drone.crazyflie.touchdown import (
    FINAL_DESCENT_MARGIN,
    HEIGHT_IF_UNKNOWN,
    SLOW_DESCENT_SPEED,
    TOUCHDOWN_HOLD,
)
from crazyflie_behavior.drone.interface import STALE_AFTER
from crazyflie_behavior.geometry import Vector3
from crazyflie_behavior.snapshot import DroneStatus, RangeDirection, RangeReading, Snapshot
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
    fake_link = MagicMock()
    answer_parameter_writes(fake_link)
    return fake_link


def answer_parameter_writes(fake_link: MagicMock) -> None:
    """The fake drone answers each parameter write at once: cflib passes the answer to the update callbacks."""
    callbacks: dict[str, list[Callable[[str, str], None]]] = {}

    def add_update_callback(group: str, name: str, cb: Callable[[str, str], None]) -> None:
        callbacks.setdefault(f"{group}.{name}", []).append(cb)

    def set_value(complete_name: str, value: object) -> None:
        for callback in callbacks.get(complete_name, []):
            callback(complete_name, str(value))

    fake_link.cf.param.add_update_callback.side_effect = add_update_callback
    fake_link.cf.param.set_value.side_effect = set_value


FLYING = DroneStatus(is_armed=True, is_flying=True, is_crashed=False, is_tumbled=False, can_arm=False, is_locked=False)
ON_THE_FLOOR = DroneStatus(
    is_armed=True, is_flying=False, is_crashed=False, is_tumbled=False, can_arm=False, is_locked=False
)


def fly_above_the_bad_flow_zone(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock, *, with_position: bool = True
) -> None:
    """Take off to 1.0 m and tick the initial climb with good flow until it hands over (ADR-0048).

    Then forget the calls it made. `with_position`: whether the position estimate streams too.
    """
    adapter.take_off(1.0)
    height = 0.0
    while adapter._is_in_initial_climb:
        if height > 1.0:
            pytest.fail("the initial climb never handed over")
        clock.advance(TICK)
        height += INITIAL_CLIMB_SPEED * TICK
        telemetry = adapter._telemetry
        if with_position:
            telemetry.write_position_estimate(Vector3(0.5, -0.25, height), None)
        telemetry.write_velocity_estimate(Vector3(0.0, 0.0, INITIAL_CLIMB_SPEED), None)
        telemetry.write_velocity_uncertainty(0.01, None)
        telemetry.write_drone_status(FLYING, None)
        telemetry.write_range_readings({RangeDirection.DOWN: RangeReading.at_distance(height)}, None)
        adapter.update_take_off_and_landing(adapter.take_snapshot(TICK))
    fake_link.reset_mock()


@pytest.fixture
def adapter(clock: SimClock, fake_link: MagicMock) -> CrazyflieAdapter:
    """A connected adapter whose drone took off, crossed the bad-flow zone and is flying at 1.0 m."""
    adapter = CrazyflieAdapter(clock)
    adapter._sync_crazyflie = fake_link
    fly_above_the_bad_flow_zone(adapter, clock, fake_link)
    adapter._telemetry.write_estimates_and_status(Vector3(0.5, -0.25, 1.0), Vector3.ZERO, FLYING, None)
    read_down(adapter, RangeReading.at_distance(1.0))
    return adapter


def report_status(adapter: CrazyflieAdapter, status: DroneStatus) -> None:
    adapter._telemetry.write_drone_status(status, None)


def skip_to_a_whole_second(clock: SimClock) -> None:
    """Move the clock to the next whole second: from there, advancing by STALE_AFTER gives an exact age."""
    clock.sleep_until(math.floor(clock.now()) + 1.0)


def motors_stopped(fake_link: MagicMock) -> bool:
    return fake_link.cf.high_level_commander.stop.called


def read_down(adapter: CrazyflieAdapter, reading: RangeReading) -> None:
    adapter._telemetry.write_range_readings({RangeDirection.DOWN: reading}, None)


def tick(adapter: CrazyflieAdapter, clock: SimClock, down: RangeReading | None = None) -> None:
    """One tick: optionally a new down reading arrives, then a snapshot is taken and the landing updated."""
    clock.advance(TICK)
    if down is not None:
        read_down(adapter, down)
    adapter.update_take_off_and_landing(adapter.take_snapshot(TICK))


def tick_for(adapter: CrazyflieAdapter, clock: SimClock, seconds: float, down: RangeReading) -> None:
    for _ in range(round(seconds / TICK)):
        tick(adapter, clock, down)


def level_setpoints(fake_link: MagicMock) -> list[float]:
    """The vertical speed of each level setpoint sent, in order (meters per second, up)."""
    return [struct.unpack("<Bffff", call.args[0].data)[4] for call in fake_link.cf.send_packet.call_args_list]


def slow_descent_moves(fake_link: MagicMock) -> list[object]:
    """The final descent without a usable down range: a relative, constant-speed go_to."""
    return [
        call
        for call in fake_link.cf.high_level_commander.go_to.call_args_list
        if call.kwargs.get("relative") and call.kwargs.get("linear")
    ]


def landing_approach_moves(fake_link: MagicMock) -> list[object]:
    """The landing approach: a smooth go_to down (not constant speed)."""
    return [call for call in fake_link.cf.high_level_commander.go_to.call_args_list if not call.kwargs.get("linear")]


def land_and_wait_for_the_landing_approach(adapter: CrazyflieAdapter, clock: SimClock) -> None:
    adapter.land()
    clock.sleep_until(adapter._landing_approach_ends_at)


# --- The landing approach -------------------------------------------------------------


def test_the_landing_approach_is_a_go_to_aimed_below_the_final_descent_height_not_the_firmware_landing(
    adapter: CrazyflieAdapter, fake_link: MagicMock
) -> None:
    # The firmware's landing switches the motors off when it ends (ADR-0032).
    height = FINAL_DESCENT_HEIGHT - LANDING_APPROACH_AIM_BELOW

    adapter.land()

    fake_link.cf.high_level_commander.land.assert_not_called()
    fake_link.cf.high_level_commander.go_to.assert_called_once_with(
        0.5, -0.25, height, DEFAULT_YAW_RAD, pytest.approx((1.0 - height) / VERTICAL_SPEED)
    )


def test_after_an_estimate_that_isnt_finite_the_landing_approach_goes_to_the_last_finite_one(
    adapter: CrazyflieAdapter, fake_link: MagicMock
) -> None:
    nan_state = {
        "stateEstimate.x": math.nan,
        "stateEstimate.y": 0.0,
        "stateEstimate.z": 1.0,
        "stateEstimate.vx": 0.0,
        "stateEstimate.vy": 0.0,
        "stateEstimate.vz": 0.0,
        "supervisor.info": float(1 << 4),  # flying
    }
    adapter._on_state(1500, nan_state, MagicMock())
    height = FINAL_DESCENT_HEIGHT - LANDING_APPROACH_AIM_BELOW

    adapter.land()

    fake_link.cf.high_level_commander.go_to.assert_called_once_with(
        0.5, -0.25, height, DEFAULT_YAW_RAD, pytest.approx((1.0 - height) / VERTICAL_SPEED)
    )


def test_without_a_position_estimate_the_landing_approach_goes_straight_down(
    clock: SimClock, fake_link: MagicMock
) -> None:
    adapter = CrazyflieAdapter(clock)
    adapter._sync_crazyflie = fake_link
    fly_above_the_bad_flow_zone(adapter, clock, fake_link, with_position=False)
    read_down(adapter, RangeReading.at_distance(1.0))

    adapter.land()

    fake_link.cf.high_level_commander.go_to.assert_called_once_with(
        0.0,
        0.0,
        -HEIGHT_IF_UNKNOWN,
        DEFAULT_YAW_RAD,
        pytest.approx(HEIGHT_IF_UNKNOWN / VERTICAL_SPEED),
        relative=True,
    )


def test_the_landing_approach_ends_early_when_the_down_range_reaches_the_final_descent_height(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    landing_starts = clock.now()
    adapter.land()
    go_to_duration = fake_link.cf.high_level_commander.go_to.call_args.args[4]

    tick(adapter, clock, RangeReading.at_distance(FINAL_DESCENT_HEIGHT))

    assert clock.now() < landing_starts + go_to_duration
    assert "hasn't reached the final descent height" not in caplog.text
    assert level_setpoints(fake_link) == [pytest.approx(-FINAL_DESCENT_SPEED)]


@pytest.mark.parametrize("with_position", [True, False], ids=["estimate", "no estimate"])
def test_the_landing_approach_waits_a_backup_past_the_end_of_its_go_to_for_the_down_range(
    clock: SimClock, fake_link: MagicMock, with_position: bool, caplog: pytest.LogCaptureFixture
) -> None:
    # The drone trails the `go_to`, so it is still above the final descent height when the `go_to` ends (ADR-0068).
    adapter = CrazyflieAdapter(clock)
    adapter._sync_crazyflie = fake_link
    fly_above_the_bad_flow_zone(adapter, clock, fake_link, with_position=with_position)
    if with_position:
        adapter._telemetry.write_position_estimate(Vector3(0.5, -0.25, 1.0), None)
    read_down(adapter, RangeReading.at_distance(1.0))
    still_above = RangeReading.at_distance(FINAL_DESCENT_HEIGHT + 0.05)
    landing_starts = clock.now()
    adapter.land()
    go_to_duration = fake_link.cf.high_level_commander.go_to.call_args.args[4]
    backup_ends = landing_starts + go_to_duration + LANDING_APPROACH_BACKUP

    clock.sleep_until(backup_ends - 1.5 * TICK)
    tick(adapter, clock, still_above)
    assert level_setpoints(fake_link) == []
    assert "hasn't reached the final descent height" not in caplog.text

    tick(adapter, clock, still_above)
    assert level_setpoints(fake_link) == [pytest.approx(-FINAL_DESCENT_SPEED)]
    assert "hasn't reached the final descent height" in caplog.text


def test_the_down_range_reaching_the_final_descent_height_at_the_backup_time_ends_the_landing_approach_with_no_warning(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    landing_starts = clock.now()
    adapter.land()
    go_to_duration = fake_link.cf.high_level_commander.go_to.call_args.args[4]

    clock.sleep_until(landing_starts + go_to_duration + LANDING_APPROACH_BACKUP)
    tick(adapter, clock, RangeReading.at_distance(FINAL_DESCENT_HEIGHT))

    assert level_setpoints(fake_link) == [pytest.approx(-FINAL_DESCENT_SPEED)]
    assert "hasn't reached the final descent height" not in caplog.text


def test_the_landing_approach_does_not_climb_to_its_aim(adapter: CrazyflieAdapter, fake_link: MagicMock) -> None:
    # The estimate already reads below the aim, but the down range says above the final descent height.
    below_the_aim = FINAL_DESCENT_HEIGHT - LANDING_APPROACH_AIM_BELOW - 0.02
    adapter._telemetry.write_position_estimate(Vector3(0.5, -0.25, below_the_aim), None)

    adapter.land()

    fake_link.cf.high_level_commander.go_to.assert_called_once_with(
        0.5, -0.25, below_the_aim, DEFAULT_YAW_RAD, MIN_MOVE_DURATION
    )


def test_a_landing_already_at_the_final_descent_height_skips_the_landing_approach(
    adapter: CrazyflieAdapter, fake_link: MagicMock
) -> None:
    read_down(adapter, RangeReading.at_distance(FINAL_DESCENT_HEIGHT - 0.02))

    adapter.land()

    fake_link.cf.high_level_commander.go_to.assert_not_called()
    assert level_setpoints(fake_link) == [pytest.approx(-FINAL_DESCENT_SPEED)]


def test_the_motors_keep_running_when_the_landing_approach_ends_without_touchdown(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    land_and_wait_for_the_landing_approach(adapter, clock)

    tick(adapter, clock, RangeReading.at_distance(0.6))  # the height estimate was stale: still well up

    assert not motors_stopped(fake_link)
    assert level_setpoints(fake_link) == [pytest.approx(-FINAL_DESCENT_SPEED)]


def test_a_new_command_cancels_the_landing_approach(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    land_and_wait_for_the_landing_approach(adapter, clock)
    adapter.hover()

    tick_for(adapter, clock, TOUCHDOWN_HOLD + TICK, RangeReading.at_distance(0.02))

    assert not motors_stopped(fake_link)
    assert level_setpoints(fake_link) == []


# --- The final descent ----------------------------------------------------------------


def test_the_final_descent_is_level_one_setpoint_each_tick(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    land_and_wait_for_the_landing_approach(adapter, clock)

    tick_for(adapter, clock, 1.0, RangeReading.at_distance(0.6))

    assert level_setpoints(fake_link) == [pytest.approx(-FINAL_DESCENT_SPEED)] * round(1.0 / TICK)
    assert slow_descent_moves(fake_link) == []
    fake_link.cf.commander.send_notify_setpoint_stop.assert_not_called()


def test_a_down_range_that_stays_low_stops_the_motors(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    land_and_wait_for_the_landing_approach(adapter, clock)

    tick_for(adapter, clock, TOUCHDOWN_HOLD + TICK, RangeReading.at_distance(0.02))

    assert motors_stopped(fake_link)


def test_one_low_reading_does_not_stop_the_motors(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    land_and_wait_for_the_landing_approach(adapter, clock)

    tick(adapter, clock, RangeReading.at_distance(0.02))
    tick_for(adapter, clock, TOUCHDOWN_HOLD, RangeReading.at_distance(0.6))

    assert not motors_stopped(fake_link)


def test_the_final_descent_ends_when_the_floor_is_reached(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    land_and_wait_for_the_landing_approach(adapter, clock)
    tick_for(adapter, clock, 1.0, RangeReading.at_distance(0.3))
    assert not motors_stopped(fake_link)

    tick_for(adapter, clock, TOUCHDOWN_HOLD + TICK, RangeReading.at_distance(0.03))

    assert motors_stopped(fake_link)


def test_a_down_range_lost_mid_descent_keeps_it_level_until_its_time_limit(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    land_and_wait_for_the_landing_approach(adapter, clock)
    tick(adapter, clock, RangeReading.at_distance(0.6))
    final_descent_starts = clock.now()

    while not motors_stopped(fake_link):
        tick(adapter, clock, RangeReading.invalid())

    assert clock.now() == pytest.approx(final_descent_starts + 0.6 / FINAL_DESCENT_SPEED + FINAL_DESCENT_MARGIN)
    assert all(speed == pytest.approx(-FINAL_DESCENT_SPEED) for speed in level_setpoints(fake_link))
    assert slow_descent_moves(fake_link) == []


def test_a_short_outlier_does_not_shorten_the_time_limit(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    adapter.land()
    tick_for(
        adapter,
        clock,
        adapter._landing_approach_ends_at - clock.now() - TICK,
        RangeReading.at_distance(0.9),
    )
    tick(adapter, clock, RangeReading.at_distance(0.1))  # an outlier, as the final descent starts
    final_descent_starts = clock.now()

    while not motors_stopped(fake_link):
        tick(adapter, clock, RangeReading.invalid())

    assert clock.now() >= final_descent_starts + 0.9 / FINAL_DESCENT_SPEED


def test_without_a_usable_down_range_the_final_descent_is_one_slow_high_level_descent(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    land_and_wait_for_the_landing_approach(adapter, clock)

    tick_for(adapter, clock, 1.0, RangeReading.invalid())

    assert not motors_stopped(fake_link)
    moves = slow_descent_moves(fake_link)
    assert len(moves) == 1
    _, _, z, _, duration = moves[0].args  # type: ignore[attr-defined]
    assert z == pytest.approx(-SLOW_DESCENT_SPEED * duration)
    assert level_setpoints(fake_link) == []


def test_a_failed_down_sensor_still_stops_the_motors_after_the_time_limit(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    land_and_wait_for_the_landing_approach(adapter, clock)
    final_descent_starts = clock.now()
    limit = HEIGHT_IF_UNKNOWN / SLOW_DESCENT_SPEED + FINAL_DESCENT_MARGIN

    while not motors_stopped(fake_link):
        tick(adapter, clock, RangeReading.invalid())

    assert clock.now() >= final_descent_starts + limit


def test_a_land_during_the_final_descent_does_not_restart_the_landing(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    land_and_wait_for_the_landing_approach(adapter, clock)
    tick(adapter, clock, RangeReading.at_distance(0.2))

    adapter.land()
    tick(adapter, clock, RangeReading.at_distance(0.19))

    assert len(landing_approach_moves(fake_link)) == 1  # no new approach back up to the final descent height
    assert level_setpoints(fake_link) == [pytest.approx(-FINAL_DESCENT_SPEED)] * 2


def test_commands_during_the_final_descent_are_ignored_and_logged_once(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    land_and_wait_for_the_landing_approach(adapter, clock)
    tick(adapter, clock, RangeReading.at_distance(0.2))
    fake_link.reset_mock()

    with caplog.at_level(logging.INFO, logger=adapter_module.logger.name):
        adapter.hover()
        adapter.move_to(Vector3(1.0, 0.0, 1.0), duration=2.0)
        adapter.set_velocity(Vector3(0.2, 0.0, 0.0))
        adapter.take_off(1.5)

    assert fake_link.mock_calls == []
    ignored = [record for record in caplog.records if "ignored during the final descent" in record.getMessage()]
    assert [record.levelno for record in ignored] == [logging.INFO]
    tick_for(adapter, clock, TOUCHDOWN_HOLD + TICK, RangeReading.at_distance(0.02))
    assert motors_stopped(fake_link)  # the landing carried on


# --- Logging touchdown ----------------------------------------------------------------


def touchdown_logs(caplog: pytest.LogCaptureFixture) -> list[logging.LogRecord]:
    return [record for record in caplog.records if "Touchdown confirmed" in record.getMessage()]


def test_touchdown_confirmed_right_after_the_landing_approach_is_logged(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO, logger=adapter_module.logger.name):
        adapter.land()
        while not motors_stopped(fake_link):
            tick(adapter, clock, RangeReading.at_distance(0.02))

    assert not slow_descent_moves(fake_link)
    assert [record.levelno for record in touchdown_logs(caplog)] == [logging.INFO]


def test_touchdown_confirmed_during_the_final_descent_is_logged(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    land_and_wait_for_the_landing_approach(adapter, clock)
    tick_for(adapter, clock, 1.0, RangeReading.at_distance(0.3))

    with caplog.at_level(logging.INFO, logger=adapter_module.logger.name):
        tick_for(adapter, clock, TOUCHDOWN_HOLD + TICK, RangeReading.at_distance(0.03))

    assert motors_stopped(fake_link)
    assert [record.levelno for record in touchdown_logs(caplog)] == [logging.INFO]


def test_a_time_limit_stop_is_not_logged_as_a_confirmed_touchdown(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    land_and_wait_for_the_landing_approach(adapter, clock)

    with caplog.at_level(logging.INFO, logger=adapter_module.logger.name):
        while not motors_stopped(fake_link):
            tick(adapter, clock, RangeReading.invalid())

    assert not touchdown_logs(caplog)


# --- Shutdown -------------------------------------------------------------------------


def test_shutdown_with_a_failed_down_sensor_lands_and_closes_the_link(
    adapter: CrazyflieAdapter, fake_link: MagicMock
) -> None:
    read_down(adapter, RangeReading.invalid())

    adapter.disconnect()

    assert motors_stopped(fake_link)
    fake_link.close_link.assert_called_once()


def test_a_landing_that_raises_sends_the_firmwares_land_then_the_release_then_closes_only_the_radio_link(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    # The last-resort landing (ADR-0084): the drone may still be flying (ADR-0038).
    radio_link = fake_link.cf.link
    fake_link.cf.high_level_commander.go_to.side_effect = OSError("made-up landing error")
    land_times: list[float] = []
    close_times: list[float] = []

    def record_the_land_time(absolute_height_m: float, duration_s: float) -> None:
        land_times.append(clock.now())

    fake_link.cf.high_level_commander.land.side_effect = record_the_land_time
    radio_link.close.side_effect = lambda: close_times.append(clock.now())

    with pytest.raises(OSError, match="made-up landing error"):  # the first error reaches the program
        adapter.disconnect()

    fake_link.cf.high_level_commander.land.assert_called_once_with(0.0, LAST_RESORT_LANDING_DURATION)
    calls = [name for name, _, _ in fake_link.mock_calls]
    land = calls.index("cf.high_level_commander.land")
    assert land < calls.index("cf.commander.send_notify_setpoint_stop", land) < calls.index("cf.link.close")
    assert close_times == [pytest.approx(land_times[0] + LAST_RESORT_LANDING_DURATION)]  # the link stays open
    radio_link.close.assert_called_once()
    fake_link.close_link.assert_not_called()  # cflib's close sends a zero-thrust setpoint
    fake_link.cf.commander.send_setpoint.assert_not_called()
    fake_link.cf.param.set_value.assert_not_called()  # no silence after a failed landing


def test_an_error_in_the_last_resort_is_logged_not_raised_and_the_radio_link_still_closes(
    adapter: CrazyflieAdapter, fake_link: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    radio_link = fake_link.cf.link
    fake_link.cf.high_level_commander.go_to.side_effect = OSError("made-up landing error")
    fake_link.cf.high_level_commander.land.side_effect = OSError("made-up error in the last resort")

    with pytest.raises(OSError, match="made-up landing error"):
        adapter.disconnect()

    assert "The last-resort landing wasn't sent" in caplog.text
    # Released alone, the idle planner's motors-off setpoint would get through (ADR-0084).
    fake_link.cf.commander.send_notify_setpoint_stop.assert_not_called()
    radio_link.close.assert_called_once()
    fake_link.close_link.assert_not_called()


def test_an_error_while_disconnecting_a_drone_on_the_floor_gets_no_last_resort(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    land_until_the_motors_stop(adapter, clock, fake_link)
    take_off_block = MagicMock()
    take_off_block.stop.side_effect = OSError("made-up error stopping the take-off block")
    adapter._take_off_block = take_off_block
    adapter._is_take_off_block_running = True

    with pytest.raises(OSError, match="made-up error stopping the take-off block"):
        adapter.disconnect()

    fake_link.cf.high_level_commander.land.assert_not_called()


def test_shutdown_during_a_landing_does_not_restart_it_and_keeps_the_level_stream_going(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    land_and_wait_for_the_landing_approach(adapter, clock)
    tick(adapter, clock, RangeReading.at_distance(0.6))

    adapter.disconnect()

    assert len(landing_approach_moves(fake_link)) == 1
    assert len(level_setpoints(fake_link)) > 1
    assert motors_stopped(fake_link)


def test_shutdown_after_our_own_stop_does_not_land_again(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    land_and_wait_for_the_landing_approach(adapter, clock)
    tick_for(adapter, clock, TOUCHDOWN_HOLD + TICK, RangeReading.at_distance(0.02))
    assert motors_stopped(fake_link)
    # The supervisor keeps saying flying for 2 s after the motors stop.
    report_status(adapter, FLYING)

    adapter.disconnect()

    assert len(landing_approach_moves(fake_link)) == 1  # only the first landing
    fake_link.close_link.assert_called_once()


# --- Closing the link after a motor stop (ADR-0058) -------------------------------------

LOCKED = DroneStatus(is_armed=False, is_flying=False, is_crashed=False, is_tumbled=False, can_arm=False, is_locked=True)


def land_until_the_motors_stop(adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock) -> float:
    """Land and tick until touchdown stops the motors. Returns when they stopped."""
    land_and_wait_for_the_landing_approach(adapter, clock)
    tick_for(adapter, clock, TOUCHDOWN_HOLD + TICK, RangeReading.at_distance(0.02))
    assert motors_stopped(fake_link)
    return clock.now()


def stream_status_while_waiting(
    adapter: CrazyflieAdapter, clock: SimClock, monkeypatch: pytest.MonkeyPatch, *, after: float, status: DroneStatus
) -> None:
    """From now on, every wait ends with a fresh status: flying, then `status` from `after` seconds on."""
    changes_at = clock.now() + after
    sleep_until = clock.sleep_until

    def sleep_and_report(deadline: float) -> None:
        sleep_until(deadline)
        report_status(adapter, FLYING if clock.now() < changes_at else status)

    monkeypatch.setattr(clock, "sleep_until", sleep_and_report)


def record_link_close_time(clock: SimClock, fake_link: MagicMock) -> list[float]:
    closed_at: list[float] = []
    fake_link.close_link.side_effect = lambda: closed_at.append(clock.now())
    return closed_at


def test_the_motor_stop_at_touchdown_releases_the_setpoint_priority_last(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    # First flight 2's lock: the level final descent's stop setpoint, never released.
    land_until_the_motors_stop(adapter, clock, fake_link)

    calls = [name for name, _, _ in fake_link.mock_calls]
    release = calls.index("cf.commander.send_notify_setpoint_stop")
    assert calls.index("cf.commander.send_stop_setpoint") < release
    assert calls.index("cf.high_level_commander.stop") < release


def test_shutdown_after_a_motor_stop_waits_until_the_drone_reports_not_flying(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    # cflib's close sends a zero-thrust setpoint, which locks a drone that still counts as flying.
    stopped_at = land_until_the_motors_stop(adapter, clock, fake_link)
    stream_status_while_waiting(adapter, clock, monkeypatch, after=2.0, status=ON_THE_FLOOR)
    closed_at = record_link_close_time(clock, fake_link)

    adapter.disconnect()

    assert closed_at == [pytest.approx(stopped_at + 2.0, abs=WAIT_SLICE)]


def test_shutdown_waits_no_longer_than_its_time_limit_and_warns(
    adapter: CrazyflieAdapter,
    clock: SimClock,
    fake_link: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    stopped_at = land_until_the_motors_stop(adapter, clock, fake_link)
    stream_status_while_waiting(adapter, clock, monkeypatch, after=math.inf, status=ON_THE_FLOOR)
    closed_at = record_link_close_time(clock, fake_link)

    with caplog.at_level(logging.WARNING, logger=adapter_module.__name__):
        adapter.disconnect()

    assert closed_at == [pytest.approx(stopped_at + NOT_FLYING_TIME_LIMIT)]
    assert "didn't report not flying" in caplog.text


def test_an_old_not_flying_status_does_not_end_the_wait(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    # Sent once, never refreshed: the link may have gone quiet. One tick past its age limit (ADR-0081).
    land_until_the_motors_stop(adapter, clock, fake_link)
    report_status(adapter, ON_THE_FLOOR)
    clock.advance(STALE_AFTER + TICK)
    closed_at = record_link_close_time(clock, fake_link)
    started_at = clock.now()

    adapter.disconnect()

    assert closed_at == [pytest.approx(started_at + NOT_FLYING_TIME_LIMIT)]


def test_a_not_flying_status_at_its_age_limit_ends_the_wait(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    # Still fresh at exactly its age limit (ADR-0081).
    land_until_the_motors_stop(adapter, clock, fake_link)
    skip_to_a_whole_second(clock)
    report_status(adapter, ON_THE_FLOOR)
    clock.advance(STALE_AFTER)
    closed_at = record_link_close_time(clock, fake_link)
    started_at = clock.now()

    adapter.disconnect()

    assert closed_at == [started_at]


def test_shutdown_reports_a_locked_drone(
    adapter: CrazyflieAdapter,
    clock: SimClock,
    fake_link: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    land_until_the_motors_stop(adapter, clock, fake_link)
    stream_status_while_waiting(adapter, clock, monkeypatch, after=2.0, status=LOCKED)

    with caplog.at_level(logging.WARNING, logger=adapter_module.__name__):
        adapter.disconnect()

    assert "locked" in caplog.text
    fake_link.close_link.assert_called_once()


def test_shutdown_without_a_motor_stop_does_not_wait(clock: SimClock, fake_link: MagicMock) -> None:
    # Never flown, and no status at all: a wait would run out its whole time limit.
    adapter = CrazyflieAdapter(clock)
    adapter._sync_crazyflie = fake_link
    closed_at = record_link_close_time(clock, fake_link)
    started_at = clock.now()

    adapter.disconnect()

    assert closed_at == [started_at]


# --- Whether the drone may be flying (ADR-0039) ---------------------------------------


def test_land_on_the_floor_just_stops_the_motors(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    # Armed, but the status says on the floor, and the take-off grace is long over.
    clock.advance(TAKE_OFF_STATUS_GRACE + TICK)
    report_status(adapter, ON_THE_FLOOR)

    adapter.land()

    fake_link.cf.high_level_commander.go_to.assert_not_called()
    assert motors_stopped(fake_link)


def test_land_after_our_own_stop_does_not_land_again(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    land_and_wait_for_the_landing_approach(adapter, clock)
    tick_for(adapter, clock, TOUCHDOWN_HOLD + TICK, RangeReading.at_distance(0.02))
    assert motors_stopped(fake_link)
    # The supervisor keeps saying flying for 2 s after the motors stop, but a
    # move down now would spin the motors up on the floor.
    report_status(adapter, FLYING)

    adapter.land()

    assert len(landing_approach_moves(fake_link)) == 1  # only the first landing


def test_after_our_own_stop_the_snapshot_says_not_flying_while_the_status_still_says_flying(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    land_and_wait_for_the_landing_approach(adapter, clock)
    assert adapter.take_snapshot(TICK).may_be_flying
    tick_for(adapter, clock, TOUCHDOWN_HOLD + TICK, RangeReading.at_distance(0.02))
    assert motors_stopped(fake_link)
    report_status(adapter, FLYING)

    assert not adapter.take_snapshot(TICK).may_be_flying  # so the safety pre-check skips the flow (ADR-0060)


def test_an_old_on_the_floor_status_counts_as_unknown_so_it_lands(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    # The status stream stalled one tick past its age limit (ADR-0081), after the take-off grace.
    # The drone may be flying: landing is safe, stopping the motors could drop it.
    clock.advance(TAKE_OFF_STATUS_GRACE)
    report_status(adapter, ON_THE_FLOOR)
    clock.advance(STALE_AFTER + TICK)

    adapter.land()

    assert len(landing_approach_moves(fake_link)) == 1
    assert not motors_stopped(fake_link)


def test_an_on_the_floor_status_at_its_age_limit_still_counts_so_land_just_stops_the_motors(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    # Still fresh at exactly its age limit (ADR-0081), after the take-off grace.
    clock.advance(TAKE_OFF_STATUS_GRACE)
    skip_to_a_whole_second(clock)
    report_status(adapter, ON_THE_FLOOR)
    clock.advance(STALE_AFTER)

    adapter.land()

    fake_link.cf.high_level_commander.go_to.assert_not_called()
    assert motors_stopped(fake_link)


# --- A lost link (ADR-0084) -----------------------------------------------------------


def adapter_on_the_floor(clock: SimClock, link: MagicMock) -> CrazyflieAdapter:
    """A connected adapter that never took off."""
    adapter = CrazyflieAdapter(clock)
    adapter._sync_crazyflie = link
    return adapter


def lose_the_link(adapter: CrazyflieAdapter, fake_link: MagicMock) -> None:
    """As cflib does on a link error: the link goes, then the connection_lost callback (facts register)."""
    fake_link.cf.link = None
    adapter._on_connection_lost("radio://0/80/2M/E7E7E7E7E7", "Too many packets lost")


def sent_to_the_drone(fake_link: MagicMock) -> int:
    """How many commands, packets and parameter writes have gone to the drone."""
    crazyflie = fake_link.cf
    return sum(
        len(calls)
        for calls in [
            crazyflie.high_level_commander.mock_calls,
            crazyflie.commander.mock_calls,
            crazyflie.supervisor.mock_calls,
            crazyflie.param.set_value.mock_calls,
            crazyflie.send_packet.mock_calls,
        ]
    )


def a_snapshot(adapter: CrazyflieAdapter) -> Snapshot:
    return adapter._telemetry.snapshot(TICK, is_in_initial_climb=False, may_be_flying=True)


TICK_CALLS: dict[str, Callable[[CrazyflieAdapter], object]] = {
    "take_snapshot": lambda adapter: adapter.take_snapshot(TICK),
    "update_take_off_and_landing": lambda adapter: adapter.update_take_off_and_landing(a_snapshot(adapter)),
    "arm": lambda adapter: adapter.arm(),
    "disarm": lambda adapter: adapter.disarm(),
    "take_off": lambda adapter: adapter.take_off(1.0),
    "land": lambda adapter: adapter.land(),
    "set_velocity": lambda adapter: adapter.set_velocity(Vector3.ZERO),
    "move_to": lambda adapter: adapter.move_to(Vector3(0.0, 0.0, 1.0), 1.0),
    "hover": lambda adapter: adapter.hover(),
    "emergency_stop": lambda adapter: adapter.emergency_stop(),
    "reset_estimate": lambda adapter: adapter.reset_estimate(),
    "chirp": lambda adapter: adapter.chirp(),
    "play_tone": lambda adapter: adapter.play_tone(440.0),
    "silence": lambda adapter: adapter.silence(),
}


@pytest.mark.parametrize("call", TICK_CALLS.values(), ids=TICK_CALLS.keys())
def test_after_a_lost_link_in_flight_every_call_a_tick_makes_raises_and_sends_nothing(
    call: Callable[[CrazyflieAdapter], object], adapter: CrazyflieAdapter, fake_link: MagicMock
) -> None:
    lose_the_link(adapter, fake_link)

    with pytest.raises(ConnectionError, match="The radio link to the drone was lost: Too many packets lost"):
        call(adapter)

    assert sent_to_the_drone(fake_link) == 0


@pytest.mark.parametrize("call", TICK_CALLS.values(), ids=TICK_CALLS.keys())
def test_after_a_lost_link_on_the_floor_every_call_a_tick_makes_raises_and_sends_nothing(
    call: Callable[[CrazyflieAdapter], object], clock: SimClock
) -> None:
    # In flight, some calls read a snapshot before they send, and that raises; on the floor, `land()` doesn't.
    link = MagicMock()
    adapter = adapter_on_the_floor(clock, link)
    lose_the_link(adapter, link)

    with pytest.raises(ConnectionError, match="The radio link to the drone was lost: Too many packets lost"):
        call(adapter)

    assert sent_to_the_drone(link) == 0


def test_after_a_lost_link_in_flight_disconnect_closes_without_landing_and_says_the_drone_may_still_be_flying(
    adapter: CrazyflieAdapter, fake_link: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    lose_the_link(adapter, fake_link)
    with pytest.raises(ConnectionError):
        adapter.take_snapshot(TICK)  # the tick's call

    with caplog.at_level(logging.ERROR, logger=adapter_module.__name__):
        adapter.disconnect()  # the tick's error is on its way: no second one

    assert sent_to_the_drone(fake_link) == 0  # no landing, no silence
    fake_link.close_link.assert_not_called()
    assert caplog.messages[-1] == (
        "Closing without landing: the link is lost and the drone may still be flying. "
        "Run the rescue landing, or tools/emergency_stop.py with something soft under the drone."
    )


def test_a_link_lost_since_the_last_tick_makes_disconnect_raise_so_the_run_ends_with_an_error(
    adapter: CrazyflieAdapter, fake_link: MagicMock
) -> None:
    lose_the_link(adapter, fake_link)

    with pytest.raises(ConnectionError, match="Too many packets lost"):
        adapter.disconnect()

    assert sent_to_the_drone(fake_link) == 0


def test_a_link_lost_on_the_floor_says_the_drone_wasnt_flying(
    clock: SimClock, fake_link: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    adapter = CrazyflieAdapter(clock)
    adapter._sync_crazyflie = fake_link
    lose_the_link(adapter, fake_link)

    with caplog.at_level(logging.ERROR, logger=adapter_module.__name__), pytest.raises(ConnectionError):
        adapter.disconnect()

    assert caplog.messages[-1] == "Closing without landing: the link is lost. The drone wasn't flying."


def lose_the_link_at_the_next_wait(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    sleep_until = clock.sleep_until

    def sleep_and_lose_the_link(deadline: float) -> None:
        sleep_until(deadline)
        lose_the_link(adapter, fake_link)

    monkeypatch.setattr(clock, "sleep_until", sleep_and_lose_the_link)


def test_a_link_lost_while_disconnect_lands_stops_its_wait_with_no_last_resort(
    adapter: CrazyflieAdapter,
    clock: SimClock,
    fake_link: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    lose_the_link_at_the_next_wait(adapter, clock, fake_link, monkeypatch)

    with caplog.at_level(logging.ERROR, logger=adapter_module.__name__), pytest.raises(ConnectionError):
        adapter.disconnect()

    assert len(landing_approach_moves(fake_link)) == 1  # the landing had started
    fake_link.cf.high_level_commander.land.assert_not_called()
    assert "may still be flying" in caplog.messages[-1]


def test_a_link_lost_while_waiting_for_not_flying_stops_the_wait_at_once(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    land_until_the_motors_stop(adapter, clock, fake_link)
    report_status(adapter, FLYING)  # the status still says flying for 2 s after the motors stop
    lose_the_link_at_the_next_wait(adapter, clock, fake_link, monkeypatch)
    started_at = clock.now()

    with pytest.raises(ConnectionError):
        adapter.disconnect()

    assert clock.now() == pytest.approx(started_at + WAIT_SLICE)  # one slice, not NOT_FLYING_TIME_LIMIT


# --- The buzzer's silence at shutdown (ADR-0083) ----------------------------------------


def test_shutdown_silences_the_buzzer_after_the_landing_and_logs_the_drones_confirmation(
    adapter: CrazyflieAdapter, fake_link: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO, logger=adapter_module.__name__)

    adapter.disconnect()

    fake_link.cf.param.set_value.assert_called_once_with("sound.effect", 0)
    calls = [name for name, _, _ in fake_link.mock_calls]
    assert calls.index("cf.high_level_commander.stop") < calls.index("cf.param.set_value")
    assert "The drone confirmed the buzzer's silence." in caplog.messages


def test_without_a_confirmation_shutdown_closes_the_link_at_the_silences_time_limit_with_a_warning(
    clock: SimClock, caplog: pytest.LogCaptureFixture
) -> None:
    link = MagicMock()  # its drone never answers a parameter write
    adapter = adapter_on_the_floor(clock, link)
    closed_at = record_link_close_time(clock, link)
    started_at = clock.now()

    with caplog.at_level(logging.WARNING, logger=adapter_module.__name__):
        adapter.disconnect()

    assert closed_at == [pytest.approx(started_at + SILENCE_CONFIRMATION_TIME_LIMIT)]
    assert caplog.messages == [
        "The drone didn't confirm the buzzer's silence within 1 s. A tone may stay on until the drone is switched off."
    ]


def test_a_confirmation_at_exactly_the_silences_time_limit_still_counts(
    clock: SimClock, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    link = MagicMock()
    callbacks: list[Callable[[str, str], None]] = []

    def add_update_callback(group: str, name: str, cb: Callable[[str, str], None]) -> None:
        callbacks.append(cb)

    link.cf.param.add_update_callback.side_effect = add_update_callback
    adapter = adapter_on_the_floor(clock, link)
    started_at = clock.now()
    sleep_until = clock.sleep_until

    def sleep_and_answer_at_the_time_limit(deadline: float) -> None:
        sleep_until(deadline)
        if clock.now() >= started_at + SILENCE_CONFIRMATION_TIME_LIMIT:
            for callback in callbacks:
                callback("sound.effect", "0")

    monkeypatch.setattr(clock, "sleep_until", sleep_and_answer_at_the_time_limit)

    with caplog.at_level(logging.WARNING, logger=adapter_module.__name__):
        adapter.disconnect()

    assert clock.now() == started_at + SILENCE_CONFIRMATION_TIME_LIMIT
    assert caplog.messages == []


def test_a_report_of_another_buzzer_value_doesnt_confirm_the_silence(
    clock: SimClock, caplog: pytest.LogCaptureFixture
) -> None:
    link = MagicMock()

    def answer_an_earlier_tones_write(group: str, name: str, cb: Callable[[str, str], None]) -> None:
        cb(f"{group}.{name}", "12")  # and nothing after it

    link.cf.param.add_update_callback.side_effect = answer_an_earlier_tones_write
    adapter = adapter_on_the_floor(clock, link)

    with caplog.at_level(logging.WARNING, logger=adapter_module.__name__):
        adapter.disconnect()

    assert "didn't confirm the buzzer's silence" in caplog.text


def test_a_drone_without_the_buzzers_parameter_gets_a_warning_and_no_wait(
    clock: SimClock, caplog: pytest.LogCaptureFixture
) -> None:
    link = MagicMock()
    link.cf.param.set_value.side_effect = KeyError("sound.effect not in param TOC")  # cflib's error (facts register)
    adapter = adapter_on_the_floor(clock, link)
    closed_at = record_link_close_time(clock, link)
    started_at = clock.now()

    with caplog.at_level(logging.WARNING, logger=adapter_module.__name__):
        adapter.disconnect()

    assert closed_at == [started_at]
    assert caplog.messages == ["Buzzer not silenced: the drone has no sound.effect parameter."]
