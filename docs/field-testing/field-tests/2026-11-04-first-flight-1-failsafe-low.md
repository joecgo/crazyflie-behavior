# YYYY-MM-DD-first-flight-1-failsafe-low

> **DRAFT.** Date and commit are pending. Nothing below the pre-flight
> section has been filled in.

- **Session:** [First flight 1](../sessions/YYYY-MM-DD-first-flight-1.md)
- **Test:** Failsafe low (safety)
- **Environment:** [Living room](../environments/living-room.md), hide-and-seek launch point, all lights on. Time of day / sunlight: ___
- **Git commit:** `<hash>` (must be committed before flying)
- **Hardware:** Crazyflie 2.1+, decks: Flow / Multi-ranger, battery #
- **Firmware / cflib:** {firmware version} / {cflib version}

## Goal and pass criteria
*Written before flying.*

- Goal: Prove the real failsafe lands the drone. The failsafe program
  (`programs.failsafe --crazyflie --height-meters 0.1`, ADR-0041) takes off to
  0.1 m, hovers about 3 s, then a wrapper forges a low battery reading. The
  real pre-check fails and the failsafe lands the drone.
- Pass if:
  - [ ] The log shows `FAULT INJECTED: battery voltage forged`.
  - [ ] The pre-check fails with the battery message, and a landing is sent.
  - [ ] The drone lands and its motors stop (seen by the operator: the exit
        code can't show it, ADR-0041), and the program exits with code 0.
  - [ ] The log has no "Failsafe test failed" error (the time limit landing
        the drone is a failed test).
  - [ ] The landing needed no help from the kill switch or rescue landing.

## Pre-flight checklist

- [ ] Bench passed
- [ ] Code committed, hash recorded above
- [ ] Mock adapter run of this exact code passed (`programs.failsafe --height-meters 0.1`)
- [ ] Propellers undamaged, battery charged (voltage: ___)
- [ ] Soft landing patch under the drone, flight area clear of people and pets
- [ ] Geofence configured for this space
- [ ] Video recording on

## During the test

- [ ] Start: `.venv\Scripts\python -m crazyflie_behavior.programs.failsafe --crazyflie --height-meters 0.1`
- [ ] Watch the take-off and hover, then the landing; note anything unexpected while it happens
- [ ] Note whether the drone landed by the failsafe or by the time limit (the log says which)
- [ ] Note whether touchdown was confirmed: the log warns "Landing time is up but touchdown isn't confirmed" if the final descent started, and "Touchdown never confirmed by the down range" if it ran out its time limit

## Flights

| # | What was run | Result | Data file | Notes |
|---|---|---|---|---|
| 1 | | | | |

## Observations
What happened, especially anything surprising. Include numbers.

## Next
- Code changes:
- ADRs to write or revisit:
- Next session's goal:
