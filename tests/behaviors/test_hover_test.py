"""The hover test (ADR-0030, ADR-0053), with hand-built snapshots and a stand-in for the safety layer."""

import logging
import math
from dataclasses import replace
from typing import NamedTuple

import pytest

from crazyflie_behavior.behaviors.hover_test import (
    ARM_TIME_LIMIT,
    CHARGE,
    CHARGE_WAIT,
    CHIRP_PERIOD,
    FLOOR_CHIRP_WAIT,
    LANDED_CHIRP_DELAY,
    SILENCE_HOLD,
    TAKE_OFF_HEIGHT,
    TAKE_OFF_TIME_LIMIT,
    HoverTest,
    note_pitch,
)
from crazyflie_behavior.geometry import Vector3
from crazyflie_behavior.safety.requests import Arm, Chirp, CommandRequest, Land, Silence, TakeOff, Tone, Verdict
from crazyflie_behavior.snapshot import DroneStatus, RangeReading, RangeReadings, Snapshot, Stamped

HOVER_DURATION = 2.0

ON_THE_FLOOR = DroneStatus(
    is_armed=False, is_flying=False, is_crashed=False, is_tumbled=False, can_arm=True, is_locked=False
)
ARMED = replace(ON_THE_FLOOR, is_armed=True)
FLYING = replace(ARMED, is_flying=True)


class SafetyLayerStandIn:
    """Records every command request and approves it, unless told to refuse."""

    def __init__(self, refuse_with: str | None = None) -> None:
        self.requests: list[CommandRequest] = []
        self._refuse_with = refuse_with

    def __call__(self, command_request: CommandRequest) -> Verdict:
        self.requests.append(command_request)
        if self._refuse_with is not None:
            return Verdict.refused(self._refuse_with)
        return Verdict.approved()


def snapshot(time: float, status: DroneStatus, height: float = 0.0) -> Snapshot:
    """A fresh snapshot at `time`, with the drone at `height`."""

    def fresh[T](value: T) -> Stamped[T]:
        return Stamped(value, arrival_time=time, drone_time=None)

    return Snapshot(
        time=time,
        dt=0.05,
        position_estimate=fresh(Vector3(0.0, 0.0, height)),
        velocity_estimate=fresh(Vector3.ZERO),
        range_readings=RangeReadings(None, None, None, None, None, fresh(RangeReading.at_distance(height))),
        battery_voltage=fresh(4.0),
        drone_status=fresh(status),
    )


def hovering_test(safety_layer: SafetyLayerStandIn) -> HoverTest:
    """A hover test that armed at 0 s, took off at 0.25 s and reached the height at 0.5 s."""
    hover_test = HoverTest(HOVER_DURATION)
    hover_test.tick(snapshot(0.0, ON_THE_FLOOR), safety_layer)
    hover_test.tick(snapshot(0.25, ARMED), safety_layer)
    hover_test.tick(snapshot(0.5, FLYING, TAKE_OFF_HEIGHT), safety_layer)
    return hover_test


def errors_in(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [r.getMessage() for r in caplog.records if r.levelno == logging.ERROR]


def test_it_asks_to_arm_first() -> None:
    safety_layer = SafetyLayerStandIn()

    HoverTest().tick(snapshot(0.0, ON_THE_FLOOR), safety_layer)

    assert safety_layer.requests == [Arm()]


def test_it_takes_off_only_once_the_drone_reports_armed() -> None:
    safety_layer = SafetyLayerStandIn()
    hover_test = HoverTest()
    hover_test.tick(snapshot(0.0, ON_THE_FLOOR), safety_layer)

    hover_test.tick(snapshot(0.25, ON_THE_FLOOR), safety_layer)  # arming hasn't shown yet
    requests_before_armed = list(safety_layer.requests)
    hover_test.tick(snapshot(0.5, ARMED), safety_layer)

    assert requests_before_armed == [Arm()]
    assert safety_layer.requests == [Arm(), TakeOff(TAKE_OFF_HEIGHT)]


def test_it_stops_if_the_drone_never_reports_armed(caplog: pytest.LogCaptureFixture) -> None:
    safety_layer = SafetyLayerStandIn()
    hover_test = HoverTest()
    hover_test.tick(snapshot(0.0, ON_THE_FLOOR), safety_layer)

    still_waiting = hover_test.tick(snapshot(ARM_TIME_LIMIT, ON_THE_FLOOR), safety_layer)
    is_done = hover_test.tick(snapshot(ARM_TIME_LIMIT + 0.25, ON_THE_FLOOR), safety_layer)

    assert not still_waiting
    assert is_done
    assert safety_layer.requests == [Arm()]
    assert errors_in(caplog) == ["Hover test failed: the drone didn't report armed within 2 s"]


def test_it_starts_hovering_once_close_to_the_take_off_height() -> None:
    safety_layer = SafetyLayerStandIn()
    hover_test = HoverTest(hover_duration=0.0)
    hover_test.tick(snapshot(0.0, ON_THE_FLOOR), safety_layer)
    hover_test.tick(snapshot(0.25, ARMED), safety_layer)

    hover_test.tick(snapshot(0.5, FLYING, height=0.375), safety_layer)  # 0.125 m short
    hover_test.tick(snapshot(0.75, FLYING, height=0.4375), safety_layer)  # close enough
    requests_when_it_got_there = list(safety_layer.requests)
    hover_test.tick(snapshot(1.0, FLYING, height=0.5), safety_layer)

    assert requests_when_it_got_there == [Arm(), TakeOff(TAKE_OFF_HEIGHT)]
    assert safety_layer.requests[-1] == Land()  # hovered for 0 s, so it lands


def test_it_hovers_for_the_hover_duration_then_lands() -> None:
    safety_layer = SafetyLayerStandIn()
    hover_test = hovering_test(safety_layer)  # hovering since 0.5 s

    hover_test.tick(snapshot(0.5 + HOVER_DURATION - 0.25, FLYING, 0.5), safety_layer)
    requests_before_the_end = list(safety_layer.requests)
    hover_test.tick(snapshot(0.5 + HOVER_DURATION, FLYING, 0.5), safety_layer)

    assert Land() not in requests_before_the_end
    assert safety_layer.requests[-1] == Land()


def test_it_is_done_once_the_drone_reports_it_landed() -> None:
    safety_layer = SafetyLayerStandIn()
    hover_test = hovering_test(safety_layer)
    hover_test.tick(snapshot(3.0, FLYING, 0.5), safety_layer)  # lands

    still_landing = hover_test.tick(snapshot(3.25, FLYING, 0.25), safety_layer)
    is_done = hover_test.tick(snapshot(3.5, ARMED, 0.0), safety_layer)

    assert not still_landing
    assert is_done
    assert safety_layer.requests == [Arm(), TakeOff(TAKE_OFF_HEIGHT), Land()]


def test_it_lands_if_the_take_off_does_not_reach_the_height_in_time(
    caplog: pytest.LogCaptureFixture,
) -> None:
    safety_layer = SafetyLayerStandIn()
    hover_test = HoverTest()
    hover_test.tick(snapshot(0.0, ON_THE_FLOOR), safety_layer)
    hover_test.tick(snapshot(0.25, ARMED), safety_layer)  # take-off starts

    hover_test.tick(snapshot(0.25 + TAKE_OFF_TIME_LIMIT, FLYING, 0.25), safety_layer)
    requests_at_the_limit = list(safety_layer.requests)
    hover_test.tick(snapshot(0.5 + TAKE_OFF_TIME_LIMIT, FLYING, 0.25), safety_layer)

    assert Land() not in requests_at_the_limit
    assert safety_layer.requests[-1] == Land()
    assert errors_in(caplog) == ["Hover test failed: not at 0.50 m after 5 s (at 0.25 m). Landing."]


def test_a_refused_request_ends_the_hover_test(caplog: pytest.LogCaptureFixture) -> None:
    safety_layer = SafetyLayerStandIn(refuse_with="the drone is already flying")

    is_done = HoverTest().tick(snapshot(0.0, ON_THE_FLOOR), safety_layer)

    assert is_done
    assert errors_in(caplog) == ["Hover test failed: Arm() was refused: the drone is already flying"]


@pytest.mark.parametrize("missing", ["drone_status", "position_estimate"])
def test_a_tick_without_a_drone_status_or_position_is_a_bug(missing: str) -> None:
    """The safety pre-check rules this out, so if it happens, it must not pass silently."""
    incomplete = replace(snapshot(0.0, ON_THE_FLOOR), **{missing: None})

    with pytest.raises(RuntimeError, match="safety pre-check should rule this out"):
        HoverTest().tick(incomplete, SafetyLayerStandIn())


def test_it_makes_each_request_once() -> None:
    safety_layer = SafetyLayerStandIn()
    hover_test = hovering_test(safety_layer)

    for tick_number in range(40):  # 10 s of quarter-second ticks: hover, land, done
        time = 0.75 + tick_number * 0.25
        status, height = (FLYING, 0.5) if time < 3.0 else (ARMED, 0.0)
        hover_test.tick(snapshot(time, status, height), safety_layer)

    assert safety_layer.requests == [Arm(), TakeOff(TAKE_OFF_HEIGHT), Land()]


@pytest.mark.parametrize("hover_duration", [-1.0, math.nan, math.inf])
def test_a_hover_duration_that_is_negative_or_endless_is_a_bug(hover_duration: float) -> None:
    with pytest.raises(ValueError, match="Hover duration"):
        HoverTest(hover_duration)


# --- With chirps (ADR-0053) -----------------------------------------------------------

TICK = 1 / 32
"""Seconds between ticks in a scripted flight. A power of two, so tick times add up exactly
and "the first tick at or after" needs no tolerance; the behavior doesn't depend on the tick rate."""
LONG_HOVER = 12.0
"""Seconds: long enough for two chirps in flight."""


class TimedRequest(NamedTuple):
    time: float
    request: CommandRequest


class ScriptedFlight:
    """Ticks a hover test every `TICK`, with a drone that carries out each movement request by the next tick.

    After a land request, the drone status keeps saying flying for `landing_lag` seconds.
    """

    def __init__(self, hover_test: HoverTest, landing_lag: float = 0.0) -> None:
        self.hover_test = hover_test
        self.safety_layer = SafetyLayerStandIn()
        self.timeline: list[TimedRequest] = []
        self.done_at: float | None = None
        self._landing_lag = landing_lag
        self._status = ON_THE_FLOOR
        self._height = 0.0
        self._land_requested_at: float | None = None

    def run(self, until: float, start: float = 0.0) -> None:
        """Tick from `start` until done or until `until`, whichever comes first."""
        tick_number = 0
        while self.done_at is None and (time := start + tick_number * TICK) <= until:
            self.tick(time)
            tick_number += 1

    def tick(self, time: float) -> None:
        if self._land_requested_at is not None and time >= self._land_requested_at + self._landing_lag:
            self._status = ARMED
        requests_before = len(self.safety_layer.requests)
        is_done = self.hover_test.tick(snapshot(time, self._status, self._height), self.safety_layer)
        for command_request in self.safety_layer.requests[requests_before:]:
            self.timeline.append(TimedRequest(time, command_request))
            match command_request:
                case Arm():
                    self._status = ARMED
                case TakeOff(height=height):
                    self._status, self._height = FLYING, height
                case Land():
                    self._height, self._land_requested_at = 0.0, time + TICK
                case _:
                    pass
        if is_done:
            self.done_at = time

    def times_of(self, command_request: CommandRequest) -> list[float]:
        return [timed.time for timed in self.timeline if timed.request == command_request]

    def time_of(self, command_request: CommandRequest) -> float:
        (time,) = self.times_of(command_request)
        return time

    def buzzer_requests(self) -> list[TimedRequest]:
        return [timed for timed in self.timeline if isinstance(timed.request, Chirp | Tone | Silence)]


def on_its_tick(time: float, due: float) -> bool:
    """Whether `time` is the first tick at or after `due`."""
    return due <= time < due + TICK


def test_with_chirps_it_chirps_on_the_floor_first() -> None:
    safety_layer = SafetyLayerStandIn()

    HoverTest(chirp=True).tick(snapshot(0.0, ON_THE_FLOOR), safety_layer)

    assert safety_layer.requests == [Chirp()]


def test_with_chirps_it_arms_once_the_floor_wait_is_over() -> None:
    flight = ScriptedFlight(HoverTest(LONG_HOVER, chirp=True))

    flight.run(until=FLOOR_CHIRP_WAIT + 1.0)

    assert flight.timeline[0] == TimedRequest(0.0, Chirp())
    assert on_its_tick(flight.time_of(Arm()), due=FLOOR_CHIRP_WAIT)


def test_with_chirps_it_chirps_every_period_from_the_take_off_until_the_drone_status_says_landed() -> None:
    flight = ScriptedFlight(HoverTest(LONG_HOVER, chirp=True))

    flight.run(until=60.0)

    take_off = flight.time_of(TakeOff(TAKE_OFF_HEIGHT))
    landed = flight.time_of(Land()) + TICK  # the stand-in drone's status says landed a tick after the request
    chirps_in_flight = [time for time in flight.times_of(Chirp()) if take_off <= time < landed]
    assert len(chirps_in_flight) == 2  # in 12 s of hover
    for number, time in enumerate(chirps_in_flight, start=1):
        assert on_its_tick(time, due=take_off + number * CHIRP_PERIOD)


def test_with_chirps_it_goes_on_chirping_while_the_drone_status_still_says_flying() -> None:
    """The status lags a landing (glossary: Drone status)."""
    flight = ScriptedFlight(HoverTest(hover_duration=0.0, chirp=True), landing_lag=8.0)

    flight.run(until=60.0)

    take_off = flight.time_of(TakeOff(TAKE_OFF_HEIGHT))
    landed = flight.time_of(Land()) + TICK + 8.0
    chirps_in_flight = [time for time in flight.times_of(Chirp()) if take_off <= time < landed]
    assert len(chirps_in_flight) == 1
    assert on_its_tick(chirps_in_flight[0], due=take_off + CHIRP_PERIOD)


def test_with_chirps_it_chirps_after_landing_then_plays_charge_then_silence() -> None:
    flight = ScriptedFlight(HoverTest(LONG_HOVER, chirp=True))

    flight.run(until=60.0)

    landed = flight.time_of(Land()) + TICK
    chirp_after_landing, *charge_notes, silence = [timed for timed in flight.buzzer_requests() if timed.time >= landed]
    assert chirp_after_landing.request == Chirp()
    assert on_its_tick(chirp_after_landing.time, due=landed + LANDED_CHIRP_DELAY)
    note_start = chirp_after_landing.time + CHARGE_WAIT
    assert len(charge_notes) == len(CHARGE)
    for timed, note in zip(charge_notes, CHARGE, strict=True):
        assert timed.request == Tone(note_pitch(note.name, 4 + note.octaves_up))
        assert on_its_tick(timed.time, due=note_start)
        note_start += note.length
    assert silence.request == Silence()
    assert on_its_tick(silence.time, due=note_start)


def test_with_chirps_it_is_done_only_after_the_silence_hold() -> None:
    flight = ScriptedFlight(HoverTest(LONG_HOVER, chirp=True))

    flight.run(until=60.0)

    assert flight.done_at is not None
    assert on_its_tick(flight.done_at, due=flight.time_of(Silence()) + SILENCE_HOLD)
    assert flight.timeline[-1].request == Silence()


def test_charge_is_the_bugle_call_g4_c5_e5_g5_e5_g5() -> None:
    pitches = [note_pitch(note.name, 4 + note.octaves_up) for note in CHARGE]

    assert note_pitch("A", 4) == 440.0
    assert pitches == pytest.approx([392.00, 523.25, 659.26, 783.99, 659.26, 783.99], abs=0.01)
    assert [note.length for note in CHARGE] == pytest.approx([0.150, 0.150, 0.150, 0.300, 0.150, 0.600])


def test_a_note_that_falls_between_two_ticks_is_skipped_so_the_rest_stay_on_time() -> None:
    flight = ScriptedFlight(HoverTest(hover_duration=0.0, chirp=True))
    flight.run(until=60.0)
    first_note = flight.buzzer_requests()[-len(CHARGE) - 1]
    replay = ScriptedFlight(HoverTest(hover_duration=0.0, chirp=True))
    replay.run(until=first_note.time)

    replay.tick(first_note.time + 0.5)  # 0.45-0.75 s into "Charge": the fourth note, G5

    assert [timed.request for timed in replay.timeline[-2:]] == [first_note.request, Tone(note_pitch("G", 5))]


def test_in_flight_chirps_after_a_long_gap_between_ticks_restart_the_period_instead_of_catching_up() -> None:
    flight = ScriptedFlight(HoverTest(hover_duration=60.0, chirp=True))
    flight.run(until=FLOOR_CHIRP_WAIT + 1.0)
    take_off = flight.time_of(TakeOff(TAKE_OFF_HEIGHT))
    late_tick = take_off + 2.5 * CHIRP_PERIOD  # two chirps late

    flight.tick(late_tick)
    flight.run(start=late_tick + TICK, until=late_tick + 1.5 * CHIRP_PERIOD)

    chirps_after_the_gap = [time for time in flight.times_of(Chirp()) if time >= late_tick]
    assert len(chirps_after_the_gap) == 2
    assert chirps_after_the_gap[0] == late_tick
    assert on_its_tick(chirps_after_the_gap[1], due=late_tick + CHIRP_PERIOD)


def test_a_refused_chirp_ends_the_hover_test(caplog: pytest.LogCaptureFixture) -> None:
    safety_layer = SafetyLayerStandIn(refuse_with="made-up reason")

    is_done = HoverTest(chirp=True).tick(snapshot(0.0, ON_THE_FLOOR), safety_layer)

    assert is_done
    assert errors_in(caplog) == ["Hover test failed: Chirp() was refused: made-up reason"]


def test_without_chirps_it_never_asks_for_the_buzzer() -> None:
    flight = ScriptedFlight(HoverTest(LONG_HOVER))

    flight.run(until=60.0)

    assert flight.done_at is not None
    assert flight.buzzer_requests() == []
