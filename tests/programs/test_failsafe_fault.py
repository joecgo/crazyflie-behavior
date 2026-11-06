"""The forged low battery wrapper (ADR-0041, ADR-0049), around a stand-in drone."""

import logging
from dataclasses import replace

import pytest

from crazyflie_behavior.behaviors.failsafe_test import HOVER_TIME_LIMIT
from crazyflie_behavior.drone.interface import DroneInterface
from crazyflie_behavior.geometry import Vector3
from crazyflie_behavior.programs.failsafe_fault import (
    CLIMB_FAULT_DOWN_RANGE,
    CLIMB_FAULT_READINGS,
    FORGED_BATTERY_VOLTAGE,
    HOVER_DURATION_BEFORE_FAULT,
    FaultTrigger,
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
        self.time = 0.0
        """The time its next snapshot is taken at, as if read from a clock."""
        self.status = FLYING
        self.height = HEIGHT
        self.battery_voltage: Stamped[float] | None = Stamped(3.9, arrival_time=0.0, drone_time=None)
        self.down: RangeReading | None = None
        """The down range reading; None means a distance equal to the height."""
        self.down_arrival_time: float | None = None
        """When the down range reading arrived; None means at the snapshot's time (a new reading each time)."""

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

    def chirp(self) -> None:
        self.calls.append("chirp")

    def play_tone(self, pitch: float) -> None:
        self.calls.append(f"play_tone {pitch}")

    def silence(self) -> None:
        self.calls.append("silence")

    def take_snapshot(self, dt: float) -> Snapshot:
        time = self.time

        def fresh[T](value: T) -> Stamped[T]:
            return Stamped(value, arrival_time=time, drone_time=time)

        return Snapshot(
            time=time,
            dt=dt,
            position_estimate=fresh(Vector3(0.1, 0.2, self.height)),
            velocity_estimate=fresh(Vector3.ZERO),
            range_readings=RangeReadings(None, None, None, None, None, self._down_reading(time)),
            battery_voltage=None if self.battery_voltage is None else fresh(self.battery_voltage.value),
            drone_status=fresh(self.status),
        )

    def _down_reading(self, time: float) -> Stamped[RangeReading]:
        reading = RangeReading.at_distance(self.height) if self.down is None else self.down
        arrival_time = time if self.down_arrival_time is None else self.down_arrival_time
        return Stamped(reading, arrival_time=arrival_time, drone_time=arrival_time)


def snapshot_at(time: float, stand_in: StandInDrone, drone: DroneInterface | None = None) -> Snapshot:
    """The snapshot `drone` (the stand-in itself if None) returns when the stand-in's clock reads `time`."""
    stand_in.time = time
    return (drone if drone is not None else stand_in).take_snapshot(0.05)


def forged(snapshot: Snapshot) -> bool:
    return snapshot.battery_voltage is not None and snapshot.battery_voltage.value == FORGED_BATTERY_VOLTAGE


def test_the_forged_voltage_is_below_the_safety_pre_checks_limit() -> None:
    assert FORGED_BATTERY_VOLTAGE < LOW_BATTERY_VOLTAGE


def hovered_drone() -> tuple[StandInDrone, ForgedLowBatteryDrone]:
    """A wrapped drone that took off and is hovering at the height from tick time 1.0 s."""
    stand_in = StandInDrone()
    wrapper = ForgedLowBatteryDrone(stand_in)
    wrapper.take_off(HEIGHT)
    snapshot_at(1.0, stand_in, wrapper)
    return stand_in, wrapper


def test_snapshots_are_the_real_ones_until_the_drone_has_hovered_for_the_hover_duration() -> None:
    stand_in, wrapper = hovered_drone()

    just_before = snapshot_at(1.0 + HOVER_DURATION_BEFORE_FAULT - 0.05, stand_in, wrapper)

    assert just_before == snapshot_at(1.0 + HOVER_DURATION_BEFORE_FAULT - 0.05, stand_in)
    assert not wrapper.has_forged_battery_voltage


def test_after_the_hover_duration_the_battery_voltage_is_forged_and_nothing_else() -> None:
    stand_in, wrapper = hovered_drone()
    time = 1.0 + HOVER_DURATION_BEFORE_FAULT
    real = snapshot_at(time, stand_in)

    snapshot = snapshot_at(time, stand_in, wrapper)

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

    real_failures = safety_pre_check(snapshot_at(time, stand_in))
    forged_failures = safety_pre_check(snapshot_at(time, stand_in, wrapper))

    assert real_failures == []
    assert len(forged_failures) == 1
    assert forged_failures[0].startswith("battery at 3.00 V")


def test_it_logs_one_warning_when_the_fault_is_injected_not_one_per_snapshot(
    caplog: pytest.LogCaptureFixture,
) -> None:
    stand_in, wrapper = hovered_drone()

    with caplog.at_level(logging.WARNING):
        for tick in range(5):
            snapshot_at(1.0 + HOVER_DURATION_BEFORE_FAULT + tick * 0.05, stand_in, wrapper)

    assert [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING] == [
        "FAULT INJECTED: battery voltage forged"
    ]


def test_the_battery_stays_forged_in_every_later_snapshot() -> None:
    stand_in, wrapper = hovered_drone()

    snapshots = [snapshot_at(1.0 + HOVER_DURATION_BEFORE_FAULT + tick * 0.05, stand_in, wrapper) for tick in range(3)]

    assert all(forged(snapshot) for snapshot in snapshots)


def test_nothing_is_forged_before_a_take_off() -> None:
    stand_in = StandInDrone()
    wrapper = ForgedLowBatteryDrone(stand_in)

    snapshot = snapshot_at(100.0, stand_in, wrapper)

    assert not forged(snapshot)


def test_the_hover_is_counted_from_reaching_the_height_not_from_the_take_off() -> None:
    stand_in = StandInDrone()
    wrapper = ForgedLowBatteryDrone(stand_in)
    wrapper.take_off(HEIGHT)
    stand_in.height = 0.2  # still climbing
    snapshot_at(1.0, stand_in, wrapper)
    snapshot_at(1.0 + HOVER_DURATION_BEFORE_FAULT, stand_in, wrapper)
    stand_in.height = HEIGHT  # arrives at 10 s
    snapshot_at(10.0, stand_in, wrapper)

    still_real = snapshot_at(10.0 + HOVER_DURATION_BEFORE_FAULT - 0.05, stand_in, wrapper)
    forged_now = snapshot_at(10.0 + HOVER_DURATION_BEFORE_FAULT, stand_in, wrapper)

    assert not forged(still_real)
    assert forged(forged_now)


def test_a_drone_the_status_says_is_on_the_floor_is_not_hovering() -> None:
    stand_in = StandInDrone()
    stand_in.status = ON_THE_FLOOR
    wrapper = ForgedLowBatteryDrone(stand_in)
    wrapper.take_off(HEIGHT)

    snapshots = [snapshot_at(tick * 1.0, stand_in, wrapper) for tick in range(10)]

    assert not any(forged(snapshot) for snapshot in snapshots)


def test_the_hover_duration_can_be_set() -> None:
    stand_in = StandInDrone()
    wrapper = ForgedLowBatteryDrone(stand_in, hover_duration_before_fault=0.5)
    wrapper.take_off(HEIGHT)
    snapshot_at(1.0, stand_in, wrapper)

    assert not forged(snapshot_at(1.45, stand_in, wrapper))
    assert forged(snapshot_at(1.5, stand_in, wrapper))


def test_a_missing_battery_voltage_is_left_missing_for_the_pre_check_to_fail_on() -> None:
    stand_in = StandInDrone()
    stand_in.battery_voltage = None
    wrapper = ForgedLowBatteryDrone(stand_in, hover_duration_before_fault=0.0)
    wrapper.take_off(HEIGHT)

    snapshot = snapshot_at(1.0, stand_in, wrapper)

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
    wrapper.chirp()
    wrapper.play_tone(523.25)
    wrapper.silence()
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
        "chirp",
        "play_tone 523.25",
        "silence",
        "disconnect",
    ]


def test_the_failsafe_test_waits_longer_than_the_hover_before_the_fault() -> None:
    # Otherwise the failsafe test gives up and lands before the fault is ever injected (ADR-0041).
    assert HOVER_TIME_LIMIT > HOVER_DURATION_BEFORE_FAULT


# --- The climb trigger (Failsafe low, ADR-0049) ---------------------------------------


def climbing_drone(height: float = 0.05) -> tuple[StandInDrone, ForgedLowBatteryDrone]:
    """A wrapped drone with the climb trigger, a take-off sent, flying at `height` (meters)."""
    stand_in = StandInDrone()
    stand_in.height = height
    wrapper = ForgedLowBatteryDrone(stand_in, FaultTrigger.CLIMB)
    wrapper.take_off(HEIGHT)
    return stand_in, wrapper


def test_the_climb_trigger_forges_once_the_down_range_has_cleared_the_floor_for_the_readings_in_a_row() -> None:
    stand_in, wrapper = climbing_drone()
    snapshot_at(1.0, stand_in, wrapper)
    stand_in.height = CLIMB_FAULT_DOWN_RANGE

    in_a_row = [snapshot_at(1.0 + tick * 0.05, stand_in, wrapper) for tick in range(1, CLIMB_FAULT_READINGS + 1)]

    assert not any(forged(snapshot) for snapshot in in_a_row[:-1])
    assert forged(in_a_row[-1])
    assert wrapper.has_forged_battery_voltage


def test_the_climb_trigger_does_not_wait_for_the_take_off_height_or_a_hover() -> None:
    stand_in, wrapper = climbing_drone(height=0.12)  # far below the 0.5 m take-off height

    snapshots = [snapshot_at(1.0 + tick * 0.05, stand_in, wrapper) for tick in range(CLIMB_FAULT_READINGS)]

    assert forged(snapshots[-1])


def test_one_reading_below_the_floor_limit_starts_the_count_again() -> None:
    stand_in, wrapper = climbing_drone(height=0.2)
    snapshot_at(1.0, stand_in, wrapper)
    stand_in.height = CLIMB_FAULT_DOWN_RANGE - 0.01  # one low reading breaks the run
    snapshot_at(1.05, stand_in, wrapper)
    stand_in.height = 0.2

    snapshots = [snapshot_at(1.05 + tick * 0.05, stand_in, wrapper) for tick in range(1, CLIMB_FAULT_READINGS + 1)]

    assert not any(forged(snapshot) for snapshot in snapshots[:-1])
    assert forged(snapshots[-1])


def test_a_reading_repeated_in_later_snapshots_counts_once() -> None:
    """A late reading can show up in two snapshots: it is still one sample."""
    stand_in, wrapper = climbing_drone(height=0.2)
    stand_in.down_arrival_time = 1.0

    snapshots = [snapshot_at(1.0 + tick * 0.05, stand_in, wrapper) for tick in range(5)]

    assert not any(forged(snapshot) for snapshot in snapshots)


@pytest.mark.parametrize(
    "down",
    [RangeReading.out_of_range(), RangeReading.invalid(), RangeReading.at_distance(CLIMB_FAULT_DOWN_RANGE - 0.001)],
    ids=["out of range", "invalid", "just below the limit"],
)
def test_a_down_range_that_isnt_clear_of_the_floor_never_fires_it(down: RangeReading) -> None:
    stand_in, wrapper = climbing_drone(height=0.2)
    stand_in.down = down

    snapshots = [snapshot_at(1.0 + tick * 0.05, stand_in, wrapper) for tick in range(10)]

    assert not any(forged(snapshot) for snapshot in snapshots)


def test_the_climb_trigger_needs_a_take_off_sent() -> None:
    stand_in = StandInDrone()
    stand_in.height = 0.2
    wrapper = ForgedLowBatteryDrone(stand_in, FaultTrigger.CLIMB)

    snapshots = [snapshot_at(1.0 + tick * 0.05, stand_in, wrapper) for tick in range(10)]

    assert not any(forged(snapshot) for snapshot in snapshots)


def test_the_climb_trigger_needs_the_status_to_say_flying() -> None:
    stand_in, wrapper = climbing_drone(height=0.2)
    stand_in.status = ON_THE_FLOOR

    snapshots = [snapshot_at(1.0 + tick * 0.05, stand_in, wrapper) for tick in range(10)]

    assert not any(forged(snapshot) for snapshot in snapshots)


def test_once_the_climb_trigger_fires_the_battery_stays_forged_even_back_near_the_floor() -> None:
    """The landing comes back down through 0.10 m: the trigger must not let the real battery back in."""
    stand_in, wrapper = climbing_drone(height=0.2)
    for tick in range(CLIMB_FAULT_READINGS):
        snapshot_at(1.0 + tick * 0.05, stand_in, wrapper)
    stand_in.height = 0.02

    later = snapshot_at(2.0, stand_in, wrapper)

    assert forged(later)


def test_the_hover_trigger_ignores_the_down_range_while_climbing() -> None:
    stand_in = StandInDrone()
    stand_in.height = 0.2  # clear of the floor, below the take-off height
    wrapper = ForgedLowBatteryDrone(stand_in, FaultTrigger.HOVER)
    wrapper.take_off(HEIGHT)

    snapshots = [snapshot_at(1.0 + tick * 0.05, stand_in, wrapper) for tick in range(10)]

    assert not any(forged(snapshot) for snapshot in snapshots)


def test_the_climb_trigger_needs_more_than_one_reading() -> None:
    # One reading is one possibly bad sample (ADR-0049).
    assert CLIMB_FAULT_READINGS >= 2
