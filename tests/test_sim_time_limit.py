"""The sim time limit of the `sim_clock` fixture (ADR-0080, ADR-0082)."""

import pytest

from crazyflie_behavior.timing.clock import SimClock

LIMIT = 120.0
"""ADR-0080's limit. `conftest.py` can't be imported under `--import-mode=importlib`."""


def test_a_wait_past_the_sim_time_limit_fails_the_test(sim_clock: SimClock) -> None:
    with pytest.raises(pytest.fail.Exception, match="120 s of sim time"):
        sim_clock.sleep_until(LIMIT + 0.05)


def test_a_wait_up_to_the_sim_time_limit_is_allowed(sim_clock: SimClock) -> None:
    sim_clock.sleep_until(LIMIT)

    assert sim_clock.now() == LIMIT


def test_the_failure_isnt_an_exception_that_except_exception_would_catch(sim_clock: SimClock) -> None:
    with pytest.raises(BaseException, match="sim time") as failure:
        sim_clock.sleep_until(LIMIT + 0.05)

    assert not isinstance(failure.value, Exception)
