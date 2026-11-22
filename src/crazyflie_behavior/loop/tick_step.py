"""The tick step for flying (ADR-0026, ADR-0055): snapshot, safety pre-check, take-off and landing, behavior, send."""

import logging

from crazyflie_behavior.behaviors.behavior import Behavior
from crazyflie_behavior.drone.interface import DroneInterface
from crazyflie_behavior.loop.tick_loop import TickStep
from crazyflie_behavior.safety.safety_layer import FlightEnd, SafetyLayer

logger = logging.getLogger(__name__)

# --- PLACEHOLDER, NOT A DECISION (ADR-0083) ------------------------------------
FLIGHT_END_TIME_LIMIT = 60.0
"""Seconds from the flight end until a drone that may still be flying is an error, which `disconnect()` lands."""
# ------------------------------------------------------------------------------


class BehaviorTickStep(TickStep):
    """One tick, always in the same order (ADR-0025, ADR-0026, ADR-0055).

    1. Snapshot.
    2. Safety pre-check. If it fails, the behavior is skipped and the
       failsafe takes over.
    3. The drone updates a take-off or landing under way. Always, a failed
       pre-check too: the level parts' setpoint stream must not stop.
    4. The behavior makes command requests, each answered at once.
    5. Send: the safety layer sends this tick's commands.

    Done when the behavior is, on the floor. After the flight end (a failed
    pre-check, a stop request, or the behavior done while the drone may be
    flying) the behavior is skipped and the ticks go on until a snapshot says
    the drone isn't flying, so the landing runs inside the tick loop (ADR-0083).
    """

    def __init__(self, drone: DroneInterface, safety_layer: SafetyLayer, behavior: Behavior) -> None:
        self._drone = drone
        self._safety_layer = safety_layer
        self._behavior = behavior
        self._flight_ended_at: float | None = None
        """The snapshot time the flight end's time limit counts from: its first tick with the drone that may be
        flying."""

    def request_stop(self) -> None:
        """Sets the flight end: a flying drone lands inside the tick loop (ADR-0083)."""
        self._safety_layer.end_flight(FlightEnd.STOP_REQUEST)

    def run(self, time: float, dt: float) -> bool:
        snapshot = self._drone.take_snapshot(dt)
        logger.debug("Snapshot: %s", snapshot)
        behavior_may_run = self._safety_layer.pre_check(snapshot)
        self._drone.update_take_off_and_landing(snapshot)
        behavior_is_done = False
        if behavior_may_run:
            behavior_is_done = self._behavior.tick(snapshot, self._safety_layer.request)
            if behavior_is_done and snapshot.may_be_flying:
                self._safety_layer.end_flight(FlightEnd.BEHAVIOR_DONE_IN_FLIGHT)
        self._safety_layer.send()
        if self._safety_layer.flight_end is None:
            return behavior_is_done
        if not snapshot.may_be_flying:
            return True
        self._check_the_flight_end_time_limit(snapshot.time)
        return False

    def _check_the_flight_end_time_limit(self, snapshot_time: float) -> None:
        """Raises once `FLIGHT_END_TIME_LIMIT` has passed. The first call starts it."""
        if self._flight_ended_at is None:
            self._flight_ended_at = snapshot_time
        if snapshot_time - self._flight_ended_at >= FLIGHT_END_TIME_LIMIT:
            raise TimeoutError(
                f"The drone may still be flying {FLIGHT_END_TIME_LIMIT:g} s after the flight end: "
                "landing it while disconnecting."
            )
