# pyright: basic
# Basic mode because cflib has no type hints (ADR-0004: tools/ runs in basic mode).
"""Last-resort emergency stop for a drone out of reach (ADR-0038).

Only opens the radio link and sends the emergency stop, a few times in case a
packet is lost. It reads no parameters, checks no decks, logs nothing and
resets no estimate, and it never imports project code, so a bug elsewhere can't
stop it. The motors stop at once: the drone drops. Run the rescue landing first
(`crazyflie_behavior.programs.rescue_landing`), and before running this, slide
something soft under the drone.

It sends both of cflib's emergency stop packets, the supervisor port's and the
older localization port's, because it doesn't ask the drone which firmware it
runs (that needs a full connection). A firmware ignores the one it doesn't know.

Run from the repository root:
    .venv\\Scripts\\python tools\\emergency_stop.py
    .venv\\Scripts\\python tools\\emergency_stop.py --uri radio://0/80/2M/E7E7E7E7E7
"""

import argparse
import struct
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


def emergency_stop(uri: str = DEFAULT_URI, send_count: int = SEND_COUNT, send_period: float = SEND_PERIOD) -> None:
    """Open the radio link, send the emergency stop `send_count` times, close the link."""
    cflib.crtp.init_drivers()
    link = cflib.crtp.get_link_driver(uri)
    if link is None:
        raise RuntimeError(f"No link driver for {uri}: check the URI.")
    try:
        for _ in range(send_count):
            for packet in emergency_stop_packets():
                link.send_packet(packet)
            time.sleep(send_period)
    finally:
        link.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Last-resort emergency stop: the drone's motors stop at once.")
    parser.add_argument("--uri", default=DEFAULT_URI, help=f"the drone's radio URI (default: {DEFAULT_URI})")
    parsed_arguments = parser.parse_args()
    print(f"Sending the emergency stop to {parsed_arguments.uri}: the drone's motors will stop at once.")
    emergency_stop(parsed_arguments.uri)
    print("Sent.")


if __name__ == "__main__":
    main()
