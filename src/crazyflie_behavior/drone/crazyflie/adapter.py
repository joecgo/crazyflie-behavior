# pyright: basic
# Basic mode because cflib has no type hints (ADR-0004). Everything this module
# exposes is fully typed; the looseness stays inside this file.
"""The Crazyflie adapter: implements the drone interface on a real Crazyflie.

Written before the drone arrived, as a deliberate exception for learning
(ADR-0010), from the installed cflib source and docs/cflib-primer.md.
Assumptions still to check in field tests are marked VERIFY.

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
from collections.abc import Callable

from cflib.crazyflie.log import LogConfig

# TODO: test-only, until the tests take the bit positions from cflib themselves (#158).
from cflib.crazyflie.supervisor import BIT_IS_ARMED as BIT_IS_ARMED

# The adapter's own.
from cflib.crazyflie.supervisor import BIT_IS_AUTO_ARMED

# TODO: test-only, until the tests take the bit positions from cflib themselves (#158).
from cflib.crazyflie.supervisor import BIT_IS_FLYING as BIT_IS_FLYING
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie

from crazyflie_behavior.drone.crazyflie.bad_flow_zone import FINAL_DESCENT_HEIGHT

# TODO: test-only, until the tests import it from commands.py (#158).
from crazyflie_behavior.drone.crazyflie.commands import DEFAULT_YAW_RAD as DEFAULT_YAW_RAD
from crazyflie_behavior.drone.crazyflie.commands import CrazyflieCommands, land_as_a_last_resort

# TODO: test-only, until the tests import it from link.py (#158).
from crazyflie_behavior.drone.crazyflie.link import THRUST_BASE as THRUST_BASE

# The adapter's own.
from crazyflie_behavior.drone.crazyflie.link import CrazyflieLink

# TODO: test-only, until the tests import them from log_blocks.py (#158).
from crazyflie_behavior.drone.crazyflie.log_blocks import _CONTROLLER_VARIABLES as _CONTROLLER_VARIABLES
from crazyflie_behavior.drone.crazyflie.log_blocks import _DIAGNOSTIC_VARIABLES as _DIAGNOSTIC_VARIABLES
from crazyflie_behavior.drone.crazyflie.log_blocks import _DOWN_VARIABLES as _DOWN_VARIABLES
from crazyflie_behavior.drone.crazyflie.log_blocks import _STATE_VARIABLES as _STATE_VARIABLES
from crazyflie_behavior.drone.crazyflie.log_blocks import _TAKE_OFF_VARIABLES as _TAKE_OFF_VARIABLES
from crazyflie_behavior.drone.crazyflie.log_blocks import TAKE_OFF_BLOCK_DURATION as TAKE_OFF_BLOCK_DURATION

# The adapter's own.
from crazyflie_behavior.drone.crazyflie.log_blocks import LogBlocks, drone_status_from_bitfield
from crazyflie_behavior.drone.crazyflie.take_off_and_landing import (
    HOVER_SETTLE_DURATION,
    MIN_MOVE_DURATION,
    VERTICAL_SPEED,
    TakeOffAndLanding,
)

# TODO: test-only, until the tests import them from take_off_and_landing.py (#158).
from crazyflie_behavior.drone.crazyflie.take_off_and_landing import (
    LANDING_APPROACH_AIM_BELOW as LANDING_APPROACH_AIM_BELOW,
)
from crazyflie_behavior.drone.crazyflie.take_off_and_landing import LANDING_APPROACH_BACKUP as LANDING_APPROACH_BACKUP
from crazyflie_behavior.drone.crazyflie.take_off_and_landing import TAKE_OFF_STATUS_GRACE as TAKE_OFF_STATUS_GRACE
from crazyflie_behavior.drone.crazyflie.take_off_and_landing import TOUCHDOWN_POLL_PERIOD as TOUCHDOWN_POLL_PERIOD
from crazyflie_behavior.drone.crazyflie.time_limit import WAIT_SLICE
from crazyflie_behavior.drone.crazyflie.touchdown import HEIGHT_IF_UNKNOWN
from crazyflie_behavior.drone.interface import STALE_AFTER, DroneInterface
from crazyflie_behavior.drone.telemetry_buffer import TelemetryBuffer
from crazyflie_behavior.geometry import Vector3
from crazyflie_behavior.snapshot import Snapshot, Stamped
from crazyflie_behavior.timing.clock import Clock

logger = logging.getLogger(__name__)

DEFAULT_URI = "radio://0/80/2M/E7E7E7E7E7"

# --- PLACEHOLDERS, NOT DECISIONS ---------------------------------------------
# Flight parameters wait on speed envelopes (ADR-0005) and the safety layer.
# These values just let the adapter run.
# Time limits for connecting (ADR-0029). VERIFY at the bench, and measure (backlog #25).
FIRST_TELEMETRY_TIME_LIMIT = 3.0
"""Seconds for every telemetry value to arrive once (ADR-0031). The battery,
streamed once a second, is the slowest."""
NOT_FLYING_TIME_LIMIT = 3.0
"""Seconds that closing the link waits, after a motor stop, for the drone to report not flying
(ADR-0058). Its status keeps saying flying for 2 s after the motors stop."""
WAIT_AFTER_SILENCE = 1.0
"""Seconds the link stays open after the silence at disconnect: closing it throws away writes not yet sent
(ADR-0085)."""
LOW_LIGHT_IMAGE_QUALITY = 60
"""The Flow deck's image quality (`motion.squal`) under which a take-off logs a low-light warning
(ADR-0054)."""
# ------------------------------------------------------------------------------

LAST_RESORT_LANDING_DURATION = HEIGHT_IF_UNKNOWN / VERTICAL_SPEED
"""Seconds: the last-resort landing's fixed time, down from the highest height assumed (ADR-0084)."""


def _yes_no(flag: bool) -> str:
    return "yes" if flag else "no"


class CrazyflieAdapter(DroneInterface):
    """Drives a real Crazyflie over the Crazyradio."""

    def __init__(
        self,
        clock: Clock,
        uri: str = DEFAULT_URI,
        cache_directory: str = "./cache",
        *,
        take_over_flight: bool = False,
        take_off_log: bool = False,
    ) -> None:
        """`take_over_flight`: only the rescue landing sets this (ADR-0038). `connect()` then
        accepts a drone that is flying, skips the position estimate reset and treats the
        drone as airborne, as if this adapter had sent the take-off. It also skips the
        diagnostic and controller blocks (ADR-0067).

        `take_off_log`: run the take-off block, from the end of connect and from each take-off
        (ADR-0063, ADR-0065)."""
        self._clock = clock
        self._uri = uri
        self._cache_directory = cache_directory
        self._take_over_flight = take_over_flight
        self._log_blocks = LogBlocks(clock, lambda: self._link.crazyflie, take_over_flight=take_over_flight)
        """The log blocks, which own the telemetry buffer (ADR-0093). `connect()` builds a new one, with no
        values."""
        self._link = CrazyflieLink(clock, uri, cache_directory, take_over_flight=take_over_flight)
        """The radio link (ADR-0093). `connect()` builds a new one, with no lost link and no thrust base report."""
        self._commands = CrazyflieCommands(lambda: self._link.crazyflie, lambda: self._log_blocks.telemetry)
        """The commands sent to the drone (ADR-0093). `connect()` builds a new one, with no setpoint stream."""
        self._take_off_and_landing = TakeOffAndLanding(
            clock, self._commands, lambda: self._log_blocks.telemetry, self.take_snapshot
        )
        """Take-off and landing (ADR-0093). It sends through `_commands`, so `connect()` builds a new one right after
        them, with no flight under way."""
        self._is_ignoring_hover = False
        """The latest hover was ignored because the drone isn't one that may be flying: the log line for
        it comes once per streak."""
        self._is_drone_state_unknown = False
        """True from the start of `connect()` until the drone is known to be on the floor or its
        flight is taken over (ADR-0038). It stays True when the drone is found flying and refused:
        while True, the drone may be flying, so the link is closed without a zero-thrust setpoint."""
        self._is_ignoring_estimate_reset = False
        """The latest estimate reset was ignored because the drone may be flying: the warning for it
        comes once per streak."""
        self._take_off_log = take_off_log

    # --- Connection ---------------------------------------------------------

    def connect(self) -> None:
        self._is_ignoring_hover = False
        self._is_ignoring_estimate_reset = False
        self._is_drone_state_unknown = True
        # A new link learns what the drone is doing from the drone, and carries on no take-off, landing or
        # setpoint stream from an earlier one.
        self._commands = CrazyflieCommands(lambda: self._link.crazyflie, lambda: self._log_blocks.telemetry)
        self._take_off_and_landing = TakeOffAndLanding(
            self._clock, self._commands, lambda: self._log_blocks.telemetry, self.take_snapshot
        )
        # A new link starts with no values, so the wait for the first telemetry
        # can't pass on values left from an earlier one (ADR-0031), and with no earlier
        # drone timestamp: the drone may have rebooted.
        self._log_blocks = LogBlocks(self._clock, lambda: self._link.crazyflie, take_over_flight=self._take_over_flight)
        # A new link part too, so no lost link or thrust base report carries over.
        self._link = CrazyflieLink(
            self._clock, self._uri, self._cache_directory, take_over_flight=self._take_over_flight
        )
        try:
            self._link.open()
            if not self._link.is_deck_attached("deck.bcFlow2", "deck.bcFlow"):  # Flow deck v2 or v1
                raise RuntimeError("Flow deck not detected: autonomous flight needs it.")
            # Find out whether the drone is flying before anything else touches it: the
            # estimate reset below expects a drone sitting still (ADR-0038).
            self._log_blocks.start_state_logging()
            self._settle_whether_the_drone_is_flying(self._wait_for_drone_status())
            self._link.write_thrust_base()
            self._log_blocks.start_remaining_logging(has_multiranger=self._link.is_deck_attached("deck.bcMultiranger"))
            self._wait_for_first_telemetry()
            self._log_whether_the_drone_arms_itself()
            self._log_whether_the_buzzer_deck_is_attached()
            if self._take_off_log:
                # Last, so its run falls in the first ticks: cflib starts a block once it's created (ADR-0065).
                self._log_blocks.create_take_off_block()
        except BaseException:
            self._close_link()
            raise

    def disconnect(self) -> None:
        if not self._link.has_link_to_close:
            return
        try:
            if not self._link.is_lost:
                self._land_silence_and_wait()
            if not self._link.is_lost_link_raised:
                # Lost since the last snapshot, or while disconnecting: the run must still end with an error.
                self._link.raise_if_lost()
        finally:
            # After a lost link, also one found while landing or waiting here.
            if self._link.is_lost:
                self._log_closing_after_the_lost_link()
            # Clean up even if landing failed.
            self._shut_down_link()

    def _land_silence_and_wait(self) -> None:
        """Disconnecting with the link up: land a drone that may be flying, silence the buzzer and keep the link
        open after it, then wait for not flying."""
        # cflib's close_link() sends a zero-thrust setpoint, which would drop a
        # flying drone. Land first and wait until the motors are stopped:
        # blocking is fine at shutdown.
        was_airborne = self._take_off_and_landing.is_airborne
        try:
            # The landing below doesn't tick, so nothing else would stop the take-off block (ADR-0065).
            self._log_blocks.stop_take_off_block()
            if self._take_off_and_landing.is_airborne:
                self._take_off_and_landing.land_and_wait_for_touchdown()
        except Exception:
            if was_airborne and not self._link.is_lost:
                land_as_a_last_resort(
                    lambda: self._link.crazyflie,
                    LAST_RESORT_LANDING_DURATION,
                    self._clock,
                    self._link.close_radio_link_only,
                )
            raise
        self._silence_and_keep_the_link_open()
        if self._take_off_and_landing.has_stopped_motors:
            # That setpoint also locks a drone that still reports flying (ADR-0058).
            self._wait_for_not_flying()

    # --- Commands -----------------------------------------------------------

    def arm(self) -> None:
        status = self._log_blocks.telemetry.latest_drone_status()
        if status is not None:
            # The drone answers an arm request with only "refused", never why (ADR-0058).
            level = logging.WARNING if status.value.is_locked else logging.INFO
            logger.log(
                level,
                "Arm requested. The drone status, %.2f s old: armed %s, can arm %s, locked %s.",
                status.age(self._clock.now()),
                _yes_no(status.value.is_armed),
                _yes_no(status.value.can_arm),
                _yes_no(status.value.is_locked),
            )
        self._commands.arm()

    def disarm(self) -> None:
        self._take_off_and_landing.stop_motors()
        self._commands.disarm()

    def take_off(self, height: float) -> None:
        """Raises for a height at or below the final descent height: no hover there can fly (ADR-0056, ADR-0077)."""
        if height <= FINAL_DESCENT_HEIGHT:
            raise ValueError(
                f"Take-off height must be above the final descent height, {FINAL_DESCENT_HEIGHT:g} m: {height}"
            )
        if not self._take_off_and_landing.take_off(height, self._log_take_off_warnings):
            return
        self._is_ignoring_hover = False  # flying from now on: a hover on the floor later is a new streak
        self._log_blocks.run_take_off_block()  # after the take-off's own commands (ADR-0065)

    def land(self) -> None:
        self._take_off_and_landing.land()

    def set_velocity(self, velocity: Vector3, yaw_rate_rad_per_s: float = 0.0) -> None:
        if self._take_off_and_landing.is_ignored_while_crossing_the_bad_flow_zone("Set-velocity"):
            return
        self._take_off_and_landing.cancel_landing()
        self._commands.send_velocity_setpoint(velocity, yaw_rate_rad_per_s)

    def move_to(self, position: Vector3, duration: float) -> None:
        if duration <= 0.0:
            raise ValueError(f"Move duration must be positive: {duration}")
        if self._take_off_and_landing.is_ignored_while_crossing_the_bad_flow_zone("Move-to"):
            return
        self._take_off_and_landing.cancel_landing()
        self._commands.go_to(position, max(duration, MIN_MOVE_DURATION))

    def hover(self) -> None:
        if self._take_off_and_landing.is_ignored_while_crossing_the_bad_flow_zone("Hover"):
            return
        if not self._take_off_and_landing.may_be_flying():
            # Ignored on the floor: a hover is a go_to to the current position, and on the
            # floor that would spin up an armed drone's motors (ADR-0039).
            if not self._is_ignoring_hover:
                logger.info("Hover ignored: the drone isn't flying. Logged once per streak.")
                self._is_ignoring_hover = True
            return
        self._is_ignoring_hover = False  # this hover goes through: the streak is over
        self._take_off_and_landing.cancel_landing()
        position_estimate = self._log_blocks.telemetry.latest_position_estimate()
        if position_estimate is None:
            # No estimate yet: hold relative to the commander's own position.
            self._commands.go_to_relative(Vector3.ZERO, HOVER_SETTLE_DURATION)
        else:
            self._commands.go_to(position_estimate.value, HOVER_SETTLE_DURATION)

    def emergency_stop(self) -> None:
        self._take_off_and_landing.emergency_stop()

    def reset_estimate(self) -> None:
        if self._take_off_and_landing.may_be_flying():
            # Just after a take-off, the drone status still says not flying and the down
            # range still reads the floor, so the safety layer can't tell (ADR-0039).
            if not self._is_ignoring_estimate_reset:
                logger.warning("Estimate reset ignored: the drone may be flying. Warned once per streak.")
                self._is_ignoring_estimate_reset = True
            return
        self._is_ignoring_estimate_reset = False  # this reset goes through: the streak is over
        self._commands.send_estimate_reset()

    def chirp(self) -> None:
        self._commands.chirp()

    def play_tone(self, pitch: float) -> None:
        self._commands.play_tone(pitch)

    def silence(self) -> None:
        self._commands.silence()

    def take_snapshot(self, dt: float) -> Snapshot:
        """Raises after a lost link (ADR-0084). Every tick starts with a snapshot, so nothing else a tick calls
        needs its own check (ADR-0086)."""
        self._link.raise_if_lost()
        return self._log_blocks.telemetry.snapshot(
            dt,
            is_in_initial_climb=self._take_off_and_landing.is_in_initial_climb,
            may_be_flying=self._take_off_and_landing.may_be_flying(),
        )

    def update_take_off_and_landing(self, snapshot: Snapshot) -> None:
        """Also stops the take-off block once its run is over (ADR-0065)."""
        self._take_off_and_landing.update(snapshot)
        self._log_blocks.stop_take_off_block_once_its_run_is_over()

    # --- Internals ----------------------------------------------------------

    def _close_link(self) -> None:
        """Only the radio link while the drone is airborne or its state is unknown: cflib's close_link() would drop a
        flying drone (ADR-0038)."""
        self._link.close(radio_link_only=self._take_off_and_landing.is_airborne or self._is_drone_state_unknown)

    def _log_closing_after_the_lost_link(self) -> None:
        if self._take_off_and_landing.may_be_flying():
            logger.error(
                "Closing without landing: the link is lost and the drone may still be flying. "
                "Run the rescue landing, or tools/emergency_stop.py with something soft under the drone."
            )
        else:
            logger.error("Closing without landing: the link is lost. The drone wasn't flying.")

    def _silence_and_keep_the_link_open(self) -> None:
        """Silence the buzzer, then keep the link open for WAIT_AFTER_SILENCE (ADR-0085). A write that fails gets
        a warning instead, and no wait."""
        if self._commands.silence_at_disconnect():
            self._clock.sleep_until(self._clock.now() + WAIT_AFTER_SILENCE)

    def _log_low_light_warning(self) -> None:
        """At take-off, warn of sideways drift when the Flow deck sees little (ADR-0054). Never refuses."""
        quality = self._log_blocks.latest_image_quality
        if quality is None or quality.age(self._clock.now()) > STALE_AFTER:
            logger.warning("Taking off with the Flow deck's image quality unknown: it may be low light.")
        elif quality.value < LOW_LIGHT_IMAGE_QUALITY:
            logger.warning(
                "Low light: the Flow deck's image quality is %d (under %d). "
                "The take-off may drift sideways until flow arrives.",
                quality.value,
                LOW_LIGHT_IMAGE_QUALITY,
            )

    def _log_thrust_base_warning(self) -> None:
        """At take-off, warn of a slow climb unless the drone confirmed the thrust base (ADR-0061). Never refuses."""
        if not self._link.is_thrust_base_confirmed:
            logger.warning("Taking off without a confirmed thrust base: the climb may be slow.")

    def _log_take_off_warnings(self) -> None:
        """Just before an initial climb: the low-light and thrust base warnings."""
        self._log_low_light_warning()
        self._log_thrust_base_warning()

    def _shut_down_link(self) -> None:
        self._log_blocks.stop_log_blocks()
        self._close_link()

    # --- Test-only forwards to the parts (ADR-0093) --------------------------
    # TODO: test-only, until the tests reach the take-off and landing part themselves (#158).

    @property
    def _is_in_initial_climb(self) -> bool:
        return self._take_off_and_landing.is_in_initial_climb

    @property
    def _take_off_sent_at(self) -> float:
        return self._take_off_and_landing._take_off_sent_at

    @_take_off_sent_at.setter
    def _take_off_sent_at(self, sent_at: float) -> None:
        self._take_off_and_landing._take_off_sent_at = sent_at

    @property
    def _landing_approach_ends_at(self) -> float:
        return self._take_off_and_landing._landing_approach_ends_at

    @property
    def _has_stopped_motors(self) -> bool:
        return self._take_off_and_landing.has_stopped_motors

    @_has_stopped_motors.setter
    def _has_stopped_motors(self, has_stopped_motors: bool) -> None:
        self._take_off_and_landing._has_stopped_motors = has_stopped_motors

    # TODO: test-only, until the tests reach the log-block part themselves (#158).

    @property
    def _telemetry(self) -> TelemetryBuffer:
        return self._log_blocks.telemetry

    @property
    def _log_configs(self) -> list[LogConfig]:
        return self._log_blocks._log_configs

    @property
    def _latest_status_bitfield(self) -> int | None:
        return self._log_blocks.latest_status_bitfield

    @_latest_status_bitfield.setter
    def _latest_status_bitfield(self, bitfield: int | None) -> None:
        self._log_blocks._latest_status_bitfield = bitfield

    @property
    def _latest_image_quality(self) -> Stamped[int] | None:
        return self._log_blocks.latest_image_quality

    @_latest_image_quality.setter
    def _latest_image_quality(self, quality: Stamped[int] | None) -> None:
        self._log_blocks._latest_image_quality = quality

    @property
    def _take_off_block(self) -> LogConfig | None:
        return self._log_blocks._take_off_block

    @_take_off_block.setter
    def _take_off_block(self, block: LogConfig | None) -> None:
        self._log_blocks._take_off_block = block

    @property
    def _is_take_off_block_running(self) -> bool:
        return self._log_blocks._is_take_off_block_running

    @_is_take_off_block_running.setter
    def _is_take_off_block_running(self, is_running: bool) -> None:
        self._log_blocks._is_take_off_block_running = is_running

    @property
    def _on_state(self) -> Callable[[int, dict[str, float], LogConfig], None]:
        return self._log_blocks._on_state

    @property
    def _on_down_range(self) -> Callable[[int, dict[str, float], LogConfig], None]:
        return self._log_blocks._on_down_range

    @property
    def _on_diagnostic(self) -> Callable[[int, dict[str, float], LogConfig], None]:
        return self._log_blocks._on_diagnostic

    @property
    def _on_controller(self) -> Callable[[int, dict[str, float], LogConfig], None]:
        return self._log_blocks._on_controller

    @property
    def _on_take_off_block(self) -> Callable[[int, dict[str, float], LogConfig], None]:
        return self._log_blocks._on_take_off_block

    @property
    def _on_multiranger(self) -> Callable[[int, dict[str, float], LogConfig], None]:
        return self._log_blocks._on_multiranger

    # TODO: test-only, until the tests reach the link part themselves (#158).

    @property
    def _sync_crazyflie(self) -> SyncCrazyflie | None:
        return self._link._sync_crazyflie

    @_sync_crazyflie.setter
    def _sync_crazyflie(self, sync_crazyflie: SyncCrazyflie | None) -> None:
        self._link._sync_crazyflie = sync_crazyflie

    @property
    def _on_connection_lost(self) -> Callable[[str, str], None]:
        return self._link._on_connection_lost

    @property
    def _on_thrust_base_reported(self) -> Callable[[str, str], None]:
        return self._link._on_thrust_base_reported

    @property
    def _is_thrust_base_confirmed(self) -> bool:
        return self._link.is_thrust_base_confirmed

    # --- Telemetry ----------------------------------------------------------

    def _wait_for_drone_status(self) -> int:
        """Return the supervisor bitfield of the first state packet since connecting (ADR-0038).

        It arrives after the state block started, so it's fresh. A status that
        never arrives is a time-limit error: unknown fails safe.
        """
        self._wait_until(
            lambda: self._log_blocks.latest_status_bitfield is not None,
            FIRST_TELEMETRY_TIME_LIMIT,
            lambda: (
                f"Waiting for the drone's status took longer than {FIRST_TELEMETRY_TIME_LIMIT:g} s. "
                "Check the Crazyflie is in range, and that its firmware logs its status."
            ),
        )
        bitfield = self._log_blocks.latest_status_bitfield
        if bitfield is None:
            raise RuntimeError("The drone's status vanished after it arrived")  # the callback never clears it
        return bitfield

    def _settle_whether_the_drone_is_flying(self, bitfield: int) -> None:
        """Refuse a flying drone, take over its flight, or reset the estimate (ADR-0038, ADR-0054)."""
        if self._take_over_flight:
            logger.warning("Taking over the flight: no estimate reset.")
            self._take_off_and_landing.take_over_flight()
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
        # No wait for the estimate to settle: the take-off rule judges it (ADR-0054).
        self._commands.send_estimate_reset()
        # The state block kept streaming, so drop what it wrote before the reset (ADR-0038).
        # Nothing waits for the reset, so values from before it can still arrive until it
        # reaches the drone, and a take-off judged on them may be refused (ADR-0054).
        self._log_blocks.replace_telemetry_buffer()

    def _wait_for_first_telemetry(self) -> None:
        """Return once every telemetry value has arrived once (ADR-0031)."""
        missing_values: list[str] = []

        def has_every_value() -> bool:
            nonlocal missing_values
            missing_values = self._log_blocks.telemetry.missing_values()
            return not missing_values

        # The message uses the list from the check that timed out: a value arriving just after
        # it can't change what the message says.
        self._wait_until(
            has_every_value,
            FIRST_TELEMETRY_TIME_LIMIT,
            lambda: self._first_telemetry_time_limit_message(missing_values),
        )

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

    def _wait_for_not_flying(self) -> None:
        """Wait until a fresh drone status says not flying, so the link close can't lock the drone (ADR-0058).

        At the time limit, warns and returns: the link closes anyway.
        """

        def is_not_flying() -> bool:
            status = self._log_blocks.telemetry.latest_drone_status()
            if status is None or status.age(self._clock.now()) > STALE_AFTER:
                return False
            return not status.value.is_flying

        try:
            self._wait_until(
                is_not_flying,
                NOT_FLYING_TIME_LIMIT,
                lambda: (
                    f"The drone still didn't report not flying after {NOT_FLYING_TIME_LIMIT:g} s of waiting. "
                    "Closing the link anyway: if it still counts as flying, it may lock and need a power cycle."
                ),
            )
        except TimeoutError as error:
            logger.warning("%s", error)
            return
        status = self._log_blocks.telemetry.latest_drone_status()
        if status is None:
            return  # can't happen: the wait just saw it, and the buffer never clears a value
        if status.value.is_locked:
            logger.warning("The drone reports it's locked: it refuses to arm until it's power cycled.")
        else:
            logger.info("The drone reports not flying and isn't locked. Can arm: %s.", _yes_no(status.value.can_arm))

    def _wait_until(
        self, is_done: Callable[[], bool], time_limit: float, time_limit_message: Callable[[], str]
    ) -> None:
        """Wait up to `time_limit` seconds for `is_done()`, or raise a TimeoutError.

        Checks every wait slice. Unlike cflib's waits (ADR-0029), a plain sleep
        ends at once on the interrupt signal, so this needs no helper thread.
        A lost link ends the wait at once with its error (ADR-0084).
        """
        deadline = self._clock.now() + time_limit
        while not is_done():
            self._link.raise_if_lost()
            now = self._clock.now()
            if now >= deadline:
                raise TimeoutError(time_limit_message())
            self._clock.sleep_until(min(deadline, now + WAIT_SLICE))

    def _log_whether_the_drone_arms_itself(self) -> None:
        """Log once whether the firmware arms the drone by itself (ADR-0037)."""
        bitfield = self._log_blocks.latest_status_bitfield
        if bitfield is None:
            return  # can't happen once the first telemetry has arrived (ADR-0031)
        if (bitfield >> BIT_IS_AUTO_ARMED) & 1:
            logger.info("The drone arms itself (auto-arming is on): a disarm won't last.")
        else:
            logger.info("The drone doesn't arm itself: it needs an arm request before it can fly.")

    def _log_whether_the_buzzer_deck_is_attached(self) -> None:
        """Log once whether the Buzzer deck is attached (ADR-0053). Flying doesn't need it."""
        if self._link.is_deck_attached("deck.bcBuzzer"):
            logger.info("Buzzer deck detected.")
        else:
            logger.info("No Buzzer deck: buzzer commands will make no sound.")
