"""The mock adapter: a simple fake drone for tests and development.

It answers commands instantly with no physics: `move_to` teleports, and
`set_velocity` moves the drone exactly. It writes its made-up telemetry
through the same `TelemetryBuffer` as every other adapter.

It mocks the Crazyflie adapter, so it uses that adapter's numbers for the
bad-flow zone (ADR-0048, ADR-0055). A take-off climbs level at its initial
climb speed (`LEVEL_VERTICAL_SPEED` unless set, ADR-0059) to the final descent height, then teleports to its
height. The mock's flow is perfect where it arrives, so the speed settles as
soon as it does: at `SETTLE_MIN_DOWN_RANGE` on a lit floor, giving the lowest
final descent height. A test can darken the floor with `set_dark_floor` (no
flow below a height) or cut the flow with `cut_flow`: the velocity uncertainty
is then high, and with no flow by `SETTLE_CAP_HEIGHT` the drone lands, as the
Crazyflie adapter does (ADR-0054). A landing teleports down to the final descent height, then descends level at
`LEVEL_VERTICAL_SPEED` to the floor. During those level parts it ignores every
command but land and the motor stops, as the Crazyflie adapter does (ADR-0056).

`update_take_off_and_landing` moves the fake drone by the snapshot's `dt`, for
every command, and streams every value again. So a snapshot shows the drone as
it was at the end of the previous tick (ADR-0055).

Like real hardware, it ignores commands it can't carry out (e.g. taking off
while disarmed) instead of raising; the outcome shows up in the snapshot.

Also like real hardware, it stops following velocity setpoints that stop
arriving (ADR-0011): a stream someone forgot to send every tick fails in tests
the way it would in the air.

The room is empty: every range reading but the down one is out of range
(clear) unless a test sets it with `set_range_reading`. The floor is flat at
height 0, so the down range reads the drone's height, never less than its
reading on the floor (ADR-0052). Like a real drone, it streams every value
again each tick, until a test makes it go quiet with `stop_telemetry`.
"""

import math

from crazyflie_behavior.drone.crazyflie.bad_flow_zone import (
    LEVEL_VERTICAL_SPEED,
    MAX_FINAL_DESCENT_HEIGHT,
    SETTLE_CAP_HEIGHT,
    SETTLE_MIN_DOWN_RANGE,
    check_initial_climb_speed,
    final_descent_height,
)
from crazyflie_behavior.drone.interface import DroneInterface
from crazyflie_behavior.drone.telemetry_buffer import TelemetryBuffer
from crazyflie_behavior.geometry import Vector3
from crazyflie_behavior.snapshot import DroneStatus, RangeDirection, RangeReading, Snapshot
from crazyflie_behavior.timing.clock import Clock

CHARGED_BATTERY_VOLTAGE = 4.0
"""Volts. A freshly charged Crazyflie battery reads a little above this."""

TAKEN_OVER_HEIGHT = 0.5
"""Meters. How high the mock drone hovers when a rescue landing takes over its flight."""

FLOOR_DOWN_RANGE = 0.02
"""Meters: the down range on the floor. The real drone read 0.019-0.024 m at rest (Bench, 2026-11-04)."""

VELOCITY_UNCERTAINTY_WITH_FLOW = 0.01
"""Meters per second: the velocity uncertainty while flow arrives. An estimate reset's value (ADR-0054)."""
VELOCITY_UNCERTAINTY_WITHOUT_FLOW = 0.5
"""Meters per second: the velocity uncertainty without flow, well over any threshold."""

# From the firmware source. VERIFY at the bench that the drone's firmware
# matches (ADR-0011).
SETPOINT_STOP_FOLLOWING_AFTER = 0.5
"""Seconds without a set_velocity before the drone stops following it."""
SETPOINT_CUT_MOTORS_AFTER = 2.0
"""Seconds without a setpoint (set_velocity, or a level part's update) before the motors are cut
and the drone drops."""


class MockAdapter(DroneInterface):
    """A fake drone that does exactly what it's told, instantly."""

    def __init__(
        self, clock: Clock, *, take_over_flight: bool = False, initial_climb_speed: float = LEVEL_VERTICAL_SPEED
    ) -> None:
        """`take_over_flight`: the rescue landing's setting (ADR-0038). `connect()` then finds the
        drone armed and hovering at `TAKEN_OVER_HEIGHT`, as if a program had been lost with it
        in the air, so the rescue landing has something to land.

        `initial_climb_speed`: meters per second, as the Crazyflie adapter's (ADR-0059). Raises
        ValueError outside the accepted range."""
        check_initial_climb_speed(initial_climb_speed)
        self._initial_climb_speed = initial_climb_speed
        self._clock = clock
        self._take_over_flight = take_over_flight
        self._telemetry = TelemetryBuffer(clock)
        # Names of the commands received, in order, for tests to check.
        self.command_log: list[str] = []
        self.tone_pitches: list[float] = []
        """Hertz: the pitch of each tone received, in order, for tests to check. The buzzer makes no sound."""
        self._is_connected = False
        self._is_armed = False
        self._is_flying = False
        self._position = Vector3.ZERO
        self._velocity = Vector3.ZERO
        # When the last set_velocity arrived; None when not in steering mode.
        self._last_setpoint_time: float | None = None
        self._climb_height: float | None = None
        """Meters: the take-off's height, during the initial climb."""
        self._is_settled = False
        """Whether this initial climb has reached its settle height."""
        self._is_in_final_descent = False
        self._final_descent_height = MAX_FINAL_DESCENT_HEIGHT
        """Meters: the lowest after its own take-off, the cap after a take-over (ADR-0056)."""
        self._last_level_setpoint_time: float | None = None
        """When the last level setpoint went out; None outside the level parts."""
        self._range_readings = dict.fromkeys(RangeDirection, RangeReading.out_of_range())
        self._is_down_range_set_by_test = False
        """Once a test sets the down range, it stays as set instead of following the height."""
        self._battery_voltage = CHARGED_BATTERY_VOLTAGE
        self._is_streaming = True
        self._dark_floor_height = 0.0
        """Meters: no flow below this height."""
        self._is_flow_cut = False

    # --- Test hooks: set the telemetry a test needs -----------------------------
    # A value set here arrives at once, so a test can set it and then stop the telemetry.

    def set_range_reading(self, direction: RangeDirection, reading: RangeReading) -> None:
        """Fixes one reading from now on. For the down range, that replaces following the height."""
        self._range_readings[direction] = reading
        if direction is RangeDirection.DOWN:
            self._is_down_range_set_by_test = True
        if self._is_streaming:
            self._telemetry.write_range_readings({direction: reading}, self._clock.now())

    def set_battery_voltage(self, voltage: float) -> None:
        self._battery_voltage = voltage
        if self._is_streaming:
            self._telemetry.write_battery_voltage(voltage, self._clock.now())

    def set_dark_floor(self, height: float) -> None:
        """No flow below `height` meters from now on, as over a dark floor (ADR-0054)."""
        self._dark_floor_height = height
        self._publish_state()

    def cut_flow(self) -> None:
        """A fault: no flow at any height from now on, so the velocity uncertainty is high (ADR-0054)."""
        self._is_flow_cut = True
        self._publish_state()

    def stop_telemetry(self) -> None:
        """Stop streaming, as if the link went quiet: every value goes stale from now on."""
        self._is_streaming = False

    # --- DroneInterface ---------------------------------------------------------

    def connect(self) -> None:
        self.command_log.append("connect")
        self._is_connected = True
        self._final_descent_height = MAX_FINAL_DESCENT_HEIGHT  # a new session knows no settle height
        if self._take_over_flight:
            self._is_armed = True
            self._is_flying = True
            self._position = Vector3(self._position.x, self._position.y, TAKEN_OVER_HEIGHT)
        self._publish_state()

    def disconnect(self) -> None:
        self.command_log.append("disconnect")
        if self._is_flying:
            self.land()
            self._drop_to_ground()  # the Crazyflie adapter waits for touchdown; the mock lands at once
            self._publish_state()  # the last telemetry, so a test can see where the drone ended up
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
        if height <= MAX_FINAL_DESCENT_HEIGHT:
            cap = MAX_FINAL_DESCENT_HEIGHT
            raise ValueError(f"Take-off height must be above the final descent height's cap, {cap:g} m: {height}")
        if self._is_armed and not self._is_flying:
            self._is_flying = True
            self._final_descent_height = MAX_FINAL_DESCENT_HEIGHT  # until the settle height is known
            self._is_settled = False
            self._climb_height = height
            self._start_level_part(self._initial_climb_speed)

    def land(self) -> None:
        self.command_log.append("land")
        if not self._is_flying:
            self._drop_to_ground()
        elif not self._is_in_final_descent:
            self._start_final_descent()

    def set_velocity(self, velocity: Vector3, yaw_rate_rad_per_s: float = 0.0) -> None:
        self.command_log.append("set_velocity")
        # Yaw is held fixed (ADR-0008), so the mock ignores the yaw rate.
        if self._is_flying and not self._is_in_level_part():
            self._velocity = velocity
            self._last_setpoint_time = self._clock.now()

    def move_to(self, position: Vector3, duration: float) -> None:
        self.command_log.append("move_to")
        if duration <= 0.0:
            raise ValueError(f"Move duration must be positive: {duration}")
        if self._is_flying and not self._is_in_level_part():
            self._position = position
            self._velocity = Vector3.ZERO
            self._last_setpoint_time = None

    def hover(self) -> None:
        self.command_log.append("hover")
        if not self._is_in_level_part():
            self._velocity = Vector3.ZERO
            self._last_setpoint_time = None

    def emergency_stop(self) -> None:
        self.command_log.append("emergency_stop")
        self._is_armed = False
        self._drop_to_ground()

    def reset_estimate(self) -> None:
        """Ignored while flying, as the Crazyflie adapter ignores it while the drone may be flying."""
        self.command_log.append("reset_estimate")
        if not self._is_flying:
            self._position = Vector3(0.0, 0.0, self._position.z)
            self._velocity = Vector3.ZERO
            self._publish_state()

    def chirp(self) -> None:
        self.command_log.append("chirp")

    def play_tone(self, pitch: float) -> None:
        self.command_log.append("play_tone")
        if not (math.isfinite(pitch) and pitch > 0.0):
            raise ValueError(f"Tone pitch must be positive: {pitch}")
        self.tone_pitches.append(pitch)

    def silence(self) -> None:
        self.command_log.append("silence")

    def take_snapshot(self, dt: float) -> Snapshot:
        return self._telemetry.snapshot(
            dt, is_in_initial_climb=self._climb_height is not None, may_be_flying=self._is_flying
        )

    def update_take_off_and_landing(self, snapshot: Snapshot) -> None:
        """Also moves the fake drone by the snapshot's `dt`, for every command, and streams every value (ADR-0055)."""
        self._apply_setpoint_timeout()
        if self._is_flying:
            self._position = self._position + self._velocity * snapshot.dt
        if self._climb_height is not None and not self._is_settled:
            settle_height = self._settle_height()
            # Kept for the rest of the climb once reached, as the Crazyflie adapter does.
            if settle_height is not None and self._position.z >= settle_height:
                self._is_settled = True
                self._final_descent_height = final_descent_height(settle_height)
        if self._climb_height is not None and not self._is_settled and self._position.z > SETTLE_CAP_HEIGHT:
            self._start_final_descent()  # no flow by the cap: the drone lands (ADR-0054)
        elif self._climb_height is not None and self._position.z >= self._final_descent_height:
            # The initial climb is over: the high-level climb to the height, teleported.
            self._position = Vector3(self._position.x, self._position.y, self._climb_height)
            self._velocity = Vector3.ZERO
            self._climb_height = None
            self._last_level_setpoint_time = None
        elif self._is_in_final_descent and self._position.z <= 0.0:
            self._drop_to_ground()  # touchdown: the motors stop
        elif self._is_in_level_part():
            self._last_level_setpoint_time = self._clock.now()  # this tick's level setpoint
        self._publish_state()

    # --- Internals --------------------------------------------------------------

    def _start_final_descent(self) -> None:
        # The landing approach, teleported. During the initial climb the drone is still below
        # the final descent height, so the final descent starts from where it is (ADR-0049).
        self._position = Vector3(self._position.x, self._position.y, min(self._position.z, self._final_descent_height))
        self._climb_height = None
        self._is_in_final_descent = True
        self._start_level_part(-LEVEL_VERTICAL_SPEED)

    def _has_flow(self) -> bool:
        return not self._is_flow_cut and self._position.z >= self._dark_floor_height

    def _settle_height(self) -> float | None:
        """Meters: where flow arrives above SETTLE_MIN_DOWN_RANGE, or None if not by the cap."""
        if self._is_flow_cut:
            return None
        settle_height = max(self._dark_floor_height, SETTLE_MIN_DOWN_RANGE)
        return settle_height if settle_height <= SETTLE_CAP_HEIGHT else None

    def _is_in_level_part(self) -> bool:
        return self._climb_height is not None or self._is_in_final_descent

    def _start_level_part(self, vertical_speed: float) -> None:
        self._velocity = Vector3(0.0, 0.0, vertical_speed)
        self._last_setpoint_time = None
        self._last_level_setpoint_time = self._clock.now()

    def _apply_setpoint_timeout(self) -> None:
        now = self._clock.now()
        if self._last_level_setpoint_time is not None:
            # A level part's setpoint keeps its vertical speed when the drone levels out after 0.5 s.
            if now - self._last_level_setpoint_time > SETPOINT_CUT_MOTORS_AFTER:
                self._drop_to_ground()
            return
        if self._last_setpoint_time is None:
            return
        silence = now - self._last_setpoint_time
        if silence > SETPOINT_CUT_MOTORS_AFTER:
            self._drop_to_ground()
        elif silence > SETPOINT_STOP_FOLLOWING_AFTER:
            self._velocity = Vector3.ZERO

    def _drop_to_ground(self) -> None:
        self._is_flying = False
        self._position = Vector3(self._position.x, self._position.y, 0.0)
        self._velocity = Vector3.ZERO
        self._last_setpoint_time = None
        self._climb_height = None
        self._is_in_final_descent = False
        self._last_level_setpoint_time = None

    def _publish_state(self) -> None:
        if not self._is_streaming:
            return
        drone_time = self._clock.now()
        if not self._is_down_range_set_by_test:
            down_range = max(self._position.z, FLOOR_DOWN_RANGE)
            self._range_readings[RangeDirection.DOWN] = RangeReading.at_distance(down_range)
        self._telemetry.write_range_readings(self._range_readings, drone_time)
        self._telemetry.write_battery_voltage(self._battery_voltage, drone_time)
        self._telemetry.write_position_estimate(self._position, drone_time)
        self._telemetry.write_velocity_estimate(self._velocity, drone_time)
        uncertainty = VELOCITY_UNCERTAINTY_WITH_FLOW if self._has_flow() else VELOCITY_UNCERTAINTY_WITHOUT_FLOW
        self._telemetry.write_velocity_uncertainty(uncertainty, drone_time)
        self._telemetry.write_drone_status(
            DroneStatus(
                is_armed=self._is_armed,
                is_flying=self._is_flying,
                is_crashed=False,
                is_tumbled=False,
                can_arm=self._is_connected and not self._is_armed and not self._is_flying,
                is_locked=False,  # the mock never locks (ADR-0058)
            ),
            drone_time,
        )
