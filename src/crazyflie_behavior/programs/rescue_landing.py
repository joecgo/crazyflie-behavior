"""The rescue landing program (ADR-0038): lands a drone a lost program left flying.

After a crash, a hang or a stopped program, the drone can still be in the air.
Run this, not the game program: it connects without resetting the position
estimate, takes over the flight and lands the drone with the normal landing.
It uses the mock adapter unless it's run with --crazyflie:

    .venv\\Scripts\\python -m crazyflie_behavior.programs.rescue_landing
    .venv\\Scripts\\python -m crazyflie_behavior.programs.rescue_landing --crazyflie

The exit code is 0 unless the rescue failed (a refused landing, or the drone still reporting
flying after the time limit) or the program stopped with an error.

If this can't bring the drone down, the last resort is `tools/emergency_stop.py`:
slide something soft under the drone first.
"""

import argparse
import sys

from crazyflie_behavior.behaviors.rescue_landing import RescueLanding
from crazyflie_behavior.loop.tick_step import BehaviorTickStep
from crazyflie_behavior.programs.start_up import EXIT_ERROR, EXIT_OK, make_drone, run_program
from crazyflie_behavior.safety.safety_layer import SafetyLayer
from crazyflie_behavior.timing.clock import RealClock


def main(arguments: list[str] | None = None) -> int:
    """Take over a flying drone and land it. Returns the program's exit code."""
    parser = argparse.ArgumentParser(
        prog="rescue_landing", description="Take over a drone a lost program left flying, and land it (ADR-0038)."
    )
    parser.add_argument(
        "--crazyflie",
        action="store_true",
        help="rescue the real Crazyflie instead of the mock adapter",
    )
    parsed_arguments = parser.parse_args(arguments)
    use_crazyflie: bool = parsed_arguments.crazyflie
    clock = RealClock()
    drone = make_drone(use_crazyflie, clock, take_over_flight=True)
    rescue_landing = RescueLanding()
    tick_step = BehaviorTickStep(drone, SafetyLayer(drone), rescue_landing)
    adapter_name = "the Crazyflie" if use_crazyflie else "the mock adapter"
    exit_code = run_program("rescue_landing", f"Rescue landing program, {adapter_name}", drone, tick_step, clock)
    # A refused landing or the time limit is a failed rescue, even though the program itself ran fine.
    return EXIT_ERROR if exit_code == EXIT_OK and rescue_landing.has_failed else exit_code


if __name__ == "__main__":
    sys.exit(main())
