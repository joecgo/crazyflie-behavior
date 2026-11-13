# 2026-11-12-first-flight-4-bench

> Flown 2026-11-12, about 15:49 to 15:55 Pacific. The Flights table and
> "Computed from the logs" are by Claude, from the recorded logs. Pass or
> fail, and Joe's own observations, are Joe's to write.

- **Session:** [First flight 4](../sessions/2026-11-12-first-flight-4.md)
- **Test:** Bench (calibration)
- **Environment:** [Kitchen](../environments/kitchen.md), center of the room, all lights on, cloudy daylight.
- **Git commit:** `8d7bc29`
- **Hardware:** Crazyflie 2.1+, decks: Flow / Multi-ranger / Buzzer, battery #: ___
- **Firmware / cflib:** 2026.08 (as in session 3, not re-read) / 0.1.34

## Goal and pass criteria
*Written before flying.*

- Goal: the session doc's plan has the reasons. The reason to run it: the first
  bench since the controller block and take-off block were added
  ([ADR-0063](../../decisions/0063-take-off-and-controller-log-blocks.md),
  [ADR-0065](../../decisions/0065-take-off-block-runs-from-connect-and-each-take-off.md)),
  to see that every value streams, the range sensors react to a covered
  sensor, and `--take-off-log` adds no visible lag.
- Pass if: Joe's call afterwards, "the sensors seem to work".

## Pre-flight checklist

- [ ] Code committed, hash recorded above, the same commit as the session doc's mock runs
- [ ] Battery voltage: 4.00 V at rest (log)
- [ ] The rest of the checklist wasn't recorded

## During the test

- [x] Bench 1: `.venv\Scripts\python -m crazyflie_behavior.programs.bench --crazyflie`; Joe covered front, back, right, left, then up, about 2 s each
- [x] Bench 2: the same with `--take-off-log` (Joe tested whether it works; the drone was carried to the window during it, so its sensor values are not a bench baseline)

## Flights

| # | What was run | Result | Data file | Notes |
|---|---|---|---|---|
| 1 | `bench --crazyflie` | 59.8 s, 1195 ticks, 0 overruns | `logs/2026-11-12_15-49-23_bench.log` | A first attempt, 15:46, failed: no Crazyradio plugged in |
| 2 | `bench --crazyflie --take-off-log` | 1828 ticks, 0 overruns | `logs/2026-11-12_15-54-39_bench.log` | Drone carried during the run |

## Observations
What happened, especially anything surprising. Include numbers.

### Joe

- Result: pass.
- "The sensors seem to work."
- Forgot the radio on the first attempt.

### Computed from the logs (Claude)

- **Connect:** opening the link to the tick loop starting took about 4.7 s in
  bench 1 (parameters done at 3.5 s).
- **Bench 1, the covered sensors** read about 0.00 m (a distance, not out of
  range) at roughly 20-22 s (front), 25-28 s (back), 32-35 s (right), 37-42 s
  (left) and 43-47 s (up). Still, the front read a steady 0.25-0.26 m and the
  left 1.45 m; the right read 0.31-0.32 m with about half the samples out of
  range, and the back was mostly out of range with occasional 0.6-0.9 m
  returns.
- **Data ages (bench 1):** position, velocity and status median 11 ms (max 29);
  ranges median 53 ms (max 119); battery median 466 ms (max 972).
- **Position estimate:** 0.02, 0.00, 0.02 m, velocity uncertainty about 0.01 m/s.
- **Controller block** (always on): logged every 0.1 s from the end of connect.
- **Take-off block** (bench 2): 199 samples over 1.98 s, exactly 10 ms apart,
  no gaps, started at connect and stopped itself. In its first 60 ticks the
  worst lateness was 1.09 ms; over the run 0 overruns, worst lateness
  19.8 ms (99th percentile 1.58 ms) against 24.9 ms (1.54 ms) in bench 1.
- Bench 2 started with an implausible estimate before its reset,
  (-1.43, 1.13, 0.35) m at 2.25 m/s, while the drone was being carried.

## Next
- Code changes:
- Simulator model changes:
- ADRs to write or revisit:
- Next session's goal:
