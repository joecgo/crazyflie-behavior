# 2026-11-14-first-flight-6-failsafe-high

> Flown 2026-11-14, 15:55 Pacific. Written 2026-11-16 from the session doc
> and the recorded log. The Flights table and "Computed from the logs" are by
> Claude; pass or fail and the observations are Joe's.

- **Session:** [First flight 6](../sessions/2026-11-14-first-flight-6.md)
- **Test:** Failsafe high (safety)
- **Environment:** [Kitchen](../environments/kitchen.md), center of the room, all lights on, at night.
- **Git commit:** `d12975a` plus one uncommitted change, the final descent at 0.3 m/s, since committed as `18ecb7a` ([ADR-0072](../../decisions/0072-final-descent-0-3-m-per-s.md))
- **Hardware:** Crazyflie 2.1+, decks: Flow / Multi-ranger / Buzzer, battery #: ___. New propellers on M2 and M4, M1 motor replaced earlier in the session.
- **Firmware / cflib:** 2026.08 / 0.1.34

## Goal and pass criteria

- Goal: the failsafe lands the drone after a hover of about 3 s at 0.5 m.
- Pass if (set by Joe on 2026-11-16, after flying): the fault fires, the drone lands and its motors stop, within 15 cm of the mark.
  - [x] `FAULT INJECTED: battery voltage forged`
  - [x] Touchdown confirmed; `The drone reports not flying and isn't locked`
  - [x] Within 15 cm: 7 cm (Joe)

## Pre-flight checklist

- [ ] Battery voltage: 4.01-4.10 V before each night flight (logs); the rest of the checklist wasn't recorded

## During the test

- [x] `.venv\Scripts\python -m crazyflie_behavior.programs.failsafe --crazyflie --fault-at hover`

## Flights

| # | What was run | Result | Data file | Notes |
|---|---|---|---|---|
| 1 | `failsafe --crazyflie --fault-at hover` | Fault fired, landed | `logs/2026-11-14_15-55-05_failsafe.log` | Final descent 0.3 m/s |

## Observations

### Joe

- Result: pass.
- Landed 7 cm back right of the mark.

### Computed from the logs (Claude)

- Exit code 0, inferred from the log (not captured): fault injected, the
  pre-check failed, no "Failsafe test failed" or other error line.
- Fault at 15:55:15.3, touchdown confirmed 2.3 s later.
- Hover pitch trim about -900. Like the hovers, it was restarted at the start
  of the final descent (session doc, "Remaining tests").

## Next

- ADRs: [ADR-0073](../../decisions/0073-landing-drift-accepted-25-cm-clearance.md) (landing drift accepted).
