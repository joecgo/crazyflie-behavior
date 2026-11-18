# 0076: Program tests run on the sim clock, with one real-clock test per program

- **Status:** Accepted. Amended by [ADR-0080](0080-sim-clock-program-tests-fail-after-120-s.md),
  2026-11-18: a sim-clock program test fails after 120 s of sim time.
- **Date:** 2026-11-17
- **Origin:** AI recommendation accepted.

## Context

Each program's `main()` builds its own `RealClock`, so program tests run in
real time: 23.3 of the suite's 38.5 s, with waits shortened by patching
module constants. A laptop stall makes them fail now and then
([backlog #70](../decision-backlog/070.md)). [ADR-0009](0009-clock-abstraction.md)
gave every component an injected clock, but the programs never took one.
This is D9 of `drafts/2026-11-13-code-recommendations.md`, item C5 part 1.

## Options considered

- **A. The sim clock, except one real-clock test per program:** `main()`
  takes an optional clock; tests pass a `SimClock` and the mock adapter, so
  the program runs on one thread in milliseconds, the same every time, with
  its real wait constants. Each program keeps one real-clock test, plus the
  interrupt signal tests, to prove the real wiring.
- **B. As today:** real time, patched constants. Nothing to build, but slow
  and flaky on a stall.

## Decision

A. Tests become fast and repeatable and stop patching constants, while one
real-clock test per program still covers `RealClock`, threads and signals,
which a sim clock can't.

## Consequences

- `main(arguments=None, *, clock: Clock | None = None)` in each program;
  `None` means a `RealClock`.
- The tests named "runs as a program" and the tests that send a real
  interrupt signal stay on the real clock, and can still fail on a laptop
  stall (#70).
- A sim-clock test can't catch a bug that needs real threads or real timing.
- Converted tests must still fail for the bug each was first proven with.
- The failsafe program never had a "runs as a program" test, and none was
  added (Joe, 2026-11-18): the hover and rescue landing programs' tests
  already run the shared start-up code on the real clock.
- Built 2026-11-18.
