# 2026-11-12-first-flight-4-hover

> Flown 2026-11-12, 16:25 to 16:27 Pacific, at night. The Flights table and
> "Computed from the logs" are by Claude, from the recorded logs. Pass or
> fail, and Joe's own observations, are Joe's to write.

- **Session:** [First flight 4](../sessions/2026-11-12-first-flight-4.md)
- **Test:** Hover (flight), with chirps
- **Environment:** [Kitchen](../environments/kitchen.md), center of the room, all lights on, night (Joe).
- **Git commit:** `8d7bc29`
- **Hardware:** Crazyflie 2.1+, decks: Flow / Multi-ranger / Buzzer, battery #: ___
- **Firmware / cflib:** 2026.08 (as in session 3, not re-read) / 0.1.34

## Goal and pass criteria
*Written before flying.*

- Goal: the session doc's plan covers it; as in
  [First flight 3's Hover](2026-11-09-first-flight-3-hover.md): a 60 s hover
  with chirps.
- Pass if: Joe's call. The program's own rule ([ADR-0062](../../decisions/0062-hover-program-fails-when-the-hover-is-cut-short.md)):
  exit code 0 unless the hover was cut short; the code was not captured.

## During the test

- [x] `.venv\Scripts\python -m crazyflie_behavior.programs.hover --crazyflie --hover-seconds 60 --chirp --climb-speed 0.4` (no `--take-off-log`)

## Flights

| # | What was run | Result | Data file | Notes |
|---|---|---|---|---|
| 1 | `hover --crazyflie --hover-seconds 60 --chirp --climb-speed 0.4` | Hovered the full 60 s, landed | `logs/2026-11-12_16-25-49_hover.log` | Battery 3.76 V at rest, 3.20 V at the end |

## Observations
What happened, especially anything surprising. Include numbers.

### Joe

- Result: pass.
- Flew pretty straight on take-off, drifted left on the landing, landed 6 cm from the mark.
- Heard the chirps, but doesn't remember hearing the last one, the Charge melody at the end. Not a reason to fail the test: a bug to fix later (backlog #92).

### Computed from the logs (Claude)

- Take-off with image quality 22 ("low light"); initial climb at 0.4 m/s
  ended normally (settle 0.112 m, final descent height 0.162 m); hovered at
  0.41 m from 16:26:00 to 16:27:00, with a chirp about every 5 s. The cap,
  the time limit and the safety layer did not cut it short.
- Final descent level from 0.290 m, touchdown confirmed, "not flying and
  isn't locked". 1360 ticks, 2 overruns, worst lateness 76 ms (99th
  percentile 2.6 ms).
- **Battery:** 3.76 V at rest on the floor (above the 3.62 V take-off limit,
  [ADR-0051](../../decisions/0051-battery-flight-limit-and-take-off-limit.md)),
  3.34 V two seconds into the hover, about 3.25-3.28 V for most of it, and
  3.20 V as the landing began, when the safety layer logged "Safety pre-check
  failed: battery at 3.20 V (land below 3.20 V). Landing." The drone was
  already landing.
- Estimate before the reset at connect: (4.6, -0.06) m at 0.01 m/s.

## Next
- Code changes:
- ADRs to write or revisit: backlog #91, ADR-0051 (a take-off at 3.76 V reached the landing limit in a 60 s hover)
- Next session's goal:
