# 2026-11-09-first-flight-3

A session is one trip with one or more field tests, flown in order. Each
field test has its own log in [`../field-tests/`](../field-tests/).

- **Milestone:** First flight, session 3
- **Environment:** [Living room](../environments/living-room.md), hide-and-seek launch point, low light (the room's usual night lighting, no flashlight)

## Plan
*Written before flying. The tests in order, each linked to its log.*

[First flight 2](2026-11-07-first-flight-2.md) failed on launch failures and
the drone drifting 18-20 cm sideways during the initial climb (backlog #68).
Session 3 flies the four tests again, as First flight 2 planned, and adds
Take-off speeds: short hovers at different initial climb speeds
([ADR-0059](../../decisions/0059-initial-climb-speed-set-per-hover-run.md)),
to learn whether a faster or slower climb drifts less in low light.

1. Bench (log to be drafted)
2. [Failsafe low](../field-tests/2026-11-09-first-flight-3-failsafe-low.md)
3. [Failsafe high](../field-tests/2026-11-09-first-flight-3-failsafe-high.md)
4. [Take-off speeds](../field-tests/2026-11-09-first-flight-3-take-off-speeds.md)
5. [Hover, with chirps](../field-tests/2026-11-09-first-flight-3-hover.md) (`--chirp`)

Each test needs the ones before it to pass. If one fails, stop and write it
up before flying the next (README, "Sessions and test logs"). Take-off speeds
comes before the Hover so a 60 s hover doesn't use up the batteries first.

## Before the session
*Done at the desk, not at the session. If any code changes after these runs, run them again.*

- **Commit to fly:** `<hash>`
- [ ] Mock adapter run of each test's program on that commit passed:
  - [ ] Bench: `.venv\Scripts\python -m crazyflie_behavior.programs.bench`
  - [ ] Failsafe low: `.venv\Scripts\python -m crazyflie_behavior.programs.failsafe --fault-at climb`
  - [ ] Failsafe high: `.venv\Scripts\python -m crazyflie_behavior.programs.failsafe --fault-at hover`
  - [ ] Take-off speeds: `.venv\Scripts\python -m crazyflie_behavior.programs.hover --hover-seconds 5 --climb-speed 0.1`, then the same with `0.2` and `0.4`
  - [ ] Hover: `.venv\Scripts\python -m crazyflie_behavior.programs.hover --hover-seconds 60 --chirp`
- [ ] `/project-review` of the changes since the last one (owed for ADR-0054, ADR-0058 and ADR-0059)

## Results
*From the operator or the recordings, never from an AI. One line per test: passed, failed or not flown.*

- Bench: not flown (Joe's call).
- Failsafe low: passed by the log; both flights landed 6 cm right.
- Failsafe high: failed. It landed early, 20 cm forward and to the right: the
  initial climb's time limit landed it before the hover.
- Take-off speeds: flown, 2 rounds (flight 5 flown twice, one take-off
  refused on the floor). Only 0.4 m/s climbed; one flight reached the hover
  and the safety layer landed it on velocity uncertainty. The time limit or
  the cap landed every other flight.
- Hover: failed. Flown with a 0.4 m/s climb (Joe's call); it reached 0.5 m
  and the safety layer landed it about 1 s into the hover (backlog #80).

## Next session
*What the results decide: another session, or the milestone is done.*
