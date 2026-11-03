"""The safety layer, minimal for First flight (ADR-0030).

Each tick, the tick step calls it in this order (ADR-0025):

1. `pre_check`: the safety pre-check on the tick's snapshot. If it fails, the
   failsafe lands the drone and the flight is over.
2. `request`: behaviors' command requests, each judged at once. An approved
   request fills the movement slot.
3. `send`: the movement slot's command goes to the drone.

The pre-check and the judging are plain functions of the snapshot. Only the
SafetyLayer holds state: what it sends, and which warnings it has already given.

Not built yet: the operator's "land now" and "hover" commands (ADR-0027).
Both will fail the pre-check, so behaviors are skipped and no behavior can
override the operator. "Land now" lands like any failed check; "hover" holds
the drone instead, so it needs a failed pre-check that doesn't end the flight
(backlog #8).
"""

import logging
import math
from typing import NamedTuple

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
MAX_NEGATIVE_AGE = 0.05
"""Seconds: one tick period at `TICK_RATE`, 20 Hz (ADR-0023, ADR-0042). A value that
arrived just after the tick's time has a slightly negative age and counts as fresh. One
more than this in the future can only be a bug, such as mixing drone time with PC time,
so it's warned about. A copy of the tick period, not an import: the safety layer doesn't
depend on the loop package. A test keeps the two equal."""


class _CheckedValue(NamedTuple):
    """A snapshot value whose freshness the safety pre-check checks."""

    name: str
    stamped: Stamped[object] | None
    stale_after: float
    """Seconds."""


def _checked_values(snapshot: Snapshot) -> list[_CheckedValue]:
    return [
        _CheckedValue("position estimate", snapshot.position_estimate, STALE_AFTER),
        _CheckedValue("drone status", snapshot.drone_status, STALE_AFTER),
        _CheckedValue("down range", snapshot.range_readings.down, STALE_AFTER),
        _CheckedValue("battery voltage", snapshot.battery_voltage, BATTERY_STALE_AFTER),
    ]


def values_from_the_future(snapshot: Snapshot) -> dict[str, float]:
    """The checked values that arrived more than `MAX_NEGATIVE_AGE` after the tick's time (ADR-0042).

    Maps each one's name to its age, which is negative. They still count as fresh.
    """
    ages = {
        checked.name: checked.stamped.age(snapshot.time)
        for checked in _checked_values(snapshot)
        if checked.stamped is not None
    }
    return {name: age for name, age in ages.items() if age < -MAX_NEGATIVE_AGE}


def safety_pre_check(snapshot: Snapshot) -> list[str]:
    """The safety pre-check (ADR-0025): why it isn't safe to fly on this snapshot.

    An empty list means it passed. Ages count from the tick's time. A value
    that arrived just after it has a slightly negative age, which is fresh.
    """
    now = snapshot.time
    failures = [
        failure
        for failure in [_staleness(checked, now) for checked in _checked_values(snapshot)]
        if failure is not None
    ]
    # A value that isn't finite (NaN or infinite) counts as missing (ADR-0030).
    position = snapshot.position_estimate
    if position is not None and not position.value.is_finite():
        p = position.value
        failures.append(f"position estimate isn't finite: ({p.x:.2f}, {p.y:.2f}, {p.z:.2f}) m")
    battery = snapshot.battery_voltage
    if battery is not None and not math.isfinite(battery.value):
        failures.append(f"battery voltage isn't finite: {battery.value} V")
    elif battery is not None and battery.value < LOW_BATTERY_VOLTAGE:
        failures.append(f"battery at {battery.value:.2f} V (land below {LOW_BATTERY_VOLTAGE:.2f} V)")
    status = snapshot.drone_status
    if status is not None and status.value.is_crashed:
        failures.append("the drone reports a crash")
    if status is not None and status.value.is_tumbled:
        failures.append("the drone reports it has tumbled")
    return failures


def _staleness(checked: _CheckedValue, now: float) -> str | None:
    if checked.stamped is None:
        return f"no {checked.name} yet"
    age = checked.stamped.age(now)
    if age > checked.stale_after:
        return f"{checked.name} is {age:.2f} s old (stale after {checked.stale_after:g} s)"
    return None


def judge(command_request: CommandRequest, snapshot: Snapshot) -> Verdict:
    """Approve or refuse a command request by First flight's state rules (ADR-0030, ADR-0039).

    Arming and taking off use the drone status, never what was sent: a command
    the drone refused leaves its status unchanged. Hover and land are approved
    whatever the status says (even a missing one): only the adapter knows
    whether the drone may be flying, and it does nothing, or just stops the
    motors, for a drone on the floor (ADR-0039).
    """
    if isinstance(command_request, Hover | Land):
        return Verdict.approved()
    status = snapshot.drone_status
    if status is None:
        return Verdict.refused("no drone status yet")
    match command_request:
        case Arm():
            if status.value.is_flying:
                return Verdict.refused("the drone is already flying")
            return Verdict.approved()
        case TakeOff():
            if not status.value.is_armed:
                return Verdict.refused("the drone isn't armed")
            if status.value.is_flying:
                return Verdict.refused("the drone is already flying")
            return Verdict.approved()
        case SetVelocity() | MoveTo():
            return Verdict.refused("steering mode and fast mode wait for the speed envelope (backlog #30)")


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
        self._movement_replaced_this_tick = False
        self._movement_replaced_last_tick = False
        self._pre_check_has_failed = False
        self._values_from_the_future: set[str] = set()
        """The values whose age is below `-MAX_NEGATIVE_AGE` on the latest tick: a warning
        comes once per streak per value (ADR-0042)."""

    @property
    def pre_check_has_failed(self) -> bool:
        """Whether the safety pre-check has failed, which ends the flight."""
        return self._pre_check_has_failed

    def pre_check(self, snapshot: Snapshot) -> bool:
        """Run the safety pre-check on this tick's snapshot. Returns whether behaviors may run.

        On the first failure, the failsafe takes the movement slot: land,
        whatever the drone status says. The adapter decides whether the drone
        may be flying, which the status alone can't tell (ADR-0039).
        """
        self._snapshot = snapshot
        if self._pre_check_has_failed:
            return False
        self._warn_about_values_from_the_future(snapshot)
        failures = safety_pre_check(snapshot)
        if not failures:
            return True
        self._pre_check_has_failed = True
        self._movement = Land()
        logger.warning("Safety pre-check failed: %s. Landing.", "; ".join(failures))
        return False

    def _warn_about_values_from_the_future(self, snapshot: Snapshot) -> None:
        """Warn, once per streak per value, about a value that arrived long after the tick's time (ADR-0042).

        The warning never fails the pre-check: the value still counts as fresh.
        """
        ages = values_from_the_future(snapshot)
        for name, age in ages.items():
            if name not in self._values_from_the_future:
                logger.warning(
                    "The %s arrived %.2f s after the tick's time, more than one tick period: a probable "
                    "clock bug (mixed drone and PC time?). It still counts as fresh. Warned once per streak.",
                    name,
                    -age,
                )
        self._values_from_the_future = set(ages)

    def request(self, command_request: CommandRequest) -> Verdict:
        """Judge a behavior's command request at once (ADR-0025).

        An approved request fills the movement slot. A later one in the same
        tick replaces it, with a warning once per streak (ADR-0020).
        """
        if self._pre_check_has_failed:
            verdict = Verdict.refused("the flight is over: the safety pre-check failed")
        elif self._snapshot is None:
            verdict = Verdict.refused("no safety pre-check yet")
        else:
            verdict = judge(command_request, self._snapshot)
        if verdict.is_approved:
            self._fill_movement_slot(command_request)
        else:
            logger.debug("Refused %s: %s", command_request, verdict.reason)
        return verdict

    def send(self) -> None:
        """Send each command slot's command, if any, then empty the slots for the next tick.

        Only the movement slot exists so far (ADR-0030); buzzer and LED slots come later (ADR-0025).
        """
        command, self._movement = self._movement, None
        self._movement_replaced_last_tick = self._movement_replaced_this_tick
        self._movement_replaced_this_tick = False
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

    def _fill_movement_slot(self, command_request: CommandRequest) -> None:
        replaced = self._movement
        self._movement = command_request
        if replaced is None:
            return
        logger.debug("%s replaces %s in the movement slot", command_request, replaced)
        if not (self._movement_replaced_this_tick or self._movement_replaced_last_tick):
            logger.warning(
                "Two movement requests in one tick: %s replaces %s. "
                "Warned once per streak; every replacement is logged at debug level.",
                command_request,
                replaced,
            )
        self._movement_replaced_this_tick = True
