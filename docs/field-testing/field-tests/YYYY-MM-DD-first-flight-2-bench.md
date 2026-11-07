# YYYY-MM-DD-first-flight-2-bench

- **Session:** [First flight 2](../sessions/YYYY-MM-DD-first-flight-2.md)
- **Test:** Bench (calibration)
- **Environment:** [Living room](../environments/living-room.md), hide-and-seek launch point, ___ (time of day)
- **Git commit:** `<hash>` (must be committed before flying)
- **Hardware:** Crazyflie 2.1+, decks: Flow / Multi-ranger / Buzzer, battery #
- **Firmware / cflib:** 2026.08, release 2026.10, unmodified ([ADR-0047](../../decisions/0047-pinned-firmware-release-warn-on-mismatch.md)) / 0.1.34

## Goal and pass criteria
*Written before flying.*

- Goal: Collect all the data the Bench's criteria ask for, which
  [First flight 1's Bench](2026-11-04-first-flight-1-bench.md) didn't: a
  clean 60 s run with the drone still, and the range-error tests.
- Two runs, kept apart because lifting the drone ruins the drift baseline:
  - **Run A:** the drone sits still on the floor, away from the wall, with
    enough light for the Flow deck, for 60 s or more. Nobody touches it.
  - **Run B:** the range-error tests (below). The drone can be held or lifted.
- Pass if:
  - [ ] The bench program (`programs.bench --crazyflie`) connects within the
        adapter's time limits (link 15 s, parameters 10 s, position estimate
        20 s, first telemetry 3 s). The time each step took is recorded
        (backlog #25).
  - [ ] Run A: position, velocity, battery, drone status and all six range
        directions arrive, none stale, over 60 s with the drone still (this
        also gives a stationary drift baseline). "Out of range" is fine on the
        sideways directions in open space; the down range must read a
        distance. *Staleness limit: to be decided. Session 1's 0.5 s didn't
        fit the battery's 1 s period.*
  - [ ] Flow deck and Multi-ranger deck are detected.
  - [ ] Run B: the Multi-ranger is made to misread, and what the console shows
        is noted for each: a hand over a sensor, something within 2 cm, a
        black surface, glass (a window), a mirror. An error that reads "out of
        range" (clear) instead of "invalid" (unknown) is the danger.
  - [ ] Each `VERIFY` item still open is confirmed or turned into a code change
        or backlog item. *List to be written from the First flight 1 findings.*
- Simulator prediction, if simulated: ___

## Pre-flight checklist

- [ ] Code committed, hash recorded above, the same commit as the session doc's mock runs
- [ ] Battery charged (voltage: ___)
- [ ] Flow deck (the right way round) and Multi-ranger deck seated
- [ ] Crazyradio plugged in, drone on the radio address the bench program uses:
      `radio://0/80/2M/E7E7E7E7E7`
- [ ] Firmware and cflib versions written in the header
- [ ] Run A: drone sitting still on the floor, away from the wall, with
      texture and light for the Flow deck (the velocity variance steady, not
      growing; backlog #48)

## During the test

- [ ] Start the bench program: `.venv\Scripts\python -m crazyflie_behavior.programs.bench --crazyflie`
- [ ] Note how long each connect step took (the console shows each step)
- [ ] **Run A:** leave the drone still for 60 s or more; check every value
      streams and the down range reads a distance. Stop with Ctrl+C.
- [ ] **Run B:** start the program again. Try to make the Multi-ranger
      misread, and note what the console shows for each: a hand over a sensor,
      something within 2 cm, a black surface, a window, a mirror. Stop with
      Ctrl+C.

## Flights

| # | What was run | Result | Data file | Notes |
|---|---|---|---|---|
| 1 | | | | |

## Observations

### Joe

-

### Computed from the logs (Claude)

-

## Next
- Code changes:
- ADRs to write or revisit:
- Next session's goal:
