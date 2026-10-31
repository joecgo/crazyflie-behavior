"""The drone interface: how the safety layer commands a drone (ADR-0008).

Only the safety layer (commands) and the tick loop (snapshots) use this.
Behaviors never do: they send command requests to the safety layer.

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
        the first snapshot has nothing missing (ADR-0031).
        """

    @abstractmethod
    def disconnect(self) -> None:
        """Leave the drone on the ground with motors stopped, then close the link.

        If the drone is flying, it lands first. Unlike the other commands this
        may block, because it's only used at shutdown.
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
        """Stop and hold the current position."""

    @abstractmethod
    def emergency_stop(self) -> None:
        """Cut the motors immediately. The drone falls. Critical faults only."""

    @abstractmethod
    def take_snapshot(self, time: float, dt: float) -> Snapshot:
        """Called once per tick by the tick loop: return this tick's snapshot.

        Adapters may also use this call to advance their own pending work,
        e.g. the mock adapter moves its fake drone forward by `dt`.
        """
