"""The Crazyflie adapter's take-off: the initial climb through the bad-flow zone (ADR-0048, ADR-0049, ADR-0056).

Against a fake cflib: each test checks what the adapter would send to a real drone.
"""

# The adapter has no seam for a fake connection, so the tests set its private fields directly.
# pyright: reportPrivateUsage=false

import itertools
import logging
import struct
from collections.abc import Callable
from unittest.mock import MagicMock

import pytest

from crazyflie_behavior.drone.crazyflie import adapter as adapter_module
from crazyflie_behavior.drone.crazyflie.adapter import (
    DEFAULT_YAW_RAD,
    LOW_LIGHT_IMAGE_QUALITY,
    TAKE_OFF_STATUS_GRACE,
    TOUCHDOWN_POLL_PERIOD,
    VERTICAL_SPEED,
    CrazyflieAdapter,
)
from crazyflie_behavior.drone.crazyflie.bad_flow_zone import (
    LEVEL_VERTICAL_SPEED,
    SETTLE_CAP_HEIGHT,
    SETTLE_SPEED,
    initial_climb_time_limit,
)
from crazyflie_behavior.drone.crazyflie.conversions import alt_hold_packet_data
from crazyflie_behavior.drone.crazyflie.touchdown import TOUCHDOWN_HOLD
from crazyflie_behavior.geometry import Vector3
from crazyflie_behavior.snapshot import DroneStatus, RangeDirection, RangeReading
from crazyflie_behavior.timing.clock import SimClock

TICK = 0.05
CLIMB_STEP = LEVEL_VERTICAL_SPEED * TICK
"""Meters climbed per tick."""
FLYING = DroneStatus(is_armed=True, is_flying=True, is_crashed=False, is_tumbled=False, can_arm=False, is_locked=False)
ON_THE_FLOOR = DroneStatus(
    is_armed=True, is_flying=False, is_crashed=False, is_tumbled=False, can_arm=False, is_locked=False
)
FAST = 2 * SETTLE_SPEED
"""Meters per second: a horizontal speed estimate that never counts as settled."""
START = 10.0
GIVE_UP_AFTER = 30.0
"""Simulated seconds after which a test fails instead of waiting forever."""
GIVE_UP_AFTER_TICKS = round(GIVE_UP_AFTER / TICK)


class BoundedSimClock(SimClock):
    """A sim clock that fails the test if a loop keeps waiting past GIVE_UP_AFTER."""

    def sleep_until(self, deadline: float) -> None:
        if deadline > START + GIVE_UP_AFTER:
            raise AssertionError(f"still waiting at t={deadline:.1f} s: the motors never stopped")
        super().sleep_until(deadline)


@pytest.fixture
def clock() -> SimClock:
    return BoundedSimClock(start=START)


@pytest.fixture
def fake_link() -> MagicMock:
    return MagicMock()


@pytest.fixture
def adapter(clock: SimClock, fake_link: MagicMock) -> CrazyflieAdapter:
    """A connected adapter whose drone sits on the floor."""
    adapter = CrazyflieAdapter(clock)
    adapter._sync_crazyflie = fake_link
    return adapter


def call_names(fake_link: MagicMock) -> list[str]:
    """Every call the adapter made, in order, e.g. "cf.send_packet"."""
    return [name for name, _, _ in fake_link.mock_calls]


def level_setpoints(fake_link: MagicMock) -> list[float]:
    """The vertical speed of each level setpoint sent, in order (meters per second, up)."""
    return [struct.unpack("<Bffff", call.args[0].data)[4] for call in fake_link.cf.send_packet.call_args_list]


def climb_tick(
    adapter: CrazyflieAdapter,
    clock: SimClock,
    height: float,
    *,
    horizontal_speed: float = 0.0,
    down: RangeReading | None = None,
    x: float = 0.5,
    velocity_uncertainty: float = 0.01,
) -> None:
    """One tick of the initial climb: the drone reports `height`, then the adapter updates.

    `down`: the down range reading; None means a distance equal to the height.
    `velocity_uncertainty`: m/s; the default means flow is arriving.
    """
    clock.advance(TICK)
    telemetry = adapter._telemetry
    telemetry.write_estimates_and_status(
        Vector3(x, -0.25, height), Vector3(horizontal_speed, 0.0, LEVEL_VERTICAL_SPEED), FLYING, None
    )
    telemetry.write_range_readings(
        {RangeDirection.DOWN: RangeReading.at_distance(height) if down is None else down}, None
    )
    telemetry.write_velocity_uncertainty(velocity_uncertainty, None)
    adapter.update_take_off_and_landing(adapter.take_snapshot(TICK))


def climb_until_handed_over(adapter: CrazyflieAdapter, clock: SimClock) -> list[float]:
    """Tick the initial climb with good flow until it hands over. Returns the height of each tick."""
    heights: list[float] = []
    while adapter._is_in_initial_climb:
        if len(heights) > GIVE_UP_AFTER_TICKS:
            pytest.fail("the initial climb never handed over")
        heights.append((len(heights) + 1) * CLIMB_STEP)
        climb_tick(adapter, clock, heights[-1])
    return heights


def climb_until_it_lands(adapter: CrazyflieAdapter, fake_link: MagicMock, next_tick: Callable[[int], None]) -> int:
    """Run `next_tick(tick)` for ticks 1, 2, ... until a level setpoint goes down. Returns the last tick."""
    for tick in range(1, GIVE_UP_AFTER_TICKS):
        next_tick(tick)
        if level_setpoints(fake_link)[-1] < 0.0:
            return tick
    pytest.fail("the initial climb never landed")


# --- The initial climb --------------------------------------------------------------


def test_take_off_starts_the_initial_climb_with_one_level_setpoint_at_once(
    adapter: CrazyflieAdapter, fake_link: MagicMock
) -> None:
    adapter.take_off(1.0)

    assert call_names(fake_link) == ["cf.send_packet"]  # no high-level take-off
    packet = fake_link.cf.send_packet.call_args.args[0]
    assert (packet.port, packet.channel) == (0x07, 0)  # cflib's COMMANDER_GENERIC port, the setpoint channel
    assert bytes(packet.data) == alt_hold_packet_data(LEVEL_VERTICAL_SPEED)


def test_each_tick_of_the_initial_climb_sends_one_level_setpoint_up(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    adapter.take_off(1.0)

    for tick in range(1, 6):
        climb_tick(adapter, clock, tick * CLIMB_STEP)

    assert level_setpoints(fake_link) == [pytest.approx(LEVEL_VERTICAL_SPEED)] * 6
    assert call_names(fake_link) == ["cf.send_packet"] * 6


def test_take_snapshot_sends_nothing_to_the_drone(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    adapter.take_off(1.0)
    climb_tick(adapter, clock, CLIMB_STEP)
    fake_link.reset_mock()

    clock.advance(TICK)
    adapter.take_snapshot(TICK)

    assert call_names(fake_link) == []


def test_the_climb_hands_over_at_the_final_descent_height_last_setpoint_then_go_to_then_release(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    adapter.take_off(1.0)

    heights = climb_until_handed_over(adapter, clock)

    final_descent_height = adapter._final_descent_height
    assert heights[-1] >= final_descent_height > heights[-2]  # not before the down range reached it
    assert len(level_setpoints(fake_link)) == 1 + len(heights)  # the take-off's, then one per tick, hand-over too
    assert call_names(fake_link)[-3:] == [
        "cf.send_packet",
        "cf.high_level_commander.go_to",
        "cf.commander.send_notify_setpoint_stop",
    ]
    assert level_setpoints(fake_link)[-1] == pytest.approx(LEVEL_VERTICAL_SPEED)
    fake_link.cf.high_level_commander.go_to.assert_called_once_with(
        0.5, -0.25, 1.0, DEFAULT_YAW_RAD, pytest.approx((1.0 - heights[-1]) / VERTICAL_SPEED)
    )


def test_after_the_hand_over_nothing_more_is_streamed(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    adapter.take_off(1.0)
    heights = climb_until_handed_over(adapter, clock)
    fake_link.reset_mock()

    for tick in range(1, 6):
        climb_tick(adapter, clock, heights[-1] + tick * CLIMB_STEP)

    assert call_names(fake_link) == []


def test_the_climb_to_the_take_off_height_holds_the_current_x_and_y_not_the_take_off_point(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    adapter.take_off(1.0)
    tick = 0
    while adapter._is_in_initial_climb and tick < GIVE_UP_AFTER_TICKS:
        tick += 1
        climb_tick(adapter, clock, tick * CLIMB_STEP, x=0.5 + 0.01 * tick)  # the estimate shifts in the zone

    x, y, _, _, _ = fake_link.cf.high_level_commander.go_to.call_args.args
    assert (x, y) == (pytest.approx(0.5 + 0.01 * tick), -0.25)


def test_the_climb_logs_the_settle_height_and_the_final_descent_height(
    adapter: CrazyflieAdapter, clock: SimClock, caplog: pytest.LogCaptureFixture
) -> None:
    adapter.take_off(1.0)

    with caplog.at_level(logging.INFO, logger=adapter_module.logger.name):
        climb_until_handed_over(adapter, clock)

    settle_height = adapter._settle_detector.settle_height
    assert settle_height is not None
    message = f"settle height {settle_height:.3f} m, final descent height {adapter._final_descent_height:.3f} m"
    assert [record.levelno for record in caplog.records if message in record.getMessage()] == [logging.INFO]


def test_a_climb_that_never_settles_lands_level_at_its_time_limit(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    adapter.take_off(1.0)
    take_off_sent_at = clock.now()

    with caplog.at_level(logging.WARNING, logger=adapter_module.logger.name):
        climb_until_it_lands(
            adapter, fake_link, lambda _: climb_tick(adapter, clock, 0.08)
        )  # stuck where no hold starts

    assert clock.now() - take_off_sent_at == pytest.approx(initial_climb_time_limit(LEVEL_VERTICAL_SPEED))
    assert level_setpoints(fake_link)[-1] == pytest.approx(-LEVEL_VERTICAL_SPEED)  # the final descent
    assert any("initial climb hasn't ended" in record.getMessage() for record in caplog.records)


def test_a_climb_whose_speed_hasnt_settled_by_the_cap_height_lands_at_once(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    adapter.take_off(1.0)
    with caplog.at_level(logging.WARNING, logger=adapter_module.logger.name):
        tick = climb_until_it_lands(
            adapter, fake_link, lambda tick: climb_tick(adapter, clock, tick * CLIMB_STEP, horizontal_speed=FAST)
        )

    assert tick * CLIMB_STEP > SETTLE_CAP_HEIGHT >= (tick - 1) * CLIMB_STEP  # the first tick above it
    assert level_setpoints(fake_link)[-1] == pytest.approx(-LEVEL_VERTICAL_SPEED)
    fake_link.cf.high_level_commander.go_to.assert_not_called()
    assert any("hasn't settled" in record.getMessage() for record in caplog.records)


# --- Landing during the initial climb (ADR-0049) --------------------------------------


def test_land_during_the_initial_climb_starts_the_level_final_descent_from_there(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    adapter.take_off(1.0)
    for tick in range(1, 4):
        climb_tick(adapter, clock, tick * CLIMB_STEP)

    adapter.land()
    climb_tick(adapter, clock, 2 * CLIMB_STEP)

    assert level_setpoints(fake_link)[-2:] == [pytest.approx(-LEVEL_VERTICAL_SPEED)] * 2
    fake_link.cf.high_level_commander.go_to.assert_not_called()  # no landing approach


def test_land_during_the_initial_climb_without_a_usable_down_range_hands_over_to_the_slow_descent(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    adapter.take_off(1.0)
    climb_tick(adapter, clock, CLIMB_STEP, down=RangeReading.invalid())

    adapter.land()

    assert call_names(fake_link)[-3:] == [
        "cf.send_packet",
        "cf.high_level_commander.go_to",
        "cf.commander.send_notify_setpoint_stop",
    ]
    # The take-off's, the tick's, then the hand-over's last one.
    assert level_setpoints(fake_link) == [pytest.approx(LEVEL_VERTICAL_SPEED)] * 3
    assert fake_link.cf.high_level_commander.go_to.call_args.kwargs == {"relative": True, "linear": True}


def test_land_right_after_a_take_off_lands_before_the_status_shows_flying(
    adapter: CrazyflieAdapter, fake_link: MagicMock
) -> None:
    adapter.take_off(1.0)
    adapter._telemetry.write_range_readings({RangeDirection.DOWN: RangeReading.at_distance(0.02)}, None)
    adapter._telemetry.write_drone_status(ON_THE_FLOOR, None)  # the status lags a few ticks behind

    adapter.land()

    assert level_setpoints(fake_link)[-1] == pytest.approx(-LEVEL_VERTICAL_SPEED)
    fake_link.cf.high_level_commander.stop.assert_not_called()


def test_land_during_a_climb_that_never_left_the_floor_just_stops_the_motors(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    adapter.take_off(1.0)
    clock.advance(TAKE_OFF_STATUS_GRACE + TICK)
    adapter._telemetry.write_drone_status(ON_THE_FLOOR, None)  # fresh, and says on the floor

    adapter.land()

    assert level_setpoints(fake_link) == [pytest.approx(LEVEL_VERTICAL_SPEED)]  # only the climb's first
    fake_link.cf.high_level_commander.stop.assert_called_once()


def test_land_during_a_climb_with_touchdown_already_confirmed_stops_the_motors_at_once(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    # The motors spin, the status says flying, but the drone hasn't left the floor.
    adapter.take_off(1.0)
    for _ in range(round(TOUCHDOWN_HOLD / TICK) + 1):
        climb_tick(adapter, clock, 0.02)

    with caplog.at_level(logging.INFO, logger=adapter_module.logger.name):
        adapter.land()

    fake_link.cf.high_level_commander.stop.assert_called_once()
    assert level_setpoints(fake_link)[-1] == pytest.approx(LEVEL_VERTICAL_SPEED)  # no final descent setpoint
    assert any("Touchdown confirmed" in record.getMessage() for record in caplog.records)


def test_shutdown_during_the_initial_climb_keeps_the_level_stream_going_every_poll(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    adapter.take_off(1.0)
    for tick in range(1, 21):  # up to 0.2 m, not settled yet
        climb_tick(adapter, clock, tick * CLIMB_STEP, horizontal_speed=FAST)
    sent_at: list[float] = []
    fake_link.cf.send_packet.side_effect = lambda packet: sent_at.append(clock.now())  # type: ignore[reportUnknownLambdaType]

    adapter.disconnect()

    gaps = [later - earlier for earlier, later in itertools.pairwise(sent_at)]
    assert len(sent_at) > 10
    assert max(gaps) == pytest.approx(TOUCHDOWN_POLL_PERIOD)
    fake_link.cf.high_level_commander.stop.assert_called_once()


def test_shutdown_after_a_take_off_that_never_flew_stops_the_motors_without_landing(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    adapter.take_off(1.0)
    clock.advance(TAKE_OFF_STATUS_GRACE + TICK)
    adapter._telemetry.write_drone_status(ON_THE_FLOOR, None)

    adapter.disconnect()

    fake_link.cf.high_level_commander.go_to.assert_not_called()
    assert level_setpoints(fake_link) == [pytest.approx(LEVEL_VERTICAL_SPEED)]
    fake_link.cf.high_level_commander.stop.assert_called_once()
    fake_link.close_link.assert_called_once()


# --- Commands during the initial climb (ADR-0056) -------------------------------------


def test_commands_during_the_initial_climb_are_ignored_and_logged_once(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    adapter.take_off(1.0)
    climb_tick(adapter, clock, CLIMB_STEP)
    fake_link.reset_mock()

    with caplog.at_level(logging.INFO, logger=adapter_module.logger.name):
        adapter.hover()
        adapter.move_to(Vector3(1.0, 0.0, 1.0), duration=2.0)
        adapter.set_velocity(Vector3(0.2, 0.0, 0.0))
        adapter.take_off(1.5)

    assert call_names(fake_link) == []
    ignored = [record for record in caplog.records if "ignored during the initial climb" in record.getMessage()]
    assert [record.levelno for record in ignored] == [logging.INFO]
    assert adapter._is_in_initial_climb


def test_a_take_off_while_flying_above_the_bad_flow_zone_is_a_high_level_climb(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    adapter.take_off(1.0)
    climb_until_handed_over(adapter, clock)
    adapter._telemetry.write_estimates_and_status(Vector3(0.5, -0.25, 1.0), Vector3.ZERO, FLYING, None)
    fake_link.reset_mock()

    adapter.take_off(1.5)

    assert call_names(fake_link) == ["cf.high_level_commander.go_to"]
    fake_link.cf.high_level_commander.go_to.assert_called_once_with(
        0.5, -0.25, 1.5, DEFAULT_YAW_RAD, pytest.approx(0.5 / VERTICAL_SPEED)
    )


# --- The flow and the estimate reset (ADR-0054) ---------------------------------------

NO_FLOW = 0.1
"""Meters per second: a velocity uncertainty without flow."""


def test_a_climb_without_flow_finds_no_settle_height_and_lands_at_the_cap(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    adapter.take_off(1.0)

    tick = climb_until_it_lands(
        adapter, fake_link, lambda tick: climb_tick(adapter, clock, tick * CLIMB_STEP, velocity_uncertainty=NO_FLOW)
    )

    assert tick * CLIMB_STEP > SETTLE_CAP_HEIGHT >= (tick - 1) * CLIMB_STEP
    fake_link.cf.high_level_commander.go_to.assert_not_called()


def test_a_climb_whose_flow_arrives_above_the_dark_floor_hands_over(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    dark_below = 0.17
    adapter.take_off(1.0)

    for tick in range(1, GIVE_UP_AFTER_TICKS):
        height = tick * CLIMB_STEP
        climb_tick(adapter, clock, height, velocity_uncertainty=NO_FLOW if height < dark_below else 0.01)
        if not adapter._is_in_initial_climb:
            break

    fake_link.cf.high_level_commander.go_to.assert_called_once()
    assert adapter._final_descent_height > dark_below


def test_the_snapshot_says_whether_the_initial_climb_is_running(adapter: CrazyflieAdapter, clock: SimClock) -> None:
    assert not adapter.take_snapshot(TICK).is_in_initial_climb
    adapter.take_off(1.0)
    assert adapter.take_snapshot(TICK).is_in_initial_climb
    climb_until_handed_over(adapter, clock)
    assert not adapter.take_snapshot(TICK).is_in_initial_climb


def low_light_warnings(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [record.getMessage() for record in caplog.records if "image quality" in record.getMessage()]


@pytest.mark.parametrize(("quality", "warns"), [(LOW_LIGHT_IMAGE_QUALITY - 1, True), (LOW_LIGHT_IMAGE_QUALITY, False)])
def test_a_take_off_warns_of_low_light_under_the_image_quality_limit(
    adapter: CrazyflieAdapter, clock: SimClock, caplog: pytest.LogCaptureFixture, quality: int, warns: bool
) -> None:
    adapter._latest_image_quality = (clock.now(), quality)

    with caplog.at_level(logging.WARNING, logger=adapter_module.logger.name):
        adapter.take_off(1.0)

    assert adapter._is_in_initial_climb  # only a log line: it never refuses
    assert bool(low_light_warnings(caplog)) == warns


def test_a_take_off_with_no_recent_image_quality_warns_it_is_unknown(
    adapter: CrazyflieAdapter, clock: SimClock, caplog: pytest.LogCaptureFixture
) -> None:
    adapter._latest_image_quality = (clock.now() - 1.0, 100)

    with caplog.at_level(logging.WARNING, logger=adapter_module.logger.name):
        adapter.take_off(1.0)

    assert any("unknown" in message for message in low_light_warnings(caplog))


def reset_writes(fake_link: MagicMock) -> int:
    return sum(1 for call in fake_link.cf.param.set_value.call_args_list if call.args == ("kalman.resetEstimation", 1))


def test_an_estimate_reset_on_the_floor_writes_the_reset_parameter(
    adapter: CrazyflieAdapter, fake_link: MagicMock
) -> None:
    adapter.reset_estimate()

    assert reset_writes(fake_link) == 1


def test_an_estimate_reset_with_the_link_closed_logs_only_that_it_wasnt_sent(
    adapter: CrazyflieAdapter, fake_link: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    fake_link.cf.link = None

    with caplog.at_level(logging.INFO, logger=adapter_module.logger.name):
        adapter.reset_estimate()

    assert reset_writes(fake_link) == 0
    assert [record.getMessage() for record in caplog.records if "Estimate reset" in record.getMessage()] == [
        "Estimate reset not sent: the link is closed."
    ]


@pytest.mark.parametrize("error", [KeyError, AttributeError])
def test_an_estimate_reset_that_loses_the_link_as_it_writes_warns_that_it_wasnt_sent(
    adapter: CrazyflieAdapter, fake_link: MagicMock, caplog: pytest.LogCaptureFixture, error: type[Exception]
) -> None:
    def lose_the_link(*_: object) -> None:
        fake_link.cf.link = None  # cflib closes the link, then forgets the parameter list
        raise error

    fake_link.cf.param.set_value.side_effect = lose_the_link

    with caplog.at_level(logging.WARNING, logger=adapter_module.logger.name):
        adapter.reset_estimate()

    assert caplog.messages == ["Estimate reset not sent: the link is closed."]


def test_an_estimate_reset_while_the_drone_may_be_flying_is_ignored_and_warned_once_per_streak(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    adapter._telemetry.write_drone_status(ON_THE_FLOOR, None)  # the status still says not flying
    adapter.take_off(1.0)

    with caplog.at_level(logging.WARNING, logger=adapter_module.logger.name):
        adapter.reset_estimate()
        adapter.reset_estimate()

    assert reset_writes(fake_link) == 0
    assert sum("Estimate reset ignored" in record.getMessage() for record in caplog.records) == 1


# --- A set initial climb speed (ADR-0059) -------------------------------------------

FAST_CLIMB = 0.4
"""Meters per second: the fastest initial climb accepted."""


@pytest.fixture
def fast_climb_adapter(clock: SimClock, fake_link: MagicMock) -> CrazyflieAdapter:
    """A connected adapter on the floor, set to climb at FAST_CLIMB."""
    adapter = CrazyflieAdapter(clock, initial_climb_speed=FAST_CLIMB)
    adapter._sync_crazyflie = fake_link
    return adapter


def test_a_set_initial_climb_speed_is_the_speed_of_every_climb_setpoint(
    fast_climb_adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    fast_climb_adapter.take_off(1.0)
    climb_tick(fast_climb_adapter, clock, 0.02)
    climb_tick(fast_climb_adapter, clock, 0.04)

    assert level_setpoints(fake_link) == [pytest.approx(FAST_CLIMB)] * 3


def test_a_faster_climb_lands_at_its_shorter_time_limit_and_descends_at_the_final_descent_speed(
    fast_climb_adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    fast_climb_adapter.take_off(1.0)
    take_off_sent_at = clock.now()

    climb_until_it_lands(fast_climb_adapter, fake_link, lambda _: climb_tick(fast_climb_adapter, clock, 0.08))

    assert clock.now() - take_off_sent_at == pytest.approx(initial_climb_time_limit(FAST_CLIMB))
    assert level_setpoints(fake_link)[-1] == pytest.approx(-LEVEL_VERTICAL_SPEED)


def test_an_initial_climb_speed_outside_the_range_is_refused_before_connecting(clock: SimClock) -> None:
    with pytest.raises(ValueError, match="initial climb speed"):
        CrazyflieAdapter(clock, initial_climb_speed=0.5)


def test_the_initial_climb_logs_its_speed(
    fast_climb_adapter: CrazyflieAdapter, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO, logger=adapter_module.logger.name):
        fast_climb_adapter.take_off(1.0)

    assert "Initial climb at 0.4 m/s." in caplog.text
