# pyright: basic
# Basic mode because cflib has no type hints (ADR-0004). Everything this module
# exposes is fully typed; the looseness stays inside this file.
"""The Crazyflie adapter: implements the drone interface on a real Crazyflie.

NOT YET RUN ON HARDWARE. Written before the drone arrived, as a deliberate
exception for learning (ADR-0010), from the installed cflib source and
docs/cflib-primer.md. Its first real test is field-test stage 0 (bench,
propellers off). Assumptions that need checking there are marked VERIFY.

How the interface maps onto cflib:
- Telemetry: log blocks stream into the shared TelemetryBuffer, converted to
  SI units. Position, velocity and drone status share one block, so they come
  from the same moment (ADR-0021).
- Steering mode (set_velocity): low-level world-frame velocity setpoints.
- Fast mode, take-off, landing, hover: the high-level commander, which plans
  and flies trajectories on the drone.
"""

import logging
from collections.abc import Callable
from enum import Enum

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.supervisor import (
    BIT_IS_ARMED,
    BIT_IS_CRASHED,
    BIT_IS_FLYING,
    BIT_IS_TUMBLED,
)
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.utils.reset_estimator import reset_estimator

from crazyflie_behavior.drone.crazyflie.conversions import (
    drone_time_from_timestamp,
    move_duration,
    range_reading_from_mm,
    yaw_rate_deg_per_s,
)
from crazyflie_behavior.drone.crazyflie.time_limit import run_with_time_limit
from crazyflie_behavior.drone.crazyflie.touchdown import (
    FINAL_DESCENT_SPEED,
    HEIGHT_IF_UNKNOWN,
    TouchdownDetector,
    final_descent_deadline,
)
from crazyflie_behavior.drone.interface import DroneInterface
from crazyflie_behavior.drone.telemetry_buffer import TelemetryBuffer
from crazyflie_behavior.geometry import Vector3
from crazyflie_behavior.snapshot import DroneStatus, RangeDirection, RangeReading, Snapshot
from crazyflie_behavior.timing.clock import Clock

logger = logging.getLogger(__name__)

DEFAULT_URI = "radio://0/80/2M/E7E7E7E7E7"

DEFAULT_YAW_RAD = 0.0
"""The heading commands use unless told otherwise: world +x is where the drone faced at
take-off."""

# Telemetry periods (ADR-0023). The state block and the down range stream faster
# than the 20 Hz tick, so a snapshot's latest value is at most about 20 ms old.
STATE_PERIOD_MS = 20
"""Position, velocity and drone status. The estimate itself updates at 100 Hz."""
DOWN_RANGE_PERIOD_MS = 20
"""The Flow deck reads the down range every 25 ms."""
MULTIRANGER_PERIOD_MS = 100
"""The firmware reads the Multi-ranger every 100 ms (ADR-0022); faster only repeats."""
BATTERY_PERIOD_MS = 1000

# --- PLACEHOLDERS, NOT DECISIONS ---------------------------------------------
# Flight parameters wait on speed envelopes (ADR-0005) and the safety layer.
# These values just let the adapter run.
VERTICAL_SPEED = 0.3
"""Meters per second, for take-off and landing."""
HOVER_SETTLE_DURATION = 1.0
"""Seconds to settle into a hover."""
MIN_MOVE_DURATION = 0.5
"""Seconds. The shortest move ever requested from the high-level commander."""
TOUCHDOWN_POLL_PERIOD = 0.05
"""Seconds between touchdown checks while landing at shutdown."""
# Time limits for connecting (ADR-0029). VERIFY at the bench, and measure (backlog #25).
LINK_TIME_LIMIT = 15.0
"""Seconds to open the link and get the drone's variable lists. A first connect,
with nothing cached, downloads more."""
PARAMETERS_TIME_LIMIT = 10.0
"""Seconds to read the parameter values."""
POSITION_ESTIMATE_TIME_LIMIT = 20.0
"""Seconds for the position estimate to settle. cflib waits for 10 steady readings
500 ms apart, so it takes at least 5 s."""
# ------------------------------------------------------------------------------

_MULTIRANGER_VARIABLES = {
    RangeDirection.FRONT: "range.front",
    RangeDirection.BACK: "range.back",
    RangeDirection.LEFT: "range.left",
    RangeDirection.RIGHT: "range.right",
    RangeDirection.UP: "range.up",
}
_DOWN_RANGE_VARIABLE = "range.zrange"  # on the Flow deck
_STATUS_VARIABLE = "supervisor.info"  # the supervisor's state bitfield
_POSITION_VARIABLES = ("stateEstimate.x", "stateEstimate.y", "stateEstimate.z")
_VELOCITY_VARIABLES = ("stateEstimate.vx", "stateEstimate.vy", "stateEstimate.vz")
_STATE_VARIABLES = (*_POSITION_VARIABLES, *_VELOCITY_VARIABLES, _STATUS_VARIABLE)
"""6 floats and a 2-byte bitfield: exactly a log block's 26-byte limit (ADR-0021)."""

type _LogData = dict[str, float]
"""One log sample: variable name to value, as cflib delivers it."""
type _LogCallback = Callable[[int, _LogData, LogConfig], None]
"""cflib's log callback signature: (timestamp in ms, data, the log block)."""

_drivers_initialized = False


class _LandingPhase(Enum):
    """Where a landing is (ADR-0012, ADR-0019)."""

    NOT_LANDING = "not_landing"
    """No landing under way."""
    PLANNED = "planned"
    """The high-level landing, planned from the height estimate, is under way."""
    FINAL_DESCENT = "final_descent"
    """The planned landing ended without confirmed touchdown: descending slowly."""


def _init_drivers_once() -> None:
    # cflib.crtp.init_drivers() appends to a global driver list on every call,
    # so a second call would register every driver twice.
    global _drivers_initialized
    if not _drivers_initialized:
        cflib.crtp.init_drivers()
        _drivers_initialized = True


def drone_status_from_bitfield(bitfield: int) -> DroneStatus:
    """Decode the supervisor's state bitfield (bit positions from cflib)."""

    def bit(position: int) -> bool:
        return bool((bitfield >> position) & 1)

    return DroneStatus(
        is_armed=bit(BIT_IS_ARMED),
        is_flying=bit(BIT_IS_FLYING),
        is_crashed=bit(BIT_IS_CRASHED),
        is_tumbled=bit(BIT_IS_TUMBLED),
    )


class CrazyflieAdapter(DroneInterface):
    """Drives a real Crazyflie over the Crazyradio."""

    def __init__(
        self, clock: Clock, uri: str = DEFAULT_URI, cache_directory: str = "./cache"
    ) -> None:
        self._clock = clock
        self._uri = uri
        self._cache_directory = cache_directory
        self._telemetry = TelemetryBuffer(clock)
        self._sync_crazyflie: SyncCrazyflie | None = None
        self._log_configs: list[LogConfig] = []
        self._is_streaming_velocity = False
        self._is_airborne = False
        self._landing_phase = _LandingPhase.NOT_LANDING
        self._landing_finishes_at = 0.0
        """When the planned landing should be over. Meaningful while PLANNED."""
        self._final_descent_deadline = 0.0
        """When the final descent must be over. Meaningful while FINAL_DESCENT."""
        self._touchdown_detector = TouchdownDetector()
        self._last_drone_time: float | None = None

    # --- Connection ---------------------------------------------------------

    def connect(self) -> None:
        _init_drivers_once()
        self._last_drone_time = None  # a new session: the drone may have rebooted
        sync_crazyflie = SyncCrazyflie(self._uri, cf=Crazyflie(rw_cache=self._cache_directory))
        self._sync_crazyflie = sync_crazyflie  # tracked from the start, so cleanup always finds it
        try:
            # cflib's blocking steps each get a time limit, waited for in short
            # slices so Ctrl+C gets through, even on Windows (ADR-0029).
            run_with_time_limit(
                "Opening the link",
                sync_crazyflie.open_link,  # raises if it can't connect
                LINK_TIME_LIMIT,
                "Check the Crazyflie is switched on, charged and in range.",
                self._clock,
                # Stop a connection still under way. When connecting fails on its
                # own, cflib closes the link itself.
                on_abandon=sync_crazyflie.cf.close_link,
            )
            run_with_time_limit(
                "Reading the parameters",
                sync_crazyflie.wait_for_params,
                PARAMETERS_TIME_LIMIT,
                "The link may have dropped: check the Crazyflie is still switched on.",
                self._clock,
            )
            if not self._deck_attached("deck.bcFlow2", "deck.bcFlow"):  # Flow deck v2 or v1
                raise RuntimeError("Flow deck not detected: autonomous flight needs it.")
            run_with_time_limit(
                "Settling the position estimate",
                lambda: reset_estimator(sync_crazyflie),
                POSITION_ESTIMATE_TIME_LIMIT,
                "Check the Flow deck can see the floor (enough light and texture) "
                "and that the drone is sitting still.",
                self._clock,
            )
            self._start_logging(has_multiranger=self._deck_attached("deck.bcMultiranger"))
        except BaseException:
            self._close_link()
            raise

    def disconnect(self) -> None:
        if self._sync_crazyflie is None:
            return
        # cflib's close_link() sends a zero-thrust setpoint, which would drop a
        # flying drone. Land first and wait until the motors are stopped:
        # blocking is fine at shutdown.
        try:
            if self._is_airborne:
                self._land_and_wait_for_touchdown()
        finally:
            # Clean up even if landing failed, e.g. because the link dropped.
            self._shut_down_link()

    # --- Commands -----------------------------------------------------------

    def arm(self) -> None:
        self._crazyflie.supervisor.send_arming_request(True)

    def disarm(self) -> None:
        self._stop_motors()
        self._crazyflie.supervisor.send_arming_request(False)

    def take_off(self, height: float) -> None:
        if height <= 0.0:
            raise ValueError(f"Take-off height must be positive: {height}")
        self._cancel_landing()
        self._release_velocity_streaming()
        current_height = self._latest_height(if_unknown=0.0)
        duration = move_duration(height - current_height, VERTICAL_SPEED, MIN_MOVE_DURATION)
        self._crazyflie.high_level_commander.takeoff(height, duration, yaw=DEFAULT_YAW_RAD)
        self._is_airborne = True

    def land(self) -> None:
        self._start_landing()

    def set_velocity(self, velocity: Vector3, yaw_rate_rad_per_s: float = 0.0) -> None:
        self._cancel_landing()
        self._crazyflie.commander.send_velocity_world_setpoint(
            velocity.x, velocity.y, velocity.z, yaw_rate_deg_per_s(yaw_rate_rad_per_s)
        )
        self._is_streaming_velocity = True

    def move_to(self, position: Vector3, duration: float) -> None:
        if duration <= 0.0:
            raise ValueError(f"Move duration must be positive: {duration}")
        self._cancel_landing()
        self._release_velocity_streaming()
        self._crazyflie.high_level_commander.go_to(
            position.x,
            position.y,
            position.z,
            DEFAULT_YAW_RAD,
            max(duration, MIN_MOVE_DURATION),
        )

    def hover(self) -> None:
        self._cancel_landing()
        self._release_velocity_streaming()
        commander = self._crazyflie.high_level_commander
        latest = self._telemetry.latest_position_estimate()
        if latest is None:
            # No estimate yet: hold relative to the commander's own position.
            commander.go_to(0.0, 0.0, 0.0, DEFAULT_YAW_RAD, HOVER_SETTLE_DURATION, relative=True)
        else:
            # VERIFY: after velocity streaming, the high-level commander starts
            # this trajectory from the drone's current state, not a stale one.
            here = latest.value
            commander.go_to(here.x, here.y, here.z, DEFAULT_YAW_RAD, HOVER_SETTLE_DURATION)

    def emergency_stop(self) -> None:
        self._crazyflie.supervisor.send_emergency_stop()
        self._is_airborne = False
        self._is_streaming_velocity = False
        self._cancel_landing()

    def take_snapshot(self, time: float, dt: float) -> Snapshot:
        snapshot = self._telemetry.snapshot(time, dt)
        self._finish_landing(snapshot)
        return snapshot

    # --- Internals ----------------------------------------------------------

    @property
    def _crazyflie(self) -> Crazyflie:
        if self._sync_crazyflie is None:
            raise RuntimeError("Not connected: call connect() first.")
        return self._sync_crazyflie.cf

    def _close_link(self) -> None:
        if self._sync_crazyflie is not None:
            self._sync_crazyflie.close_link()
            self._sync_crazyflie = None
        self._log_configs.clear()  # they belonged to that link

    def _deck_attached(self, *parameters: str) -> bool:
        """True if any of the deck parameters says the deck is attached."""
        for parameter in parameters:
            try:
                if int(self._crazyflie.param.get_value(parameter)) == 1:
                    return True
            except KeyError:
                pass  # this firmware doesn't know the parameter: not attached
        return False

    def _latest_height(self, if_unknown: float) -> float:
        latest = self._telemetry.latest_position_estimate()
        return if_unknown if latest is None else latest.value.z

    def _release_velocity_streaming(self) -> None:
        # Hand control from low-level setpoints back to the high-level
        # commander, as cflib's MotionCommander does before landing.
        if self._is_streaming_velocity:
            self._crazyflie.commander.send_notify_setpoint_stop()
            self._is_streaming_velocity = False

    def _stop_motors(self) -> None:
        if self._is_streaming_velocity:
            self._crazyflie.commander.send_stop_setpoint()
            self._is_streaming_velocity = False
        self._crazyflie.high_level_commander.stop()  # stops the trajectory and the motors
        self._is_airborne = False
        self._cancel_landing()

    def _shut_down_link(self) -> None:
        for log_config in self._log_configs:
            log_config.stop()
        self._close_link()

    # --- Landing (ADR-0012, ADR-0019) ----------------------------------------

    def _start_landing(self) -> float:
        """Start descending to the ground. Returns when the descent should be done."""
        self._release_velocity_streaming()
        current_height = self._latest_height(if_unknown=HEIGHT_IF_UNKNOWN)
        duration = move_duration(current_height, VERTICAL_SPEED, MIN_MOVE_DURATION)
        self._crazyflie.high_level_commander.land(0.0, duration, yaw=DEFAULT_YAW_RAD)
        # The high-level commander keeps the motors running after it lands;
        # they're stopped once touchdown is confirmed.
        self._landing_finishes_at = self._clock.now() + duration
        self._landing_phase = _LandingPhase.PLANNED
        self._touchdown_detector = TouchdownDetector()
        return self._landing_finishes_at

    def _cancel_landing(self) -> None:
        self._landing_phase = _LandingPhase.NOT_LANDING

    def _finish_landing(self, snapshot: Snapshot) -> None:
        # Stop the motors only once touchdown is confirmed, never just because
        # the planned landing time is up: the plan may have used a stale height.
        # Until then, keep descending slowly (the final descent), and stop the
        # motors when its time limit says the drone must be on the floor.
        if self._landing_phase is _LandingPhase.NOT_LANDING:
            return
        now = self._clock.now()
        self._touchdown_detector.observe(snapshot, now)
        match self._landing_phase:
            case _LandingPhase.PLANNED:
                if now < self._landing_finishes_at:
                    return
                if self._touchdown_detector.touchdown_confirmed(now):
                    self._stop_motors()
                else:
                    self._start_final_descent(now)
            case _LandingPhase.FINAL_DESCENT:
                if self._touchdown_detector.touchdown_confirmed(now):
                    self._stop_motors()
                elif now >= self._final_descent_deadline:
                    logger.warning(
                        "Touchdown never confirmed by the down range; the final descent's "
                        "time limit is up, so the drone must be on the floor. Stopping the motors."
                    )
                    self._stop_motors()
            case _LandingPhase.NOT_LANDING:
                pass  # handled by the early return above

    def _start_final_descent(self, now: float) -> None:
        deadline = final_descent_deadline(now, self._touchdown_detector.highest_recent_distance())
        self._final_descent_deadline = deadline
        self._landing_phase = _LandingPhase.FINAL_DESCENT
        logger.warning("Landing time is up but touchdown isn't confirmed; descending slowly.")
        # One high-level move straight down at FINAL_DESCENT_SPEED until the
        # deadline, past the floor if need be. Unlike streamed setpoints, it
        # keeps going if ticks stop (ADR-0011). VERIFY: a relative go_to is
        # accepted after the high-level landing has finished.
        duration = deadline - now
        self._crazyflie.high_level_commander.go_to(
            0.0,
            0.0,
            -FINAL_DESCENT_SPEED * duration,
            DEFAULT_YAW_RAD,
            duration,
            relative=True,
            linear=True,
        )

    def _land_and_wait_for_touchdown(self) -> None:
        """Land, or finish a landing already under way, and block until the motors are stopped."""
        if self._landing_phase is _LandingPhase.NOT_LANDING:
            self._clock.sleep_until(self._start_landing())
        while self._landing_phase is not _LandingPhase.NOT_LANDING:
            self._finish_landing(self._telemetry.snapshot(self._clock.now(), 0.0))
            if self._landing_phase is not _LandingPhase.NOT_LANDING:
                self._clock.sleep_until(self._clock.now() + TOUCHDOWN_POLL_PERIOD)

    # --- Telemetry ----------------------------------------------------------

    def _start_logging(self, has_multiranger: bool) -> None:
        self._add_log_block("state", STATE_PERIOD_MS, list(_STATE_VARIABLES), self._on_state)
        self._add_log_block("battery", BATTERY_PERIOD_MS, ["pm.vbat"], self._on_battery)
        self._add_log_block(
            "down", DOWN_RANGE_PERIOD_MS, [_DOWN_RANGE_VARIABLE], self._on_down_range
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

    def _add_log_block(
        self, name: str, period_ms: int, variables: list[str], on_data: _LogCallback
    ) -> None:
        log_config = LogConfig(name=name, period_in_ms=period_ms)
        for variable in variables:
            log_config.add_variable(variable)  # fetched as the type the drone stores
        try:
            self._crazyflie.log.add_config(log_config)
        except KeyError as error:
            raise RuntimeError(
                f"The drone's firmware doesn't log a variable this adapter needs ({error}). "
                "Update the firmware."
            ) from error
        log_config.data_received_cb.add_callback(on_data)
        log_config.start()
        self._log_configs.append(log_config)

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
        status = drone_status_from_bitfield(int(data[_STATUS_VARIABLE]))
        self._telemetry.write_estimates_and_status(position, velocity, status, drone_time)

    def _on_battery(self, timestamp: int, data: _LogData, log_config: LogConfig) -> None:
        self._telemetry.write_battery_voltage(data["pm.vbat"], self._drone_time(timestamp))

    def _on_down_range(self, timestamp: int, data: _LogData, log_config: LogConfig) -> None:
        reading = range_reading_from_mm(int(data[_DOWN_RANGE_VARIABLE]))
        self._telemetry.write_range_readings(
            {RangeDirection.DOWN: reading}, self._drone_time(timestamp)
        )

    def _on_multiranger(self, timestamp: int, data: _LogData, log_config: LogConfig) -> None:
        readings = {
            direction: range_reading_from_mm(int(data[variable]))
            for direction, variable in _MULTIRANGER_VARIABLES.items()
        }
        self._telemetry.write_range_readings(readings, self._drone_time(timestamp))
