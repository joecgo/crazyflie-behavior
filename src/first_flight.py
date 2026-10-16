"""First contact with cflib: scan for a Crazyflie over the Crazyradio.

No drone or radio yet? That's fine. The scan just finds nothing, which still
proves Python, the virtual environment and cflib are set up correctly.

Run from the repository root:
    .venv\\Scripts\\python src\\first_flight.py
"""

import cflib.crtp


def main():
    # Load cflib's link drivers (radio, USB, ...). Must happen before any scan
    # or connection, like registering subsystems before the game loop starts.
    cflib.crtp.init_drivers()

    print("Scanning for Crazyflies...")
    found = cflib.crtp.scan_interfaces()

    if not found:
        print("No Crazyflie found (expected until the hardware arrives).")
        return

    # Each entry is a list like [uri, description]; the URI is the drone's
    # "address", e.g. radio://0/80/2M/E7E7E7E7E7.
    for uri, description in found:
        print(f"Found: {uri} {description}")


# This block runs only when the file is executed directly, not when another
# file imports it. It's Python's equivalent of a program entry point.
if __name__ == "__main__":
    main()
