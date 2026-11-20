# 0082: Every test that runs the tick loop on a sim clock has the 120 s limit; a fitness function keeps it so

- **Status:** Accepted. Amends [ADR-0080](0080-sim-clock-program-tests-fail-after-120-s.md).
- **Date:** 2026-11-20
- **Origin:** AI recommendation accepted (the scope, the fitness function,
  the test of the limit, removing `start` and the glossary term).

## Context

ADR-0080 gave the program tests a sim clock that fails past 120 s of sim
time, through the `sim_clock` fixture in `tests/programs/conftest.py`. Its
project review (backlog #129) found two places that still run the real tick
loop on a plain `SimClock()`, where a loop that never ends spins forever:
16 tests in `tests/programs/test_start_up.py` (11 directly, 5 through
`run_test_program`) and the tests in `tests/loop/`. It also found no test of
the limit itself, and an unused `start` parameter.

## Options considered

- **A. Program tests only:** `test_start_up.py` takes the existing fixture.
  Smallest; leaves the tick loop's own tests unbounded.
- **B. The fixture moves to `tests/conftest.py`;** `test_start_up.py` and
  `tests/loop/` use it. Covers every test of the real tick loop, one class.
- **C. B, and one shared clock replaces the Crazyflie adapter tests' three
  `BoundedSimClock`s.** One mechanism, but they differ (a sleep count on
  `StreamingSimClock`, per-file sim-time limits).
- **D. B, and the three switch from `AssertionError` to `pytest.fail`.**

## Decision

**B.** Every test that runs the tick loop on a sim clock fails past 120 s of
sim time. Before choosing, Joe asked whether 120 s fits the newly covered
tests: the longest runs 1.12 s of sim time
(`test_missed_ticks_are_skipped_never_caught_up`, measured 2026-11-20 over
all 67 tests in `tests/loop/` and `test_start_up.py`).

- `TimeLimitedSimClock` and the `sim_clock` fixture move to
  `tests/conftest.py`; the 11 tests and `run_test_program` in
  `test_start_up.py`, and the tests in `tests/loop/`, use the fixture.
- **A fitness function** fails if a test file in `tests/programs/` or
  `tests/loop/` calls `SimClock(` directly or subclasses `SimClock`. This
  is mistake M-012's pattern (a fake that hangs instead of failing) coming
  back, and ADR-0080's own Consequences named the gap. `LateWakingClock` in
  `tests/loop/test_tick_loop.py` is the one named exception (Joe, while
  building): its one test's tick step ends after 4 ticks, and giving it the
  limit would need `TimeLimitedSimClock` in an importable module.
- **A test of `TimeLimitedSimClock`:** a wait past 120 s fails with
  `pytest.fail`; a wait at 120 s doesn't.
- **`start` is removed:** the clock always starts at 0.
- The adapter tests' three `BoundedSimClock`s are unchanged (not C or D).

## Consequences

- A new test of the tick loop can't skip the limit by building its own
  `SimClock()`; the fitness function names the fixture to use.
- Tests in other folders that build a `SimClock()` (the mock adapter, the
  telemetry buffer, the safety layer) stay unbounded: they don't run the
  tick loop.
- Whether an `except Exception` in the Crazyflie adapter's waits can swallow
  the three `BoundedSimClock`s' `AssertionError` isn't checked: backlog
  #132.
- Glossary: **Sim time** added.
- Built 2026-11-20.
