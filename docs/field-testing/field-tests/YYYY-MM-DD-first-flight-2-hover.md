# YYYY-MM-DD-first-flight-2-hover

- **Session:** [First flight 2](../sessions/YYYY-MM-DD-first-flight-2.md)
- **Test:** Hover (flight)
- **Environment:** [Living room](../environments/living-room.md), hide-and-seek launch point, ___ (time of day)
- **Git commit:** `<hash>` (must be committed before flying)
- **Hardware:** Crazyflie 2.1+, decks: Flow / Multi-ranger / Buzzer, battery #
- **Firmware / cflib:** 2026.08, release 2026.10, unmodified ([ADR-0047](../../decisions/0047-pinned-firmware-release-warn-on-mismatch.md)) / 0.1.34

## Goal and pass criteria
*Written before flying.*

- Goal: Hover through the project's own code with the new take-off and
  landing ([ADR-0048](../../decisions/0048-level-through-the-bad-flow-zone.md)):
  arm, take off to 0.5 m, hover 60 s, land. Land closer to the take-off point
  than in [session 1](2026-11-04-first-flight-1-hover.md) (about 4 cm).
- Also measure (not passed or failed): the mid-air swing from session 1, a
  0.85 Hz circle about 1.2 cm in radius. Compare it with the diagnostic
  block's debug lines ([ADR-0050](../../decisions/0050-diagnostic-log-block-to-the-debug-log.md)):
  attitude (roll, pitch, yaw), the four motor outputs, and the Flow deck's
  surface quality and shutter time.
- Pass if:
  - [ ] The hover test reports done: armed within 2 s, reached 0.5 m (within
        0.1 m) within 5 s, hovered, landed, no error logged.
  - [ ] A 60 s hover is flown, and the drift over it is measured from the
        recording and by eye, and recorded.
  - [ ] **The landing is within 3 cm of the take-off point**, measured with a
        tape measure from the take-off mark to the drone (the drone's own
        estimate drifts).
  - [ ] Motors stop only after touchdown is confirmed. A landing that needed
        the final descent still passes, but is recorded as a finding.
  - [ ] Each `VERIFY` item still open is confirmed or turned into a code change
        or backlog item. *List to be written from the First flight 1 findings.*
- Simulator prediction (or, if not simulated, the mock adapter run): ___

## Pre-flight checklist

- [ ] Bench, Failsafe low and Failsafe high passed
- [ ] Code committed, hash recorded above
- [ ] Mock adapter run of this exact code passed
- [ ] Propellers undamaged, battery fully charged (voltage: ___)
- [ ] Soft landing patch under the drone, flight area clear of people and pets
- [ ] Geofence configured for this space
- [ ] Video recording on

## During the test

- [ ] Mark the take-off point on the floor
- [ ] Start: `.venv\Scripts\python -m crazyflie_behavior.programs.hover --crazyflie --hover-seconds 60`
- [ ] Watch the flight; note anything unexpected while it happens
- [ ] After landing, measure from the take-off mark to the drone with a tape measure
- [ ] Note whether the landing needed the final descent (the log says so)
- [ ] Note whether the drone slid, and whether before or after the propellers stopped
- [ ] Note whether it swings mid-air, and which way it circles seen from above

## Flights

| # | What was run | Result | Data file | Notes |
|---|---|---|---|---|
| 1 | | | | |

## Observations

### Joe

-

### Computed from the log (Claude)

-

## Next
- Code changes:
- ADRs to write or revisit:
- Next session's goal:
