# Next up

The project's state on one page, read first by a fresh work session.
`/wrap-up` rewrites it at the end of each work session.

**Keep it current.** When an item here finishes (a decision made, a pull
request merged, a step built), update this page in the same step: remove or
move the item, renumber "Next three", and update "Last commit" and
"Uncommitted".

- **Date:** 2026-11-23 (Pacific)
- **Last commit:** "Work log 2026-11-23, mistakes M-225 and M-226, next-up
  brief", on `main`. Uncommitted: nothing.

## Done last

- 2026-11-23: review pull request #30 (the recorder, `e8f7e10..fdcd31c`)
  closed. Its findings fixed on `main` (`05637fa`): `_TickStepRecord`
  (glossary: Tick step record), the `CallNoting*` test doubles, the
  interrupt message at start-up, "Recording finished". Others moved to
  backlog #149 to #151. `/project-review high`: no correctness bug; one
  finding accepted (an interrupt signal after disconnect is logged as before
  the tick loop).
- 2026-11-23: ADR-0089 decided and built (`33125ea`): the golden file
  `tests/recording/golden/format_v1.jsonl`, its tests, and `REVIEW.md`
  Q-57. Glossary: Code version, Format version, Golden file, Replaced
  request. Mistakes M-222 to M-226.
- 2026-11-22: the recorder built (ADR-0034, ADR-0087, ADR-0088); every
  program records to `recordings/`.

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
requests #24 to #30 read single changes ahead of the full review; the last,
#30, read up to `fdcd31c` and closed 2026-11-23. The full line-by-line walk
comes after the refactor (W9).
