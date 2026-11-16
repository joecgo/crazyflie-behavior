# 2026-11-14-first-flight-6-hover

> Flown 2026-11-14, 14:45 to 15:58 Pacific. Written 2026-11-16 from the
> session doc and the recorded logs. The Flights table and "Computed from the
> logs" are by Claude; pass or fail and the observations are Joe's. Details
> and the hardware changes between flights are in the session doc.

- **Session:** [First flight 6](../sessions/2026-11-14-first-flight-6.md)
- **Test:** Hover (flight): at 0.5 m, then at 0.75 m and 1.0 m, 5 s each
- **Environment:** [Kitchen](../environments/kitchen.md), center of the room. Daylight from 14:45 to 15:20, at night with all lights on from 15:56.
- **Git commit:** `d12975a`; the night flights add one uncommitted change, the final descent at 0.3 m/s, since committed as `18ecb7a` ([ADR-0072](../../decisions/0072-final-descent-0-3-m-per-s.md))
- **Hardware:** Crazyflie 2.1+, decks: Flow / Multi-ranger / Buzzer, battery #: ___. Changed during the session: M4's and M2's propellers, then the M1 motor.
- **Firmware / cflib:** 2026.08 / 0.1.34

## Goal and pass criteria

- Goal: wrap up First flight: take off, hover 5 s and land near the mark, at 0.5, 0.75 and 1.0 m.
- Pass if (set by Joe on 2026-11-16, after flying): every flight takes off, hovers 5 s and lands within 15 cm of the mark. The plan's 5 cm goal was dropped ([ADR-0073](../../decisions/0073-landing-drift-accepted-25-cm-clearance.md)).

## Pre-flight checklist

- [ ] Battery voltage: 3.79-4.04 V before the daylight flights, 4.01-4.10 V before the night flights (logs); the rest of the checklist wasn't recorded

## During the test

- [x] `.venv\Scripts\python -m crazyflie_behavior.programs.hover --crazyflie --hover-seconds 5 --take-off-log`, with `--take-off-height` 0.75 and 1.0 for the heights

## Flights

Distances are Joe's, by the tape, in the drone's direction at the take-off.

| # | Time | What was run | Final descent | Result (logs) | Landing (Joe) | Data file |
|---|---|---|---|---|---|---|
| - | 14:43, 14:44 | 0.5 m | 0.2 m/s | Opening the link timed out | Not flown | `logs/2026-11-14_14-43-08_hover.log`, `..._14-44-10_hover.log` |
| 1 | 14:45 | 0.5 m | 0.2 m/s | Hovered 5 s, landed | 23 cm right | `logs/2026-11-14_14-45-16_hover.log` |
| 2 | 14:51 | 0.5 m, turned 180° | 0.2 m/s | Hovered 5 s, landed | 20 cm right | `logs/2026-11-14_14-51-45_hover.log` |
| 3 | 15:02 | 0.5 m | 0.2 m/s | Landed at 0.26 m in the initial climb: speed estimate not settled | Not measured | `logs/2026-11-14_15-02-33_hover.log` |
| 4 | 15:03 | 0.5 m | 0.2 m/s | Hovered 5 s, landed | About 9 cm | `logs/2026-11-14_15-03-05_hover.log` |
| 5 | 15:05 | 0.5 m, more light | 0.2 m/s | Hovered 5 s, landed | About 25 cm right | `logs/2026-11-14_15-05-38_hover.log` |
| 6 | 15:15 | 0.5 m, M1 motor new | 0.2 m/s | Hovered 5 s, landed | 9 cm back left | `logs/2026-11-14_15-15-49_hover.log` |
| 7 | 15:17 | 0.5 m | 0.2 m/s | Hovered 5 s, landed | 7 cm back right | `logs/2026-11-14_15-17-24_hover.log` |
| 8 | 15:18 | 0.5 m | 0.2 m/s | Hovered 5 s, landed | 16 cm back left | `logs/2026-11-14_15-18-26_hover.log` |
| 9 | 15:20 | 0.5 m | 0.2 m/s | Hovered 5 s, landed | 7 cm back left | `logs/2026-11-14_15-20-43_hover.log` |
| 10 | 15:56 | 0.5 m, night | 0.3 m/s | Hovered 5 s, landed | 10 cm back right | `logs/2026-11-14_15-56-13_hover.log` |
| 11 | 15:56 | 0.75 m, night | 0.3 m/s | Hovered 5 s, landed | 8 cm back right | `logs/2026-11-14_15-56-48_hover.log` |
| 12 | 15:57 | 1.0 m, night | 0.3 m/s | Hovered 5 s, landed | 10 cm back right | `logs/2026-11-14_15-57-56_hover.log` |

## Observations

### Joe

- Result: the flights before the 0.3 m/s final descent (1-9) failed; the
  three night flights at 0.3 m/s (10-12) passed, all within 15 cm.
- Landing distances: the table above. Joe's notes per flight are in the
  session doc.

### Computed from the logs (Claude)

- Flight 3 ended in the initial climb, an abnormal end; Joe flew on after it
  with more light at the mark.
- No tick overruns in the night flights.
- **Exit codes, inferred from the logs** (not captured; the program doesn't
  write its exit code to the log,
  [ADR-0066](../../decisions/0066-hover-program-reports-by-exit-code-only.md)):
  0 for flights 1, 2 and 4-12 ("hovered 5 s", "landed", no error line); 1
  for flight 3 ("Hover test failed: not at 0.50 m after 5 s"); not 0 for the
  two link timeouts (the run ended with a `TimeoutError`).
- The trim is restarted at the start of every final descent after a landing
  approach (session doc, "Remaining tests"), the cause of the landing drift
  accepted in ADR-0073.

## Next

- ADRs: [ADR-0072](../../decisions/0072-final-descent-0-3-m-per-s.md), [ADR-0073](../../decisions/0073-landing-drift-accepted-25-cm-clearance.md).
