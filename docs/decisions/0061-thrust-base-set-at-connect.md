# 0061: The Crazyflie adapter sets the firmware's thrust base to 43,000 at connect

- **Status:** Accepted. Amends [ADR-0048](0048-level-through-the-bad-flow-zone.md): its level parts now start near the hover thrust. Closes backlog #82.
- **Date:** 2026-11-10
- **Origin:** Mixed. 43,000, over the AI's 42,000: mine. Writing the thrust base at connect, flying on with a warning when the drone doesn't confirm it, and skipping the write on a flying drone: AI recommendations accepted.

## Context

First flight 3's slow climbs, time-limit landings and dips after the
hand-over come from the firmware's vertical speed controller (analysis in
[Take-off speeds' log](../field-testing/field-tests/2026-11-09-first-flight-3-take-off-speeds.md#analysis-2026-11-10-claude)).
Its thrust command is a fixed thrust base, 36,000, plus a PID on the vertical
speed whose integral restarts at zero at every setpoint mode change and on
the floor. With three decks, this drone's hover thrust is about 43,300
(43,106-43,392 in three long hovers). So every take-off and hand-over waits
for the integral to make up about 7,300: at 0.1 m/s the drone left the floor
only after 2.8 s, the hand-over dipped 6-8 cm, and the level final descent
ran at about twice its speed.

## Options considered

- **A. Write `posCtlPid.thrustBase` at connect:** a runtime parameter, so no
  firmware build (ADR-0047 holds), and the Crazyflie adapter only. The value
  must match the drone's weight.
- **B. Raise the integral gain (`velCtlPid.vzKi`):** catches up faster, but
  changes the loop's stability and still starts from 36,000.
- **C. Command a faster climb:** helps the take-off only; the dip and the
  landing stay.
- **D. Lengthen the climb time limit:** accepts the stalls near the floor.

## Decision

Option A, with 43,000: close to the hover thrust, so after a mode change the
integral has almost nothing to make up.

- `connect()` writes `posCtlPid.thrustBase` = 43,000 on every connection,
  once the parameters are loaded. The firmware keeps it only until a reboot.
- Not when `connect()` finds the drone flying (ADR-0038's take-over): a write
  in mid-air would add about 7,000 to the thrust at once. The drone keeps its
  base, likely already 43,000 from the program it took over from. Logged.
- The adapter logs the value the drone reports back. If the drone hasn't
  confirmed 43,000 when the take-off is sent, or its firmware lacks the
  parameter, the take-off logs a warning and goes ahead.
- The climb time limits (ADR-0056, ADR-0059) are unchanged.
- 43,000 is a placeholder to verify in flight, from each hover's motor
  outputs.

## Failure modes

- **Inputs:** a lost or refused write leaves 36,000: First flight 3's slow
  climbs, which the climb time limit already lands, and the warning says
  why. A base above the hover thrust gives a quicker climb and a small
  overshoot until the integral goes negative, not a drop.
- **Backups:** unchanged: the climb time limit and the cap work from the down
  range and the clock, which the base doesn't touch.
- **Never:** the base changes while the drone may be flying.
- **Always eventually:** the motors stop, as in ADR-0048.

## Consequences

- **Risks I accept knowingly:**
  - 43,000 is about 300 under the measured hover thrust, inside the
    reconstruction's error of about 1%, so it may sit a little above it.
    A lighter drone (a deck removed, other propellers) puts it above for
    sure.
  - The value fits this drone with these decks and propellers; changing
    either needs a new measurement.
  - The hand-over still restarts the integral, and the planner starts each
    `go_to` at zero speed, so a smaller dip may remain (backlog #69).
- High-level moves hold height with less integral too, in every program.
- Tests: the write at connect; no write on a flying drone; the confirmed
  value logged; the take-off warning when unconfirmed and when the parameter
  is missing. The mock adapter has no vertical controller (backlog #84).
- Glossary: *Thrust command*, *Hover thrust* and *Thrust base* are new.

## Firmware sources (firmware 2026.08)

- Thrust command = base + 1,000 × PID on the vertical speed:
  `position_controller_pid.c` 236-266; the parameter: 576; gains and base:
  `platform_defaults_cf2.h` 142-156.
- Integrals restart at a setpoint mode change and at zero thrust:
  `controller_pid.c` (`setpointModeChanged`, `controllerPidReinitialize`).
- The battery compensation keeps a thrust command's thrust the same at any
  charge: `stabilizer.c` 208-218, `motors.c` 180-221.

## cflib sources (cflib 0.1.34, `crazyflie/param.py`)

- `set_value` only queues the write. It raises `KeyError` for a parameter
  missing from the drone's list, which cflib empties when the link is lost,
  and `AttributeError` for a read-only one. Until every parameter has been
  read, it waits up to 60 s: `connect()` writes after `wait_for_params`.
- The drone's answer calls the `add_update_callback` callbacks, with the
  value as text, on cflib's receive thread (`_ParamUpdater._new_packet_cb`).
  The parameter writer sends nothing more until they return, so an
  exception in one blocks every later parameter write.
