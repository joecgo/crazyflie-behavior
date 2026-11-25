# pyright: basic
# Basic mode because cflib has no type hints (ADR-0004). Everything this module
# exposes is fully typed; the looseness stays inside this file.
"""The commands sent to a Crazyflie, and the setpoint stream's state (ADR-0093).

Setpoints, high-level moves, the motor stop, arming, the emergency stop, the buzzer and the estimate reset. Opening
and closing the link and the thrust base write stay in the adapter; the log blocks are in `log_blocks.py`.
"""

import logging
import math
from collections.abc import Callable, Iterator
from contextlib import contextmanager

from cflib.crazyflie import Crazyflie
from cflib.crazyflie.commander import SET_SETPOINT_CHANNEL
from cflib.crtp.crtpstack import CRTPPacket, CRTPPort

from crazyflie_behavior.drone.crazyflie.conversions import (
    alt_hold_packet_data,
    sound_frequency_from_pitch,
    yaw_rate_deg_per_s,
)
from crazyflie_behavior.drone.interface import FLOOR_MAX_SPEED
from crazyflie_behavior.drone.telemetry_buffer import TelemetryBuffer
from crazyflie_behavior.geometry import Vector3
from crazyflie_behavior.snapshot import Stamped
from crazyflie_behavior.timing.clock import Clock

logger = logging.getLogger(__name__)

DEFAULT_YAW_RAD = 0.0
"""The heading commands use unless told otherwise: world +x is where the drone faced at
take-off."""

_RESET_ESTIMATE_PARAMETER = "kalman.resetEstimation"
"""Written 1 for an estimate reset; the firmware sets it back to 0 (ADR-0054)."""
# Buzzer parameters (ADR-0053). `sound.effect` picks an entry in the firmware's effects table.
_SOUND_EFFECT_PARAMETER = "sound.effect"
_SOUND_FREQUENCY_PARAMETER = "sound.freq"
"""The steady tone's pitch, in whole hertz."""
_SOUND_EFFECT_OFF = 0
_SOUND_EFFECT_CHIRP = 4
"""The firmware's "charging done" tune: two notes, then it switches itself off."""
_SOUND_EFFECT_TONE = 12
"""A steady tone at `sound.freq`. The parameter's own description numbers it wrongly."""


class CrazyflieCommands:
    """The commands sent to the drone, and the setpoint stream's state (ADR-0093).

    Looks up the drone and the telemetry buffer on every call: `connect()` replaces both after building this, and
    the buffer a second time after the estimate reset.
    """

    def __init__(
        self, current_crazyflie: Callable[[], Crazyflie], current_telemetry: Callable[[], TelemetryBuffer]
    ) -> None:
        self._current_crazyflie = current_crazyflie
        self._current_telemetry = current_telemetry
        self._is_streaming = False
        """Low-level setpoints are being sent, velocity or level: a high-level command needs a hand-over."""
        self._level_vertical_speed: float | None = None
        """Meters per second, up: the latest level setpoint's, while the stream is level."""
        self._is_skipping_buzzer_commands = False
        """The latest buzzer command was skipped because the link is closed: the warning for it
        comes once per streak."""

    # --- Setpoints ------------------------------------------------------------

    def send_level_setpoint(self, vertical_speed: float) -> None:
        """One altHold setpoint: roll and pitch held at 0, `vertical_speed` m/s up (ADR-0048)."""
        packet = CRTPPacket()
        packet.port = CRTPPort.COMMANDER_GENERIC
        packet.channel = SET_SETPOINT_CHANNEL
        packet.data = alt_hold_packet_data(vertical_speed)
        self._current_crazyflie().send_packet(packet)
        self._is_streaming = True
        self._level_vertical_speed = vertical_speed

    def send_velocity_setpoint(self, velocity: Vector3, yaw_rate_rad_per_s: float) -> None:
        """One world-frame velocity setpoint."""
        self._current_crazyflie().commander.send_velocity_world_setpoint(
            velocity.x, velocity.y, velocity.z, yaw_rate_deg_per_s(yaw_rate_rad_per_s)
        )
        self._is_streaming = True
        self._level_vertical_speed = None

    # --- High-level moves, each handed over from any setpoint stream ----------

    def go_to(self, position: Vector3, duration: float) -> None:
        """A high-level move to `position` in `duration` seconds."""
        commander = self._current_crazyflie().high_level_commander
        with self._handing_over_to_high_level():
            commander.go_to(position.x, position.y, position.z, DEFAULT_YAW_RAD, duration)

    def go_to_relative(self, offset: Vector3, duration: float, *, linear: bool = False) -> None:
        """A high-level move by `offset` from the commander's own position, in `duration` seconds.

        `linear` goes to the high-level commander's `go_to` only when True, so the other moves' calls keep the
        arguments they had before the split (ADR-0093).
        """
        commander = self._current_crazyflie().high_level_commander
        with self._handing_over_to_high_level():
            if linear:
                commander.go_to(offset.x, offset.y, offset.z, DEFAULT_YAW_RAD, duration, relative=True, linear=True)
            else:
                commander.go_to(offset.x, offset.y, offset.z, DEFAULT_YAW_RAD, duration, relative=True)

    @contextmanager
    def _handing_over_to_high_level(self) -> Iterator[None]:
        """Wraps a high-level command so it takes over from a setpoint stream (ADR-0048, ADR-0056).

        The order: a level stream's last setpoint, the high-level command, then the
        release. A setpoint stops the high-level commander, and a stopped high-level
        commander commands the motors off once the stream is released. It plans the
        command from the current estimate (sources in ADR-0056).
        """
        if self._level_vertical_speed is not None:
            self.send_level_setpoint(self._level_vertical_speed)
        yield
        if self._is_streaming:
            self._current_crazyflie().commander.send_notify_setpoint_stop()
            self._is_streaming = False
            self._level_vertical_speed = None

    # --- Motors ---------------------------------------------------------------

    def stop_motors(self) -> None:
        """Stop the motors, then release the setpoint priority (ADR-0058). Sends only: the caller clears its
        flight state.

        Without the release, the stopped high-level commander's motors-off setpoints are refused, and a
        drone that still counts as flying locks once its setpoint is 2 s old.
        """
        crazyflie = self._current_crazyflie()
        commander = crazyflie.commander
        if self._is_streaming:
            commander.send_stop_setpoint()
            self._is_streaming = False
            self._level_vertical_speed = None
        crazyflie.high_level_commander.stop()  # stops the trajectory and the motors
        # The release hands the motors to the high-level commander, so it comes after its stop.
        commander.send_notify_setpoint_stop()

    def arm(self) -> None:
        """Send an arming request."""
        self._current_crazyflie().supervisor.send_arming_request(True)

    def disarm(self) -> None:
        """Send a disarming request."""
        self._current_crazyflie().supervisor.send_arming_request(False)

    def emergency_stop(self) -> None:
        """Cut the motors at once, which ends the setpoint stream."""
        self._current_crazyflie().supervisor.send_emergency_stop()
        self._is_streaming = False
        self._level_vertical_speed = None

    # --- Buzzer ---------------------------------------------------------------

    def chirp(self) -> None:
        """Play the firmware's two-note chirp (ADR-0053)."""
        # A chirp that a silence or a tone cuts short leaves the firmware partway through its
        # tune, so the next chirp plays only the rest.
        self._write_buzzer_parameter(_SOUND_EFFECT_PARAMETER, _SOUND_EFFECT_CHIRP)

    def play_tone(self, pitch: float) -> None:
        """Play a steady tone at `pitch` (ADR-0053)."""
        frequency = sound_frequency_from_pitch(pitch)
        # The pitch first: the tone plays whatever `sound.freq` holds when it starts.
        self._write_buzzer_parameter(_SOUND_FREQUENCY_PARAMETER, frequency)
        self._write_buzzer_parameter(_SOUND_EFFECT_PARAMETER, _SOUND_EFFECT_TONE)

    def silence(self) -> None:
        """Stop any sound (ADR-0053)."""
        self._write_buzzer_parameter(_SOUND_EFFECT_PARAMETER, _SOUND_EFFECT_OFF)

    def silence_at_disconnect(self) -> bool:
        """Silence the buzzer (ADR-0085). Returns whether the write was queued: one that fails gets a warning."""
        crazyflie = self._current_crazyflie()
        try:
            crazyflie.param.set_value(_SOUND_EFFECT_PARAMETER, _SOUND_EFFECT_OFF)
        except KeyError:
            # Once the link is lost, cflib forgets the parameter list and a write raises.
            # The firmware may also lack it without a Buzzer deck: not checked (backlog #136).
            if crazyflie.link is None:
                logger.warning("Buzzer not silenced: the link is closed.")
            else:
                logger.warning("Buzzer not silenced: the drone has no %s parameter.", _SOUND_EFFECT_PARAMETER)
            return False
        return True

    def _write_buzzer_parameter(self, name: str, value: int) -> None:
        """Queue one parameter write, or skip it with a warning while the link is closed (ADR-0053)."""
        crazyflie = self._current_crazyflie()
        # Once the link is lost, cflib forgets the parameter list and a write raises, while a
        # movement command is only dropped.
        if crazyflie.link is None:
            if not self._is_skipping_buzzer_commands:
                logger.warning("Buzzer command not sent: the link is closed. Warned once per streak.")
                self._is_skipping_buzzer_commands = True
            return
        self._is_skipping_buzzer_commands = False  # this write goes through: the streak is over
        crazyflie.param.set_value(name, value)

    # --- Estimate -------------------------------------------------------------

    def send_estimate_reset(self) -> None:
        """Write the reset without waiting (ADR-0054), then log the estimate it erases (ADR-0020)."""
        crazyflie = self._current_crazyflie()
        # Once the link is lost, cflib forgets the parameter list and a write raises.
        if crazyflie.link is None:
            logger.warning("Estimate reset not sent: the link is closed.")
            return
        # Read before the write: telemetry that arrives after it may already show the reset.
        telemetry = self._current_telemetry()
        position = telemetry.latest_position_estimate()
        velocity = telemetry.latest_velocity_estimate()
        try:
            crazyflie.param.set_value(_RESET_ESTIMATE_PARAMETER, 1)
        except (KeyError, AttributeError):
            # The link can be lost after the check above. The drone is on the floor, so carry on (ADR-0020).
            cause = "the link is closed" if crazyflie.link is None else "the firmware can't write it"
            logger.warning("Estimate reset not sent: %s.", cause)
            return
        self._log_estimate_before_reset(position, velocity)

    def _log_estimate_before_reset(self, position: Stamped[Vector3] | None, velocity: Stamped[Vector3] | None) -> None:
        if position is None or velocity is None:
            logger.info("Estimate reset, with no estimate before it.")
            return
        p, v = position.value, velocity.value
        speed = math.hypot(v.x, v.y)
        # The comparison is false for NaN too: an estimate that isn't finite is implausible.
        is_plausible = speed < FLOOR_MAX_SPEED
        logger.log(
            logging.INFO if is_plausible else logging.WARNING,
            "Estimate reset. Before it: position (%.3f, %.3f, %.3f) m, velocity (%.3f, %.3f, %.3f) m/s%s",
            p.x,
            p.y,
            p.z,
            v.x,
            v.y,
            v.z,
            "" if is_plausible else f": implausible on the floor, the speed must be under {FLOOR_MAX_SPEED:g} m/s",
        )


def land_as_a_last_resort(
    current_crazyflie: Callable[[], Crazyflie],
    duration: float,
    clock: Clock,
    close_radio_link_only: Callable[[], None],
) -> None:
    """The last-resort landing (ADR-0084): the firmware's land, the release, a wait with the link open, then
    the radio link closes. It reads no telemetry and no landing state, and logs its errors instead of
    raising them. It blocks, so only `disconnect()` may run it.

    `duration`: seconds, for the firmware's land and for the wait.
    """
    logger.critical("Our landing failed: sending the firmware's land as a last resort.")
    try:
        crazyflie = current_crazyflie()
        crazyflie.high_level_commander.land(0.0, duration)
    except Exception:
        logger.exception(
            "The last-resort landing wasn't sent. "
            "Run the rescue landing, or tools/emergency_stop.py with something soft under the drone."
        )
    else:
        try:
            # Released before the land, the firmware's motors-off setpoint would get through first (ADR-0084).
            crazyflie.commander.send_notify_setpoint_stop()
        except Exception:
            logger.exception(
                "The last-resort landing was sent, but the setpoint priority wasn't released. "
                "Run the rescue landing, or tools/emergency_stop.py with something soft under the drone."
            )
        # Closing the link throws away packets not yet sent, so wait with it open (ADR-0084).
        clock.sleep_until(clock.now() + duration)
    try:
        close_radio_link_only()
    except Exception:
        logger.exception("Closing the radio link after the last-resort landing failed")
