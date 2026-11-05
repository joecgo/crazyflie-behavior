# 2026-11-04-first-flight-1-failsafe-high

> Flown on 2026-11-04 at 16:28 Pacific. The Flights table and "Computed from
> the logs" are by Claude, from the recorded logs. Pass or fail, and Joe's own
> observations, are Joe's to write.

- **Session:** [First flight 1](../sessions/2026-11-04-first-flight-1.md)
- **Test:** Failsafe high (safety)
- **Environment:** [Living room](../environments/living-room.md), hide-and-seek launch point, all lights on. Time of day / sunlight: ___
- **Git commit:** `de24a7c` (must be committed before flying)
- **Hardware:** Crazyflie 2.1+, decks: Flow / Multi-ranger / Buzzer, battery #
- **Firmware / cflib:** 2026.08, release 2026.10, unmodified ([ADR-0047](../../decisions/0047-pinned-firmware-release-warn-on-mismatch.md)) / 0.1.34

## Goal and pass criteria
*Written before flying.*

- Goal: Prove the real failsafe lands the drone. The failsafe program
  (`programs.failsafe --crazyflie --height-meters 0.5`, ADR-0041) takes off to
  0.5 m, hovers about 3 s, then a wrapper forges a low battery reading. The
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
- [ ] Note whether touchdown was confirmed: the log warns "Landing time is up but touchdown isn't confirmed" if the final descent started, and "Touchdown never confirmed by the down range" if it ran out its time limit

## Flights

| # | What was run | Result | Data file | Notes |
|---|---|---|---|---|
| 0 | `failsafe --height-meters 0.5` (mock) | Fault injected, pre-check failed, `Land()`, exit 0 | `logs/2026-11-04_16-27-26_failsafe.log` | |
| 1 | `failsafe --crazyflie --height-meters 0.5` | The **real** battery (3.37 V) failed the pre-check 1 s after take-off, at 0.06 m; no fault injected | `logs/2026-11-04_16-27-54_failsafe.log` | Joe: landed, motors stopped on their own |

## Observations

### Joe (said during the session)

- It landed and the motors stopped on their own.

### Computed from the logs (Claude)

- **The forged-battery path wasn't exercised, and 0.5 m wasn't reached.**
  The battery read 3.76-3.77 V at rest and 3.37 V 20 ticks after `TakeOff`,
  at 0.06 m, during the climb. The real low-battery failsafe landed it.
- **Touchdown:** not confirmed by the down range; the final descent ran.
- **Before the flight,** the Flow deck's motion flag was set in about two
  thirds of the samples (quality 22-36); the position variance stayed at
  about 1e-4.

## Next
- Code changes: none yet.
- ADRs to write or revisit: backlog #50 (low-battery limit under load), #51
  (touchdown never confirmed).
- Next session's goal: fly again on a fully charged battery, after Failsafe
  low passes.
