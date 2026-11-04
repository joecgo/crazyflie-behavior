"""The failsafe program (ADR-0041): runs the Failsafe low or Failsafe high field test once.

Arm, take off to the height (0.1 m for Failsafe low, 0.5 m for Failsafe high),
hover, and wait for the safety layer's failsafe to land the drone. The fault
that makes it fire is a forged low battery: a wrapper around the drone hands
the safety layer a snapshot with a low battery voltage after a few seconds of
hovering (`HOVER_DURATION_BEFORE_FAULT` in `failsafe_fault.py`), and logs
"FAULT INJECTED". The safety layer itself is unmodified.
It uses the mock adapter unless it's run with --crazyflie:

    .venv\\Scripts\\python -m crazyflie_behavior.programs.failsafe --height-meters 0.1
    .venv\\Scripts\\python -m crazyflie_behavior.programs.failsafe --crazyflie --height-meters 0.5

If the fault never takes effect, the failsafe test lands the drone normally
after a time limit and has failed. The exit code is 0 only if the fault was
injected, the safety pre-check then failed, the test didn't fail by its own
rules, and `disconnect()` returned (it raises if its landing fails, which makes
the exit code 1). ADR-0036 says a program exits nonzero when the failsafe ends
the flight; for this program that is the pass (ADR-0041 amends the rule).

Exit code 0 doesn't say whether the motors stopped (a lost radio link drops the
motor stop without an error, backlog #46), nor whether touchdown was confirmed
or the final descent ran out its time limit. The operator's test log records
those, from what they saw and the warnings in the log file. A pytest test checks
that the pre-check failed because of the battery.

The interrupt signal makes a stop request: before the fault, the drone lands
and the test hasn't passed.
"""

import argparse
import sys

from crazyflie_behavior.behaviors.failsafe_test import FailsafeTest
from crazyflie_behavior.loop.tick_step import BehaviorTickStep
from crazyflie_behavior.programs.failsafe_fault import ForgedLowBatteryDrone
from crazyflie_behavior.programs.start_up import EXIT_ERROR, EXIT_OK, make_drone, run_program
from crazyflie_behavior.safety.safety_layer import SafetyLayer
from crazyflie_behavior.timing.clock import RealClock

FAILSAFE_LOW_HEIGHT = 0.1
"""Meters: the Failsafe low field test."""
FAILSAFE_HIGH_HEIGHT = 0.5
"""Meters: the Failsafe high field test, the Hover test's height."""


def main(arguments: list[str] | None = None) -> int:
    """Run the failsafe test once. Returns the exit code: 0 only if it passed, as the module docstring says."""
    parser = argparse.ArgumentParser(
        prog="failsafe",
        description=(
            "Take off, hover, forge a low battery so the failsafe lands the drone "
            "(the Failsafe low and Failsafe high field tests)."
        ),
    )
    parser.add_argument(
        "--crazyflie",
        action="store_true",
        help="fly the real Crazyflie instead of the mock adapter",
    )
    parser.add_argument(
        "--height-meters",
        type=float,
        required=True,
        choices=[FAILSAFE_LOW_HEIGHT, FAILSAFE_HIGH_HEIGHT],
        metavar="METERS",
        help=f"the take-off height: {FAILSAFE_LOW_HEIGHT:g} (Failsafe low) or {FAILSAFE_HIGH_HEIGHT:g} (Failsafe high)",
    )
    parsed_arguments = parser.parse_args(arguments)
    use_crazyflie: bool = parsed_arguments.crazyflie
    height: float = parsed_arguments.height_meters
    clock = RealClock()
    drone = ForgedLowBatteryDrone(make_drone(use_crazyflie, clock))
    safety_layer = SafetyLayer(drone)
    failsafe_test = FailsafeTest(height)
    tick_step = BehaviorTickStep(drone, safety_layer, failsafe_test)
    adapter_name = "the Crazyflie" if use_crazyflie else "the mock adapter"
    test_name = "Failsafe low" if height == FAILSAFE_LOW_HEIGHT else "Failsafe high"
    description = f"Failsafe program, {adapter_name}, {test_name} ({height:g} m)"
    exit_code = run_program("failsafe", description, drone, tick_step, clock)
    if exit_code != EXIT_OK:
        return exit_code
    # The run ended without an error (`disconnect()` returned). It passed if the fault was injected, the
    # safety pre-check failed, and the test didn't fail by its own rules.
    test_passed = (
        drone.has_forged_battery_voltage and safety_layer.pre_check_has_failed and not failsafe_test.has_failed
    )
    return EXIT_OK if test_passed else EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
