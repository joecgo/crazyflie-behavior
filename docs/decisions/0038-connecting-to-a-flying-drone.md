# 0038: Connecting refuses a flying drone; a rescue landing takes over the flight

- **Status:** Accepted
- **Date:** 2026-11-02
- **Origin:** Mixed. AI recommendations accepted (choices 1 to 5). Doing the full version now, rather than only the guard, and a manual emergency stop over a soft landing area for a drone out of reach, were mine.

## Context

Backlog #36. The high-level commander keeps a drone hovering with no PC at
all ([ADR-0011](0011-mock-models-setpoint-timeout.md)), so after a crash, a
hang or PyCharm's Stop ([ADR-0027](0027-operator-controls.md)) the drone can
still be in the air, or sitting on the floor with its motors running under the
landing's `go_to` ([ADR-0032](0032-landing-with-a-go-to.md)). The natural
reflex is to run the program again. Today that goes wrong:

- `connect()` resets the position estimate, which expects a drone sitting
  still. What the firmware does with a reset in flight is unchecked.
- Any `connect()` failure after the link opens (a missing Flow deck, a
  parameter timeout) runs cflib's `close_link()`, which sends a zero-thrust
  setpoint before closing: a drop.
- If `connect()` succeeds, `_may_be_flying()` only counts a take-off this
  adapter sent, so `land()` and `disconnect()` stop the motors: a drop.

Checked in the installed cflib: `supervisor.is_flying` returns "not flying"
when its reply times out or the firmware is too old (`supervisor.py`), so it
fails unsafe.

## Options considered

1. **Detecting a flying drone:** (A) start the state log block before the
   estimate reset and wait for a fresh drone status, with the existing time
   limits; (B) cflib's `supervisor.is_flying`.
2. **What `connect()` does:** (A) refuse by default, and let a rescue landing
   take over the flight on purpose; (B) always refuse.
3. **Bringing down a lost drone:** (A) a rescue-landing program in
   `src/programs/`, using the adapter's tested landing; (B) a `tools/` script
   calling cflib's `land()`, whose firmware landing turns the motors off even
   above the floor; (C) emergency stop only, a drop.
4. **How the rescue program asks for the takeover:** (A) a setting when the
   adapter is built; (B) a `connect()` parameter; (C) a separate interface
   method.
5. **Closing the link while the drone may be flying:** (A) the adapter turns
   off only the radio link, without cflib's zero-thrust setpoint. The others
   discussed didn't fix the drop (see the mistakes log).

## Decision

1A, 2A, 3A, 4A, 5A.

- `connect()` starts the state log block and waits for a fresh drone status.
  If it says flying, it raises before the estimate reset: "the drone is still
  flying: run the rescue landing." A status that never arrives is a
  time-limit error, so unknown fails safe.
- Otherwise it resets the estimate and starts a new telemetry buffer, so no
  position from before the reset is used.
- Whenever the drone may be flying, closing the link (a `connect()` failure,
  the refusal, `disconnect()` after a failed landing) turns off only the radio
  link. The drone keeps doing what it was doing, as when a program is killed.
- The rescue landing builds the adapter with `take_over_flight=True`: it skips
  the estimate reset and treats the drone as airborne, as if this adapter had
  sent the take-off, so `land()` runs the normal landing. The drone interface
  doesn't change: behaviors and game programs have no way to ask for it. The
  mock adapter gets the same setting, so the rescue program runs in
  continuous integration.
- Last resort: a `tools/` emergency-stop script that only opens the radio
  link and sends emergency stop, with no parameters, deck check, logging or
  estimate reset. Before running it, slide something soft under the drone.

## Failure modes

- **Inputs:** the status says flying for 2 s after the motors stop, so a drone
  that just landed is refused. Harmless: the error says to wait and retry.
- **Backups:** the rescue landing, then the emergency-stop script, then
  physical (wait or catch). The two software ones share the radio link: if the
  link is why the drone was lost, only the physical one is left. Early flights
  are flown low over a soft mat, a backup that needs no link. What the firmware
  does at low battery is unchecked. Accepted risk.
- **Never:** `connect()` resets the estimate of a drone that reports flying;
  the adapter sends the zero-thrust setpoint to a drone that may be flying.

## Consequences

- To build: the reordered `connect()`, the safe link close and the takeover
  setting in the Crazyflie adapter and the mock, the rescue-landing program,
  the emergency-stop script, and tests, including one that a flying drone is
  refused before any estimate reset and without a zero-thrust setpoint.
- The safe link close copies part of cflib's `close_link()` and uses its
  internals (`link`, `incoming`). Re-check it whenever cflib is upgraded.
- The field-testing procedure gains: fly early sessions low over a soft mat;
  if the program dies with the drone up, run the rescue landing, not the game
  program, then the emergency-stop script.
- VERIFY at the bench: what the firmware does with an estimate reset in
  flight, and whether cflib's link opening waits for more than the radio (the
  emergency-stop script must not).
- Glossary: **Rescue landing** added.
- **Known risk, accepted (amended 2026-11-03, my call on the AI's
  recommendation):** if the link opens and cflib's download of the parameter
  and log tables then fails, cflib's own `SyncCrazyflie.open_link` calls
  `close_link()`, which sends a zero-thrust setpoint before our code gets
  control back. On a rescue landing, that drops the flying drone. It needs a
  link that opens, a download that fails, and a zero-thrust packet that still
  gets through; at 0.1 to 0.5 m it is the drop the emergency stop makes on
  purpose. Fixing it (our own `open_link` in the adapter) is backlog #43.
