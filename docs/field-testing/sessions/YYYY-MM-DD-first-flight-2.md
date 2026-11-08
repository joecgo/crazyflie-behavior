# YYYY-MM-DD-first-flight-2

A session is one trip with one or more field tests, flown in order. Each
field test has its own log in [`../field-tests/`](../field-tests/).

- **Milestone:** First flight, session 2
- **Environment:** [Living room](../environments/living-room.md), hide-and-seek launch point

## Plan
*Written before flying. The tests in order, each linked to its log.*

Session 1 ([First flight 1](2026-11-04-first-flight-1.md)) flew all four
tests. Session 2 flies them again after the code changes, to test the new
take-off and landing
([ADR-0048](../../decisions/0048-level-through-the-bad-flow-zone.md)), to
collect the Bench data session 1 missed, and to land within 3 cm of the
take-off point.

1. [Bench](../field-tests/YYYY-MM-DD-first-flight-2-bench.md) (Run A, then Run B)
2. [Failsafe low](../field-tests/YYYY-MM-DD-first-flight-2-failsafe-low.md)
3. [Failsafe high](../field-tests/YYYY-MM-DD-first-flight-2-failsafe-high.md)
4. [Hover](../field-tests/YYYY-MM-DD-first-flight-2-hover.md)

Each test needs the ones before it to pass. If one fails, stop and write it
up before flying the next (README, "Sessions and test logs").

Flown on 2026-11-07 in a changed order, Joe's call: Failsafe low, Failsafe
high and Hover first, the Bench last. No geofence was set up.

## Before the session
*Done at the desk, not at the session. If any code changes after these runs, run them again.*

- **Commit to fly:** `<hash>`
- [ ] Mock adapter run of each test's program on that commit passed:
  - [ ] Bench: `.venv\Scripts\python -m crazyflie_behavior.programs.bench`
  - [ ] Failsafe low: `.venv\Scripts\python -m crazyflie_behavior.programs.failsafe --fault-at climb`
  - [ ] Failsafe high: `.venv\Scripts\python -m crazyflie_behavior.programs.failsafe --fault-at hover`
  - [ ] Hover: `.venv\Scripts\python -m crazyflie_behavior.programs.hover --hover-seconds 60`

## Results
*From the operator or the recordings, never from an AI. One line per test: passed, failed or not flown.*

-

## Next session
*What the results decide: another session, or the milestone is done.*

