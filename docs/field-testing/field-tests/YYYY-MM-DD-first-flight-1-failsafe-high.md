# YYYY-MM-DD-first-flight-1-failsafe-high

> **DRAFT.** Date and commit are pending. The failsafe program isn't built
> yet (next-up.md, item 5). Nothing below the pre-flight section has been
> filled in.

- **Session:** [First flight 1](../sessions/YYYY-MM-DD-first-flight-1.md)
- **Test:** Failsafe high (safety)
- **Environment:** [Living room](../environments/living-room.md), hide-and-seek launch point, all lights on. Time of day / sunlight: ___
- **Git commit:** `<hash>` (must be committed before flying)
- **Hardware:** Crazyflie 2.1+, decks: Flow / Multi-ranger, battery #
- **Firmware / cflib:** {firmware version} / {cflib version}

## Goal and pass criteria
*Written before flying.*

- Goal: Prove the real failsafe lands the drone. The failsafe program
  (`programs.failsafe --crazyflie --height-meters 0.5`, ADR-0041) takes off to
  0.5 m, hovers about 3 s, then a wrapper forges a low battery reading. The
  real pre-check fails and the failsafe lands the drone.
- Pass if:
  - [ ] The log shows `FAULT INJECTED: battery voltage forged`.
  - [ ] The pre-check fails with the battery message, and a landing is sent.
  - [ ] The drone lands and its motors stop, and the program reports done
        (not the time limit landing it: that is a failed test).
  - [ ] The landing needed no help from the kill switch or rescue landing.

## Pre-flight checklist

- [ ] Bench and Failsafe low passed
- [ ] Code committed, hash recorded above
- [ ] Mock adapter run of this exact code passed (`programs.failsafe --height-meters 0.5`)
- [ ] Propellers undamaged, battery charged (voltage: ___)
- [ ] Soft landing patch under the drone, flight area clear of people and pets
- [ ] Geofence configured for this space
- [ ] Video recording on

## During the test

- [ ] Start: `.venv\Scripts\python -m crazyflie_behavior.programs.failsafe --crazyflie --height-meters 0.5`
- [ ] Watch the take-off and hover, then the landing; note anything unexpected while it happens
- [ ] Note whether the drone landed by the failsafe or by the time limit (the log says which)

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
