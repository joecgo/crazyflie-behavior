# YYYY-MM-DD-first-flight-2-failsafe-high

- **Session:** [First flight 2](../sessions/YYYY-MM-DD-first-flight-2.md)
- **Test:** Failsafe high (safety)
- **Environment:** [Living room](../environments/living-room.md), hide-and-seek launch point, ___ (time of day)
- **Git commit:** `<hash>` (must be committed before flying)
- **Hardware:** Crazyflie 2.1+, decks: Flow / Multi-ranger / Buzzer, battery #
- **Firmware / cflib:** 2026.08, release 2026.10, unmodified ([ADR-0047](../../decisions/0047-pinned-firmware-release-warn-on-mismatch.md)) / 0.1.34

## Goal and pass criteria
*Written before flying.*

- Goal: Prove the real failsafe lands the drone, now with the new take-off
  and landing ([ADR-0048](../../decisions/0048-level-through-the-bad-flow-zone.md)).
  The failsafe program (`programs.failsafe --crazyflie --fault-at hover`,
  ADR-0041) takes off to 0.5 m, hovers about 3 s, then a wrapper forges a low
  battery reading. The real pre-check fails and the failsafe lands the drone.
- Also check the take-off: this is the first full initial climb (Failsafe low
  lands during it, [ADR-0056](../../decisions/0056-adr-0048-as-built.md)).
  Record the settle height and the final descent height from the log, whether
  the cap tripped, and the sideways shift at take-off.
- Pass if:
  - [ ] The initial climb ends normally: the log shows `Initial climb done:
        settle height ___ m, final descent height ___ m`, with no warning that
        the speed hasn't settled (the cap) or that the climb ran out of time.
  - [ ] The log shows `FAULT INJECTED: battery voltage forged`.
  - [ ] The pre-check fails with the battery message, and a landing is sent.
  - [ ] The drone lands and its motors stop (seen by the operator: the exit
        code can't show it, ADR-0041), and the program exits with code 0.
  - [ ] The log has no "Failsafe test failed" error (the time limit landing
        the drone is a failed test).
  - [ ] The landing needed no help from the kill switch or rescue landing.
  - [ ] The final descent was level (`Final descent: level, from ___ m by the
        down range`) and ended with `Touchdown confirmed`. The slow descent or
        the final descent's time limit still passes, but is recorded as a finding.
- Simulator prediction, if simulated: ___

## Pre-flight checklist

- [ ] Bench and Failsafe low passed
- [ ] Code committed, hash recorded above, the same commit as the session doc's mock runs
- [ ] Propellers undamaged, battery fully charged (voltage: ___; below 3.62 V the take-off is refused, [ADR-0051](../../decisions/0051-battery-flight-limit-and-take-off-limit.md))
- [ ] Soft landing patch under the drone, flight area clear of people and pets
- [ ] Geofence configured for this space
- [ ] Video recording on

## During the test

- [ ] Mark the take-off point on the floor
- [ ] Start: `.venv\Scripts\python -m crazyflie_behavior.programs.failsafe --crazyflie --fault-at hover`
- [ ] Watch the take-off and hover, then the landing; note anything unexpected while it happens
- [ ] Note how far the drone shifted sideways during the take-off: from the take-off mark to below the drone at 0.5 m (the video helps)
- [ ] Note whether the drone landed by the failsafe or by the time limit (the log says which)
- [ ] Note whether touchdown was confirmed (the log warns if it wasn't)

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
