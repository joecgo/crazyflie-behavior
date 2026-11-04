"""The fault the failsafe program injects (ADR-0041): a forged low battery.

A wrapper around a drone. It hands the safety layer the real snapshot until the
drone has hovered for a while, then the same snapshot with the battery voltage
replaced by one below the safety pre-check's limit, so the real pre-check fails
and the real failsafe lands the drone. Every other field stays real, down range
included: the landing uses it for touchdown (ADR-0032). Everything else is
delegated to the real drone.

Only the failsafe program uses this. A fitness function keeps everything else
from importing it (ADR-0041): the fault must be unreachable from a game
program or a behavior, and never on by default.
"""

import logging
from dataclasses import replace

from crazyflie_behavior.behaviors.failsafe_test import is_at_take_off_height
from crazyflie_behavior.drone.interface import DroneInterface
from crazyflie_behavior.geometry import Vector3
from crazyflie_behavior.safety.safety_layer import LOW_BATTERY_VOLTAGE
from crazyflie_behavior.snapshot import Snapshot

logger = logging.getLogger(__name__)

# --- PLACEHOLDERS, NOT DECISIONS: tune in the Failsafe low and Failsafe high field tests ---
HOVER_DURATION_BEFORE_FAULT = 3.0
"""Seconds the drone hovers at the take-off height before the battery voltage is forged."""
FORGED_BATTERY_VOLTAGE = LOW_BATTERY_VOLTAGE - 0.2
"""Volts. Below the safety pre-check's limit."""
# ------------------------------------------------------------------------------------------


class ForgedLowBatteryDrone(DroneInterface):
    """Passes everything to a real drone, but forges a low battery after a hover of a few seconds."""

    def __init__(self, drone: DroneInterface, hover_duration_before_fault: float | None = None) -> None:
        """`hover_duration_before_fault`: seconds; None means `HOVER_DURATION_BEFORE_FAULT`."""
        self._drone = drone
        self._hover_duration_before_fault = (
            HOVER_DURATION_BEFORE_FAULT if hover_duration_before_fault is None else hover_duration_before_fault
        )
        self._take_off_height: float | None = None
        """The height of the latest take-off sent."""
        self._hover_started_at: float | None = None
        """The snapshot time of the first snapshot that showed the drone hovering at the take-off height."""
        self._has_forged = False

    @property
    def has_forged_battery_voltage(self) -> bool:
        """Whether the fault has been injected: some snapshot went out with a forged battery voltage."""
        return self._has_forged

    def take_snapshot(self, dt: float) -> Snapshot:
        snapshot = self._drone.take_snapshot(dt)
        if self._hover_started_at is None and self._is_hovering(snapshot):
            self._hover_started_at = snapshot.time
        if self._hover_started_at is None or snapshot.time - self._hover_started_at < self._hover_duration_before_fault:
            return snapshot
        battery_voltage = snapshot.battery_voltage
        if battery_voltage is None:
            return snapshot  # nothing to forge: the pre-check fails on its own without a battery voltage
        if not self._has_forged:
            logger.warning("FAULT INJECTED: battery voltage forged")
            self._has_forged = True
        # The snapshot is frozen: this is a copy with one value replaced, keeping the real timestamps.
        return replace(snapshot, battery_voltage=replace(battery_voltage, value=FORGED_BATTERY_VOLTAGE))

    def _is_hovering(self, snapshot: Snapshot) -> bool:
        status = snapshot.drone_status
        position = snapshot.position_estimate
        if self._take_off_height is None or status is None or position is None:
            return False
        return status.value.is_flying and is_at_take_off_height(position.value.z, self._take_off_height)

    # --- Everything else goes to the real drone, unchanged -----------------------------

    def connect(self) -> None:
        self._drone.connect()

    def disconnect(self) -> None:
        self._drone.disconnect()

    def arm(self) -> None:
        self._drone.arm()

    def disarm(self) -> None:
        self._drone.disarm()

    def take_off(self, height: float) -> None:
        self._take_off_height = height
        self._drone.take_off(height)

    def land(self) -> None:
        self._drone.land()

    def set_velocity(self, velocity: Vector3, yaw_rate_rad_per_s: float = 0.0) -> None:
        self._drone.set_velocity(velocity, yaw_rate_rad_per_s)

    def move_to(self, position: Vector3, duration: float) -> None:
        self._drone.move_to(position, duration)

    def hover(self) -> None:
        self._drone.hover()

    def emergency_stop(self) -> None:
        self._drone.emergency_stop()
