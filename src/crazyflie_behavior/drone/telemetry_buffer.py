"""The telemetry buffer: latest telemetry, written in the background (ADR-0007).

Adapters write here from whatever thread their data arrives on; the tick loop
calls `snapshot()` once per tick. A single lock guards both sides. It's the
only lock in the data path, so behaviors never need one.

Every adapter uses this same class (ADR-0008), so the locking is written and
tested once.
"""

import threading
from collections.abc import Mapping

from crazyflie_behavior.geometry import Vector3
from crazyflie_behavior.snapshot import (
    DroneStatus,
    RangeDirection,
    RangeReading,
    RangeReadings,
    Snapshot,
    Stamped,
)
from crazyflie_behavior.timing.clock import Clock


class TelemetryBuffer:
    """Thread-safe store of the latest value of each telemetry variable."""

    # Quoted because in Python 3.12 threading.Lock is a factory function at
    # run time, so `threading.Lock | None` only works as a type-checker hint.
    def __init__(self, clock: Clock, *, lock: "threading.Lock | None" = None) -> None:
        """`lock` lets a test hold the buffer's lock; adapters leave it out."""
        self._clock = clock
        self._lock = lock if lock is not None else threading.Lock()
        self._position_estimate: Stamped[Vector3] | None = None
        self._velocity_estimate: Stamped[Vector3] | None = None
        self._range_readings: dict[RangeDirection, Stamped[RangeReading]] = {}
        self._battery_voltage: Stamped[float] | None = None
        self._drone_status: Stamped[DroneStatus] | None = None

    # --- Writers: called by adapters, from any thread -------------------------

    def write_position_estimate(self, position: Vector3, drone_time: float | None) -> None:
        stamped = Stamped(position, self._clock.now(), drone_time)
        with self._lock:
            self._position_estimate = stamped

    def write_velocity_estimate(self, velocity: Vector3, drone_time: float | None) -> None:
        stamped = Stamped(velocity, self._clock.now(), drone_time)
        with self._lock:
            self._velocity_estimate = stamped

    def write_range_readings(
        self,
        range_readings: Mapping[RangeDirection, RangeReading],
        drone_time: float | None,
    ) -> None:
        """Write readings that arrived together. They always appear together.

        A snapshot never mixes some directions from one sample with others
        from the previous sample (a torn read).
        """
        arrival_time = self._clock.now()
        stamped = {
            direction: Stamped(reading, arrival_time, drone_time)
            for direction, reading in range_readings.items()
        }
        with self._lock:
            self._range_readings.update(stamped)

    def write_battery_voltage(self, voltage: float, drone_time: float | None) -> None:
        stamped = Stamped(voltage, self._clock.now(), drone_time)
        with self._lock:
            self._battery_voltage = stamped

    def write_drone_status(self, status: DroneStatus, drone_time: float | None) -> None:
        stamped = Stamped(status, self._clock.now(), drone_time)
        with self._lock:
            self._drone_status = stamped

    def write_estimates_and_status(
        self,
        position: Vector3,
        velocity: Vector3,
        status: DroneStatus,
        drone_time: float | None,
    ) -> None:
        """Write a position estimate, velocity estimate and drone status that arrived
        together. They always appear together, like `write_range_readings`."""
        arrival_time = self._clock.now()
        with self._lock:
            self._position_estimate = Stamped(position, arrival_time, drone_time)
            self._velocity_estimate = Stamped(velocity, arrival_time, drone_time)
            self._drone_status = Stamped(status, arrival_time, drone_time)

    # --- Readers --------------------------------------------------------------

    def latest_position_estimate(self) -> Stamped[Vector3] | None:
        """For adapters that need the drone's position to carry out a command."""
        with self._lock:
            return self._position_estimate

    def snapshot(self, time: float, dt: float) -> Snapshot:
        """Copy everything into a read-only snapshot for one tick (ADR-0007).

        Stored values are immutable, so copying references under the lock
        gives a true, consistent copy.
        """
        with self._lock:
            position_estimate = self._position_estimate
            velocity_estimate = self._velocity_estimate
            range_readings = dict(self._range_readings)
            battery_voltage = self._battery_voltage
            drone_status = self._drone_status

        return Snapshot(
            time=time,
            dt=dt,
            position_estimate=position_estimate,
            velocity_estimate=velocity_estimate,
            range_readings=RangeReadings(
                front=range_readings.get(RangeDirection.FRONT),
                back=range_readings.get(RangeDirection.BACK),
                left=range_readings.get(RangeDirection.LEFT),
                right=range_readings.get(RangeDirection.RIGHT),
                up=range_readings.get(RangeDirection.UP),
                down=range_readings.get(RangeDirection.DOWN),
            ),
            battery_voltage=battery_voltage,
            drone_status=drone_status,
        )
