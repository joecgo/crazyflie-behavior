import threading
from collections.abc import Callable

import pytest

from crazyflie_behavior.drone.telemetry_buffer import TelemetryBuffer
from crazyflie_behavior.geometry import Vector3
from crazyflie_behavior.snapshot import (
    DroneStatus,
    RangeDirection,
    RangeReading,
    RangeReadings,
    Stamped,
)
from crazyflie_behavior.timing.clock import RealClock, SimClock

ORIGIN = Vector3.ZERO
LANDED = DroneStatus(is_armed=False, is_flying=False, is_crashed=False, is_tumbled=False)


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


type BufferOperation = Callable[[TelemetryBuffer], object]

EVERY_OPERATION: dict[str, BufferOperation] = {
    "snapshot": lambda buffer: buffer.snapshot(time=0.0, dt=0.0),
    "latest_position_estimate": lambda buffer: buffer.latest_position_estimate(),
    "write_position_estimate": lambda buffer: buffer.write_position_estimate(ORIGIN, None),
    "write_velocity_estimate": lambda buffer: buffer.write_velocity_estimate(ORIGIN, None),
    "write_range_readings": lambda buffer: buffer.write_range_readings(
        {RangeDirection.FRONT: RangeReading.out_of_range()}, None
    ),
    "write_battery_voltage": lambda buffer: buffer.write_battery_voltage(4.0, None),
    "write_drone_status": lambda buffer: buffer.write_drone_status(LANDED, None),
    "write_estimates_and_status": lambda buffer: buffer.write_estimates_and_status(
        ORIGIN, ORIGIN, LANDED, None
    ),
}


@pytest.mark.parametrize("operation", EVERY_OPERATION.values(), ids=EVERY_OPERATION.keys())
def test_every_read_and_write_waits_for_the_lock(operation: BufferOperation) -> None:
    # The lock is the buffer's whole thread-safety story. Hold it, as a writer
    # in the middle of a write would, and check the operation can't get past it.
    lock = threading.Lock()
    buffer = TelemetryBuffer(SimClock(), lock=lock)
    finished = threading.Event()

    def run_operation() -> None:
        operation(buffer)
        finished.set()

    thread = threading.Thread(target=run_operation, daemon=True)
    with lock:
        thread.start()
        assert not finished.wait(timeout=0.1)  # blocked while the lock is held
    assert finished.wait(timeout=2.0)  # and goes ahead once it's released
    thread.join()


def test_range_readings_written_together_never_appear_split() -> None:
    # A writer thread keeps writing all five Multi-ranger directions at once,
    # each time with a new distance. Every snapshot must show the five from the
    # same write, never a mix of old and new (a torn read). This guards the
    # write-them-together contract; the lock itself is guarded by the test above
    # (on CPython the dict operations here are atomic even without it).
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


def test_estimates_and_status_written_together_share_one_arrival() -> None:
    clock = SimClock(start=3.0)
    buffer = TelemetryBuffer(clock)

    buffer.write_estimates_and_status(ORIGIN, ORIGIN, LANDED, drone_time=1.25)
    snapshot = buffer.snapshot(time=3.0, dt=0.0)

    assert snapshot.position_estimate == Stamped(ORIGIN, 3.0, 1.25)
    assert snapshot.velocity_estimate == Stamped(ORIGIN, 3.0, 1.25)
    assert snapshot.drone_status == Stamped(LANDED, 3.0, 1.25)
