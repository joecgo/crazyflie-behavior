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
| 2 | Same, on a charged battery, with a flashlight on the floor aimed at the take-off spot | `FAULT INJECTED` after about 3 s of hover at 0.51-0.54 m; the pre-check failed on the forged 3.20 V; `Land()` | `logs/2026-11-04_17-11-59_failsafe.log` | Joe: landed, motors stopped on their own |

## Observations

### Joe (said during the session)

- Flights 1 and 2: it landed and the motors stopped on their own.

### Computed from the logs, flight 2 (Claude)

- **All of the log's criteria met:** `FAULT INJECTED`, the battery message,
  `Land()`, no "Failsafe test failed". The exit code wasn't shown.
- Battery 4.05 V on the floor, 3.63-3.67 V while climbing and hovering: well
  above 3.40 V on a full charge.
- Climbed to 0.45 m in about 2 s, then held 0.51-0.54 m.
- Touchdown: the final descent ran, then the down range confirmed touchdown
  (backlog #51).
- Before it: with the room's own light, the Flow deck's surface quality was
  12-28 and the position variance grew, even when the drone was slid by hand.
  With the flashlight, quality was 87-103 and the variance held at about
  2e-4. With a clear view and the drone still, the motion flag reads "no
  motion" in most samples; the variance is the better pre-flight check.

### Computed from the logs, flight 1 (Claude)

- **The forged-battery path wasn't exercised, and 0.5 m wasn't reached.**
  The battery read 3.76-3.77 V at rest and 3.37 V 20 ticks after `TakeOff`,
  at 0.06 m, during the climb. The real low-battery failsafe landed it.
- **Touchdown:** the final descent ran, then the down range confirmed
  touchdown.
- **Before the flight,** the Flow deck's motion flag was set in about two
  thirds of the samples (quality 22-36); the position variance stayed at
  about 1e-4.

## Next
- Code changes: none yet.
- ADRs to write or revisit: backlog #50 (low-battery limit under load), #51
  (the landing logs and the final descent).
- Next session's goal: fly again on a fully charged battery, after Failsafe
  low passes.
