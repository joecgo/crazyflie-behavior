# 0057: Failsafe low forges its battery fault when the down range reaches 0.05 m

- **Status:** Accepted. Amends [ADR-0049](0049-failsafe-low-fires-its-fault-during-the-initial-climb.md): the trigger's down range drops from 0.10 m to 0.05 m. Two readings in a row stay.
- **Date:** 2026-11-07
- **Origin:** My idea (5 cm, and what Failsafe low is for). The AI first recommended keeping 0.10 m, worried about noise near the floor; my goal made that worry small, and the AI agreed.

## Context

ADR-0049 forges the battery fault once the down range has been at least 0.10 m
for two readings in a row, and calls both numbers placeholders. I want Failsafe
low to test one thing: the drone switches from the take-off state into the
landing state. The height only has to show the drone is still taking off when
the fault fires.

## Options considered

- **A. Keep 0.10 m:** no change. The fault fires about 0.5 s after take-off,
  closer to the real battery's best observed 0.9 s (backlog #50).
- **B. 0.05 m, two readings (chosen).** Fires earlier, so the real battery has
  less time to beat it, and any landing falls from less height.
- **C. 0.05 m, three readings:** more guard against floor noise, at the cost of
  firing later.

## Decision

Option B. `CLIMB_FAULT_DOWN_RANGE` becomes 0.05 m; `CLIMB_FAULT_READINGS` stays 2.
Everything else in ADR-0049 stands: the landing stops the climb and starts the
final descent from where the drone is. Still a placeholder, tuned in the
field test.

## Failure modes

- **Inputs:** the down range dips to 0.000-0.003 m at spin-up, and the floor is
  its noisiest region. A burst of noise above 0.05 m, two readings in a row,
  could fire the fault while the drone is barely off the floor. The drone is
  still in the take-off state, so the transition under test still happens, but
  the landing is less meaningful. The log shows the height it fired at.
- **Backups:** the real low battery can still trip first; the log says which
  fired. A down range that never reaches 0.05 m: as ADR-0049, the take-off time
  limit lands the drone and the test has failed.
- **Never:** unchanged from ADR-0049.
- **Always eventually:** the motors stop.

## Consequences

- **Risks I accept knowingly:**
  - 0.05 m is close to the spin-up noise, and no recorded trace of it exists
    for the 0.05-0.10 m range. I accept the early fire; the field test shows
    whether it is too early.
  - A landing from 5 cm proves the switch from take-off to landing, not a
    landing from a clearly airborne climb. Failsafe high proves the hover
    landing.
- Code: `CLIMB_FAULT_DOWN_RANGE`, its tests, the Failsafe low log and the docs
  that say 0.10 m.
- No glossary change.
