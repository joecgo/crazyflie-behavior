"""The rescue landing (ADR-0038): land a drone that a lost program left flying.

Asks for a landing once, then waits until the snapshot shows the drone is no
longer flying. The drone was taken over by the adapter, which treats it as
airborne, so the landing is the normal one (ADR-0032).

Failure rule (ADR-0033): the first refused request ends it, and so does its
time limit. Ending lands the drone anyway, since disconnecting finishes or
starts a landing for a drone that may be flying, and every failure is logged
as an error with its reason.
"""

import logging
from collections.abc import Callable

from crazyflie_behavior.behaviors.behavior import Behavior
from crazyflie_behavior.safety.requests import CommandRequest, Land, Verdict
from crazyflie_behavior.snapshot import Snapshot

logger = logging.getLogger(__name__)

# --- PLACEHOLDER, NOT A DECISION: tune in the Bench field test ----------------
LANDING_TIME_LIMIT = 30.0
"""Seconds after the landing was requested that the drone may still report flying."""
# ------------------------------------------------------------------------------


class RescueLanding(Behavior):
    """Request a landing, then report done once the drone says it's no longer flying."""

    def __init__(self) -> None:
        self._landing_requested_at: float | None = None
        self._has_failed = False

    @property
    def has_failed(self) -> bool:
        """Whether the rescue failed by its own rules: a refused landing or the time limit."""
        return self._has_failed

    def tick(self, snapshot: Snapshot, ask_safety_layer: Callable[[CommandRequest], Verdict]) -> bool:
        status = snapshot.drone_status
        if status is None:
            raise RuntimeError("tick ran without a drone status: the safety pre-check should rule this out")
        now = snapshot.time
        if self._landing_requested_at is None:
            verdict = ask_safety_layer(Land())
            if not verdict.is_approved:
                logger.error("Rescue landing failed: Land() was refused: %s", verdict.reason)
                self._has_failed = True
                return True
            logger.info("Rescue landing: landing")
            self._landing_requested_at = now
            return False
        if not status.value.is_flying:
            logger.info("Rescue landing: the drone reports it's no longer flying. Done.")
            return True
        if now - self._landing_requested_at > LANDING_TIME_LIMIT:
            logger.error(
                "Rescue landing failed: the drone still reports flying %g s after the landing was requested",
                LANDING_TIME_LIMIT,
            )
            self._has_failed = True
            return True
        return False
