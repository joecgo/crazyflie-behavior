"""Running a blocking step with a time limit, so the interrupt signal still gets through (ADR-0029).

cflib's connect waits with no time limit, and on Windows Python 3.12 can't
interrupt such a wait. So each step runs on a helper thread, and the calling
thread waits for it in short slices: between slices, Python handles the
interrupt signal and the time limit is checked.
"""

import logging
import threading
from collections.abc import Callable

from crazyflie_behavior.timing.clock import Clock

logger = logging.getLogger(__name__)

WAIT_SLICE = 0.1
"""Seconds per wait, so the interrupt signal gets through within this long, even on Windows."""


class _HelperStep:
    """One step on a helper thread.

    Python can't end a thread from outside: a thread ends only when its own code
    returns or raises. A step stuck in a wait inside cflib never does, so it can't be
    stopped, only abandoned: no longer waited for.
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
    logger.warning("%s ended with an error after it was abandoned", name, exc_info=error)


def run_with_time_limit(
    name: str,
    action: Callable[[], object],
    time_limit: float,
    *,
    what_to_check: str,
    clock: Clock,
    on_abandon: Callable[[], object] | None = None,
) -> None:
    """Run `action` on a helper thread and wait for it, at most `time_limit` seconds.

    Past the limit, raises TimeoutError naming the step and `what_to_check`.
    The action's own error rises here, as if it had run on this thread. On a
    timeout or KeyboardInterrupt (the interrupt signal), `on_abandon` runs
    before the error rises, for example to stop a connection still under way.
    The interrupt signal is noticed within one wait slice; `on_abandon` may
    take longer. An interrupt signal that CPython hid in a threading lock
    error still rises as KeyboardInterrupt (ADR-0094).
    """
    step = _HelperStep(name, action)
    deadline = clock.now() + time_limit
    hidden_interrupt: KeyboardInterrupt | None = None
    try:
        # Started inside the try: the interrupt signal can arrive the moment the step starts.
        step.start()
        while not step.finished.wait(WAIT_SLICE):
            # A step that finished just after the wait gave up still counts as in time.
            if clock.now() >= deadline and not step.finished.is_set():
                raise TimeoutError(f"{name} took longer than {time_limit:g} s. {what_to_check}")
    except BaseException as error:
        hidden_interrupt = _interrupt_hidden_in(error)
        step.abandon()
        if on_abandon is not None:
            try:
                on_abandon()
            except Exception:
                # Keep the timeout (it names the step and what to check) or KeyboardInterrupt, not this error.
                logger.warning("Cleaning up after %s failed", name, exc_info=True)
        if hidden_interrupt is None:
            raise
        # Logged after the cleanup, so a second interrupt signal here can't skip it.
        logger.debug("%s: the interrupt signal came as a threading lock error", name, exc_info=error)
    if hidden_interrupt is not None:
        # Raised outside the except: inside it, the threading lock error would become its context, and the
        # interrupt signal would read as one that came while an error was being handled (ADR-0094).
        raise hidden_interrupt
    step.raise_error()


def _interrupt_hidden_in(error: BaseException) -> KeyboardInterrupt | None:
    """The KeyboardInterrupt that `error` carries as its context when `error` is the threading lock error CPython
    raises for an interrupt signal that lands while a lock is released (ADR-0094); otherwise None."""
    exception_being_handled = error.__context__
    if isinstance(error, RuntimeError) and isinstance(exception_being_handled, KeyboardInterrupt):
        return exception_being_handled
    return None
