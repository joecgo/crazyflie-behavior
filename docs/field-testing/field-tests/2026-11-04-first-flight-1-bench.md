# 2026-11-04-first-flight-1-bench

> Flown 2026-11-04, 16:00 to 16:17 Pacific. The Flights table and "Computed
> from the logs" are by Claude, from the recorded logs. Pass or fail, and
> Joe's own observations, are Joe's to write.

- **Session:** [First flight 1](../sessions/2026-11-04-first-flight-1.md)
- **Test:** Bench (calibration)
- **Environment:** [Living room](../environments/living-room.md), hide-and-seek launch point, all lights on. Time of day / sunlight: ___
- **Git commit:** `65665e4` (must be committed before flying)
- **Hardware:** Crazyflie 2.1+, decks: Flow / Multi-ranger / Buzzer, battery #
- **Firmware / cflib:** 2026.08, release 2026.10, unmodified ([ADR-0047](../../decisions/0047-pinned-firmware-release-warn-on-mismatch.md)) / 0.1.34

## Goal and pass criteria
*Written before flying.*

- Goal: Connect to the real drone through the Crazyflie adapter, confirm every
  telemetry value streams and the decks are detected, and settle the
  assumptions the code marks `VERIFY`.
- Pass if:
  - [ ] The bench program (`programs.bench --crazyflie`) connects within the
        adapter's time limits (link 15 s, parameters 10 s, position estimate
        20 s, first telemetry 3 s). The time each step took is recorded
        (backlog #25).
  - [ ] Position, velocity, battery, drone status and all six range directions
        arrive, none stale (older than 0.5 s), over a 60 s run with the drone
        still (this also gives a stationary drift baseline). "Out of range"
        is fine on the sideways directions in open space; the down range
        must read a distance.
  - [ ] Flow deck and Multi-ranger deck are detected.
  - [ ] Each `VERIFY` item is confirmed or turned into a code change or
        backlog item:
    - Range readings at or above 8000 mm mean "nothing in range", and sensor
      errors don't also report as large values (`conversions.py`).
    - Log timestamps are milliseconds since boot (`conversions.py`).
    - Whether the drone arms itself (ADR-0037): the connect log says so;
      if it contradicts the firmware source, revisit the ADR.

## Pre-flight checklist

- [ ] Code committed, hash recorded above
- [ ] Mock adapter run of this exact code passed
- [ ] Battery charged (voltage: ___)
- [ ] Flow deck and Multi-ranger deck seated
- [ ] Crazyradio plugged in, Windows USB driver installed with Zadig (README, "Run")
- [ ] Drone on the radio address the bench program uses (no option for
      another): `radio://0/80/2M/E7E7E7E7E7`
- [ ] Firmware and cflib versions written in the header (how to read the
      firmware version: to find out before the session)
- [ ] Drone sitting still on the floor, with texture and light for the Flow
      deck (the position estimate settles on connect)

## During the test

- [ ] Start the bench program: `.venv\Scripts\python -m crazyflie_behavior.programs.bench --crazyflie`
- [ ] Note how long each connect step took (the console shows each step)
- [ ] Note the connect log line about auto-arming
- [ ] Leave the drone still for 60 s; check every value streams and the down
      range reads a distance
- [ ] Try to make the Multi-ranger misread: cover a sensor with a hand, point
      one at a black or glass surface, hold something within 2 cm. Note what
      the console shows for each: an error that reads "out of range" (clear)
      instead of "invalid" (unknown) is the danger
- [ ] Stop with Ctrl+C
- [ ] Switch the drone off and on, run the program again, and compare the
      first drone time in the log file (snapshot lines are debug level, so
      only in the file) with the seconds since power-on

## Flights

| # | What was run | Result | Data file | Notes |
|---|---|---|---|---|
| 1 | `bench --crazyflie` | Stopped at connect: Flow deck not detected | `logs/2026-11-04_16-00-46_bench.log` | Joe: the Flow deck was on backwards. Reseated, then detected |
| 2 | `bench --crazyflie` | Ran 3.7 min, stopped with Ctrl+C | `logs/2026-11-04_16-05-49_bench.log` | 4400 ticks, 1 overrun. Hand tests 16:08:31-48; drone lifted at 16:08:50 |
| 3 | `bench --crazyflie`, after a power cycle | Stopped at connect: position estimate didn't settle in 20 s | `logs/2026-11-04_16-12-17_bench.log` | |
| 4 | `bench --crazyflie` | Same as 3 | `logs/2026-11-04_16-13-22_bench.log` | Stray log stream id=1 left by 3 |
| 5 | `bench --crazyflie` | Ran 20 s, stopped by the interrupt signal | `logs/2026-11-04_16-16-31_bench.log` | 401 ticks, 0 overruns. Lights on, away from the wall |

## Observations

### Joe (said during the session)

- The Flow deck was mounted backwards at first.
- The drone sat near a wall; he lifted it for about 3 s at the end of run 2.

### Computed from the logs (Claude)

- **Connect steps,** runs 2 / 5: link and parameters 3.1 / 3.4 s, position
  estimate 5.0 / 5.0 s, first telemetry 1.1 / 1.1 s. All within the limits.
- **Oldest value ages,** runs 2 / 5: position, velocity and status 85 / 21 ms;
  down range 96 / 21 ms; side and up ranges 175 / 101 ms; battery 1013 /
  998 ms. Within the safety layer's limits (0.25 s; battery 3 s). The pass
  criterion's 0.5 s didn't allow for the battery's 1 s period.
- **Decks:** Flow deck v2, Multi-ranger and Buzzer deck detected
  (`bcZRanger2 = 1` is the Flow deck's down sensor).
- **VERIFY, auto-arming:** the drone arms itself (connect log line, status
  armed).
- **VERIFY, range errors:** never "invalid" in about 1200 samples per
  direction. Errors arrive as "out of range": one or two samples as a hand
  arrives or leaves, and the up sensor while a hand was 5-9 cm away.
  Distances of 0.000-0.016 m arrive as valid. Errors are **not** kept apart
  from real readings.
- **VERIFY, drone time:** consistent with seconds since boot. The first drone
  times (44.9 s, 287.5 s) put the power-ons at about 16:05:14 and 16:11:53.
- **Stationary drift,** run 2: about 6 cm in y over 3 minutes.
- **Runaway estimate,** run 2: after the lift, the velocity estimate grew
  about 0.1 m/s each second with the drone on the floor; position reached
  -87 m.
- **Runs 3 and 4:** the Flow deck's motion flag read 0x30 (no motion) with
  zero deltas and surface quality 12-27, so the firmware fused no flow
  (`flowdeck_v1v2.c:157` at 2026.08) and the velocity variance grew without
  limit (`kalman.varPX` to 12). Before run 5: motion mostly 0xB0, quality
  23-43, variance about 1e-4. The shutter read 8191 in both cases.

## Next
- Code changes: the failed-connect cleanup gap (backlog #53) and the
  firmware warning (ADR-0047).
- ADRs to write or revisit: backlog #47 to #53.
- Next session's goal: Failsafe low and Failsafe high on a full battery.
