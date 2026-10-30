"""Command requests and verdicts: how behaviors ask the safety layer to command the drone.

A behavior makes a command request; the safety layer answers it at once with
a verdict (ADR-0025) and is the only code that sends commands (ADR-0008).
Behaviors import this module, never the safety layer itself.

First flight approves arm, take off, hover and land (ADR-0030). Velocity and
fast-mode requests are always refused until the speed envelope exists
(backlog #30).
"""

import math
from dataclasses import dataclass

from crazyflie_behavior.geometry import Vector3


@dataclass(frozen=True, slots=True)
class Arm:
    """Enable the motors."""


@dataclass(frozen=True, slots=True)
class TakeOff:
    """Rise straight up to `height` and hover."""

    height: float
    """Meters."""

    def __post_init__(self) -> None:
        if not (math.isfinite(self.height) and self.height > 0.0):
            raise ValueError(f"Take-off height must be positive: {self.height}")


@dataclass(frozen=True, slots=True)
class Hover:
    """Stop and hold the current position."""


@dataclass(frozen=True, slots=True)
class Land:
    """Descend straight down, then stop the motors."""


@dataclass(frozen=True, slots=True)
class SetVelocity:
    """Steering mode (ADR-0005). Always refused until the speed envelope exists."""

    velocity: Vector3
    """World frame, meters per second."""


@dataclass(frozen=True, slots=True)
class MoveTo:
    """Fast mode (ADR-0005). Always refused until the speed envelope exists."""

    position: Vector3
    """World frame, meters."""
    duration: float
    """Seconds."""


type CommandRequest = Arm | TakeOff | Hover | Land | SetVelocity | MoveTo
"""What a behavior can ask the drone to do (glossary: Command request)."""


@dataclass(frozen=True, slots=True)
class Verdict:
    """The safety layer's answer to a command request (glossary: Verdict).

    Approved means the safety layer accepted the request, not that the drone
    did it: what happens shows up in later snapshots (ADR-0025). Nothing is
    clamped yet: that comes with the speed envelope (backlog #30).
    """

    is_approved: bool
    reason: str
    """Why the request was refused. Empty when approved."""

    @classmethod
    def approved(cls) -> "Verdict":
        return cls(is_approved=True, reason="")

    @classmethod
    def refused(cls, reason: str) -> "Verdict":
        return cls(is_approved=False, reason=reason)
