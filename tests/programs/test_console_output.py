"""Console output on a background thread (ADR-0035) and its exit (ADR-0075, ADR-0078).

A console that stops reading is faked by one whose writes wait until it's
released, or, for a program's exit, by a pipe nobody reads. Every wait has a
time limit, so a broken test fails instead of hanging.
"""

import io
import logging
import os
import subprocess
import sys
import threading
import time
import weakref
from pathlib import Path

from crazyflie_behavior.programs.console_output import EXIT_TIME_LIMIT, UnlockedConsoleHandler
from crazyflie_behavior.programs.start_up import logging_for_run

GIVE_UP_AFTER = 10.0
"""Seconds a test waits for something that should be quick, before failing."""

PROGRAM_LOGGER = "crazyflie_behavior.test_program"

PROGRAM_THAT_FILLS_STANDARD_ERROR = f"""
import logging
import sys
from pathlib import Path

from crazyflie_behavior.programs.start_up import logging_for_run

with logging_for_run("exit_test", Path(sys.argv[1])):
    for number in range(3000):
        logging.getLogger("{PROGRAM_LOGGER}").info("log message %d %s", number, "x" * 100)
"""
"""A program whose 3000 info messages of about 150 characters fill any pipe buffer."""


class ConsoleThatStopsReading(io.StringIO):
    """A console whose writes and flushes wait until `release()`, like a paused pipe."""

    def __init__(self) -> None:
        super().__init__()
        self._released = threading.Event()
        self.write_started = threading.Event()

    def release(self) -> None:
        self._released.set()

    def write(self, text: str) -> int:
        self.write_started.set()
        self._released.wait(GIVE_UP_AFTER)
        return super().write(text)

    def flush(self) -> None:
        self._released.wait(GIVE_UP_AFTER)


def the_log_file_text(log_directory: Path) -> str:
    log_files = list(log_directory.glob("*.log"))
    assert len(log_files) == 1
    return log_files[0].read_text(encoding="utf-8")


def test_a_log_call_returns_while_the_console_stops_reading(tmp_path: Path) -> None:
    console = ConsoleThatStopsReading()

    def log_messages() -> None:
        for number in range(50):
            logging.getLogger(PROGRAM_LOGGER).info("log message %d", number)

    try:
        with logging_for_run("test", tmp_path, console):
            logger_thread = threading.Thread(target=log_messages)
            logger_thread.start()
            logger_thread.join(GIVE_UP_AFTER / 2)
            assert not logger_thread.is_alive()
            console.release()
    finally:
        console.release()


def test_the_log_file_gets_info_and_debug_messages_while_the_console_stops_reading(tmp_path: Path) -> None:
    console = ConsoleThatStopsReading()
    try:
        with logging_for_run("test", tmp_path, console):
            logging.getLogger(PROGRAM_LOGGER).info("an event")
            logging.getLogger(PROGRAM_LOGGER).debug("a detail")
            assert console.write_started.wait(GIVE_UP_AFTER)

            log_text = the_log_file_text(tmp_path)
            assert "an event" in log_text
            assert "a detail" in log_text
            console.release()
    finally:
        console.release()


def test_the_console_gets_every_log_message_in_order_once_it_reads_again(tmp_path: Path) -> None:
    console = ConsoleThatStopsReading()
    try:
        with logging_for_run("test", tmp_path, console):
            for number in range(5):
                logging.getLogger(PROGRAM_LOGGER).info("log message %d", number)
            assert console.write_started.wait(GIVE_UP_AFTER)
            console.release()
    finally:
        console.release()

    console_lines = console.getvalue().splitlines()
    assert console_lines[0].startswith("INFO crazyflie_behavior.programs.start_up: Logging to ")
    assert console_lines[1:] == [f"INFO {PROGRAM_LOGGER}: log message {number}" for number in range(5)]


def test_exit_gives_up_on_a_console_that_stopped_reading_and_warns_in_the_log_file(tmp_path: Path) -> None:
    console = ConsoleThatStopsReading()
    try:
        with logging_for_run("test", tmp_path, console):
            # "Logging to" is the first log message: its write is the one stuck.
            assert console.write_started.wait(GIVE_UP_AFTER)
            logging.getLogger(PROGRAM_LOGGER).info("an event")
            logging.getLogger(PROGRAM_LOGGER).info("another event")
            for _ in range(5):
                logging.getLogger(PROGRAM_LOGGER).debug("a detail")
            exit_start = time.monotonic()
        exit_duration = time.monotonic() - exit_start
    finally:
        console.release()

    # The 0.05 s margin: a timed wait or the clock may come up a little short on Windows (not checked).
    assert EXIT_TIME_LIMIT - 0.05 <= exit_duration < EXIT_TIME_LIMIT + 1.0
    # Three log messages unshown: the stuck one and the two events. Debug messages never entered the queue.
    assert (
        f"The console hadn't caught up after {EXIT_TIME_LIMIT:g} s; 3 log messages weren't shown there,"
        " but the log file has them."
    ) in the_log_file_text(tmp_path)


def test_logging_shutdown_does_not_wait_on_a_stuck_console_write() -> None:
    console = ConsoleThatStopsReading()
    handler = UnlockedConsoleHandler(console)
    record = logging.LogRecord(PROGRAM_LOGGER, logging.INFO, __file__, 0, "an event", None, None)
    try:
        writer_thread = threading.Thread(target=handler.handle, args=(record,), daemon=True)
        writer_thread.start()
        assert console.write_started.wait(GIVE_UP_AFTER)

        # What Python runs at exit, for this handler only.
        cleanup_thread = threading.Thread(target=logging.shutdown, args=([weakref.ref(handler)],), daemon=True)
        cleanup_thread.start()
        cleanup_thread.join(GIVE_UP_AFTER / 2)
        assert not cleanup_thread.is_alive()
    finally:
        console.release()


def test_a_program_ends_with_exit_code_0_while_nobody_reads_its_standard_error(tmp_path: Path) -> None:
    # Unbuffered, as PyCharm's run configurations set it: with a buffered standard error,
    # Python's own flush at exit can still wait on the stuck write (ADR-0078).
    environment = {**os.environ, "PYTHONUNBUFFERED": "1"}
    program = subprocess.Popen(
        [sys.executable, "-c", PROGRAM_THAT_FILLS_STANDARD_ERROR, str(tmp_path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        env=environment,
    )
    try:
        exit_code = program.wait(timeout=EXIT_TIME_LIMIT + GIVE_UP_AFTER)
    finally:
        if program.poll() is None:
            program.kill()
        program.communicate(timeout=GIVE_UP_AFTER)  # reads the pipe, so the program can end

    assert exit_code == 0
    # The warning shows the console was given up on, not that the pipe kept up.
    assert f"The console hadn't caught up after {EXIT_TIME_LIMIT:g} s;" in the_log_file_text(tmp_path)
