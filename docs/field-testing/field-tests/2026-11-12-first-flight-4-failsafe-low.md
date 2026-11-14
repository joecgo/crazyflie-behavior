# 2026-11-12-first-flight-4-failsafe-low

> Flown 2026-11-12, 16:02 Pacific. The Flights table and "Computed from the
> logs" are by Claude, from the recorded logs. Pass or fail, and Joe's own
> observations, are Joe's to write.

- **Session:** [First flight 4](../sessions/2026-11-12-first-flight-4.md)
- **Test:** Failsafe low (safety)
- **Environment:** [Kitchen](../environments/kitchen.md), center of the room, all lights on, cloudy daylight.
- **Git commit:** `8d7bc29`
- **Hardware:** Crazyflie 2.1+, decks: Flow / Multi-ranger / Buzzer, battery #: ___
- **Firmware / cflib:** 2026.08 (as in session 3, not re-read) / 0.1.34

## Goal and pass criteria
*Written before flying.*

- Goal: the session doc's plan covers it; the test is as in
  [First flight 3's log](2026-11-09-first-flight-3-failsafe-low.md)
  ([ADR-0049](../../decisions/0049-failsafe-low-fires-its-fault-during-the-initial-climb.md)).
- Pass if (the criteria of First flight 3, drift not among them):
  - [x] The log shows `FAULT INJECTED: battery voltage forged`
  - [x] The pre-check fails with the battery message (3.00 V), and a landing is sent
  - [x] `Landing during the initial climb: no landing approach.`
  - [x] No "Failsafe test failed" error; touchdown confirmed
  - [ ] Exit code 0: not captured
  - [x] `The drone reports not flying and isn't locked`

## Pre-flight checklist

- [ ] Battery voltage: 3.92 V at rest (log); the rest of the checklist wasn't recorded

## During the test

- [x] `.venv\Scripts\python -m crazyflie_behavior.programs.failsafe --crazyflie --fault-at climb`

## Flights

| # | What was run | Result | Data file | Notes |
|---|---|---|---|---|
| 1 | `failsafe --crazyflie --fault-at climb` | Fault fired, landed | `logs/2026-11-12_16-02-53_failsafe.log` | One flight, no second flight without a power cycle |

## Observations
What happened, especially anything surprising. Include numbers.

### Joe

- Result: fail.
- It landed 20 cm forward and right of the mark (Joe measured where it landed).

### Computed from the logs (Claude)

- Take-off at 16:02:58 with the Flow deck's image quality 31 ("low light"); the
  fault 0.6 s into the climb, the pre-check failed at 3.00 V, `Land()`; final
  descent level from 0.093 m; touchdown confirmed; 14 ticks, 0 overruns.
- The estimate before the reset at connect was (-10.9, -64.0, 0.02) m at
  4.8 m/s, implausible on the floor (backlog #81).

## Analysis (Claude, 2026-11-13)

From the logs and the firmware 2026.08 source, not observations. Scripts in
`drafts/ff4/` (not in the repository).

- The flight was short and low: the fault came 0.6 s after the take-off with
  the down range at 0.09 m, and touchdown was confirmed at 1.5 s. The
  snapshots end with the fault (the tick loop stops and the adapter lands the
  drone), so the position estimate covers only 0.3 s, all under 0.10 m, where
  the flow model overstates movement.
- The same front-right torque as in Failsafe high (the old M1 propeller): the
  rate integrals reached -1,440 (roll) and +1,518 (pitch) in 0.6 s.
- **Sideways movement:** the logged tilt gives about 7 cm forward and right
  over the second in the air (rough). Joe measured 20 cm forward and right:
  the direction agrees, and most of the distance is where the logs can't see,
  under 0.10 m and on the floor.
- **Battery at spin-up:** 3.22 V in the first reading, from 3.91 V at rest.

## Next
- Code changes:
- ADRs to write or revisit: backlog #68 (take-off drift)
- Next session's goal:
