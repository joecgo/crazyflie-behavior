import pytest

from crazyflie_behavior.drone.mock_adapter import MockAdapter
from crazyflie_behavior.geometry import Vector3
from crazyflie_behavior.snapshot import (
    DroneStatus,
    RangeDirection,
    RangeReading,
    RangeStatus,
    Snapshot,
)
from crazyflie_behavior.timing.clock import SimClock


def snapshot_now(drone: MockAdapter, clock: SimClock, dt: float = 0.0) -> Snapshot:
    return drone.take_snapshot(clock.now(), dt)


def position_of(snapshot: Snapshot) -> Vector3:
    assert snapshot.position_estimate is not None
    return snapshot.position_estimate.value


def status_of(snapshot: Snapshot) -> DroneStatus:
    assert snapshot.drone_status is not None
    return snapshot.drone_status.value


def flying_drone(clock: SimClock, height: float = 0.5) -> MockAdapter:
    drone = MockAdapter(clock)
    drone.connect()
    drone.arm()
    drone.take_off(height)
    return drone


def test_take_off_rises_to_the_height_and_reports_flying() -> None:
    clock = SimClock()

    drone = flying_drone(clock, height=0.8)
    snapshot = snapshot_now(drone, clock)

    assert position_of(snapshot) == Vector3(0.0, 0.0, 0.8)
    assert status_of(snapshot).is_flying


def test_take_off_is_ignored_while_disarmed_like_real_hardware() -> None:
    clock = SimClock()
    drone = MockAdapter(clock)
    drone.connect()

    drone.take_off(0.5)

    assert not status_of(snapshot_now(drone, clock)).is_flying


def test_set_velocity_moves_the_drone_by_velocity_times_dt() -> None:
    clock = SimClock()
    drone = flying_drone(clock, height=0.5)

    drone.set_velocity(Vector3(0.2, -0.1, 0.0))
    clock.advance(0.4)
    snapshot = snapshot_now(drone, clock, dt=0.4)

    assert position_of(snapshot).x == pytest.approx(0.08)
    assert position_of(snapshot).y == pytest.approx(-0.04)
    assert position_of(snapshot).z == pytest.approx(0.5)


def test_streaming_a_velocity_every_tick_keeps_the_drone_moving() -> None:
    clock = SimClock()
    drone = flying_drone(clock)

    for _ in range(30):  # 3 seconds of 10 Hz ticks
        drone.set_velocity(Vector3(0.1, 0.0, 0.0))
        clock.advance(0.1)
        snapshot_now(drone, clock, dt=0.1)
    snapshot = snapshot_now(drone, clock)

    assert status_of(snapshot).is_flying
    assert position_of(snapshot).x == pytest.approx(0.3)


def test_the_drone_stops_following_a_velocity_that_stops_arriving() -> None:
    clock = SimClock()
    drone = flying_drone(clock)

    drone.set_velocity(Vector3(0.2, 0.0, 0.0))
    clock.advance(0.6)  # no new set_velocity for longer than the drone waits
    snapshot = snapshot_now(drone, clock, dt=0.6)

    assert snapshot.velocity_estimate is not None
    assert snapshot.velocity_estimate.value == Vector3.ZERO
    assert status_of(snapshot).is_flying


def test_the_drone_drops_when_velocities_stop_arriving_for_too_long() -> None:
    clock = SimClock()
    drone = flying_drone(clock)

    drone.set_velocity(Vector3(0.2, 0.0, 0.0))
    clock.advance(2.5)
    snapshot = snapshot_now(drone, clock, dt=2.5)

    assert not status_of(snapshot).is_flying
    assert position_of(snapshot).z == 0.0


def test_the_setpoint_timeout_only_applies_while_streaming() -> None:
    clock = SimClock()
    drone = flying_drone(clock)
    drone.set_velocity(Vector3(0.2, 0.0, 0.0))

    drone.hover()  # hands control back to the drone, ending the stream
    clock.advance(5.0)

    assert status_of(snapshot_now(drone, clock, dt=5.0)).is_flying


def test_hover_stops_the_drone_where_it_is() -> None:
    clock = SimClock()
    drone = flying_drone(clock)
    drone.set_velocity(Vector3(0.3, 0.0, 0.0))

    drone.hover()
    snapshot = snapshot_now(drone, clock, dt=1.0)

    assert position_of(snapshot) == Vector3(0.0, 0.0, 0.5)


def test_move_to_arrives_instantly_because_the_mock_has_no_physics() -> None:
    clock = SimClock()
    drone = flying_drone(clock)

    drone.move_to(Vector3(1.0, 1.0, 1.0), duration=3.0)

    assert position_of(snapshot_now(drone, clock)) == Vector3(1.0, 1.0, 1.0)


def test_move_to_rejects_a_non_positive_duration_as_a_bug() -> None:
    drone = flying_drone(SimClock())

    with pytest.raises(ValueError, match="duration"):
        drone.move_to(Vector3(1.0, 0.0, 0.5), duration=0.0)


def test_land_puts_the_drone_on_the_ground() -> None:
    clock = SimClock()
    drone = flying_drone(clock)

    drone.land()
    snapshot = snapshot_now(drone, clock)

    assert position_of(snapshot).z == 0.0
    assert not status_of(snapshot).is_flying


def test_emergency_stop_drops_and_disarms() -> None:
    clock = SimClock()
    drone = flying_drone(clock)

    drone.emergency_stop()
    status = status_of(snapshot_now(drone, clock))

    assert not status.is_flying
    assert not status.is_armed


def test_the_room_is_empty_unless_a_test_says_otherwise() -> None:
    clock = SimClock()
    drone = flying_drone(clock)
    drone.set_range_reading(RangeDirection.FRONT, RangeReading.at_distance(0.3))

    readings = snapshot_now(drone, clock).range_readings

    assert readings.front is not None
    assert readings.front.value == RangeReading.at_distance(0.3)
    assert readings.back is not None
    assert readings.back.value.status is RangeStatus.OUT_OF_RANGE


def test_every_value_streams_again_with_each_snapshot_like_a_real_drone() -> None:
    clock = SimClock()
    drone = flying_drone(clock)
    drone.set_battery_voltage(3.7)
    clock.advance(5.0)

    snapshot = snapshot_now(drone, clock, dt=5.0)

    assert snapshot.battery_voltage is not None
    assert snapshot.battery_voltage.value == 3.7
    assert snapshot.battery_voltage.age(clock.now()) == 0.0
    assert snapshot.range_readings.down is not None
    assert snapshot.range_readings.down.age(clock.now()) == 0.0


def test_after_stop_telemetry_nothing_arrives_and_every_value_goes_stale() -> None:
    clock = SimClock()
    drone = flying_drone(clock)
    snapshot_now(drone, clock)

    drone.stop_telemetry()
    drone.set_battery_voltage(3.0)
    clock.advance(1.0)
    snapshot = snapshot_now(drone, clock, dt=1.0)

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
        assert stamped.age(clock.now()) == 1.0


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
    assert not status_of(snapshot_now(drone, clock)).is_flying


def test_after_connect_every_telemetry_value_has_arrived() -> None:
    # The drone interface's promise (ADR-0031): the first snapshot has nothing missing.
    clock = SimClock()
    drone = MockAdapter(clock)

    drone.connect()
    snapshot = snapshot_now(drone, clock)

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
