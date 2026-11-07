"""The failsafe landing with the Crazyflie adapter, against a fake cflib connection (ADR-0039).

The safety layer decides to land from a failed pre-check alone; the adapter
decides what a landing means. Right after a take-off the drone status doesn't
show flying yet, and the landing must still go out. During the initial climb,
it goes out as the final descent, level from where the drone is (ADR-0049).
"""

# The adapter has no seam for a fake connection, so the tests set its private fields directly.
# pyright: reportPrivateUsage=false

import struct
from unittest.mock import MagicMock

import pytest

from crazyflie_behavior.drone.crazyflie.adapter import TAKE_OFF_STATUS_GRACE, CrazyflieAdapter
from crazyflie_behavior.drone.crazyflie.bad_flow_zone import LEVEL_VERTICAL_SPEED
from crazyflie_behavior.geometry import Vector3
from crazyflie_behavior.safety.safety_layer import LOW_BATTERY_VOLTAGE, SafetyLayer
from crazyflie_behavior.snapshot import DroneStatus, RangeDirection, RangeReading
from crazyflie_behavior.timing.clock import SimClock

ON_THE_FLOOR = DroneStatus(is_armed=True, is_flying=False, is_crashed=False, is_tumbled=False)
FLYING = DroneStatus(is_armed=True, is_flying=True, is_crashed=False, is_tumbled=False)
TICK = 0.05


def adapter_after_a_take_off(clock: SimClock, fake_link: MagicMock) -> CrazyflieAdapter:
    adapter = CrazyflieAdapter(clock)
    adapter._sync_crazyflie = fake_link
    adapter.take_off(0.5)
    return adapter


def report_everything(adapter: CrazyflieAdapter, status: DroneStatus, battery_voltage: float) -> None:
    telemetry = adapter._telemetry
    telemetry.write_estimates_and_status(Vector3(0.0, 0.0, 0.3), Vector3.ZERO, status, None)
    telemetry.write_range_readings({RangeDirection.DOWN: RangeReading.at_distance(0.3)}, None)
    telemetry.write_battery_voltage(battery_voltage, None)


def level_setpoints(fake_link: MagicMock) -> list[float]:
    """The vertical speed of each level setpoint sent, in order (meters per second, up)."""
    return [struct.unpack("<Bffff", call.args[0].data)[4] for call in fake_link.cf.send_packet.call_args_list]


def fail_the_pre_check_and_send(adapter: CrazyflieAdapter, clock: SimClock) -> SafetyLayer:
    safety_layer = SafetyLayer(adapter)
    clock.advance(TICK)
    safety_layer.pre_check(adapter.take_snapshot(TICK))
    safety_layer.send()
    return safety_layer


def test_the_failsafe_lands_during_the_take_off_grace_period_though_the_status_says_on_the_floor() -> None:
    clock = SimClock(start=10.0)
    fake_link = MagicMock()
    adapter = adapter_after_a_take_off(clock, fake_link)
    report_everything(adapter, ON_THE_FLOOR, battery_voltage=LOW_BATTERY_VOLTAGE - 0.1)

    safety_layer = fail_the_pre_check_and_send(adapter, clock)

    assert safety_layer.pre_check_has_failed
    # The climb's setpoint, then the final descent's.
    assert level_setpoints(fake_link) == [pytest.approx(LEVEL_VERTICAL_SPEED), pytest.approx(-LEVEL_VERTICAL_SPEED)]
    fake_link.cf.high_level_commander.stop.assert_not_called()  # the motors keep running until touchdown


def test_the_failsafe_on_a_drone_that_never_flew_just_stops_the_motors() -> None:
    clock = SimClock(start=10.0)
    fake_link = MagicMock()
    adapter = adapter_after_a_take_off(clock, fake_link)
    clock.advance(TAKE_OFF_STATUS_GRACE + 1.0)  # the take-off never took effect
    report_everything(adapter, ON_THE_FLOOR, battery_voltage=LOW_BATTERY_VOLTAGE - 0.1)

    fail_the_pre_check_and_send(adapter, clock)

    fake_link.cf.high_level_commander.go_to.assert_not_called()
    fake_link.cf.high_level_commander.stop.assert_called_once()


def test_the_failsafe_lands_a_flying_drone() -> None:
    clock = SimClock(start=10.0)
    fake_link = MagicMock()
    adapter = adapter_after_a_take_off(clock, fake_link)
    clock.advance(TAKE_OFF_STATUS_GRACE + 1.0)
    report_everything(adapter, FLYING, battery_voltage=LOW_BATTERY_VOLTAGE - 0.1)

    fail_the_pre_check_and_send(adapter, clock)

    assert level_setpoints(fake_link)[-1] == pytest.approx(-LEVEL_VERTICAL_SPEED)  # the final descent
    fake_link.cf.high_level_commander.stop.assert_not_called()
