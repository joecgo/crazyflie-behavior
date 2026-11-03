# YYYY-MM-DD-first-flight-1-bench

> **DRAFT.** Date and commit are pending. Nothing below the pre-flight section has been filled in.

- **Session:** [First flight 1](../sessions/YYYY-MM-DD-first-flight-1.md)
- **Test:** Bench (calibration)
- **Environment:** [Living room](../environments/living-room.md), hide-and-seek launch point, all lights on. Time of day / sunlight: ___
- **Git commit:** `<hash>` (must be committed before flying)
- **Hardware:** Crazyflie 2.1+, decks: Flow / Multi-ranger, battery #
- **Firmware / cflib:** {firmware version} / {cflib version}

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
| 1 | | | | |

## Observations
What happened, especially anything surprising. Include numbers.

## Next
- Code changes:
- ADRs to write or revisit:
- Next session's goal:
