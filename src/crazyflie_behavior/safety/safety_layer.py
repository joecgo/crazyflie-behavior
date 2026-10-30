"""The safety layer, minimal for First flight (ADR-0030).

Each tick, the tick step calls it in this order (ADR-0025):

1. `pre_check`: the safety pre-check on the tick's snapshot. If it fails, the
   failsafe lands the drone and the flight is over.
2. `request`: behaviors' command requests, each judged at once. An approved
   request fills the movement slot.
3. `send`: the movement slot's command goes to the drone.

The pre-check and the judging are plain functions of the snapshot. Only the
SafetyLayer, which sends, holds state. The operator's "land now" and "hover"
(ADR-0027) join the pre-check with the operator controls, not built yet.
"""

import logging

from crazyflie_behavior.drone.interface import DroneInterface
from crazyflie_behavior.safety.requests import (
    Arm,
    CommandRequest,
    Hover,
    Land,
    MoveTo,
    SetVelocity,
    TakeOff,
    Verdict,
)
from crazyflie_behavior.snapshot import Snapshot, Stamped

logger = logging.getLogger(__name__)

# --- PLACEHOLDERS, NOT DECISIONS: measure at the bench (ADR-0030) -------------
STALE_AFTER = 0.25
"""Seconds. The position estimate, drone status and down range stream every
20 ms, so this is about 12 missed values in a row."""
BATTERY_STALE_AFTER = 3.0
"""Seconds. The battery voltage streams once a second."""
LOW_BATTERY_VOLTAGE = 3.4
"""Volts. Land below this: well before the firmware's own handling (low at
3.2 V; at 3.0 V for 5 s it shuts the drone down). A battery reads lower under
load, so this may land a little early, which is the safe direction."""
# ------------------------------------------------------------------------------


def safety_pre_check(snapshot: Snapshot) -> list[str]:
    """The safety pre-check (ADR-0025): why it isn't safe to fly on this snapshot.

    An empty list means it passed. Ages count from the tick's time. A value
    that arrived just after it has a slightly negative age, which is fresh.
    """
    now = snapshot.time
    failures = [
        failure
        for failure in [
            _staleness("position estimate", snapshot.position_estimate, now, STALE_AFTER),
            _staleness("drone status", snapshot.drone_status, now, STALE_AFTER),
            _staleness("down range", snapshot.range_readings.down, now, STALE_AFTER),
            _staleness("battery voltage", snapshot.battery_voltage, now, BATTERY_STALE_AFTER),
        ]
        if failure is not None
    ]
    battery = snapshot.battery_voltage
    if battery is not None and battery.value < LOW_BATTERY_VOLTAGE:
        failures.append(
            f"battery at {battery.value:.2f} V (land below {LOW_BATTERY_VOLTAGE:.2f} V)"
        )
    status = snapshot.drone_status
    if status is not None and status.value.is_crashed:
        failures.append("the drone reports a crash")
    if status is not None and status.value.is_tumbled:
        failures.append("the drone reports it has tumbled")
    return failures


def _staleness[T](name: str, stamped: Stamped[T] | None, now: float, limit: float) -> str | None:
    if stamped is None:
        return f"no {name} yet"
    age = stamped.age(now)
    if age > limit:
        return f"{name} is {age:.2f} s old (stale after {limit:g} s)"
    return None


def judge(request: CommandRequest, snapshot: Snapshot) -> Verdict:
    """Approve or refuse a command request by First flight's state rules (ADR-0030).

    Uses the drone status, never what was sent: a command the drone refused
    leaves its status unchanged.
    """
    status = snapshot.drone_status
    if status is None:
        return Verdict.refused("no drone status yet")
    is_armed = status.value.is_armed
    is_flying = status.value.is_flying
    match request:
        case Arm():
            return (
                Verdict.refused("the drone is already flying") if is_flying else Verdict.approved()
            )
        case TakeOff():
            if not is_armed:
                return Verdict.refused("the drone isn't armed")
            if is_flying:
                return Verdict.refused("the drone is already flying")
            return Verdict.approved()
        case Hover() | Land():
            # On the floor, the firmware would start the move anyway and spin the
            # motors of an armed drone (planner.c, checked 2026-10-30).
            return Verdict.approved() if is_flying else Verdict.refused("the drone isn't flying")
        case SetVelocity() | MoveTo():
            return Verdict.refused(
                "steering mode and fast mode wait for the speed envelope (backlog #30)"
            )


class SafetyLayer:
    """The only code that sends commands to the drone, apart from the kill switch (ADR-0013).

    Minimal for First flight (ADR-0030): one failsafe, land, and only the
    movement slot. Once the safety pre-check fails, the flight is over: it
    never resumes, and every later request is refused.
    """

    def __init__(self, drone: DroneInterface) -> None:
        self._drone = drone
        self._snapshot: Snapshot | None = None
        """This tick's snapshot: requests are judged against it."""
        self._movement: CommandRequest | None = None
        """The movement slot: the command to send at the end of this tick."""
        self._replaced_this_tick = False
        self._replaced_last_tick = False
        self._flight_is_over = False

    @property
    def flight_is_over(self) -> bool:
        """Whether the safety pre-check has failed, which ends the flight."""
        return self._flight_is_over

    def pre_check(self, snapshot: Snapshot) -> bool:
        """Run the safety pre-check on this tick's snapshot. Returns whether behaviors may run.

        On the first failure, the failsafe takes the movement slot: land, if
        the drone reports flying. The drone status may be stale by then, but
        it's the best knowledge there is.
        """
        self._snapshot = snapshot
        if self._flight_is_over:
            return False
        failures = safety_pre_check(snapshot)
        if not failures:
            return True
        self._flight_is_over = True
        status = snapshot.drone_status
        if status is not None and status.value.is_flying:
            self._movement = Land()
            logger.warning("Safety pre-check failed: %s. Landing.", "; ".join(failures))
        else:
            logger.warning(
                "Safety pre-check failed: %s. The drone doesn't report flying: no landing sent.",
                "; ".join(failures),
            )
        return False

    def request(self, request: CommandRequest) -> Verdict:
        """Judge a behavior's command request at once (ADR-0025).

        An approved request fills the movement slot. A later one in the same
        tick replaces it, with a warning once per streak (ADR-0020).
        """
        if self._flight_is_over:
            verdict = Verdict.refused("the flight is over: the safety pre-check failed")
        elif self._snapshot is None:
            verdict = Verdict.refused("no safety pre-check yet")
        else:
            verdict = judge(request, self._snapshot)
        if verdict.is_approved:
            self._fill_movement_slot(request)
        else:
            logger.debug("Refused %s: %s", request, verdict.reason)
        return verdict

    def send(self) -> None:
        """Send the movement slot's command, if any, then empty the slot for the next tick."""
        command, self._movement = self._movement, None
        self._replaced_last_tick = self._replaced_this_tick
        self._replaced_this_tick = False
        if command is None:
            return
        logger.info("Sending %s", command)
        match command:
            case Arm():
                self._drone.arm()
            case TakeOff(height=height):
                self._drone.take_off(height)
            case Hover():
                self._drone.hover()
            case Land():
                self._drone.land()
            case SetVelocity() | MoveTo():
                # judge() never approves these: a bug if it ever happens.
                raise RuntimeError(f"{command} reached the movement slot before the speed envelope")

    def _fill_movement_slot(self, request: CommandRequest) -> None:
        replaced = self._movement
        self._movement = request
        if replaced is None:
            return
        logger.debug("%s replaces %s in the movement slot", request, replaced)
        if not (self._replaced_this_tick or self._replaced_last_tick):
            logger.warning(
                "Two movement requests in one tick: %s replaces %s. "
                "Warned once per streak; every replacement is logged at debug level.",
                request,
                replaced,
            )
        self._replaced_this_tick = True
