"""Command requests and verdicts: how behaviors ask the safety layer to command the drone.

A behavior makes a command request; the safety layer answers it at once with
a verdict (ADR-0025) and is the only code that sends commands (ADR-0008).
Behaviors import this module, never the safety layer itself.

The safety layer approves only arm, take off, hover and land (ADR-0030), and
the buzzer requests: chirp, tone and silence (ADR-0053).
TODO: it refuses velocity and fast-mode requests until the speed envelope
exists (backlog #30).
"""

import math
from dataclasses import dataclass

from crazyflie_behavior.geometry import Vector3

MIN_TONE_PITCH = 20.0
"""Hertz. The lowest pitch people hear."""
MAX_TONE_PITCH = 20_000.0
"""Hertz. The highest pitch people hear."""


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
    """Steering mode (ADR-0005). TODO: always refused until the speed envelope exists."""

    velocity: Vector3
    """World frame, meters per second."""


@dataclass(frozen=True, slots=True)
class MoveTo:
    """Fast mode (ADR-0005). TODO: always refused until the speed envelope exists."""

    position: Vector3
    """World frame, meters."""
    duration: float
    """Seconds."""


@dataclass(frozen=True, slots=True)
class Chirp:
    """One chirp from the buzzer: a short sound that stops by itself (ADR-0053)."""


@dataclass(frozen=True, slots=True)
class Tone:
    """A steady tone from the buzzer at `pitch`, until a silence (ADR-0053)."""

    pitch: float
    """Hertz."""

    def __post_init__(self) -> None:
        # The comparison is false for NaN too.
        if not MIN_TONE_PITCH <= self.pitch <= MAX_TONE_PITCH:
            raise ValueError(f"Tone pitch must be {MIN_TONE_PITCH:g}-{MAX_TONE_PITCH:g} Hz: {self.pitch}")


@dataclass(frozen=True, slots=True)
class Silence:
    """Stop the buzzer (ADR-0053)."""


type MovementRequest = Arm | TakeOff | Hover | Land | SetVelocity | MoveTo
"""The command requests that share the movement slot (ADR-0025)."""

type BuzzerRequest = Chirp | Tone | Silence
"""The command requests that share the buzzer slot (ADR-0025, ADR-0053)."""

type CommandRequest = MovementRequest | BuzzerRequest
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

    def __post_init__(self) -> None:
        if not self.is_approved and not self.reason:
            raise ValueError("A refused verdict needs a reason")
        if self.is_approved and self.reason:
            raise ValueError(f"An approved verdict has no reason: {self.reason}")

    @classmethod
    def approved(cls) -> "Verdict":
        return cls(is_approved=True, reason="")

    @classmethod
    def refused(cls, reason: str) -> "Verdict":
        return cls(is_approved=False, reason=reason)
