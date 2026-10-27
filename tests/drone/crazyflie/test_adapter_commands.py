"""The Crazyflie adapter's commands, against a fake cflib connection.

Each test checks what the adapter would send to a real drone.
"""

# pyright: reportPrivateUsage=false

import math
from unittest.mock import MagicMock

import pytest

from crazyflie_behavior.drone.crazyflie.adapter import (
    DEFAULT_YAW_RAD,
    HOVER_SETTLE_DURATION,
    MIN_MOVE_DURATION,
    VERTICAL_SPEED,
    CrazyflieAdapter,
)
from crazyflie_behavior.geometry import Vector3
from crazyflie_behavior.snapshot import RangeDirection, RangeReading
from crazyflie_behavior.timing.clock import SimClock


@pytest.fixture
def clock() -> SimClock:
    return SimClock(start=10.0)


@pytest.fixture
def fake_link() -> MagicMock:
    return MagicMock()


@pytest.fixture
def adapter(clock: SimClock, fake_link: MagicMock) -> CrazyflieAdapter:
    adapter = CrazyflieAdapter(clock)
    adapter._sync_crazyflie = fake_link
    return adapter


def call_names(fake_link: MagicMock) -> list[str]:
    """Every call the adapter made, in order, e.g. "cf.supervisor.send_arming_request"."""
    return [name for name, _, _ in fake_link.mock_calls]


def test_take_off_climbs_at_the_vertical_speed_with_the_default_yaw(
    adapter: CrazyflieAdapter, fake_link: MagicMock
) -> None:
    adapter.take_off(1.2)

    fake_link.cf.high_level_commander.takeoff.assert_called_once_with(
        1.2, pytest.approx(1.2 / VERTICAL_SPEED), yaw=DEFAULT_YAW_RAD
    )


def test_take_off_rejects_a_non_positive_height(adapter: CrazyflieAdapter) -> None:
    with pytest.raises(ValueError, match="height"):
        adapter.take_off(0.0)


def test_move_to_never_asks_for_a_move_shorter_than_the_minimum(
    adapter: CrazyflieAdapter, fake_link: MagicMock
) -> None:
    adapter.move_to(Vector3(1.0, 0.0, 0.5), duration=0.1)

    fake_link.cf.high_level_commander.go_to.assert_called_once_with(
        1.0, 0.0, 0.5, DEFAULT_YAW_RAD, MIN_MOVE_DURATION
    )


def test_move_to_rejects_a_non_positive_duration(adapter: CrazyflieAdapter) -> None:
    with pytest.raises(ValueError, match="duration"):
        adapter.move_to(Vector3(1.0, 0.0, 0.5), duration=0.0)


def test_hover_holds_the_latest_position_estimate(
    adapter: CrazyflieAdapter, fake_link: MagicMock
) -> None:
    adapter._telemetry.write_position_estimate(Vector3(0.5, -0.25, 1.0), None)

    adapter.hover()

    fake_link.cf.high_level_commander.go_to.assert_called_once_with(
        0.5, -0.25, 1.0, DEFAULT_YAW_RAD, HOVER_SETTLE_DURATION
    )


def test_hover_without_an_estimate_holds_where_it_is(
    adapter: CrazyflieAdapter, fake_link: MagicMock
) -> None:
    adapter.hover()

    fake_link.cf.high_level_commander.go_to.assert_called_once_with(
        0.0, 0.0, 0.0, DEFAULT_YAW_RAD, HOVER_SETTLE_DURATION, relative=True
    )


def test_set_velocity_sends_the_yaw_rate_in_degrees(
    adapter: CrazyflieAdapter, fake_link: MagicMock
) -> None:
    adapter.set_velocity(Vector3(0.2, 0.0, -0.1), yaw_rate_rad_per_s=math.pi)

    fake_link.cf.commander.send_velocity_world_setpoint.assert_called_once_with(
        0.2, 0.0, -0.1, pytest.approx(180.0)
    )


def test_after_steering_mode_a_high_level_command_first_hands_control_back(
    adapter: CrazyflieAdapter, fake_link: MagicMock
) -> None:
    adapter.set_velocity(Vector3(0.2, 0.0, 0.0))

    adapter.hover()

    calls = call_names(fake_link)
    assert calls.index("cf.commander.send_notify_setpoint_stop") < calls.index(
        "cf.high_level_commander.go_to"
    )


def test_disarm_stops_the_motors_before_disarming(
    adapter: CrazyflieAdapter, fake_link: MagicMock
) -> None:
    adapter.disarm()

    calls = call_names(fake_link)
    assert calls.index("cf.high_level_commander.stop") < calls.index(
        "cf.supervisor.send_arming_request"
    )
    fake_link.cf.supervisor.send_arming_request.assert_called_once_with(False)


def test_emergency_stop_cuts_the_motors_and_cancels_a_landing(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    adapter.take_off(1.0)
    adapter.land()

    adapter.emergency_stop()
    clock.advance(30.0)
    adapter._telemetry.write_range_readings(
        {RangeDirection.DOWN: RangeReading.at_distance(0.02)}, None
    )
    adapter.take_snapshot(clock.now(), 0.05)

    fake_link.cf.supervisor.send_emergency_stop.assert_called_once()
    fake_link.cf.high_level_commander.stop.assert_not_called()  # no landing left to finish


def test_commands_before_connect_say_so(clock: SimClock) -> None:
    adapter = CrazyflieAdapter(clock)

    with pytest.raises(RuntimeError, match="Not connected"):
        adapter.arm()
