"""The hover program (ADR-0030), on the sim clock except the test that runs it as a program (ADR-0076)."""

import signal
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from crazyflie_behavior.behaviors.hover_test import TAKE_OFF_HEIGHT, note_pitch
from crazyflie_behavior.drone.interface import DroneInterface
from crazyflie_behavior.drone.mock_adapter import MockAdapter
from crazyflie_behavior.programs import hover as hover_module
from crazyflie_behavior.programs.hover import main
from crazyflie_behavior.safety.safety_layer import LOW_BATTERY_VOLTAGE
from crazyflie_behavior.snapshot import Snapshot
from crazyflie_behavior.timing.clock import Clock, SimClock


def the_log_file_text(log_directory: Path) -> str:
    log_files = list(log_directory.glob("*.log"))
    assert len(log_files) == 1
    return log_files[0].read_text(encoding="utf-8")


def test_the_hover_program_flies_the_hover_test_on_the_mock_adapter(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, sim_clock: SimClock
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["--hover-seconds", "0.1"], clock=sim_clock)

    assert exit_code == 0
    log_text = the_log_file_text(tmp_path / "logs")
    assert "Hover program, the mock adapter, hovering 0.1 s at 0.5 m" in log_text
    assert "Sending Arm()" in log_text
    assert "Sending TakeOff(height=0.5)" in log_text
    assert "Hovering for 0.1 s" in log_text
    assert "Sending Land()" in log_text
    assert "Hover test: landed. Done." in log_text
    assert "Snapshot: Snapshot(" in log_text  # every snapshot reaches the file
    assert "Tick loop summary" in log_text
    assert "Chirp()" not in log_text  # chirps are off by default


def test_with_chirp_the_buzzer_commands_reach_the_drone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, sim_clock: SimClock
) -> None:
    monkeypatch.chdir(tmp_path)
    drones: list[MockAdapter] = []

    def make_mock_adapter(use_crazyflie: bool, clock: Clock, *, take_off_log: bool) -> DroneInterface:
        drone = MockAdapter(clock)
        drones.append(drone)
        return drone

    monkeypatch.setattr(hover_module, "make_drone", make_mock_adapter)

    exit_code = main(["--hover-seconds", "0.1", "--chirp"], clock=sim_clock)

    assert exit_code == 0
    (drone,) = drones
    buzzer_commands = [command for command in drone.command_log if command in {"chirp", "play_tone", "silence"}]
    charge = [("G", 4), ("C", 5), ("E", 5), ("G", 5), ("E", 5), ("G", 5)]
    # A chirp on the floor and after landing (the hover is too short for more), then "Charge", then silence.
    assert buzzer_commands == ["chirp", "chirp", *["play_tone"] * len(charge), "silence"]
    assert drone.tone_pitches == pytest.approx([note_pitch(name, octave) for name, octave in charge])
    assert drone.playing_tone is None
    log_text = the_log_file_text(tmp_path / "logs")
    assert "Hover program, the mock adapter, hovering 0.1 s at 0.5 m, with chirps" in log_text
    assert "Hover test: done." in log_text


def capture_the_mock_adapter[T: MockAdapter](
    monkeypatch: pytest.MonkeyPatch, adapter_class: Callable[[Clock], T]
) -> list[T]:
    """Has the hover program make its drone with `adapter_class`, and returns the list it lands in."""
    drones: list[T] = []

    def make_mock_adapter(use_crazyflie: bool, clock: Clock, *, take_off_log: bool) -> DroneInterface:
        drones.append(adapter_class(clock))
        return drones[-1]

    monkeypatch.setattr(hover_module, "make_drone", make_mock_adapter)
    return drones


def test_the_hover_program_lands_before_disconnecting(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, sim_clock: SimClock
) -> None:
    monkeypatch.chdir(tmp_path)
    drones = capture_the_mock_adapter(monkeypatch, MockAdapter)

    assert main(["--hover-seconds", "0.1"], clock=sim_clock) == 0

    (drone,) = drones
    assert drone.command_log == ["connect", "arm", "take_off", "land", "disconnect"]  # no landing in disconnect()


class StopRequestAtTheHoverHeightMockAdapter(MockAdapter):
    """A mock drone that sends the interrupt signal once, when it's at the take-off height."""

    def __init__(self, clock: Clock) -> None:
        super().__init__(clock)
        self._has_sent_the_signal = False

    def update_take_off_and_landing(self, snapshot: Snapshot) -> None:
        super().update_take_off_and_landing(snapshot)
        position = snapshot.position_estimate
        if not self._has_sent_the_signal and position is not None and position.value.z == TAKE_OFF_HEIGHT:
            self._has_sent_the_signal = True
            signal.raise_signal(signal.SIGINT)


def test_a_stop_request_mid_hover_lands_inside_the_tick_loop_and_still_exits_with_1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, sim_clock: SimClock
) -> None:
    """ADR-0062's exit code for a hover cut short, with the landing before `disconnect()` (ADR-0083)."""
    monkeypatch.chdir(tmp_path)
    drones = capture_the_mock_adapter(monkeypatch, StopRequestAtTheHoverHeightMockAdapter)

    exit_code = main(["--hover-seconds", "5"], clock=sim_clock)

    assert exit_code == 1
    (drone,) = drones
    assert drone.command_log == ["connect", "arm", "take_off", "land", "disconnect"]
    log_text = the_log_file_text(tmp_path / "logs")
    assert "The flight is over: a stop request. Landing." in log_text
    assert "Hover test: hovered" not in log_text


class StopRequestAtTheFirstToneMockAdapter(MockAdapter):
    """A mock drone that sends the interrupt signal when its first tone arrives: "Charge" is cut short."""

    def play_tone(self, pitch: float) -> None:
        super().play_tone(pitch)
        if len(self.tone_pitches) == 1:
            signal.raise_signal(signal.SIGINT)


def test_a_stop_request_during_charge_leaves_no_tone_playing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, sim_clock: SimClock
) -> None:
    """Backlog #59's case: `disconnect()` silences the buzzer (ADR-0083)."""
    monkeypatch.chdir(tmp_path)
    drones = capture_the_mock_adapter(monkeypatch, StopRequestAtTheFirstToneMockAdapter)

    exit_code = main(["--hover-seconds", "0.1", "--chirp"], clock=sim_clock)

    assert exit_code == 0  # the hover test had landed
    (drone,) = drones
    assert drone.tone_pitches == [pytest.approx(note_pitch("G", 4))]
    assert drone.playing_tone is None


class LinkLostAtTheHoverHeightMockAdapter(MockAdapter):
    """A mock drone that loses its link once it's at the take-off height (ADR-0084)."""

    def __init__(self, clock: Clock) -> None:
        super().__init__(clock)
        self.snapshots_asked_for_after_the_loss = 0
        self._has_lost_the_link = False

    def take_snapshot(self, dt: float) -> Snapshot:
        if self._has_lost_the_link:
            self.snapshots_asked_for_after_the_loss += 1
        return super().take_snapshot(dt)

    def update_take_off_and_landing(self, snapshot: Snapshot) -> None:
        super().update_take_off_and_landing(snapshot)
        position = snapshot.position_estimate
        if not self._has_lost_the_link and position is not None and position.value.z == TAKE_OFF_HEIGHT:
            self._has_lost_the_link = True
            self.lose_link()


def test_a_link_lost_in_flight_ends_the_run_at_once_with_1_and_says_the_drone_may_still_be_flying(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, sim_clock: SimClock
) -> None:
    monkeypatch.chdir(tmp_path)
    drones = capture_the_mock_adapter(monkeypatch, LinkLostAtTheHoverHeightMockAdapter)

    exit_code = main(["--hover-seconds", "5"], clock=sim_clock)

    assert exit_code == 1
    (drone,) = drones
    assert drone.snapshots_asked_for_after_the_loss == 1  # the next tick's first call raised
    assert drone.command_log == ["connect", "arm", "take_off", "disconnect"]
    log_text = the_log_file_text(tmp_path / "logs")
    assert "The radio link to the drone was lost" in log_text
    assert "Closing without landing: the link is lost and the drone may still be flying." in log_text
    assert "Sending Land()" not in log_text


class SaggingBatteryMockAdapter(MockAdapter):
    """A mock drone whose battery reads below the safety pre-check's limit from the take-off height on."""

    def take_snapshot(self, dt: float) -> Snapshot:
        snapshot = super().take_snapshot(dt)
        position = snapshot.position_estimate
        if position is not None and position.value.z >= TAKE_OFF_HEIGHT:
            self.set_battery_voltage(LOW_BATTERY_VOLTAGE - 0.1)
        return snapshot


def test_a_hover_the_safety_layer_cut_short_exits_with_1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, sim_clock: SimClock
) -> None:
    """ADR-0062, with no line of its own in the log (ADR-0066)."""
    monkeypatch.chdir(tmp_path)

    def make_sagging_drone(use_crazyflie: bool, clock: Clock, *, take_off_log: bool) -> DroneInterface:
        return SaggingBatteryMockAdapter(clock)

    monkeypatch.setattr(hover_module, "make_drone", make_sagging_drone)

    exit_code = main(["--hover-seconds", "5"], clock=sim_clock)

    assert exit_code == 1
    log_text = the_log_file_text(tmp_path / "logs")
    assert "Safety pre-check failed: battery at" in log_text
    assert "Hover test: hovered" not in log_text
    assert "Hover test failed" not in log_text


class InterruptedWhileConnectingMockAdapter(MockAdapter):
    def connect(self) -> None:
        raise KeyboardInterrupt


class FailingDisconnectMockAdapter(MockAdapter):
    def disconnect(self) -> None:
        super().disconnect()
        raise RuntimeError("made-up disconnect failure")


def test_the_interrupt_signal_while_connecting_still_exits_with_130(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, sim_clock: SimClock
) -> None:
    """Though the hover test never ran, so it has failed (ADR-0062)."""
    monkeypatch.chdir(tmp_path)

    def make_drone(use_crazyflie: bool, clock: Clock, *, take_off_log: bool) -> DroneInterface:
        return InterruptedWhileConnectingMockAdapter(clock)

    monkeypatch.setattr(hover_module, "make_drone", make_drone)

    assert main(["--hover-seconds", "0"], clock=sim_clock) == 130


def test_an_error_after_a_full_hover_still_exits_with_1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, sim_clock: SimClock
) -> None:
    """Though the hover test passed (ADR-0062)."""
    monkeypatch.chdir(tmp_path)

    def make_drone(use_crazyflie: bool, clock: Clock, *, take_off_log: bool) -> DroneInterface:
        return FailingDisconnectMockAdapter(clock)

    monkeypatch.setattr(hover_module, "make_drone", make_drone)

    exit_code = main(["--hover-seconds", "0"], clock=sim_clock)

    assert exit_code == 1
    log_text = the_log_file_text(tmp_path / "logs")
    assert "Hover test: landed. Done." in log_text
    assert "made-up disconnect failure" in log_text


@pytest.mark.parametrize("hover_seconds", ["-1", "nan", "inf"])
def test_a_hover_time_that_is_negative_or_endless_is_refused(
    hover_seconds: str, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as stopped:
        main(["--hover-seconds", hover_seconds])

    assert stopped.value.code == 2  # argparse's exit code for a usage error
    assert "--hover-seconds: Hover duration must be zero or more" in capsys.readouterr().err


def test_the_hover_program_runs_as_a_program(tmp_path: Path) -> None:
    finished = subprocess.run(
        [sys.executable, "-m", "crazyflie_behavior.programs.hover", "--hover-seconds", "0"],
        cwd=tmp_path,
        capture_output=True,
        timeout=60.0,
        check=False,
    )

    assert finished.returncode == 0
    assert "Hover test: landed. Done." in the_log_file_text(tmp_path / "logs")


@pytest.mark.parametrize(("arguments", "expected"), [([], False), (["--take-off-log"], True)])
def test_the_take_off_log_option_reaches_make_drone_and_the_description(
    arguments: list[str], expected: bool, monkeypatch: pytest.MonkeyPatch, sim_clock: SimClock
) -> None:
    take_off_logs: list[bool] = []
    descriptions: list[str] = []

    def make_mock_adapter(use_crazyflie: bool, clock: Clock, *, take_off_log: bool) -> DroneInterface:
        take_off_logs.append(take_off_log)
        return MockAdapter(clock)

    def record_the_description(program_name: str, description: str, *_rest: object) -> int:
        descriptions.append(description)
        return 0

    monkeypatch.setattr(hover_module, "make_drone", make_mock_adapter)
    monkeypatch.setattr(hover_module, "run_program", record_the_description)

    main(arguments, clock=sim_clock)

    assert take_off_logs == [expected]
    assert descriptions[0].endswith(", with the take-off block (the mock adapter has none)") == expected


def test_take_off_height_reaches_the_hover_test_and_the_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, sim_clock: SimClock
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["--hover-seconds", "0", "--take-off-height", "0.75"], clock=sim_clock)

    assert exit_code == 0
    log_text = the_log_file_text(tmp_path / "logs")
    assert "hovering 0 s at 0.75 m" in log_text
    assert "Sending TakeOff(height=0.75)" in log_text
    assert "Hover test: landed. Done." in log_text  # it reached that height


@pytest.mark.parametrize("take_off_height", ["0.3", "1.1", "nan"])
def test_a_take_off_height_outside_the_range_is_refused_before_connecting(
    take_off_height: str, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    drones_made: list[bool] = []

    def make_mock_adapter(use_crazyflie: bool, clock: Clock, *, take_off_log: bool) -> DroneInterface:
        drones_made.append(use_crazyflie)
        return MockAdapter(clock)

    monkeypatch.setattr(hover_module, "make_drone", make_mock_adapter)

    with pytest.raises(SystemExit) as stopped:
        main(["--crazyflie", "--take-off-height", take_off_height])

    assert stopped.value.code == 2
    assert "--take-off-height: The take-off height must be 0.4-1 m" in capsys.readouterr().err
    assert drones_made == []


def test_the_hover_program_has_no_climb_speed_option(capsys: pytest.CaptureFixture[str]) -> None:
    # The initial climb is always 0.4 m/s (ADR-0077).
    with pytest.raises(SystemExit) as stopped:
        main(["--climb-speed", "0.3"])

    assert stopped.value.code == 2
    assert "unrecognized arguments: --climb-speed" in capsys.readouterr().err
