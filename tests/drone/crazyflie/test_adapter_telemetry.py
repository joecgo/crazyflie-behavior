"""The Crazyflie adapter's telemetry callbacks (ADR-0021), without a drone.

Log callbacks only convert and write to the telemetry buffer, so they can be
called directly with the data cflib would deliver.
"""

# The callbacks are private; the tests call them as cflib would.
# pyright: reportPrivateUsage=false

import logging
import math
from unittest.mock import MagicMock

import pytest

from crazyflie_behavior.drone.crazyflie.adapter import _DIAGNOSTIC_VARIABLES, _STATE_VARIABLES, CrazyflieAdapter
from crazyflie_behavior.geometry import Vector3
from crazyflie_behavior.snapshot import DroneStatus, RangeReading, Snapshot
from crazyflie_behavior.timing.clock import SimClock

# Supervisor bit positions, from cflib.crazyflie.supervisor.
ARMED = 1 << 1
FLYING = 1 << 4

LOG_BLOCK_LIMIT_BYTES = 26  # cflib's LogConfig.MAX_LEN

VARIABLE_SIZES_BYTES = {
    "stateEstimate.x": 4,
    "stateEstimate.y": 4,
    "stateEstimate.z": 4,
    "stateEstimate.vx": 4,
    "stateEstimate.vy": 4,
    "stateEstimate.vz": 4,
    "supervisor.info": 2,
    "stateEstimate.roll": 4,
    "stateEstimate.pitch": 4,
    "stateEstimate.yaw": 4,
    "motor.m1": 2,
    "motor.m2": 2,
    "motor.m3": 2,
    "motor.m4": 2,
    "motion.squal": 1,
    "motion.shutter": 2,
    "pm.vbatMV": 2,
}
"""Sizes as the firmware 2026.08 stores them (ADR-0047)."""

STATE_SAMPLE = {
    "stateEstimate.x": 1.0,
    "stateEstimate.y": 2.0,
    "stateEstimate.z": 0.5,
    "stateEstimate.vx": 0.1,
    "stateEstimate.vy": -0.2,
    "stateEstimate.vz": 0.0,
    "supervisor.info": float(ARMED | FLYING),
}


ADAPTER_LOGGER = "crazyflie_behavior.drone.crazyflie.adapter"


@pytest.fixture
def clock() -> SimClock:
    return SimClock(start=10.0)


@pytest.fixture
def adapter(clock: SimClock) -> CrazyflieAdapter:
    return CrazyflieAdapter(clock)


def snapshot_of(adapter: CrazyflieAdapter) -> Snapshot:
    return adapter._telemetry.snapshot(0.05)


def test_the_state_block_writes_position_velocity_and_status(adapter: CrazyflieAdapter) -> None:
    adapter._on_state(1500, STATE_SAMPLE, MagicMock())

    snapshot = snapshot_of(adapter)

    assert snapshot.position_estimate is not None
    assert snapshot.position_estimate.value == Vector3(1.0, 2.0, 0.5)
    assert snapshot.velocity_estimate is not None
    assert snapshot.velocity_estimate.value == Vector3(0.1, -0.2, 0.0)
    assert snapshot.drone_status is not None
    assert snapshot.drone_status.value == DroneStatus(is_armed=True, is_flying=True, is_crashed=False, is_tumbled=False)


def test_position_velocity_and_status_share_one_drone_time(adapter: CrazyflieAdapter) -> None:
    adapter._on_state(1500, STATE_SAMPLE, MagicMock())

    snapshot = snapshot_of(adapter)

    assert snapshot.position_estimate is not None
    assert snapshot.velocity_estimate is not None
    assert snapshot.drone_status is not None
    assert snapshot.position_estimate.drone_time == 1.5
    assert snapshot.velocity_estimate.drone_time == 1.5
    assert snapshot.drone_status.drone_time == 1.5


@pytest.mark.parametrize(
    ("variable", "value"),
    [("stateEstimate.z", math.nan), ("stateEstimate.x", math.inf), ("stateEstimate.vy", -math.inf)],
)
def test_an_estimate_that_isnt_finite_is_dropped_and_the_last_finite_one_goes_stale(
    adapter: CrazyflieAdapter, clock: SimClock, variable: str, value: float
) -> None:
    adapter._on_state(1500, STATE_SAMPLE, MagicMock())
    clock.advance(1.0)

    adapter._on_state(2500, {**STATE_SAMPLE, variable: value, "supervisor.info": float(ARMED)}, MagicMock())

    snapshot = adapter._telemetry.snapshot(0.05)
    assert snapshot.position_estimate is not None
    assert snapshot.velocity_estimate is not None
    assert snapshot.drone_status is not None
    is_velocity = variable.startswith("stateEstimate.v")
    estimate = snapshot.velocity_estimate if is_velocity else snapshot.position_estimate
    assert estimate.value.is_finite()
    assert estimate.age(clock.now()) == 1.0  # still the earlier one
    assert not snapshot.drone_status.value.is_flying  # the status in the same packet still arrives


def test_dropped_estimates_are_warned_once_per_streak(
    adapter: CrazyflieAdapter, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO, logger=ADAPTER_LOGGER)
    nan_sample = {**STATE_SAMPLE, "stateEstimate.z": math.nan}

    for timestamp in (1500, 1520, 1540):
        adapter._on_state(timestamp, nan_sample, MagicMock())
    adapter._on_state(1560, STATE_SAMPLE, MagicMock())
    adapter._on_state(1580, nan_sample, MagicMock())  # a new streak

    assert [record.levelno for record in caplog.records] == [logging.WARNING, logging.INFO, logging.WARNING]
    assert "isn't finite" in caplog.messages[0]
    assert caplog.messages[1] == "Finite estimates are back after 3 dropped state packets"


def test_drone_status_is_unknown_until_the_first_state_arrives(adapter: CrazyflieAdapter) -> None:
    # Unknown is None, never a made-up "all flags false".
    assert snapshot_of(adapter).drone_status is None


def test_the_state_block_fits_in_one_log_block() -> None:
    # A new variable without a size here fails this test, so the budget is
    # checked in continuous integration, not first at the bench.
    size = sum(VARIABLE_SIZES_BYTES[variable] for variable in _STATE_VARIABLES)

    assert size <= LOG_BLOCK_LIMIT_BYTES


def test_the_diagnostic_block_fits_in_one_log_block() -> None:
    size = sum(VARIABLE_SIZES_BYTES[variable] for variable in _DIAGNOSTIC_VARIABLES)

    assert size <= LOG_BLOCK_LIMIT_BYTES


def test_a_diagnostic_sample_is_one_debug_line_and_never_telemetry(
    adapter: CrazyflieAdapter, caplog: pytest.LogCaptureFixture
) -> None:
    sample = {
        "stateEstimate.roll": 1.5,
        "stateEstimate.pitch": -2.25,
        "stateEstimate.yaw": 10.0,
        "motor.m1": 40000.0,
        "motor.m2": 41000.0,
        "motor.m3": 42000.0,
        "motor.m4": 43000.0,
        "motion.squal": 90.0,
        "motion.shutter": 2500.0,
        "pm.vbatMV": 3871.0,
    }
    before = snapshot_of(adapter)

    with caplog.at_level(logging.DEBUG, logger=ADAPTER_LOGGER):
        adapter._on_diagnostic(3000, sample, MagicMock())

    assert [r.getMessage() for r in caplog.records] == [
        "Diagnostic: drone_time=3.000 roll_deg=1.50 pitch_deg=-2.25 yaw_deg=10.00 "
        "motors=[40000, 41000, 42000, 43000] squal=90 shutter=2500 battery_voltage=3.871"
    ]
    assert caplog.records[0].levelno == logging.DEBUG
    assert snapshot_of(adapter) == before


def test_the_down_range_arrives_in_meters(adapter: CrazyflieAdapter) -> None:
    adapter._on_down_range(2000, {"range.zrange": 250.0}, MagicMock())

    down = snapshot_of(adapter).range_readings.down

    assert down is not None
    assert down.value == RangeReading.at_distance(0.25)
    assert down.drone_time == 2.0


def test_each_multi_ranger_direction_reads_its_own_variable(adapter: CrazyflieAdapter) -> None:
    sample = {
        "range.front": 100.0,
        "range.back": 200.0,
        "range.left": 300.0,
        "range.right": 400.0,
        "range.up": 8000.0,
    }

    adapter._on_multiranger(2000, sample, MagicMock())
    readings = snapshot_of(adapter).range_readings

    distances = {
        "front": readings.front,
        "back": readings.back,
        "left": readings.left,
        "right": readings.right,
        "up": readings.up,
    }
    assert {name: r.value if r else None for name, r in distances.items()} == {
        "front": RangeReading.at_distance(0.1),
        "back": RangeReading.at_distance(0.2),
        "left": RangeReading.at_distance(0.3),
        "right": RangeReading.at_distance(0.4),
        "up": RangeReading.out_of_range(),
    }
