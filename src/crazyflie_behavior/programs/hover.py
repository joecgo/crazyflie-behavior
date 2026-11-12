"""The hover program (ADR-0030): runs the hover test once, for the Hover field test.

Arm, take off to `TAKE_OFF_HEIGHT`, hover, land. It uses the mock adapter
unless it's run with --crazyflie. With --chirp, the hover test also chirps
and ends with "Charge" (ADR-0053). --climb-speed sets the initial climb's
speed, for take-off speed tests (ADR-0059):

    .venv\\Scripts\\python -m crazyflie_behavior.programs.hover
    .venv\\Scripts\\python -m crazyflie_behavior.programs.hover --crazyflie
    .venv\\Scripts\\python -m crazyflie_behavior.programs.hover --crazyflie --hover-seconds 60
    .venv\\Scripts\\python -m crazyflie_behavior.programs.hover --crazyflie --chirp
    .venv\\Scripts\\python -m crazyflie_behavior.programs.hover --crazyflie --climb-speed 0.4
    .venv\\Scripts\\python -m crazyflie_behavior.programs.hover --crazyflie --take-off-log

Each snapshot goes to the log file; the console shows the hover test's steps
and each command sent. In a terminal, Ctrl+C sends the interrupt signal, which
makes a stop request: the drone lands.

The exit code is 1 when the hover test failed, even if the program ran fine:
a refused request, a time limit, or a hover the safety layer or a stop request
cut short (ADR-0062). The log shows the cause, not the exit code (ADR-0066).
"""

import argparse
import sys

from crazyflie_behavior.behaviors.hover_test import CHIRP_PERIOD, DEFAULT_HOVER_DURATION, TAKE_OFF_HEIGHT, HoverTest
from crazyflie_behavior.drone.crazyflie.bad_flow_zone import (
    LEVEL_VERTICAL_SPEED,
    MAX_INITIAL_CLIMB_SPEED,
    MIN_INITIAL_CLIMB_SPEED,
    check_initial_climb_speed,
)
from crazyflie_behavior.loop.tick_step import BehaviorTickStep
from crazyflie_behavior.programs.start_up import (
    EXIT_ERROR,
    EXIT_OK,
    add_take_off_log_option,
    make_drone,
    run_program,
    take_off_log_description,
)
from crazyflie_behavior.safety.safety_layer import SafetyLayer
from crazyflie_behavior.timing.clock import RealClock


def main(arguments: list[str] | None = None) -> int:
    """Run the hover test once. Returns the program's exit code."""
    parser = argparse.ArgumentParser(
        prog="hover", description=f"Arm, take off to {TAKE_OFF_HEIGHT:g} m, hover, land (the Hover field test)."
    )
    parser.add_argument(
        "--crazyflie",
        action="store_true",
        help="fly the real Crazyflie instead of the mock adapter",
    )
    parser.add_argument(
        "--hover-seconds",
        type=float,
        default=DEFAULT_HOVER_DURATION,
        metavar="SECONDS",
        help=f"how long to hover at the take-off height (default: {DEFAULT_HOVER_DURATION:g})",
    )
    parser.add_argument(
        "--chirp",
        action="store_true",
        help=f'chirp on the floor, every {CHIRP_PERIOD:g} s in flight and after landing, then play "Charge"',
    )
    parser.add_argument(
        "--climb-speed",
        type=float,
        default=LEVEL_VERTICAL_SPEED,
        metavar="M_PER_S",
        help=(
            f"the initial climb's speed, {MIN_INITIAL_CLIMB_SPEED:g}-{MAX_INITIAL_CLIMB_SPEED:g} m/s "
            f"(default: {LEVEL_VERTICAL_SPEED:g}); the landing keeps its own"
        ),
    )
    add_take_off_log_option(parser)
    parsed_arguments = parser.parse_args(arguments)
    use_crazyflie: bool = parsed_arguments.crazyflie
    hover_duration: float = parsed_arguments.hover_seconds
    chirp: bool = parsed_arguments.chirp
    climb_speed: float = parsed_arguments.climb_speed
    take_off_log: bool = parsed_arguments.take_off_log
    try:
        hover_test = HoverTest(hover_duration, chirp=chirp)
    except ValueError as error:
        parser.error(f"--hover-seconds: {error}")
    try:
        check_initial_climb_speed(climb_speed)
    except ValueError as error:
        parser.error(f"--climb-speed: {error}")
    clock = RealClock()
    drone = make_drone(use_crazyflie, clock, initial_climb_speed=climb_speed, take_off_log=take_off_log)
    tick_step = BehaviorTickStep(drone, SafetyLayer(drone), hover_test)
    adapter_name = "the Crazyflie" if use_crazyflie else "the mock adapter"
    description = f"Hover program, {adapter_name}, hovering {hover_duration:g} s, climbing at {climb_speed:g} m/s"
    if chirp:
        description += ", with chirps"
    if take_off_log:
        description += take_off_log_description(use_crazyflie)
    exit_code = run_program("hover", description, drone, tick_step, clock)
    # A failed hover test exits 1 even though the program itself ran fine: see `has_failed` (ADR-0062).
    return EXIT_ERROR if exit_code == EXIT_OK and hover_test.has_failed else exit_code


if __name__ == "__main__":
    sys.exit(main())
