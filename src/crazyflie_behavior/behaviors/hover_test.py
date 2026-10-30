"""The hover test (ADR-0030): the behavior for field-test stage 1.

Arm, take off to 0.5 m, hover, land, then report done. Each step waits until
the snapshot shows it happened, because commands take effect after they're
sent (latency), and the waits for arming and taking off have time limits.
"""

import logging
import math
from collections.abc import Callable
from enum import Enum

from crazyflie_behavior.behaviors.behavior import Behavior
from crazyflie_behavior.safety.requests import Arm, CommandRequest, Land, TakeOff, Verdict
from crazyflie_behavior.snapshot import Snapshot

logger = logging.getLogger(__name__)

TAKE_OFF_HEIGHT = 0.5
"""Meters, as field-test stage 1 asks."""
DEFAULT_HOVER_DURATION = 10.0
"""Seconds."""

# --- PLACEHOLDERS, NOT DECISIONS: tune in field-test stage 1 -------------------
HEIGHT_TOLERANCE = 0.1
"""Meters. This close to the take-off height counts as there."""
ARM_TIME_LIMIT = 2.0
"""Seconds for the drone status to show armed."""
TAKE_OFF_TIME_LIMIT = 5.0
"""Seconds to reach the take-off height. The Crazyflie adapter plans the
take-off itself to take about 1.7 s (0.5 m at 0.3 m/s)."""
# ------------------------------------------------------------------------------


class _Step(Enum):
    START = "start"
    ARMING = "arming"
    TAKING_OFF = "taking off"
    HOVERING = "hovering"
    LANDING = "landing"
    DONE = "done"


class HoverTest(Behavior):
    """Arm, take off to 0.5 m, hover, land, then report done."""

    def __init__(self, hover_duration: float = DEFAULT_HOVER_DURATION) -> None:
        """`hover_duration`: seconds to hover once at the take-off height."""
        if not (math.isfinite(hover_duration) and hover_duration >= 0.0):
            raise ValueError(f"Hover duration must be zero or more seconds: {hover_duration}")
        self._hover_duration = hover_duration
        self._step = _Step.START
        self._step_started_at = 0.0
        """The tick time the current step started."""

    def tick(self, snapshot: Snapshot, request: Callable[[CommandRequest], Verdict]) -> bool:
        status = snapshot.drone_status
        position = snapshot.position_estimate
        if status is None or position is None:
            return False  # a passed safety pre-check rules this out
        now = snapshot.time
        time_in_step = now - self._step_started_at
        height = position.value.z
        match self._step:
            case _Step.START:
                if self._is_approved(request, Arm(), now):
                    logger.info("Hover test: arming")
                    self._go_to(_Step.ARMING, now)
            case _Step.ARMING:
                if status.value.is_armed:
                    if self._is_approved(request, TakeOff(TAKE_OFF_HEIGHT), now):
                        logger.info("Hover test: armed. Taking off to %.2f m", TAKE_OFF_HEIGHT)
                        self._go_to(_Step.TAKING_OFF, now)
                elif time_in_step > ARM_TIME_LIMIT:
                    logger.error(
                        "Hover test failed: the drone didn't report armed within %g s",
                        ARM_TIME_LIMIT,
                    )
                    self._go_to(_Step.DONE, now)
            case _Step.TAKING_OFF:
                if abs(height - TAKE_OFF_HEIGHT) <= HEIGHT_TOLERANCE:
                    logger.info(
                        "Hover test: at %.2f m. Hovering for %g s", height, self._hover_duration
                    )
                    self._go_to(_Step.HOVERING, now)
                elif time_in_step > TAKE_OFF_TIME_LIMIT:
                    logger.warning(
                        "Hover test: not at %.2f m after %g s (at %.2f m). Landing.",
                        TAKE_OFF_HEIGHT,
                        TAKE_OFF_TIME_LIMIT,
                        height,
                    )
                    self._land(request, now)
            case _Step.HOVERING:
                if time_in_step >= self._hover_duration:
                    logger.info("Hover test: hovered %g s. Landing.", self._hover_duration)
                    self._land(request, now)
            case _Step.LANDING:
                if not status.value.is_flying:
                    logger.info("Hover test: landed. Done.")
                    self._go_to(_Step.DONE, now)
            case _Step.DONE:
                pass
        return self._step is _Step.DONE

    def _land(self, request: Callable[[CommandRequest], Verdict], now: float) -> None:
        if self._is_approved(request, Land(), now):
            self._go_to(_Step.LANDING, now)

    def _is_approved(
        self,
        request: Callable[[CommandRequest], Verdict],
        command_request: CommandRequest,
        now: float,
    ) -> bool:
        """Make a command request. A refused one ends the hover test."""
        verdict = request(command_request)
        if not verdict.is_approved:
            logger.error("Hover test failed: %s was refused: %s", command_request, verdict.reason)
            self._go_to(_Step.DONE, now)
        return verdict.is_approved

    def _go_to(self, step: _Step, now: float) -> None:
        self._step = step
        self._step_started_at = now
