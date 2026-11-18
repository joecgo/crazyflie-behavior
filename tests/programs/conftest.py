"""Fixtures for the program tests."""

import pytest

from crazyflie_behavior.timing.clock import SimClock

PROGRAM_TEST_TIME_LIMIT = 120.0
"""How much sim time a program test may run before it fails (ADR-0080)."""


class TimeLimitedSimClock(SimClock):
    """A sim clock that fails the test when a program runs past the time limit, instead of running forever."""

    def __init__(self, start: float = 0.0) -> None:
        super().__init__(start)
        self._fail_after = start + PROGRAM_TEST_TIME_LIMIT

    def sleep_until(self, deadline: float) -> None:
        if deadline > self._fail_after:
            # pytest.fail, not an AssertionError, which run_program would turn into exit code 1 (ADR-0080).
            pytest.fail(f"The program was still running after {PROGRAM_TEST_TIME_LIMIT:g} s of sim time")
        super().sleep_until(deadline)


@pytest.fixture
def sim_clock() -> SimClock:
    """A sim clock with the program test time limit (ADR-0080)."""
    return TimeLimitedSimClock()
