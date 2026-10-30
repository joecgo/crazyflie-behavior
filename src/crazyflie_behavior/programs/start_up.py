"""Start-up code every program shares (ADR-0026, ADR-0028).

Logging to the console and a log file, QuickEdit off in an old Windows console
window, and running the tick loop between connecting and disconnecting the
drone, with Ctrl+C as a stop request.
"""

import ctypes
import logging
import signal
import sys
import threading
from collections.abc import Callable, Generator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from types import FrameType, TracebackType
from typing import Any, Self, TextIO

from crazyflie_behavior.drone.interface import DroneInterface
from crazyflie_behavior.loop.tick_loop import HangWatchdog, TickLoop, TickStep
from crazyflie_behavior.timing.clock import Clock

logger = logging.getLogger(__name__)

LOG_DIRECTORY = Path("logs")
"""Where each run's log file goes, relative to the working directory (git-ignored)."""

_PROJECT_LOGGER = "crazyflie_behavior"
"""The parent of every logger in this project, including the programs' own."""

_CONSOLE_FORMAT = "%(levelname)s %(name)s: %(message)s"
_FILE_FORMAT = "%(asctime)s %(levelname)s [%(threadName)s] %(name)s: %(message)s"

# Windows console input mode flags (wincon.h).
_ENABLE_QUICK_EDIT_MODE = 0x0040
_ENABLE_EXTENDED_FLAGS = 0x0080
_STANDARD_INPUT_HANDLE = 0xFFFFFFF6  # STD_INPUT_HANDLE, (DWORD)-10

# What signal.signal accepts and returns (typeshed spells it the same way).
_SignalHandler = Callable[[int, FrameType | None], Any] | int | signal.Handlers | None


@contextmanager
def logging_for_run(program_name: str, log_directory: Path = LOG_DIRECTORY) -> Generator[TextIO]:
    """Log to the console (info and above) and to a new log file (everything of ours).

    Libraries such as cflib log at info and above only: cflib logs every radio
    packet at debug level. Python warnings and errors in other threads are
    logged too. Yields the open log file, for the hang watchdog. On exit, the
    handlers, levels and thread hook are put back and warning capture is off.
    """
    log_directory.mkdir(parents=True, exist_ok=True)
    log_path = log_directory / f"{datetime.now():%Y-%m-%d_%H-%M-%S}_{program_name}.log"
    log_file = log_path.open("a", encoding="utf-8")
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(_CONSOLE_FORMAT))
    file_handler = logging.StreamHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(_FILE_FORMAT))

    root_logger = logging.getLogger()
    project_logger = logging.getLogger(_PROJECT_LOGGER)
    previous_root_level = root_logger.level
    previous_project_level = project_logger.level
    previous_thread_hook = threading.excepthook
    try:
        root_logger.setLevel(logging.INFO)
        project_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
        logging.captureWarnings(True)
        threading.excepthook = _log_thread_error
        logger.info("Logging to %s", log_path)
        yield log_file
    finally:
        threading.excepthook = previous_thread_hook
        logging.captureWarnings(False)
        root_logger.removeHandler(console_handler)
        root_logger.removeHandler(file_handler)
        log_file.close()
        project_logger.setLevel(previous_project_level)
        root_logger.setLevel(previous_root_level)


def _log_thread_error(arguments: threading.ExceptHookArgs) -> None:
    """Log an error that ended another thread, instead of only printing it (ADR-0020)."""
    if issubclass(arguments.exc_type, SystemExit):
        return  # Python's default ignores these too
    thread_name = arguments.thread.name if arguments.thread is not None else "unknown"
    if arguments.exc_value is None:
        logger.critical("Error in thread %s: %s", thread_name, arguments.exc_type.__name__)
        return
    logger.critical(
        "Error in thread %s",
        thread_name,
        exc_info=(arguments.exc_type, arguments.exc_value, arguments.exc_traceback),
    )


def mode_without_quick_edit(console_mode: int) -> int:
    """A console input mode with QuickEdit off. Windows only applies it with extended flags set."""
    return (console_mode & ~_ENABLE_QUICK_EDIT_MODE) | _ENABLE_EXTENDED_FLAGS


def restored_mode(original_mode: int) -> int:
    """The original console input mode, with extended flags so Windows applies its QuickEdit bit."""
    return original_mode | _ENABLE_EXTENDED_FLAGS


@contextmanager
def quick_edit_off() -> Generator[None]:
    """Turn QuickEdit off while the program runs in an old Windows console window (ADR-0028).

    There, selecting text pauses the program the next time it writes to the
    console, which would stall a tick. Does nothing anywhere else: PyCharm's
    Run window, or another operating system.
    """
    if sys.platform != "win32":
        yield
        return
    from ctypes import wintypes  # Windows only

    # A private copy of kernel32 with declared types: a handle is pointer-sized
    # on 64-bit Windows, and ctypes would otherwise cut it to 32 bits.
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.GetStdHandle.argtypes = [wintypes.DWORD]
    kernel32.GetStdHandle.restype = wintypes.HANDLE
    kernel32.GetConsoleMode.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel32.GetConsoleMode.restype = wintypes.BOOL
    kernel32.SetConsoleMode.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel32.SetConsoleMode.restype = wintypes.BOOL

    handle = kernel32.GetStdHandle(_STANDARD_INPUT_HANDLE)
    original_mode = wintypes.DWORD()
    if not kernel32.GetConsoleMode(handle, ctypes.byref(original_mode)):
        yield  # not a console window
        return
    kernel32.SetConsoleMode(handle, mode_without_quick_edit(original_mode.value))
    logger.debug("QuickEdit is off in this console window until the program exits")
    try:
        yield
    finally:
        kernel32.SetConsoleMode(handle, restored_mode(original_mode.value))


class _CtrlCHandler:
    """Ctrl+C during one run: an error while connecting, then a stop request (ADR-0026).

    While connecting, nothing is flying, so the first press raises
    KeyboardInterrupt, as Python does by default, and the program stops. (The
    Crazyflie adapter waits in short slices while connecting, so this works on
    Windows too: ADR-0029.) Once connected, the first press makes a stop
    request instead.
    Every later press is ignored, so it can't cut the landing, or the cleanup
    after a failed connect, short. The handler never logs: a log write that a
    signal interrupts can fail with a "reentrant call" error. Python runs
    signal handlers on the main thread, so this must be used there.
    """

    def __init__(self, tick_loop: TickLoop) -> None:
        self._tick_loop = tick_loop
        self._makes_stop_requests = False
        self._has_interrupted = False
        self._has_made_stop_request = False
        self._ignored_press_count = 0
        self._previous_handler: _SignalHandler = None

    def __enter__(self) -> Self:
        self._previous_handler = signal.signal(signal.SIGINT, self._on_ctrl_c)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        # None means the old handler wasn't set from Python; the default stands in.
        previous_handler = self._previous_handler
        signal.signal(
            signal.SIGINT, previous_handler if previous_handler is not None else signal.SIG_DFL
        )
        if self._has_made_stop_request:
            logger.info("Ctrl+C made the stop request")
        if self._ignored_press_count > 0:
            logger.warning(
                "Ctrl+C pressed again while stopping (ignored presses: %d), "
                "so stopping wasn't cut short",
                self._ignored_press_count,
            )

    def make_stop_requests(self) -> None:
        """From now on, Ctrl+C makes a stop request instead of raising KeyboardInterrupt."""
        self._makes_stop_requests = True

    def _on_ctrl_c(self, _signal_number: int, _frame: FrameType | None) -> None:
        if self._has_interrupted or self._has_made_stop_request:
            self._ignored_press_count += 1
        elif self._makes_stop_requests:
            self._has_made_stop_request = True
            self._tick_loop.request_stop()
        else:
            self._has_interrupted = True
            raise KeyboardInterrupt


def run_tick_loop(
    drone: DroneInterface, tick_step: TickStep, clock: Clock, log_file: TextIO
) -> None:
    """Connect, run the tick loop until it's done or stopped, then disconnect (ADR-0026).

    Disconnecting always happens, also after an error or a failed connect (it
    does nothing if nothing is connected), and it lands a flying drone. Once
    connected, Ctrl+C is a stop request, so it can't cut the landing short.
    While connecting, nothing is flying, so Ctrl+C stops the program (ADR-0028,
    ADR-0029).

    This uses `try`/`finally` rather than `with drone:` so that the Ctrl+C
    handler is in place before connecting and stays until after the landing.
    """
    tick_loop = TickLoop(clock, tick_step, HangWatchdog(log_file))
    with _CtrlCHandler(tick_loop) as ctrl_c:
        try:
            drone.connect()
            ctrl_c.make_stop_requests()
            tick_loop.run()
        finally:
            drone.disconnect()
