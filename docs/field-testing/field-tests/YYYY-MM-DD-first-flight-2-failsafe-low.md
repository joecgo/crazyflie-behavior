# YYYY-MM-DD-first-flight-2-failsafe-low

- **Session:** [First flight 2](../sessions/YYYY-MM-DD-first-flight-2.md)
- **Test:** Failsafe low (safety)
- **Environment:** [Living room](../environments/living-room.md), hide-and-seek launch point, ___ (time of day)
- **Git commit:** `<hash>` (must be committed before flying)
- **Hardware:** Crazyflie 2.1+, decks: Flow / Multi-ranger / Buzzer, battery #
- **Firmware / cflib:** 2026.08, release 2026.10, unmodified ([ADR-0047](../../decisions/0047-pinned-firmware-release-warn-on-mismatch.md)) / 0.1.34

## Goal and pass criteria
*Written before flying.*

- Goal: *To be written once backlog #52 is decided.* Session 1's version
  (take off to 0.1 m, then a forged low battery reading) can't run any more:
  ADR-0048 refuses take-off targets at or below 0.30 m. Session 1's real
  battery tripped before the forged fault both times (backlog #50).
- Pass if: *To be written with the goal.* Session 1's criteria, for reference:
  - [ ] The log shows `FAULT INJECTED: battery voltage forged`.
  - [ ] The pre-check fails with the battery message, and a landing is sent.
  - [ ] The drone lands and its motors stop (seen by the operator), and the
        program exits with code 0.
  - [ ] The log has no "Failsafe test failed" error.
  - [ ] The landing needed no help from the kill switch or rescue landing.
- Simulator prediction (or, if not simulated, the mock adapter run): ___

## Pre-flight checklist

- [ ] Bench passed
- [ ] Code committed, hash recorded above
- [ ] Mock adapter run of this exact code passed
- [ ] Propellers undamaged, battery charged (voltage: ___)
- [ ] Soft landing patch under the drone, flight area clear of people and pets
- [ ] Geofence configured for this space
- [ ] Video recording on

## During the test

*To be written with the goal.*

- [ ]

## Flights

| # | What was run | Result | Data file | Notes |
|---|---|---|---|---|
| 1 | | | | |

## Observations

### Joe

-

### Computed from the logs (Claude)

-

## Next
- Code changes:
- ADRs to write or revisit:
- Next session's goal:
