"""The mock adapter: a simple fake drone for tests and development.

It answers commands instantly with no physics: `take_off` and `move_to`
teleport, and `set_velocity` moves the drone exactly. It writes its made-up
telemetry through the same `TelemetryBuffer` as every other adapter.

Like real hardware, it ignores commands it can't carry out (e.g. taking off
while disarmed) instead of raising; the outcome shows up in the snapshot.

Also like real hardware, it stops following velocity setpoints that stop
arriving (ADR-0011): a stream someone forgot to send every tick fails in tests
the way it would in the air.

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

# From the firmware source (supervisor.c, checked 2026-10-29): a Crazyflie
# levels out 0.5 s after velocity setpoints stop, and cuts its motors after
# 2 s. VERIFY at the bench that the drone's firmware matches (ADR-0011).
SETPOINT_STOP_FOLLOWING_AFTER = 0.5
"""Seconds without a set_velocity before the drone stops following it."""
SETPOINT_CUT_MOTORS_AFTER = 2.0
"""Seconds without a set_velocity before the motors are cut and the drone drops."""


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
        self._position = Vector3.ZERO
        self._velocity = Vector3.ZERO
        # When the last set_velocity arrived; None when not in steering mode.
        self._last_setpoint_time: float | None = None

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
            self._velocity = Vector3.ZERO
            self._last_setpoint_time = None

    def land(self) -> None:
        self.command_log.append("land")
        self._drop_to_ground()

    def set_velocity(self, velocity: Vector3, yaw_rate_rad_per_s: float = 0.0) -> None:
        self.command_log.append("set_velocity")
        # Yaw is held fixed (ADR-0008), so the mock ignores the yaw rate.
        if self._is_flying:
            self._velocity = velocity
            self._last_setpoint_time = self._clock.now()

    def move_to(self, position: Vector3, duration: float) -> None:
        self.command_log.append("move_to")
        if duration <= 0.0:
            raise ValueError(f"Move duration must be positive: {duration}")
        if self._is_flying:
            self._position = position
            self._velocity = Vector3.ZERO
            self._last_setpoint_time = None

    def hover(self) -> None:
        self.command_log.append("hover")
        self._velocity = Vector3.ZERO
        self._last_setpoint_time = None

    def emergency_stop(self) -> None:
        self.command_log.append("emergency_stop")
        self._is_armed = False
        self._drop_to_ground()

    def take_snapshot(self, time: float, dt: float) -> Snapshot:
        self._apply_setpoint_timeout()
        if self._is_flying:
            self._position = self._position + self._velocity * dt
        self._publish_state()
        return self._telemetry.snapshot(time, dt)

    # --- Internals --------------------------------------------------------------

    def _apply_setpoint_timeout(self) -> None:
        if self._last_setpoint_time is None:
            return
        silence = self._clock.now() - self._last_setpoint_time
        if silence > SETPOINT_CUT_MOTORS_AFTER:
            self._drop_to_ground()
        elif silence > SETPOINT_STOP_FOLLOWING_AFTER:
            self._velocity = Vector3.ZERO

    def _drop_to_ground(self) -> None:
        self._is_flying = False
        self._position = Vector3(self._position.x, self._position.y, 0.0)
        self._velocity = Vector3.ZERO
        self._last_setpoint_time = None

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
