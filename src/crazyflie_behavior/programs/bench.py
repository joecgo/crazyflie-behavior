"""The bench program (ADR-0028): connect, tick, and log every snapshot. Never commands the drone.

For the Bench field test, with the propellers on (ADR-0044). It uses the mock
adapter unless it's run with --crazyflie:

    .venv\\Scripts\\python -m crazyflie_behavior.programs.bench
    .venv\\Scripts\\python -m crazyflie_behavior.programs.bench --crazyflie
    .venv\\Scripts\\python -m crazyflie_behavior.programs.bench --crazyflie --take-off-log

Each snapshot goes to the log file; the console gets a summary every second.
With --take-off-log, the take-off block runs for its time at connect, which
shows its radio load on the data ages (ADR-0063, ADR-0065).
"""

import argparse
import logging
import sys
from collections.abc import Callable

from crazyflie_behavior.drone.interface import DroneInterface
from crazyflie_behavior.loop.tick_loop import TickStep
from crazyflie_behavior.programs.start_up import (
    add_take_off_log_option,
    make_drone,
    run_program,
    take_off_log_description,
)
from crazyflie_behavior.snapshot import RangeReading, RangeStatus, Snapshot, Stamped
from crazyflie_behavior.timing.clock import RealClock

# Not __name__: run as a program, this module is called __main__, which is
# outside the project's loggers and would lose the debug lines.
logger = logging.getLogger("crazyflie_behavior.programs.bench")

SUMMARY_PERIOD = 1.0
"""Seconds between snapshot summaries on the console."""


class BenchTickStep(TickStep):
    """Takes a snapshot each tick and logs it. Never commands the drone.

    It still updates take-off and landing each tick (ADR-0055), as every tick step does.
    """

    def __init__(self, drone: DroneInterface) -> None:
        self._drone = drone
        self._next_summary_time: float | None = None

    def run(self, time: float, dt: float) -> bool:
        snapshot = self._drone.take_snapshot(dt)
        logger.debug("Snapshot: %s", snapshot)
        self._drone.update_take_off_and_landing(snapshot)
        if self._next_summary_time is None or time >= self._next_summary_time:
            logger.info("%s", snapshot_summary(snapshot))
            self._next_summary_time = time + SUMMARY_PERIOD
        return False  # runs until stopped


def snapshot_summary(snapshot: Snapshot) -> str:
    """One line describing a snapshot, with how old each value is."""
    now = snapshot.time
    parts = [
        _describe_stamped(
            "position",
            snapshot.position_estimate,
            now,
            lambda p: f"{p.x:.2f}, {p.y:.2f}, {p.z:.2f} m",
        ),
        _describe_stamped(
            "velocity",
            snapshot.velocity_estimate,
            now,
            lambda v: f"{v.x:.2f}, {v.y:.2f}, {v.z:.2f} m/s",
        ),
        _describe_stamped("velocity uncertainty", snapshot.velocity_uncertainty, now, lambda u: f"{u:.3f} m/s"),
        _describe_stamped("battery", snapshot.battery_voltage, now, lambda v: f"{v:.2f} V"),
        _describe_stamped(
            "status",
            snapshot.drone_status,
            now,
            lambda s: (
                f"armed {_yes_no(s.is_armed)}, flying {_yes_no(s.is_flying)}, "
                f"crashed {_yes_no(s.is_crashed)}, tumbled {_yes_no(s.is_tumbled)}"
            ),
        ),
    ]
    readings = snapshot.range_readings
    for name, reading in [
        ("front", readings.front),
        ("back", readings.back),
        ("left", readings.left),
        ("right", readings.right),
        ("up", readings.up),
        ("down", readings.down),
    ]:
        parts.append(_describe_stamped(name, reading, now, _describe_range))
    return " | ".join(parts)


def _describe_stamped[T](name: str, stamped: Stamped[T] | None, now: float, describe: Callable[[T], str]) -> str:
    if stamped is None:
        return f"{name} no reading yet"
    # A value can arrive a moment after the tick started; show that as 0 ms old.
    age_ms = max(0.0, stamped.age(now)) * 1000.0
    return f"{name} {describe(stamped.value)} ({age_ms:.0f} ms old)"


def _describe_range(reading: RangeReading) -> str:
    if reading.status is RangeStatus.DISTANCE and reading.distance is not None:
        return f"{reading.distance:.2f} m"
    return "out of range" if reading.status is RangeStatus.OUT_OF_RANGE else "invalid"


def _yes_no(flag: bool) -> str:
    return "yes" if flag else "no"


def main(arguments: list[str] | None = None) -> int:
    """Run the bench program until a stop request. Returns the program's exit code."""
    parser = argparse.ArgumentParser(
        prog="bench", description="Connect, tick and log every snapshot (the Bench field test)."
    )
    parser.add_argument(
        "--crazyflie",
        action="store_true",
        help="use the real Crazyflie instead of the mock adapter",
    )
    add_take_off_log_option(parser)
    parsed_arguments = parser.parse_args(arguments)
    use_crazyflie: bool = parsed_arguments.crazyflie
    take_off_log: bool = parsed_arguments.take_off_log
    clock = RealClock()
    drone = make_drone(use_crazyflie, clock, take_off_log=take_off_log)
    adapter_name = "the Crazyflie" if use_crazyflie else "the mock adapter"
    description = f"Bench program, {adapter_name}"
    if take_off_log:
        description += take_off_log_description(use_crazyflie)
    return run_program("bench", description, drone, BenchTickStep(drone), clock)


if __name__ == "__main__":
    sys.exit(main())
