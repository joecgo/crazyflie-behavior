"""The programs' shared start-up code (ADR-0026, ADR-0028): logging, QuickEdit and the interrupt signal.

The interrupt signal tests send it with `signal.raise_signal`, which runs the
handler on the main thread just as Ctrl+C in the console would.
"""

import ctypes
import logging
import re
import signal
import sys
import threading
import warnings
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import TextIO

import pytest

from crazyflie_behavior.drone.crazyflie.adapter import CrazyflieAdapter
from crazyflie_behavior.drone.crazyflie.bad_flow_zone import DEFAULT_INITIAL_CLIMB_SPEED
from crazyflie_behavior.drone.mock_adapter import MockAdapter
from crazyflie_behavior.loop.tick_loop import TickStep
from crazyflie_behavior.programs import start_up as start_up_module
from crazyflie_behavior.programs.start_up import (
    logging_for_run,
    make_drone,
    mode_without_quick_edit,
    quick_edit_off,
    restored_mode,
    run_program,
    run_tick_loop,
    take_off_log_description,
)
from crazyflie_behavior.timing.clock import SimClock

START_UP_LOGGER = "crazyflie_behavior.programs.start_up"
GIVE_UP_AFTER_TICKS = 100
"""Fakes that would otherwise tick forever report done after this many ticks, so
a broken stop path fails its test instead of hanging it."""


def run_without_keyboard_interrupt(drone: MockAdapter, tick_step: TickStep, clock: SimClock, log_file: TextIO) -> None:
    """Run the tick loop; a KeyboardInterrupt fails the test instead of stopping pytest."""
    try:
        run_tick_loop(drone, tick_step, clock, log_file)
    except KeyboardInterrupt:
        pytest.fail("The interrupt signal raised KeyboardInterrupt instead of making a stop request")


def the_log_file_text(log_directory: Path) -> str:
    log_files = list(log_directory.glob("*.log"))
    assert len(log_files) == 1
    return log_files[0].read_text(encoding="utf-8")


class InterruptSignalOnMessage(logging.Handler):
    """Sends the interrupt signal while a log message containing `text` is written."""

    def __init__(self, text: str) -> None:
        super().__init__()
        self._text = text

    def emit(self, record: logging.LogRecord) -> None:
        if self._text in record.getMessage():
            signal.raise_signal(signal.SIGINT)


@contextmanager
def interrupt_signal_when_logged(text: str) -> Generator[None]:
    """While active, the start-up code's log message containing `text` brings the interrupt signal."""
    handler = InterruptSignalOnMessage(text)
    start_up_logger = logging.getLogger(START_UP_LOGGER)
    start_up_logger.addHandler(handler)
    try:
        yield
    finally:
        start_up_logger.removeHandler(handler)


# --- Logging (ADR-0028) ---------------------------------------------------------


def test_the_log_file_gets_everything(tmp_path: Path) -> None:
    with logging_for_run("test", tmp_path):
        logging.getLogger("crazyflie_behavior.test_program").debug("a detail")
        logging.getLogger("crazyflie_behavior.test_program").info("an event")

    log_text = the_log_file_text(tmp_path)
    assert "a detail" in log_text
    assert "an event" in log_text


def test_the_console_shows_info_and_above(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    with logging_for_run("test", tmp_path):
        logging.getLogger("crazyflie_behavior.test_program").debug("a detail")
        logging.getLogger("crazyflie_behavior.test_program").info("an event")

    console = capsys.readouterr().err
    assert "an event" in console
    assert "a detail" not in console


def test_libraries_debug_lines_stay_out_of_the_log(tmp_path: Path) -> None:
    with logging_for_run("test", tmp_path):
        logging.getLogger("cflib.crazyflie").debug("every radio packet")
        logging.getLogger("cflib.crazyflie").warning("a link warning")

    log_text = the_log_file_text(tmp_path)
    assert "every radio packet" not in log_text
    assert "a link warning" in log_text


def test_the_log_file_is_named_after_the_start_time_and_the_program(tmp_path: Path) -> None:
    with logging_for_run("bench", tmp_path):
        pass

    names = [path.name for path in tmp_path.glob("*.log")]
    assert len(names) == 1
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}_bench\.log", names[0])


def test_python_warnings_go_to_the_log(tmp_path: Path) -> None:
    with logging_for_run("test", tmp_path), warnings.catch_warnings():
        warnings.simplefilter("always")
        warnings.warn("careful with that", UserWarning, stacklevel=1)

    assert "careful with that" in the_log_file_text(tmp_path)


def test_errors_in_other_threads_go_to_the_log(tmp_path: Path) -> None:
    def fail() -> None:
        raise RuntimeError("the helper thread broke")

    with logging_for_run("test", tmp_path):
        thread = threading.Thread(target=fail, name="helper")
        thread.start()
        thread.join()

    log_text = the_log_file_text(tmp_path)
    assert "Error in thread helper" in log_text
    assert "the helper thread broke" in log_text


def test_logging_for_run_puts_everything_back_afterwards(tmp_path: Path) -> None:
    root_logger = logging.getLogger()
    project_logger = logging.getLogger("crazyflie_behavior")
    handlers_before = list(root_logger.handlers)
    level_before = root_logger.level
    project_level_before = project_logger.level
    thread_hook_before = threading.excepthook
    show_warning_before = warnings.showwarning

    with logging_for_run("test", tmp_path) as log_file:
        pass

    assert root_logger.handlers == handlers_before
    assert root_logger.level == level_before
    assert project_logger.level == project_level_before
    assert threading.excepthook is thread_hook_before
    assert warnings.showwarning is show_warning_before
    assert log_file.closed


# --- QuickEdit (ADR-0028) -------------------------------------------------------

QUICK_EDIT = 0x0040
EXTENDED_FLAGS = 0x0080


def test_turning_quick_edit_off_keeps_every_other_console_setting() -> None:
    other_settings = 0x0007  # processed input, line input, echo
    console_mode = other_settings | QUICK_EDIT  # no extended flags yet

    new_mode = mode_without_quick_edit(console_mode)

    # Windows applies the change only with extended flags set.
    assert new_mode == other_settings | EXTENDED_FLAGS


def test_restoring_the_console_mode_brings_quick_edit_back() -> None:
    original_mode = 0x0007 | QUICK_EDIT  # no extended flags

    # Without extended flags, Windows would ignore the QuickEdit bit.
    assert restored_mode(original_mode) == original_mode | EXTENDED_FLAGS


def test_quick_edit_off_is_safe_anywhere() -> None:
    # Under pytest, standard input is usually not a console window: nothing to change.
    with quick_edit_off():
        pass


def a_console_window(monkeypatch: pytest.MonkeyPatch, set_console_mode_results: list[bool]) -> None:
    """Stand in a fake kernel32: a console window whose mode changes succeed or fail in turn."""
    results = iter(set_console_mode_results)

    def get_std_handle(_which: int) -> int:
        return 1

    def get_console_mode(_handle: int, _mode: object) -> bool:
        return True

    def set_console_mode(_handle: int, _mode: int) -> bool:
        return next(results)

    def load_library(*_arguments: object, **_keywords: object) -> SimpleNamespace:
        return SimpleNamespace(
            GetStdHandle=get_std_handle, GetConsoleMode=get_console_mode, SetConsoleMode=set_console_mode
        )

    monkeypatch.setattr(ctypes, "WinDLL", load_library)


@pytest.mark.skipif(sys.platform != "win32", reason="the console mode exists only on Windows")
def test_quick_edit_that_cant_be_turned_off_is_a_warning(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG, logger=START_UP_LOGGER)
    a_console_window(monkeypatch, set_console_mode_results=[False])

    with quick_edit_off():
        pass

    assert [record.levelno for record in caplog.records] == [logging.WARNING]
    assert caplog.messages[0].startswith("Couldn't turn QuickEdit off")


@pytest.mark.skipif(sys.platform != "win32", reason="the console mode exists only on Windows")
def test_quick_edit_that_cant_be_turned_back_on_is_a_warning(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG, logger=START_UP_LOGGER)
    a_console_window(monkeypatch, set_console_mode_results=[True, False])

    with quick_edit_off():
        pass

    assert caplog.messages[-1].startswith("Couldn't turn QuickEdit back on")


# --- Running the tick loop, and the interrupt signal (ADR-0026, ADR-0028) -------


@pytest.fixture
def log_file(tmp_path: Path) -> Generator[TextIO]:
    with (tmp_path / "run.log").open("w", encoding="utf-8") as file:
        yield file


class CountingTickStep(TickStep):
    """A fake tick step that runs a set number of ticks, sending the interrupt signal on some."""

    def __init__(self, tick_count: int, interrupt_signal_on_ticks: tuple[int, ...] = ()) -> None:
        self._tick_count = tick_count
        self._interrupt_signal_on_ticks = interrupt_signal_on_ticks
        self.ticks_run = 0

    def run(self, time: float, dt: float) -> bool:
        tick_number = self.ticks_run
        self.ticks_run += 1
        if tick_number in self._interrupt_signal_on_ticks:
            signal.raise_signal(signal.SIGINT)
        return self.ticks_run >= self._tick_count


class FailingTickStep(TickStep):
    def run(self, time: float, dt: float) -> bool:
        raise RuntimeError("the tick step broke")


class InterruptSignalWhileConnectingDrone(MockAdapter):
    """A mock drone that gets the interrupt signal while it connects."""

    def connect(self) -> None:
        super().connect()
        signal.raise_signal(signal.SIGINT)


class InterruptSignalTwiceWhileConnectingDrone(MockAdapter):
    """A mock drone that gets the interrupt signal while it connects, and again during the cleanup."""

    def connect(self) -> None:
        super().connect()
        signal.raise_signal(signal.SIGINT)

    def disconnect(self) -> None:
        signal.raise_signal(signal.SIGINT)
        super().disconnect()
        self.command_log.append("cleanup finished")


class InterruptSignalDuringLandingDrone(MockAdapter):
    """A mock drone that gets the interrupt signal while it lands."""

    def disconnect(self) -> None:
        signal.raise_signal(signal.SIGINT)
        super().disconnect()
        self.command_log.append("landing finished")


def test_the_drone_is_connected_for_the_ticks_and_disconnected_after(log_file: TextIO) -> None:
    clock = SimClock()
    drone = MockAdapter(clock)
    tick_step = CountingTickStep(3)

    run_tick_loop(drone, tick_step, clock, log_file)

    assert tick_step.ticks_run == 3
    assert drone.command_log == ["connect", "disconnect"]


def test_the_drone_is_disconnected_even_when_a_tick_raises(log_file: TextIO) -> None:
    clock = SimClock()
    drone = MockAdapter(clock)

    with pytest.raises(RuntimeError, match="the tick step broke"):
        run_tick_loop(drone, FailingTickStep(), clock, log_file)

    assert drone.command_log == ["connect", "disconnect"]


def test_the_interrupt_signal_once_connected_lets_the_tick_finish_and_starts_no_more(
    log_file: TextIO,
) -> None:
    clock = SimClock()
    tick_step = CountingTickStep(GIVE_UP_AFTER_TICKS, interrupt_signal_on_ticks=(1,))

    run_without_keyboard_interrupt(MockAdapter(clock), tick_step, clock, log_file)

    assert tick_step.ticks_run == 2


def test_the_interrupt_signal_during_the_landing_is_ignored_so_the_landing_finishes(
    log_file: TextIO, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO, logger=START_UP_LOGGER)
    clock = SimClock()
    drone = InterruptSignalDuringLandingDrone(clock)
    tick_step = CountingTickStep(GIVE_UP_AFTER_TICKS, interrupt_signal_on_ticks=(0,))

    run_without_keyboard_interrupt(drone, tick_step, clock, log_file)

    assert drone.command_log[-1] == "landing finished"
    assert "The interrupt signal made the stop request" in caplog.messages
    assert any("ignored (times: 1)" in message for message in caplog.messages)


def test_the_interrupt_signal_while_the_end_of_a_run_is_logged_is_ignored(
    log_file: TextIO, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO, logger=START_UP_LOGGER)
    clock = SimClock()
    tick_step = CountingTickStep(GIVE_UP_AFTER_TICKS, interrupt_signal_on_ticks=(0,))

    with interrupt_signal_when_logged("made the stop request"):
        run_without_keyboard_interrupt(MockAdapter(clock), tick_step, clock, log_file)

    assert any("ignored (times: 1)" in message for message in caplog.messages)


def test_the_interrupt_signal_while_connecting_stops_at_once_and_still_disconnects(log_file: TextIO) -> None:
    clock = SimClock()
    drone = InterruptSignalWhileConnectingDrone(clock)
    tick_step = CountingTickStep(GIVE_UP_AFTER_TICKS)

    # Nothing is flying yet, so the interrupt signal stops the program as Python normally does.
    with pytest.raises(KeyboardInterrupt):
        run_tick_loop(drone, tick_step, clock, log_file)

    assert tick_step.ticks_run == 0
    assert drone.command_log == ["connect", "disconnect"]


def test_a_second_interrupt_signal_while_connecting_doesnt_cut_the_cleanup_short(
    log_file: TextIO,
) -> None:
    clock = SimClock()
    drone = InterruptSignalTwiceWhileConnectingDrone(clock)

    with pytest.raises(KeyboardInterrupt):
        run_tick_loop(drone, CountingTickStep(GIVE_UP_AFTER_TICKS), clock, log_file)

    assert drone.command_log[-1] == "cleanup finished"


def test_the_previous_interrupt_signal_handler_is_back_after_a_run(log_file: TextIO) -> None:
    handler_before = signal.getsignal(signal.SIGINT)
    clock = SimClock()

    run_tick_loop(MockAdapter(clock), CountingTickStep(1), clock, log_file)

    assert signal.getsignal(signal.SIGINT) is handler_before


# --- Running a program (ADR-0028) -----------------------------------------------


def test_the_mock_adapter_is_the_default_and_the_crazyflie_needs_the_flag() -> None:
    clock = SimClock()

    assert isinstance(make_drone(use_crazyflie=False, clock=clock), MockAdapter)
    assert isinstance(make_drone(use_crazyflie=True, clock=clock), CrazyflieAdapter)


def test_make_drone_passes_the_take_over_setting_on_to_either_adapter() -> None:
    clock = SimClock()

    mock_drone = make_drone(use_crazyflie=False, clock=clock, take_over_flight=True)
    mock_drone.connect()
    mock_status = mock_drone.take_snapshot(0.0).drone_status
    crazyflie = make_drone(use_crazyflie=True, clock=clock, take_over_flight=True)

    assert mock_status is not None
    assert mock_status.value.is_flying
    assert isinstance(crazyflie, CrazyflieAdapter)
    assert crazyflie._take_over_flight  # pyright: ignore[reportPrivateUsage]


def run_test_program(tick_step: TickStep) -> int:
    clock = SimClock()
    return run_program("test", "Test program, the mock adapter", MockAdapter(clock), tick_step, clock)


def test_a_program_that_runs_until_done_ends_with_exit_code_0(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)

    assert run_test_program(CountingTickStep(3)) == 0
    log_text = the_log_file_text(tmp_path / "logs")
    assert "Test program, the mock adapter" in log_text
    assert "Tick loop summary: ticks: 3" in log_text


def test_the_interrupt_signal_while_connecting_ends_a_program_with_exit_code_130(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    def interrupted(*_arguments: object) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(start_up_module, "run_tick_loop", interrupted)

    assert run_test_program(CountingTickStep(1)) == 130
    assert "stopped before the tick loop started" in the_log_file_text(tmp_path / "logs")


def test_the_interrupt_signal_while_a_program_logs_its_description_ends_it_with_exit_code_130(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    with interrupt_signal_when_logged("Test program, the mock adapter"):
        try:
            exit_code = run_test_program(CountingTickStep(1))
        except KeyboardInterrupt:
            pytest.fail("The interrupt signal escaped the program as KeyboardInterrupt")

    assert exit_code == 130


def test_an_error_cut_short_by_the_interrupt_signal_still_goes_to_the_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    def interrupted_while_failing(*_arguments: object) -> None:
        try:
            raise RuntimeError("Flow deck not detected")
        except RuntimeError as error:
            raise KeyboardInterrupt from error

    monkeypatch.setattr(start_up_module, "run_tick_loop", interrupted_while_failing)

    assert run_test_program(CountingTickStep(1)) == 130
    assert "Flow deck not detected" in the_log_file_text(tmp_path / "logs")


def test_an_error_ends_a_program_with_exit_code_1_and_goes_to_the_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    assert run_test_program(FailingTickStep()) == 1
    log_text = the_log_file_text(tmp_path / "logs")
    assert "The test program stopped with an error" in log_text
    assert "the tick step broke" in log_text


def test_make_drone_passes_the_take_off_log_on_to_the_crazyflie_adapter() -> None:
    clock = SimClock()

    mock_drone = make_drone(use_crazyflie=False, clock=clock, take_off_log=True)
    crazyflie = make_drone(use_crazyflie=True, clock=clock, take_off_log=True)
    default = make_drone(use_crazyflie=True, clock=clock)

    assert isinstance(mock_drone, MockAdapter)  # it has no take-off block
    assert isinstance(crazyflie, CrazyflieAdapter)
    assert crazyflie._take_off_log  # pyright: ignore[reportPrivateUsage]
    assert isinstance(default, CrazyflieAdapter)
    assert not default._take_off_log  # pyright: ignore[reportPrivateUsage]


def test_the_description_says_when_the_take_off_block_runs_and_when_the_adapter_has_none() -> None:
    assert take_off_log_description(use_crazyflie=True) == ", with the take-off block"
    assert take_off_log_description(use_crazyflie=False) == ", with the take-off block (the mock adapter has none)"


def test_make_drone_without_a_climb_speed_gives_either_adapter_the_default() -> None:
    # The failsafe program sets none, so it flies the default (ADR-0070).
    clock = SimClock()

    mock_drone = make_drone(use_crazyflie=False, clock=clock)
    crazyflie = make_drone(use_crazyflie=True, clock=clock)

    assert isinstance(mock_drone, MockAdapter)
    assert mock_drone._initial_climb_speed == DEFAULT_INITIAL_CLIMB_SPEED  # pyright: ignore[reportPrivateUsage]
    assert isinstance(crazyflie, CrazyflieAdapter)
    assert crazyflie._initial_climb_speed == DEFAULT_INITIAL_CLIMB_SPEED  # pyright: ignore[reportPrivateUsage]


def test_make_drone_passes_the_initial_climb_speed_on_to_either_adapter() -> None:
    clock = SimClock()

    mock_drone = make_drone(use_crazyflie=False, clock=clock, initial_climb_speed=0.3)
    crazyflie = make_drone(use_crazyflie=True, clock=clock, initial_climb_speed=0.3)

    assert isinstance(mock_drone, MockAdapter)
    assert mock_drone._initial_climb_speed == 0.3  # pyright: ignore[reportPrivateUsage]
    assert isinstance(crazyflie, CrazyflieAdapter)
    assert crazyflie._initial_climb_speed == 0.3  # pyright: ignore[reportPrivateUsage]
