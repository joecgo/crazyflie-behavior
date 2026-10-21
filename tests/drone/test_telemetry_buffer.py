import threading

import pytest

from crazyflie_behavior.drone.telemetry_buffer import TelemetryBuffer
from crazyflie_behavior.geometry import Vector3
from crazyflie_behavior.snapshot import RangeDirection, RangeReading, RangeReadings, Stamped
from crazyflie_behavior.timing.clock import RealClock, SimClock


def test_values_are_stamped_with_arrival_time_and_drone_time() -> None:
    clock = SimClock(start=12.0)
    buffer = TelemetryBuffer(clock)

    buffer.write_position_estimate(Vector3(1.0, 2.0, 0.5), drone_time=3.5)
    clock.advance(0.1)
    snapshot = buffer.snapshot(time=clock.now(), dt=0.1)

    position_estimate = snapshot.position_estimate
    assert position_estimate is not None
    assert position_estimate == Stamped(Vector3(1.0, 2.0, 0.5), arrival_time=12.0, drone_time=3.5)
    assert position_estimate.age(snapshot.time) == pytest.approx(0.1)


def test_snapshot_carries_the_tick_time_and_dt() -> None:
    buffer = TelemetryBuffer(SimClock())

    snapshot = buffer.snapshot(time=7.0, dt=0.05)

    assert (snapshot.time, snapshot.dt) == (7.0, 0.05)


def test_nothing_received_yet_shows_as_none() -> None:
    snapshot = TelemetryBuffer(SimClock()).snapshot(time=0.0, dt=0.0)

    assert snapshot.position_estimate is None
    assert snapshot.drone_status is None
    assert snapshot.range_readings == RangeReadings(None, None, None, None, None, None)


def test_a_snapshot_does_not_change_when_new_telemetry_arrives() -> None:
    buffer = TelemetryBuffer(SimClock())
    buffer.write_battery_voltage(3.9, drone_time=None)
    snapshot = buffer.snapshot(time=0.0, dt=0.0)

    buffer.write_battery_voltage(3.6, drone_time=None)

    assert snapshot.battery_voltage is not None
    assert snapshot.battery_voltage.value == 3.9


def test_range_readings_written_together_never_appear_split() -> None:
    # A writer thread keeps writing all five Multi-ranger directions at once,
    # each time with a new distance. Every snapshot must show the five from the
    # same write, never a mix of old and new (a torn read).
    buffer = TelemetryBuffer(RealClock())
    directions = [
        RangeDirection.FRONT,
        RangeDirection.BACK,
        RangeDirection.LEFT,
        RangeDirection.RIGHT,
        RangeDirection.UP,
    ]
    stop_writing = threading.Event()

    def write_continuously() -> None:
        distance = 0.0
        while not stop_writing.is_set():
            distance = (distance + 0.001) % 4.0
            reading = RangeReading.at_distance(distance)
            buffer.write_range_readings(dict.fromkeys(directions, reading), drone_time=None)

    writer = threading.Thread(target=write_continuously, daemon=True)
    writer.start()
    try:
        for _ in range(5000):
            readings = buffer.snapshot(time=0.0, dt=0.0).range_readings
            five = [readings.front, readings.back, readings.left, readings.right, readings.up]
            distances = {stamped.value.distance for stamped in five if stamped is not None}
            assert len(distances) <= 1
    finally:
        stop_writing.set()
        writer.join()
