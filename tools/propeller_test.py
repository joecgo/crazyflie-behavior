# pyright: basic
# Basic mode because cflib has no type hints (ADR-0004: tools/ runs in basic mode).
"""Propeller test: the firmware spins each motor alone and reports its vibration.

Starts `health.startPropTest` and prints the drone's console until the test ends:
per motor, the accelerometer's sideways variance and the battery sag. One motor far
above the rest points to an unbalanced or damaged propeller or a worn bearing. It
doesn't measure thrust.

The motors spin without arming, and the firmware pauses the estimator and the
controller while the test runs: drone on the floor only.

Run from the repository root:
    .venv\\Scripts\\python tools\\propeller_test.py
    .venv\\Scripts\\python tools\\propeller_test.py --uri radio://0/80/2M/E7E7E7E7E7
"""

import argparse
import sys
import threading
import time

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie

# The same as the Crazyflie adapter's default (a test keeps them equal).
DEFAULT_URI = "radio://0/80/2M/E7E7E7E7E7"
TIME_LIMIT = 60.0
"""Seconds to wait for the first count sample, then again for the test to end."""
CONSOLE_WAIT = 1.0
"""Seconds to keep the link open after the end, for the console's last lines."""
COUNT_VARIABLE = "health.motorTestCount"
"""Goes up by one when a propeller test ends."""


def run_propeller_test(
    uri: str = DEFAULT_URI, time_limit: float = TIME_LIMIT, console_wait: float = CONSOLE_WAIT
) -> bool:
    """Run the test, printing the console. Returns whether it ended within the time limit."""
    cflib.crtp.init_drivers()
    with SyncCrazyflie(uri, cf=Crazyflie()) as sync_crazyflie:
        crazyflie = sync_crazyflie.cf
        crazyflie.console.receivedChar.add_callback(lambda text: print(text, end="", flush=True))
        counts: list[int] = []
        has_count = threading.Event()
        has_ended = threading.Event()

        def on_count(_timestamp, data, _block) -> None:
            counts.append(data[COUNT_VARIABLE])
            has_count.set()
            if counts[-1] != counts[0]:
                has_ended.set()

        block = LogConfig(name="propeller_test", period_in_ms=100)
        block.add_variable(COUNT_VARIABLE, "uint16_t")
        block.data_received_cb.add_callback(on_count)
        crazyflie.log.add_config(block)
        block.start()
        # The count before the test starts, so a test that ends between samples isn't missed.
        ended = has_count.wait(time_limit)
        if ended:
            crazyflie.param.set_value("health.startPropTest", 1)
            ended = has_ended.wait(time_limit)
            time.sleep(console_wait)
        block.stop()
    return ended


def main(arguments: list[str] | None = None) -> int:
    """Returns the exit code: 0 only if the test ended."""
    parser = argparse.ArgumentParser(description="Propeller test: spins each motor alone, drone on the floor.")
    parser.add_argument("--uri", default=DEFAULT_URI, help=f"the drone's radio URI (default: {DEFAULT_URI})")
    parsed_arguments = parser.parse_args(arguments)
    if run_propeller_test(parsed_arguments.uri):
        return 0
    print(f"The propeller test didn't end within {TIME_LIMIT:g} s.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
