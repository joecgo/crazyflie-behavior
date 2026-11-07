"""The Crazyflie adapter's commands, against a fake cflib connection.

Each test checks what the adapter would send to a real drone.
"""

# pyright: reportPrivateUsage=false

import logging
import math
from unittest.mock import MagicMock

import pytest

from crazyflie_behavior.drone.crazyflie import adapter as adapter_module
from crazyflie_behavior.drone.crazyflie.adapter import (
    DEFAULT_YAW_RAD,
    HOVER_SETTLE_DURATION,
    MIN_MOVE_DURATION,
    TAKE_OFF_STATUS_GRACE,
    CrazyflieAdapter,
)
from crazyflie_behavior.drone.crazyflie.bad_flow_zone import LEVEL_VERTICAL_SPEED, MAX_FINAL_DESCENT_HEIGHT
from crazyflie_behavior.geometry import Vector3
from crazyflie_behavior.snapshot import DroneStatus, RangeDirection, RangeReading
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


ON_THE_FLOOR = DroneStatus(is_armed=True, is_flying=False, is_crashed=False, is_tumbled=False)
FLYING = DroneStatus(is_armed=True, is_flying=True, is_crashed=False, is_tumbled=False)
TICK = 0.05


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
        height += LEVEL_VERTICAL_SPEED * TICK
        telemetry = adapter._telemetry
        if with_position:
            telemetry.write_position_estimate(Vector3(0.5, -0.25, height), None)
        telemetry.write_velocity_estimate(Vector3(0.0, 0.0, LEVEL_VERTICAL_SPEED), None)
        telemetry.write_drone_status(FLYING, None)
        telemetry.write_range_readings({RangeDirection.DOWN: RangeReading.at_distance(height)}, None)
        adapter.update_take_off_and_landing(adapter.take_snapshot(TICK))
    fake_link.reset_mock()


@pytest.mark.parametrize("height", [0.0, 0.1, MAX_FINAL_DESCENT_HEIGHT])
def test_take_off_to_the_final_descent_heights_cap_or_below_is_a_bug_and_sends_nothing(
    adapter: CrazyflieAdapter, fake_link: MagicMock, height: float
) -> None:
    with pytest.raises(ValueError, match="cap"):
        adapter.take_off(height)

    assert call_names(fake_link) == []


def test_move_to_never_asks_for_a_move_shorter_than_the_minimum(
    adapter: CrazyflieAdapter, fake_link: MagicMock
) -> None:
    adapter.move_to(Vector3(1.0, 0.0, 0.5), duration=0.1)

    fake_link.cf.high_level_commander.go_to.assert_called_once_with(1.0, 0.0, 0.5, DEFAULT_YAW_RAD, MIN_MOVE_DURATION)


def test_move_to_rejects_a_non_positive_duration(adapter: CrazyflieAdapter) -> None:
    with pytest.raises(ValueError, match="duration"):
        adapter.move_to(Vector3(1.0, 0.0, 0.5), duration=0.0)


def test_hover_holds_the_latest_position_estimate(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    fly_above_the_bad_flow_zone(adapter, clock, fake_link)
    adapter._telemetry.write_position_estimate(Vector3(0.5, -0.25, 1.0), None)

    adapter.hover()

    fake_link.cf.high_level_commander.go_to.assert_called_once_with(
        0.5, -0.25, 1.0, DEFAULT_YAW_RAD, HOVER_SETTLE_DURATION
    )


def test_hover_without_an_estimate_holds_where_it_is(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    fly_above_the_bad_flow_zone(adapter, clock, fake_link, with_position=False)

    adapter.hover()

    fake_link.cf.high_level_commander.go_to.assert_called_once_with(
        0.0, 0.0, 0.0, DEFAULT_YAW_RAD, HOVER_SETTLE_DURATION, relative=True
    )


def test_hover_on_the_floor_does_nothing(adapter: CrazyflieAdapter, fake_link: MagicMock) -> None:
    # A go_to at floor height would spin up an armed drone's motors (ADR-0039).
    adapter.hover()

    assert call_names(fake_link) == []


def test_hover_after_our_own_motor_stop_does_nothing_though_the_status_still_says_flying(
    adapter: CrazyflieAdapter, fake_link: MagicMock
) -> None:
    adapter.take_off(1.0)
    adapter.emergency_stop()
    fake_link.reset_mock()
    adapter._telemetry.write_drone_status(FLYING, None)  # the supervisor says flying for 2 s after the stop

    adapter.hover()

    assert call_names(fake_link) == []


def test_hover_after_a_take_off_that_never_flew_does_nothing(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    adapter.take_off(1.0)
    clock.advance(TAKE_OFF_STATUS_GRACE + 0.5)
    adapter._telemetry.write_drone_status(ON_THE_FLOOR, None)  # fresh, and says on the floor
    fake_link.reset_mock()

    adapter.hover()

    assert call_names(fake_link) == []


def test_hover_right_after_the_initial_climb_still_flies_before_the_status_shows_flying(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    fly_above_the_bad_flow_zone(adapter, clock, fake_link)
    adapter._take_off_sent_at = clock.now()  # a climb quicker than the status: still in the take-off grace
    adapter._telemetry.write_drone_status(ON_THE_FLOOR, None)

    adapter.hover()

    fake_link.cf.high_level_commander.go_to.assert_called_once()


def test_hover_on_the_floor_is_logged_once_per_streak_at_info_level(
    adapter: CrazyflieAdapter, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO, logger=adapter_module.logger.name):
        adapter.hover()
        adapter.hover()
        adapter.hover()
        adapter.take_off(1.0)  # flying: the streak is over
        adapter.emergency_stop()
        adapter.hover()  # a new streak

    ignored = [record for record in caplog.records if "Hover ignored" in record.getMessage()]
    assert len(ignored) == 2
    assert {record.levelno for record in ignored} == {logging.INFO}


def test_a_hover_that_goes_through_ends_the_streak_of_ignored_ones(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    # After the rescue landing takes over a flight, no take-off is ever sent, so a hover that goes
    # through is the only thing that can end a streak of ignored ones (ADR-0038, ADR-0039).
    fly_above_the_bad_flow_zone(adapter, clock, fake_link)
    clock.advance(TAKE_OFF_STATUS_GRACE + 0.5)
    with caplog.at_level(logging.INFO, logger=adapter_module.logger.name):
        adapter._telemetry.write_drone_status(ON_THE_FLOOR, None)
        adapter.hover()  # ignored: the first streak
        adapter._telemetry.write_drone_status(FLYING, None)
        adapter.hover()  # goes through
        adapter._telemetry.write_drone_status(ON_THE_FLOOR, None)
        adapter.hover()  # ignored: a new streak

    fake_link.cf.high_level_commander.go_to.assert_called_once()
    ignored = [record for record in caplog.records if "Hover ignored" in record.getMessage()]
    assert len(ignored) == 2


def test_set_velocity_sends_the_yaw_rate_in_degrees(adapter: CrazyflieAdapter, fake_link: MagicMock) -> None:
    adapter.set_velocity(Vector3(0.2, 0.0, -0.1), yaw_rate_rad_per_s=math.pi)

    fake_link.cf.commander.send_velocity_world_setpoint.assert_called_once_with(0.2, 0.0, -0.1, pytest.approx(180.0))


def test_after_steering_mode_a_hover_goes_out_before_the_stream_is_released(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    # Released first, the high-level planner, stopped by the stream, would command the motors off (ADR-0048).
    fly_above_the_bad_flow_zone(adapter, clock, fake_link)
    adapter.set_velocity(Vector3(0.2, 0.0, 0.0))

    adapter.hover()

    assert call_names(fake_link)[-2:] == ["cf.high_level_commander.go_to", "cf.commander.send_notify_setpoint_stop"]


def test_after_steering_mode_a_move_to_goes_out_before_the_stream_is_released(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    fly_above_the_bad_flow_zone(adapter, clock, fake_link)
    adapter.set_velocity(Vector3(0.2, 0.0, 0.0))

    adapter.move_to(Vector3(1.0, 0.0, 1.0), duration=2.0)

    assert call_names(fake_link)[-2:] == ["cf.high_level_commander.go_to", "cf.commander.send_notify_setpoint_stop"]


def test_without_a_stream_a_high_level_command_releases_nothing(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    fly_above_the_bad_flow_zone(adapter, clock, fake_link)

    adapter.hover()

    assert call_names(fake_link) == ["cf.high_level_commander.go_to"]


def test_disarm_stops_the_motors_before_disarming(adapter: CrazyflieAdapter, fake_link: MagicMock) -> None:
    adapter.disarm()

    calls = call_names(fake_link)
    assert calls.index("cf.high_level_commander.stop") < calls.index("cf.supervisor.send_arming_request")
    fake_link.cf.supervisor.send_arming_request.assert_called_once_with(False)


def test_emergency_stop_cuts_the_motors_and_cancels_a_landing(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    adapter.take_off(1.0)
    adapter.land()

    adapter.emergency_stop()
    clock.advance(30.0)
    adapter._telemetry.write_range_readings({RangeDirection.DOWN: RangeReading.at_distance(0.02)}, None)
    adapter.update_take_off_and_landing(adapter.take_snapshot(0.05))

    fake_link.cf.supervisor.send_emergency_stop.assert_called_once()
    fake_link.cf.high_level_commander.stop.assert_not_called()  # no landing left to finish


def test_commands_before_connect_say_so(clock: SimClock) -> None:
    adapter = CrazyflieAdapter(clock)

    with pytest.raises(RuntimeError, match="Not connected"):
        adapter.arm()


# --- Buzzer (ADR-0053) --------------------------------------------------------------


def parameter_writes(fake_link: MagicMock) -> list[tuple[str, int]]:
    """Each parameter write the adapter queued, in order: (name, value)."""
    return [(write.args[0], write.args[1]) for write in fake_link.cf.param.set_value.call_args_list]


def test_a_chirp_plays_the_firmwares_two_note_tune(adapter: CrazyflieAdapter, fake_link: MagicMock) -> None:
    adapter.chirp()

    assert parameter_writes(fake_link) == [("sound.effect", 4)]


def test_a_tone_sets_its_pitch_in_whole_hertz_before_starting_the_steady_tone(
    adapter: CrazyflieAdapter, fake_link: MagicMock
) -> None:
    adapter.play_tone(391.995)

    assert parameter_writes(fake_link) == [("sound.freq", 392), ("sound.effect", 12)]


def test_a_silence_switches_the_sound_off(adapter: CrazyflieAdapter, fake_link: MagicMock) -> None:
    adapter.silence()

    assert parameter_writes(fake_link) == [("sound.effect", 0)]


def test_a_tone_the_firmware_cant_hold_is_a_bug_and_writes_nothing(
    adapter: CrazyflieAdapter, fake_link: MagicMock
) -> None:
    with pytest.raises(ValueError, match="can't play"):
        adapter.play_tone(70_000.0)

    assert parameter_writes(fake_link) == []


def buzzer_warnings(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING and "Buzzer" in r.getMessage()]


def test_buzzer_commands_on_a_closed_link_are_skipped_with_a_warning_once_per_streak(
    adapter: CrazyflieAdapter, fake_link: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    """cflib's parameter write raises once the link is lost, unlike a movement command (ADR-0053)."""
    fake_link.cf.link = None

    with caplog.at_level(logging.WARNING, logger=adapter_module.logger.name):
        adapter.chirp()
        adapter.play_tone(523.25)
        adapter.silence()

    assert parameter_writes(fake_link) == []
    assert buzzer_warnings(caplog) == ["Buzzer command not sent: the link is closed. Warned once per streak."]


def test_a_buzzer_command_that_goes_through_ends_the_streak(
    adapter: CrazyflieAdapter, fake_link: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    radio_link = fake_link.cf.link
    with caplog.at_level(logging.WARNING, logger=adapter_module.logger.name):
        fake_link.cf.link = None
        adapter.chirp()  # a streak starts: one warning
        fake_link.cf.link = radio_link
        adapter.chirp()  # written: the streak ends
        fake_link.cf.link = None
        adapter.chirp()  # a new streak: a new warning

    assert parameter_writes(fake_link) == [("sound.effect", 4)]
    assert len(buzzer_warnings(caplog)) == 2
