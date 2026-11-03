# YYYY-MM-DD · living-room · bench: connect and telemetry (propellers off)

> **DRAFT.** Date and commit are pending. Nothing below the pre-flight section has been filled in.

- **Stage:** Bench
- **Git commit:** `<hash>` (must be committed before flying)
- **Hardware:** Crazyflie 2.1+, decks: Flow / Multi-ranger, battery #
- **Firmware / cflib:** <firmware version> / <cflib version>

## Goal and pass criteria
*Written before flying.*

- Goal: Connect to the real drone through the Crazyflie adapter with the
  **propellers off**, confirm every telemetry value streams and the decks are
  detected. Settle the assumptions the code marks `VERIFY`. Arming isn't
  tested (the firmware arms itself) and neither is the emergency stop (no
  operator control exists yet, ADR-0013, ADR-0027).
- Pass if (the README's exit criterion is "all sensors stream"):
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
  - [ ] Every `VERIFY` item below is either confirmed or turned into a code
        change or backlog item.
- Simulator prediction: **mock adapter, run 2026-11-02 (`programs.bench`,
  mock):** connects instantly, battery 4.00 V, position and velocity zero,
  status not armed/flying/crashed/tumbled, all six ranges "out of range",
  every reading 0 ms old. This is the mock's fixed script, not a model of the
  real drone, so it predicts almost nothing about real readings.
  **Guess, not a run:** a real drone shows small non-zero position and
  velocity noise, a floor distance on the down range, and a battery near 4.0 V
  on a charged pack.

### `VERIFY` items this session can settle
From the code's notes:

- Connect time limits (`adapter.py`): link 15 s, parameters 10 s, position
  estimate 20 s, first telemetry 3 s.
- Range readings at or above 8000 mm mean "nothing in range", and **sensor
  errors don't also report as large values** (`conversions.py`).
- Log timestamps are milliseconds since boot (`conversions.py`).
- Setpoint timeouts match the firmware: stops following after 0.5 s, cuts
  motors after 2.0 s (`mock_adapter.py`).

Not testable with propellers off, so left for the hover session: the high-level
commander after velocity streaming, how the drone settles at the floor during
a go_to landing, `TAKE_OFF_STATUS_GRACE`, and the touchdown placeholders.

## Environment
*Full profile on the first visit; afterwards, only what changed.*

- Size / ceiling height:
- Floor surface:
- Lighting:
- Obstacles and reflective surfaces:

## Pre-flight checklist

- [ ] Code committed, hash recorded above
- [ ] Mock adapter run of this exact code passed (and the simulator's, if used)
- [ ] **Propellers off** (bench session), battery charged (voltage: ___)
- [ ] Flight area clear of people and pets
- [ ] Geofence configured for this space
- [ ] Recording on (telemetry + video)

## Flights

| # | What was run | Result | Data file | Notes |
|---|---|---|---|---|
| 1 | | | | |

## Observations
What happened, especially anything surprising. Include numbers.

## Sim vs real
Where the simulator's prediction matched reality and where it didn't.

## Next
- Code changes:
- Simulator model changes:
- ADRs to write or revisit:
- Next session's goal:
