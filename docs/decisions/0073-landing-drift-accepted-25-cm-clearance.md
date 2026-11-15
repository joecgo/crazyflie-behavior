# 0073: The landing drift is accepted; a landing target needs 25 cm clear in every direction

- **Status:** Accepted. Closes backlog #101 and #102. First flight's 5 cm landing goal is dropped, so First flight is done.
- **Date:** 2026-11-14
- **Origin:** Mixed. Accepting the drift if no software fix existed, and the 25 cm (the drone's 7 cm radius plus 18 cm of landing error): mine. Accepting it although a partial software fix exists, a full circle, and dropping the 5 cm goal: AI recommendations accepted.

## Context

First flight's goal was landings within 5 cm of the mark. In First flight 6,
after the M1 motor swap, hovers with a 0.2 m/s final descent landed 7-16 cm
from the mark; at 0.3 m/s ([ADR-0072](0072-final-descent-0-3-m-per-s.md)),
five flights landed 7-10 cm back right. The analysis
([First flight 6](../field-testing/sessions/2026-11-14-first-flight-6.md)):
the switch to the level final descent is a setpoint mode change, at which
firmware 2026.08 restarts every controller integral, so the drone's trim is
gone for the whole level part and the nose comes up. The final descent also
starts while the landing approach is still correcting (tilted 1.4-4°, moving
up to 0.10 m/s), which the level part can't brake. Failsafe low, with no mode
change, still landed 7 cm off.

## Options considered

- **A. Accept the drift (chosen),** and size the landing clearance from it.
- **B. Hand over at rest:** hold position at the final descent height until
  the drone is still, then go level. Removes the hand-over's speed and tilt,
  not the lost trim or what happens on the floor: a few cm, not measured.
- **C. Our own firmware build** that keeps the rate integrals across mode
  changes: the only fix for the lost trim short of balancing the drone, but a
  firmware fork to own.
- **D. Aim the landing against the drift:** a calibration whose direction
  changed twice in session 6 with the hardware.

## Decision

Option A. Software can win back a few cm at most, and a hiding spot needs a
margin anyway; the bigger unknown is the drift over a real hiding flight.

- **First flight is done.** Its 5 cm goal is dropped, and session 6's spread
  is the result: 7-10 cm at 0.3 m/s (one flight per condition), 7-16 cm at
  0.2 m/s.
- **Landing clearance:** a landing target needs 25 cm clear in every
  direction: no walls or obstacles within 25 cm of it. That's the drone's
  radius (7 cm) plus 18 cm of landing error, which covers session 6's worst
  landing (16 cm). A full circle, because the drift's direction changed with
  each hardware change in session 6.
- The final descent stays as it is (ADR-0048, ADR-0068, ADR-0072).

## Failure modes

- **Inputs:** the clearance is only as good as the map it's checked on
  (backlog #7). A landing further off than 18 cm, after a hiding flight's
  drift or a hardware change that turns or grows the trim, can come down on
  or against an obstacle.
- **Never** and **always eventually:** unchanged (ADR-0048): the motors stop
  only at confirmed touchdown or the final descent's time limit, and every
  landing ends with the motors stopped.

## Consequences

- **Risks I accept knowingly:**
  - The 18 cm comes from hovers on the mark. A hiding flight adds position
    drift, not yet measured. VERIFY in the first hide-and-seek field test
    that lands after a flight across the room.
  - The drift follows the hardware: the trim's size and direction changed
    with each change in session 6, and a larger trim lands further off.
  - One flight per condition at 0.3 m/s.
- Backlog #103 keeps B and C for later. Not pursued: what made the trim
  larger since session 5 (hardware).
- Hide-and-seek: a candidate hiding spot needs 25 cm clear (backlog #5a).
- Code: none.
- Glossary: *Landing clearance* is new, and *Hiding spot* now includes it (my OK, 2026-11-14).
