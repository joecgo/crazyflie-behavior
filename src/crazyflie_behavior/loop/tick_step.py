"""The tick step for flying (ADR-0026): snapshot, safety pre-check, behavior, send."""

import logging

from crazyflie_behavior.behaviors.behavior import Behavior
from crazyflie_behavior.drone.interface import DroneInterface
from crazyflie_behavior.loop.tick_loop import TickStep
from crazyflie_behavior.safety.safety_layer import SafetyLayer

logger = logging.getLogger(__name__)


class BehaviorTickStep(TickStep):
    """One tick, always in the same order (ADR-0025, ADR-0026).

    1. Snapshot.
    2. Safety pre-check. If it fails, the behavior is skipped and the
       failsafe takes the movement slot.
    3. The behavior makes command requests, each answered at once.
    4. Send: the movement slot's command goes to the drone.

    Done when the behavior is, or when the safety pre-check has failed, which
    ends the flight. Leaving the tick loop then disconnects, which finishes a
    landing under way (ADR-0026).
    """

    def __init__(
        self, drone: DroneInterface, safety_layer: SafetyLayer, behavior: Behavior
    ) -> None:
        self._drone = drone
        self._safety_layer = safety_layer
        self._behavior = behavior

    def run(self, time: float, dt: float) -> bool:
        snapshot = self._drone.take_snapshot(time, dt)
        logger.debug("Snapshot: %s", snapshot)
        behavior_is_done = False
        if self._safety_layer.pre_check(snapshot):
            behavior_is_done = self._behavior.tick(snapshot, self._safety_layer.request)
        self._safety_layer.send()
        return behavior_is_done or self._safety_layer.flight_is_over
