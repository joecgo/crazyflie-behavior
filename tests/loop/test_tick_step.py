"""The tick step for flying (ADR-0026): its order, and whole hover tests on the mock adapter."""

import logging
from collections.abc import Callable

import pytest

from crazyflie_behavior.behaviors.behavior import Behavior
from crazyflie_behavior.behaviors.hover_test import TAKE_OFF_HEIGHT, HoverTest
from crazyflie_behavior.drone.mock_adapter import MockAdapter
from crazyflie_behavior.loop.tick_step import BehaviorTickStep
from crazyflie_behavior.safety.requests import CommandRequest, Hover, Verdict
from crazyflie_behavior.safety.safety_layer import SafetyLayer
from crazyflie_behavior.snapshot import Snapshot
from crazyflie_behavior.timing.clock import SimClock

TICK_PERIOD = 0.25
"""Quarter-second ticks keep every time exact in binary."""
GIVE_UP_AFTER_TICKS = 200
"""A flight that never reports done stops after this many ticks."""
HOVER_DURATION = 2.0


class RecordingDrone(MockAdapter):
    def __init__(self, clock: SimClock, events: list[str]) -> None:
        super().__init__(clock)
        self._events = events

    def take_snapshot(self, time: float, dt: float) -> Snapshot:
        self._events.append("snapshot")
        return super().take_snapshot(time, dt)


class RecordingSafetyLayer(SafetyLayer):
    def __init__(self, drone: MockAdapter, events: list[str]) -> None:
        super().__init__(drone)
        self._events = events

    def pre_check(self, snapshot: Snapshot) -> bool:
        self._events.append("pre-check")
        return super().pre_check(snapshot)

    def send(self) -> None:
        self._events.append("send")
        super().send()


class RecordingBehavior(Behavior):
    """Asks to hover each tick, and records when it ran."""

    def __init__(self, events: list[str]) -> None:
        self._events = events

    def tick(self, snapshot: Snapshot, request: Callable[[CommandRequest], Verdict]) -> bool:
        self._events.append("behavior")
        request(Hover())
        return False


def fly(tick_step: BehaviorTickStep, clock: SimClock) -> int:
    """Tick until the tick step is done. Returns how many ticks it took."""
    for tick_number in range(1, GIVE_UP_AFTER_TICKS + 1):
        is_done = tick_step.run(clock.now(), TICK_PERIOD)
        clock.advance(TICK_PERIOD)
        if is_done:
            return tick_number
    pytest.fail(f"Not done after {GIVE_UP_AFTER_TICKS} ticks")


def connected_mock(clock: SimClock) -> MockAdapter:
    drone = MockAdapter(clock)
    drone.connect()
    return drone


def hover_flight(drone: MockAdapter) -> BehaviorTickStep:
    return BehaviorTickStep(drone, SafetyLayer(drone), HoverTest(HOVER_DURATION))


# --- The order --------------------------------------------------------------------


def test_a_tick_runs_snapshot_pre_check_behavior_send_in_that_order() -> None:
    clock = SimClock()
    events: list[str] = []
    drone = RecordingDrone(clock, events)
    drone.connect()
    tick_step = BehaviorTickStep(
        drone, RecordingSafetyLayer(drone, events), RecordingBehavior(events)
    )

    tick_step.run(clock.now(), TICK_PERIOD)

    assert events == ["snapshot", "pre-check", "behavior", "send"]


def test_a_failed_pre_check_skips_the_behavior_and_ends_the_flight() -> None:
    clock = SimClock()
    events: list[str] = []
    drone = RecordingDrone(clock, events)
    drone.connect()
    drone.set_battery_voltage(3.0)
    tick_step = BehaviorTickStep(
        drone, RecordingSafetyLayer(drone, events), RecordingBehavior(events)
    )

    is_done = tick_step.run(clock.now(), TICK_PERIOD)

    assert events == ["snapshot", "pre-check", "send"]
    assert is_done


def test_every_snapshot_goes_to_the_log_at_debug_level(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG, logger="crazyflie_behavior.loop.tick_step")
    clock = SimClock()

    hover_flight(connected_mock(clock)).run(clock.now(), TICK_PERIOD)

    assert "Snapshot: Snapshot(" in caplog.text


# --- Whole hover tests on the mock adapter ----------------------------------------


def test_the_hover_test_arms_takes_off_hovers_and_lands() -> None:
    clock = SimClock()
    drone = connected_mock(clock)
    heights: list[float] = []

    class HeightRecorder(HoverTest):
        def tick(self, snapshot: Snapshot, request: Callable[[CommandRequest], Verdict]) -> bool:
            assert snapshot.position_estimate is not None
            heights.append(snapshot.position_estimate.value.z)
            return super().tick(snapshot, request)

    tick_count = fly(
        BehaviorTickStep(drone, SafetyLayer(drone), HeightRecorder(HOVER_DURATION)), clock
    )

    assert drone.command_log == ["connect", "arm", "take_off", "land"]
    # Arm, take off, then at the height for the hover duration, then landed.
    assert heights.count(TAKE_OFF_HEIGHT) * TICK_PERIOD == HOVER_DURATION + TICK_PERIOD
    assert heights[-1] == 0.0
    assert tick_count == len(heights)


def test_a_low_battery_mid_hover_lands_the_drone_and_ends_the_flight(
    caplog: pytest.LogCaptureFixture,
) -> None:
    clock = SimClock()
    drone = connected_mock(clock)
    tick_step = hover_flight(drone)
    for _ in range(4):  # arm, take off, hovering
        tick_step.run(clock.now(), TICK_PERIOD)
        clock.advance(TICK_PERIOD)

    drone.set_battery_voltage(3.3)
    is_done = tick_step.run(clock.now(), TICK_PERIOD)

    assert is_done
    assert drone.command_log == ["connect", "arm", "take_off", "land"]
    assert "battery at 3.30 V" in caplog.text


def test_a_link_gone_quiet_mid_hover_lands_the_drone() -> None:
    clock = SimClock()
    drone = connected_mock(clock)
    tick_step = hover_flight(drone)
    for _ in range(4):  # arm, take off, hovering
        tick_step.run(clock.now(), TICK_PERIOD)
        clock.advance(TICK_PERIOD)

    drone.stop_telemetry()
    fly(tick_step, clock)

    assert drone.command_log == ["connect", "arm", "take_off", "land"]
