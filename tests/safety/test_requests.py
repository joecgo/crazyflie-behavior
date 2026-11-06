"""Command requests and verdicts (ADR-0030, ADR-0053)."""

import math

import pytest

from crazyflie_behavior.safety.requests import MAX_TONE_PITCH, MIN_TONE_PITCH, TakeOff, Tone, Verdict


@pytest.mark.parametrize("height", [0.0, -0.5, math.nan, math.inf])
def test_a_take_off_height_that_isnt_positive_is_a_bug(height: float) -> None:
    with pytest.raises(ValueError, match="height"):
        TakeOff(height)


def test_a_tone_from_the_lowest_to_the_highest_pitch_people_hear_is_allowed() -> None:
    assert Tone(MIN_TONE_PITCH).pitch == MIN_TONE_PITCH
    assert Tone(MAX_TONE_PITCH).pitch == MAX_TONE_PITCH


@pytest.mark.parametrize("pitch", [MIN_TONE_PITCH - 0.5, MAX_TONE_PITCH + 0.5, 0.0, math.nan, math.inf])
def test_a_tone_pitch_people_cant_hear_is_a_bug(pitch: float) -> None:
    with pytest.raises(ValueError, match="Tone pitch must be 20-20000 Hz"):
        Tone(pitch)


def test_an_approved_verdict_has_no_reason() -> None:
    assert Verdict.approved() == Verdict(is_approved=True, reason="")


def test_a_refused_verdict_says_why() -> None:
    verdict = Verdict.refused("the drone isn't armed")

    assert not verdict.is_approved
    assert verdict.reason == "the drone isn't armed"


@pytest.mark.parametrize(("is_approved", "reason"), [(False, ""), (True, "the drone isn't armed")])
def test_a_refusal_without_a_reason_or_an_approval_with_one_is_a_bug(is_approved: bool, reason: str) -> None:
    with pytest.raises(ValueError, match="reason"):
        Verdict(is_approved=is_approved, reason=reason)
