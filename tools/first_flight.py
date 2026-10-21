# pyright: basic
# Basic mode because cflib has no type hints (ADR-0004: tools/ runs in basic mode).
"""Hardware smoke test: scan for a Crazyflie over the Crazyradio.

A diagnostic tool, so it talks to cflib directly and bypasses the drone
interface (see the tools exemption in ADR-0002).

No drone or radio yet? That's fine. The scan just finds nothing, which still
proves Python, the virtual environment and cflib are set up correctly.

Run from the repository root:
    .venv\\Scripts\\python tools\\first_flight.py
"""

import cflib.crtp


def main() -> None:
    # Load cflib's link drivers (radio, USB, ...). Must happen before any scan
    # or connection, like registering subsystems before the game loop starts.
    cflib.crtp.init_drivers()

    print("Scanning for Crazyflies...")
    # cflib is untyped, so state the type here: one [uri, description] pair per
    # drone found. The URI is the drone's "address", e.g. radio://0/80/2M.
    available_drones: list[list[str]] = cflib.crtp.scan_interfaces()

    if not available_drones:
        print("No Crazyflie found (expected until the hardware arrives).")
        return

    for uri, description in available_drones:
        print(f"Found: {uri} {description}")


# This block runs only when the file is executed directly, not when another
# file imports it. It's Python's equivalent of a program entry point.
if __name__ == "__main__":
    main()
