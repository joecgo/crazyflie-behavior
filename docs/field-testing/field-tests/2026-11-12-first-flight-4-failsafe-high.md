# 2026-11-12-first-flight-4-failsafe-high

> Flown 2026-11-12, 16:05 Pacific. The Flights table and "Computed from the
> logs" are by Claude, from the recorded logs. Pass or fail, and Joe's own
> observations, are Joe's to write.

- **Session:** [First flight 4](../sessions/2026-11-12-first-flight-4.md)
- **Test:** Failsafe high (safety)
- **Environment:** [Kitchen](../environments/kitchen.md), center of the room, all lights on, cloudy daylight.
- **Git commit:** `8d7bc29`
- **Hardware:** Crazyflie 2.1+, decks: Flow / Multi-ranger / Buzzer, battery #: ___
- **Firmware / cflib:** 2026.08 (as in session 3, not re-read) / 0.1.34

## Goal and pass criteria
*Written before flying.*

- Goal: the session doc's plan covers it; as in
  [First flight 3's log](2026-11-09-first-flight-3-failsafe-high.md): the real
  failsafe lands the drone from a hover.
- Pass if: the fault fires after a few seconds of hover, the pre-check fails
  on the battery, the drone lands, and the log has no "Failsafe test failed".
- Flown after Failsafe low failed, against the README's rule (Joe's call).

## Pre-flight checklist

- [ ] Battery voltage: 3.89 V at rest (log); the rest of the checklist wasn't recorded

## During the test

- [x] `.venv\Scripts\python -m crazyflie_behavior.programs.failsafe --crazyflie --fault-at hover`

## Flights

| # | What was run | Result | Data file | Notes |
|---|---|---|---|---|
| 1 | `failsafe --crazyflie --fault-at hover` | Failed: landed at 0.26 m in the initial climb, no fault | `logs/2026-11-12_16-05-06_failsafe.log` | |

## Observations
What happened, especially anything surprising. Include numbers.

### Joe

- Result: fail.
- It landed 59 cm from the mark (Joe measured where it landed).

### Computed from the logs (Claude)

- Take-off with image quality 34 ("low light"), initial climb at 0.2 m/s.
  "The horizontal speed estimate hasn't settled by 0.25 m. Landing." Final
  descent from 0.259 m, touchdown confirmed. No `FAULT INJECTED`, then
  "Failsafe test failed: not at 0.50 m after 5 s (at 0.02 m)". 112 ticks,
  0 overruns.
- The estimate before the reset was (4.2, -15.2) m at 2.0 m/s (backlog #81).
- The settle-cap landing before the hover happened in First flight 3's Failsafe
  high too (backlog #78).

## Next
- Code changes:
- ADRs to write or revisit: backlog #68, #78, #81
- Next session's goal: Joe to decide.
