# pyright: basic
# Basic mode because cflib has no type hints (ADR-0004). Everything this module
# exposes is fully typed; the looseness stays inside this file.
"""The Crazyflie adapter: implements the drone interface on a real Crazyflie.

TODO: not yet run on hardware. Written before the drone arrived, as a deliberate
exception for learning (ADR-0010), from the installed cflib source and
docs/cflib-primer.md. Its first real test is the Bench field test (propellers on:
ADR-0044). Assumptions that need checking there are marked VERIFY.

How the interface maps onto cflib:
- Telemetry: log blocks stream into the shared TelemetryBuffer, converted to
  SI units. Position, velocity and drone status share one block, so they come
  from the same moment (ADR-0021).
- Steering mode (set_velocity): low-level world-frame velocity setpoints.
- Fast mode, take-off, landing, hover: the high-level commander, which plans
  and flies trajectories on the drone.
"""

import logging
import math
from collections.abc import Callable
from enum import Enum

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.supervisor import (
    BIT_IS_ARMED,
    BIT_IS_AUTO_ARMED,
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
from crazyflie_behavior.drone.crazyflie.time_limit import WAIT_SLICE, run_with_time_limit
from crazyflie_behavior.drone.crazyflie.touchdown import (
    FINAL_DESCENT_SPEED,
    HEIGHT_IF_UNKNOWN,
    MAX_READING_AGE,
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
"""Position, velocity and drone status. The estimate itself updates at 100 Hz (ADR-0023)."""
DOWN_RANGE_PERIOD_MS = 20
"""The Flow deck reads the down range every 25 ms (ADR-0023)."""
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
TAKE_OFF_STATUS_GRACE = 1.0
"""Seconds after a take-off is sent during which the drone may be flying before its
status shows it (ADR-0032). VERIFY at the bench."""
# Time limits for connecting (ADR-0029). VERIFY at the bench, and measure (backlog #25).
LINK_TIME_LIMIT = 15.0
"""Seconds to open the link and get the drone's variable lists. A first connect,
with nothing cached, downloads more."""
PARAMETERS_TIME_LIMIT = 10.0
"""Seconds to read the parameter values."""
POSITION_ESTIMATE_TIME_LIMIT = 20.0
"""Seconds for the position estimate to settle. cflib needs at least 5 s (ADR-0029)."""
FIRST_TELEMETRY_TIME_LIMIT = 3.0
"""Seconds for every telemetry value to arrive once (ADR-0031). The battery,
streamed once a second, is the slowest."""
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
        self,
        clock: Clock,
        uri: str = DEFAULT_URI,
        cache_directory: str = "./cache",
        *,
        take_over_flight: bool = False,
    ) -> None:
        """`take_over_flight`: only the rescue landing sets this (ADR-0038). `connect()` then
        accepts a drone that is flying, skips the position estimate reset and treats the
        drone as airborne, as if this adapter had sent the take-off."""
        self._clock = clock
        self._uri = uri
        self._cache_directory = cache_directory
        self._take_over_flight = take_over_flight
        self._telemetry = TelemetryBuffer(clock)
        self._sync_crazyflie: SyncCrazyflie | None = None
        self._log_configs: list[LogConfig] = []
        self._is_streaming_velocity = False
        self._is_airborne = False
        """A take-off was sent (or the flight was taken over) and the motors haven't been stopped since."""
        self._is_ignoring_hover = False
        """The latest hover was ignored because the drone isn't one that may be flying: the log line for
        it comes once per streak."""
        self._is_drone_state_unknown = False
        """True from the start of `connect()` until the drone is known to be on the floor or its
        flight is taken over (ADR-0038). It stays True when the drone is found flying and refused:
        while True, the drone may be flying, so the link is closed without a zero-thrust setpoint."""
        self._take_off_sent_at = 0.0
        """When the latest take-off was sent. Meaningful while airborne."""
        self._landing_phase = _LandingPhase.NOT_LANDING
        self._landing_finishes_at = 0.0
        """When the planned landing should be over. Meaningful while PLANNED."""
        self._final_descent_deadline = 0.0
        """When the final descent must be over. Meaningful while FINAL_DESCENT."""
        self._touchdown_detector = TouchdownDetector()
        self._last_drone_time: float | None = None
        self._dropped_state_count = 0
        """State packets in a row with an estimate that isn't finite."""
        self._latest_status_bitfield: int | None = None
        """The supervisor bitfield of the latest state packet, for bits `DroneStatus`
        doesn't carry (auto-arming, ADR-0037). Written on cflib's receive thread."""

    # --- Connection ---------------------------------------------------------

    def connect(self) -> None:
        _init_drivers_once()
        self._last_drone_time = None  # a new session: the drone may have rebooted
        self._dropped_state_count = 0
        self._latest_status_bitfield = None
        self._is_airborne = False  # a new session learns what the drone is doing from the drone
        self._is_ignoring_hover = False
        self._is_drone_state_unknown = True
        self._cancel_landing()  # nor does it carry on a landing from an earlier session
        # A new session starts with no values, so the wait for the first telemetry
        # can't pass on values left from an earlier one (ADR-0031).
        self._telemetry = TelemetryBuffer(self._clock)
        sync_crazyflie = SyncCrazyflie(self._uri, cf=Crazyflie(rw_cache=self._cache_directory))
        self._sync_crazyflie = sync_crazyflie  # tracked from the start, so cleanup always finds it
        try:
            # cflib's blocking steps each get a time limit, waited for in short
            # slices so the interrupt signal gets through, even on Windows (ADR-0029).
            run_with_time_limit(
                "Opening the link",
                sync_crazyflie.open_link,  # raises if it can't connect
                LINK_TIME_LIMIT,
                what_to_check="Check the Crazyflie is switched on, charged and in range.",
                clock=self._clock,
                # Stop a connection still under way, without cflib's zero-thrust
                # setpoint: the drone may be flying (ADR-0038). When connecting
                # fails on its own, cflib closes the link itself.
                on_abandon=self._close_radio_link_only,
            )
            run_with_time_limit(
                "Reading the parameters",
                sync_crazyflie.wait_for_params,
                PARAMETERS_TIME_LIMIT,
                what_to_check="The link may have dropped: check the Crazyflie is still switched on.",
                clock=self._clock,
            )
            if not self._deck_attached("deck.bcFlow2", "deck.bcFlow"):  # Flow deck v2 or v1
                raise RuntimeError("Flow deck not detected: autonomous flight needs it.")
            # Find out whether the drone is flying before anything else touches it: the
            # position estimate reset below expects a drone sitting still (ADR-0038).
            self._start_state_logging()
            self._settle_whether_the_drone_is_flying(self._wait_for_drone_status())
            self._start_remaining_logging(has_multiranger=self._deck_attached("deck.bcMultiranger"))
            self._wait_for_first_telemetry()
            self._log_whether_the_drone_arms_itself()
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
        self._is_ignoring_hover = False  # flying from now on: a hover on the floor later is a new streak
        current_height = self._latest_height(if_unknown=0.0)
        duration = move_duration(height - current_height, VERTICAL_SPEED, MIN_MOVE_DURATION)
        self._crazyflie.high_level_commander.takeoff(height, duration, yaw=DEFAULT_YAW_RAD)
        self._is_airborne = True
        self._take_off_sent_at = self._clock.now()

    def land(self) -> None:
        if self._may_be_flying():
            self._start_landing()
        else:
            # On the floor, a move down would spin an armed drone's motors up
            # (ADR-0032), so just make sure they're stopped.
            self._stop_motors()

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
        if not self._may_be_flying():
            # Ignored on the floor: a hover is a go_to to the current position, and on the
            # floor that would spin up an armed drone's motors (ADR-0039).
            if not self._is_ignoring_hover:
                logger.info("Hover ignored: the drone isn't flying. Logged once per streak.")
                self._is_ignoring_hover = True
            return
        self._is_ignoring_hover = False  # this hover goes through: the streak is over
        self._cancel_landing()
        self._release_velocity_streaming()
        commander = self._crazyflie.high_level_commander
        position_estimate = self._telemetry.latest_position_estimate()
        if position_estimate is None:
            # No estimate yet: hold relative to the commander's own position.
            commander.go_to(0.0, 0.0, 0.0, DEFAULT_YAW_RAD, HOVER_SETTLE_DURATION, relative=True)
        else:
            # VERIFY: after velocity streaming, the high-level commander starts
            # this trajectory from the drone's current state, not a stale one.
            here = position_estimate.value
            commander.go_to(here.x, here.y, here.z, DEFAULT_YAW_RAD, HOVER_SETTLE_DURATION)

    def emergency_stop(self) -> None:
        self._crazyflie.supervisor.send_emergency_stop()
        self._is_airborne = False
        self._is_streaming_velocity = False
        self._cancel_landing()

    def take_snapshot(self, dt: float) -> Snapshot:
        snapshot = self._telemetry.snapshot(dt)
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
            if self._is_airborne or self._is_drone_state_unknown:
                # The drone may be flying: cflib's close_link() would drop it (ADR-0038).
                self._close_radio_link_only()
            else:
                self._sync_crazyflie.close_link()
            self._sync_crazyflie = None
        self._log_configs.clear()  # they belonged to that link

    def _close_radio_link_only(self) -> None:
        """Turn off the radio link and nothing else, so a flying drone keeps flying (ADR-0038).

        cflib's `Crazyflie.close_link()` first sends a zero-thrust setpoint, which
        would drop a flying drone. This does three of its other steps, in the same
        order: close the link, stop the incoming packet handler, and call the
        disconnected callbacks. It skips the rest (re-creating the incoming packet
        handler, clearing the expected answers, setting the state to disconnected),
        which matters only to a Crazyflie object that is used again: `connect()`
        always makes a new one. It uses cflib internals (`link`, `incoming`):
        re-check it against `close_link()` whenever cflib is upgraded. Safe to call
        twice, and when the link isn't open.
        """
        if self._sync_crazyflie is None:
            return
        crazyflie = self._sync_crazyflie.cf
        if crazyflie.link is not None:
            logger.info("Closing the radio link only, with no zero-thrust setpoint: the drone may be flying")
            crazyflie.link.close()
            crazyflie.link = None
        if crazyflie.incoming and crazyflie.incoming.is_alive():
            crazyflie.incoming.stop()
            crazyflie.incoming.join(timeout=1)
        # cflib's own close_link() calls this too: it tells SyncCrazyflie the link is closed.
        crazyflie.disconnected.call(crazyflie.link_uri)

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
        position_estimate = self._telemetry.latest_position_estimate()
        return if_unknown if position_estimate is None else position_estimate.value.z

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

    def _may_be_flying(self) -> bool:
        """Whether the drone may be in the air, so stopping it needs a landing (ADR-0032).

        - No take-off sent since our last motor stop: not flying. The drone
          status can't be trusted here, because after the motors stop it keeps
          saying flying for 2 s.
        - Otherwise, flying if the status is missing, older than
          `MAX_READING_AGE`, or says flying. When unsure, say flying: a landing
          sent to a drone already down only runs the motors until touchdown is
          confirmed, while stopping the motors of a flying drone drops it.
        - Otherwise (a fresh status says not flying), still flying for
          `TAKE_OFF_STATUS_GRACE` after the take-off was sent, because the
          status shows a take-off only after a short delay.
        """
        if not self._is_airborne:
            return False
        now = self._clock.now()
        status = self._telemetry.latest_drone_status()
        if status is None or status.age(now) > MAX_READING_AGE or status.value.is_flying:
            return True
        return now - self._take_off_sent_at < TAKE_OFF_STATUS_GRACE

    def _start_landing(self) -> float:
        """Start descending to the floor. Returns when the descent should be done."""
        self._release_velocity_streaming()
        position_estimate = self._telemetry.latest_position_estimate()
        current_height = HEIGHT_IF_UNKNOWN if position_estimate is None else position_estimate.value.z
        duration = move_duration(current_height, VERTICAL_SPEED, MIN_MOVE_DURATION)
        # A go_to, not the firmware's landing: when a landing finishes, the
        # firmware switches the motors off by itself, even above the floor. A
        # go_to keeps holding its end point, so the motors stop only once
        # touchdown is confirmed (ADR-0032). VERIFY at the bench how the drone
        # settles at the floor while the go_to holds it there.
        commander = self._crazyflie.high_level_commander
        if position_estimate is None:
            # No estimate yet: straight down from the commander's own position.
            commander.go_to(0.0, 0.0, -HEIGHT_IF_UNKNOWN, DEFAULT_YAW_RAD, duration, relative=True)
        else:
            here = position_estimate.value
            commander.go_to(here.x, here.y, 0.0, DEFAULT_YAW_RAD, duration)
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
        # deadline, past the floor if need be, from where the landing's go_to
        # ends. Unlike streamed setpoints, it keeps going if ticks stop
        # (ADR-0011).
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
            if not self._may_be_flying():
                self._stop_motors()  # a take-off was sent, but the drone never flew
                return
            self._clock.sleep_until(self._start_landing())
        while self._landing_phase is not _LandingPhase.NOT_LANDING:
            self._finish_landing(self._telemetry.snapshot(0.0))
            if self._landing_phase is not _LandingPhase.NOT_LANDING:
                self._clock.sleep_until(self._clock.now() + TOUCHDOWN_POLL_PERIOD)

    # --- Telemetry ----------------------------------------------------------

    def _start_state_logging(self) -> None:
        self._add_log_block("state", STATE_PERIOD_MS, list(_STATE_VARIABLES), self._on_state)

    def _start_remaining_logging(self, has_multiranger: bool) -> None:
        self._add_log_block("battery", BATTERY_PERIOD_MS, ["pm.vbat"], self._on_battery)
        self._add_log_block("down", DOWN_RANGE_PERIOD_MS, [_DOWN_RANGE_VARIABLE], self._on_down_range)
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

    def _wait_for_drone_status(self) -> int:
        """Return the supervisor bitfield of the first state packet since connecting (ADR-0038).

        It arrives after the state block started, so it's fresh. A status that
        never arrives is a time-limit error: unknown fails safe.
        """
        self._wait_until(
            lambda: self._latest_status_bitfield is not None,
            lambda: (
                f"Waiting for the drone's status took longer than {FIRST_TELEMETRY_TIME_LIMIT:g} s. "
                "Check the Crazyflie is in range, and that its firmware logs its status."
            ),
        )
        bitfield = self._latest_status_bitfield
        if bitfield is None:
            raise RuntimeError("The drone's status vanished after it arrived")  # the callback never clears it
        return bitfield

    def _settle_whether_the_drone_is_flying(self, bitfield: int) -> None:
        """Refuse a flying drone, take over its flight, or reset the position estimate (ADR-0038)."""
        if self._take_over_flight:
            logger.warning("Taking over the flight: no estimate reset.")
            self._is_airborne = True
            # No take-off of ours, so no status lag to wait out: the status just read is the truth. A land
            # request for a drone that reports it's on the floor then only stops the motors (ADR-0039).
            self._take_off_sent_at = -math.inf
            self._is_drone_state_unknown = False
            return
        if drone_status_from_bitfield(bitfield).is_flying:
            # Raised before the estimate reset. The drone stays unknown-or-flying for the
            # link close, which then leaves it alone. A drone that just landed also lands
            # here: its status says flying for a while after the motors stop (ADR-0032).
            raise RuntimeError(
                "The drone is still flying: run the rescue landing, or wait a few seconds if it just landed."
            )
        self._is_drone_state_unknown = False  # on the floor: a normal link close is safe from here
        run_with_time_limit(
            "Settling the position estimate",
            lambda: reset_estimator(self._sync_crazyflie),
            POSITION_ESTIMATE_TIME_LIMIT,
            what_to_check=(
                "Check the Flow deck can see the floor (enough light and texture) and that the drone is sitting still."
            ),
            clock=self._clock,
        )
        # The state block kept streaming through the reset, so drop what it wrote before
        # it: no position from before the reset is used (ADR-0038).
        self._telemetry = TelemetryBuffer(self._clock)

    def _wait_for_first_telemetry(self) -> None:
        """Return once every telemetry value has arrived once (ADR-0031)."""
        missing_values: list[str] = []

        def has_every_value() -> bool:
            nonlocal missing_values
            missing_values = self._telemetry.missing_values()
            return not missing_values

        # The message uses the list from the check that timed out: a value arriving just after
        # it can't change what the message says.
        self._wait_until(has_every_value, lambda: self._first_telemetry_time_limit_message(missing_values))

    def _first_telemetry_time_limit_message(self, missing_values: list[str]) -> str:
        message = (
            f"Waiting for the first telemetry took longer than "
            f"{FIRST_TELEMETRY_TIME_LIMIT:g} s. Still missing: {', '.join(missing_values)}. "
        )
        if self._take_over_flight and ("position estimate" in missing_values or "velocity estimate" in missing_values):
            # The status wait already got a state packet, which carries the estimates too, so
            # every packet received had a value that isn't finite for the missing estimate
            # (ADR-0045). A take-over's drone may be in the air or on the floor: in the air, it
            # can't follow our landings, which are position commands.
            return message + (
                "If the drone is in the air, it can't land under control without its estimate: "
                "use tools/emergency_stop.py, with something soft under the drone first."
            )
        return message + "Check the Crazyflie is in range, and that its firmware logs these values."

    def _wait_until(self, is_done: Callable[[], bool], time_limit_message: Callable[[], str]) -> None:
        """Wait up to `FIRST_TELEMETRY_TIME_LIMIT` for `is_done()`, or raise a TimeoutError.

        Checks every wait slice. Unlike cflib's waits (ADR-0029), a plain sleep
        ends at once on the interrupt signal, so this needs no helper thread.
        """
        deadline = self._clock.now() + FIRST_TELEMETRY_TIME_LIMIT
        while not is_done():
            now = self._clock.now()
            if now >= deadline:
                raise TimeoutError(time_limit_message())
            self._clock.sleep_until(min(deadline, now + WAIT_SLICE))

    def _log_whether_the_drone_arms_itself(self) -> None:
        """Log once whether the firmware arms the drone by itself (ADR-0037)."""
        bitfield = self._latest_status_bitfield
        if bitfield is None:
            return  # can't happen once the first telemetry has arrived (ADR-0031)
        if (bitfield >> BIT_IS_AUTO_ARMED) & 1:
            logger.info("The drone arms itself (auto-arming is on): a disarm won't last.")
        else:
            logger.info("The drone doesn't arm itself: it needs an arm request before it can fly.")

    def _add_log_block(self, name: str, period_ms: int, variables: list[str], on_data: _LogCallback) -> None:
        log_config = LogConfig(name=name, period_in_ms=period_ms)
        for variable in variables:
            log_config.add_variable(variable)  # fetched as the type the drone stores
        try:
            self._crazyflie.log.add_config(log_config)
        except KeyError as error:
            raise RuntimeError(
                f"The drone's firmware doesn't log a variable this adapter needs ({error}). Update the firmware."
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
        reading = range_reading_from_mm(int(data[_DOWN_RANGE_VARIABLE]))
        self._telemetry.write_range_readings({RangeDirection.DOWN: reading}, self._drone_time(timestamp))

    def _on_multiranger(self, timestamp: int, data: _LogData, log_config: LogConfig) -> None:
        readings = {
            direction: range_reading_from_mm(int(data[variable]))
            for direction, variable in _MULTIRANGER_VARIABLES.items()
        }
        self._telemetry.write_range_readings(readings, self._drone_time(timestamp))
