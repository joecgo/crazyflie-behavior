"""Running a blocking step with a time limit, so Ctrl+C still gets through (ADR-0029).

cflib's connect waits with no time limit, and on Windows Python 3.12 can't
interrupt such a wait. So each step runs on a helper thread, and the calling
thread waits for it in short slices: between slices, Python handles Ctrl+C and
the time limit is checked.
"""

import logging
import threading
from collections.abc import Callable

from crazyflie_behavior.timing.clock import Clock

logger = logging.getLogger(__name__)

WAIT_SLICE = 0.1
"""Seconds per wait, so Ctrl+C gets through within this long, even on Windows."""


class _HelperStep:
    """One step on a helper thread.

    A step stuck inside a library can't be stopped, only abandoned.
    """

    def __init__(self, name: str, action: Callable[[], object]) -> None:
        self.name = name
        self.finished = threading.Event()
        self._action = action
        self._lock = threading.Lock()
        self._error: BaseException | None = None
        self._is_abandoned = False
        # A daemon thread doesn't keep the program alive if the step never returns.
        self._thread = threading.Thread(target=self._run, name=f"connect: {name}", daemon=True)

    def start(self) -> None:
        self._thread.start()

    def abandon(self) -> None:
        """Stop waiting for the step. An error it raised, or raises later, is logged (ADR-0020)."""
        with self._lock:
            self._is_abandoned = True
            error = self._error
        if error is not None:
            _log_abandoned_error(self.name, error)

    def raise_error(self) -> None:
        """Raise the step's own error, if it had one, on the waiting thread."""
        if self._error is not None:
            raise self._error

    def _run(self) -> None:
        try:
            self._action()
        except BaseException as error:  # noqa: BLE001  # raised on the waiting thread, or logged
            with self._lock:
                self._error = error
                is_abandoned = self._is_abandoned
            if is_abandoned:
                _log_abandoned_error(self.name, error)
        finally:
            self.finished.set()


def _log_abandoned_error(name: str, error: BaseException) -> None:
    logger.warning("%s ended with an error after its time limit", name, exc_info=error)


def run_with_time_limit(
    name: str,
    action: Callable[[], object],
    time_limit: float,
    hint: str,
    clock: Clock,
    on_abandon: Callable[[], object] | None = None,
) -> None:
    """Run `action` on a helper thread and wait for it, at most `time_limit` seconds.

    Past the limit, raises TimeoutError naming the step and the `hint` (what
    to check). The action's own error rises here, as if it had run on this
    thread. On a timeout or Ctrl+C, `on_abandon` runs before the error rises,
    for example to stop a connection still under way. Ctrl+C is noticed within
    one wait slice; `on_abandon` may take longer.
    """
    step = _HelperStep(name, action)
    deadline = clock.now() + time_limit
    try:
        # Started inside the try: a Ctrl+C can arrive the moment the step starts.
        step.start()
        while not step.finished.wait(WAIT_SLICE):
            # A step that finished just after the wait gave up still counts as in time.
            if clock.now() >= deadline and not step.finished.is_set():
                raise TimeoutError(f"{name} took longer than {time_limit:g} s. {hint}")
    except BaseException:
        step.abandon()
        if on_abandon is not None:
            try:
                on_abandon()
            except Exception:
                # Keep the time limit's or Ctrl+C's error: it names the step and the fix.
                logger.warning("Cleaning up after %s failed", name, exc_info=True)
        raise
    step.raise_error()
