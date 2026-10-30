"""The hover program (ADR-0030): runs the hover test once, for field-test stage 1.

Arm, take off to 0.5 m, hover, land. It uses the mock adapter unless it's run
with --crazyflie:

    .venv\\Scripts\\python -m crazyflie_behavior.programs.hover
    .venv\\Scripts\\python -m crazyflie_behavior.programs.hover --crazyflie
    .venv\\Scripts\\python -m crazyflie_behavior.programs.hover --crazyflie --hover-seconds 60

Each snapshot goes to the log file; the console shows the hover test's steps
and each command sent. Ctrl+C is a stop request: the drone lands.
"""

import argparse
import sys

from crazyflie_behavior.behaviors.hover_test import DEFAULT_HOVER_DURATION, HoverTest
from crazyflie_behavior.loop.tick_step import BehaviorTickStep
from crazyflie_behavior.programs.start_up import make_drone, run_program
from crazyflie_behavior.safety.safety_layer import SafetyLayer
from crazyflie_behavior.timing.clock import RealClock


def main(arguments: list[str] | None = None) -> int:
    """Run the hover test once. Returns the program's exit code."""
    parser = argparse.ArgumentParser(
        prog="hover", description="Arm, take off to 0.5 m, hover, land (field-test stage 1)."
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
    parsed_arguments = parser.parse_args(arguments)
    use_crazyflie: bool = parsed_arguments.crazyflie
    hover_duration: float = parsed_arguments.hover_seconds
    try:
        hover_test = HoverTest(hover_duration)
    except ValueError as error:
        parser.error(f"--hover-seconds: {error}")
    clock = RealClock()
    drone = make_drone(use_crazyflie, clock)
    tick_step = BehaviorTickStep(drone, SafetyLayer(drone), hover_test)
    adapter_name = "the Crazyflie" if use_crazyflie else "the mock adapter"
    description = f"Hover program, {adapter_name}, hovering {hover_duration:g} s"
    return run_program("hover", description, drone, tick_step, clock)


if __name__ == "__main__":
    sys.exit(main())
