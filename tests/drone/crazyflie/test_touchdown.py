from crazyflie_behavior.drone.crazyflie.touchdown import touchdown_confirmed
from crazyflie_behavior.geometry import Vector3
from crazyflie_behavior.snapshot import RangeReading, RangeReadings, Snapshot, Stamped

NOW = 100.0
FRESH = NOW - 0.05
STALE = NOW - 5.0


def snapshot_with(
    down: RangeReading | None = None,
    down_arrived: float = FRESH,
    height: float | None = None,
    height_arrived: float = FRESH,
) -> Snapshot:
    return Snapshot(
        time=NOW,
        dt=0.05,
        position_estimate=(
            None if height is None else Stamped(Vector3(0.0, 0.0, height), height_arrived, None)
        ),
        velocity_estimate=None,
        range_readings=RangeReadings(
            front=None,
            back=None,
            left=None,
            right=None,
            up=None,
            down=None if down is None else Stamped(down, down_arrived, None),
        ),
        battery_voltage=None,
        drone_status=None,
    )


def test_a_short_down_range_confirms_touchdown() -> None:
    assert touchdown_confirmed(snapshot_with(down=RangeReading.at_distance(0.02)), NOW)


def test_the_down_range_wins_over_a_drifted_height_estimate() -> None:
    # The case that matters most: the estimate claims the ground, but the
    # sensor still sees 60 cm below. The drone is in the air.
    snapshot = snapshot_with(down=RangeReading.at_distance(0.6), height=0.0)

    assert not touchdown_confirmed(snapshot, NOW)


def test_nothing_in_range_below_means_still_in_the_air() -> None:
    snapshot = snapshot_with(down=RangeReading.out_of_range(), height=0.0)

    assert not touchdown_confirmed(snapshot, NOW)


def test_the_height_estimate_stands_in_when_the_down_range_is_invalid() -> None:
    snapshot = snapshot_with(down=RangeReading.invalid(), height=0.03)

    assert touchdown_confirmed(snapshot, NOW)


def test_a_stale_down_range_does_not_count() -> None:
    snapshot = snapshot_with(down=RangeReading.at_distance(0.02), down_arrived=STALE, height=0.8)

    assert not touchdown_confirmed(snapshot, NOW)


def test_a_stale_height_estimate_does_not_count_either() -> None:
    snapshot = snapshot_with(height=0.0, height_arrived=STALE)

    assert not touchdown_confirmed(snapshot, NOW)


def test_no_telemetry_means_no_confirmation() -> None:
    assert not touchdown_confirmed(snapshot_with(), NOW)
