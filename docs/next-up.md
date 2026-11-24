# Next up

The project's state on one page, read first by a fresh work session.
`/wrap-up` rewrites it at the end of each work session.

**Keep it current.** When an item here finishes (a decision made, a pull
request merged, a step built), update this page in the same step: remove or
move the item, renumber "Next three", and update "Last commit" and
"Uncommitted".

- **Date:** 2026-11-24 (Pacific)
- **Last commit:** "Work log 2026-11-24, mistakes M-227 to M-230, next-up
  brief", on `main`, after `afea472`. Uncommitted: nothing. Not pushed
  when written. The continuous integration checks pass (943 passed, 1
  skipped).

## Done last

- 2026-11-24: `/project-review high` on the day's work: 8 findings. Fixed:
  a damaged `.gz` recording now raises `ValueError` (with tests and a
  facts-register row), `/debrief` commits a script's recordings, ADR-0092
  says what's built, the glossary's Bug planting says "once it's built".
  Notes added to #153 and #156. `REVIEW.md`'s map has rows for
  `recording/` and `analysis/`. Mistakes M-228 to M-230.
- 2026-11-24: decided #142 as ADR-0090: a bug-planting tool,
  `tools/plant_bugs.py`, that generates its plants from the code's named
  limits (a time limit plus `0.8 / TICK_RATE` among them), runs on demand,
  and keeps known survivors with reasons. Also a coding-style line, and the
  glossary's Survivor. Not built (#152).
- 2026-11-24: decided #144 as ADR-0091: a test fails when a live doc cites a
  removed backlog row. Not built (#153).
- 2026-11-24: a second work session decided #55 as ADR-0092 (cited analysis
  scripts are committed to `analysis/`; the snapshot line goes after the
  first recorded session's check) and built #154: the folder, its checks,
  and `.gz` reading. Not built: #155 and #156.

## In progress

Nothing.

## Next three

1. C6, Joe's priority: split the Crazyflie adapter (`ARCHITECTURE.md`
   section 7, first row; `drafts/2026-11-13-code-recommendations.md`, D13
   to D16, still unanswered). It starts with `/decide` and the split's ADR,
   no code yet. Opus, Max.
2. Build #153, the test for citations of removed backlog rows (ADR-0091),
   before the next backlog row is removed. Sonnet, medium.
3. Build #152, the bug-planting tool (ADR-0090), before Joe's next code
   review. Opus, high.

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
- **E6.** The bug-planting tool (ADR-0090) runs on demand, but the test for
  citations of removed backlog rows (ADR-0091) runs in continuous
  integration on every push. Why the difference, and what does the tool
  need so that its report doesn't become noise people learn to ignore?
- **E7.** ADR-0092 keeps the text log's snapshot line until the first
  recorded session's recordings match it. What could be lost in that
  session if the line were already gone, and why is the text log still no
  help if the laptop's disk fails?

## Last reviewed

`0846826`, 2026-11-04: the last full row of `REVIEW.md`'s review log. Pull
requests #24 to #30 read single changes ahead of the full review; the last,
#30, read up to `fdcd31c` and closed 2026-11-23. The full line-by-line walk
comes after the refactor (W9).
