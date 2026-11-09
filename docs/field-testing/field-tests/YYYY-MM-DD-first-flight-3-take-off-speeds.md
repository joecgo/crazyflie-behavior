# YYYY-MM-DD-first-flight-3-take-off-speeds

*Draft: rename with the session's date once it's set.*

- **Session:** [First flight 3](../sessions/YYYY-MM-DD-first-flight-3.md)
- **Test:** Hover (flight), short hovers at different initial climb speeds
- **Environment:** [Living room](../environments/living-room.md), hide-and-seek launch point, low light (the room's usual night lighting, no flashlight). Time of day / sunlight: ___
- **Git commit:** `<hash>` (must be committed before flying)
- **Hardware:** Crazyflie 2.1+, decks: Flow / Multi-ranger / Buzzer, battery #
- **Firmware / cflib:** 2026.08, release 2026.10, unmodified ([ADR-0047](../../decisions/0047-pinned-firmware-release-warn-on-mismatch.md)) / 0.1.34

## Goal and pass criteria
*Written before flying.*

- Goal: find out whether the initial climb's speed changes the sideways
  drift at take-off in low light (backlog #68), using the hover program's
  `--climb-speed` ([ADR-0059](../../decisions/0059-initial-climb-speed-set-per-hover-run.md)).
  In [First flight 2](2026-11-07-first-flight-2-hover.md) the drone drifted
  18-20 cm sideways, almost all of it in the initial climb: a push of a few
  centimeters at spin-up, then a steady 0.1 m/s by the estimate.
- Pass if (this is a measurement, no pass or fail on distance):
  - [ ] At least 2 flights at each speed, 0.1, 0.2 and 0.4 m/s.
  - [ ] Every flight ends with the motors stopped after touchdown, whether
        its initial climb ended normally or the cap or the time limit landed
        it. A cap or time-limit landing is a finding, not a failure.
  - [ ] For every flight, the table below has: the speed, the battery
        voltage, the sideways shift at take-off (from the take-off mark to
        below the drone once it's hovering), the landing's distance from the
        mark, and from the log the settle height, the final descent height,
        and whether the low-light warning appeared.
- Prediction (analysis of First flight 2's estimate, not a simulator run):
  if the drift is the speed left over after the push, the shift is about
  the push plus 0.1 m/s times the level part's time (final descent height
  over climb speed). For a final descent height near 0.25 m: about 25 cm at
  0.1 m/s, 12 cm at 0.2 m/s and 6 cm at 0.4 m/s, plus the push. If the push
  grows with a faster spin-up, 0.4 m/s won't shrink the shift as much, or at
  all. Flights at the same speed that differ a lot point to something else
  (the floor, the propellers, the light).

## Pre-flight checklist

- [ ] Bench, Failsafe low and Failsafe high passed
- [ ] Code committed, hash recorded above, the same commit as the session doc's mock runs
- [ ] Propellers undamaged, battery charged (voltage: ___; below 3.62 V the take-off is refused, [ADR-0051](../../decisions/0051-battery-flight-limit-and-take-off-limit.md))
- [ ] Soft landing patch under the drone, flight area clear of people and pets, at least 0.5 m clear on every side (0.1 m/s may drift about 30 cm)
- [ ] Same lighting for every flight; note any change
- [ ] Geofence configured for this space
- [ ] Video recording on, framed to see the floor marks

## During the test

- [ ] Mark the take-off point on the floor, and lay a tape measure on the
      floor through it, along First flight 2's drift (to the right), so the
      video can read the shift
- [ ] Fly in this order, so battery level and lighting changes spread over
      all speeds: 0.2, 0.4, 0.1, then again 0.2, 0.4, 0.1 (a third round if
      the batteries allow)
- [ ] Each flight: `.venv\Scripts\python -m crazyflie_behavior.programs.hover --crazyflie --hover-seconds 5 --climb-speed <speed>`
- [ ] Each flight: put the drone back on the mark facing the same way, and
      note the battery voltage from the log's opening lines
- [ ] Watch the take-off; note anything unexpected while it happens (a jump
      or tilt at spin-up, a direction change)
- [ ] After landing, measure from the take-off mark to the drone with a tape measure

## Flights

| # | Climb speed (m/s) | Battery (V) | Shift at take-off (cm) | Landing from mark (cm) | Settle / final descent height (m) | Low-light warning | Result | Data file | Notes |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.2 | | | | | | | | |
| 2 | 0.4 | | | | | | | | |
| 3 | 0.1 | | | | | | | | |
| 4 | 0.2 | | | | | | | | |
| 5 | 0.4 | | | | | | | | |
| 6 | 0.1 | | | | | | | | |

## Observations
What happened, especially anything surprising. Include numbers.

## Next
- Code changes:
- Simulator model changes:
- ADRs to write or revisit:
- Next session's goal:
