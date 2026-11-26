# pyright: basic
# Basic mode because cflib has no type hints (ADR-0004). Everything this module
# exposes is fully typed; the looseness stays inside this file.
"""The Crazyflie adapter's radio link: opening and closing it, the parameters and decks, the lost link and the thrust
base (ADR-0093).

Owns cflib's `SyncCrazyflie`: the adapter and its other parts look up `crazyflie` on every call and keep no reference
to it.
"""

import logging

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie

from crazyflie_behavior.drone.crazyflie.time_limit import run_with_time_limit
from crazyflie_behavior.timing.clock import Clock

logger = logging.getLogger(__name__)

# --- PLACEHOLDERS, NOT DECISIONS ---------------------------------------------
# Flight parameters wait on speed envelopes (ADR-0005) and the safety layer.
# These values just let the adapter run.
# Time limits for connecting (ADR-0029). VERIFY at the bench, and measure (backlog #25).
LINK_TIME_LIMIT = 15.0
"""Seconds to open the link and get the drone's variable lists. A first connect,
with nothing cached, downloads more."""
PARAMETERS_TIME_LIMIT = 10.0
"""Seconds to read the parameter values."""
THRUST_BASE = 43_000
"""Written to the drone at connect, near this drone's hover thrust (ADR-0061). VERIFY from each hover's
motor outputs."""
# ------------------------------------------------------------------------------

_THRUST_BASE_PARAMETER = "posCtlPid.thrustBase"

_drivers_initialized = False


def _init_drivers_once() -> None:
    # cflib.crtp.init_drivers() appends to a global driver list on every call,
    # so a second call would register every driver twice.
    global _drivers_initialized
    if not _drivers_initialized:
        cflib.crtp.init_drivers()
        _drivers_initialized = True


class CrazyflieLink:
    """The radio link to one Crazyflie: opening and closing it, the parameters and decks, the lost link and the
    thrust base (ADR-0093)."""

    def __init__(self, clock: Clock, uri: str, cache_directory: str, *, take_over_flight: bool) -> None:
        """`take_over_flight`: leave the thrust base as it is, since the drone may be flying (ADR-0061)."""
        self._clock = clock
        self._uri = uri
        self._cache_directory = cache_directory
        self._take_over_flight = take_over_flight
        self._sync_crazyflie: SyncCrazyflie | None = None
        self._is_thrust_base_confirmed = False
        """The drone's latest report of its thrust base was THRUST_BASE (ADR-0061). Written on cflib's
        receive thread."""
        self._lost_link_message: str | None = None
        """cflib's message for a lost link (ADR-0084). Written on whichever thread cflib reports it from."""
        self._is_lost_link_raised = False
        """A snapshot or a wait has raised for the lost link, so `disconnect()` doesn't raise for it again."""

    @property
    def crazyflie(self) -> Crazyflie:
        """The cflib `Crazyflie` of the link; raises when there's none. Look it up on every use: `open()` makes a new
        one."""
        if self._sync_crazyflie is None:
            raise RuntimeError("Not connected: call connect() first.")
        return self._sync_crazyflie.cf

    @property
    def has_link_to_close(self) -> bool:
        """From the start of `open()` until `close()`, so also while opening and after a lost link."""
        return self._sync_crazyflie is not None

    @property
    def is_thrust_base_confirmed(self) -> bool:
        return self._is_thrust_base_confirmed

    @property
    def is_lost(self) -> bool:
        """cflib reported the link lost (ADR-0084)."""
        return self._lost_link_message is not None

    @property
    def is_lost_link_raised(self) -> bool:
        return self._is_lost_link_raised

    def open(self) -> None:
        """Open the link and read the parameters, each with its time limit (ADR-0029). Blocks."""
        _init_drivers_once()
        sync_crazyflie = SyncCrazyflie(self._uri, cf=Crazyflie(rw_cache=self._cache_directory))
        self._sync_crazyflie = sync_crazyflie  # tracked from the start, so cleanup always finds it
        # Before the link opens, so no lost link goes unheard (ADR-0084).
        sync_crazyflie.cf.connection_lost.add_callback(self._on_connection_lost)
        # cflib's blocking steps each get a time limit, waited for in short
        # slices so the interrupt signal gets through, even on Windows (ADR-0029).
        run_with_time_limit(
            "Opening the link",
            sync_crazyflie.open_link,  # raises if it can't connect
            LINK_TIME_LIMIT,
            what_to_check="Check the Crazyflie is switched on, charged and in range.",
            clock=self._clock,
            # Stop a connection still under way, without cflib's zero-thrust
            # setpoint: the drone may be flying (ADR-0038). When connecting
            # fails on its own, cflib closes the link itself.
            on_abandon=self.close_radio_link_only,
        )
        run_with_time_limit(
            "Reading the parameters",
            sync_crazyflie.wait_for_params,
            PARAMETERS_TIME_LIMIT,
            what_to_check="The link may have dropped: check the Crazyflie is still switched on.",
            clock=self._clock,
        )

    def close(self, *, radio_link_only: bool) -> None:
        """Close the link if there is one, only its radio link when `radio_link_only` (ADR-0038). Blocks."""
        if self._sync_crazyflie is not None:
            if radio_link_only:
                # The drone may be flying: cflib's close_link() would drop it (ADR-0038).
                self.close_radio_link_only()
            else:
                self._sync_crazyflie.close_link()
            self._sync_crazyflie = None

    def close_radio_link_only(self) -> None:
        """Turn off the radio link and nothing else, so a flying drone keeps flying (ADR-0038).

        cflib's `Crazyflie.close_link()` first sends a zero-thrust setpoint, which
        would drop a flying drone. This does three of its other steps, in the same
        order: close the link, stop the incoming packet handler, and call the
        disconnected callbacks. It skips the rest (re-creating the incoming packet
        handler, clearing the expected answers, setting the state to disconnected),
        which matters only to a Crazyflie object that is used again: `connect()`
        always makes a new one. It uses cflib internals (`link`, `incoming`):
        re-check it against `close_link()` whenever cflib is upgraded. Safe to call
        twice, and when the link isn't open.
        """
        if self._sync_crazyflie is None:
            return
        crazyflie = self._sync_crazyflie.cf
        if crazyflie.link is not None:
            logger.info("Closing the radio link only, with no zero-thrust setpoint: the drone may be flying")
            crazyflie.link.close()
            crazyflie.link = None
        if crazyflie.incoming and crazyflie.incoming.is_alive():
            crazyflie.incoming.stop()
            crazyflie.incoming.join(timeout=1)
        # cflib's own close_link() calls this too: it tells SyncCrazyflie the link is closed.
        crazyflie.disconnected.call(crazyflie.link_uri)

    def is_deck_attached(self, *parameters: str) -> bool:
        """True if any of the deck parameters says the deck is attached."""
        for parameter in parameters:
            try:
                if int(self.crazyflie.param.get_value(parameter)) == 1:
                    return True
            except KeyError:
                pass  # this firmware doesn't know the parameter: not attached
        return False

    def write_thrust_base(self) -> None:
        """Write THRUST_BASE and log what the drone reports back, unless taking over a flight (ADR-0061)."""
        if self._take_over_flight:
            # The drone may be flying: a new base would change its thrust at once.
            logger.info("Thrust base left as it is: the drone may be flying.")
            return
        param = self.crazyflie.param
        group, name = _THRUST_BASE_PARAMETER.split(".")
        param.add_update_callback(group=group, name=name, cb=self._on_thrust_base_reported)
        try:
            param.set_value(_THRUST_BASE_PARAMETER, THRUST_BASE)
        except (KeyError, AttributeError):
            # cflib raises these for a parameter the firmware lacks or can't write, and once the link is
            # lost. The take-off warns and flies on without it.
            cause = "the link is closed" if self.crazyflie.link is None else "the firmware can't write it"
            logger.warning("Thrust base not sent: %s.", cause)

    def _on_thrust_base_reported(self, name: str, value: str) -> None:
        # cflib calls this on its receive thread, inside its parameter writer: an exception here would block
        # every later parameter write. So the value is compared as text, never parsed.
        self._is_thrust_base_confirmed = value == str(THRUST_BASE)
        if self._is_thrust_base_confirmed:
            logger.info("Thrust base confirmed: the drone reports %s.", value)
        else:
            logger.warning("Thrust base not confirmed: the drone reports %s, not %d.", value, THRUST_BASE)

    def raise_if_lost(self) -> None:
        """Raise after a lost link, so the run ends with an error (ADR-0084)."""
        message = self._lost_link_message
        if message is None:
            return
        self._is_lost_link_raised = True
        raise ConnectionError(f"The radio link to the drone was lost: {message}")

    def _on_connection_lost(self, link_uri: str, message: str) -> None:
        # cflib calls this on whichever thread found the link error, the tick's included: store and log only.
        self._lost_link_message = str(message)
        logger.error("The radio link to the drone was lost: %s", message)
