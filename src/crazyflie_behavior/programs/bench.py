"""The bench program (ADR-0028): connect, tick, and log every snapshot. Never commands the drone.

For field-test stage 0, propellers off. It uses the mock adapter unless it's
run with --crazyflie:

    .venv\\Scripts\\python -m crazyflie_behavior.programs.bench
    .venv\\Scripts\\python -m crazyflie_behavior.programs.bench --crazyflie

Each snapshot goes to the log file; the console gets a summary every second.
"""

import argparse
import logging
import sys
from collections.abc import Callable

from crazyflie_behavior.drone.crazyflie.adapter import CrazyflieAdapter
from crazyflie_behavior.drone.interface import DroneInterface
from crazyflie_behavior.drone.mock_adapter import MockAdapter
from crazyflie_behavior.loop.tick_loop import TickStep
from crazyflie_behavior.programs.start_up import logging_for_run, quick_edit_off, run_tick_loop
from crazyflie_behavior.snapshot import RangeReading, RangeStatus, Snapshot, Stamped
from crazyflie_behavior.timing.clock import Clock, RealClock

# Not __name__: run as a program, this module is called __main__, which is
# outside the project's loggers and would lose the debug lines.
logger = logging.getLogger("crazyflie_behavior.programs.bench")

SUMMARY_PERIOD = 1.0
"""Seconds between snapshot summaries on the console."""

_EXIT_OK = 0
_EXIT_ERROR = 1
_EXIT_CTRL_C = 130
"""Ctrl+C before the tick loop started: the usual exit code for a program it stopped.
A Ctrl+C stop request during the run is the normal end, with exit code 0."""


class BenchTickStep(TickStep):
    """Takes a snapshot each tick and logs it. Never commands the drone."""

    def __init__(self, drone: DroneInterface) -> None:
        self._drone = drone
        self._next_summary_time: float | None = None

    def run(self, time: float, dt: float) -> bool:
        snapshot = self._drone.take_snapshot(time, dt)
        logger.debug("Snapshot: %s", snapshot)
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


def _describe_stamped[T](
    name: str, stamped: Stamped[T] | None, now: float, describe: Callable[[T], str]
) -> str:
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


def make_drone(use_crazyflie: bool, clock: Clock) -> DroneInterface:
    """The real Crazyflie only when asked for, otherwise the mock adapter (ADR-0028)."""
    return CrazyflieAdapter(clock) if use_crazyflie else MockAdapter(clock)


def main(arguments: list[str] | None = None) -> int:
    """Run the bench program until Ctrl+C. Returns the program's exit code."""
    parser = argparse.ArgumentParser(
        prog="bench", description="Connect, tick and log every snapshot (field-test stage 0)."
    )
    parser.add_argument(
        "--crazyflie",
        action="store_true",
        help="use the real Crazyflie instead of the mock adapter",
    )
    use_crazyflie: bool = parser.parse_args(arguments).crazyflie
    clock = RealClock()
    drone = make_drone(use_crazyflie, clock)
    with logging_for_run("bench") as log_file, quick_edit_off():
        logger.info("Bench program, %s", "the Crazyflie" if use_crazyflie else "the mock adapter")
        try:
            run_tick_loop(drone, BenchTickStep(drone), clock, log_file)
        except KeyboardInterrupt as interrupt:
            if interrupt.__context__ is not None:
                # Ctrl+C came while an error was being handled: log that error too (ADR-0020).
                logger.error(
                    "Ctrl+C while connecting; the exception being handled then is below",
                    exc_info=True,
                )
            else:
                logger.info("Ctrl+C while connecting: stopped before the tick loop started")
            return _EXIT_CTRL_C
        except Exception:
            logger.critical("The bench program stopped with an error", exc_info=True)
            return _EXIT_ERROR
    return _EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
