import math

import pytest

from crazyflie_behavior.drone.crazyflie.bad_flow_zone import (
    LEVEL_VERTICAL_SPEED,
    MAX_FINAL_DESCENT_HEIGHT,
    MIN_FINAL_DESCENT_HEIGHT,
    SETTLE_CAP_HEIGHT,
    final_descent_height,
)
from crazyflie_behavior.drone.interface import FLOW_VELOCITY_UNCERTAINTY
from crazyflie_behavior.drone.mock_adapter import (
    FLOOR_DOWN_RANGE,
    SETPOINT_CUT_MOTORS_AFTER,
    TAKEN_OVER_HEIGHT,
    MockAdapter,
)
from crazyflie_behavior.geometry import Vector3
from crazyflie_behavior.safety.safety_layer import SafetyLayer
from crazyflie_behavior.snapshot import (
    DroneStatus,
    RangeDirection,
    RangeReading,
    RangeStatus,
    Snapshot,
)
from crazyflie_behavior.timing.clock import SimClock

TICK = 0.05
LEVEL_STEP = LEVEL_VERTICAL_SPEED * TICK
"""Meters climbed or descended per tick in a level part."""


def tick(drone: MockAdapter, clock: SimClock, dt: float = TICK) -> None:
    """`dt` seconds pass, then one tick as the tick step runs it: the snapshot, then the update (ADR-0055)."""
    clock.advance(dt)
    drone.update_take_off_and_landing(drone.take_snapshot(dt))


def snapshot_now(drone: MockAdapter) -> Snapshot:
    """A snapshot of what the drone streamed last: its state at the end of the latest update."""
    return drone.take_snapshot(0.0)


def position_of(snapshot: Snapshot) -> Vector3:
    assert snapshot.position_estimate is not None
    return snapshot.position_estimate.value


def xyz(position: Vector3) -> tuple[float, float, float]:
    """For comparing with pytest.approx."""
    return (position.x, position.y, position.z)


def height_now(drone: MockAdapter) -> float:
    return position_of(snapshot_now(drone)).z


def status_of(snapshot: Snapshot) -> DroneStatus:
    assert snapshot.drone_status is not None
    return snapshot.drone_status.value


def flying_drone(clock: SimClock, height: float = 0.5) -> MockAdapter:
    """A drone that took off and has reached `height`."""
    drone = MockAdapter(clock)
    drone.connect()
    drone.arm()
    drone.take_off(height)
    for _ in range(100):
        tick(drone, clock)
        if height_now(drone) == height:
            return drone
    pytest.fail(f"the take-off never reached {height} m")


def tick_until_landed(drone: MockAdapter, clock: SimClock) -> list[float]:
    """Tick until the status says on the floor. Returns the height after each tick."""
    heights: list[float] = []
    for _ in range(100):
        tick(drone, clock)
        heights.append(height_now(drone))
        if not status_of(snapshot_now(drone)).is_flying:
            return heights
    pytest.fail("the drone never landed")


# --- Take-off: the initial climb (ADR-0048) ----------------------------------------


def test_take_off_climbs_level_to_the_lowest_final_descent_height_then_is_at_its_height() -> None:
    clock = SimClock()
    drone = MockAdapter(clock)
    drone.connect()
    drone.arm()

    drone.take_off(0.8)
    heights: list[float] = []
    while not heights or heights[-1] < MIN_FINAL_DESCENT_HEIGHT:
        if len(heights) > 100:
            pytest.fail("the initial climb never ended")
        tick(drone, clock)
        heights.append(height_now(drone))
        assert status_of(snapshot_now(drone)).is_flying

    assert heights[:-1] == [pytest.approx(n * LEVEL_STEP) for n in range(1, len(heights))]
    assert heights[-1] == 0.8  # the high-level climb to the height, teleported
    assert position_of(snapshot_now(drone)).x == 0.0


@pytest.mark.parametrize("height", [0.0, 0.1, MAX_FINAL_DESCENT_HEIGHT])
def test_take_off_to_the_final_descent_heights_cap_or_below_is_a_bug(height: float) -> None:
    drone = MockAdapter(SimClock())
    drone.connect()
    drone.arm()

    with pytest.raises(ValueError, match="cap"):
        drone.take_off(height)


def test_take_off_is_ignored_while_disarmed_like_real_hardware() -> None:
    clock = SimClock()
    drone = MockAdapter(clock)
    drone.connect()

    drone.take_off(0.5)
    tick(drone, clock)

    assert not status_of(snapshot_now(drone)).is_flying


def test_commands_during_the_initial_climb_are_ignored() -> None:
    clock = SimClock()
    drone = MockAdapter(clock)
    drone.connect()
    drone.arm()
    drone.take_off(0.5)
    tick(drone, clock)

    drone.move_to(Vector3(1.0, 0.0, 1.0), duration=2.0)
    drone.set_velocity(Vector3(0.5, 0.0, 0.0))
    drone.hover()
    tick(drone, clock)

    assert xyz(position_of(snapshot_now(drone))) == pytest.approx((0.0, 0.0, 2 * LEVEL_STEP))


def test_an_initial_climb_without_updates_for_too_long_drops_the_drone() -> None:
    # The level setpoints stopped: the firmware cuts the motors (ADR-0048).
    clock = SimClock()
    drone = MockAdapter(clock)
    drone.connect()
    drone.arm()
    drone.take_off(0.5)

    tick(drone, clock, SETPOINT_CUT_MOTORS_AFTER + TICK)

    assert not status_of(snapshot_now(drone)).is_flying
    assert height_now(drone) == 0.0


# --- Landing: the landing approach, then the level final descent (ADR-0048) -------


def test_land_teleports_to_the_final_descent_height_then_descends_level_to_the_floor() -> None:
    clock = SimClock()
    drone = flying_drone(clock)

    drone.land()
    heights = tick_until_landed(drone, clock)

    assert heights[0] == pytest.approx(MIN_FINAL_DESCENT_HEIGHT - LEVEL_STEP)
    assert heights[:-1] == [pytest.approx(MIN_FINAL_DESCENT_HEIGHT - n * LEVEL_STEP) for n in range(1, len(heights))]
    assert heights[-1] == 0.0


def test_after_a_take_over_the_landing_descends_from_the_cap() -> None:
    # No take-off of its own, so no final descent height but the cap (ADR-0056).
    clock = SimClock()
    drone = MockAdapter(clock, take_over_flight=True)
    drone.connect()

    drone.land()
    tick(drone, clock)

    assert height_now(drone) == pytest.approx(MAX_FINAL_DESCENT_HEIGHT - LEVEL_STEP)


def test_land_during_the_initial_climb_descends_level_from_where_it_is() -> None:
    clock = SimClock()
    drone = MockAdapter(clock)
    drone.connect()
    drone.arm()
    drone.take_off(0.5)
    for _ in range(5):
        tick(drone, clock)

    drone.land()
    heights = tick_until_landed(drone, clock)

    assert heights[0] == pytest.approx(4 * LEVEL_STEP)
    assert heights[-1] == 0.0


def test_commands_during_the_final_descent_are_ignored() -> None:
    clock = SimClock()
    drone = flying_drone(clock)
    drone.land()
    tick(drone, clock)

    drone.move_to(Vector3(1.0, 0.0, 1.0), duration=2.0)
    drone.set_velocity(Vector3(0.5, 0.0, 0.0))
    drone.hover()
    drone.take_off(0.5)
    drone.land()
    tick(drone, clock)

    assert xyz(position_of(snapshot_now(drone))) == pytest.approx((0.0, 0.0, MIN_FINAL_DESCENT_HEIGHT - 2 * LEVEL_STEP))


def test_disconnecting_finishes_a_landing_at_once() -> None:
    # The Crazyflie adapter blocks until touchdown; the mock just puts the drone down.
    clock = SimClock()
    drone = flying_drone(clock)
    drone.land()
    tick(drone, clock)

    drone.disconnect()

    assert height_now(drone) == 0.0
    assert not status_of(snapshot_now(drone)).is_flying


# --- Steering mode, fast mode, hover -----------------------------------------------


def test_set_velocity_moves_the_drone_by_velocity_times_dt() -> None:
    clock = SimClock()
    drone = flying_drone(clock, height=0.5)

    drone.set_velocity(Vector3(0.2, -0.1, 0.0))
    tick(drone, clock, 0.4)

    assert xyz(position_of(snapshot_now(drone))) == pytest.approx((0.08, -0.04, 0.5))


def test_streaming_a_velocity_every_tick_keeps_the_drone_moving() -> None:
    clock = SimClock()
    drone = flying_drone(clock)

    for _ in range(30):  # 3 seconds of 10 Hz ticks
        drone.set_velocity(Vector3(0.1, 0.0, 0.0))
        tick(drone, clock, 0.1)

    assert status_of(snapshot_now(drone)).is_flying
    assert position_of(snapshot_now(drone)).x == pytest.approx(0.3)


def test_the_drone_stops_following_a_velocity_that_stops_arriving() -> None:
    clock = SimClock()
    drone = flying_drone(clock)

    drone.set_velocity(Vector3(0.2, 0.0, 0.0))
    tick(drone, clock, 0.6)  # no new set_velocity for longer than the drone waits

    snapshot = snapshot_now(drone)
    assert snapshot.velocity_estimate is not None
    assert snapshot.velocity_estimate.value == Vector3.ZERO
    assert status_of(snapshot).is_flying


def test_the_drone_drops_when_velocities_stop_arriving_for_too_long() -> None:
    clock = SimClock()
    drone = flying_drone(clock)

    drone.set_velocity(Vector3(0.2, 0.0, 0.0))
    tick(drone, clock, 2.5)

    assert not status_of(snapshot_now(drone)).is_flying
    assert height_now(drone) == 0.0


def test_the_setpoint_timeout_only_applies_while_streaming() -> None:
    clock = SimClock()
    drone = flying_drone(clock)
    drone.set_velocity(Vector3(0.2, 0.0, 0.0))

    drone.hover()  # hands control back to the drone, ending the stream
    tick(drone, clock, 5.0)

    assert status_of(snapshot_now(drone)).is_flying


def test_hover_stops_the_drone_where_it_is() -> None:
    clock = SimClock()
    drone = flying_drone(clock)
    drone.set_velocity(Vector3(0.3, 0.0, 0.0))

    drone.hover()
    tick(drone, clock, 1.0)

    assert position_of(snapshot_now(drone)) == Vector3(0.0, 0.0, 0.5)


def test_move_to_arrives_instantly_because_the_mock_has_no_physics() -> None:
    clock = SimClock()
    drone = flying_drone(clock)

    drone.move_to(Vector3(1.0, 1.0, 1.0), duration=3.0)
    tick(drone, clock)

    assert position_of(snapshot_now(drone)) == Vector3(1.0, 1.0, 1.0)


def test_move_to_rejects_a_non_positive_duration_as_a_bug() -> None:
    drone = flying_drone(SimClock())

    with pytest.raises(ValueError, match="duration"):
        drone.move_to(Vector3(1.0, 0.0, 0.5), duration=0.0)


def test_the_mock_can_arm_only_on_the_floor_while_disarmed_and_never_locks() -> None:
    clock = SimClock()
    drone = MockAdapter(clock)
    drone.connect()
    on_the_floor = status_of(snapshot_now(drone))
    drone.arm()
    tick(drone, clock)
    armed = status_of(snapshot_now(drone))
    drone.emergency_stop()  # locks a real Crazyflie
    tick(drone, clock)
    after_the_emergency_stop = status_of(snapshot_now(drone))

    assert [on_the_floor.can_arm, armed.can_arm, after_the_emergency_stop.can_arm] == [True, False, True]
    assert not any(status.is_locked for status in (on_the_floor, armed, after_the_emergency_stop))


def test_emergency_stop_drops_and_disarms() -> None:
    clock = SimClock()
    drone = flying_drone(clock)

    drone.emergency_stop()
    tick(drone, clock)
    status = status_of(snapshot_now(drone))

    assert not status.is_flying
    assert not status.is_armed


# --- Telemetry ---------------------------------------------------------------------


def test_take_snapshot_neither_moves_the_drone_nor_streams() -> None:
    # The update does both (ADR-0055), so a snapshot shows the end of the previous tick.
    clock = SimClock()
    drone = flying_drone(clock)
    drone.set_velocity(Vector3(0.2, 0.0, 0.0))
    clock.advance(0.4)

    first = drone.take_snapshot(0.4)
    second = drone.take_snapshot(0.4)

    assert position_of(first) == position_of(second) == Vector3(0.0, 0.0, 0.5)
    assert first.position_estimate is not None
    assert first.position_estimate.age(clock.now()) == pytest.approx(0.4)


def test_the_room_is_empty_unless_a_test_says_otherwise() -> None:
    clock = SimClock()
    drone = flying_drone(clock)
    drone.set_range_reading(RangeDirection.FRONT, RangeReading.at_distance(0.3))

    readings = snapshot_now(drone).range_readings

    assert readings.front is not None
    assert readings.front.value == RangeReading.at_distance(0.3)
    assert readings.back is not None
    assert readings.back.value.status is RangeStatus.OUT_OF_RANGE


def test_every_value_streams_again_each_tick_like_a_real_drone() -> None:
    clock = SimClock()
    drone = flying_drone(clock)
    drone.set_battery_voltage(3.7)

    tick(drone, clock, 5.0)
    snapshot = snapshot_now(drone)

    assert snapshot.battery_voltage is not None
    assert snapshot.battery_voltage.value == 3.7
    assert snapshot.battery_voltage.age(clock.now()) == 0.0
    assert snapshot.range_readings.down is not None
    assert snapshot.range_readings.down.age(clock.now()) == 0.0


def test_after_stop_telemetry_nothing_arrives_and_every_value_goes_stale() -> None:
    clock = SimClock()
    drone = flying_drone(clock)

    drone.stop_telemetry()
    drone.set_battery_voltage(3.0)
    tick(drone, clock, 1.0)
    snapshot = snapshot_now(drone)

    assert snapshot.battery_voltage is not None
    assert snapshot.battery_voltage.value == 4.0
    for stamped in [
        snapshot.position_estimate,
        snapshot.velocity_estimate,
        snapshot.battery_voltage,
        snapshot.drone_status,
        snapshot.range_readings.down,
    ]:
        assert stamped is not None
        assert stamped.age(clock.now()) == pytest.approx(1.0)


def fly_then_fail(drone: MockAdapter) -> None:
    with drone:
        drone.arm()
        drone.take_off(0.5)
        raise RuntimeError("behavior bug")


def test_leaving_the_with_block_lands_even_when_code_raises() -> None:
    clock = SimClock()
    drone = MockAdapter(clock)

    with pytest.raises(RuntimeError, match="behavior bug"):
        fly_then_fail(drone)

    assert drone.command_log[-2:] == ["disconnect", "land"]
    assert not status_of(snapshot_now(drone)).is_flying


def test_after_connect_every_telemetry_value_has_arrived() -> None:
    # The drone interface's promise (ADR-0031): the first snapshot has nothing missing.
    clock = SimClock()
    drone = MockAdapter(clock)

    drone.connect()
    snapshot = snapshot_now(drone)

    ranges = snapshot.range_readings
    values = [
        snapshot.position_estimate,
        snapshot.velocity_estimate,
        snapshot.battery_voltage,
        snapshot.drone_status,
        ranges.front,
        ranges.back,
        ranges.left,
        ranges.right,
        ranges.up,
        ranges.down,
    ]
    assert None not in values


def test_taking_over_a_flight_finds_the_drone_armed_and_hovering() -> None:
    clock = SimClock()
    drone = MockAdapter(clock, take_over_flight=True)

    drone.connect()
    snapshot = snapshot_now(drone)

    assert status_of(snapshot).is_armed
    assert status_of(snapshot).is_flying
    assert position_of(snapshot) == Vector3(0.0, 0.0, TAKEN_OVER_HEIGHT)


def test_a_taken_over_drone_can_be_landed() -> None:
    clock = SimClock()
    drone = MockAdapter(clock, take_over_flight=True)
    drone.connect()

    drone.land()

    assert tick_until_landed(drone, clock)[-1] == 0.0


def test_without_the_take_over_setting_a_connected_drone_is_on_the_floor() -> None:
    clock = SimClock()
    drone = MockAdapter(clock)

    drone.connect()

    assert not status_of(snapshot_now(drone)).is_flying


# --- The down range follows the height (ADR-0052) ----------------------------------


def down_range_of(snapshot: Snapshot) -> float | None:
    assert snapshot.range_readings.down is not None
    return snapshot.range_readings.down.value.distance


def test_on_the_floor_the_down_range_reads_the_floor_reading() -> None:
    clock = SimClock()
    drone = MockAdapter(clock)
    drone.connect()

    assert down_range_of(snapshot_now(drone)) == FLOOR_DOWN_RANGE


def test_after_a_take_off_the_down_range_reads_the_height() -> None:
    clock = SimClock()

    drone = flying_drone(clock, height=0.8)

    assert down_range_of(snapshot_now(drone)) == 0.8


def test_the_down_range_follows_a_move_and_a_velocity() -> None:
    clock = SimClock()
    drone = flying_drone(clock, height=0.5)

    drone.move_to(Vector3(0.0, 0.0, 1.2), duration=2.0)
    tick(drone, clock, 0.0)
    after_move = down_range_of(snapshot_now(drone))
    drone.set_velocity(Vector3(0.0, 0.0, -0.5))
    tick(drone, clock, 0.4)
    after_velocity = down_range_of(snapshot_now(drone))

    assert after_move == 1.2
    assert after_velocity == pytest.approx(1.0)


def test_after_landing_the_down_range_reads_the_floor_again() -> None:
    clock = SimClock()
    drone = flying_drone(clock)

    drone.land()
    tick_until_landed(drone, clock)

    assert down_range_of(snapshot_now(drone)) == FLOOR_DOWN_RANGE


def test_the_down_range_never_reads_less_than_the_floor_reading() -> None:
    """The mock has no floor to stop it: a velocity can take its height below 0, the reading can't follow."""
    clock = SimClock()
    drone = flying_drone(clock, height=0.5)

    drone.set_velocity(Vector3(0.0, 0.0, -1.5))
    tick(drone, clock, 0.4)  # 0.6 m down from 0.5 m

    assert height_now(drone) < 0.0
    assert down_range_of(snapshot_now(drone)) == FLOOR_DOWN_RANGE


def test_a_down_range_a_test_sets_stays_as_set_whatever_the_height() -> None:
    clock = SimClock()
    drone = MockAdapter(clock)
    drone.connect()
    drone.set_range_reading(RangeDirection.DOWN, RangeReading.invalid())
    drone.arm()

    drone.take_off(0.5)
    tick(drone, clock)
    snapshot = snapshot_now(drone)

    assert snapshot.range_readings.down is not None
    assert snapshot.range_readings.down.value == RangeReading.invalid()


def test_setting_another_direction_leaves_the_down_range_following_the_height() -> None:
    clock = SimClock()
    drone = flying_drone(clock, height=0.6)

    drone.set_range_reading(RangeDirection.FRONT, RangeReading.at_distance(0.3))

    assert down_range_of(snapshot_now(drone)) == 0.6


def test_a_taken_over_flight_reads_its_height_below() -> None:
    clock = SimClock()
    drone = MockAdapter(clock, take_over_flight=True)

    drone.connect()

    assert down_range_of(snapshot_now(drone)) == TAKEN_OVER_HEIGHT


def test_the_floor_reading_is_a_distance_the_real_drone_reads_at_rest() -> None:
    # 0.019-0.024 m at rest on 2026-11-04: above zero, and far below any flying height.
    assert 0.0 < FLOOR_DOWN_RANGE < 0.05


# --- Buzzer ------------------------------------------------------------------------


def test_buzzer_commands_are_recorded_with_each_tones_pitch() -> None:
    drone = MockAdapter(SimClock())
    drone.connect()

    drone.chirp()
    drone.play_tone(392.0)
    drone.play_tone(523.25)
    drone.silence()

    assert drone.command_log == ["connect", "chirp", "play_tone", "play_tone", "silence"]
    assert drone.tone_pitches == [392.0, 523.25]


@pytest.mark.parametrize("pitch", [0.0, -440.0, math.nan, math.inf])
def test_a_tone_pitch_that_isnt_positive_is_a_bug(pitch: float) -> None:
    drone = MockAdapter(SimClock())

    with pytest.raises(ValueError, match="pitch"):
        drone.play_tone(pitch)

    assert drone.tone_pitches == []


# --- The flow (ADR-0054) ---------------------------------------------------------------


def uncertainty_now(drone: MockAdapter) -> float:
    uncertainty = snapshot_now(drone).velocity_uncertainty
    assert uncertainty is not None
    return uncertainty.value


def armed_drone(clock: SimClock) -> MockAdapter:
    drone = MockAdapter(clock)
    drone.connect()
    drone.arm()
    return drone


def climb(drone: MockAdapter, clock: SimClock) -> list[float]:
    """Tick until the initial climb is over. Returns each tick's height."""
    heights: list[float] = []
    while snapshot_now(drone).is_in_initial_climb or not heights:
        if len(heights) > 100:
            pytest.fail("the initial climb never ended")
        tick(drone, clock)
        heights.append(height_now(drone))
    return heights


def test_over_a_dark_floor_the_velocity_uncertainty_is_high_below_its_height() -> None:
    clock = SimClock()
    drone = armed_drone(clock)
    lit = uncertainty_now(drone)

    drone.set_dark_floor(0.2)

    assert lit < FLOW_VELOCITY_UNCERTAINTY < uncertainty_now(drone)


def test_a_climb_over_a_dark_floor_lower_than_the_cap_settles_where_flow_arrives() -> None:
    clock = SimClock()
    drone = armed_drone(clock)
    drone.set_dark_floor(0.2)

    drone.take_off(0.8)
    heights = climb(drone, clock)

    assert heights[-2] == pytest.approx(final_descent_height(0.2), abs=LEVEL_STEP)
    assert heights[-1] == pytest.approx(0.8)


def test_a_climb_over_a_dark_floor_higher_than_the_cap_lands() -> None:
    clock = SimClock()
    drone = armed_drone(clock)
    drone.set_dark_floor(SETTLE_CAP_HEIGHT + 0.1)

    drone.take_off(0.8)
    heights = climb(drone, clock) + tick_until_landed(drone, clock)

    assert max(heights) == pytest.approx(SETTLE_CAP_HEIGHT, abs=LEVEL_STEP)
    assert not status_of(snapshot_now(drone)).is_flying


def test_a_flow_cut_after_the_settle_height_doesnt_undo_it() -> None:
    clock = SimClock()
    drone = armed_drone(clock)
    settle_height = SETTLE_CAP_HEIGHT - 0.03  # its final descent height is above the cap
    drone.set_dark_floor(settle_height)
    drone.take_off(0.8)
    while height_now(drone) < SETTLE_CAP_HEIGHT - LEVEL_STEP:
        tick(drone, clock)

    drone.cut_flow()
    heights = climb(drone, clock)

    assert heights[-1] == pytest.approx(0.8)  # the climb went on past the cap, as the Crazyflie adapter's does


def test_the_snapshot_says_may_be_flying_from_the_take_off_to_touchdown() -> None:
    clock = SimClock()
    drone = armed_drone(clock)
    assert not snapshot_now(drone).may_be_flying

    drone.take_off(0.8)
    climb(drone, clock)
    assert snapshot_now(drone).may_be_flying

    drone.land()
    tick_until_landed(drone, clock)
    assert not snapshot_now(drone).may_be_flying


def test_a_flow_cut_in_flight_fails_the_pre_check_so_the_failsafe_lands() -> None:
    clock = SimClock()
    drone = flying_drone(clock)
    safety_layer = SafetyLayer(drone)

    drone.cut_flow()
    tick(drone, clock)

    assert not safety_layer.pre_check(snapshot_now(drone))
    safety_layer.send()
    assert drone.command_log[-1] == "land"


def test_an_estimate_reset_on_the_floor_puts_the_estimate_at_the_reset_point() -> None:
    clock = SimClock()
    drone = flying_drone(clock)
    drone.move_to(Vector3(1.0, -2.0, 0.5), 1.0)
    drone.land()
    tick_until_landed(drone, clock)

    drone.reset_estimate()

    assert xyz(position_of(snapshot_now(drone)))[:2] == (0.0, 0.0)


def test_an_estimate_reset_in_flight_is_ignored() -> None:
    clock = SimClock()
    drone = flying_drone(clock)
    drone.move_to(Vector3(1.0, -2.0, 0.5), 1.0)

    drone.reset_estimate()
    tick(drone, clock)

    assert xyz(position_of(snapshot_now(drone)))[:2] == (1.0, -2.0)


# --- A set initial climb speed (ADR-0059) -------------------------------------------


def test_take_off_climbs_level_at_a_set_initial_climb_speed() -> None:
    clock = SimClock()
    drone = MockAdapter(clock, initial_climb_speed=0.4)
    drone.connect()
    drone.arm()

    drone.take_off(0.8)
    tick(drone, clock)
    tick(drone, clock)

    assert height_now(drone) == pytest.approx(2 * 0.4 * TICK)


def test_an_initial_climb_speed_outside_the_range_is_refused() -> None:
    with pytest.raises(ValueError, match="initial climb speed"):
        MockAdapter(SimClock(), initial_climb_speed=0.05)
