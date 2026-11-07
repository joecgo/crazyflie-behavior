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
- Take-off and landing cross the bad-flow zone level, on low-level altHold
  setpoints that update_take_off_and_landing sends each tick (ADR-0048, ADR-0055).
- Fast mode, hover, and the rest of take-off and landing: the high-level
  commander, which plans and flies trajectories on the drone.
"""

import logging
import math
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from enum import Enum

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.commander import SET_SETPOINT_CHANNEL
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.supervisor import (
    BIT_IS_ARMED,
    BIT_IS_AUTO_ARMED,
    BIT_IS_CRASHED,
    BIT_IS_FLYING,
    BIT_IS_TUMBLED,
)
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crtp.crtpstack import CRTPPacket, CRTPPort
from cflib.utils.reset_estimator import reset_estimator

from crazyflie_behavior.drone.crazyflie.bad_flow_zone import (
    INITIAL_CLIMB_TIME_LIMIT,
    LEVEL_VERTICAL_SPEED,
    MAX_FINAL_DESCENT_HEIGHT,
    SETTLE_CAP_HEIGHT,
    SettleDetector,
    final_descent_height,
)
from crazyflie_behavior.drone.crazyflie.conversions import (
    alt_hold_packet_data,
    battery_voltage_from_mv,
    drone_time_from_timestamp,
    move_duration,
    range_reading_from_mm,
    sound_frequency_from_pitch,
    yaw_rate_deg_per_s,
)
from crazyflie_behavior.drone.crazyflie.time_limit import WAIT_SLICE, run_with_time_limit
from crazyflie_behavior.drone.crazyflie.touchdown import (
    HEIGHT_IF_UNKNOWN,
    MAX_READING_AGE,
    SLOW_DESCENT_SPEED,
    TouchdownDetector,
    final_descent_deadline,
    fresh_down_distance,
)
from crazyflie_behavior.drone.interface import DroneInterface
from crazyflie_behavior.drone.telemetry_buffer import TelemetryBuffer
from crazyflie_behavior.geometry import Vector3
from crazyflie_behavior.snapshot import DroneStatus, RangeDirection, RangeReading, Snapshot, Stamped
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
DIAGNOSTIC_PERIOD_MS = 100
"""Attitude, motor power and flow quality, for the debug log only (ADR-0050)."""

# --- PLACEHOLDERS, NOT DECISIONS ---------------------------------------------
# Flight parameters wait on speed envelopes (ADR-0005) and the safety layer.
# These values just let the adapter run.
VERTICAL_SPEED = 0.3
"""Meters per second, for the high-level parts of take-off and landing."""
HOVER_SETTLE_DURATION = 1.0
"""Seconds to settle into a hover."""
MIN_MOVE_DURATION = 0.5
"""Seconds. The shortest move ever requested from the high-level commander."""
TOUCHDOWN_POLL_PERIOD = 0.05
"""Seconds between landing updates while landing at shutdown: a tick's length."""
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
# The diagnostic block (ADR-0050, ADR-0053): 3 floats, 4 uint16, a uint8 and two uint16, 25 bytes.
_ATTITUDE_VARIABLES = ("stateEstimate.roll", "stateEstimate.pitch", "stateEstimate.yaw")
"""Degrees. The firmware logs pitch with the legacy inverted sign."""
_MOTOR_VARIABLES = ("motor.m1", "motor.m2", "motor.m3", "motor.m4")
"""Motor power, 0-65535."""
_FLOW_QUALITY_VARIABLES = ("motion.squal", "motion.shutter")
"""Surface features seen, and shutter time (longer in low light)."""
_DIAGNOSTIC_BATTERY_VARIABLE = "pm.vbatMV"
"""Millivolts: the battery voltage, faster than the battery block's once a second."""
_DIAGNOSTIC_VARIABLES = (
    *_ATTITUDE_VARIABLES,
    *_MOTOR_VARIABLES,
    *_FLOW_QUALITY_VARIABLES,
    _DIAGNOSTIC_BATTERY_VARIABLE,
)
# Buzzer parameters (ADR-0053). `sound.effect` picks an entry in the firmware's effects table.
_SOUND_EFFECT_PARAMETER = "sound.effect"
_SOUND_FREQUENCY_PARAMETER = "sound.freq"
"""The steady tone's pitch, in whole hertz."""
_SOUND_EFFECT_OFF = 0
_SOUND_EFFECT_CHIRP = 4
"""The firmware's "charging done" tune: two notes, then it switches itself off."""
_SOUND_EFFECT_TONE = 12
"""A steady tone at `sound.freq`. The parameter's own description numbers it wrongly."""
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
    """Where a landing is (ADR-0012, ADR-0019, ADR-0048)."""

    NOT_LANDING = "not_landing"
    """No landing under way."""
    LANDING_APPROACH = "landing_approach"
    """A high-level move down to the final descent height."""
    FINAL_DESCENT = "final_descent"
    """Down through the bad-flow zone until touchdown: level, or slowly by the high-level
    commander when the down range isn't usable."""


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
        self._is_streaming = False
        """Low-level setpoints are being sent, velocity or level: a high-level command needs a hand-over."""
        self._level_vertical_speed: float | None = None
        """Meters per second, up: the latest level setpoint's, while the stream is level."""
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
        self._is_in_initial_climb = False
        self._take_off_height = 0.0
        """Meters: the latest take-off's target. Meaningful during the initial climb."""
        self._settle_detector = SettleDetector()
        self._final_descent_height = final_descent_height(None)
        """Meters, by the down range. Set when an initial climb ends; the cap until then."""
        self._is_ignoring_commands = False
        """The latest command was ignored while crossing the bad-flow zone: the log line for it comes
        once per streak."""
        self._landing_phase = _LandingPhase.NOT_LANDING
        self._landing_approach_ends_at = 0.0
        """When the landing approach should be over. Meaningful while LANDING_APPROACH."""
        self._is_final_descent_level = False
        """Meaningful while FINAL_DESCENT: level on the down range, or the slow high-level descent."""
        self._final_descent_deadline = 0.0
        """When the final descent must be over. Meaningful while FINAL_DESCENT."""
        self._touchdown_detector = TouchdownDetector()
        self._last_drone_time: float | None = None
        self._dropped_state_count = 0
        """State packets in a row with an estimate that isn't finite."""
        self._latest_status_bitfield: int | None = None
        """The supervisor bitfield of the latest state packet, for bits `DroneStatus`
        doesn't carry (auto-arming, ADR-0037). Written on cflib's receive thread."""
        self._is_skipping_buzzer_commands = False
        """The latest buzzer command was skipped because the link is closed: the warning for it
        comes once per streak."""

    # --- Connection ---------------------------------------------------------

    def connect(self) -> None:
        _init_drivers_once()
        self._last_drone_time = None  # a new session: the drone may have rebooted
        self._dropped_state_count = 0
        self._latest_status_bitfield = None
        self._is_airborne = False  # a new session learns what the drone is doing from the drone
        self._is_ignoring_hover = False
        self._is_skipping_buzzer_commands = False
        self._is_drone_state_unknown = True
        # Nor does it carry on a take-off, landing or setpoint stream from an earlier session.
        self._is_in_initial_climb = False
        self._cancel_landing()
        self._is_streaming = False
        self._level_vertical_speed = None
        self._is_ignoring_commands = False
        self._final_descent_height = final_descent_height(None)
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
            self._log_whether_the_buzzer_deck_is_attached()
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
        """Raises for a height at or below the final descent height's cap: no hover there can fly (ADR-0056)."""
        if height <= MAX_FINAL_DESCENT_HEIGHT:
            raise ValueError(
                f"Take-off height must be above the final descent height's cap, "
                f"{MAX_FINAL_DESCENT_HEIGHT:g} m: {height}"
            )
        if self._is_ignored_while_crossing_the_bad_flow_zone("Take-off"):
            return
        self._is_ignoring_hover = False  # flying from now on: a hover on the floor later is a new streak
        if self._may_be_flying():
            # Already in the air, above the bad-flow zone: no initial climb.
            self._cancel_landing()
            with self._handing_over_to_high_level():
                self._go_to_height(height)
        else:
            self._start_initial_climb(height)
        self._is_airborne = True
        self._take_off_sent_at = self._clock.now()

    def land(self) -> None:
        if not self._may_be_flying():
            # On the floor, a move down would spin an armed drone's motors up
            # (ADR-0032), so just make sure they're stopped.
            self._stop_motors()
        elif self._is_in_initial_climb:
            # No landing approach: this take-off has no final descent height yet (ADR-0049).
            logger.info("Landing during the initial climb: no landing approach.")
            self._is_in_initial_climb = False
            self._start_final_descent(self._latest_fresh_down_distance())
        elif self._landing_phase is _LandingPhase.NOT_LANDING:
            self._start_landing_approach()
        # Otherwise already landing: a new landing approach could climb back up (ADR-0056).

    def set_velocity(self, velocity: Vector3, yaw_rate_rad_per_s: float = 0.0) -> None:
        if self._is_ignored_while_crossing_the_bad_flow_zone("Set-velocity"):
            return
        self._cancel_landing()
        self._crazyflie.commander.send_velocity_world_setpoint(
            velocity.x, velocity.y, velocity.z, yaw_rate_deg_per_s(yaw_rate_rad_per_s)
        )
        self._is_streaming = True
        self._level_vertical_speed = None

    def move_to(self, position: Vector3, duration: float) -> None:
        if duration <= 0.0:
            raise ValueError(f"Move duration must be positive: {duration}")
        if self._is_ignored_while_crossing_the_bad_flow_zone("Move-to"):
            return
        self._cancel_landing()
        with self._handing_over_to_high_level():
            self._crazyflie.high_level_commander.go_to(
                position.x,
                position.y,
                position.z,
                DEFAULT_YAW_RAD,
                max(duration, MIN_MOVE_DURATION),
            )

    def hover(self) -> None:
        if self._is_ignored_while_crossing_the_bad_flow_zone("Hover"):
            return
        if not self._may_be_flying():
            # Ignored on the floor: a hover is a go_to to the current position, and on the
            # floor that would spin up an armed drone's motors (ADR-0039).
            if not self._is_ignoring_hover:
                logger.info("Hover ignored: the drone isn't flying. Logged once per streak.")
                self._is_ignoring_hover = True
            return
        self._is_ignoring_hover = False  # this hover goes through: the streak is over
        self._cancel_landing()
        commander = self._crazyflie.high_level_commander
        position_estimate = self._telemetry.latest_position_estimate()
        with self._handing_over_to_high_level():
            if position_estimate is None:
                # No estimate yet: hold relative to the commander's own position.
                commander.go_to(0.0, 0.0, 0.0, DEFAULT_YAW_RAD, HOVER_SETTLE_DURATION, relative=True)
            else:
                here = position_estimate.value
                commander.go_to(here.x, here.y, here.z, DEFAULT_YAW_RAD, HOVER_SETTLE_DURATION)

    def emergency_stop(self) -> None:
        self._crazyflie.supervisor.send_emergency_stop()
        self._is_airborne = False
        self._is_in_initial_climb = False
        self._is_streaming = False
        self._level_vertical_speed = None
        self._cancel_landing()

    def chirp(self) -> None:
        # A chirp that a silence or a tone cuts short leaves the firmware partway through its
        # tune, so the next chirp plays only the rest.
        self._write_buzzer_parameter(_SOUND_EFFECT_PARAMETER, _SOUND_EFFECT_CHIRP)

    def play_tone(self, pitch: float) -> None:
        frequency = sound_frequency_from_pitch(pitch)
        # The pitch first: the tone plays whatever `sound.freq` holds when it starts.
        self._write_buzzer_parameter(_SOUND_FREQUENCY_PARAMETER, frequency)
        self._write_buzzer_parameter(_SOUND_EFFECT_PARAMETER, _SOUND_EFFECT_TONE)

    def silence(self) -> None:
        self._write_buzzer_parameter(_SOUND_EFFECT_PARAMETER, _SOUND_EFFECT_OFF)

    def take_snapshot(self, dt: float) -> Snapshot:
        return self._telemetry.snapshot(dt)

    def update_take_off_and_landing(self, snapshot: Snapshot) -> None:
        if self._is_in_initial_climb:
            self._update_initial_climb(snapshot)
        else:
            self._update_landing(snapshot)

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

    def _write_buzzer_parameter(self, name: str, value: int) -> None:
        """Queue one parameter write, or skip it with a warning while the link is closed (ADR-0053)."""
        # Once the link is lost, cflib forgets the parameter list and a write raises, while a
        # movement command is only dropped.
        if self._crazyflie.link is None:
            if not self._is_skipping_buzzer_commands:
                logger.warning("Buzzer command not sent: the link is closed. Warned once per streak.")
                self._is_skipping_buzzer_commands = True
            return
        self._is_skipping_buzzer_commands = False  # this write goes through: the streak is over
        self._crazyflie.param.set_value(name, value)

    @contextmanager
    def _handing_over_to_high_level(self) -> Iterator[None]:
        """Wraps a high-level command so it takes over from a setpoint stream (ADR-0048, ADR-0056).

        The order: a level stream's last setpoint, the high-level command, then the
        release. A setpoint stops the high-level planner, and a stopped planner
        commands the motors off once the stream is released. The planner plans the
        command from the current estimate (sources in ADR-0056).
        """
        if self._level_vertical_speed is not None:
            self._send_level_setpoint(self._level_vertical_speed)
        yield
        if self._is_streaming:
            self._crazyflie.commander.send_notify_setpoint_stop()
            self._is_streaming = False
            self._level_vertical_speed = None

    def _send_level_setpoint(self, vertical_speed: float) -> None:
        """One altHold setpoint: roll and pitch held at 0, `vertical_speed` m/s up (ADR-0048)."""
        packet = CRTPPacket()
        packet.port = CRTPPort.COMMANDER_GENERIC
        packet.channel = SET_SETPOINT_CHANNEL
        packet.data = alt_hold_packet_data(vertical_speed)
        self._crazyflie.send_packet(packet)
        self._is_streaming = True
        self._level_vertical_speed = vertical_speed

    def _is_ignored_while_crossing_the_bad_flow_zone(self, command: str) -> bool:
        """Whether a command is ignored: it is during the initial climb and the final descent (ADR-0056).

        Logged once per streak.
        """
        if self._is_in_initial_climb:
            part = "initial climb"
        elif self._landing_phase is _LandingPhase.FINAL_DESCENT:
            part = "final descent"
        else:
            self._is_ignoring_commands = False  # this command goes through: the streak is over
            return False
        if not self._is_ignoring_commands:
            logger.info("%s ignored during the %s. Logged once per streak.", command, part)
            self._is_ignoring_commands = True
        return True

    def _go_to_height(self, height: float) -> None:
        """A high-level move straight up or down to `height`, at the estimated x and y (ADR-0048)."""
        commander = self._crazyflie.high_level_commander
        position_estimate = self._telemetry.latest_position_estimate()
        if position_estimate is None:
            # No estimate yet, which connect() rules out (ADR-0031): hold where it is.
            commander.go_to(0.0, 0.0, 0.0, DEFAULT_YAW_RAD, HOVER_SETTLE_DURATION, relative=True)
            return
        here = position_estimate.value
        duration = move_duration(height - here.z, VERTICAL_SPEED, MIN_MOVE_DURATION)
        commander.go_to(here.x, here.y, height, DEFAULT_YAW_RAD, duration)

    def _stop_motors(self) -> None:
        if self._is_streaming:
            self._crazyflie.commander.send_stop_setpoint()
            self._is_streaming = False
            self._level_vertical_speed = None
        self._crazyflie.high_level_commander.stop()  # stops the trajectory and the motors
        self._is_airborne = False
        self._is_in_initial_climb = False
        self._cancel_landing()

    def _shut_down_link(self) -> None:
        for log_config in self._log_configs:
            log_config.stop()
        self._close_link()

    # --- Take-off and landing (ADR-0012, ADR-0019, ADR-0048, ADR-0049) -------

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

    def _start_initial_climb(self, height: float) -> None:
        """Start climbing level through the bad-flow zone (ADR-0048). The first setpoint goes out at once."""
        self._cancel_landing()
        self._is_in_initial_climb = True
        self._is_ignoring_commands = False  # a new crossing: a new streak
        self._take_off_height = height
        self._settle_detector = SettleDetector()
        # A landing during the climb sets its final descent's time limit from these readings (ADR-0049).
        self._touchdown_detector = TouchdownDetector()
        self._final_descent_height = final_descent_height(None)
        self._send_level_setpoint(LEVEL_VERTICAL_SPEED)

    def _update_initial_climb(self, snapshot: Snapshot) -> None:
        now = self._clock.now()
        self._settle_detector.observe(snapshot, now)
        self._touchdown_detector.observe(snapshot, now)
        if now - self._take_off_sent_at >= INITIAL_CLIMB_TIME_LIMIT:
            logger.warning("The initial climb hasn't ended %g s after the take-off. Landing.", INITIAL_CLIMB_TIME_LIMIT)
            self.land()
            return
        if self._settle_detector.is_cap_tripped:
            logger.warning(
                "The horizontal speed estimate hasn't settled by %.2f m. Landing.",
                SETTLE_CAP_HEIGHT,
            )
            self.land()
            return
        settle_height = self._settle_detector.settle_height
        down = fresh_down_distance(snapshot, now)
        if settle_height is not None and down is not None and down.value >= final_descent_height(settle_height):
            self._end_initial_climb(settle_height)
        else:
            self._send_level_setpoint(LEVEL_VERTICAL_SPEED)

    def _end_initial_climb(self, settle_height: float) -> None:
        """Hand over to a high-level climb to the take-off height, at the current x and y (ADR-0048)."""
        self._is_in_initial_climb = False
        self._final_descent_height = final_descent_height(settle_height)
        logger.info(
            "Initial climb done: settle height %.3f m, final descent height %.3f m. Climbing to %.2f m.",
            settle_height,
            self._final_descent_height,
            self._take_off_height,
        )
        with self._handing_over_to_high_level():
            self._go_to_height(self._take_off_height)

    def _start_landing_approach(self) -> None:
        """A high-level move down to the final descent height, or the final descent at once if already there."""
        self._touchdown_detector = TouchdownDetector()
        down = self._latest_fresh_down_distance()
        if down is not None and down.value <= self._final_descent_height:
            self._start_final_descent(down)
            return
        # A go_to, not the firmware's landing, which switches the motors off when it
        # ends, even above the floor (ADR-0032).
        commander = self._crazyflie.high_level_commander
        position_estimate = self._telemetry.latest_position_estimate()
        with self._handing_over_to_high_level():
            if position_estimate is None:
                # No estimate yet: straight down from the commander's own position, until the
                # down range reaches the final descent height.
                duration = move_duration(HEIGHT_IF_UNKNOWN, VERTICAL_SPEED, MIN_MOVE_DURATION)
                commander.go_to(0.0, 0.0, -HEIGHT_IF_UNKNOWN, DEFAULT_YAW_RAD, duration, relative=True)
            else:
                here = position_estimate.value
                height = min(here.z, self._final_descent_height)
                duration = move_duration(here.z - height, VERTICAL_SPEED, MIN_MOVE_DURATION)
                commander.go_to(here.x, here.y, height, DEFAULT_YAW_RAD, duration)
        self._landing_approach_ends_at = self._clock.now() + duration
        self._landing_phase = _LandingPhase.LANDING_APPROACH

    def _cancel_landing(self) -> None:
        self._landing_phase = _LandingPhase.NOT_LANDING
        self._is_final_descent_level = False

    def _update_landing(self, snapshot: Snapshot) -> None:
        # Stop the motors only once touchdown is confirmed, or at the final
        # descent's time limit, never just because the landing approach's time is
        # up: it may have used a stale height.
        if self._landing_phase is _LandingPhase.NOT_LANDING:
            return
        now = self._clock.now()
        self._touchdown_detector.observe(snapshot, now)
        match self._landing_phase:
            case _LandingPhase.LANDING_APPROACH:
                down = fresh_down_distance(snapshot, now)
                if now >= self._landing_approach_ends_at or (
                    down is not None and down.value <= self._final_descent_height
                ):
                    self._start_final_descent(down)
            case _LandingPhase.FINAL_DESCENT:
                if self._touchdown_detector.touchdown_confirmed(now):
                    logger.info("Touchdown confirmed; stopping the motors.")
                    self._stop_motors()
                elif now >= self._final_descent_deadline:
                    logger.warning(
                        "Touchdown never confirmed by the down range; the final descent's "
                        "time limit is up, so the drone must be on the floor. Stopping the motors."
                    )
                    self._stop_motors()
                elif self._is_final_descent_level:
                    self._send_level_setpoint(-LEVEL_VERTICAL_SPEED)
            case _LandingPhase.NOT_LANDING:
                pass  # handled by the early return above

    def _start_final_descent(self, down: Stamped[float] | None) -> None:
        """Level on a usable down range, else ADR-0019's slow high-level descent (ADR-0048).

        `down`: the latest fresh down range, if any.
        """
        now = self._clock.now()
        if self._touchdown_detector.touchdown_confirmed(now):
            logger.info("Touchdown confirmed; stopping the motors.")
            self._stop_motors()
            return
        self._landing_phase = _LandingPhase.FINAL_DESCENT
        self._is_ignoring_commands = False  # a new crossing: a new streak
        heights = [self._touchdown_detector.highest_recent_distance(), None if down is None else down.value]
        highest = max((height for height in heights if height is not None), default=None)
        if down is not None:
            self._is_final_descent_level = True
            self._final_descent_deadline = final_descent_deadline(now, highest, LEVEL_VERTICAL_SPEED)
            logger.info("Final descent: level, from %.3f m by the down range.", down.value)
            self._send_level_setpoint(-LEVEL_VERTICAL_SPEED)
            return
        self._is_final_descent_level = False
        self._final_descent_deadline = final_descent_deadline(now, highest, SLOW_DESCENT_SPEED)
        logger.warning("Final descent without a usable down range: descending slowly.")
        # One high-level move straight down at SLOW_DESCENT_SPEED until the
        # deadline, past the floor if need be. Unlike streamed setpoints, it
        # keeps going if ticks stop (ADR-0011).
        duration = self._final_descent_deadline - now
        with self._handing_over_to_high_level():
            self._crazyflie.high_level_commander.go_to(
                0.0,
                0.0,
                -SLOW_DESCENT_SPEED * duration,
                DEFAULT_YAW_RAD,
                duration,
                relative=True,
                linear=True,
            )

    def _latest_fresh_down_distance(self) -> Stamped[float] | None:
        return fresh_down_distance(self._telemetry.snapshot(0.0), self._clock.now())

    def _land_and_wait_for_touchdown(self) -> None:
        """Land, or finish a take-off or landing under way, and block until the motors are stopped.

        Updates every TOUCHDOWN_POLL_PERIOD from the start, so a level setpoint stream keeps going.
        """
        self.land()
        while self._landing_phase is not _LandingPhase.NOT_LANDING:
            self._clock.sleep_until(self._clock.now() + TOUCHDOWN_POLL_PERIOD)
            self._update_landing(self._telemetry.snapshot(0.0))

    # --- Telemetry ----------------------------------------------------------

    def _start_state_logging(self) -> None:
        self._add_log_block("state", STATE_PERIOD_MS, list(_STATE_VARIABLES), self._on_state)

    def _start_remaining_logging(self, has_multiranger: bool) -> None:
        self._add_log_block("battery", BATTERY_PERIOD_MS, ["pm.vbat"], self._on_battery)
        self._add_log_block("down", DOWN_RANGE_PERIOD_MS, [_DOWN_RANGE_VARIABLE], self._on_down_range)
        self._add_log_block("diagnostic", DIAGNOSTIC_PERIOD_MS, list(_DIAGNOSTIC_VARIABLES), self._on_diagnostic)
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

    def _log_whether_the_buzzer_deck_is_attached(self) -> None:
        """Log once whether the Buzzer deck is attached (ADR-0053). Flying doesn't need it."""
        if self._deck_attached("deck.bcBuzzer"):
            logger.info("Buzzer deck detected.")
        else:
            logger.info("No Buzzer deck: buzzer commands will make no sound.")

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

    def _on_diagnostic(self, timestamp: int, data: _LogData, log_config: LogConfig) -> None:
        """One debug line, nothing in the telemetry buffer (ADR-0050)."""
        roll_deg, pitch_deg, yaw_deg = (data[variable] for variable in _ATTITUDE_VARIABLES)
        squal, shutter = (int(data[variable]) for variable in _FLOW_QUALITY_VARIABLES)
        battery_voltage = battery_voltage_from_mv(int(data[_DIAGNOSTIC_BATTERY_VARIABLE]))
        logger.debug(
            "Diagnostic: drone_time=%.3f roll_deg=%.2f pitch_deg=%.2f yaw_deg=%.2f motors=%s squal=%d shutter=%d "
            "battery_voltage=%.3f",
            self._drone_time(timestamp),
            roll_deg,
            pitch_deg,
            yaw_deg,
            [int(data[variable]) for variable in _MOTOR_VARIABLES],
            squal,
            shutter,
            battery_voltage,
        )

    def _on_multiranger(self, timestamp: int, data: _LogData, log_config: LogConfig) -> None:
        readings = {
            direction: range_reading_from_mm(int(data[variable]))
            for direction, variable in _MULTIRANGER_VARIABLES.items()
        }
        self._telemetry.write_range_readings(readings, self._drone_time(timestamp))
