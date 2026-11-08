from crazyflie_behavior.drone.crazyflie.adapter import drone_status_from_bitfield
from crazyflie_behavior.snapshot import DroneStatus

# Supervisor bit positions, from cflib.crazyflie.supervisor.
CAN_BE_ARMED = 1 << 0
ARMED = 1 << 1
FLYING = 1 << 4
TUMBLED = 1 << 5
LOCKED = 1 << 6
CRASHED = 1 << 7


def test_an_empty_bitfield_means_nothing_is_set() -> None:
    assert drone_status_from_bitfield(0) == DroneStatus(
        is_armed=False, is_flying=False, is_crashed=False, is_tumbled=False, can_arm=False, is_locked=False
    )


def test_each_status_flag_reads_its_own_bit() -> None:
    assert drone_status_from_bitfield(ARMED | FLYING) == DroneStatus(
        is_armed=True, is_flying=True, is_crashed=False, is_tumbled=False, can_arm=False, is_locked=False
    )
    assert drone_status_from_bitfield(TUMBLED | CRASHED) == DroneStatus(
        is_armed=False, is_flying=False, is_crashed=True, is_tumbled=True, can_arm=False, is_locked=False
    )
    assert drone_status_from_bitfield(CAN_BE_ARMED | LOCKED) == DroneStatus(
        is_armed=False, is_flying=False, is_crashed=False, is_tumbled=False, can_arm=True, is_locked=True
    )
