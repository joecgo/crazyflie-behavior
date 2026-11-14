# 2026-11-13-first-flight-5

A session is one trip with one or more field tests, flown in order. Each
field test has its own log in [`../field-tests/`](../field-tests/).

- **Milestone:** First flight, session 5
- **Environment:** [Kitchen](../environments/kitchen.md), center of the room, all lights on, daylight (Joe, 2026-11-13).

## Plan
*Written before flying. The tests in order, each linked to its log.*

No plan was written before flying (Joe's call). Joe's aim, said before the
flights: "a few more test flights today to add to the data in session 4 …
the hover test with chirps with a 0.4m/s take off and all the debug logging
on".

1. [Hover, with chirps](../field-tests/2026-11-13-first-flight-5-hover.md)

## Before the session
*Done at the desk, not at the session. If any code changes after these runs, run them again.*

- **Commit to fly:** `c7ecffe`, clean tree. New code since session 4's
  `8d7bc29`: `e6ec43f` (the hover test's landing rule), `edaa6e0`
  ([ADR-0067](../../decisions/0067-a-take-over-connects-without-the-debug-only-blocks.md),
  the Crazyflie adapter) and `1d4ae8f` (review fixes, including the safety
  layer's staleness rule). Failsafe low and Failsafe high were not flown on
  it (README, "When to repeat a test").
- [ ] Mock adapter run of each test's program on that commit passed. One
  run, started by Claude at the session: it hovered and landed in the log,
  and was stopped about 5 s before its end (Joe's call), so it has no exit
  code.
  - [ ] Hover: `.venv\Scripts\python -m crazyflie_behavior.programs.hover --hover-seconds 60 --chirp --climb-speed 0.4 --take-off-log`

## What was flown
*Added after the session.*

Every flight and propeller test run was started by Claude in a terminal tab.
Exit codes were not captured.

1. Hover flights 1-6 (11:01 to 11:11): flight 1 hovered 60 s, flights 2-6
   hovered 10 s.
2. Propeller test runs 1 and 2 (about 11:16 to 11:18), after three attempts
   that failed to connect and a power cycle. Before run 2 Joe pressed the
   propellers on: he thought they might not all be on securely.
3. Hover flights 7 and 8 (11:19 and 11:21), 10 s each. After flight 7
   landed, Joe picked the drone up while the program waited to play
   "Charge"; the safety pre-check failed on the drone's tumble report and the
   tick loop stopped. Claude started flight 8 without reading how flight 7
   had ended, against the README's rule after an abnormal end
   ([mistakes log](../../claude-mistakes.md)).
4. Propeller test runs 3-6 (11:21 to 11:28). Joe worked on the propellers
   between runs 3 and 6; what he did isn't recorded.

One battery for all eight flights (Joe). Joe shifted it around between
flights to counter the direction of the drift; it didn't seem to affect the
flights (Joe). Which flights is not recorded.

## Results
*From the operator or the recordings, never from an AI. One line per test: pass, fail or not flown.*

- Hover: fail (Joe): "I would say it failed due to propeller issues." All
  eight flights hovered their full time and landed (the logs). They landed
  generally 7-15 cm from the mark, not measured exactly (Joe).
- Propeller test: run 6 times (backlog #83). M4 jumped from about 6 to 25-61
  in runs 3-6, after flights 7 and 8; M2 stayed at 7-11, as in session 4.
  Joe: "I think I need to replace the M4 propeller at least, and maybe the
  motor too. I find the propeller really difficult to pop off."

### Propeller test runs

The script writes no log, so its console output is the only record. Sideways
vibration variance X+Y (Z in brackets), voltage sag per motor, and the noise
floor X+Y.

| Run | M1 | M2 | M3 | M4 | Sag M1-M4 (V) | Noise floor |
|---|---|---|---|---|---|---|
| 1 | 4.29 (2.16) | 11.24 (11.75) | 3.64 (1.22) | 5.99 (4.79) | 0.41 0.43 0.43 0.43 | 0.0033 |
| 2 | 3.06 (2.68) | 10.30 (7.61) | 3.64 (0.78) | 6.08 (4.90) | 0.42 0.44 0.45 0.45 | 0.0041 |
| 3 | 4.36 (5.28) | 10.17 (2.92) | 3.68 (1.60) | 33.85 (14.14) | 0.39 0.41 0.39 0.41 | 0.0046 |
| 4 | 5.06 (2.79) | 7.20 (3.98) | 4.27 (3.52) | 60.52 (23.66) | 0.38 0.40 0.39 0.39 | 0.0047 |
| 5 | 6.30 (2.86) | 10.39 (1.81) | 4.93 (2.19) | 26.76 (13.27) | 0.37 0.40 0.38 0.39 | 0.0042 |
| 6 | 4.52 (0.86) | 7.19 (17.89) | 4.99 (1.04) | 24.96 (35.80) | 0.38 0.42 0.41 0.40 | 0.0043 |

Session 4's three runs had M4 at 17.53, 12.32 and 9.32. "Kalman prediction
rate off (28-54)" was printed after runs 1-5, not run 6; the cause wasn't
checked.

![Propeller test vibration by motor over session 4's three runs and session 5's six: M4 rises to 25-61 after flights 7 and 8](../field-tests/figures/2026-11-13-first-flight-5-propeller-tests.svg)

## Analysis (Claude, 2026-11-13)
*From the logs, not observations. Details in the [Hover log](../field-tests/2026-11-13-first-flight-5-hover.md).*

- **The hovers were as steady as session 4's:** position within 0.7-1.8 cm
  (standard deviation), velocity uncertainty at most 0.038 m/s against
  [ADR-0064](../../decisions/0064-in-flight-flow-limit-grows-with-height.md)'s
  0.05 at 0.5 m, no tick overruns.
- **The motor balance changed from flight to flight, and the hover took 3-7%
  more thrust** than in sessions 3 and 4 (44,600-46,300 against the thrust
  base of 43,000). Candidates: the propellers, a motor, the battery's
  position (Joe moved it), a heavier battery. The logs can't separate them
  (backlog #83, #97).
- **The climb pauses at about 0.3 m** for 0.34-0.40 s after the hand-over,
  longer than in session 4, and the drone keeps sliding sideways through it,
  up to 9 cm by the estimate: Joe's "slowed down during the ascent" (backlog
  #69).
- **The landing approach ended 11-17 cm above the final descent height** in
  all eight landings (backlog #93, since decided in
  [ADR-0068](../../decisions/0068-landing-approach-aims-below-the-final-descent-height.md)).
- **The low-light warning fired at every take-off in daylight**: on the floor
  the image quality reads as low by day as at night (backlog #96).

## Next session
*What the results decide: another session, or the milestone is done.*

- Hardware first (Joe, 2026-11-13, backlog #83): one time-boxed pass before
  session 6's 5 cm flights: new propellers on all four motors, one propeller
  test, one hover; the M4 motor swapped only if it still reads high; then
  stop.
- Session 6's [draft plan](draft-first-flight-6.md) was written before these
  results; its own note says to revise it against them.
- The rescue landing wasn't flown. Joe's call (2026-11-13) was to fly it in
  the next session, so it carries to session 6; whether it flies there is
  open.
- Open from this session: backlog #69, #81, #83, #91, #92, #96 and #97.
