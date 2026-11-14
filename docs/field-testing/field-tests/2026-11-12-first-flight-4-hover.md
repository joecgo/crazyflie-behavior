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
  0.50 m by the down range (mean) from 16:26:00 to 16:27:00, with a chirp
  about every 5 s (corrected 2026-11-13: first written as 0.41 m, the height
  at which the hover test counted the drone as there). The cap,
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

## Analysis (Claude, 2026-11-13)

From the logs and the firmware 2026.08 source, not observations. Scripts in
`drafts/ff4/` (not in the repository).

- **Sideways movement, by the position estimate** (corrected for the flow
  model below 0.10 m, with the estimate as logged in brackets): the take-off
  moved the drone about 6 cm forward and right (12) by the time it hovered.
  Over the 59 s hover it ended 3 cm from where it started, inside a patch of
  6 x 7.5 cm. The landing approach moved it 4 cm. The final descent isn't in
  the snapshots (next point); by the logged tilt and the speed it started
  with, it went 6-14 cm to the left: rough, but the direction Joe saw.
- **The landing finished inside `disconnect()`.** 0.05 s into the final
  descent the battery read 3.20 V (braking from 0.46 m/s raises the thrust),
  the safety pre-check failed and the tick loop stopped, so the adapter's
  shutdown landing flew the last 1.3 s. The hover test's "landed" line never
  came, and the final descent has no snapshots (backlog #91).
- **The landing approach ended at 0.280 m,** 12 cm above the final descent
  height of 0.162 m (backlog #93; chart in the
  [Take-off speeds log](2026-11-12-first-flight-4-take-off-speeds.md)).
- **Velocity uncertainty**
  ([ADR-0064](../../decisions/0064-in-flight-flow-limit-grows-with-height.md)):
  mean 0.031 m/s, highest 0.034, flat over the 60 s, against a limit of about
  0.05 m/s at 0.5 m: 68% of the limit at most. Across this session's flights
  it grew about 0.05 m/s per meter of height (0.012 at 0.1 m, 0.031 at
  0.5 m), half the growth of the limit; nothing is measured above 0.52 m.
- **Battery:** 3.31 V under load early in the hover, falling 1.0 mV/s (0.06 V
  a minute); mean 3.28 V, a sag of 0.49 V from the 3.77 V at rest; 3.61 V at
  rest after landing, just under the 3.62 V take-off limit. At spin-up the
  first two readings were 3.11 and 3.17 V.
- **The two overruns** (ticks 51.6 and 76.2 ms late, 32 s apart): the
  diagnostic block's lines from cflib's thread paused at the same moments, so
  the whole process stalled, not only the tick loop. The position estimate
  was 83 and 100 ms old at those ticks; the stale limit is 0.25 s (backlog
  #70).
- **Thrust and balance:** the hover's thrust command averaged 43,458, within
  about 1% of the thrust base. Roll and pitch were balanced (as a
  centre-of-mass offset, 0.04 mm); (m1+m3)/(m2+m4) was 1.24 (backlog #83).
- **The estimate on the floor:** the 5 s chirp wait moved it 3 cm before the
  take-off (session 3: 2.2 m, backlog #81).

## Next
- Code changes:
- ADRs to write or revisit: backlog #91, ADR-0051 (a take-off at 3.76 V reached the landing limit in a 60 s hover); backlog #93 (the landing approach), #70 (the two overruns)
- Next session's goal:
