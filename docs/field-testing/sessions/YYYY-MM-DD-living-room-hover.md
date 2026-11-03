# YYYY-MM-DD · living-room · hover at 0.5 m and land

> **DRAFT.** Date and commit are pending. Nothing below the pre-flight
> section has been filled in.

- **Test:** Hover (flight)
- **Git commit:** `<hash>` (must be committed before flying)
- **Hardware:** Crazyflie 2.1+, decks: Flow / Multi-ranger, battery #
- **Firmware / cflib:** <firmware version> / <cflib version>

## Goal and pass criteria
*Written before flying.*

- Goal: First hover through the project's own code: arm, take off to 0.5 m,
  hover, land, using the hover program (`programs.hover --crazyflie`, the
  hover test behavior, ADR-0030). Measure the drift over 60 s. Settle the
  flight-related `VERIFY` items.
- Pass if (the aim is to measure the drift, not to pass or fail it, so
  there is no distance limit):
  - [ ] The hover test reports done: armed within 2 s, reached 0.5 m (within
        0.1 m) within 5 s, hovered, landed, no error logged.
  - [ ] The distance from the take-off point to the landing point is
        measured with a tape measure (the drone's own position estimate
        drifts) and recorded.
  - [ ] A 60 s hover is flown (`--hover-seconds 60`) and the drift over it is
        measured from the recorded flight and by eye, and the number is
        recorded.
  - [ ] Motors stop only after touchdown is confirmed. A landing that needed the final descent still
        passes, but is recorded as a finding.
- Simulator prediction: **mock adapter, run 2026-11-02 (`programs.hover
  --hover-seconds 5`, mock):** arming, take-off to 0.50 m, hover, landing,
  done, no errors, 105 ticks at 20 Hz, 0 overruns. The mock does exactly what
  it's told, with no noise, drift or latency, so this predicts a perfect
  landing at the take-off point and zero drift. It is a baseline, not a
  prediction of the real drone. **Guess, not a run:** the real drone drifts
  visibly over 60 s and lands off the take-off point. The noisy simulator has
  not been run for this.

### `VERIFY` items this session can settle
- How the drone settles at the floor while the landing go_to holds it there
  (`adapter.py`, ADR-0032).
- Touchdown placeholders: down range at or below 0.05 m held for 0.3 s, final
  descent 0.1 m/s, margin 2 s (`touchdown.py`, ADR-0012, ADR-0019).
- `TAKE_OFF_STATUS_GRACE` of 1.0 s (`adapter.py`).
- Hover test placeholders: height tolerance 0.1 m, arm limit 2 s, take-off
  limit 5 s (`hover_test.py`).
- Vertical speed 0.3 m/s and hover settle time 1 s (`adapter.py`).

Not exercised by the hover test: the high-level commander after velocity
streaming (`adapter.py`), since the hover test never streams velocity.

## Environment
*Full profile on the first visit; afterwards, only what changed.*

- Size / ceiling height:
- Floor surface:
- Lighting:
- Obstacles and reflective surfaces:

## Pre-flight checklist

- [ ] Bench, Failsafe low and Failsafe high passed
- [ ] Code committed, hash recorded above
- [ ] Mock adapter run of this exact code passed (and the simulator's, if used)
- [ ] Propellers undamaged, battery charged (voltage: ___)
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
