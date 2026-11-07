# YYYY-MM-DD-first-flight-2-failsafe-low

- **Session:** [First flight 2](../sessions/YYYY-MM-DD-first-flight-2.md)
- **Test:** Failsafe low (safety)
- **Environment:** [Living room](../environments/living-room.md), hide-and-seek launch point, ___ (time of day)
- **Git commit:** `<hash>` (must be committed before flying)
- **Hardware:** Crazyflie 2.1+, decks: Flow / Multi-ranger / Buzzer, battery #
- **Firmware / cflib:** 2026.08, release 2026.10, unmodified ([ADR-0047](../../decisions/0047-pinned-firmware-release-warn-on-mismatch.md)) / 0.1.34

## Goal and pass criteria
*Written before flying.*

- Goal: Prove the real failsafe lands the drone from the initial climb
  ([ADR-0049](../../decisions/0049-failsafe-low-fires-its-fault-during-the-initial-climb.md)).
  The failsafe program (`programs.failsafe --crazyflie --fault-at climb`)
  takes off to 0.5 m; once the down range has been at least 0.10 m for two
  readings in a row, a wrapper forges a low battery reading. The
  real pre-check fails, the climb stops and the final descent lands the
  drone. Fully charged battery (about 4.2 V): session 1's real battery
  tripped before the forged fault both times ([ADR-0051](../../decisions/0051-battery-flight-limit-and-take-off-limit.md)).
- Pass if:
  - [ ] The log shows `FAULT INJECTED: battery voltage forged`, and the
        battery that tripped the pre-check is the forged 3.00 V, not the real one.
  - [ ] The pre-check fails with the battery message, and a landing is sent.
  - [ ] The climb stops and the final descent starts from where the drone is,
        with no landing approach (the log says so).
  - [ ] The drone lands and its motors stop (seen by the operator), and the
        program exits with code 0.
  - [ ] The log has no "Failsafe test failed" error.
  - [ ] The landing needed no help from the kill switch or rescue landing.
- Simulator prediction, if simulated: ___

## Pre-flight checklist

- [ ] Bench passed
- [ ] Code committed, hash recorded above, the same commit as the session doc's mock runs
- [ ] Propellers undamaged, battery charged (voltage: ___; below 3.62 V the take-off is refused, [ADR-0051](../../decisions/0051-battery-flight-limit-and-take-off-limit.md))
- [ ] Soft landing patch under the drone, flight area clear of people and pets
- [ ] Geofence configured for this space
- [ ] Video recording on

## During the test

- [ ] Start: `.venv\Scripts\python -m crazyflie_behavior.programs.failsafe --crazyflie --fault-at climb`
- [ ] Watch the climb and the landing; note anything unexpected while it happens (sideways drift during the climb, where it stopped climbing)
- [ ] Note whether the drone landed by the failsafe, or by the climb's time limit or settle cap (the log says which)
- [ ] Note whether touchdown was confirmed or the final descent ran out its time limit

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
