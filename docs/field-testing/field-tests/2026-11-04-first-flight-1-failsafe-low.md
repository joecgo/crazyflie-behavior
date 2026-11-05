# 2026-11-04-first-flight-1-failsafe-low

> Flown twice on 2026-11-04, 16:23 and 16:26 Pacific. The Flights table and
> "Computed from the logs" are by Claude, from the recorded logs. Pass or
> fail, and Joe's own observations, are Joe's to write.

- **Session:** [First flight 1](../sessions/2026-11-04-first-flight-1.md)
- **Test:** Failsafe low (safety)
- **Environment:** [Living room](../environments/living-room.md), hide-and-seek launch point, all lights on. Time of day / sunlight: ___
- **Git commit:** `de24a7c` (must be committed before flying)
- **Hardware:** Crazyflie 2.1+, decks: Flow / Multi-ranger / Buzzer, battery #
- **Firmware / cflib:** 2026.08, release 2026.10, unmodified ([ADR-0047](../../decisions/0047-pinned-firmware-release-warn-on-mismatch.md)) / 0.1.34

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
| 0 | `failsafe --height-meters 0.1` (mock) | Fault injected, pre-check failed, `Land()`, exit 0 | `logs/2026-11-04_16-22-02_failsafe.log` | |
| 1 | `failsafe --crazyflie --height-meters 0.1` | The **real** battery (3.39 V) failed the pre-check about 2 s in; no fault injected | `logs/2026-11-04_16-23-14_failsafe.log` | Joe: landed, motors stopped on their own |
| 2 | Same | Same, real battery 3.38 V after 41 ticks | `logs/2026-11-04_16-26-02_failsafe.log` | Joe: landed, motors stopped on their own |

## Observations

### Joe (said during the session)

- Both flights landed and the motors stopped on their own.

### Computed from the logs (Claude)

- **The forged-battery path wasn't exercised.** The battery read 3.78-3.79 V
  at rest and sagged to 3.45 V within 1 s of take-off, then under 3.40 V
  about 2 s in, before the fault's 3 s of hovering. The real low-battery
  failsafe landed the drone both times.
- **Height:** bounced between 0.004 and 0.094 m around the 0.1 m target;
  "hovering" was declared at 0.05-0.06 m (within the 5 cm tolerance).
- **Touchdown:** "Landing time is up but touchdown isn't confirmed;
  descending slowly" both times, so the final descent (ADR-0019) ran; then
  the down range confirmed touchdown (backlog #51).
- **Before flight 1,** the Flow deck check showed the motion flag set in every
  sample and the velocity variance steady at about 1e-4.

## Next
- Code changes: none yet.
- ADRs to write or revisit: backlog #50 (low-battery limit under load), #51
  (the landing logs and the final descent), #52 (height at 0.1 m).
- Next session's goal: fly again on a fully charged battery (about 4.2 V).
