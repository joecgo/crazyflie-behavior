"""Command requests and verdicts (ADR-0030)."""

import math

import pytest

from crazyflie_behavior.safety.requests import TakeOff, Verdict


@pytest.mark.parametrize("height", [0.0, -0.5, math.nan, math.inf])
def test_a_take_off_height_that_isnt_positive_is_a_bug(height: float) -> None:
    with pytest.raises(ValueError, match="height"):
        TakeOff(height)


def test_an_approved_verdict_has_no_reason() -> None:
    assert Verdict.approved() == Verdict(is_approved=True, reason="")


def test_a_refused_verdict_says_why() -> None:
    verdict = Verdict.refused("the drone isn't armed")

    assert not verdict.is_approved
    assert verdict.reason == "the drone isn't armed"
