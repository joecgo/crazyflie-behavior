"""The clock interface and its real and simulated implementations (ADR-0009).

The tick loop, adapters and safety layer receive a clock instead of reading the
computer's time directly. Behaviors never hold a clock: they receive the tick's
time in the snapshot.
"""

import time
from abc import ABC, abstractmethod


class Clock(ABC):
    """A source of time, in seconds. Only differences between readings matter."""

    @abstractmethod
    def now(self) -> float:
        """The current time in seconds."""

    @abstractmethod
    def sleep_until(self, deadline: float) -> None:
        """Wait until `now()` reaches `deadline`. Returns at once if it already has."""


class RealClock(Clock):
    """The computer's own time.

    Uses `time.perf_counter`, not `time.monotonic`: on Windows, `monotonic` only
    ticks every ~15.6 ms, while `perf_counter` resolves well under a microsecond.
    Both are monotonic (they never jump backward).

    Deadline scheduling, sleep-then-spin and garbage-collector control belong
    to the backlog item "Tick timing strategy"; this is the simple version.
    """

    def now(self) -> float:
        return time.perf_counter()

    def sleep_until(self, deadline: float) -> None:
        # time.sleep uses a different OS timer than perf_counter and can wake
        # a hair early, so keep sleeping until this clock agrees.
        while (remaining := deadline - self.now()) > 0.0:
            time.sleep(remaining)


class SimClock(Clock):
    """A clock that only moves when told to.

    Sleeping jumps straight to the deadline, so simulated time runs as fast as
    the code does, and every run gives exactly the same times. Single-threaded
    by design: simulations and tests drive it from one thread.
    """

    def __init__(self, start: float = 0.0) -> None:
        self._time = start

    def now(self) -> float:
        return self._time

    def sleep_until(self, deadline: float) -> None:
        self._time = max(self._time, deadline)

    def advance(self, duration: float) -> None:
        """Move time forward by `duration` seconds."""
        if duration < 0.0:
            raise ValueError(f"Time can't go backward: {duration}")
        self._time += duration
