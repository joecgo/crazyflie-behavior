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

from crazyflie_behavior.drone.interface import (
    FLOOR_MAX_SPEED,
    FLOW_VELOCITY_UNCERTAINTY,
    TOUCHDOWN_DOWN_RANGE,
    DroneInterface,
)
from crazyflie_behavior.safety.requests import (
    Arm,
    BuzzerRequest,
    Chirp,
    CommandRequest,
    Hover,
    Land,
    MovementRequest,
    MoveTo,
    ResetEstimate,
    SetVelocity,
    Silence,
    TakeOff,
    Tone,
    Verdict,
)
from crazyflie_behavior.snapshot import RangeStatus, Snapshot, Stamped

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

# The take-off rule's estimate check, with flow arriving (ADR-0054). A PLACEHOLDER, to verify in flight.
# Its speed limit is FLOOR_MAX_SPEED, shared with the adapter (ADR-0060).
TAKE_OFF_MAX_DISTANCE_FROM_RESET_POINT = 0.05
"""Meters: how far from the reset point (0, 0) the horizontal position estimate may be."""

# The in-flight check's velocity uncertainty limit grows with height (ADR-0064), from
# FLOW_VELOCITY_UNCERTAINTY up to a cap. The growth is a PLACEHOLDER, to verify in flight.
VELOCITY_UNCERTAINTY_LIMIT_PER_METER = 0.1
"""Meters per second, per meter of height."""
MAX_VELOCITY_UNCERTAINTY_LIMIT = 0.1
"""Meters per second."""


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


def _was_previous_battery_reading_low(previous: Stamped[float] | None) -> bool:
    """For the low-battery limit's two readings in a row (ADR-0069). Missing or not finite counts as low,
    so the latest reading decides alone."""
    return previous is None or not math.isfinite(previous.value) or previous.value < LOW_BATTERY_VOLTAGE


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
    elif (
        battery is not None
        and battery.value < LOW_BATTERY_VOLTAGE
        and _was_previous_battery_reading_low(snapshot.previous_battery_voltage)
    ):
        failures.append(f"battery at {battery.value:.2f} V (land below {LOW_BATTERY_VOLTAGE:.2f} V)")
    status = snapshot.drone_status
    if status is not None and status.value.is_crashed:
        failures.append("the drone reports a crash")
    if status is not None and status.value.is_tumbled:
        failures.append("the drone reports it has tumbled")
    # Only in flight: on the floor a failed pre-check would end every round at a dark hiding spot.
    # By "may be flying", not the drone status, which says flying for 2 s after the motors stop.
    # The initial climb checks the flow itself (ADR-0054, ADR-0060).
    if snapshot.may_be_flying and not snapshot.is_in_initial_climb:
        failure = _velocity_uncertainty_failure(snapshot)
        if failure is not None:
            failures.append(failure)
    return failures


def _velocity_uncertainty_failure(snapshot: Snapshot) -> str | None:
    uncertainty = snapshot.velocity_uncertainty
    stale = _staleness(_CheckedValue("velocity uncertainty", uncertainty, STALE_AFTER), snapshot.time)
    if stale is not None or uncertainty is None:
        return stale
    height = _known_height(snapshot)
    limit = in_flight_velocity_uncertainty_limit(height)
    # The comparison is false for NaN too, so NaN fails like a missing value (ADR-0030).
    if not uncertainty.value < limit:
        at_height = "an unknown height" if height is None else f"{height:.2f} m"
        return (
            f"velocity uncertainty {uncertainty.value:.3f} m/s in flight, "
            f"must be under {limit:g} at {at_height}: no flow"
        )
    return None


def in_flight_velocity_uncertainty_limit(height: float | None) -> float:
    """Meters per second: in flight, the velocity uncertainty must be under this at `height` meters (ADR-0064).

    An unknown height (None, or not finite) gets the strictest limit.
    """
    if height is None or not math.isfinite(height):
        return FLOW_VELOCITY_UNCERTAINTY
    grown = VELOCITY_UNCERTAINTY_LIMIT_PER_METER * height
    return min(MAX_VELOCITY_UNCERTAINTY_LIMIT, max(FLOW_VELOCITY_UNCERTAINTY, grown))


def _known_height(snapshot: Snapshot) -> float | None:
    """Meters: the position estimate's height, or None if it's missing, stale or not finite."""
    position = snapshot.position_estimate
    stale = _staleness(_CheckedValue("position estimate", position, STALE_AFTER), snapshot.time)
    if position is None or stale is not None or not math.isfinite(position.value.z):
        return None
    return position.value.z


def _staleness(checked: _CheckedValue, now: float) -> str | None:
    if checked.stamped is None:
        return f"no {checked.name} yet"
    age = checked.stamped.age(now)
    if age > checked.stale_after:
        return f"{checked.name} is {age:.2f} s old (stale after {checked.stale_after:g} s)"
    return None


def judge(command_request: CommandRequest, snapshot: Snapshot) -> Verdict:
    """Approve or refuse a behavior's command request (ADR-0030, ADR-0039, ADR-0051, ADR-0053).

    Arm is judged on the drone status, and take off on the drone status, the
    take-off limit and the estimate (ADR-0054). An estimate reset only on the
    floor. Hover and land are always approved, and the adapter decides whether
    to act on them. Buzzer requests are always approved.
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
            battery_verdict = _judge_take_off_battery(snapshot)
            if not battery_verdict.is_approved:
                return battery_verdict
            return _judge_take_off_estimate(snapshot)
        case ResetEstimate():
            if status.value.is_flying:
                return Verdict.refused("an estimate reset is never sent in flight")
            return _judge_on_the_floor(snapshot) or Verdict.approved()
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


def _judge_on_the_floor(snapshot: Snapshot) -> Verdict | None:
    """A refusal unless the down range reads the floor (ADR-0054)."""
    down = snapshot.range_readings.down
    if down is None or down.value.status is not RangeStatus.DISTANCE or down.value.distance is None:
        return Verdict.refused("the down range doesn't read the floor: no distance")
    if down.value.distance > TOUCHDOWN_DOWN_RANGE:
        return Verdict.refused(
            f"the down range doesn't read the floor: {down.value.distance:.3f} m (floor up to {TOUCHDOWN_DOWN_RANGE:g})"
        )
    return None


def _judge_take_off_estimate(snapshot: Snapshot) -> Verdict:
    """On the floor; with flow arriving, the estimate must also be still at the reset point (ADR-0054).

    Without flow, the take-off goes ahead: the initial climb checks the flow at the settle height.
    """
    floor_refusal = _judge_on_the_floor(snapshot)
    if floor_refusal is not None:
        return floor_refusal
    uncertainty = snapshot.velocity_uncertainty
    if uncertainty is None or uncertainty.age(snapshot.time) > STALE_AFTER or math.isnan(uncertainty.value):
        return Verdict.refused("no fresh velocity uncertainty")
    if uncertainty.value >= FLOW_VELOCITY_UNCERTAINTY:
        return Verdict.approved()  # no flow: nothing to check the estimate against
    velocity = snapshot.velocity_estimate
    position = snapshot.position_estimate
    if velocity is None or position is None:
        return Verdict.refused("no position or velocity estimate yet")
    speed = math.hypot(velocity.value.x, velocity.value.y)
    # The comparisons are false for NaN too.
    if not speed < FLOOR_MAX_SPEED:
        return Verdict.refused(
            f"the estimate is moving on the floor: {speed:.3f} m/s, must be under {FLOOR_MAX_SPEED:g}"
        )
    distance = math.hypot(position.value.x, position.value.y)
    if not distance <= TAKE_OFF_MAX_DISTANCE_FROM_RESET_POINT:
        return Verdict.refused(
            f"the estimate is {distance:.3f} m from the reset point, "
            f"must be within {TAKE_OFF_MAX_DISTANCE_FROM_RESET_POINT:g}: request an estimate reset"
        )
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
        self._is_estimate_reset_requested = False
        """An approved estimate reset waits for the end of the tick. It has no slot (ADR-0054)."""
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
        An approved estimate reset has no slot: it's sent after the slots' commands (ADR-0054).
        """
        if self._pre_check_has_failed:
            verdict = Verdict.refused("the flight is over: the safety pre-check failed")
        elif self._snapshot is None:
            verdict = Verdict.refused("no safety pre-check yet")
        else:
            verdict = judge(command_request, self._snapshot)
        if not verdict.is_approved:
            logger.debug("Refused %s: %s", command_request, verdict.reason)
        elif isinstance(command_request, ResetEstimate):
            self._is_estimate_reset_requested = True
        elif isinstance(command_request, Chirp | Tone | Silence):
            self._buzzer_slot.fill(command_request)
        else:
            self._movement_slot.fill(command_request)
        return verdict

    def send(self) -> None:
        """Send each command slot's command, if any, then empty the slots for the next tick.

        Movement first, then buzzer, then an approved estimate reset (ADR-0054).
        TODO: the LED slot comes later (ADR-0025).
        """
        movement = self._movement_slot.take()
        buzzer = self._buzzer_slot.take()
        is_estimate_reset_requested = self._is_estimate_reset_requested
        self._is_estimate_reset_requested = False
        if movement is not None:
            self._send_movement(movement)
        if buzzer is not None:
            self._send_buzzer(buzzer)
        if is_estimate_reset_requested:
            logger.info("Sending %s", ResetEstimate())
            self._drone.reset_estimate()

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
