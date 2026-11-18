"""Console output on a background thread (ADR-0035, ADR-0075).

A console that stops reading must never block the thread that logs: log
messages go into a queue, and the console's thread writes them. The log file
is not here; it stays on the thread that logs.
"""

import logging
import queue
from collections.abc import Generator
from contextlib import contextmanager
from logging.handlers import QueueHandler, QueueListener
from typing import TextIO, override

logger = logging.getLogger(__name__)

EXIT_TIME_LIMIT = 2.0
"""How long the console's thread gets at exit to write the log messages still queued (ADR-0075)."""

_CONSOLE_FORMAT = "%(levelname)s %(name)s: %(message)s"


class UnlockedConsoleHandler(logging.StreamHandler[TextIO]):
    """Writes to the console with no lock, so `logging.shutdown` at exit doesn't wait on this handler (ADR-0075).

    Safe only while one thread writes through it: the console's thread.
    """

    flushOnClose = False  # noqa: N815  # Python's name; its exit cleanup would flush a stuck console

    @override
    def createLock(self) -> None:
        self.lock = None


class _ConsoleListener(QueueListener):
    """A `QueueListener` with `stop_within`, a stop that waits at most a time limit (ADR-0075)."""

    def stop_within(self, time_limit: float) -> bool:
        """Ask the console's thread to finish, and wait at most `time_limit` seconds.

        True if it finished or never started.
        """
        self.enqueue_sentinel()
        thread = self._thread
        if thread is None:
            return True  # never started
        thread.join(time_limit)
        return not thread.is_alive()


@contextmanager
def console_output(console: TextIO) -> Generator[None]:
    """While active, log messages at info and above go to `console` from the console's thread.

    Its exit warning needs another handler on the root logger, such as the log file's.
    """
    console_queue: queue.SimpleQueue[logging.LogRecord] = queue.SimpleQueue()
    queued_console = QueueHandler(console_queue)
    # On the queue's handler, not the console's, so debug messages never enter the queue.
    queued_console.setLevel(logging.INFO)
    console_handler = UnlockedConsoleHandler(console)
    console_handler.setFormatter(logging.Formatter(_CONSOLE_FORMAT))
    listener = _ConsoleListener(console_queue, console_handler)
    root_logger = logging.getLogger()
    try:
        listener.start()
        root_logger.addHandler(queued_console)
        yield
    finally:
        # Removed before the stop, so no new log message is queued. One that another thread is
        # logging at this moment can still be queued after the stop; it's never shown (ADR-0078).
        root_logger.removeHandler(queued_console)
        if not listener.stop_within(EXIT_TIME_LIMIT):
            # `qsize` counts the unwritten log messages plus `stop_within`'s end marker, which
            # stands in for the message stuck in its write: together, the number not shown.
            logger.warning(
                "The console hadn't caught up after %g s; %d log messages weren't shown there,"
                " but the log file has them.",
                EXIT_TIME_LIMIT,
                console_queue.qsize(),
            )
