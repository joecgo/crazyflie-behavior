"""The tick step for flying (ADR-0026, ADR-0055): snapshot, safety pre-check, take-off and landing, behavior, send."""

import logging

from crazyflie_behavior.behaviors.behavior import Behavior
from crazyflie_behavior.drone.interface import DroneInterface
from crazyflie_behavior.loop.tick_loop import TickStep
from crazyflie_behavior.safety.safety_layer import SafetyLayer

logger = logging.getLogger(__name__)


class BehaviorTickStep(TickStep):
    """One tick, always in the same order (ADR-0025, ADR-0026, ADR-0055).

    1. Snapshot.
    2. Safety pre-check. If it fails, the behavior is skipped and the
       failsafe takes over.
    3. The drone updates a take-off or landing under way. Always, a failed
       pre-check too: the level parts' setpoint stream must not stop.
    4. The behavior makes command requests, each answered at once.
    5. Send: the safety layer sends this tick's commands.

    Done when the behavior is, or when the safety pre-check has failed, which
    ends the flight. Leaving the tick loop then disconnects, which finishes a
    landing under way (ADR-0026).
    """

    def __init__(self, drone: DroneInterface, safety_layer: SafetyLayer, behavior: Behavior) -> None:
        self._drone = drone
        self._safety_layer = safety_layer
        self._behavior = behavior

    def run(self, time: float, dt: float) -> bool:
        snapshot = self._drone.take_snapshot(dt)
        logger.debug("Snapshot: %s", snapshot)
        behavior_may_run = self._safety_layer.pre_check(snapshot)
        self._drone.update_take_off_and_landing(snapshot)
        behavior_is_done = False
        if behavior_may_run:
            behavior_is_done = self._behavior.tick(snapshot, self._safety_layer.request)
        self._safety_layer.send()
        return behavior_is_done or self._safety_layer.pre_check_has_failed
