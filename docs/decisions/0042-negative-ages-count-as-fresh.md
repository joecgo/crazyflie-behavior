# 0042: Slightly negative ages count as fresh; a large one is a warning

- **Status:** Superseded by [0046](0046-snapshot-time-read-after-the-copy.md)
- **Date:** 2026-11-02
- **Origin:** AI recommendation accepted (option C). Splitting this off from backlog #8: AI suggestion accepted.

## Context

The tick reads its time first, then `take_snapshot` copies the telemetry
buffer. cflib's receive thread can store a value in between, stamped with a
later arrival time, so `age(now)` comes out a few milliseconds negative. Every
staleness check tests `age > limit`, so this already counts as fresh. A future
use that divides by an age, or treats a negative one as impossible, could
break; an age far below zero can only be a bug, such as mixing drone time and
PC time.

## Options considered

- **A. No clamp; write the rule down.** Docstring and a test only.
- **B. Clamp at zero in `age()`.** Safe for every caller, but a clock bug
  looks fresh.
- **C. A, plus a warning** for an age more negative than one tick period.
- **D. Read the tick time after the copy.** Changes the tick timing model
  (ADR-0003, ADR-0024) to remove a harmless gap.

## Decision

Option C.

- `age()` isn't clamped. Its docstring says it can be slightly negative,
  meaning just arrived.
- Staleness is always tested as `age > limit`.
- The safety pre-check warns when an age is below `-MAX_NEGATIVE_AGE`, one
  tick period (0.05 s at 20 Hz), logged once per streak per value. The value
  still counts as fresh; the warning doesn't fail the pre-check.

## Failure modes

- **Inputs:** a value from the future by more than a tick: logged as a
  probable clock bug, still used.
- **Backups:** none new.
- **Never:** a slightly negative age makes a check fail; a large negative age
  goes unlogged.
- **Always eventually:** none new.

## Consequences

- **Risk I accept knowingly:** a clock bug is reported, not acted on. If it
  makes stale values look fresh, the pre-check won't catch the staleness.
- Code to build, with tests: the docstring, the warning (once per streak), a
  slightly negative age passing the pre-check, a large one warning.
