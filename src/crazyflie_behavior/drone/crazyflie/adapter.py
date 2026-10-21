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
  SI units. Drone status is polled from the supervisor on its own thread.
- Steering mode (set_velocity): low-level world-frame velocity setpoints.
- Fast mode, take-off, landing, hover: the high-level commander, which plans
  and flies trajectories on the drone.
"""

import threading
from collections.abc import Callable

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
from crazyflie_behavior.drone.interface import DroneInterface
from crazyflie_behavior.drone.telemetry_buffer import TelemetryBuffer
from crazyflie_behavior.geometry import Vector3
from crazyflie_behavior.snapshot import DroneStatus, RangeDirection, RangeReading, Snapshot
from crazyflie_behavior.timing.clock import Clock

DEFAULT_URI = "radio://0/80/2M/E7E7E7E7E7"

FIXED_YAW_RAD = 0.0
"""Yaw is held fixed (ADR-0008): the world's +x is where the drone faced at take-off."""

# --- PLACEHOLDERS, NOT DECISIONS ---------------------------------------------
# Telemetry periods belong to the backlog item "Tick rate, and telemetry
# periods". Flight parameters wait on speed envelopes (ADR-0005) and the
# safety layer. These values just let the adapter run.
POSITION_PERIOD_MS = 50
VELOCITY_PERIOD_MS = 50
RANGE_PERIOD_MS = 50
BATTERY_PERIOD_MS = 500
STATUS_POLL_PERIOD = 0.2
"""Seconds between drone status polls."""
VERTICAL_SPEED = 0.3
"""Meters per second, for take-off and landing."""
HOVER_SETTLE_DURATION = 1.0
"""Seconds to settle into a hover."""
MIN_MOVE_DURATION = 0.5
"""Seconds. The shortest move ever requested from the high-level commander."""
HEIGHT_IF_UNKNOWN = 2.0
"""Meters assumed when landing without a position estimate: a slow, safe descent."""
# ------------------------------------------------------------------------------

_MULTIRANGER_VARIABLES = {
    RangeDirection.FRONT: "range.front",
    RangeDirection.BACK: "range.back",
    RangeDirection.LEFT: "range.left",
    RangeDirection.RIGHT: "range.right",
    RangeDirection.UP: "range.up",
}
_DOWN_RANGE_VARIABLE = "range.zrange"  # on the Flow deck

type _LogData = dict[str, float]
"""One log sample: variable name to value, as cflib delivers it."""
type _LogCallback = Callable[[int, _LogData, LogConfig], None]
"""cflib's log callback signature: (timestamp in ms, data, the log block)."""

_drivers_initialized = False


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
        self._stop_status_polling = threading.Event()
        self._status_thread: threading.Thread | None = None
        self._is_streaming_velocity = False
        self._is_airborne = False
        self._landing_finishes_at: float | None = None

    # --- Connection ---------------------------------------------------------

    def connect(self) -> None:
        _init_drivers_once()
        sync_crazyflie = SyncCrazyflie(self._uri, cf=Crazyflie(rw_cache=self._cache_directory))
        sync_crazyflie.open_link()  # blocks until connected; raises if it can't connect
        self._sync_crazyflie = sync_crazyflie
        try:
            sync_crazyflie.wait_for_params()
            if not self._deck_attached("deck.bcFlow2", "deck.bcFlow"):  # Flow deck v2 or v1
                raise RuntimeError("Flow deck not detected: autonomous flight needs it.")
            reset_estimator(sync_crazyflie)  # blocks until the position estimate settles
            self._start_logging(has_multiranger=self._deck_attached("deck.bcMultiranger"))
            self._start_status_polling()
        except BaseException:
            self._close_link()
            raise

    def disconnect(self) -> None:
        if self._sync_crazyflie is None:
            return
        # cflib's close_link() sends a zero-thrust setpoint, which would drop a
        # flying drone. Land first and wait for it: blocking is fine at shutdown.
        try:
            if self._is_airborne:
                self.land()
                if self._landing_finishes_at is not None:
                    self._clock.sleep_until(self._landing_finishes_at)
                self._finish_landing_if_due()
        finally:
            # Clean up even if landing failed (e.g. the link already dropped).
            self._stop_status_polling.set()
            if self._status_thread is not None:
                self._status_thread.join(timeout=1.0)
                self._status_thread = None
            for log_config in self._log_configs:
                log_config.stop()
            self._log_configs.clear()
            self._close_link()

    # --- Commands -----------------------------------------------------------

    def arm(self) -> None:
        self._cf.supervisor.send_arming_request(True)

    def disarm(self) -> None:
        self._stop_motors()
        self._cf.supervisor.send_arming_request(False)

    def take_off(self, height: float) -> None:
        if height <= 0.0:
            raise ValueError(f"Take-off height must be positive: {height}")
        self._landing_finishes_at = None
        self._release_velocity_streaming()
        current_height = self._latest_height(if_unknown=0.0)
        duration = move_duration(height - current_height, VERTICAL_SPEED, MIN_MOVE_DURATION)
        self._cf.high_level_commander.takeoff(height, duration, yaw=FIXED_YAW_RAD)
        self._is_airborne = True

    def land(self) -> None:
        self._release_velocity_streaming()
        current_height = self._latest_height(if_unknown=HEIGHT_IF_UNKNOWN)
        duration = move_duration(current_height, VERTICAL_SPEED, MIN_MOVE_DURATION)
        self._cf.high_level_commander.land(0.0, duration, yaw=FIXED_YAW_RAD)
        # The high-level commander keeps the motors running after it lands;
        # take_snapshot stops them once the landing has had time to finish.
        self._landing_finishes_at = self._clock.now() + duration

    def set_velocity(self, velocity: Vector3, yaw_rate_rad_per_s: float = 0.0) -> None:
        self._landing_finishes_at = None
        self._cf.commander.send_velocity_world_setpoint(
            velocity.x, velocity.y, velocity.z, yaw_rate_deg_per_s(yaw_rate_rad_per_s)
        )
        self._is_streaming_velocity = True

    def move_to(self, position: Vector3, duration: float) -> None:
        if duration <= 0.0:
            raise ValueError(f"Move duration must be positive: {duration}")
        self._landing_finishes_at = None
        self._release_velocity_streaming()
        self._cf.high_level_commander.go_to(
            position.x,
            position.y,
            position.z,
            FIXED_YAW_RAD,
            max(duration, MIN_MOVE_DURATION),
        )

    def hover(self) -> None:
        self._landing_finishes_at = None
        self._release_velocity_streaming()
        commander = self._cf.high_level_commander
        latest = self._telemetry.latest_position_estimate()
        if latest is None:
            # No estimate yet: hold relative to the commander's own position.
            commander.go_to(0.0, 0.0, 0.0, FIXED_YAW_RAD, HOVER_SETTLE_DURATION, relative=True)
        else:
            # VERIFY: after velocity streaming, the high-level commander starts
            # this trajectory from the drone's current state, not a stale one.
            here = latest.value
            commander.go_to(here.x, here.y, here.z, FIXED_YAW_RAD, HOVER_SETTLE_DURATION)

    def emergency_stop(self) -> None:
        self._cf.supervisor.send_emergency_stop()
        self._is_airborne = False
        self._is_streaming_velocity = False
        self._landing_finishes_at = None

    def take_snapshot(self, time: float, dt: float) -> Snapshot:
        self._finish_landing_if_due()
        return self._telemetry.snapshot(time, dt)

    # --- Internals ----------------------------------------------------------

    @property
    def _cf(self) -> Crazyflie:
        if self._sync_crazyflie is None:
            raise RuntimeError("Not connected: call connect() first.")
        return self._sync_crazyflie.cf

    def _close_link(self) -> None:
        if self._sync_crazyflie is not None:
            self._sync_crazyflie.close_link()
            self._sync_crazyflie = None

    def _deck_attached(self, *parameters: str) -> bool:
        """True if any of the deck parameters says the deck is attached."""
        for parameter in parameters:
            try:
                if int(self._cf.param.get_value(parameter)) == 1:
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
            self._cf.commander.send_notify_setpoint_stop()
            self._is_streaming_velocity = False

    def _stop_motors(self) -> None:
        if self._is_streaming_velocity:
            self._cf.commander.send_stop_setpoint()
            self._is_streaming_velocity = False
        self._cf.high_level_commander.stop()  # stops the trajectory and the motors
        self._is_airborne = False
        self._landing_finishes_at = None

    def _finish_landing_if_due(self) -> None:
        # VERIFY: the landing trajectory has really touched down by now.
        if self._landing_finishes_at is not None and self._clock.now() >= self._landing_finishes_at:
            self._stop_motors()

    # --- Telemetry ----------------------------------------------------------

    def _start_logging(self, has_multiranger: bool) -> None:
        self._add_log_block(
            "position",
            POSITION_PERIOD_MS,
            ["stateEstimate.x", "stateEstimate.y", "stateEstimate.z"],
            self._on_position,
        )
        self._add_log_block(
            "velocity",
            VELOCITY_PERIOD_MS,
            ["stateEstimate.vx", "stateEstimate.vy", "stateEstimate.vz"],
            self._on_velocity,
        )
        self._add_log_block("battery", BATTERY_PERIOD_MS, ["pm.vbat"], self._on_battery)
        self._add_log_block("down", RANGE_PERIOD_MS, [_DOWN_RANGE_VARIABLE], self._on_down_range)
        if has_multiranger:
            self._add_log_block(
                "multiranger",
                RANGE_PERIOD_MS,
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
        self._cf.log.add_config(log_config)
        log_config.data_received_cb.add_callback(on_data)
        log_config.start()
        self._log_configs.append(log_config)

    # Log callbacks run on cflib's receive thread. Keep them tiny: convert and
    # write to the telemetry buffer, nothing else.

    def _on_position(self, timestamp: int, data: _LogData, log_config: LogConfig) -> None:
        position = Vector3(
            data["stateEstimate.x"], data["stateEstimate.y"], data["stateEstimate.z"]
        )
        self._telemetry.write_position_estimate(position, drone_time_from_timestamp(timestamp))

    def _on_velocity(self, timestamp: int, data: _LogData, log_config: LogConfig) -> None:
        velocity = Vector3(
            data["stateEstimate.vx"], data["stateEstimate.vy"], data["stateEstimate.vz"]
        )
        self._telemetry.write_velocity_estimate(velocity, drone_time_from_timestamp(timestamp))

    def _on_battery(self, timestamp: int, data: _LogData, log_config: LogConfig) -> None:
        self._telemetry.write_battery_voltage(data["pm.vbat"], drone_time_from_timestamp(timestamp))

    def _on_down_range(self, timestamp: int, data: _LogData, log_config: LogConfig) -> None:
        reading = range_reading_from_mm(int(data[_DOWN_RANGE_VARIABLE]))
        self._telemetry.write_range_readings(
            {RangeDirection.DOWN: reading}, drone_time_from_timestamp(timestamp)
        )

    def _on_multiranger(self, timestamp: int, data: _LogData, log_config: LogConfig) -> None:
        readings = {
            direction: range_reading_from_mm(int(data[variable]))
            for direction, variable in _MULTIRANGER_VARIABLES.items()
        }
        self._telemetry.write_range_readings(readings, drone_time_from_timestamp(timestamp))

    # --- Drone status -------------------------------------------------------

    def _start_status_polling(self) -> None:
        self._stop_status_polling.clear()
        thread = threading.Thread(target=self._poll_status, name="crazyflie-status", daemon=True)
        thread.start()
        self._status_thread = thread

    def _poll_status(self) -> None:
        # Its own thread, because read_bitfield() blocks for up to ~0.2 s while
        # it waits for the drone's reply: never acceptable inside a tick.
        # If this thread dies, drone status simply goes stale, which staleness
        # checks will see.
        while not self._stop_status_polling.wait(STATUS_POLL_PERIOD):
            bitfield = self._cf.supervisor.read_bitfield()
            self._telemetry.write_drone_status(drone_status_from_bitfield(bitfield), None)
