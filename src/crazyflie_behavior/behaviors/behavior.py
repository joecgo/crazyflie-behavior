"""What every behavior implements.

A behavior reads the tick's snapshot and makes command requests, which the
safety layer answers at once (ADR-0025). It never commands the drone itself:
only the safety layer does (ADR-0008).
"""

from abc import ABC, abstractmethod
from collections.abc import Callable

from crazyflie_behavior.safety.requests import CommandRequest, Verdict
from crazyflie_behavior.snapshot import Snapshot


class Behavior(ABC):
    """Decision-making logic, run once per tick while the safety pre-check passes."""

    @abstractmethod
    def tick(self, snapshot: Snapshot, ask_safety_layer: Callable[[CommandRequest], Verdict]) -> bool:
        """Decide this tick, making command requests through `ask_safety_layer`. Returns True when done.

        Only runs after the safety pre-check passed, so every value the safety
        pre-check checks is present and fresh, and the position estimate and
        battery voltage are finite (see `safety_pre_check`).
        """
