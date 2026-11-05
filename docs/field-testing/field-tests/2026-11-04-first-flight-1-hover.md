# 2026-11-04-first-flight-1-hover

> **DRAFT.** Date and commit are pending. Nothing below the pre-flight
> section has been filled in.

- **Session:** [First flight 1](../sessions/2026-11-04-first-flight-1.md)
- **Test:** Hover (flight)
- **Environment:** [Living room](../environments/living-room.md), hide-and-seek launch point, all lights on. Time of day / sunlight: ___
- **Git commit:** `<hash>` (must be committed before flying)
- **Hardware:** Crazyflie 2.1+, decks: Flow / Multi-ranger, battery #
- **Firmware / cflib:** {firmware version} / {cflib version}

## Goal and pass criteria
*Written before flying.*

- Goal: First hover through the project's own code: arm, take off to 0.5 m,
  hover, land, using the hover program (ADR-0030). Measure the drift over
  60 s and settle the flight-related `VERIFY` items.
- Pass if (drift is measured, not passed or failed, so there is no distance
  limit):
  - [ ] The hover test reports done: armed within 2 s, reached 0.5 m (within
        0.1 m) within 5 s, hovered, landed, no error logged.
  - [ ] A 60 s hover is flown, and the drift over it is measured from the
        recording and by eye, and recorded.
  - [ ] The distance from the take-off point to the landing point is
        measured with a tape measure (the drone's own estimate drifts) and
        recorded.
  - [ ] Motors stop only after touchdown is confirmed. A landing that needed
        the final descent still passes, but is recorded as a finding.
  - [ ] Each `VERIFY` item below is confirmed or turned into a code change or
        backlog item.

### `VERIFY` items
- How the drone settles at the floor while the landing go_to holds it there
  (`adapter.py`, ADR-0032).
- Touchdown placeholders: down range at or below 0.05 m held for 0.3 s, final
  descent 0.1 m/s, margin 2 s (`touchdown.py`).
- `TAKE_OFF_STATUS_GRACE` of 1.0 s (`adapter.py`).
- Hover test placeholders: height tolerance 0.1 m, arm limit 2 s, take-off
  limit 5 s (`hover_test.py`).
- Vertical speed 0.3 m/s and hover settle time 1 s (`adapter.py`).

## Pre-flight checklist

- [ ] Bench, Failsafe low and Failsafe high passed
- [ ] Code committed, hash recorded above
- [ ] Mock adapter run of this exact code passed
- [ ] Propellers undamaged, battery charged (voltage: ___)
- [ ] Soft landing patch under the drone, flight area clear of people and pets
- [ ] Geofence configured for this space
- [ ] Video recording on

## During the test

- [ ] Mark the take-off point on the floor
- [ ] Start: `.venv\Scripts\python -m crazyflie_behavior.programs.hover --crazyflie --hover-seconds 60`
- [ ] Watch the flight; note anything unexpected while it happens
- [ ] After landing, measure from the take-off mark to the drone with a tape measure
- [ ] Note whether the landing needed the final descent (the log says so)

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
