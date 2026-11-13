# 2026-11-12-first-flight-4

A session is one trip with one or more field tests, flown in order. Each
field test has its own log in [`../field-tests/`](../field-tests/).

- **Milestone:** First flight, session 4
- **Environment:** [Kitchen](../environments/kitchen.md), all lights on. Bench, Window bench, Failsafe low and Failsafe high in cloudy daylight; Take-off speeds and Hover in the dark (night, Joe, 2026-11-12). Location of the night tests: to confirm.

## Plan
*Written before flying. The tests in order, each linked to its log.*

There was no written plan: the tests were chosen during the session (Joe).
They ran in this order.

1. [Bench](../field-tests/2026-11-12-first-flight-4-bench.md), with the new controller block
2. [Window bench](../field-tests/2026-11-12-first-flight-4-window-bench.md) (sensor characterization), added by Joe
3. [Failsafe low](../field-tests/2026-11-12-first-flight-4-failsafe-low.md)
4. [Failsafe high](../field-tests/2026-11-12-first-flight-4-failsafe-high.md), flown after Failsafe low failed (Joe's call, against the README's rule)
5. Propeller test (`tools/propeller_test.py`, backlog #83), forgotten before the session
6. [Take-off speeds](../field-tests/2026-11-12-first-flight-4-take-off-speeds.md), with `--take-off-log`
7. [Hover, with chirps](../field-tests/2026-11-12-first-flight-4-hover.md)

## Before the session
*Done at the desk, not at the session. If any code changes after these runs, run them again.*

- **Commit to fly:** `8d7bc29`
- [x] Mock adapter run of each test's program on that commit passed (run at the start of the session, by Claude):
  - [x] Bench: `.venv\Scripts\python -m crazyflie_behavior.programs.bench` (runs until stopped; stopped after 8 s, all values streamed)
  - [x] Failsafe low: `.venv\Scripts\python -m crazyflie_behavior.programs.failsafe --fault-at climb`
  - [x] Failsafe high: `.venv\Scripts\python -m crazyflie_behavior.programs.failsafe --fault-at hover`
  - [x] Take-off speeds: `.venv\Scripts\python -m crazyflie_behavior.programs.hover --hover-seconds 5 --climb-speed 0.1`, then `0.2` and `0.4`
  - [x] Hover: `.venv\Scripts\python -m crazyflie_behavior.programs.hover --hover-seconds 60 --chirp`
- [ ] `/project-review` of the changes since the last one: not run before this session (Joe's call, to confirm)

## Results
*From the operator or the recordings, never from an AI. One line per test: passed, failed or not flown.*

- Bench: passed (Joe).
- Window bench: run, 4 runs; the first two don't count (Joe wasn't at the window yet, then a mesh screen was in front). Joe held it about 9 inches (23 cm) from the glass; the front read 0.43-0.44 m. Joe's assumption: the sensor sees things outside the window, not the glass.
- Failsafe low: "I guess that's a fail": drifted 20 cm forward and right (Joe). The log shows the fault, the pre-check failure and the landing.
- Failsafe high: failed. It drifted 59 cm away (Joe); the log shows the safety layer landed it at 0.26 m in the initial climb, before the hover, and the fault never fired.
- Propeller test: run 3 times (backlog #83). M2 and M4 vibrate most in all three runs.
- Take-off speeds: flown, one flight at each of 0.1, 0.2 and 0.4 m/s; a second 0.2 m/s attempt was refused on the floor and isn't counted. All three reached the hover. Drift: 7, 9 and 3.5 cm (Joe). Pass or fail: Joe to call (the test has no pass or fail on distance).
- Hover: flew the full 60 s and landed; straight take-off, drifted left on the landing, 6 cm from the mark (Joe). Pass or fail: Joe to call.

## Next session
*What the results decide: another session, or the milestone is done.*

To decide (Joe). Open from this session: the take-off drift against the
light (backlog #68, #78), the estimate running away on the floor (#81), the
M2 and M4 propellers (#83), the battery margin for a 60 s hover, and that
the Multi-ranger doesn't see windows.
