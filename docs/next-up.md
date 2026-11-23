# Next up

The project's state on one page, read first by a fresh work session.
`/wrap-up` rewrites it at the end of each work session.

**Keep it current.** When an item here finishes (a decision made, a pull
request merged, a step built), update this page in the same step: remove or
move the item, renumber "Next three", and update "Last commit" and
"Uncommitted".

- **Date:** 2026-11-22 (Pacific)
- **Last commit:** this brief, with the work log, after the boundary tests
  part 2, the mistakes log and backlog, and ADR-0087, on `main`.
  Uncommitted: nothing.

## Done last

- 2026-11-22: boundary tests part 2 (#133, now done): rows 4-6, 8-11 and
  18-20, every planted bug caught; a test past a time limit checks 0.01 s
  past it (Joe's choice). #140: the tick-step tests tick every
  `STALE_AFTER / 2` (Joe's choice), and two now tick until hovering (M-216).
  `/project-review high`: 8 small findings, all fixed (M-217 to M-220).
- 2026-11-22: D10 to D12 decided (ADR-0087): non-finite floats as strings,
  only the tick step's and the safety layer's events, a last line for how
  the run ended (closes #137), old logs converted on demand. Backlog #145
  (build the recorder) and #146 (the adapter's events).
- 2026-11-22: boundary tests part 1 (`a900cb6`); Joe's review of #29 fixed
  (`4a97e68`); ADR-0085 and ADR-0086 built (`92d0ceb`, `e8f7e10`); #29
  closed and logged in `REVIEW.md`.

## In progress

- Nothing.

## Next three

1. Decide the recorder's design points (#145: where it plugs in, the tick's
   timing, the header's settings; C5 of
   `drafts/2026-11-13-code-recommendations.md`), then build it before
   session 7. Opus, high.
2. Decide #142 (a bug-planting tool), due now that the boundary tests are
   done; #144 (rows that wait on a removed backlog row) beside it. Opus,
   high.
3. `ARCHITECTURE.md` still says ADR-0034's details are open (about line
   230); ADR-0087 settled some. Editing it needs Joe's ask. Sonnet, low.

## Explain-backs waiting

Answer by number, such as "E1: ...", in any work session. Claude grades
from `drafts/explain-back-notes.md`; don't open it first.

- **E1.** ADR-0086 checks for a lost link only in `take_snapshot()`. Why
  does that still stop every tick after a lost link before it does anything,
  and which command still raises on its own after one, and why?
- **E2.** A recording writes a NaN battery voltage as the string `"nan"`,
  not as `null`. What would go wrong in a replay test if it wrote `null`?

## Last reviewed

`0846826`, 2026-11-04: the last full row of `REVIEW.md`'s review log. The next
full code review covers everything after it, as the first pull request into
the `reviewed` branch, which doesn't exist yet; the full line-by-line walk
comes after the refactor (W9). Pull requests #24 to #28 reviewed C1,
ADR-0077, ADR-0076 (with ADR-0080), ADR-0081 and ADR-0082 alone, ahead of it;
#29 read ADR-0083 to ADR-0086, up to `e8f7e10`, and is closed unmerged.
