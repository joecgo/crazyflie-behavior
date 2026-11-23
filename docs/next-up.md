# Next up

The project's state on one page, read first by a fresh work session.
`/wrap-up` rewrites it at the end of each work session.

**Keep it current.** When an item here finishes (a decision made, a pull
request merged, a step built), update this page in the same step: remove or
move the item, renumber "Next three", and update "Last commit" and
"Uncommitted".

- **Date:** 2026-11-22 (Pacific)
- **Last commit:** the recorder (#145), its tests and its records, then this
  brief, on `main`, pushed.
  Uncommitted: nothing (today's work-log row waits for `/wrap-up`).

## Done last

- 2026-11-22: the recorder built (ADR-0034, ADR-0087, ADR-0088; #145
  removed): `recording/` (the format, `read_recording`, the recorder),
  `SafetyLayer.events_this_tick`, the tick step's recording, the tick
  loop's `on_tick_measured`; every program records to `recordings/`. 87
  planted bugs, all caught. `/project-review high` with `fresh`: no
  correctness bug, 12 small findings, not fixed: Joe wants them as comments
  on the review's pull request. Measured on this laptop: the write takes about
  85 µs a tick, 4.3 ms at worst in 18,000 ticks. #148 added (a converter
  for old logs, ADR-0087).
- 2026-11-22: #145's design points decided (ADR-0088, all four as
  recommended): the tick step holds the recorder and wraps `ask`; the tick
  loop's optional `on_tick_measured`; the header's settings are the
  command-line arguments and whether the tree was clean; a write error stops
  the recording, not the flight. #147 added (C7, tuning values).
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

- The review of everything after `e8f7e10` (the "Next" row of `REVIEW.md`'s
  review log), the recorder included: committed and pushed; the review
  packet and pull request are next.

## Next three

1. The review's packet and pull request: `/review-packet` on
   `e8f7e10..main`, then the pull request the way #24 to #29 were opened
   (a `review-base/*` branch at the range's start; `REVIEW.md`'s review
   log). Post each finding in `drafts/review-findings-2026-11-22-recorder.md`
   as its own comment at its line, as one review: Joe asked for this on
   2026-11-22 ("save each finding as a comment in the PR for the code
   review"). The project review ran in an earlier context, so the packet
   takes its findings from that file. Confirm before pushing the review
   branches. Opus, high.
2. Decide #142 (a bug-planting tool), due now that the boundary tests are
   done; #144 (rows that wait on a removed backlog row) beside it. Opus,
   high.
3. Decide #55 (where analysis scripts live): the recorder drops the text
   log's snapshot line, which breaks the scripts in `drafts/`, so the two
   go together. Opus, high.

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

## Last reviewed

`0846826`, 2026-11-04: the last full row of `REVIEW.md`'s review log. The next
full code review covers everything after it, as the first pull request into
the `reviewed` branch, which doesn't exist yet; the full line-by-line walk
comes after the refactor (W9). Pull requests #24 to #28 reviewed C1,
ADR-0077, ADR-0076 (with ADR-0080), ADR-0081 and ADR-0082 alone, ahead of it;
#29 read ADR-0083 to ADR-0086, up to `e8f7e10`, and is closed unmerged.
