"""The hover test (ADR-0030): the behavior for the Hover field test.

Arm, take off to `TAKE_OFF_HEIGHT`, hover, land, then report done. Each step
waits until the snapshot shows it happened, because commands take effect after
they're sent (latency), and the waits for arming and taking off have time limits.

With chirps (ADR-0053), to see how the buzzer drains the battery: chirp on the
floor and wait `FLOOR_CHIRP_WAIT` before arming; chirp every `CHIRP_PERIOD`
from the take-off request until the drone status says landed; chirp
`LANDED_CHIRP_DELAY` after that, wait `CHARGE_WAIT`, play "Charge" one note
per tick as each is due, then silence; done `SILENCE_HOLD` later, so the
silence reaches the drone before the link closes.

Failure rule (ADR-0033): the first refused request ends the test, since it
tests the basic sequence and an unexpected state is the finding. So do its
time limits: arming too slowly ends it at once, and a take-off that doesn't
reach the height lands first. Ending lands the drone, and every failure is
logged as an error with its reason.
"""

import logging
import math
from bisect import bisect_right
from collections.abc import Callable
from enum import Enum
from itertools import accumulate
from typing import NamedTuple

from crazyflie_behavior.behaviors.behavior import Behavior
from crazyflie_behavior.safety.requests import Arm, Chirp, CommandRequest, Land, Silence, TakeOff, Tone, Verdict
from crazyflie_behavior.snapshot import Snapshot

logger = logging.getLogger(__name__)

TAKE_OFF_HEIGHT = 0.5
"""Meters, as the Hover field test asks."""
DEFAULT_HOVER_DURATION = 10.0
"""Seconds."""

# --- PLACEHOLDERS, NOT DECISIONS: tune in the Hover field test ----------------
HEIGHT_TOLERANCE = 0.1
"""Meters. This close to the take-off height counts as there."""
ARM_TIME_LIMIT = 2.0
"""Seconds for the drone status to show armed."""
TAKE_OFF_TIME_LIMIT = 5.0
"""Seconds to reach the take-off height, with a margin over the time the Crazyflie
adapter plans for the take-off (its `VERTICAL_SPEED`)."""
# ------------------------------------------------------------------------------

# The chirp schedule (ADR-0053).
FLOOR_CHIRP_WAIT = 5.0
"""Seconds from the chirp on the floor to arming."""
CHIRP_PERIOD = 5.0
"""Seconds between chirps in flight, counted from the take-off request."""
LANDED_CHIRP_DELAY = 1.0
"""Seconds from the drone status saying landed to the chirp after landing."""
CHARGE_WAIT = 5.0
"""Seconds from the chirp after landing to "Charge"."""
SILENCE_HOLD = 1.0
"""Seconds from the silence to done: cflib drops writes still waiting when the link closes."""


class Note(NamedTuple):
    """One note of a tune."""

    name: str
    """C, E, G or A."""
    octaves_up: int
    """Octaves above the tune's starting octave."""
    length: float
    """Seconds."""


# --- PLACEHOLDERS, NOT DECISIONS: tune by ear (ADR-0053) ----------------------
CHARGE_OCTAVE = 4
"""The octave "Charge" starts in: 4 plays G4 C5 E5 G5 E5 G5."""
CHARGE = (
    Note("G", 0, 0.150),
    Note("C", 1, 0.150),
    Note("E", 1, 0.150),
    Note("G", 1, 0.300),
    Note("E", 1, 0.150),
    Note("G", 1, 0.600),
)
"""The bugle call, played after landing."""
# ------------------------------------------------------------------------------

CONCERT_PITCH = 440.0
"""Hertz: A4, the tuning reference."""
_SEMITONES_ABOVE_C = {"C": 0, "E": 4, "G": 7, "A": 9}


def note_pitch(name: str, octave: int) -> float:
    """Hertz, in equal temperament."""
    semitones_above_a4 = 12 * (octave - 4) + _SEMITONES_ABOVE_C[name] - _SEMITONES_ABOVE_C["A"]
    return CONCERT_PITCH * 2.0 ** (semitones_above_a4 / 12)


# Built on import, so a pitch the buzzer can't play fails every run, not just a flight with chirps.
_CHARGE_TONES = [Tone(note_pitch(note.name, CHARGE_OCTAVE + note.octaves_up)) for note in CHARGE]
_CHARGE_NOTE_STARTS = list(accumulate((note.length for note in CHARGE[:-1]), initial=0.0))
"""Seconds from the start of "Charge" to each note."""
_CHARGE_LENGTH = sum(note.length for note in CHARGE)
"""Seconds from the start of "Charge" to its silence."""


class _Step(Enum):
    FLOOR_CHIRP = "chirp on the floor"
    AFTER_FLOOR_CHIRP = "after the chirp on the floor"
    START = "start"
    ARMING = "arming"
    TAKING_OFF = "taking off"
    HOVERING = "hovering"
    LANDING = "landing"
    LANDED = "landed"
    AFTER_LANDED_CHIRP = "after the chirp after landing"
    CHARGE = "playing Charge"
    SILENCED = "silenced"
    DONE = "done"


_IN_FLIGHT_STEPS = {_Step.TAKING_OFF, _Step.HOVERING, _Step.LANDING}
"""The steps that chirp every `CHIRP_PERIOD`: from the take-off request until the drone status says landed."""


class HoverTest(Behavior):
    """Arm, take off to `TAKE_OFF_HEIGHT`, hover, land, then report done. Optionally with chirps."""

    def __init__(self, hover_duration: float = DEFAULT_HOVER_DURATION, *, chirp: bool = False) -> None:
        """`hover_duration`: seconds to hover once at the take-off height. `chirp`: chirp
        on the floor, in flight and after landing, then play "Charge" (ADR-0053)."""
        if not (math.isfinite(hover_duration) and hover_duration >= 0.0):
            raise ValueError(f"Hover duration must be zero or more seconds: {hover_duration}")
        self._hover_duration = hover_duration
        self._chirps = chirp
        self._step = _Step.FLOOR_CHIRP if chirp else _Step.START
        self._step_started_at = 0.0
        """The snapshot time the current step started."""
        self._next_chirp_at = math.inf
        """The snapshot time of the next chirp in flight."""
        self._charge_note_playing: int | None = None
        """The index of the latest note requested."""

    def tick(self, snapshot: Snapshot, ask_safety_layer: Callable[[CommandRequest], Verdict]) -> bool:
        status = snapshot.drone_status
        position = snapshot.position_estimate
        if status is None or position is None:
            raise RuntimeError("tick ran without a drone status or position: the safety pre-check should rule this out")
        now = snapshot.time
        time_in_step = now - self._step_started_at
        height = position.value.z
        match self._step:
            case _Step.FLOOR_CHIRP:
                if self._ask(ask_safety_layer, Chirp(), now):
                    logger.info("Hover test: chirp on the floor. Arming in %g s", FLOOR_CHIRP_WAIT)
                    self._start_step(_Step.AFTER_FLOOR_CHIRP, now)
            case _Step.AFTER_FLOOR_CHIRP:
                if time_in_step >= FLOOR_CHIRP_WAIT:
                    self._arm(ask_safety_layer, now)
            case _Step.START:
                self._arm(ask_safety_layer, now)
            case _Step.ARMING:
                if status.value.is_armed:
                    if self._ask(ask_safety_layer, TakeOff(TAKE_OFF_HEIGHT), now):
                        logger.info("Hover test: armed. Taking off to %.2f m", TAKE_OFF_HEIGHT)
                        self._start_step(_Step.TAKING_OFF, now)
                        self._next_chirp_at = now + CHIRP_PERIOD
                elif time_in_step > ARM_TIME_LIMIT:
                    logger.error(
                        "Hover test failed: the drone didn't report armed within %g s",
                        ARM_TIME_LIMIT,
                    )
                    self._start_step(_Step.DONE, now)
            case _Step.TAKING_OFF:
                if abs(height - TAKE_OFF_HEIGHT) <= HEIGHT_TOLERANCE:
                    logger.info("Hover test: at %.2f m. Hovering for %g s", height, self._hover_duration)
                    self._start_step(_Step.HOVERING, now)
                elif time_in_step > TAKE_OFF_TIME_LIMIT:
                    logger.error(
                        "Hover test failed: not at %.2f m after %g s (at %.2f m). Landing.",
                        TAKE_OFF_HEIGHT,
                        TAKE_OFF_TIME_LIMIT,
                        height,
                    )
                    self._land(ask_safety_layer, now)
            case _Step.HOVERING:
                if time_in_step >= self._hover_duration:
                    logger.info("Hover test: hovered %g s. Landing.", self._hover_duration)
                    self._land(ask_safety_layer, now)
            case _Step.LANDING:
                if not status.value.is_flying:
                    if self._chirps:
                        logger.info("Hover test: landed. Chirping in %g s", LANDED_CHIRP_DELAY)
                        self._start_step(_Step.LANDED, now)
                    else:
                        logger.info("Hover test: landed. Done.")
                        self._start_step(_Step.DONE, now)
            case _Step.LANDED:
                if time_in_step >= LANDED_CHIRP_DELAY and self._ask(ask_safety_layer, Chirp(), now):
                    logger.info('Hover test: chirp after landing. "Charge" in %g s', CHARGE_WAIT)
                    self._start_step(_Step.AFTER_LANDED_CHIRP, now)
            case _Step.AFTER_LANDED_CHIRP:
                if time_in_step >= CHARGE_WAIT:
                    logger.info('Hover test: playing "Charge"')
                    self._start_step(_Step.CHARGE, now)
                    self._play_charge(ask_safety_layer, now, time_in_charge=0.0)
            case _Step.CHARGE:
                self._play_charge(ask_safety_layer, now, time_in_step)
            case _Step.SILENCED:
                if time_in_step >= SILENCE_HOLD:
                    logger.info("Hover test: done.")
                    self._start_step(_Step.DONE, now)
            case _Step.DONE:
                pass
        if self._chirps and self._step in _IN_FLIGHT_STEPS and now >= self._next_chirp_at:
            self._chirp_in_flight(ask_safety_layer, now)
        return self._step is _Step.DONE

    def _arm(self, ask_safety_layer: Callable[[CommandRequest], Verdict], now: float) -> None:
        if self._ask(ask_safety_layer, Arm(), now):
            logger.info("Hover test: arming")
            self._start_step(_Step.ARMING, now)

    def _land(self, ask_safety_layer: Callable[[CommandRequest], Verdict], now: float) -> None:
        if self._ask(ask_safety_layer, Land(), now):
            self._start_step(_Step.LANDING, now)

    def _chirp_in_flight(self, ask_safety_layer: Callable[[CommandRequest], Verdict], now: float) -> None:
        if self._ask(ask_safety_layer, Chirp(), now):
            # On the period's beat, unless a long gap between ticks has already passed the next one.
            self._next_chirp_at += CHIRP_PERIOD
            if self._next_chirp_at <= now:
                self._next_chirp_at = now + CHIRP_PERIOD

    def _play_charge(
        self, ask_safety_layer: Callable[[CommandRequest], Verdict], now: float, time_in_charge: float
    ) -> None:
        """Request the note due now, if it isn't playing yet, or the silence once the last note has ended.

        A note whose whole length falls between two ticks is skipped, so the rest stay on time.
        """
        if time_in_charge >= _CHARGE_LENGTH:
            if self._ask(ask_safety_layer, Silence(), now):
                self._start_step(_Step.SILENCED, now)
            return
        note_due = bisect_right(_CHARGE_NOTE_STARTS, time_in_charge) - 1
        if note_due != self._charge_note_playing and self._ask(ask_safety_layer, _CHARGE_TONES[note_due], now):
            self._charge_note_playing = note_due

    def _ask(
        self,
        ask_safety_layer: Callable[[CommandRequest], Verdict],
        command_request: CommandRequest,
        now: float,
    ) -> bool:
        """Make a command request; returns whether it was approved. A refused one ends the hover test."""
        verdict = ask_safety_layer(command_request)
        if not verdict.is_approved:
            logger.error("Hover test failed: %s was refused: %s", command_request, verdict.reason)
            self._start_step(_Step.DONE, now)
        return verdict.is_approved

    def _start_step(self, step: _Step, now: float) -> None:
        self._step = step
        self._step_started_at = now
