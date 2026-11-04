# pyright: basic
# Basic mode because cflib has no type hints (ADR-0004: tools/ runs in basic mode).
"""Last-resort emergency stop for a drone out of reach (ADR-0038).

Only opens the radio link and sends the emergency stop, a few times in case a
packet is lost. It reads no parameters, checks no decks, sets up no logging and
resets no estimate, and it never imports project code, so a bug elsewhere can't
stop it. The motors stop at once: the drone drops. Run the rescue landing first
(`crazyflie_behavior.programs.rescue_landing`), and before running this, slide
something soft under the drone.

It sends both of cflib's emergency stop packets, the supervisor port's and the
older localization port's, because it doesn't ask the drone which firmware it
runs (that needs a full connection). NOT YET RUN ON HARDWARE. VERIFY at the bench that a firmware accepts either packet
without a connection set up first, and ignores the one it doesn't know.

Run from the repository root:
    .venv\\Scripts\\python tools\\emergency_stop.py
    .venv\\Scripts\\python tools\\emergency_stop.py --uri radio://0/80/2M/E7E7E7E7E7
"""

import argparse
import struct
import sys
import time

import cflib.crtp
from cflib.crazyflie.localization import Localization
from cflib.crazyflie.supervisor import CMD_EMERGENCY_STOP, SUPERVISOR_CH_COMMAND
from cflib.crtp.crtpstack import CRTPPacket, CRTPPort

# The same as the Crazyflie adapter's default (a test keeps them equal). Copied, not
# imported, so this script stays independent of project code.
DEFAULT_URI = "radio://0/80/2M/E7E7E7E7E7"
SEND_COUNT = 10
"""How many times the pair of packets is sent."""
SEND_PERIOD = 0.1
"""Seconds between sends, and the wait after the last one before the link closes."""


def emergency_stop_packets() -> list[CRTPPacket]:
    """The emergency stop packets of both firmware generations."""
    supervisor_packet = CRTPPacket()
    supervisor_packet.set_header(CRTPPort.SUPERVISOR, SUPERVISOR_CH_COMMAND)
    supervisor_packet.data = (CMD_EMERGENCY_STOP,)
    localization_packet = CRTPPacket()
    localization_packet.set_header(CRTPPort.LOCALIZATION, Localization.GENERIC_CH)
    localization_packet.data = struct.pack("<B", Localization.EMERGENCY_STOP)
    return [supervisor_packet, localization_packet]


def emergency_stop(uri: str = DEFAULT_URI, send_count: int = SEND_COUNT, send_period: float = SEND_PERIOD) -> bool:
    """Open the radio link, send the emergency stop `send_count` times, close the link.

    Returns whether the radio took every packet without a link error. False means
    the stop isn't confirmed: cflib's `send_packet` waits up to 2 s for a free slot
    and returns False when the radio isn't delivering (a drone out of range, off or
    on another channel), so it gives up at the first failure instead of waiting
    for the rest.
    """
    cflib.crtp.init_drivers()
    link_errors: list[str] = []
    link = cflib.crtp.get_link_driver(uri, link_error_callback=link_errors.append)
    if link is None:
        raise RuntimeError(f"No link driver for {uri}: check the URI.")
    try:
        for _ in range(send_count):
            for packet in emergency_stop_packets():
                if not link.send_packet(packet):
                    return False
            time.sleep(send_period)
    finally:
        link.close()
    return not link_errors


def main(arguments: list[str] | None = None) -> int:
    """Returns the exit code: 0 only if the radio took every packet."""
    parser = argparse.ArgumentParser(description="Last-resort emergency stop: the drone's motors stop at once.")
    parser.add_argument("--uri", default=DEFAULT_URI, help=f"the drone's radio URI (default: {DEFAULT_URI})")
    parsed_arguments = parser.parse_args(arguments)
    print(f"Sending the emergency stop to {parsed_arguments.uri}: the drone's motors will stop at once.")
    if emergency_stop(parsed_arguments.uri):
        print("Sent: the radio took every packet. Check that the motors stopped.")
        return 0
    print(
        "NOT CONFIRMED: the radio didn't take every packet, or it reported a link error. "
        "Assume the drone is still flying. Run it again, or bring the Crazyradio closer, "
        "keeping clear of the drone.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
