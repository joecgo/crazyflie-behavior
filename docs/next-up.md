# Next up

The project's state on one page, read first by a fresh work session.
`/wrap-up` rewrites it at the end of each work session.

**Keep it current.** When an item here finishes (a decision made, a pull
request merged, a step built), update this page in the same step: remove or
move the item, renumber "Next three", and update "Last commit" and
"Uncommitted".

- **Date:** 2026-11-23 (Pacific)
- **Last commit:** the records for pull request #30's fixes (glossary,
  ARCHITECTURE.md, backlog, mistakes log, this brief), on `main`, pushed.
  Uncommitted: nothing.

## Done last

- 2026-11-23: pull request #30's findings fixed on `main` (Joe's comments
  and Claude's), or moved to the backlog (#149, #150, #151). ADR-0089 built:
  the golden file and Q-57. `_TickStepPart` renamed `_TickStepRecord`
  (glossary: Tick step record); the test doubles renamed `CallNoting*`.
  #30 closed, its review-log row added. `/project-review high`: no correctness bug; one finding accepted (an
  interrupt signal after disconnect is logged as before the tick loop).
- 2026-11-22: review pull request #30 opened on `e8f7e10..fdcd31c` (the
  recorder and the boundary tests), branches `review/2026-11-22-recorder`
  into `review-base/2026-11-22-recorder`. Packet:
  `drafts/review-packets/2026-11-22-recorder.md`. The project review's 12
  findings posted as comments, one review: 10 at their lines, 2 in the
  summary (lines outside the diff). None fixed. M-221 logged (84 vs 87).
- 2026-11-22: the recorder built (ADR-0034, ADR-0087, ADR-0088; #145
  removed): `recording/`, `SafetyLayer.events_this_tick`, the tick step's
  recording, the tick loop's `on_tick_measured`; every program records to
  `recordings/`. 87 planted bugs, all caught. #148 added (a converter for
  old logs).
- 2026-11-22: boundary tests done (#133), #140 done, ADR-0085 and ADR-0086
  built, #29 closed.

## In progress

- Nothing.

## Next three

1. Decide #142 (a bug-planting tool), due now that the boundary tests are
   done; #144 (rows that wait on a removed backlog row) beside it. Opus,
   high.
2. Decide #55 (where analysis scripts live): the recorder drops the text
   log's snapshot line, which breaks the scripts in `drafts/`, so the two
   go together. Opus, high.
3. Not chosen yet: Joe picks it from the backlog.

## Explain-backs waiting

Answer by number, such as "E1: ...", in any work session. Claude grades
from `drafts/explain-back-notes.md`; don't open it first.

- **E1.** ADR-0086 checks for a lost link only in `take_snapshot()`. Why
  does that still stop every tick after a lost link before it does anything,
  and which command still raises on its own after one, and why?
- **E2.** A recording writes a NaN battery voltage as the string `"nan"`,
  not as `null`. What would go wrong in a replay test if it wrote `null`?
- **E3.** The tick's timing reaches the recorder through a callable the
  tick loop calls (ADR-0088). Why can't the tick step measure a tick's
  lateness and work time itself?
- **E4.** A behavior raises halfway through a tick, after one command
  request. What does that tick's line in the recording hold, and what makes
  sure the line, and the recording's last line, still get written?
- **E5.** Change the name a recording uses for a flight end reason, in the
  one table both the encoder and the decoder read. Why do the round-trip
  tests still pass, which golden file tests fail (ADR-0089), and what
  does the golden file deliberately not catch?

## Last reviewed

`0846826`, 2026-11-04: the last full row of `REVIEW.md`'s review log. Pull
requests #24 to #29 read single ADRs ahead of the full review; #30 (open)
reads `e8f7e10..fdcd31c`. The full line-by-line walk comes after the
refactor (W9).
