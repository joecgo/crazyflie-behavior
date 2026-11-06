"""The hover program (ADR-0030): runs the hover test once, for the Hover field test.

Arm, take off to `TAKE_OFF_HEIGHT`, hover, land. It uses the mock adapter
unless it's run with --crazyflie. With --chirp, the hover test also chirps
and ends with "Charge" (ADR-0053):

    .venv\\Scripts\\python -m crazyflie_behavior.programs.hover
    .venv\\Scripts\\python -m crazyflie_behavior.programs.hover --crazyflie
    .venv\\Scripts\\python -m crazyflie_behavior.programs.hover --crazyflie --hover-seconds 60
    .venv\\Scripts\\python -m crazyflie_behavior.programs.hover --crazyflie --chirp

Each snapshot goes to the log file; the console shows the hover test's steps
and each command sent. In a terminal, Ctrl+C sends the interrupt signal, which
makes a stop request: the drone lands.
"""

import argparse
import sys

from crazyflie_behavior.behaviors.hover_test import CHIRP_PERIOD, DEFAULT_HOVER_DURATION, TAKE_OFF_HEIGHT, HoverTest
from crazyflie_behavior.loop.tick_step import BehaviorTickStep
from crazyflie_behavior.programs.start_up import make_drone, run_program
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
    parsed_arguments = parser.parse_args(arguments)
    use_crazyflie: bool = parsed_arguments.crazyflie
    hover_duration: float = parsed_arguments.hover_seconds
    chirp: bool = parsed_arguments.chirp
    try:
        hover_test = HoverTest(hover_duration, chirp=chirp)
    except ValueError as error:
        parser.error(f"--hover-seconds: {error}")
    clock = RealClock()
    drone = make_drone(use_crazyflie, clock)
    tick_step = BehaviorTickStep(drone, SafetyLayer(drone), hover_test)
    adapter_name = "the Crazyflie" if use_crazyflie else "the mock adapter"
    description = f"Hover program, {adapter_name}, hovering {hover_duration:g} s"
    if chirp:
        description += ", with chirps"
    return run_program("hover", description, drone, tick_step, clock)


if __name__ == "__main__":
    sys.exit(main())
