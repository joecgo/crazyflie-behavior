# 2026-11-12-first-flight-4-window-bench

> Flown 2026-11-12, about 15:56 to 16:00 Pacific. The Flights table and
> "Computed from the logs" are by Claude, from the recorded logs. Pass or
> fail, and Joe's own observations, are Joe's to write.

- **Session:** [First flight 4](../sessions/2026-11-12-first-flight-4.md)
- **Test:** Sensor characterization (the range sensors near a window)
- **Environment:** [Kitchen](../environments/kitchen.md), all lights on, cloudy daylight, at a window (which one: to confirm). Glass, with a mesh screen in the first runs.
- **Git commit:** `8d7bc29`
- **Hardware:** Crazyflie 2.1+, decks: Flow / Multi-ranger / Buzzer, battery #: ___
- **Firmware / cflib:** 2026.08 (as in session 3, not re-read) / 0.1.34

## Goal and pass criteria
*Written before flying.*

- Goal (Joe): see how the front, back, left and right range sensors work near
  a window. Held by hand, no flight, the bench program.
- Pass if: none; this is a measurement.

## During the test

- [x] `.venv\Scripts\python -m crazyflie_behavior.programs.bench --crazyflie`, the drone held at the window

## Flights

| # | What was run | Result | Data file | Notes |
|---|---|---|---|---|
| 1 | `bench --crazyflie --take-off-log` | Doesn't count | `logs/2026-11-12_15-54-39_bench.log` | Joe wasn't at the window until the end |
| 2 | `bench --crazyflie` | Doesn't count | `logs/2026-11-12_15-56-45_bench.log` | About 14 s; no clear order of sides |
| 3 | `bench --crazyflie` | Front at the glass, with a mesh screen | `logs/2026-11-12_15-57-51_bench.log` | 12 s, held still |
| 4 | `bench --crazyflie` | Front at the glass, screen out of the way | `logs/2026-11-12_15-59-24_bench.log` | 11 s, held still |

## Observations
What happened, especially anything surprising. Include numbers.

### Joe

- Run 3 had a mesh screen in front of the window.
- Run 4: the drone was about 9 inches (23 cm) from the glass.
- "It was hitting stuff outside the window I think; I'll assume it can't see the window."

### Computed from the logs (Claude)

- **Run 3 (mesh screen):** front 0.04 m, steady, never out of range.
- **Run 4 (about 23 cm from the glass):** front 0.42-0.45 m, steady, 3 of about
  110 samples out of range. That's about 20 cm farther than Joe's distance.
  Back 0.69-0.70 m, right 0.86 m, left 0.19 m, up 2.01 m, all steady.
- Back, left and right at the glass were not tested.
- Tick loop, run 3: 0 overruns, worst lateness 9.2 ms. Run 2: 2 overruns,
  worst 54 ms. Run 4: 0 overruns, worst 40 ms, 99th percentile 32.7 ms.
- Reading the result as "the Multi-ranger doesn't see the glass" is Joe's
  assumption; these runs don't prove it.

## Next
- Code changes: none yet.
- ADRs to write or revisit: the geofence must keep the drone away from windows (backlog #90).
- Next session's goal: back, left and right at the glass at measured distances (10, 20, 40 cm).
