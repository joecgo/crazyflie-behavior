"""The tick loop (ADR-0024, ADR-0026), driven by a sim clock and fake tick steps.

Most tests tick at 4 Hz: quarter-second periods keep every time exact in
binary, so start times can be compared with `==`. Only the hang watchdog's own
tests wait in real time, because `faulthandler` counts real time.
"""

import gc
import io
import logging
import sys
import threading
import time
from pathlib import Path
from typing import NamedTuple

import pytest

from crazyflie_behavior.drone.mock_adapter import SETPOINT_CUT_MOTORS_AFTER
from crazyflie_behavior.loop.tick_loop import (
    HANG_TIMEOUT,
    TICK_RATE,
    HangWatchdog,
    TickLoop,
    TickStep,
)
from crazyflie_behavior.timing.clock import SimClock

TEST_TICK_RATE = 4.0
LOGGER_NAME = "crazyflie_behavior.loop.tick_loop"
GIVE_UP_AFTER_TICKS = 100
"""Fakes that would otherwise tick forever report done after this many ticks, so
a broken stop or error path fails its test instead of hanging it."""


class TickCall(NamedTuple):
    time: float
    dt: float


class ScriptedTickStep(TickStep):
    """A fake tick step: each tick takes the next scripted work time; done after the last."""

    def __init__(self, clock: SimClock, work_times: list[float]) -> None:
        self._clock = clock
        self._work_times = work_times
        self.calls: list[TickCall] = []

    def run(self, time: float, dt: float) -> bool:
        self.calls.append(TickCall(time, dt))
        self._clock.advance(self._work_times[len(self.calls) - 1])
        return len(self.calls) == len(self._work_times)

    @property
    def start_times(self) -> list[float]:
        return [call.time for call in self.calls]


class FakeHangWatchdog(HangWatchdog):
    """Records arming and disarming instead of starting a real countdown."""

    def __init__(self, events: list[str] | None = None) -> None:
        # No super().__init__(): this fake never touches a file.
        self.events = events if events is not None else []

    def arm(self) -> None:
        self.events.append("arm")

    def disarm(self) -> None:
        self.events.append("disarm")


class LateWakingClock(SimClock):
    """A sim clock whose every wait wakes a little late, as a real operating system does."""

    def __init__(self, wake_lateness: float) -> None:
        super().__init__()
        self._wake_lateness = wake_lateness

    def sleep_until(self, deadline: float) -> None:
        if deadline > self.now():
            super().sleep_until(deadline + self._wake_lateness)


def make_loop(
    clock: SimClock, tick_step: TickStep, hang_watchdog: HangWatchdog | None = None
) -> TickLoop:
    return TickLoop(clock, tick_step, hang_watchdog or FakeHangWatchdog(), TEST_TICK_RATE)


def messages(caplog: pytest.LogCaptureFixture, level: int) -> list[str]:
    return [record.getMessage() for record in caplog.records if record.levelno == level]


# --- Due times (ADR-0024) -----------------------------------------------------


def test_ticks_start_one_tick_period_apart() -> None:
    clock = SimClock()
    tick_step = ScriptedTickStep(clock, [0.125, 0.125, 0.125])

    make_loop(clock, tick_step).run()

    assert tick_step.start_times == [0.0, 0.25, 0.5]


def test_a_late_start_shortens_the_next_wait_so_lateness_never_adds_up() -> None:
    clock = LateWakingClock(wake_lateness=1 / 64)
    tick_step = ScriptedTickStep(clock, [0.125, 0.125, 0.125, 0.125])

    make_loop(clock, tick_step).run()

    # Every wait wakes 1/64 s late, yet each tick stays on the beat.
    assert tick_step.start_times == [0.0, 0.25 + 1 / 64, 0.5 + 1 / 64, 0.75 + 1 / 64]


def test_after_an_overrun_the_next_tick_starts_at_once_and_the_beat_restarts() -> None:
    clock = SimClock()
    tick_step = ScriptedTickStep(clock, [0.375, 0.125, 0.125])

    make_loop(clock, tick_step).run()

    assert tick_step.start_times == [0.0, 0.375, 0.625]


def test_missed_ticks_are_skipped_never_caught_up() -> None:
    clock = SimClock()
    tick_step = ScriptedTickStep(clock, [0.875, 0.125, 0.125])

    make_loop(clock, tick_step).run()

    # The ticks due at 0.25, 0.5 and 0.75 never run.
    assert tick_step.start_times == [0.0, 0.875, 1.125]


def test_a_tick_that_ends_exactly_at_the_next_due_time_is_not_an_overrun(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.WARNING, logger=LOGGER_NAME)
    clock = SimClock()
    tick_step = ScriptedTickStep(clock, [0.25, 0.125])

    make_loop(clock, tick_step).run()

    assert tick_step.start_times == [0.0, 0.25]
    assert messages(caplog, logging.WARNING) == []


def test_dt_is_zero_on_the_first_tick_then_the_time_since_the_previous_start() -> None:
    clock = SimClock()
    tick_step = ScriptedTickStep(clock, [0.375, 0.125, 0.125])

    make_loop(clock, tick_step).run()

    assert [call.dt for call in tick_step.calls] == [0.0, 0.375, 0.25]


def test_the_default_tick_rate_is_20_hz() -> None:
    clock = SimClock()
    tick_step = ScriptedTickStep(clock, [0.01, 0.01, 0.01])

    TickLoop(clock, tick_step, FakeHangWatchdog()).run()

    assert TICK_RATE == 20.0
    assert tick_step.start_times == pytest.approx([0.0, 0.05, 0.1])


def test_the_tick_rate_must_be_positive() -> None:
    clock = SimClock()

    with pytest.raises(ValueError, match="positive"):
        TickLoop(clock, ScriptedTickStep(clock, [0.1]), FakeHangWatchdog(), tick_rate=0.0)


# --- Stopping and errors (ADR-0026) ----------------------------------------------


class StopRequestingTickStep(TickStep):
    """A fake tick step that makes a stop request on one tick, and otherwise keeps going."""

    def __init__(
        self,
        stop_on_tick: int,
        from_another_thread: bool = False,
        clock: SimClock | None = None,
        work_time: float = 0.0,
    ) -> None:
        self._stop_on_tick = stop_on_tick
        self._from_another_thread = from_another_thread
        self._clock = clock
        self._work_time = work_time
        self.loop: TickLoop | None = None
        self.tick_count = 0

    def run(self, time: float, dt: float) -> bool:
        if self._clock is not None:
            self._clock.advance(self._work_time)
        if self.tick_count == self._stop_on_tick:
            assert self.loop is not None
            if self._from_another_thread:
                other_thread = threading.Thread(target=self.loop.request_stop)
                other_thread.start()
                other_thread.join()
            else:
                self.loop.request_stop()
        self.tick_count += 1
        return self.tick_count == GIVE_UP_AFTER_TICKS


def test_the_loop_stops_when_the_tick_step_is_done() -> None:
    clock = SimClock()
    tick_step = ScriptedTickStep(clock, [0.125, 0.125, 0.125])

    make_loop(clock, tick_step).run()

    assert len(tick_step.calls) == 3


def test_a_stop_request_lets_the_current_tick_finish_and_starts_no_more() -> None:
    tick_step = StopRequestingTickStep(stop_on_tick=1)
    loop = make_loop(SimClock(), tick_step)
    tick_step.loop = loop

    loop.run()

    assert tick_step.tick_count == 2


def test_a_stop_request_during_a_tick_returns_without_waiting_for_the_next_due_time() -> None:
    clock = SimClock()
    tick_step = StopRequestingTickStep(stop_on_tick=0, clock=clock, work_time=0.125)
    loop = make_loop(clock, tick_step)
    tick_step.loop = loop

    loop.run()

    # The tick ended at 0.125; the next one was due at 0.25.
    assert clock.now() == 0.125


def test_a_stop_request_can_come_from_another_thread() -> None:
    tick_step = StopRequestingTickStep(stop_on_tick=0, from_another_thread=True)
    loop = make_loop(SimClock(), tick_step)
    tick_step.loop = loop

    loop.run()

    assert tick_step.tick_count == 1


def test_a_stop_request_before_the_loop_runs_starts_no_ticks() -> None:
    clock = SimClock()
    tick_step = ScriptedTickStep(clock, [0.125])
    loop = make_loop(clock, tick_step)

    loop.request_stop()
    loop.run()

    assert tick_step.calls == []


class FailingTickStep(TickStep):
    """A fake tick step that raises on one tick."""

    def __init__(self, fail_on_tick: int, events: list[str] | None = None) -> None:
        self._fail_on_tick = fail_on_tick
        self._events = events if events is not None else []
        self.tick_count = 0

    def run(self, time: float, dt: float) -> bool:
        self._events.append("tick")
        tick_number = self.tick_count
        self.tick_count += 1
        if tick_number == self._fail_on_tick:
            raise RuntimeError("the tick step broke")
        return self.tick_count == GIVE_UP_AFTER_TICKS


def test_errors_from_the_tick_step_rise_to_the_caller() -> None:
    loop = make_loop(SimClock(), FailingTickStep(fail_on_tick=1))

    # In a program, this reaches the `with drone:` block, which lands.
    with pytest.raises(RuntimeError, match="the tick step broke"):
        loop.run()


# --- The hang watchdog (ADR-0026) ----------------------------------------------


class RecordingTickStep(TickStep):
    """A fake tick step that writes each tick into a shared event list."""

    def __init__(self, events: list[str], tick_count: int) -> None:
        self._events = events
        self._tick_count = tick_count
        self._ticks_run = 0

    def run(self, time: float, dt: float) -> bool:
        self._events.append("tick")
        self._ticks_run += 1
        return self._ticks_run == self._tick_count


def test_the_hang_watchdog_is_armed_for_each_tick_and_disarmed_after_it() -> None:
    events: list[str] = []

    make_loop(SimClock(), RecordingTickStep(events, tick_count=2), FakeHangWatchdog(events)).run()

    assert events == ["arm", "tick", "disarm", "arm", "tick", "disarm"]


def test_the_hang_watchdog_is_disarmed_even_when_the_tick_step_raises() -> None:
    events: list[str] = []
    loop = make_loop(
        SimClock(), FailingTickStep(fail_on_tick=0, events=events), FakeHangWatchdog(events)
    )

    with pytest.raises(RuntimeError):
        loop.run()

    assert events == ["arm", "tick", "disarm"]


def test_the_hang_watchdog_writes_every_threads_stack_trace_when_a_tick_hangs(
    tmp_path: Path,
) -> None:
    log_path = tmp_path / "hang.log"
    with log_path.open("w") as log_file:
        hang_watchdog = HangWatchdog(log_file, timeout=0.05)

        hang_watchdog.arm()
        time.sleep(0.5)  # a "hung" tick, in real time
        hang_watchdog.disarm()

    trace = log_path.read_text()
    assert "Timeout" in trace
    assert "most recent call first" in trace
    # The trace points at the code that hung.
    assert "test_the_hang_watchdog_writes_every_threads_stack_trace_when_a_tick_hangs" in trace


def test_a_disarmed_hang_watchdog_writes_nothing(tmp_path: Path) -> None:
    log_path = tmp_path / "hang.log"
    with log_path.open("w") as log_file:
        hang_watchdog = HangWatchdog(log_file, timeout=0.05)

        hang_watchdog.arm()
        hang_watchdog.disarm()
        time.sleep(0.2)

    assert log_path.read_text() == ""


class EventLogHandler(logging.Handler):
    """Writes each log record into a shared event list, to check what the watchdog watches."""

    def __init__(self, events: list[str]) -> None:
        super().__init__(logging.DEBUG)
        self._events = events

    def emit(self, record: logging.LogRecord) -> None:
        self._events.append("log")


def test_the_hang_watchdog_also_watches_the_ticks_logging(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger=LOGGER_NAME)
    events: list[str] = []
    handler = EventLogHandler(events)
    tick_loop_logger = logging.getLogger(LOGGER_NAME)
    tick_loop_logger.addHandler(handler)
    loop = make_loop(SimClock(), RecordingTickStep(events, tick_count=1), FakeHangWatchdog(events))
    try:
        loop.run()
    finally:
        tick_loop_logger.removeHandler(handler)

    # A blocked console or log file during the tick's logging is still reported.
    tick_events = events[events.index("arm") : events.index("disarm") + 1]
    assert tick_events == ["arm", "tick", "log", "disarm"]


def test_a_real_hang_watchdog_writes_nothing_when_ticks_finish_in_time(tmp_path: Path) -> None:
    log_path = tmp_path / "run.log"
    clock = SimClock()
    with log_path.open("w") as log_file:
        loop = make_loop(clock, ScriptedTickStep(clock, [0.125, 0.125]), HangWatchdog(log_file))

        loop.run()

    assert log_path.read_text() == ""


def test_the_hang_watchdog_refuses_a_file_without_a_file_descriptor() -> None:
    # faulthandler writes to the operating system's file descriptor directly.
    with pytest.raises(ValueError, match="real file"):
        HangWatchdog(io.StringIO())


def test_the_hang_timeout_reports_before_the_firmware_cuts_the_motors() -> None:
    assert HANG_TIMEOUT < SETPOINT_CUT_MOTORS_AFTER


def test_the_hang_timeout_must_be_positive() -> None:
    with pytest.raises(ValueError, match="positive"):
        HangWatchdog(sys.stderr, timeout=0.0)


# --- Logging (ADR-0026) ----------------------------------------------------------


def test_every_tick_is_logged_at_debug_level_with_its_lateness_and_work_time(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger=LOGGER_NAME)
    clock = SimClock()

    make_loop(clock, ScriptedTickStep(clock, [0.125, 0.375])).run()

    assert messages(caplog, logging.DEBUG) == [
        "Tick 0: lateness 0.00 ms, work time 125.00 ms",
        "Tick 1: lateness 0.00 ms, work time 375.00 ms",
    ]


def test_every_overrun_is_logged_as_a_warning_even_several_in_a_row(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.WARNING, logger=LOGGER_NAME)
    clock = SimClock()

    make_loop(clock, ScriptedTickStep(clock, [0.375, 0.375, 0.375, 0.125])).run()

    assert messages(caplog, logging.WARNING) == [
        "Overrun on tick 0: work time 375.00 ms, 125.00 ms past the next due time",
        "Overrun on tick 1: work time 375.00 ms, 125.00 ms past the next due time",
        "Overrun on tick 2: work time 375.00 ms, 125.00 ms past the next due time",
    ]


def test_an_overrun_on_the_last_tick_is_logged_too(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger=LOGGER_NAME)
    clock = SimClock()

    make_loop(clock, ScriptedTickStep(clock, [0.125, 0.375])).run()

    assert messages(caplog, logging.WARNING) == [
        "Overrun on tick 1: work time 375.00 ms, 125.00 ms past the next due time",
    ]
    summaries = [m for m in messages(caplog, logging.INFO) if m.startswith("Tick loop summary")]
    assert "overruns: 1" in summaries[0]


def test_the_log_says_why_the_loop_stopped(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger=LOGGER_NAME)
    clock = SimClock()
    make_loop(clock, ScriptedTickStep(clock, [0.125])).run()
    stopping_tick_step = StopRequestingTickStep(stop_on_tick=1)
    stopping_loop = make_loop(SimClock(), stopping_tick_step)
    stopping_tick_step.loop = stopping_loop
    stopping_loop.run()

    reasons = [m for m in messages(caplog, logging.INFO) if "tick loop stopping" in m]
    assert reasons == [
        "Tick step done: tick loop stopping (ticks run: 1)",
        "Stop request: tick loop stopping (ticks run: 2)",
    ]


def test_the_end_of_a_run_logs_a_summary(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger=LOGGER_NAME)
    clock = SimClock()

    make_loop(clock, ScriptedTickStep(clock, [0.375, 0.125])).run()

    summaries = [m for m in messages(caplog, logging.INFO) if m.startswith("Tick loop summary")]
    assert len(summaries) == 1
    assert "ticks: 2, overruns: 1" in summaries[0]
    assert "Work time: worst 375.00 ms" in summaries[0]


def test_the_summary_is_logged_even_when_the_tick_step_raises(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger=LOGGER_NAME)
    loop = make_loop(SimClock(), FailingTickStep(fail_on_tick=1))

    with pytest.raises(RuntimeError):
        loop.run()

    summaries = [m for m in messages(caplog, logging.INFO) if m.startswith("Tick loop summary")]
    assert len(summaries) == 1
    assert "ticks: 1, overruns: 0" in summaries[0]


# --- Garbage-collector pauses (ADR-0024) -----------------------------------------


class CollectingTickStep(TickStep):
    """A fake tick step that runs the garbage collector on its only tick."""

    def run(self, time: float, dt: float) -> bool:
        gc.collect()
        return True


def test_garbage_collector_pauses_show_in_the_tick_log(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG, logger=LOGGER_NAME)

    make_loop(SimClock(), CollectingTickStep()).run()

    tick_lines = messages(caplog, logging.DEBUG)
    assert len(tick_lines) == 1
    assert "garbage collector" in tick_lines[0]


def test_the_loop_stops_measuring_the_garbage_collector_after_a_run() -> None:
    callbacks_before = list(gc.callbacks)
    clock = SimClock()

    make_loop(clock, ScriptedTickStep(clock, [0.125])).run()

    assert gc.callbacks == callbacks_before
