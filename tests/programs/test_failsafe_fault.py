"""The forged low battery wrapper (ADR-0041), around a stand-in drone."""

import logging
from dataclasses import replace

import pytest

from crazyflie_behavior.behaviors.failsafe_test import FAULT_TIME_LIMIT
from crazyflie_behavior.drone.interface import DroneInterface
from crazyflie_behavior.geometry import Vector3
from crazyflie_behavior.programs.failsafe_fault import (
    FORGED_BATTERY_VOLTAGE,
    HOVER_DURATION_BEFORE_FAULT,
    ForgedLowBatteryDrone,
)
from crazyflie_behavior.safety.safety_layer import LOW_BATTERY_VOLTAGE, safety_pre_check
from crazyflie_behavior.snapshot import (
    DroneStatus,
    RangeReading,
    RangeReadings,
    Snapshot,
    Stamped,
)

HEIGHT = 0.5
FLYING = DroneStatus(is_armed=True, is_flying=True, is_crashed=False, is_tumbled=False)
ON_THE_FLOOR = replace(FLYING, is_flying=False)


class StandInDrone(DroneInterface):
    """Records the commands it gets and returns whatever snapshot it was told to."""

    def __init__(self) -> None:
        self.calls: list[str] = []
        self.status = FLYING
        self.height = HEIGHT
        self.battery_voltage: Stamped[float] | None = Stamped(3.9, arrival_time=0.0, drone_time=None)

    def connect(self) -> None:
        self.calls.append("connect")

    def disconnect(self) -> None:
        self.calls.append("disconnect")

    def arm(self) -> None:
        self.calls.append("arm")

    def disarm(self) -> None:
        self.calls.append("disarm")

    def take_off(self, height: float) -> None:
        self.calls.append(f"take_off {height}")

    def land(self) -> None:
        self.calls.append("land")

    def set_velocity(self, velocity: Vector3, yaw_rate_rad_per_s: float = 0.0) -> None:
        self.calls.append(f"set_velocity {velocity} {yaw_rate_rad_per_s}")

    def move_to(self, position: Vector3, duration: float) -> None:
        self.calls.append(f"move_to {position} {duration}")

    def hover(self) -> None:
        self.calls.append("hover")

    def emergency_stop(self) -> None:
        self.calls.append("emergency_stop")

    def take_snapshot(self, time: float, dt: float) -> Snapshot:
        def fresh[T](value: T) -> Stamped[T]:
            return Stamped(value, arrival_time=time, drone_time=time)

        return Snapshot(
            time=time,
            dt=dt,
            position_estimate=fresh(Vector3(0.1, 0.2, self.height)),
            velocity_estimate=fresh(Vector3.ZERO),
            range_readings=RangeReadings(None, None, None, None, None, fresh(RangeReading.at_distance(self.height))),
            battery_voltage=None if self.battery_voltage is None else fresh(self.battery_voltage.value),
            drone_status=fresh(self.status),
        )


def forged(snapshot: Snapshot) -> bool:
    return snapshot.battery_voltage is not None and snapshot.battery_voltage.value == FORGED_BATTERY_VOLTAGE


def test_the_forged_voltage_is_below_the_safety_pre_checks_limit() -> None:
    assert FORGED_BATTERY_VOLTAGE < LOW_BATTERY_VOLTAGE


def hovered_drone() -> tuple[StandInDrone, ForgedLowBatteryDrone]:
    """A wrapped drone that took off and is hovering at the height from tick time 1.0 s."""
    stand_in = StandInDrone()
    wrapper = ForgedLowBatteryDrone(stand_in)
    wrapper.take_off(HEIGHT)
    wrapper.take_snapshot(1.0, 0.05)
    return stand_in, wrapper


def test_snapshots_are_the_real_ones_until_the_drone_has_hovered_for_the_hover_duration() -> None:
    stand_in, wrapper = hovered_drone()

    just_before = wrapper.take_snapshot(1.0 + HOVER_DURATION_BEFORE_FAULT - 0.05, 0.05)

    assert just_before == stand_in.take_snapshot(1.0 + HOVER_DURATION_BEFORE_FAULT - 0.05, 0.05)
    assert not wrapper.has_forged_battery_voltage


def test_after_the_hover_duration_the_battery_voltage_is_forged_and_nothing_else() -> None:
    stand_in, wrapper = hovered_drone()
    time = 1.0 + HOVER_DURATION_BEFORE_FAULT
    real = stand_in.take_snapshot(time, 0.05)

    snapshot = wrapper.take_snapshot(time, 0.05)

    assert wrapper.has_forged_battery_voltage
    assert snapshot.battery_voltage is not None
    assert real.battery_voltage is not None
    assert snapshot.battery_voltage.value == FORGED_BATTERY_VOLTAGE
    # The timestamps stay real, so the forged value is as fresh as the real one: only its value is a lie.
    assert snapshot.battery_voltage.arrival_time == real.battery_voltage.arrival_time
    assert replace(snapshot, battery_voltage=real.battery_voltage) == real  # every other field is real
    assert real.battery_voltage.value == 3.9  # the real snapshot isn't modified


def test_the_forged_snapshot_fails_the_real_safety_pre_check_for_the_battery_only() -> None:
    stand_in, wrapper = hovered_drone()
    time = 1.0 + HOVER_DURATION_BEFORE_FAULT

    real_failures = safety_pre_check(stand_in.take_snapshot(time, 0.05))
    forged_failures = safety_pre_check(wrapper.take_snapshot(time, 0.05))

    assert real_failures == []
    assert len(forged_failures) == 1
    assert forged_failures[0].startswith("battery at 3.20 V")


def test_it_logs_one_warning_when_the_fault_is_injected_not_one_per_snapshot(
    caplog: pytest.LogCaptureFixture,
) -> None:
    _, wrapper = hovered_drone()

    with caplog.at_level(logging.WARNING):
        for tick in range(5):
            wrapper.take_snapshot(1.0 + HOVER_DURATION_BEFORE_FAULT + tick * 0.05, 0.05)

    assert [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING] == [
        "FAULT INJECTED: battery voltage forged"
    ]


def test_the_battery_stays_forged_in_every_later_snapshot() -> None:
    _, wrapper = hovered_drone()

    snapshots = [wrapper.take_snapshot(1.0 + HOVER_DURATION_BEFORE_FAULT + tick * 0.05, 0.05) for tick in range(3)]

    assert all(forged(snapshot) for snapshot in snapshots)


def test_nothing_is_forged_before_a_take_off() -> None:
    wrapper = ForgedLowBatteryDrone(StandInDrone())

    snapshot = wrapper.take_snapshot(100.0, 0.05)

    assert not forged(snapshot)


def test_the_hover_is_counted_from_reaching_the_height_not_from_the_take_off() -> None:
    stand_in = StandInDrone()
    wrapper = ForgedLowBatteryDrone(stand_in)
    wrapper.take_off(HEIGHT)
    stand_in.height = 0.2  # still climbing
    wrapper.take_snapshot(1.0, 0.05)
    wrapper.take_snapshot(1.0 + HOVER_DURATION_BEFORE_FAULT, 0.05)
    stand_in.height = HEIGHT  # arrives at 10 s
    wrapper.take_snapshot(10.0, 0.05)

    still_real = wrapper.take_snapshot(10.0 + HOVER_DURATION_BEFORE_FAULT - 0.05, 0.05)
    forged_now = wrapper.take_snapshot(10.0 + HOVER_DURATION_BEFORE_FAULT, 0.05)

    assert not forged(still_real)
    assert forged(forged_now)


def test_a_drone_the_status_says_is_on_the_floor_is_not_hovering() -> None:
    stand_in = StandInDrone()
    stand_in.status = ON_THE_FLOOR
    wrapper = ForgedLowBatteryDrone(stand_in)
    wrapper.take_off(HEIGHT)

    snapshots = [wrapper.take_snapshot(tick * 1.0, 0.05) for tick in range(10)]

    assert not any(forged(snapshot) for snapshot in snapshots)


def test_the_hover_duration_can_be_set() -> None:
    stand_in = StandInDrone()
    wrapper = ForgedLowBatteryDrone(stand_in, hover_duration_before_fault=0.5)
    wrapper.take_off(HEIGHT)
    wrapper.take_snapshot(1.0, 0.05)

    assert not forged(wrapper.take_snapshot(1.45, 0.05))
    assert forged(wrapper.take_snapshot(1.5, 0.05))


def test_a_missing_battery_voltage_is_left_missing_for_the_pre_check_to_fail_on() -> None:
    stand_in = StandInDrone()
    stand_in.battery_voltage = None
    wrapper = ForgedLowBatteryDrone(stand_in, hover_duration_before_fault=0.0)
    wrapper.take_off(HEIGHT)

    snapshot = wrapper.take_snapshot(1.0, 0.05)

    assert snapshot.battery_voltage is None
    assert not wrapper.has_forged_battery_voltage


def test_every_command_goes_to_the_real_drone_unchanged() -> None:
    stand_in = StandInDrone()
    wrapper = ForgedLowBatteryDrone(stand_in)

    wrapper.connect()
    wrapper.arm()
    wrapper.take_off(0.5)
    wrapper.set_velocity(Vector3(0.1, 0.0, 0.0), 0.2)
    wrapper.move_to(Vector3(1.0, 0.0, 0.5), 2.0)
    wrapper.hover()
    wrapper.land()
    wrapper.disarm()
    wrapper.emergency_stop()
    wrapper.disconnect()

    assert stand_in.calls == [
        "connect",
        "arm",
        "take_off 0.5",
        f"set_velocity {Vector3(0.1, 0.0, 0.0)} 0.2",
        f"move_to {Vector3(1.0, 0.0, 0.5)} 2.0",
        "hover",
        "land",
        "disarm",
        "emergency_stop",
        "disconnect",
    ]


def test_the_failsafe_test_waits_longer_than_the_hover_before_the_fault() -> None:
    # Otherwise the failsafe test gives up and lands before the fault is ever injected (ADR-0041).
    assert FAULT_TIME_LIMIT > HOVER_DURATION_BEFORE_FAULT
