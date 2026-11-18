# 0080: Sim-clock program tests fail after 120 s of sim time; the continuous integration job stops after 15 minutes

- **Status:** Accepted. Amends [ADR-0076](0076-program-tests-run-on-the-sim-clock.md).
- **Date:** 2026-11-18
- **Origin:** Mixed: the 15-minute limit on the continuous integration job
  was mine, over the AI's recommendation not to add it; the time-limited sim
  clock and its 120 s limit were AI recommendations accepted.

## Context

On the sim clock ([ADR-0076](0076-program-tests-run-on-the-sim-clock.md)),
a program that never ends doesn't hang: each wait jumps straight to its
deadline, so the tick loop runs about 3,000 ticks and writes about 6.6 MB of
log per real second, without end. The hang watchdog counts real time and
only reports, and neither pytest nor the workflow had a time limit. This was
finding 1 of the project review of ADR-0076's build, the pattern of mistake
M-012, "Test fakes that hang instead of failing" (`REVIEW.md` Q-10). The
Crazyflie adapter's tests already limit their sim clock (`BoundedSimClock`,
1,000 sleeps).

## Options considered

- **A. A sim clock with a time limit, for the program tests only:** a
  test-only `SimClock` whose `sleep_until` fails the test once a program
  runs past a set sim time. No dependency and no change to production code,
  but it doesn't cover the real-clock tests.
- **B. `pytest-timeout`:** a real-time limit on every test. It covers every
  hang, but adds a dependency, and a program that never ends still writes
  about 400 MB before a 60 s limit stops it.
- **C. A time limit on the continuous integration job:** one line in the
  workflow. It stops a hung run on GitHub, but gives no reason and does
  nothing on the laptop.

## Decision

A, with C as a backstop. A program that never ends fails its test in under
2 s, with a message that names the cause, on the laptop and in continuous
integration. C costs one line, with no code, and stops any other hang on
GitHub after 15 minutes.

- The limit is 120 s of sim time, four times the longest program test
  (30 s, a rescue landing that runs out its time limit). Fine for now (Joe).
- It fails with `pytest.fail`, not an `AssertionError`: `run_program` turns
  any `Exception` into exit code 1. With a planted tick loop that never
  stops, an `AssertionError` let 7 of the 14 affected tests pass;
  `pytest.fail` raises a `BaseException`, which `run_program` lets through,
  and all 14 failed.
- `TimeLimitedSimClock` and the `sim_clock` fixture are in
  `tests/programs/conftest.py`, and the fixture replaces every `SimClock()`
  in the four program test files.

## Consequences

- A program test that builds a plain `SimClock()` has no limit again.
- A program test that needs more than 120 s of sim time needs the limit
  raised.
- The real-clock tests have no limit on the laptop; on GitHub, C stops them
  after 15 minutes.
- Most of the bench tests' clocks only run the tick step a set number of
  times and can't run on forever; they use the fixture so the four files
  keep one rule.
- No glossary change.
- Built 2026-11-18.
