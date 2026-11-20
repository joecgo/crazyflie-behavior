"""The Crazyflie adapter's take-off: the initial climb through the bad-flow zone (ADR-0048, ADR-0049, ADR-0056,
ADR-0077).

Against a fake cflib: each test checks what the adapter would send to a real drone.
"""

# The adapter has no seam for a fake connection, so the tests set its private fields directly.
# pyright: reportPrivateUsage=false

import itertools
import logging
import math
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
    FINAL_DESCENT_HEIGHT,
    FINAL_DESCENT_SPEED,
    INITIAL_CLIMB_SPEED,
    INITIAL_CLIMB_TIME_LIMIT,
)
from crazyflie_behavior.drone.crazyflie.conversions import alt_hold_packet_data
from crazyflie_behavior.drone.crazyflie.touchdown import TOUCHDOWN_HOLD
from crazyflie_behavior.drone.interface import STALE_AFTER
from crazyflie_behavior.geometry import Vector3
from crazyflie_behavior.snapshot import DroneStatus, RangeDirection, RangeReading
from crazyflie_behavior.timing.clock import SimClock

TICK = 0.05
CLIMB_STEP = INITIAL_CLIMB_SPEED * TICK
"""Meters climbed per tick."""
FLYING = DroneStatus(is_armed=True, is_flying=True, is_crashed=False, is_tumbled=False, can_arm=False, is_locked=False)
ON_THE_FLOOR = DroneStatus(
    is_armed=True, is_flying=False, is_crashed=False, is_tumbled=False, can_arm=False, is_locked=False
)
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
    velocity_uncertainty: float | None = 0.01,
) -> None:
    """One tick of the initial climb: the drone reports `height`, then the adapter updates.

    `down`: the down range reading; None means a distance equal to the height.
    `velocity_uncertainty`: m/s; the default means flow is arriving. None sends none this tick.
    """
    clock.advance(TICK)
    telemetry = adapter._telemetry
    telemetry.write_estimates_and_status(
        Vector3(x, -0.25, height), Vector3(horizontal_speed, 0.0, INITIAL_CLIMB_SPEED), FLYING, None
    )
    telemetry.write_range_readings(
        {RangeDirection.DOWN: RangeReading.at_distance(height) if down is None else down}, None
    )
    if velocity_uncertainty is not None:
        telemetry.write_velocity_uncertainty(velocity_uncertainty, None)
    adapter.update_take_off_and_landing(adapter.take_snapshot(TICK))


def skip_to_a_whole_second(clock: SimClock) -> None:
    """Move the clock to the next whole second: from there, advancing by STALE_AFTER gives an exact age."""
    clock.sleep_until(math.floor(clock.now()) + 1.0)


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
    assert bytes(packet.data) == alt_hold_packet_data(INITIAL_CLIMB_SPEED)


def test_each_tick_of_the_initial_climb_sends_one_level_setpoint_up(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    adapter.take_off(1.0)

    for tick in range(1, 6):
        climb_tick(adapter, clock, tick * CLIMB_STEP)

    assert level_setpoints(fake_link) == [pytest.approx(INITIAL_CLIMB_SPEED)] * 6
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

    assert heights[-1] >= FINAL_DESCENT_HEIGHT > heights[-2]  # not before the down range reached it
    assert len(level_setpoints(fake_link)) == 1 + len(heights)  # the take-off's, then one per tick, hand-over too
    assert call_names(fake_link)[-3:] == [
        "cf.send_packet",
        "cf.high_level_commander.go_to",
        "cf.commander.send_notify_setpoint_stop",
    ]
    assert level_setpoints(fake_link)[-1] == pytest.approx(INITIAL_CLIMB_SPEED)
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


@pytest.mark.parametrize(("down", "hands_over"), [(FINAL_DESCENT_HEIGHT, True), (FINAL_DESCENT_HEIGHT - 0.001, False)])
def test_the_climb_hands_over_at_a_down_range_at_or_above_the_final_descent_height(
    adapter: CrazyflieAdapter, clock: SimClock, down: float, hands_over: bool
) -> None:
    adapter.take_off(1.0)

    climb_tick(adapter, clock, down)

    assert adapter._is_in_initial_climb is not hands_over


@pytest.mark.parametrize("down", [math.nan, math.inf], ids=["NaN", "infinite"])
def test_a_non_finite_down_range_doesnt_end_the_climb(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock, down: float
) -> None:
    adapter.take_off(1.0)

    climb_tick(adapter, clock, 0.2, down=RangeReading.at_distance(down))

    assert adapter._is_in_initial_climb
    fake_link.cf.high_level_commander.go_to.assert_not_called()


def test_the_climb_logs_the_down_range_where_it_ended(
    adapter: CrazyflieAdapter, clock: SimClock, caplog: pytest.LogCaptureFixture
) -> None:
    adapter.take_off(1.0)

    with caplog.at_level(logging.INFO, logger=adapter_module.logger.name):
        heights = climb_until_handed_over(adapter, clock)

    message = f"Initial climb done at {heights[-1]:.3f} m by the down range"
    assert [record.levelno for record in caplog.records if message in record.getMessage()] == [logging.INFO]


def test_the_initial_climb_logs_its_speed(adapter: CrazyflieAdapter, caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO, logger=adapter_module.logger.name):
        adapter.take_off(1.0)

    assert f"Initial climb at {INITIAL_CLIMB_SPEED:g} m/s." in caplog.text


def test_a_climb_that_never_reaches_the_final_descent_height_lands_level_at_its_time_limit(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    adapter.take_off(1.0)
    take_off_sent_at = clock.now()

    with caplog.at_level(logging.WARNING, logger=adapter_module.logger.name):
        climb_until_it_lands(adapter, fake_link, lambda _: climb_tick(adapter, clock, 0.08))

    assert clock.now() - take_off_sent_at == pytest.approx(INITIAL_CLIMB_TIME_LIMIT)
    assert level_setpoints(fake_link)[-1] == pytest.approx(-FINAL_DESCENT_SPEED)  # the final descent
    assert any("initial climb hasn't ended" in record.getMessage() for record in caplog.records)


def test_a_climb_without_a_usable_down_range_lands_at_its_time_limit(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    adapter.take_off(1.0)
    take_off_sent_at = clock.now()

    for tick in range(1, GIVE_UP_AFTER_TICKS):
        climb_tick(adapter, clock, tick * CLIMB_STEP, down=RangeReading.invalid())
        if not adapter._is_in_initial_climb:
            break

    assert clock.now() - take_off_sent_at == pytest.approx(INITIAL_CLIMB_TIME_LIMIT)
    # The slow high-level descent, since the down range is unusable (ADR-0019).
    assert fake_link.cf.high_level_commander.go_to.call_args.kwargs == {"relative": True, "linear": True}


def test_a_fast_speed_estimate_at_the_final_descent_height_hands_over(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    # Only the velocity uncertainty is checked there, not the speed (ADR-0077, option A).
    adapter.take_off(1.0)

    climb_tick(adapter, clock, FINAL_DESCENT_HEIGHT, horizontal_speed=1.0)

    fake_link.cf.high_level_commander.go_to.assert_called_once()


# --- Landing during the initial climb (ADR-0049) --------------------------------------


def test_land_during_the_initial_climb_starts_the_level_final_descent_from_there(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    adapter.take_off(1.0)
    for tick in range(1, 4):
        climb_tick(adapter, clock, tick * CLIMB_STEP)

    adapter.land()
    climb_tick(adapter, clock, 2 * CLIMB_STEP)

    assert level_setpoints(fake_link)[-2:] == [pytest.approx(-FINAL_DESCENT_SPEED)] * 2
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
    assert level_setpoints(fake_link) == [pytest.approx(INITIAL_CLIMB_SPEED)] * 3
    assert fake_link.cf.high_level_commander.go_to.call_args.kwargs == {"relative": True, "linear": True}


def test_land_right_after_a_take_off_lands_before_the_status_shows_flying(
    adapter: CrazyflieAdapter, fake_link: MagicMock
) -> None:
    adapter.take_off(1.0)
    adapter._telemetry.write_range_readings({RangeDirection.DOWN: RangeReading.at_distance(0.02)}, None)
    adapter._telemetry.write_drone_status(ON_THE_FLOOR, None)  # the status lags a few ticks behind

    adapter.land()

    assert level_setpoints(fake_link)[-1] == pytest.approx(-FINAL_DESCENT_SPEED)
    fake_link.cf.high_level_commander.stop.assert_not_called()


def test_land_during_a_climb_that_never_left_the_floor_just_stops_the_motors(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    adapter.take_off(1.0)
    clock.advance(TAKE_OFF_STATUS_GRACE + TICK)
    adapter._telemetry.write_drone_status(ON_THE_FLOOR, None)  # fresh, and says on the floor

    adapter.land()

    assert level_setpoints(fake_link) == [pytest.approx(INITIAL_CLIMB_SPEED)]  # only the climb's first
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
    assert level_setpoints(fake_link)[-1] == pytest.approx(INITIAL_CLIMB_SPEED)  # no final descent setpoint
    assert any("Touchdown confirmed" in record.getMessage() for record in caplog.records)


def test_shutdown_during_the_initial_climb_keeps_the_level_stream_going_every_poll(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    adapter.take_off(1.0)
    for tick in range(1, 7):  # up to 0.12 m, below the final descent height
        climb_tick(adapter, clock, tick * CLIMB_STEP)
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
    assert level_setpoints(fake_link) == [pytest.approx(INITIAL_CLIMB_SPEED)]
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


@pytest.mark.parametrize("velocity_uncertainty", [NO_FLOW, math.nan, None], ids=["high", "NaN", "missing"])
def test_a_climb_without_flow_at_the_final_descent_height_lands_there(
    adapter: CrazyflieAdapter,
    clock: SimClock,
    fake_link: MagicMock,
    caplog: pytest.LogCaptureFixture,
    velocity_uncertainty: float | None,
) -> None:
    adapter.take_off(1.0)

    with caplog.at_level(logging.WARNING, logger=adapter_module.logger.name):
        tick = climb_until_it_lands(
            adapter,
            fake_link,
            lambda tick: climb_tick(adapter, clock, tick * CLIMB_STEP, velocity_uncertainty=velocity_uncertainty),
        )

    assert tick * CLIMB_STEP >= FINAL_DESCENT_HEIGHT > (tick - 1) * CLIMB_STEP  # the first tick at or above it
    fake_link.cf.high_level_commander.go_to.assert_not_called()
    assert any("No flow at the end of the initial climb" in record.getMessage() for record in caplog.records)


def test_a_stale_velocity_uncertainty_at_the_final_descent_height_lands_there_and_logs_its_age(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    adapter.take_off(1.0)
    climb_tick(adapter, clock, 0.10)  # the last velocity uncertainty
    # Then none: each tick advances the clock first, so the next tick is one past its age limit (ADR-0081).
    for _ in range(round(STALE_AFTER / TICK)):
        climb_tick(adapter, clock, 0.10, velocity_uncertainty=None)

    with caplog.at_level(logging.WARNING, logger=adapter_module.logger.name):
        climb_tick(adapter, clock, FINAL_DESCENT_HEIGHT, velocity_uncertainty=None)

    assert level_setpoints(fake_link)[-1] == pytest.approx(-FINAL_DESCENT_SPEED)
    fake_link.cf.high_level_commander.go_to.assert_not_called()
    assert "s old at the end of the initial climb" in caplog.text
    assert "No flow" not in caplog.text


def test_a_velocity_uncertainty_at_its_age_limit_without_flow_logs_no_flow_not_its_age(
    adapter: CrazyflieAdapter, clock: SimClock, caplog: pytest.LogCaptureFixture
) -> None:
    # Still fresh at exactly its age limit (ADR-0081), so the warning is about the missing flow.
    adapter.take_off(1.0)
    skip_to_a_whole_second(clock)
    adapter._telemetry.write_velocity_uncertainty(NO_FLOW, None)
    clock.advance(STALE_AFTER)
    adapter._telemetry.write_range_readings({RangeDirection.DOWN: RangeReading.at_distance(FINAL_DESCENT_HEIGHT)}, None)

    with caplog.at_level(logging.WARNING, logger=adapter_module.logger.name):
        adapter.update_take_off_and_landing(adapter.take_snapshot(TICK))

    assert "No flow at the end of the initial climb" in caplog.text
    assert "s old at the end of the initial climb" not in caplog.text


def test_no_flow_below_the_final_descent_height_doesnt_stop_the_climb(
    adapter: CrazyflieAdapter, clock: SimClock, fake_link: MagicMock
) -> None:
    # A dark floor: flow arrives only at the final descent height (ADR-0054).
    adapter.take_off(1.0)

    for tick in range(1, GIVE_UP_AFTER_TICKS):
        height = tick * CLIMB_STEP
        climb_tick(adapter, clock, height, velocity_uncertainty=NO_FLOW if height < FINAL_DESCENT_HEIGHT else 0.01)
        if not adapter._is_in_initial_climb:
            break

    fake_link.cf.high_level_commander.go_to.assert_called_once()


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
    adapter._latest_image_quality = (clock.now() - STALE_AFTER - TICK, 100)  # one tick past its age limit (ADR-0081)

    with caplog.at_level(logging.WARNING, logger=adapter_module.logger.name):
        adapter.take_off(1.0)

    assert any("unknown" in message for message in low_light_warnings(caplog))


def test_a_take_off_with_an_image_quality_at_its_age_limit_gives_no_warning(
    adapter: CrazyflieAdapter, clock: SimClock, caplog: pytest.LogCaptureFixture
) -> None:
    # Still fresh at exactly its age limit (ADR-0081).
    skip_to_a_whole_second(clock)
    adapter._latest_image_quality = (clock.now(), LOW_LIGHT_IMAGE_QUALITY)
    clock.advance(STALE_AFTER)

    with caplog.at_level(logging.WARNING, logger=adapter_module.logger.name):
        adapter.take_off(1.0)

    assert low_light_warnings(caplog) == []


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
@pytest.mark.parametrize(
    ("loses_the_link", "cause"),
    [(True, "the link is closed"), (False, "the firmware can't write it")],
    ids=["link lost", "firmware"],
)
def test_an_estimate_reset_whose_write_fails_logs_only_that_it_wasnt_sent_and_why(
    adapter: CrazyflieAdapter,
    fake_link: MagicMock,
    caplog: pytest.LogCaptureFixture,
    error: type[Exception],
    loses_the_link: bool,
    cause: str,
) -> None:
    def fail(*_: object) -> None:
        if loses_the_link:
            fake_link.cf.link = None  # cflib closes the link, then forgets the parameter list
        raise error

    fake_link.cf.param.set_value.side_effect = fail

    with caplog.at_level(logging.INFO, logger=adapter_module.logger.name):
        adapter.reset_estimate()

    assert caplog.messages == [f"Estimate reset not sent: {cause}."]


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
