# 2026-11-09-first-flight-3-hover

- **Session:** [First flight 3](../sessions/2026-11-09-first-flight-3.md)
- **Test:** Hover (flight), with chirps
- **Environment:** [Living room](../environments/living-room.md), hide-and-seek launch point, low light (the room's usual night lighting, no flashlight)
- **Git commit:** `876ba6d`
- **Hardware:** Crazyflie 2.1+, decks: Flow / Multi-ranger / Buzzer, battery #
- **Firmware / cflib:** 2026.08, release 2026.10, unmodified ([ADR-0047](../../decisions/0047-pinned-firmware-release-warn-on-mismatch.md)) / 0.1.34

## Goal and pass criteria
*Written before flying.*

- Goal: arm, take off to 0.5 m, hover 60 s with chirps
  ([ADR-0053](../../decisions/0053-buzzer-commands-and-a-chirp-hover-test.md)),
  land close to the take-off point.
- **Changed from the plan, Joe's call (2026-11-09):** the initial climb runs
  at 0.4 m/s (`--climb-speed 0.4`, [ADR-0059](../../decisions/0059-initial-climb-speed-set-per-hover-run.md)),
  since in Take-off speeds no 0.1 or 0.2 m/s climb got above 0.12 m (backlog
  #78). Flown after Failsafe high failed, without the Bench or the
  `/project-review`.
- Expected, from Take-off speeds: a cap landing (2 of 3 flights at 0.4 m/s),
  or a hover that the safety layer's velocity uncertainty limit ends within
  about 1 s (backlog #80). Battery about 3.87 V at rest, after 9 flights.
- Pass if:
  - [ ] The initial climb ends normally: `Initial climb done: settle height
        ___ m, final descent height ___ m`, no cap or time-limit warning.
  - [ ] The hover test reports done: reached 0.5 m, hovered 60 s, landed, no
        error logged.
  - [ ] Chirps heard during the hover.
  - [ ] The landing is within 3 cm of the take-off point, by tape measure.
  - [ ] Motors stop only after touchdown is confirmed, at the end of a level
        final descent.
- Simulator prediction: no simulator run. The mock run of the planned command
  wasn't run; the Take-off speeds mock runs at 0.4 m/s passed.

## Pre-flight checklist

- [ ] Bench, Failsafe low and Failsafe high passed: **Bench not flown,
      Failsafe high failed**
- [ ] Code committed, hash recorded above
- [ ] Propellers undamaged, battery voltage: ___ (below 3.62 V the take-off is refused, [ADR-0051](../../decisions/0051-battery-flight-limit-and-take-off-limit.md))
- [ ] Soft landing patch under the drone, about 1 m clear on every side
- [ ] Video recording on

## During the test

- [ ] Drone on the take-off mark
- [ ] Start: `.venv\Scripts\python -m crazyflie_behavior.programs.hover --crazyflie --hover-seconds 60 --chirp --climb-speed 0.4`
- [ ] Watch the flight; note anything unexpected while it happens
- [ ] After landing, measure from the take-off mark to the drone

## Flights

| # | What was run | Result | Data file | Notes |
|---|---|---|---|---|
| 1 | `hover --crazyflie --hover-seconds 60 --chirp --climb-speed 0.4` | Reached 0.5 m; the safety layer landed it about 1 s into the hover (velocity uncertainty) | `logs/2026-11-09_17-05-45_hover.log` | |

## Observations

### Joe

- It ended early, 25 cm to the right.

### Computed from the logs (Claude)

- **Before the take-off:** the estimate reset at connect, then the chirp on
  the floor and its 5 s wait. Image quality 31-41 on the floor. At the
  take-off the estimate said (-0.11, -2.23) m with velocity uncertainty
  0.65 m/s: it had run away about 2.2 m on the floor after the reset, and the
  take-off check allowed it. 0.2 s after the take-off, as flow arrived, the
  estimate jumped 2.5 m back in one step.
- **Initial climb:** `Initial climb done: settle height 0.110 m, final
  descent height 0.160 m` at 0.90 s. A dip from 0.186 m (1.0 s) to 0.126 m
  (1.6 s), as backlog #69, then the climb; `Hover test: at 0.41 m` at 2.30 s.
- **Hover:** the velocity uncertainty rose with height, 0.015 at 0.19 m,
  0.022 at 0.45 m, 0.028-0.030 at 0.5 m, and at 3.25 s the safety pre-check
  failed (`velocity uncertainty 0.030 m/s in flight (no flow over 0.03)`),
  0.95 s into the hover, as in Take-off speeds' flight 5 (backlog #80).
- **Landing:** `Final descent: level, from 0.306 m by the down range`,
  touchdown confirmed at 5.32 s. The log has no estimate after 3.25 s.
- **Shift by the estimate**, from 0.6 s (after the jump) to 3.2 s: within
  about 10 cm.
- No chirps during the hover: it never got that far. Battery 3.86 V at rest.
- **Analysis, 2026-11-10:** the dip, the fast final descent and the velocity
  uncertainty's rise are explained in
  [Take-off speeds' analysis](2026-11-09-first-flight-3-take-off-speeds.md#analysis-2026-11-10-claude):
  the firmware's vertical speed controller restarts its integral at every
  mode change, and the uncertainty grows with height in any light.

## Next
- Code changes and ADRs:
- Next session's goal:
