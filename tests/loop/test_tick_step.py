"""The tick step for flying (ADR-0026, ADR-0055, ADR-0083): its order, the flight end, and whole hover tests on
the mock adapter."""

import logging
from collections.abc import Callable

import pytest

from crazyflie_behavior.behaviors.behavior import Behavior
from crazyflie_behavior.behaviors.hover_test import TAKE_OFF_HEIGHT, HoverTest
from crazyflie_behavior.drone.crazyflie.bad_flow_zone import FINAL_DESCENT_HEIGHT
from crazyflie_behavior.drone.interface import STALE_AFTER
from crazyflie_behavior.drone.mock_adapter import MockAdapter
from crazyflie_behavior.geometry import Vector3
from crazyflie_behavior.loop.tick_step import FLIGHT_END_TIME_LIMIT, BehaviorTickStep
from crazyflie_behavior.recording.encoding import RequestAndVerdict
from crazyflie_behavior.recording.recorder import Recorder
from crazyflie_behavior.safety.requests import Arm, CommandRequest, Hover, Land, SetVelocity, TakeOff, Verdict
from crazyflie_behavior.safety.safety_layer import FlightEndReason, ReplacedRequest, SafetyEvents, SafetyLayer
from crazyflie_behavior.snapshot import Snapshot
from crazyflie_behavior.timing.clock import SimClock

TICK_PERIOD = STALE_AFTER / 2.0
"""Under the age limit, so a value a tick old isn't at it. Exact in binary only while STALE_AFTER is."""
GIVE_UP_AFTER_TICKS = 200
"""A flight that never reports done stops after this many ticks."""
HOVER_DURATION = 2.0


class CallNotingDrone(MockAdapter):
    def __init__(self, clock: SimClock, events: list[str]) -> None:
        super().__init__(clock)
        self._events = events
        self.snapshots: list[Snapshot] = []

    def take_snapshot(self, dt: float) -> Snapshot:
        self._events.append("snapshot")
        snapshot = super().take_snapshot(dt)
        self.snapshots.append(snapshot)
        return snapshot

    def update_take_off_and_landing(self, snapshot: Snapshot) -> None:
        self._events.append("take-off and landing")
        super().update_take_off_and_landing(snapshot)


class CallNotingSafetyLayer(SafetyLayer):
    def __init__(self, drone: MockAdapter, events: list[str]) -> None:
        super().__init__(drone)
        self._events = events

    def pre_check(self, snapshot: Snapshot) -> bool:
        self._events.append("pre-check")
        return super().pre_check(snapshot)

    def send(self) -> None:
        self._events.append("send")
        super().send()


class CallNotingBehavior(Behavior):
    """Asks to hover each tick, and notes when it ran."""

    def __init__(self, events: list[str]) -> None:
        self._events = events

    def tick(self, snapshot: Snapshot, ask_safety_layer: Callable[[CommandRequest], Verdict]) -> bool:
        self._events.append("behavior")
        ask_safety_layer(Hover())
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


def tick_until_hovering(tick_step: BehaviorTickStep, drone: MockAdapter, clock: SimClock) -> None:
    """Tick the hover test until the drone is at its take-off height, past the initial climb."""
    for _ in range(GIVE_UP_AFTER_TICKS):
        if drone.take_snapshot(0.0).may_be_flying and height_now(drone) == TAKE_OFF_HEIGHT:
            return
        assert not tick_step.run(clock.now(), TICK_PERIOD)
        clock.advance(TICK_PERIOD)
    pytest.fail(f"Not hovering after {GIVE_UP_AFTER_TICKS} ticks")


def height_now(drone: MockAdapter) -> float:
    position_estimate = drone.take_snapshot(0.0).position_estimate
    assert position_estimate is not None
    return position_estimate.value.z


# --- The order --------------------------------------------------------------------


def test_a_tick_runs_snapshot_pre_check_take_off_and_landing_behavior_send_in_that_order(sim_clock: SimClock) -> None:
    clock = sim_clock
    events: list[str] = []
    drone = CallNotingDrone(clock, events)
    drone.connect()
    tick_step = BehaviorTickStep(drone, CallNotingSafetyLayer(drone, events), CallNotingBehavior(events))

    tick_step.run(clock.now(), TICK_PERIOD)

    assert events == ["snapshot", "pre-check", "take-off and landing", "behavior", "send"]


def test_a_failed_pre_check_skips_the_behavior_but_not_take_off_and_landing_and_ends_the_flight(
    sim_clock: SimClock,
) -> None:
    clock = sim_clock
    events: list[str] = []
    drone = CallNotingDrone(clock, events)
    drone.connect()
    drone.set_battery_voltage(3.0)
    drone.set_battery_voltage(3.0)  # two readings in a row (ADR-0069)
    tick_step = BehaviorTickStep(drone, CallNotingSafetyLayer(drone, events), CallNotingBehavior(events))

    is_done = tick_step.run(clock.now(), TICK_PERIOD)

    # Take-off and landing still update: a level part's setpoint stream must not stop (ADR-0055).
    assert events == ["snapshot", "pre-check", "take-off and landing", "send"]
    assert is_done


def test_every_snapshot_goes_to_the_log_at_debug_level(caplog: pytest.LogCaptureFixture, sim_clock: SimClock) -> None:
    caplog.set_level(logging.DEBUG, logger="crazyflie_behavior.loop.tick_step")
    clock = sim_clock

    hover_flight(connected_mock(clock)).run(clock.now(), TICK_PERIOD)

    assert "Snapshot: Snapshot(" in caplog.text


# --- Whole hover tests on the mock adapter ----------------------------------------


def test_the_hover_test_arms_takes_off_hovers_and_lands(sim_clock: SimClock) -> None:
    clock = sim_clock
    drone = connected_mock(clock)
    heights: list[float] = []

    class HeightRecorder(HoverTest):
        def tick(self, snapshot: Snapshot, ask_safety_layer: Callable[[CommandRequest], Verdict]) -> bool:
            assert snapshot.position_estimate is not None
            heights.append(snapshot.position_estimate.value.z)
            return super().tick(snapshot, ask_safety_layer)

    tick_count = fly(BehaviorTickStep(drone, SafetyLayer(drone), HeightRecorder(HOVER_DURATION)), clock)

    assert drone.command_log == ["connect", "arm", "take_off", "land"]
    # Arm, the level initial climb, at the height for the hover duration, then the level final descent.
    # Each snapshot shows the end of the previous tick (ADR-0055), so the landing shows a tick late.
    first_at_height = heights.index(TAKE_OFF_HEIGHT)
    ticks_at_height = heights.count(TAKE_OFF_HEIGHT)
    climb, descent = heights[:first_at_height], heights[first_at_height + ticks_at_height :]
    assert climb == sorted(climb)
    assert max(climb) < FINAL_DESCENT_HEIGHT
    assert ticks_at_height * TICK_PERIOD == pytest.approx(HOVER_DURATION + 2 * TICK_PERIOD)
    assert descent == sorted(descent, reverse=True)
    assert descent[0] < FINAL_DESCENT_HEIGHT
    assert heights[-1] == 0.0
    assert tick_count == len(heights)


def test_a_low_battery_mid_hover_lands_the_drone_before_the_run_ends(
    caplog: pytest.LogCaptureFixture,
    sim_clock: SimClock,
) -> None:
    clock = sim_clock
    drone = connected_mock(clock)
    tick_step = hover_flight(drone)
    tick_until_hovering(tick_step, drone, clock)

    drone.set_battery_voltage(3.1)
    drone.set_battery_voltage(3.1)  # two readings in a row (ADR-0069)
    is_done = tick_step.run(clock.now(), TICK_PERIOD)
    clock.advance(TICK_PERIOD)

    assert not is_done  # the drone lands inside the tick loop first (ADR-0083)
    fly(tick_step, clock)
    assert drone.command_log == ["connect", "arm", "take_off", "land"]
    assert not drone.take_snapshot(0.0).may_be_flying
    assert "battery at 3.10 V" in caplog.text


def test_a_link_gone_quiet_mid_hover_lands_the_drone(sim_clock: SimClock) -> None:
    clock = sim_clock
    drone = connected_mock(clock)
    tick_step = hover_flight(drone)
    tick_until_hovering(tick_step, drone, clock)

    drone.stop_telemetry()
    fly(tick_step, clock)

    assert drone.command_log == ["connect", "arm", "take_off", "land"]


# --- The flight end (ADR-0083) ------------------------------------------------------


class TickCountingHoverTest(HoverTest):
    """The hover test, counting the ticks it's given."""

    def __init__(self) -> None:
        super().__init__(HOVER_DURATION)
        self.tick_count = 0

    def tick(self, snapshot: Snapshot, ask_safety_layer: Callable[[CommandRequest], Verdict]) -> bool:
        self.tick_count += 1
        return super().tick(snapshot, ask_safety_layer)


class DoneInFlight(Behavior):
    """Arms, takes off, and reports done as soon as the drone may be flying, as a behavior that fails in the air."""

    def __init__(self) -> None:
        self.ticks_after_done = 0
        self._requests: list[CommandRequest] = []
        self._is_done = False

    def tick(self, snapshot: Snapshot, ask_safety_layer: Callable[[CommandRequest], Verdict]) -> bool:
        status = snapshot.drone_status
        assert status is not None
        # Each request once: a snapshot shows the drone as it was a tick earlier (ADR-0055).
        if self._is_done:
            self.ticks_after_done += 1
        elif snapshot.may_be_flying:
            self._is_done = True
        elif not self._requests:
            self._ask(Arm(), ask_safety_layer)
        elif status.value.is_armed and len(self._requests) == 1:
            self._ask(TakeOff(TAKE_OFF_HEIGHT), ask_safety_layer)
        return self._is_done

    def _ask(self, request: CommandRequest, ask_safety_layer: Callable[[CommandRequest], Verdict]) -> None:
        assert ask_safety_layer(request).is_approved
        self._requests.append(request)


class UnlandableMockAdapter(MockAdapter):
    """A mock drone that ignores land, so it may be flying for as long as a test runs."""

    def land(self) -> None:
        self.command_log.append("land (ignored)")


def tick_until_it_may_be_flying(tick_step: BehaviorTickStep, drone: MockAdapter, clock: SimClock) -> None:
    for _ in range(GIVE_UP_AFTER_TICKS):
        if drone.take_snapshot(0.0).may_be_flying:
            return
        assert not tick_step.run(clock.now(), TICK_PERIOD)
        clock.advance(TICK_PERIOD)
    pytest.fail(f"Not flying after {GIVE_UP_AFTER_TICKS} ticks")


def test_a_stop_request_in_flight_lands_the_drone_and_skips_the_behavior_until_the_drone_is_down(
    sim_clock: SimClock,
) -> None:
    clock = sim_clock
    drone = connected_mock(clock)
    behavior = TickCountingHoverTest()
    safety_layer = SafetyLayer(drone)
    tick_step = BehaviorTickStep(drone, safety_layer, behavior)
    tick_until_it_may_be_flying(tick_step, drone, clock)
    ticks_before_the_stop_request = behavior.tick_count

    tick_step.request_stop()
    tick_count = fly(tick_step, clock)

    assert tick_count > 1  # it kept ticking while the drone landed
    assert behavior.tick_count == ticks_before_the_stop_request
    assert drone.command_log == ["connect", "arm", "take_off", "land"]
    assert not drone.take_snapshot(0.0).may_be_flying
    assert safety_layer.flight_end_reason is FlightEndReason.STOP_REQUEST
    assert not safety_layer.pre_check_has_failed  # so it can't count as the failsafe program's pass


def test_a_stop_request_on_the_floor_sends_a_land_and_ends_the_run_on_that_tick(sim_clock: SimClock) -> None:
    clock = sim_clock
    events: list[str] = []
    drone = connected_mock(clock)
    tick_step = BehaviorTickStep(drone, SafetyLayer(drone), CallNotingBehavior(events))

    tick_step.request_stop()
    is_done = tick_step.run(clock.now(), TICK_PERIOD)

    assert is_done
    assert drone.command_log == ["connect", "land"]  # the adapter turns it into a motor stop
    assert events == []


def test_a_behavior_done_in_flight_sets_the_flight_end_and_the_drone_lands_before_the_run_ends(
    sim_clock: SimClock,
) -> None:
    clock = sim_clock
    drone = connected_mock(clock)
    behavior = DoneInFlight()
    safety_layer = SafetyLayer(drone)

    fly(BehaviorTickStep(drone, safety_layer, behavior), clock)

    assert safety_layer.flight_end_reason is FlightEndReason.BEHAVIOR_DONE_IN_FLIGHT
    assert drone.command_log == ["connect", "arm", "take_off", "land"]
    assert behavior.ticks_after_done == 0
    assert not drone.take_snapshot(0.0).may_be_flying


def test_a_behavior_done_on_the_floor_ends_the_run_with_no_flight_end(sim_clock: SimClock) -> None:
    clock = sim_clock
    drone = connected_mock(clock)
    safety_layer = SafetyLayer(drone)

    fly(BehaviorTickStep(drone, safety_layer, HoverTest(HOVER_DURATION)), clock)

    assert safety_layer.flight_end_reason is None
    assert drone.command_log == ["connect", "arm", "take_off", "land"]


def test_a_drone_that_may_still_be_flying_at_the_flight_ends_time_limit_is_an_error_one_tick_before_is_not(
    sim_clock: SimClock,
) -> None:
    clock = sim_clock
    drone = UnlandableMockAdapter(clock)
    drone.connect()
    tick_step = hover_flight(drone)
    tick_until_it_may_be_flying(tick_step, drone, clock)
    tick_step.request_stop()
    flight_ended_at = clock.now()  # the next tick is the first after the flight end
    while clock.now() < flight_ended_at + FLIGHT_END_TIME_LIMIT - TICK_PERIOD:
        assert not tick_step.run(clock.now(), TICK_PERIOD)
        clock.advance(TICK_PERIOD)

    is_done_one_tick_before = tick_step.run(clock.now(), TICK_PERIOD)
    clock.advance(TICK_PERIOD)

    assert not is_done_one_tick_before
    assert clock.now() == flight_ended_at + FLIGHT_END_TIME_LIMIT
    with pytest.raises(TimeoutError, match="may still be flying 60 s after the flight end"):
        tick_step.run(clock.now(), TICK_PERIOD)


# --- The recording (ADR-0088) -------------------------------------------------------


class FakeRecorder(Recorder):
    """Keeps what the tick step hands it instead of writing a file, and notes each call in the events."""

    def __init__(self, events: list[str] | None = None) -> None:
        super().__init__("mock", ())
        self._events = events if events is not None else []
        self.requests: list[RequestAndVerdict] = []
        self.tick_step_records: list[tuple[Snapshot, SafetyEvents, FlightEndReason | None]] = []

    def record_request(self, command_request: CommandRequest, verdict: Verdict) -> None:
        self._events.append("record request")
        self.requests.append(RequestAndVerdict(command_request, verdict))

    def record_tick(self, snapshot: Snapshot, events: SafetyEvents, flight_end_reason: FlightEndReason | None) -> None:
        self._events.append("record tick")
        self.tick_step_records.append((snapshot, events, flight_end_reason))


class AskingBehavior(Behavior):
    """Asks for each of its requests on its first tick, keeping the verdicts it gets."""

    def __init__(self, *requests: CommandRequest) -> None:
        self.requests = requests
        self.verdicts: list[Verdict] = []

    def tick(self, snapshot: Snapshot, ask_safety_layer: Callable[[CommandRequest], Verdict]) -> bool:
        if not self.verdicts:
            self.verdicts = [ask_safety_layer(command_request) for command_request in self.requests]
        return False


class FailingBehavior(Behavior):
    """Asks to hover, then raises, as a behavior with a bug."""

    def tick(self, snapshot: Snapshot, ask_safety_layer: Callable[[CommandRequest], Verdict]) -> bool:
        ask_safety_layer(Hover())
        raise RuntimeError("the behavior broke")


def test_with_a_recorder_a_tick_hands_it_each_request_as_asked_then_its_record_after_the_send(
    sim_clock: SimClock,
) -> None:
    clock = sim_clock
    events: list[str] = []
    drone = CallNotingDrone(clock, events)
    drone.connect()
    recorder = FakeRecorder(events)
    tick_step = BehaviorTickStep(drone, CallNotingSafetyLayer(drone, events), CallNotingBehavior(events), recorder)

    tick_step.run(clock.now(), TICK_PERIOD)

    assert events == [
        "snapshot",
        "pre-check",
        "take-off and landing",
        "behavior",
        "record request",
        "send",
        "record tick",
    ]


def test_each_request_is_recorded_with_the_verdict_the_behavior_got(sim_clock: SimClock) -> None:
    clock = sim_clock
    drone = connected_mock(clock)
    behavior = AskingBehavior(Hover(), SetVelocity(Vector3(0.5, 0.0, 0.0)), Land())
    recorder = FakeRecorder()

    BehaviorTickStep(drone, SafetyLayer(drone), behavior, recorder).run(clock.now(), TICK_PERIOD)

    assert recorder.requests == [
        RequestAndVerdict(command_request, verdict)
        for command_request, verdict in zip(behavior.requests, behavior.verdicts, strict=True)
    ]
    assert [verdict.is_approved for verdict in behavior.verdicts] == [True, False, True]


def test_the_tick_step_record_is_the_ticks_snapshot_and_its_events_once_the_behavior_has_run(
    sim_clock: SimClock,
) -> None:
    clock = sim_clock
    drone = CallNotingDrone(clock, [])
    drone.connect()
    recorder = FakeRecorder()

    BehaviorTickStep(drone, SafetyLayer(drone), AskingBehavior(Hover(), Land()), recorder).run(clock.now(), TICK_PERIOD)

    [snapshot] = drone.snapshots
    replaced = SafetyEvents(pre_check_failures=(), replaced_requests=(ReplacedRequest("movement", Hover(), Land()),))
    assert recorder.tick_step_records == [(snapshot, replaced, None)]


def test_a_failed_pre_checks_record_has_its_reasons_and_the_flight_end_reason(sim_clock: SimClock) -> None:
    clock = sim_clock
    drone = connected_mock(clock)
    drone.set_battery_voltage(3.0)
    drone.set_battery_voltage(3.0)  # two readings in a row (ADR-0069)
    recorder = FakeRecorder()

    BehaviorTickStep(drone, SafetyLayer(drone), CallNotingBehavior([]), recorder).run(clock.now(), TICK_PERIOD)

    [(_snapshot, events, flight_end_reason)] = recorder.tick_step_records
    assert events.pre_check_failures == ("battery at 3.00 V (land below 3.20 V)",)
    assert flight_end_reason is FlightEndReason.PRE_CHECK_FAILED


def test_a_tick_that_raised_after_its_snapshot_still_hands_its_record_over(sim_clock: SimClock) -> None:
    """So the recording keeps what that tick saw, up to the error."""
    clock = sim_clock
    drone = CallNotingDrone(clock, [])
    drone.connect()
    recorder = FakeRecorder()
    tick_step = BehaviorTickStep(drone, SafetyLayer(drone), FailingBehavior(), recorder)

    with pytest.raises(RuntimeError, match="the behavior broke"):
        tick_step.run(clock.now(), TICK_PERIOD)

    assert recorder.requests == [RequestAndVerdict(Hover(), Verdict.approved())]
    assert [snapshot for snapshot, _events, _flight_end_reason in recorder.tick_step_records] == drone.snapshots
