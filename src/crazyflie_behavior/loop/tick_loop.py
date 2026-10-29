"""The tick loop: calls the tick step at the tick rate and keeps time (ADR-0024, ADR-0026).

The loop is only a timer. It doesn't know what a tick does: the tick step holds
the order (snapshot, safety pre-check, behaviors, send). A fitness function
keeps this module from importing anything that does a tick's work.
"""

import faulthandler
import gc
import logging
import math
import threading
from abc import ABC, abstractmethod
from typing import TextIO

from crazyflie_behavior.timing.clock import Clock

logger = logging.getLogger(__name__)

TICK_RATE = 20.0
"""Ticks per second (ADR-0023)."""

HANG_TIMEOUT = 1.0
"""Seconds a tick may run before the hang watchdog reports it (ADR-0026). Well
below the firmware's ~2 s setpoint timeout, so the report comes before a drop."""


class TickStep(ABC):
    """What one tick does, in a fixed order. The tick loop calls it once per tick."""

    @abstractmethod
    def run(self, time: float, dt: float) -> bool:
        """Do one tick's work. Return True when the job is done and the loop should stop.

        `time` is when this tick started, in seconds. `dt` is the seconds since
        the previous tick started, or 0.0 on the first tick.
        """


class HangWatchdog:
    """Reports a tick that runs longer than `timeout` seconds (ADR-0026).

    It writes every thread's stack trace to `file`, the run's log file, and
    only reports: acting on a hang is backlog #26. It uses `faulthandler`,
    which runs in C, so it works even when Python itself is stuck. It counts
    real time, not the injected clock.
    """

    def __init__(self, file: TextIO, timeout: float = HANG_TIMEOUT) -> None:
        if timeout <= 0.0:
            raise ValueError(f"The hang timeout must be positive: {timeout}")
        # faulthandler writes to the operating system's file descriptor, so
        # check there is one now, before take-off, not at the first tick.
        try:
            file.fileno()
        except (OSError, ValueError) as error:
            raise ValueError(
                f"The hang watchdog needs a real file, such as the run's log file: {file!r}"
            ) from error
        self._file = file
        self._timeout = timeout

    def arm(self) -> None:
        """Start counting down for one tick."""
        # Each call starts a small native thread, about 0.1 ms on Linux.
        faulthandler.dump_traceback_later(self._timeout, file=self._file)

    def disarm(self) -> None:
        """Stop counting down: the tick finished in time."""
        faulthandler.cancel_dump_traceback_later()


class _GarbageCollectorPauses:
    """Measures every garbage-collector pause while the loop runs (ADR-0024).

    Python calls `on_collection` from whichever thread set off the collection,
    cflib's included, so it only records numbers. Logging from inside a
    collection could re-enter the logging module halfway through a message.
    """

    def __init__(self, clock: Clock) -> None:
        self._clock = clock
        self._started_at: float | None = None
        self._count_before_tick = 0
        self._total_before_tick = 0.0
        self.count = 0
        self.total = 0.0
        self.worst = 0.0

    def on_collection(self, phase: str, _info: dict[str, int]) -> None:
        if phase == "start":
            self._started_at = self._clock.now()
        elif self._started_at is not None:
            pause = self._clock.now() - self._started_at
            self._started_at = None
            self.count += 1
            self.total += pause
            self.worst = max(self.worst, pause)

    def start_tick(self) -> None:
        """Start counting this tick's pauses."""
        self._count_before_tick = self.count
        self._total_before_tick = self.total

    @property
    def count_this_tick(self) -> int:
        return self.count - self._count_before_tick

    @property
    def total_this_tick(self) -> float:
        return self.total - self._total_before_tick


class _TimingRecord:
    """Every tick's lateness and work time, for the summary at the end of a run."""

    def __init__(self) -> None:
        self.lateness: list[float] = []
        self.work_time: list[float] = []
        self.overrun_count = 0

    @property
    def tick_count(self) -> int:
        return len(self.work_time)

    def add(self, lateness: float, work_time: float) -> None:
        self.lateness.append(lateness)
        self.work_time.append(work_time)

    def summary(self, pauses: _GarbageCollectorPauses) -> str:
        if self.tick_count == 0:
            return "no ticks ran"
        return (
            f"ticks: {self.tick_count}, overruns: {self.overrun_count}. "
            f"Lateness: worst {_ms(max(self.lateness))}, "
            f"99th percentile {_ms(_percentile_99(self.lateness))}. "
            f"Work time: worst {_ms(max(self.work_time))}, "
            f"99th percentile {_ms(_percentile_99(self.work_time))}. "
            f"Garbage collector: pauses: {pauses.count}, worst {_ms(pauses.worst)}, "
            f"total {_ms(pauses.total)}."
        )


def _percentile_99(values: list[float]) -> float:
    """The nearest-rank 99th percentile: the smallest value at or above 99% of them."""
    ordered = sorted(values)
    return ordered[math.ceil(0.99 * len(ordered)) - 1]


def _ms(seconds: float) -> str:
    """Seconds shown as milliseconds, for log messages."""
    return f"{seconds * 1000.0:.2f} ms"


class TickLoop:
    """Calls the tick step at the tick rate until it's done or a stop request arrives.

    Due times follow ADR-0024: each one is the previous due time plus one tick
    period, so a late start shortens the next wait instead of adding up. After
    an overrun the next tick starts at once and the beat restarts from there;
    missed ticks are skipped, never caught up.

    Errors from the tick step aren't caught here. They rise to the caller's
    `with drone:` block, which lands (ADR-0026).
    """

    def __init__(
        self,
        clock: Clock,
        tick_step: TickStep,
        hang_watchdog: HangWatchdog,
        tick_rate: float = TICK_RATE,
    ) -> None:
        if tick_rate <= 0.0:
            raise ValueError(f"The tick rate must be positive: {tick_rate}")
        self._clock = clock
        self._tick_step = tick_step
        self._hang_watchdog = hang_watchdog
        self._tick_rate = tick_rate
        self._tick_period = 1.0 / tick_rate
        self._stop_requested = threading.Event()

    def request_stop(self) -> None:
        """Make a stop request: the loop returns after the current tick. Safe from any thread."""
        self._stop_requested.set()

    def run(self) -> None:
        """Run ticks until the tick step reports it's done or a stop request arrives."""
        record = _TimingRecord()
        pauses = _GarbageCollectorPauses(self._clock)
        gc.callbacks.append(pauses.on_collection)
        logger.info("Tick loop starting at %g Hz", self._tick_rate)
        try:
            self._run_ticks(record, pauses)
        finally:
            # Also on an error, so the log shows how the loop was keeping time.
            gc.callbacks.remove(pauses.on_collection)
            logger.info("Tick loop summary: %s", record.summary(pauses))

    def _run_ticks(self, record: _TimingRecord, pauses: _GarbageCollectorPauses) -> None:
        due_time = self._clock.now()
        previous_start: float | None = None
        while True:
            self._clock.sleep_until(due_time)
            if self._stop_requested.is_set():
                self._log_stop_request(record)
                return

            start = self._clock.now()
            dt = 0.0 if previous_start is None else start - previous_start
            previous_start = start
            pauses.start_tick()
            try:
                # Watched until the tick's logging is done too, so a hang there
                # (a blocked console, say) is also reported.
                self._hang_watchdog.arm()
                done = self._tick_step.run(start, dt)
                due_time = self._finish_tick(record, pauses, due_time, start)
            finally:
                self._hang_watchdog.disarm()

            if done:
                logger.info("Tick step done: tick loop stopping (ticks run: %d)", record.tick_count)
                return
            if self._stop_requested.is_set():
                self._log_stop_request(record)
                return

    def _finish_tick(
        self,
        record: _TimingRecord,
        pauses: _GarbageCollectorPauses,
        due_time: float,
        start: float,
    ) -> float:
        """Record and log the tick that just ran. Returns the next tick's due time."""
        end = self._clock.now()
        tick_number = record.tick_count
        lateness = start - due_time
        work_time = end - start  # includes arming the hang watchdog
        record.add(lateness, work_time)
        if logger.isEnabledFor(logging.DEBUG):
            message = f"Tick {tick_number}: lateness {_ms(lateness)}, work time {_ms(work_time)}"
            if pauses.count_this_tick > 0:
                message += (
                    f", garbage collector {_ms(pauses.total_this_tick)}"
                    f" (pauses: {pauses.count_this_tick})"
                )
            logger.debug(message)

        next_due_time = due_time + self._tick_period
        if end <= next_due_time:
            return next_due_time
        # Overrun: start the next tick at once and restart the beat from here,
        # never catching up (ADR-0024). Every overrun gets its own warning, even
        # several in a row, and even on the last tick (ADR-0026).
        record.overrun_count += 1
        logger.warning(
            "Overrun on tick %d: work time %s, %s past the next due time",
            tick_number,
            _ms(work_time),
            _ms(end - next_due_time),
        )
        return end

    def _log_stop_request(self, record: _TimingRecord) -> None:
        logger.info("Stop request: tick loop stopping (ticks run: %d)", record.tick_count)
