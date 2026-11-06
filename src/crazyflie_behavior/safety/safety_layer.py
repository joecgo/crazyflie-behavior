"""The safety layer (ADR-0030).

Each tick, the tick step calls it in this order (ADR-0025):

1. `pre_check`: the safety pre-check on the tick's snapshot. If it fails, the
   failsafe lands the drone and the flight is over.
2. `request`: behaviors' command requests, each judged at once. An approved
   request fills its command slot: movement or buzzer.
3. `send`: each slot's command goes to the drone.

The pre-check and the judging are plain functions of the snapshot. Only the
SafetyLayer holds state: what it sends, and which warnings it has already given.

TODO: the operator's "land now" and "hover" commands aren't built yet (ADR-0027).
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
    BuzzerRequest,
    Chirp,
    CommandRequest,
    Hover,
    Land,
    MovementRequest,
    MoveTo,
    SetVelocity,
    Silence,
    TakeOff,
    Tone,
    Verdict,
)
from crazyflie_behavior.snapshot import Snapshot, Stamped

logger = logging.getLogger(__name__)

# --- PLACEHOLDERS, NOT DECISIONS: measure in the Bench field test (ADR-0030) --
STALE_AFTER = 0.25
"""Seconds. The position estimate, drone status and down range stream every
20 ms, so this is about 12 missed values in a row."""
BATTERY_STALE_AFTER = 3.0
"""Seconds. The battery voltage streams once a second."""
# ------------------------------------------------------------------------------

# Battery limits (ADR-0051). TODO: revisit after the first flight down to the limit (backlog #57).
LOW_BATTERY_VOLTAGE = 3.2
"""Volts. The low-battery limit: the safety pre-check fails below this."""
BATTERY_SAG_VOLTAGE = 0.42
"""Volts. The sag value the take-off limit allows for."""
TAKE_OFF_BATTERY_VOLTAGE = LOW_BATTERY_VOLTAGE + BATTERY_SAG_VOLTAGE
"""Volts. The take-off limit: a take-off is refused below this, so the sag doesn't fail the safety pre-check at once."""


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


def safety_pre_check(snapshot: Snapshot) -> list[str]:
    """The safety pre-check (ADR-0025): why it isn't safe to fly on this snapshot.

    An empty list means it passed. Ages count from the snapshot's time (ADR-0046).
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
    """Approve or refuse a behavior's command request (ADR-0030, ADR-0039, ADR-0051, ADR-0053).

    Arm is judged on the drone status, and take off on the drone status and
    the take-off limit. Hover and land are always approved, and the adapter
    decides whether to act on them. Buzzer requests are always approved.
    """
    # The drone status lags: it says "not flying" just after a take-off, and
    # "flying" for a while after the motors stop. Only the adapter, which
    # knows what it sent, can tell whether the drone may be flying.
    if isinstance(command_request, Hover | Land):
        return Verdict.approved()
    # Nothing in the buzzer path moves the drone (ADR-0053).
    if isinstance(command_request, Chirp | Tone | Silence):
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
            return _judge_take_off_battery(snapshot)
        case SetVelocity() | MoveTo():
            # TODO: refused until the speed envelope exists (backlog #30).
            return Verdict.refused("steering mode and fast mode wait for the speed envelope (backlog #30)")


def _judge_take_off_battery(snapshot: Snapshot) -> Verdict:
    # Judged here, on a reading from before the motors spin, and not in the
    # pre-check by drone status: the status still says "not flying" just after
    # a take-off, so the pre-check would hold the voltage, sag included, to the
    # take-off limit and land every flight (ADR-0051).
    battery = snapshot.battery_voltage
    if battery is None:
        return Verdict.refused("no battery voltage yet")
    # A value that isn't finite counts as missing (ADR-0030).
    if not math.isfinite(battery.value):
        return Verdict.refused(f"battery voltage isn't finite: {battery.value} V")
    if battery.value < TAKE_OFF_BATTERY_VOLTAGE:
        return Verdict.refused(f"battery at {battery.value:.2f} V (take off from {TAKE_OFF_BATTERY_VOLTAGE:.2f} V)")
    return Verdict.approved()


class _CommandSlot[T]:
    """One command slot (ADR-0025): the request to send at the end of this tick."""

    def __init__(self, name: str) -> None:
        self._name = name
        self._request: T | None = None
        self._replaced_this_tick = False
        self._replaced_last_tick = False

    def fill(self, request: T) -> None:
        """Hold `request` for this tick. One already held is replaced, with a warning once per streak (ADR-0020)."""
        replaced = self._request
        self._request = request
        if replaced is None:
            return
        logger.debug("%s replaces %s in the %s slot", request, replaced, self._name)
        if not (self._replaced_this_tick or self._replaced_last_tick):
            logger.warning(
                "Two %s requests in one tick: %s replaces %s. "
                "Warned once per streak; every replacement is logged at debug level.",
                self._name,
                request,
                replaced,
            )
        self._replaced_this_tick = True

    def take(self) -> T | None:
        """The request to send this tick, if any. Empties the slot for the next tick."""
        request, self._request = self._request, None
        self._replaced_last_tick = self._replaced_this_tick
        self._replaced_this_tick = False
        return request


class SafetyLayer:
    """The only code that sends commands to the drone, apart from the kill switch (ADR-0013).

    TODO: one failsafe (land) so far (ADR-0030), and no LED slot (ADR-0025).
    Once the safety pre-check fails, the flight is over: it
    never resumes, and every later request is refused.
    """

    def __init__(self, drone: DroneInterface) -> None:
        self._drone = drone
        self._snapshot: Snapshot | None = None
        """This tick's snapshot: requests are judged against it."""
        self._movement_slot = _CommandSlot[MovementRequest]("movement")
        self._buzzer_slot = _CommandSlot[BuzzerRequest]("buzzer")
        self._pre_check_has_failed = False

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
        failures = safety_pre_check(snapshot)
        if not failures:
            return True
        self._pre_check_has_failed = True
        self._movement_slot.fill(Land())
        logger.warning("Safety pre-check failed: %s. Landing.", "; ".join(failures))
        return False

    def request(self, command_request: CommandRequest) -> Verdict:
        """Judge a behavior's command request at once (ADR-0025).

        An approved request fills its command slot, movement or buzzer. A later
        one in the same slot and tick replaces it, with a warning once per streak (ADR-0020).
        """
        if self._pre_check_has_failed:
            verdict = Verdict.refused("the flight is over: the safety pre-check failed")
        elif self._snapshot is None:
            verdict = Verdict.refused("no safety pre-check yet")
        else:
            verdict = judge(command_request, self._snapshot)
        if not verdict.is_approved:
            logger.debug("Refused %s: %s", command_request, verdict.reason)
        elif isinstance(command_request, Chirp | Tone | Silence):
            self._buzzer_slot.fill(command_request)
        else:
            self._movement_slot.fill(command_request)
        return verdict

    def send(self) -> None:
        """Send each command slot's command, if any, then empty the slots for the next tick.

        Movement first. TODO: the LED slot comes later (ADR-0025).
        """
        movement = self._movement_slot.take()
        buzzer = self._buzzer_slot.take()
        if movement is not None:
            self._send_movement(movement)
        if buzzer is not None:
            self._send_buzzer(buzzer)

    def _send_movement(self, command: MovementRequest) -> None:
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

    def _send_buzzer(self, command: BuzzerRequest) -> None:
        logger.info("Sending %s", command)
        match command:
            case Chirp():
                self._drone.chirp()
            case Tone(pitch=pitch):
                self._drone.play_tone(pitch)
            case Silence():
                self._drone.silence()
