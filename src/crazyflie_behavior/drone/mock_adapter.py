"""The mock adapter: a simple fake drone for tests and development.

It answers commands instantly with no physics: `take_off` and `move_to`
teleport, and `set_velocity` moves the drone exactly. It writes its made-up
telemetry through the same `TelemetryBuffer` as every other adapter.

Like real hardware, it ignores commands it can't carry out (e.g. taking off
while disarmed) instead of raising; the outcome shows up in the snapshot.

The room is empty: every range reading is out of range (clear) unless a test
sets it with `set_range_reading`.
"""

from crazyflie_behavior.drone.interface import DroneInterface
from crazyflie_behavior.drone.telemetry_buffer import TelemetryBuffer
from crazyflie_behavior.geometry import Vector3
from crazyflie_behavior.snapshot import DroneStatus, RangeDirection, RangeReading, Snapshot
from crazyflie_behavior.timing.clock import Clock

CHARGED_BATTERY_VOLTAGE = 4.0
"""Volts. A freshly charged Crazyflie battery reads a little above this."""

_ZERO = Vector3(0.0, 0.0, 0.0)


class MockAdapter(DroneInterface):
    """A fake drone that does exactly what it's told, instantly."""

    def __init__(self, clock: Clock) -> None:
        self._clock = clock
        self._telemetry = TelemetryBuffer(clock)
        # Names of the commands received, in order, for tests to check.
        self.command_log: list[str] = []
        self._is_connected = False
        self._is_armed = False
        self._is_flying = False
        self._position = _ZERO
        self._velocity = _ZERO

    # --- Test hooks: set the telemetry a test needs -----------------------------

    def set_range_reading(self, direction: RangeDirection, reading: RangeReading) -> None:
        self._telemetry.write_range_readings({direction: reading}, self._clock.now())

    def set_battery_voltage(self, voltage: float) -> None:
        self._telemetry.write_battery_voltage(voltage, self._clock.now())

    # --- DroneInterface ---------------------------------------------------------

    def connect(self) -> None:
        self.command_log.append("connect")
        self._is_connected = True
        self._telemetry.write_range_readings(
            dict.fromkeys(RangeDirection, RangeReading.out_of_range()), self._clock.now()
        )
        self.set_battery_voltage(CHARGED_BATTERY_VOLTAGE)
        self._publish_state()

    def disconnect(self) -> None:
        self.command_log.append("disconnect")
        if self._is_flying:
            self.land()
        self._is_connected = False

    def arm(self) -> None:
        self.command_log.append("arm")
        if self._is_connected:
            self._is_armed = True

    def disarm(self) -> None:
        self.command_log.append("disarm")
        self._is_armed = False
        self._drop_to_ground()

    def take_off(self, height: float) -> None:
        self.command_log.append("take_off")
        if height <= 0.0:
            raise ValueError(f"Take-off height must be positive: {height}")
        if self._is_armed and not self._is_flying:
            self._is_flying = True
            self._position = Vector3(self._position.x, self._position.y, height)
            self._velocity = _ZERO

    def land(self) -> None:
        self.command_log.append("land")
        self._drop_to_ground()

    def set_velocity(self, velocity: Vector3, yaw_rate_rad_per_s: float = 0.0) -> None:
        self.command_log.append("set_velocity")
        # Yaw is held fixed (ADR-0008), so the mock ignores the yaw rate.
        if self._is_flying:
            self._velocity = velocity

    def move_to(self, position: Vector3, duration: float) -> None:
        self.command_log.append("move_to")
        if duration <= 0.0:
            raise ValueError(f"Move duration must be positive: {duration}")
        if self._is_flying:
            self._position = position
            self._velocity = _ZERO

    def hover(self) -> None:
        self.command_log.append("hover")
        self._velocity = _ZERO

    def emergency_stop(self) -> None:
        self.command_log.append("emergency_stop")
        self._is_armed = False
        self._drop_to_ground()

    def take_snapshot(self, time: float, dt: float) -> Snapshot:
        if self._is_flying:
            self._position = self._position + self._velocity * dt
        self._publish_state()
        return self._telemetry.snapshot(time, dt)

    # --- Internals --------------------------------------------------------------

    def _drop_to_ground(self) -> None:
        self._is_flying = False
        self._position = Vector3(self._position.x, self._position.y, 0.0)
        self._velocity = _ZERO

    def _publish_state(self) -> None:
        drone_time = self._clock.now()
        self._telemetry.write_position_estimate(self._position, drone_time)
        self._telemetry.write_velocity_estimate(self._velocity, drone_time)
        self._telemetry.write_drone_status(
            DroneStatus(
                is_armed=self._is_armed,
                is_flying=self._is_flying,
                is_crashed=False,
                is_tumbled=False,
            ),
            drone_time,
        )
