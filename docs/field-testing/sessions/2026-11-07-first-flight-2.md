# 2026-11-07-first-flight-2

A session is one trip with one or more field tests, flown in order. Each
field test has its own log in [`../field-tests/`](../field-tests/).

- **Milestone:** First flight, session 2
- **Environment:** [Living room](../environments/living-room.md), hide-and-seek launch point, night

## Plan
*Written before flying. The tests in order, each linked to its log.*

Session 1 ([First flight 1](2026-11-04-first-flight-1.md)) flew all four
tests. Session 2 flies them again after the code changes, to test the new
take-off and landing
([ADR-0048](../../decisions/0048-level-through-the-bad-flow-zone.md)) and to
land within 3 cm of the take-off point.

1. [Failsafe low](../field-tests/2026-11-07-first-flight-2-failsafe-low.md)
2. [Failsafe high](../field-tests/2026-11-07-first-flight-2-failsafe-high.md)
3. [Hover](../field-tests/2026-11-07-first-flight-2-hover.md)

Each test needs the ones before it to pass. If one fails, stop and write it
up before flying the next (README, "Sessions and test logs").

The Bench was dropped from this session: it moves to the next one. No
geofence was set up.

## Before the session
*Done at the desk, not at the session. If any code changes after these runs, run them again.*

- **Commit to fly:** `189a0e1`
- [ ] Mock adapter run of each test's program on that commit passed:
  - [ ] Failsafe low: `.venv\Scripts\python -m crazyflie_behavior.programs.failsafe --fault-at climb`
  - [ ] Failsafe high: `.venv\Scripts\python -m crazyflie_behavior.programs.failsafe --fault-at hover`
  - [ ] Hover: `.venv\Scripts\python -m crazyflie_behavior.programs.hover --hover-seconds 60`

## Results
*From the operator or the recordings, never from an AI. One line per test: passed, failed or not flown.*

Joe's verdict, said on 2026-11-08: all the flights in this session failed,
because of the launch failures and the massive drifting on take-off.

- Failsafe low: failed. Findings: backlog #67 (arm refused after a flight),
  #68 (sideways drift during the initial climb).
- Failsafe high: failed. Findings: backlog #67-#69.
- Hover: failed. Findings: backlog #53, #67-#72.
- Bench: not flown. Moves to the next session.

## Next session
*What the results decide: another session, or the milestone is done.*

Plan: fly all four tests again, in this order:

1. Bench
2. Failsafe low
3. Failsafe high
4. Hover, with chirps (`--chirp`)

