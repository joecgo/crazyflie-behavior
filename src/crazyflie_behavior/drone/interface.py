"""The drone interface: how the safety layer commands a drone (ADR-0008).

The safety layer sends the commands; the tick step takes the snapshots and
updates take-off and landing; a program connects and disconnects. Behaviors never use it:
they send command requests to the safety layer.

Rules every adapter follows:
- Commands are non-blocking (ADR-0003). They start an action and return;
  outcomes show up in later snapshots.
- Positions and velocities are in the world frame, SI units (ADR-0004).
- Yaw is held fixed (ADR-0008).
- Exceptions are for bugs and broken connections, never for normal refusals.
"""

from abc import ABC, abstractmethod
from types import TracebackType
from typing import Self

from crazyflie_behavior.geometry import Vector3
from crazyflie_behavior.snapshot import Snapshot

# PLACEHOLDERS, to verify in flight (ADR-0012, ADR-0054).
TOUCHDOWN_DOWN_RANGE = 0.05
"""Meters. A down range at or below this means the drone is resting on something."""
FLOW_VELOCITY_UNCERTAINTY = 0.03
"""Meters per second. A velocity uncertainty under this means flow is arriving (ADR-0054). In flight,
the safety pre-check's limit grows from this with height (ADR-0064)."""
FLOOR_MAX_SPEED = 0.05
"""Meters per second. A drone on the floor is still, so with flow arriving its horizontal speed
estimate is under this (ADR-0054, ADR-0060)."""


class DroneInterface(ABC):
    """What every adapter implements: the Crazyflie adapter and the mock adapter."""

    def __enter__(self) -> Self:
        self.connect()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        # Runs even when the code inside the `with` block raises, so the
        # drone always ends up on the ground.
        self.disconnect()

    @abstractmethod
    def connect(self) -> None:
        """Open the link and start telemetry. May block while connecting.

        When it returns, every telemetry value has arrived at least once, so
        the first snapshot has nothing missing (ADR-0031). Raises for a drone
        that is already flying, unless the adapter was built to take over its
        flight, as only the rescue landing program does (ADR-0038).
        """

    @abstractmethod
    def disconnect(self) -> None:
        """Leave the drone on the ground with motors stopped, then close the link.

        If the drone may be flying, it lands first. If that landing fails, the
        link is closed without stopping the motors, so a flying drone keeps
        flying: run the rescue landing (ADR-0038). Unlike the other commands
        this may block, because it's only used at shutdown.
        """

    @abstractmethod
    def arm(self) -> None:
        """Enable the motors."""

    @abstractmethod
    def disarm(self) -> None:
        """Disable the motors. In flight, the drone falls."""

    @abstractmethod
    def take_off(self, height: float) -> None:
        """Rise straight up to `height` meters and hover. Requires arming first."""

    @abstractmethod
    def land(self) -> None:
        """Descend straight down, then stop the motors. On the floor, just stop them."""

    @abstractmethod
    def set_velocity(self, velocity: Vector3, yaw_rate_rad_per_s: float = 0.0) -> None:
        """Steering mode (ADR-0005): move at `velocity` meters per second.

        This is a setpoint stream: send it every tick. If it stops, the
        drone stops following it.
        """

    @abstractmethod
    def move_to(self, position: Vector3, duration: float) -> None:
        """Fast mode (ADR-0005): fly a smooth trajectory to `position` in `duration` seconds.

        The drone plans and flies the trajectory itself, so radio latency
        isn't in the loop.
        """

    @abstractmethod
    def hover(self) -> None:
        """Stop and hold the current position.

        Does nothing unless the drone may be flying (the adapter's judgment, which
        says flying when unsure): on the floor, a move to hold the position would
        spin up an armed drone's motors (ADR-0039).
        """

    @abstractmethod
    def emergency_stop(self) -> None:
        """Cut the motors immediately. The drone falls. Critical faults only."""

    @abstractmethod
    def reset_estimate(self) -> None:
        """Estimate reset (ADR-0054): position (0, 0, 0) where the drone sits, velocity zero.

        Doesn't wait for it. Ignored, logged once per streak, while the drone may be flying.
        """

    @abstractmethod
    def chirp(self) -> None:
        """Play one chirp on the buzzer: a short sound that stops by itself (ADR-0053)."""

    @abstractmethod
    def play_tone(self, pitch: float) -> None:
        """Play a steady tone at `pitch` hertz on the buzzer, until `silence()` (ADR-0053)."""

    @abstractmethod
    def silence(self) -> None:
        """Stop the buzzer (ADR-0053)."""

    @abstractmethod
    def take_snapshot(self, dt: float) -> Snapshot:
        """Called once per tick by the tick step: return this tick's snapshot.

        `dt` is the seconds since the previous tick started. The snapshot's time
        comes from the adapter's clock, read after its values are copied (ADR-0046).
        It only copies the telemetry: it sends nothing to the drone (ADR-0055).
        """

    @abstractmethod
    def update_take_off_and_landing(self, snapshot: Snapshot) -> None:
        """Called once per tick by the tick step, after the safety pre-check, even a failed one (ADR-0055).

        Moves a take-off or landing under way on by one tick, deciding from `snapshot`.
        """
