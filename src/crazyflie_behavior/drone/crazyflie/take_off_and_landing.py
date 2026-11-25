"""Take-off and landing for the Crazyflie adapter: the initial climb, the landing approach, the final descent and
"may be flying" (ADR-0012, ADR-0019, ADR-0048, ADR-0049).

It sends through `FlightCommands`, which the adapter's commands part satisfies, so it never imports cflib (ADR-0093).
"""

import logging
import math
from collections.abc import Callable
from enum import Enum
from typing import Protocol

from crazyflie_behavior.drone.crazyflie.bad_flow_zone import (
    FINAL_DESCENT_HEIGHT,
    FINAL_DESCENT_SPEED,
    INITIAL_CLIMB_SPEED,
    INITIAL_CLIMB_TIME_LIMIT,
    has_fresh_flow,
)
from crazyflie_behavior.drone.crazyflie.conversions import move_duration
from crazyflie_behavior.drone.crazyflie.touchdown import (
    HEIGHT_IF_UNKNOWN,
    SLOW_DESCENT_SPEED,
    TouchdownDetector,
    final_descent_deadline,
    fresh_down_distance,
)
from crazyflie_behavior.drone.interface import STALE_AFTER
from crazyflie_behavior.drone.telemetry_buffer import TelemetryBuffer
from crazyflie_behavior.geometry import Vector3
from crazyflie_behavior.snapshot import Snapshot, Stamped
from crazyflie_behavior.timing.clock import Clock

logger = logging.getLogger(__name__)

LANDING_APPROACH_AIM_BELOW = 0.05
"""How far below the final descent height the landing approach aims, in meters (ADR-0068)."""
LANDING_APPROACH_BACKUP = 1.0
"""Seconds after the landing approach's `go_to` ends before the final descent starts anyway, if
the down range hasn't started it (ADR-0068)."""

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
# ------------------------------------------------------------------------------


class _LandingPhase(Enum):
    """Where a landing is (ADR-0012, ADR-0019, ADR-0048)."""

    NOT_LANDING = "not_landing"
    """No landing under way."""
    LANDING_APPROACH = "landing_approach"
    """A high-level move down to the final descent height."""
    FINAL_DESCENT = "final_descent"
    """Down through the bad-flow zone until touchdown: level, or slowly by the high-level
    commander when the down range isn't usable."""


class FlightCommands(Protocol):
    """The sends take-off and landing makes. The adapter's `CrazyflieCommands` satisfies it (ADR-0093)."""

    def send_level_setpoint(self, vertical_speed: float) -> None: ...

    def go_to(self, position: Vector3, duration: float) -> None: ...

    def go_to_relative(self, offset: Vector3, duration: float, *, linear: bool = False) -> None: ...

    def stop_motors(self) -> None: ...

    def emergency_stop(self) -> None: ...


class TakeOffAndLanding:
    """Take-off and landing, moved on by one tick at each `update` (ADR-0055).

    Looks up the telemetry buffer on every call, since `connect()` replaces it (ADR-0093). Takes its snapshots through
    the adapter's `take_snapshot`, which raises after a lost link (ADR-0084).
    """

    def __init__(
        self,
        clock: Clock,
        commands: FlightCommands,
        current_telemetry: Callable[[], TelemetryBuffer],
        take_snapshot: Callable[[float], Snapshot],
    ) -> None:
        self._clock = clock
        self._commands = commands
        self._current_telemetry = current_telemetry
        self._take_snapshot = take_snapshot
        self._is_airborne = False
        self._has_stopped_motors = False
        self._take_off_sent_at = 0.0
        """When the latest take-off was sent. Meaningful while airborne."""
        self._is_in_initial_climb = False
        self._take_off_height = 0.0
        """Meters: the latest take-off's target. Meaningful during the initial climb."""
        self._is_ignoring_commands = False
        """The latest command was ignored while crossing the bad-flow zone: the log line for it comes
        once per streak."""
        self._landing_phase = _LandingPhase.NOT_LANDING
        self._landing_approach_ends_at = 0.0
        """When the landing approach ends if the down range hasn't ended it: its backup (ADR-0068).
        Meaningful while LANDING_APPROACH."""
        self._is_final_descent_level = False
        """Meaningful while FINAL_DESCENT: level on the down range, or the slow high-level descent."""
        self._final_descent_deadline = 0.0
        """When the final descent must be over. Meaningful while FINAL_DESCENT."""
        self._touchdown_detector = TouchdownDetector()

    # --- What the adapter reads ---------------------------------------------

    @property
    def is_airborne(self) -> bool:
        """A take-off was sent (or the flight was taken over) and the motors haven't been stopped since."""
        return self._is_airborne

    @property
    def has_stopped_motors(self) -> bool:
        """A motor stop was sent this session, so closing the link waits for not flying (ADR-0058)."""
        return self._has_stopped_motors

    @property
    def is_in_initial_climb(self) -> bool:
        """In the initial climb: level through the bad-flow zone, at the start of a take-off (ADR-0048)."""
        return self._is_in_initial_climb

    def may_be_flying(self) -> bool:
        """Whether the drone may be in the air, so stopping it needs a landing (ADR-0032).

        - No take-off sent since our last motor stop: not flying. The drone
          status can't be trusted here, because after the motors stop it keeps
          saying flying for 2 s.
        - Otherwise, flying if the status is missing, older than
          `STALE_AFTER`, or says flying. When unsure, say flying: a landing
          sent to a drone already down only runs the motors until touchdown is
          confirmed, while stopping the motors of a flying drone drops it.
        - Otherwise (a fresh status says not flying), still flying for
          `TAKE_OFF_STATUS_GRACE` after the take-off was sent, because the
          status shows a take-off only after a short delay.
        """
        if not self._is_airborne:
            return False
        now = self._clock.now()
        status = self._current_telemetry().latest_drone_status()
        if status is None or status.age(now) > STALE_AFTER or status.value.is_flying:
            return True
        return now - self._take_off_sent_at < TAKE_OFF_STATUS_GRACE

    # --- Commands -----------------------------------------------------------

    def take_off(self, height: float, log_take_off_warnings: Callable[[], None]) -> bool:
        """Take off to `height`, or move straight to it if the drone may already be flying. Returns whether it was
        sent: not while crossing the bad-flow zone (ADR-0056). `log_take_off_warnings` runs just before an initial
        climb starts."""
        if self.is_ignored_while_crossing_the_bad_flow_zone("Take-off"):
            return False
        if self.may_be_flying():
            # Already in the air, above the bad-flow zone: no initial climb.
            self.cancel_landing()
            self._go_to_height(height)
        else:
            log_take_off_warnings()
            self._start_initial_climb(height)
        self._is_airborne = True
        self._take_off_sent_at = self._clock.now()
        return True

    def land(self) -> None:
        """Start a landing, or only stop the motors of a drone that isn't flying (ADR-0032)."""
        if not self.may_be_flying():
            # On the floor, a move down would spin an armed drone's motors up
            # (ADR-0032), so just make sure they're stopped.
            self.stop_motors()
        elif self._is_in_initial_climb:
            # No landing approach during the initial climb (ADR-0049, ADR-0077).
            logger.info("Landing during the initial climb: no landing approach.")
            self._is_in_initial_climb = False
            self._start_final_descent(self._latest_fresh_down_distance())
        elif self._landing_phase is _LandingPhase.NOT_LANDING:
            self._start_landing_approach()
        # Otherwise already landing: a new landing approach could climb back up (ADR-0056).

    def update(self, snapshot: Snapshot) -> None:
        """Move a take-off or landing under way on by one tick (ADR-0055)."""
        if self._is_in_initial_climb:
            self._update_initial_climb(snapshot)
        else:
            self._update_landing(snapshot)

    def stop_motors(self) -> None:
        """Stop the motors and clear the flight state together: a stop that left the state would leave "may be
        flying" true (ADR-0093)."""
        self._commands.stop_motors()
        self._has_stopped_motors = True
        self._is_airborne = False
        self._is_in_initial_climb = False
        self.cancel_landing()

    def emergency_stop(self) -> None:
        """Cut the motors at once and clear the flight state, as `stop_motors` does, but record no motor stop: the
        emergency stop locks the drone on purpose (ADR-0058)."""
        self._commands.emergency_stop()
        self._is_airborne = False
        self._is_in_initial_climb = False
        self.cancel_landing()

    def take_over_flight(self) -> None:
        """Treat the drone as airborne, as if this adapter had sent its take-off (ADR-0038)."""
        self._is_airborne = True
        # No take-off of ours, so no status lag to wait out: the status just read is the truth. A land
        # request for a drone that reports it's on the floor then only stops the motors (ADR-0039).
        self._take_off_sent_at = -math.inf

    def cancel_landing(self) -> None:
        """Forget any landing under way."""
        self._landing_phase = _LandingPhase.NOT_LANDING
        self._is_final_descent_level = False

    def is_ignored_while_crossing_the_bad_flow_zone(self, command: str) -> bool:
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

    def land_and_wait_for_touchdown(self) -> None:
        """Land, or finish a take-off or landing under way, and block until the motors are stopped. It blocks, so
        only `disconnect()` may run it.

        Updates every TOUCHDOWN_POLL_PERIOD from the start, so a level setpoint stream keeps going.
        """
        self.land()
        while self._landing_phase is not _LandingPhase.NOT_LANDING:
            self._clock.sleep_until(self._clock.now() + TOUCHDOWN_POLL_PERIOD)
            self._update_landing(self._take_snapshot(0.0))

    # --- Internals ----------------------------------------------------------

    def _go_to_height(self, height: float) -> None:
        """A high-level move straight up or down to `height`, at the estimated x and y (ADR-0048)."""
        position_estimate = self._current_telemetry().latest_position_estimate()
        if position_estimate is None:
            # No estimate yet, which connect() rules out (ADR-0031): hold where it is.
            self._commands.go_to_relative(Vector3.ZERO, HOVER_SETTLE_DURATION)
            return
        here = position_estimate.value
        duration = move_duration(height - here.z, VERTICAL_SPEED, MIN_MOVE_DURATION)
        self._commands.go_to(Vector3(here.x, here.y, height), duration)

    def _start_initial_climb(self, height: float) -> None:
        """Start climbing level through the bad-flow zone (ADR-0048). The first setpoint goes out at once."""
        self.cancel_landing()
        self._is_in_initial_climb = True
        self._is_ignoring_commands = False  # a new crossing: a new streak
        self._take_off_height = height
        # A landing during the climb sets its final descent's time limit from these readings (ADR-0049).
        self._touchdown_detector = TouchdownDetector()
        logger.info("Initial climb at %g m/s.", INITIAL_CLIMB_SPEED)
        self._commands.send_level_setpoint(INITIAL_CLIMB_SPEED)

    def _update_initial_climb(self, snapshot: Snapshot) -> None:
        now = self._clock.now()
        self._touchdown_detector.observe(snapshot, now)
        if now - self._take_off_sent_at >= INITIAL_CLIMB_TIME_LIMIT:
            logger.warning("The initial climb hasn't ended %g s after the take-off. Landing.", INITIAL_CLIMB_TIME_LIMIT)
            self.land()
            return
        down = fresh_down_distance(snapshot, now)
        if down is None or not math.isfinite(down.value) or down.value < FINAL_DESCENT_HEIGHT:
            self._commands.send_level_setpoint(INITIAL_CLIMB_SPEED)
        elif has_fresh_flow(snapshot, now):
            self._end_initial_climb(down.value)
        else:
            uncertainty = snapshot.velocity_uncertainty
            if uncertainty is not None and uncertainty.age(now) > STALE_AFTER:
                # An old reading may be a telemetry stall, not darkness.
                logger.warning(
                    "The velocity uncertainty is %.2f s old at the end of the initial climb. Landing.",
                    uncertainty.age(now),
                )
            else:
                logger.warning(
                    "No flow at the end of the initial climb, %.3f m by the down range "
                    "(velocity uncertainty %s). Landing.",
                    down.value,
                    "missing" if uncertainty is None else f"{uncertainty.value:.3f} m/s",
                )
            self.land()

    def _end_initial_climb(self, down_distance: float) -> None:
        """Hand over to a high-level climb to the take-off height, at the current x and y (ADR-0048, ADR-0077)."""
        self._is_in_initial_climb = False
        logger.info(
            "Initial climb done at %.3f m by the down range. Climbing to %.2f m.", down_distance, self._take_off_height
        )
        self._go_to_height(self._take_off_height)

    def _start_landing_approach(self) -> None:
        """A high-level move aimed below the final descent height, or the final descent at once if already there."""
        self._touchdown_detector = TouchdownDetector()
        down = self._latest_fresh_down_distance()
        if down is not None and down.value <= FINAL_DESCENT_HEIGHT:
            self._start_final_descent(down)
            return
        # A go_to, not the firmware's landing, which switches the motors off when it
        # ends, even above the floor (ADR-0032).
        position_estimate = self._current_telemetry().latest_position_estimate()
        if position_estimate is None:
            # No estimate yet: straight down from the commander's own position, until the
            # down range reaches the final descent height.
            duration = move_duration(HEIGHT_IF_UNKNOWN, VERTICAL_SPEED, MIN_MOVE_DURATION)
            self._commands.go_to_relative(Vector3(0.0, 0.0, -HEIGHT_IF_UNKNOWN), duration)
        else:
            here = position_estimate.value
            height = min(here.z, FINAL_DESCENT_HEIGHT - LANDING_APPROACH_AIM_BELOW)
            duration = move_duration(here.z - height, VERTICAL_SPEED, MIN_MOVE_DURATION)
            self._commands.go_to(Vector3(here.x, here.y, height), duration)
        # The drone trails the `go_to`, so the down range, not the `go_to`'s end, should start
        # the final descent (ADR-0068).
        self._landing_approach_ends_at = self._clock.now() + duration + LANDING_APPROACH_BACKUP
        self._landing_phase = _LandingPhase.LANDING_APPROACH

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
                if down is not None and down.value <= FINAL_DESCENT_HEIGHT:
                    self._start_final_descent(down)
                elif now >= self._landing_approach_ends_at:
                    logger.warning(
                        "The down range hasn't reached the final descent height %g s after the "
                        "landing approach's go_to ended. Starting the final descent.",
                        LANDING_APPROACH_BACKUP,
                    )
                    self._start_final_descent(down)
            case _LandingPhase.FINAL_DESCENT:
                if self._touchdown_detector.touchdown_confirmed(now):
                    logger.info("Touchdown confirmed; stopping the motors.")
                    self.stop_motors()
                elif now >= self._final_descent_deadline:
                    logger.warning(
                        "Touchdown never confirmed by the down range; the final descent's "
                        "time limit is up, so the drone must be on the floor. Stopping the motors."
                    )
                    self.stop_motors()
                elif self._is_final_descent_level:
                    self._commands.send_level_setpoint(-FINAL_DESCENT_SPEED)

    def _start_final_descent(self, down: Stamped[float] | None) -> None:
        """Level on a usable down range, else ADR-0019's slow high-level descent (ADR-0048).

        `down`: the latest fresh down range, if any.
        """
        now = self._clock.now()
        if self._touchdown_detector.touchdown_confirmed(now):
            logger.info("Touchdown confirmed; stopping the motors.")
            self.stop_motors()
            return
        self._landing_phase = _LandingPhase.FINAL_DESCENT
        self._is_ignoring_commands = False  # a new crossing: a new streak
        heights = [self._touchdown_detector.highest_recent_distance(), None if down is None else down.value]
        highest = max((height for height in heights if height is not None), default=None)
        if down is not None:
            self._is_final_descent_level = True
            self._final_descent_deadline = final_descent_deadline(now, highest, FINAL_DESCENT_SPEED)
            logger.info("Final descent: level, from %.3f m by the down range.", down.value)
            self._commands.send_level_setpoint(-FINAL_DESCENT_SPEED)
            return
        self._is_final_descent_level = False
        self._final_descent_deadline = final_descent_deadline(now, highest, SLOW_DESCENT_SPEED)
        logger.warning("Final descent without a usable down range: descending slowly.")
        # One high-level move straight down at SLOW_DESCENT_SPEED until the
        # deadline, past the floor if need be. Unlike streamed setpoints, it
        # keeps going if ticks stop (ADR-0011).
        duration = self._final_descent_deadline - now
        self._commands.go_to_relative(Vector3(0.0, 0.0, -SLOW_DESCENT_SPEED * duration), duration, linear=True)

    def _latest_fresh_down_distance(self) -> Stamped[float] | None:
        snapshot = self._take_snapshot(0.0)
        return fresh_down_distance(snapshot, self._clock.now())
