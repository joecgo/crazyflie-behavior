"""Transcript tests: every cflib call the Crazyflie adapter makes, in order, for five scripted flights (ADR-0093).

Each flight runs the adapter against a fake cflib on a sim clock and compares its calls with a stored
transcript in `transcripts/`, one call per line, so a move that reorders or changes a send fails. A missing
transcript is written and its test fails: read it, then commit it. A stored one is never rewritten: delete
it to write it again, so the diff shows the change.
"""

# pyright: reportPrivateUsage=false

import difflib
import inspect
from collections.abc import Callable
from pathlib import Path
from typing import Protocol, cast
from unittest.mock import MagicMock, NonCallableMock

import pytest

from crazyflie_behavior.drone.crazyflie import adapter as adapter_module
from crazyflie_behavior.drone.crazyflie import log_blocks as log_blocks_module
from crazyflie_behavior.drone.crazyflie.adapter import CrazyflieAdapter
from crazyflie_behavior.drone.crazyflie.bad_flow_zone import (
    FINAL_DESCENT_HEIGHT,
    FINAL_DESCENT_SPEED,
    INITIAL_CLIMB_SPEED,
)
from crazyflie_behavior.drone.crazyflie.conversions import OUT_OF_RANGE_THRESHOLD_MM
from crazyflie_behavior.loop.tick_loop import TICK_RATE
from crazyflie_behavior.timing.clock import SimClock

TRANSCRIPTS = Path(__file__).parent / "transcripts"
TICK = 1.0 / TICK_RATE
"""Seconds: one tick period."""
TAKE_OFF_HEIGHT = 0.5
"""Meters: the scripted take-offs' target."""
TAKE_OVER_HEIGHT = 0.6
"""Meters: where the taken-over drone is flying when the link opens."""
FLIGHT_TIME_LIMIT = 60.0
"""Seconds a scripted flight may tick while waiting for something, before its test fails."""
FLYING = float(1 << adapter_module.BIT_IS_FLYING)
"""The supervisor bitfield of a drone that reports flying."""
PARAMETERS = {"deck.bcFlow2": "1", "deck.bcMultiranger": "0", "deck.bcBuzzer": "1"}
"""Parameter values as cflib returns them, as text. A missing one raises KeyError, as in cflib."""
SAMPLE_DEFAULTS = {
    "pm.vbat": 4.0,
    "pm.vbatMV": 4000.0,
    "motion.squal": 80.0,
    "motion.shutter": 3000.0,
    "kalman.varPX": 1e-4,
    "kalman.varPY": 1e-4,
}
"""Log variables that aren't zero and don't follow the flight: a charged battery and good flow."""

type _LogCallback = Callable[[int, dict[str, float], object], None]


class StreamingSimClock(SimClock):
    """A sim clock after whose every wait the fake drone has streamed, as a real drone does meanwhile."""

    def __init__(self, start: float) -> None:
        super().__init__(start)
        self.after_each_wait: Callable[[], None] = lambda: None

    def sleep_until(self, deadline: float) -> None:
        super().sleep_until(deadline)
        self.after_each_wait()


class FakeDrone:
    """The fake drone's flight as the script sets it: its height moves at a set speed toward a set height."""

    def __init__(self, clock: SimClock) -> None:
        self._clock = clock
        self._start_height = 0.0
        self._target_height = 0.0
        self._speed = 0.0
        self._moving_since = clock.now()
        self.is_flying = False
        """What its status reports. The motor stop clears it."""
        self.has_down_range = True
        """False: the down range reads out of range."""

    def height(self) -> float:
        travelled = self._speed * (self._clock.now() - self._moving_since)
        if self._target_height >= self._start_height:
            return min(self._target_height, self._start_height + travelled)
        return max(self._target_height, self._start_height - travelled)

    def move(self, target_height: float, speed: float) -> None:
        """From now on, at `speed` m/s toward `target_height`."""
        self._start_height = self.height()
        self._target_height = target_height
        self._speed = speed
        self._moving_since = self._clock.now()

    def place(self, height: float) -> None:
        """Put it at `height`, still."""
        self._start_height = height
        self._target_height = height
        self._speed = 0.0

    def stop_motors(self, *_: object) -> None:
        self.is_flying = False

    def sample(self, variables: list[str]) -> dict[str, float]:
        """One log sample of `variables`, now."""
        height = self.height()
        flight_values = {
            "stateEstimate.z": height,
            "supervisor.info": FLYING if self.is_flying else 0.0,
            "range.zrange": height * 1000.0 if self.has_down_range else float(OUT_OF_RANGE_THRESHOLD_MM),
        }
        return {variable: flight_values.get(variable, SAMPLE_DEFAULTS.get(variable, 0.0)) for variable in variables}


class FakeCflib:
    """Stands in for cflib: every call on it lands, in order, in `root.mock_calls`.

    Each log block sends the fake drone's sample when it starts and after every wait on the clock. A
    block's `started` is True from its start, as if the drone confirmed it at once, until its stop.
    """

    def __init__(self, drone: FakeDrone, clock: SimClock) -> None:
        self._drone = drone
        self._clock = clock
        self.root = MagicMock(name="cflib")
        self.crazyflie = self.root.Crazyflie.return_value
        # cflib's SyncCrazyflie keeps the Crazyflie it's given as `.cf`.
        self.root.SyncCrazyflie.return_value.cf = self.crazyflie
        self.crazyflie.param.get_value.side_effect = PARAMETERS.__getitem__
        self.crazyflie.high_level_commander.stop.side_effect = drone.stop_motors
        self.root.LogConfig.side_effect = self._make_log_block
        self._blocks: dict[str, MagicMock] = {}
        self._variables: dict[str, list[str]] = {}
        self._callbacks: dict[str, list[_LogCallback]] = {}

    def is_running(self, block_name: str) -> bool:
        block = self._blocks.get(block_name)
        return block is not None and block.started is True

    def stream(self) -> None:
        """Send every started block's sample, as a streaming drone does."""
        for name, block in self._blocks.items():
            if block.started is True:
                self._send(name, block)

    def _send(self, name: str, block: MagicMock) -> None:
        timestamp_ms = round(self._clock.now() * 1000.0)
        sample = self._drone.sample(self._variables[name])
        for callback in self._callbacks[name]:
            callback(timestamp_ms, sample, block)

    def _make_log_block(self, name: str, **_: object) -> MagicMock:
        block = MagicMock()
        self.root.attach_mock(block, f"log_block_{name}")
        block.started = False
        variables: list[str] = []
        self._blocks[name] = block
        self._variables[name] = variables
        self._callbacks[name] = []

        def add_variable(variable: str, fetch_as: str | None = None) -> None:
            variables.append(variable)

        def start() -> None:
            block.started = True
            self._send(name, block)

        def stop() -> None:
            block.started = False

        block.add_variable.side_effect = add_variable
        block.data_received_cb.add_callback.side_effect = self._callbacks[name].append
        block.start.side_effect = start
        block.stop.side_effect = stop
        return block


class ScriptedFlight:
    """A sim clock, the fake drone and the fake cflib, wired together."""

    def __init__(self) -> None:
        self.clock = StreamingSimClock(start=10.0)
        self.drone = FakeDrone(self.clock)
        self.cflib = FakeCflib(self.drone, self.clock)
        self.clock.after_each_wait = self.cflib.stream


@pytest.fixture
def flight(monkeypatch: pytest.MonkeyPatch) -> ScriptedFlight:
    scripted_flight = ScriptedFlight()
    cflib = scripted_flight.cflib.root
    monkeypatch.setattr(adapter_module, "_drivers_initialized", True)
    monkeypatch.setattr(adapter_module, "SyncCrazyflie", cflib.SyncCrazyflie)
    monkeypatch.setattr(adapter_module, "Crazyflie", cflib.Crazyflie)
    monkeypatch.setattr(log_blocks_module, "LogConfig", cflib.LogConfig)
    return scripted_flight


class _Packet(Protocol):
    port: int
    channel: int
    data: bytes


def describe(value: object) -> str:
    """An argument as transcript text, with nothing in it that changes from run to run."""
    if isinstance(value, NonCallableMock):
        # Its name, never its id. str() on a mock would itself be recorded as a call.
        return value._extract_mock_name().removeprefix("cflib.")
    if inspect.ismethod(value):
        return value.__name__  # a callback the adapter hands cflib
    if type(value).__name__ == "CRTPPacket":
        packet = cast(_Packet, value)
        return f"CRTPPacket(port={packet.port}, channel={packet.channel}, data={bytes(packet.data).hex()})"
    if value is None or isinstance(value, bool | int | float | str):
        return repr(value)  # floats in full, so an arithmetic change shows
    raise TypeError(f"No stable transcript text for a {type(value).__name__}")


def describe_call(name: str, args: tuple[object, ...], kwargs: dict[str, object]) -> str:
    arguments = [describe(value) for value in args] + [f"{key}={describe(value)}" for key, value in kwargs.items()]
    return f"{name}({', '.join(arguments)})"


def check_transcript(flight: ScriptedFlight, transcript_name: str) -> None:
    """Compare every cflib call so far with the stored transcript, or write a missing one and fail."""
    calls = [describe_call(name, args, kwargs) for name, args, kwargs in list(flight.cflib.root.mock_calls)]
    path = TRANSCRIPTS / f"{transcript_name}.txt"
    if not path.exists():
        path.parent.mkdir(exist_ok=True)
        path.write_text("\n".join(calls) + "\n", encoding="utf-8", newline="\n")
        pytest.fail(f"Wrote the missing transcript {path.name}: read it, then commit it.")
    stored = path.read_text(encoding="utf-8").splitlines()
    if calls != stored:
        difference = "\n".join(difflib.unified_diff(stored, calls, "stored", "flown", lineterm=""))
        pytest.fail(f"The cflib calls differ from {path.name}:\n{difference}")


def tick(adapter: CrazyflieAdapter, flight: ScriptedFlight) -> None:
    """One tick's calls into the adapter, in the tick step's order: the snapshot, then the take-off and landing
    update."""
    flight.clock.sleep_until(flight.clock.now() + TICK)
    adapter.update_take_off_and_landing(adapter.take_snapshot(TICK))


def fly_until(adapter: CrazyflieAdapter, flight: ScriptedFlight, is_done: Callable[[], bool]) -> None:
    deadline = flight.clock.now() + FLIGHT_TIME_LIMIT
    while not is_done():
        assert flight.clock.now() < deadline, "The scripted flight never got there."
        tick(adapter, flight)


def take_off(adapter: CrazyflieAdapter, flight: ScriptedFlight) -> None:
    adapter.take_off(TAKE_OFF_HEIGHT)
    flight.drone.is_flying = True
    flight.drone.move(TAKE_OFF_HEIGHT, INITIAL_CLIMB_SPEED)


def take_off_and_hover(adapter: CrazyflieAdapter, flight: ScriptedFlight) -> None:
    """Take off once a take-off block's run from connect is over, climb to the take-off height, then hover."""
    tick(adapter, flight)
    fly_until(adapter, flight, lambda: not flight.cflib.is_running("take_off"))
    take_off(adapter, flight)
    fly_until(
        adapter, flight, lambda: flight.drone.height() >= TAKE_OFF_HEIGHT and not flight.cflib.is_running("take_off")
    )
    adapter.hover()
    tick(adapter, flight)


def land_and_wait_for_the_motor_stop(adapter: CrazyflieAdapter, flight: ScriptedFlight) -> None:
    adapter.land()
    flight.drone.move(0.0, FINAL_DESCENT_SPEED)
    fly_until(adapter, flight, lambda: not flight.drone.is_flying)


def test_a_take_off_to_touchdown_sends_what_its_transcript_says(flight: ScriptedFlight) -> None:
    # The take-off log is on, so the take-off block's runs from connect and from the take-off are in it (ADR-0065).
    adapter = CrazyflieAdapter(flight.clock, take_off_log=True)
    adapter.connect()
    take_off_and_hover(adapter, flight)
    land_and_wait_for_the_motor_stop(adapter, flight)
    adapter.disconnect()
    check_transcript(flight, "take_off_to_touchdown")


def test_a_landing_during_the_initial_climb_sends_what_its_transcript_says(flight: ScriptedFlight) -> None:
    adapter = CrazyflieAdapter(flight.clock)
    adapter.connect()
    tick(adapter, flight)
    take_off(adapter, flight)
    # Half the final descent height: still in the initial climb, above the touchdown range.
    fly_until(adapter, flight, lambda: flight.drone.height() >= FINAL_DESCENT_HEIGHT / 2)
    land_and_wait_for_the_motor_stop(adapter, flight)
    adapter.disconnect()
    check_transcript(flight, "landing_during_the_initial_climb")


def test_a_landing_with_no_usable_down_range_sends_what_its_transcript_says(flight: ScriptedFlight) -> None:
    adapter = CrazyflieAdapter(flight.clock)
    adapter.connect()
    take_off_and_hover(adapter, flight)
    flight.drone.has_down_range = False
    tick(adapter, flight)
    land_and_wait_for_the_motor_stop(adapter, flight)  # at the final descent's time limit
    adapter.disconnect()
    check_transcript(flight, "landing_with_no_usable_down_range")


def test_a_take_over_then_a_landing_sends_what_its_transcript_says(flight: ScriptedFlight) -> None:
    flight.drone.place(TAKE_OVER_HEIGHT)
    flight.drone.is_flying = True
    adapter = CrazyflieAdapter(flight.clock, take_over_flight=True)
    adapter.connect()
    tick(adapter, flight)
    land_and_wait_for_the_motor_stop(adapter, flight)
    adapter.disconnect()
    check_transcript(flight, "take_over_then_landing")


def test_a_disconnect_while_flying_lands_then_sends_what_its_transcript_says(flight: ScriptedFlight) -> None:
    adapter = CrazyflieAdapter(flight.clock)
    adapter.connect()
    take_off_and_hover(adapter, flight)
    flight.drone.move(0.0, FINAL_DESCENT_SPEED)  # it follows the landing that disconnect() sends
    adapter.disconnect()
    check_transcript(flight, "disconnect_while_flying")
