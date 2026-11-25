# pyright: basic
# Basic mode because cflib has no type hints (ADR-0004). Everything this module
# exposes is fully typed; the looseness stays inside this file.
"""The Crazyflie adapter's log blocks, and their callbacks that write the telemetry buffer (ADR-0093).

Owns the telemetry buffer: the adapter and its other parts read `telemetry` on every call and keep no reference
to it.
"""

import logging
from collections.abc import Callable

from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.supervisor import (
    BIT_CAN_BE_ARMED,
    BIT_IS_ARMED,
    BIT_IS_CRASHED,
    BIT_IS_FLYING,
    BIT_IS_LOCKED,
    BIT_IS_TUMBLED,
)

from crazyflie_behavior.drone.crazyflie.conversions import (
    battery_voltage_from_mv,
    drone_time_from_timestamp,
    range_reading_from_mm,
    velocity_uncertainty_from_variances,
)
from crazyflie_behavior.drone.telemetry_buffer import TelemetryBuffer
from crazyflie_behavior.geometry import Vector3
from crazyflie_behavior.snapshot import DroneStatus, RangeDirection, RangeReading, Stamped
from crazyflie_behavior.timing.clock import Clock

logger = logging.getLogger(__name__)

# Telemetry periods (ADR-0023). The state block and the down range stream faster
# than the 20 Hz tick, so a snapshot's latest value is at most about 20 ms old.
STATE_PERIOD_MS = 20
"""Position, velocity and drone status. The estimate itself updates at 100 Hz (ADR-0023)."""
DOWN_RANGE_PERIOD_MS = 20
"""The Flow deck reads the down range every 25 ms (ADR-0023)."""
MULTIRANGER_PERIOD_MS = 100
"""The firmware reads the Multi-ranger every 100 ms (ADR-0022); faster only repeats."""
BATTERY_PERIOD_MS = 1000
DIAGNOSTIC_PERIOD_MS = 100
"""Attitude, motor power and flow quality, for the debug log only (ADR-0050)."""
CONTROLLER_PERIOD_MS = 100
"""The controller block, for the debug log only (ADR-0063)."""
TAKE_OFF_PERIOD_MS = 10
"""The take-off block, for the debug log only (ADR-0063)."""
TAKE_OFF_BLOCK_DURATION = 2.0
"""Seconds the take-off block runs from the end of connect and from each take-off (ADR-0065)."""

_MULTIRANGER_VARIABLES = {
    RangeDirection.FRONT: "range.front",
    RangeDirection.BACK: "range.back",
    RangeDirection.LEFT: "range.left",
    RangeDirection.RIGHT: "range.right",
    RangeDirection.UP: "range.up",
}
_DOWN_RANGE_VARIABLE = "range.zrange"  # on the Flow deck
_VELOCITY_VARIANCE_VARIABLES = ("kalman.varPX", "kalman.varPY")
"""m²/s²: the velocity variances in the drone's forward and sideways directions (ADR-0054)."""
_DOWN_VARIABLES = (_DOWN_RANGE_VARIABLE, *_VELOCITY_VARIANCE_VARIABLES)
"""A uint16 and 2 floats: 10 bytes of a log block's 26 (ADR-0054)."""
_IMAGE_QUALITY_VARIABLE = "motion.squal"
# The diagnostic block (ADR-0050, ADR-0053): 3 floats, 4 uint16, a uint8 and two uint16, 25 bytes.
_ATTITUDE_VARIABLES = ("stateEstimate.roll", "stateEstimate.pitch", "stateEstimate.yaw")
"""Degrees. The firmware logs pitch with the legacy inverted sign."""
_MOTOR_VARIABLES = ("motor.m1", "motor.m2", "motor.m3", "motor.m4")
"""Motor power, 0-65535."""
_FLOW_QUALITY_VARIABLES = (_IMAGE_QUALITY_VARIABLE, "motion.shutter")
"""Surface features seen, and shutter time (longer in low light)."""
_DIAGNOSTIC_BATTERY_VARIABLE = "pm.vbatMV"
"""Millivolts: the battery voltage, faster than the battery block's once a second."""
_DIAGNOSTIC_VARIABLES = (
    *_ATTITUDE_VARIABLES,
    *_MOTOR_VARIABLES,
    *_FLOW_QUALITY_VARIABLES,
    _DIAGNOSTIC_BATTERY_VARIABLE,
)
# The controller block (ADR-0063): 10 floats fetched as FP16, 20 bytes. Each pair is roll, then pitch,
# with the signs the firmware logs.
_CONTROLLER_VARIABLES = (
    "pid_attitude.roll_outI",  # the attitude controllers' integrals: degrees per second of rate setpoint
    "pid_attitude.pitch_outI",
    "pid_rate.roll_outI",  # the rate controllers' integrals, in command units
    "pid_rate.pitch_outI",
    "controller.cmd_roll",  # the controller's commands: 16-bit, signed
    "controller.cmd_pitch",
    "controller.roll",  # the attitude setpoint: degrees
    "controller.pitch",
    "gyro.x",  # degrees per second
    "gyro.y",
)
_CONTROLLER_FETCH_AS = "FP16"
"""2 bytes a variable, about 3 significant digits (ADR-0063)."""
# The take-off block (ADR-0063): 3 floats and 4 uint16, 20 bytes.
_TAKE_OFF_VARIABLES = (*_ATTITUDE_VARIABLES, *_MOTOR_VARIABLES)
_STATUS_VARIABLE = "supervisor.info"  # the supervisor's state bitfield
_POSITION_VARIABLES = ("stateEstimate.x", "stateEstimate.y", "stateEstimate.z")
_VELOCITY_VARIABLES = ("stateEstimate.vx", "stateEstimate.vy", "stateEstimate.vz")
_STATE_VARIABLES = (*_POSITION_VARIABLES, *_VELOCITY_VARIABLES, _STATUS_VARIABLE)
"""6 floats and a 2-byte bitfield: exactly a log block's 26-byte limit (ADR-0021)."""

type _LogData = dict[str, float]
"""One log sample: variable name to value, as cflib delivers it."""
type _LogCallback = Callable[[int, _LogData, LogConfig], None]
"""cflib's log callback signature: (timestamp in ms, data, the log block)."""


def drone_status_from_bitfield(bitfield: int) -> DroneStatus:
    """Decode the supervisor's state bitfield (bit positions from cflib)."""

    def bit(position: int) -> bool:
        return bool((bitfield >> position) & 1)

    return DroneStatus(
        is_armed=bit(BIT_IS_ARMED),
        is_flying=bit(BIT_IS_FLYING),
        is_crashed=bit(BIT_IS_CRASHED),
        is_tumbled=bit(BIT_IS_TUMBLED),
        can_arm=bit(BIT_CAN_BE_ARMED),
        is_locked=bit(BIT_IS_LOCKED),
    )


class LogBlocks:
    """The log blocks, and their callbacks that write the telemetry buffer on cflib's receive thread (ADR-0093).

    Looks up the drone on every call: `connect()` opens the link after building this.
    """

    def __init__(self, clock: Clock, current_crazyflie: Callable[[], Crazyflie], *, take_over_flight: bool) -> None:
        """`take_over_flight`: skip the diagnostic and controller blocks (ADR-0067)."""
        self._clock = clock
        self._current_crazyflie = current_crazyflie
        self._take_over_flight = take_over_flight
        self._telemetry = TelemetryBuffer(clock)
        self._log_configs: list[LogConfig] = []
        self._last_drone_time: float | None = None
        self._dropped_state_count = 0
        """State packets in a row with an estimate that isn't finite."""
        self._latest_status_bitfield: int | None = None
        """The supervisor bitfield of the latest state packet, for bits `DroneStatus`
        doesn't carry (auto-arming, ADR-0037). Written on cflib's receive thread."""
        self._latest_image_quality: Stamped[int] | None = None
        """The latest image quality (`motion.squal`), for the low-light warning (ADR-0054).
        Written on cflib's receive thread."""
        self._take_off_block: LogConfig | None = None
        """Created last in connect with `take_off_log`, for this link."""
        self._is_take_off_block_running = False
        """A start or create was sent for the take-off block, and no stop since."""
        self._take_off_block_stops_at = 0.0
        """When the take-off block's run is over. Meaningful while it runs."""

    @property
    def telemetry(self) -> TelemetryBuffer:
        """The telemetry buffer the callbacks write now. Read it on every use: `replace_telemetry_buffer()`
        replaces it."""
        return self._telemetry

    @property
    def latest_status_bitfield(self) -> int | None:
        return self._latest_status_bitfield

    @property
    def latest_image_quality(self) -> Stamped[int] | None:
        return self._latest_image_quality

    def replace_telemetry_buffer(self) -> None:
        """Start a new, empty telemetry buffer: the callbacks write the new one from their next sample."""
        self._telemetry = TelemetryBuffer(self._clock)

    def start_state_logging(self) -> None:
        self._add_log_block("state", STATE_PERIOD_MS, list(_STATE_VARIABLES), self._on_state)

    def start_remaining_logging(self, has_multiranger: bool) -> None:
        self._add_log_block("battery", BATTERY_PERIOD_MS, ["pm.vbat"], self._on_battery)
        self._add_log_block("down", DOWN_RANGE_PERIOD_MS, list(_DOWN_VARIABLES), self._on_down_range)
        # A take-over connects to a drone that may be flying: a missing debug-only variable mustn't fail it (ADR-0067).
        if not self._take_over_flight:
            self._add_log_block("diagnostic", DIAGNOSTIC_PERIOD_MS, list(_DIAGNOSTIC_VARIABLES), self._on_diagnostic)
            self._add_log_block(
                "controller",
                CONTROLLER_PERIOD_MS,
                list(_CONTROLLER_VARIABLES),
                self._on_controller,
                fetch_as=_CONTROLLER_FETCH_AS,
            )
        if has_multiranger:
            self._add_log_block(
                "multiranger",
                MULTIRANGER_PERIOD_MS,
                list(_MULTIRANGER_VARIABLES.values()),
                self._on_multiranger,
            )
        else:
            # No Multi-ranger: say so explicitly. These directions are unknown,
            # never clear.
            self._telemetry.write_range_readings(
                dict.fromkeys(_MULTIRANGER_VARIABLES, RangeReading.invalid()), drone_time=None
            )

    def stop_log_blocks(self) -> None:
        for log_config in self._log_configs:
            log_config.stop()

    def forget_log_blocks(self) -> None:
        """Forget the log blocks and the take-off block's state: they belonged to the link just closed."""
        self._log_configs.clear()
        self._take_off_block = None
        self._is_take_off_block_running = False

    # The take-off block (ADR-0063, ADR-0065). Nothing waits for it. cflib sends one packet for each start
    # or stop, and sets `started` on its receive thread once the drone confirms a start.

    def create_take_off_block(self) -> None:
        """Its run counts from the create request: cflib starts it once the drone confirms the create."""
        self._take_off_block = self._add_log_block(
            "take_off", TAKE_OFF_PERIOD_MS, list(_TAKE_OFF_VARIABLES), self._on_take_off_block
        )
        self._is_take_off_block_running = True
        self._take_off_block_stops_at = self._clock.now() + TAKE_OFF_BLOCK_DURATION

    def run_take_off_block(self) -> None:
        """Run it from now: a start, or just a later stop for a run under way."""
        if self._take_off_block is None:
            return
        if not self._is_take_off_block_running:
            self._take_off_block.start()  # the drone kept the block from connect, so no create
            self._is_take_off_block_running = True
        self._take_off_block_stops_at = self._clock.now() + TAKE_OFF_BLOCK_DURATION

    def stop_take_off_block_once_its_run_is_over(self) -> None:
        """Only once the drone has confirmed its start, so the stop can't overtake cflib's start."""
        block = self._take_off_block
        if (
            block is not None
            and self._is_take_off_block_running
            and self._clock.now() >= self._take_off_block_stops_at
            and block.started
        ):
            self.stop_take_off_block()

    def stop_take_off_block(self) -> None:
        if self._take_off_block is not None and self._is_take_off_block_running:
            self._take_off_block.stop()
            self._is_take_off_block_running = False

    def _add_log_block(
        self, name: str, period_ms: int, variables: list[str], on_data: _LogCallback, fetch_as: str | None = None
    ) -> LogConfig:
        """Create and start a log block. `fetch_as`: the cflib type to fetch every variable as; by default,
        each comes as the type the drone stores."""
        log_config = LogConfig(name=name, period_in_ms=period_ms)
        for variable in variables:
            log_config.add_variable(variable, fetch_as)
        try:
            self._current_crazyflie().log.add_config(log_config)
        except KeyError as error:
            raise RuntimeError(
                f"The drone's firmware doesn't log a variable this adapter needs ({error}). Update the firmware."
            ) from error
        log_config.data_received_cb.add_callback(on_data)
        log_config.start()
        self._log_configs.append(log_config)
        return log_config

    # Log callbacks run on cflib's receive thread. Keep them tiny: convert and
    # write to the telemetry buffer, nothing else.

    def _drone_time(self, timestamp: int) -> float:
        # Every log callback runs on cflib's single receive thread, so this
        # state needs no lock.
        self._last_drone_time = drone_time_from_timestamp(timestamp, self._last_drone_time)
        return self._last_drone_time

    def _on_state(self, timestamp: int, data: _LogData, log_config: LogConfig) -> None:
        drone_time = self._drone_time(timestamp)
        position = Vector3(*(data[variable] for variable in _POSITION_VARIABLES))
        velocity = Vector3(*(data[variable] for variable in _VELOCITY_VARIABLES))
        bitfield = int(data[_STATUS_VARIABLE])
        self._latest_status_bitfield = bitfield
        status = drone_status_from_bitfield(bitfield)
        if position.is_finite() and velocity.is_finite():
            self._telemetry.write_estimates_and_status(position, velocity, status, drone_time)
            if self._dropped_state_count > 0:
                logger.info("Finite estimates are back after %d dropped state packets", self._dropped_state_count)
                self._dropped_state_count = 0
            return
        # An estimate that isn't finite is dropped, so any earlier finite one stays
        # and goes stale, and the safety pre-check fails on it (ADR-0030). The
        # drone's own estimate is then NaN, so it can't follow the failsafe's
        # landing either (ADR-0045, backlog #45).
        if position.is_finite():
            self._telemetry.write_position_estimate(position, drone_time)
        if velocity.is_finite():
            self._telemetry.write_velocity_estimate(velocity, drone_time)
        self._telemetry.write_drone_status(status, drone_time)
        if self._dropped_state_count == 0:
            logger.warning(
                "Dropped an estimate that isn't finite (position %s, velocity %s). Warned once per streak.",
                position,
                velocity,
            )
        self._dropped_state_count += 1

    def _on_battery(self, timestamp: int, data: _LogData, log_config: LogConfig) -> None:
        self._telemetry.write_battery_voltage(data["pm.vbat"], self._drone_time(timestamp))

    def _on_down_range(self, timestamp: int, data: _LogData, log_config: LogConfig) -> None:
        drone_time = self._drone_time(timestamp)
        reading = range_reading_from_mm(int(data[_DOWN_RANGE_VARIABLE]))
        self._telemetry.write_range_readings({RangeDirection.DOWN: reading}, drone_time)
        # NaN when a variance isn't finite: the safety layer counts it as missing (ADR-0054).
        variance_px, variance_py = (data[variable] for variable in _VELOCITY_VARIANCE_VARIABLES)
        self._telemetry.write_velocity_uncertainty(
            velocity_uncertainty_from_variances(variance_px, variance_py), drone_time
        )

    def _on_diagnostic(self, timestamp: int, data: _LogData, log_config: LogConfig) -> None:
        """One debug line, nothing in the telemetry buffer (ADR-0050)."""
        roll_deg, pitch_deg, yaw_deg = (data[variable] for variable in _ATTITUDE_VARIABLES)
        squal, shutter = (int(data[variable]) for variable in _FLOW_QUALITY_VARIABLES)
        drone_time = self._drone_time(timestamp)
        self._latest_image_quality = Stamped(squal, self._clock.now(), drone_time)
        battery_voltage = battery_voltage_from_mv(int(data[_DIAGNOSTIC_BATTERY_VARIABLE]))
        logger.debug(
            "Diagnostic: drone_time=%.3f roll_deg=%.2f pitch_deg=%.2f yaw_deg=%.2f motors=%s squal=%d shutter=%d "
            "battery_voltage=%.3f",
            drone_time,
            roll_deg,
            pitch_deg,
            yaw_deg,
            [int(data[variable]) for variable in _MOTOR_VARIABLES],
            squal,
            shutter,
            battery_voltage,
        )

    def _on_controller(self, timestamp: int, data: _LogData, log_config: LogConfig) -> None:
        """One debug line, nothing in the telemetry buffer (ADR-0063)."""
        logger.debug(
            "Controller block: drone_time=%.3f attitude_integral_deg_per_s=[%.4g, %.4g] rate_integral=[%.4g, %.4g] "
            "command=[%.4g, %.4g] attitude_setpoint_deg=[%.4g, %.4g] gyro_deg_per_s=[%.4g, %.4g]",
            self._drone_time(timestamp),
            *(data[variable] for variable in _CONTROLLER_VARIABLES),
        )

    def _on_take_off_block(self, timestamp: int, data: _LogData, log_config: LogConfig) -> None:
        """One debug line, nothing in the telemetry buffer (ADR-0063)."""
        roll_deg, pitch_deg, yaw_deg = (data[variable] for variable in _ATTITUDE_VARIABLES)
        logger.debug(
            "Take-off block: drone_time=%.3f roll_deg=%.2f pitch_deg=%.2f yaw_deg=%.2f motors=%s",
            self._drone_time(timestamp),
            roll_deg,
            pitch_deg,
            yaw_deg,
            [int(data[variable]) for variable in _MOTOR_VARIABLES],
        )

    def _on_multiranger(self, timestamp: int, data: _LogData, log_config: LogConfig) -> None:
        readings = {
            direction: range_reading_from_mm(int(data[variable]))
            for direction, variable in _MULTIRANGER_VARIABLES.items()
        }
        self._telemetry.write_range_readings(readings, self._drone_time(timestamp))
