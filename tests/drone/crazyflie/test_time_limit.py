"""Running a blocking step with a time limit (ADR-0029).

The stuck steps wait in real time, because a stuck library call doesn't care
about a sim clock. On Linux any wait can be interrupted by Ctrl+C; on Windows
only the waiting in short slices makes the Ctrl+C test pass.
"""

# pyright: reportPrivateUsage=false

import logging
import signal
import threading
import time
from collections.abc import Generator

import pytest

from crazyflie_behavior.drone.crazyflie import time_limit as time_limit_module
from crazyflie_behavior.drone.crazyflie.time_limit import run_with_time_limit
from crazyflie_behavior.timing.clock import Clock, RealClock, SimClock

TIME_LIMIT_LOGGER = "crazyflie_behavior.drone.crazyflie.time_limit"


class StuckStep:
    """A fake blocking call: waits until the test releases it, then may raise."""

    def __init__(
        self, error_when_released: BaseException | None = None, press_ctrl_c: bool = False
    ) -> None:
        self.release = threading.Event()
        self._error = error_when_released
        self._press_ctrl_c = press_ctrl_c

    def __call__(self) -> None:
        if self._press_ctrl_c:
            signal.raise_signal(signal.SIGINT)
        self.release.wait(timeout=10.0)
        if self._error is not None:
            raise self._error


@pytest.fixture
def stuck_steps() -> Generator[list[StuckStep]]:
    steps: list[StuckStep] = []
    yield steps
    for step in steps:
        step.release.set()  # let the abandoned helper threads finish


def test_a_step_that_finishes_in_time_returns_normally() -> None:
    results: list[str] = []

    run_with_time_limit("A quick step", lambda: results.append("done"), 1.0, "", SimClock())

    assert results == ["done"]


def test_a_steps_own_error_rises_as_if_it_ran_on_this_thread() -> None:
    def fail() -> None:
        raise RuntimeError("the drone said no")

    with pytest.raises(RuntimeError, match="the drone said no"):
        run_with_time_limit("A failing step", fail, 1.0, "", SimClock())


def test_a_step_past_its_time_limit_raises_naming_the_step_and_what_to_check(
    stuck_steps: list[StuckStep],
) -> None:
    step = StuckStep()
    stuck_steps.append(step)

    with pytest.raises(TimeoutError, match=r"^A stuck step took longer than 0\.2 s\. Check it\.$"):
        run_with_time_limit("A stuck step", step, 0.2, "Check it.", RealClock())


def test_on_abandon_runs_before_the_timeout_rises(stuck_steps: list[StuckStep]) -> None:
    step = StuckStep()
    stuck_steps.append(step)
    events: list[str] = []

    with pytest.raises(TimeoutError):
        run_with_time_limit(
            "A stuck step",
            step,
            0.2,
            "",
            RealClock(),
            on_abandon=lambda: events.append("abandoned"),
        )

    assert events == ["abandoned"]


def test_ctrl_c_gets_through_while_a_step_is_stuck(stuck_steps: list[StuckStep]) -> None:
    step = StuckStep(press_ctrl_c=True)
    stuck_steps.append(step)
    events: list[str] = []
    started = time.monotonic()

    with pytest.raises(KeyboardInterrupt):
        run_with_time_limit(
            "A stuck step",
            step,
            30.0,
            "",
            RealClock(),
            on_abandon=lambda: events.append("abandoned"),
        )

    assert time.monotonic() - started < 2.0  # long before the 30 s limit
    assert events == ["abandoned"]


def test_ctrl_c_the_moment_the_step_starts_still_cleans_up(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    start = time_limit_module._HelperStep.start

    def start_then_ctrl_c(step: time_limit_module._HelperStep) -> None:
        start(step)
        raise KeyboardInterrupt  # as if Ctrl+C landed right as the helper started

    monkeypatch.setattr(time_limit_module._HelperStep, "start", start_then_ctrl_c)
    events: list[str] = []

    with pytest.raises(KeyboardInterrupt):
        run_with_time_limit(
            "A step",
            lambda: None,
            1.0,
            "",
            SimClock(),
            on_abandon=lambda: events.append("abandoned"),
        )

    assert events == ["abandoned"]


def test_an_error_after_a_step_was_abandoned_is_still_logged(
    stuck_steps: list[StuckStep], caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.WARNING, logger=TIME_LIMIT_LOGGER)
    step = StuckStep(error_when_released=RuntimeError("too late"))
    stuck_steps.append(step)

    with pytest.raises(TimeoutError):
        run_with_time_limit("A stuck step", step, 0.2, "", RealClock())
    step.release.set()

    deadline = time.monotonic() + 5.0
    while not caplog.records and time.monotonic() < deadline:
        time.sleep(0.01)
    assert caplog.messages == ["A stuck step ended with an error after its time limit"]
    exc_info = caplog.records[0].exc_info
    assert exc_info is not None
    assert exc_info[2] is not None  # the traceback shows where it failed


def test_a_failing_cleanup_keeps_the_time_limit_message(
    stuck_steps: list[StuckStep], caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.WARNING, logger=TIME_LIMIT_LOGGER)
    step = StuckStep()
    stuck_steps.append(step)

    def broken_cleanup() -> None:
        raise RuntimeError("the link was half open")

    with pytest.raises(TimeoutError, match="A stuck step took longer"):
        run_with_time_limit("A stuck step", step, 0.2, "", RealClock(), on_abandon=broken_cleanup)

    assert "Cleaning up after A stuck step failed" in caplog.messages


class FinishesBetweenWaitAndCheck(Clock):
    """A clock that lets the step finish just after a wait slice gave up, then reads late.

    That's the moment between the wait and the time-limit check.
    """

    def __init__(self, let_step_finish: threading.Event) -> None:
        self._let_step_finish = let_step_finish
        self._readings = 0

    def now(self) -> float:
        self._readings += 1
        if self._readings == 1:
            return 0.0  # the deadline is computed from this
        self._let_step_finish.set()
        time.sleep(0.05)  # the step finishes now
        return 100.0  # well past the deadline

    def sleep_until(self, deadline: float) -> None:
        raise NotImplementedError


def test_a_step_that_finishes_just_after_a_wait_slice_still_counts_as_in_time() -> None:
    let_step_finish = threading.Event()
    results: list[str] = []

    def finishes_when_let() -> None:
        let_step_finish.wait(timeout=10.0)
        results.append("done")

    run_with_time_limit(
        "A step", finishes_when_let, 1.0, "", FinishesBetweenWaitAndCheck(let_step_finish)
    )

    assert results == ["done"]
