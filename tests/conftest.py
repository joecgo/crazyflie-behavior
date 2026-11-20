"""Fixtures shared by every test folder."""

import pytest

from crazyflie_behavior.timing.clock import SimClock

SIM_TIME_LIMIT = 120.0
"""How much sim time a test may run before it fails (ADR-0080, ADR-0082)."""


class TimeLimitedSimClock(SimClock):
    """A sim clock that fails the test when a loop runs past the time limit, instead of running forever."""

    def sleep_until(self, deadline: float) -> None:
        if deadline > SIM_TIME_LIMIT:
            # pytest.fail, not an AssertionError, which run_program would turn into exit code 1 (ADR-0080).
            pytest.fail(f"Still running after {SIM_TIME_LIMIT:g} s of sim time")
        super().sleep_until(deadline)


@pytest.fixture
def sim_clock() -> SimClock:
    """A sim clock with the sim time limit (ADR-0080, ADR-0082)."""
    return TimeLimitedSimClock()
