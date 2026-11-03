"""The failsafe test (ADR-0041): the behavior for the Failsafe low and Failsafe high field tests.

Arm, take off to the height it's given, hover, and wait for the failsafe to
land the drone. The failsafe is the safety layer's: the program forges a low
battery after the drone has hovered a while, the safety pre-check fails, and
the safety layer lands the drone and ends the flight. From then on the safety
layer skips this behavior, so it never sees the landing: it is the tick step
that ends the run (ADR-0026). So the only ways this behavior reports done are
the ways the test failed.

Failure rule (ADR-0033): the first refused request ends the test, since the
basic sequence is what's tested and an unexpected state is the finding. So do
its time limits: arming too slowly ends it at once, a take-off that doesn't
reach the height lands first, and a hover that goes on past `FAULT_TIME_LIMIT`
(the injected fault never took effect) lands the drone normally. Every failure
is logged as an error with its reason and counts in `has_failed`.
"""

import logging
import math
from collections.abc import Callable
from enum import Enum

from crazyflie_behavior.behaviors.behavior import Behavior
from crazyflie_behavior.behaviors.hover_test import ARM_TIME_LIMIT, TAKE_OFF_TIME_LIMIT
from crazyflie_behavior.safety.requests import Arm, CommandRequest, Land, TakeOff, Verdict
from crazyflie_behavior.snapshot import Snapshot

logger = logging.getLogger(__name__)

# --- PLACEHOLDERS, NOT DECISIONS: tune in the Failsafe low and Failsafe high field tests ---
HEIGHT_TOLERANCE_FRACTION = 0.25
"""Of the take-off height: this close to it counts as there. A fraction, not meters,
because the Hover test's 0.1 m would count the floor as being at the 0.1 m height."""
FAULT_TIME_LIMIT = 10.0
"""Seconds of hovering after which the injected fault is taken never to have worked. The
program's wrapper forges the battery after 3 s of hovering (ADR-0041)."""
# ------------------------------------------------------------------------------------------


def is_at_take_off_height(height: float, take_off_height: float) -> bool:
    """Whether `height` is close enough to the `take_off_height` to count as hovering at it (meters)."""
    return abs(height - take_off_height) <= HEIGHT_TOLERANCE_FRACTION * take_off_height


class _Step(Enum):
    START = "start"
    ARMING = "arming"
    TAKING_OFF = "taking off"
    HOVERING = "hovering"
    LANDING = "landing"
    DONE = "done"


class FailsafeTest(Behavior):
    """Arm, take off to a height, hover, and wait for the failsafe to land the drone."""

    def __init__(self, take_off_height: float) -> None:
        """`take_off_height`: meters, the height the failsafe is tested from."""
        if not (math.isfinite(take_off_height) and take_off_height > 0.0):
            raise ValueError(f"Take-off height must be a positive number of meters: {take_off_height}")
        self._take_off_height = take_off_height
        self._step = _Step.START
        self._step_started_at = 0.0
        """The tick time the current step started."""
        self._has_failed = False

    @property
    def has_failed(self) -> bool:
        """Whether the test failed by its own rules: a refused request or a time limit."""
        return self._has_failed

    def tick(self, snapshot: Snapshot, ask_safety_layer: Callable[[CommandRequest], Verdict]) -> bool:
        status = snapshot.drone_status
        position = snapshot.position_estimate
        if status is None or position is None:
            raise RuntimeError("tick ran without a drone status or position: the safety pre-check should rule this out")
        now = snapshot.time
        time_in_step = now - self._step_started_at
        match self._step:
            case _Step.START:
                if self._ask(ask_safety_layer, Arm(), now):
                    logger.info("Failsafe test: arming")
                    self._start_step(_Step.ARMING, now)
            case _Step.ARMING:
                if status.value.is_armed:
                    if self._ask(ask_safety_layer, TakeOff(self._take_off_height), now):
                        logger.info("Failsafe test: armed. Taking off to %.2f m", self._take_off_height)
                        self._start_step(_Step.TAKING_OFF, now)
                elif time_in_step > ARM_TIME_LIMIT:
                    self._fail(f"the drone didn't report armed within {ARM_TIME_LIMIT:g} s", now)
            case _Step.TAKING_OFF:
                height = position.value.z
                if is_at_take_off_height(height, self._take_off_height):
                    logger.info("Failsafe test: at %.2f m. Hovering until the failsafe lands the drone", height)
                    self._start_step(_Step.HOVERING, now)
                elif time_in_step > TAKE_OFF_TIME_LIMIT:
                    self._fail(
                        f"not at {self._take_off_height:.2f} m after {TAKE_OFF_TIME_LIMIT:g} s "
                        f"(at {height:.2f} m). Landing",
                        now,
                    )
                    self._land(ask_safety_layer, now)
            case _Step.HOVERING:
                if time_in_step > FAULT_TIME_LIMIT:
                    self._fail(
                        f"the failsafe didn't land the drone within {FAULT_TIME_LIMIT:g} s of hovering: "
                        "the injected fault never took effect. Landing normally",
                        now,
                    )
                    self._land(ask_safety_layer, now)
            case _Step.LANDING:
                if not status.value.is_flying:
                    logger.info("Failsafe test: landed. Done (the test failed).")
                    self._start_step(_Step.DONE, now)
            case _Step.DONE:
                pass
        return self._step is _Step.DONE

    def _land(self, ask_safety_layer: Callable[[CommandRequest], Verdict], now: float) -> None:
        if self._ask(ask_safety_layer, Land(), now):
            self._start_step(_Step.LANDING, now)

    def _ask(
        self,
        ask_safety_layer: Callable[[CommandRequest], Verdict],
        command_request: CommandRequest,
        now: float,
    ) -> bool:
        """Make a command request; returns whether it was approved. A refused one ends the test."""
        verdict = ask_safety_layer(command_request)
        if not verdict.is_approved:
            self._fail(f"{command_request} was refused: {verdict.reason}", now)
        return verdict.is_approved

    def _fail(self, reason: str, now: float) -> None:
        logger.error("Failsafe test failed: %s", reason)
        self._has_failed = True
        self._start_step(_Step.DONE, now)

    def _start_step(self, step: _Step, now: float) -> None:
        self._step = step
        self._step_started_at = now
