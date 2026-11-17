# Next up

The project's state on one page, read first by a fresh work session.
`/wrap-up` rewrites it at the end of each work session.

**Keep it current.** When an item here finishes (a decision made, a pull
request merged, a step built), update this page in the same step: remove or
move the item, renumber "Next three", and update "Last commit" and
"Uncommitted".

- **Date:** 2026-11-17 (Pacific)
- **Last commit:** `0a13d82`, the merge of pull request #23 into `main`.
  Uncommitted: ADR-0075 with its index row, ADR-0035's amendment, the
  facts register, backlog #113 removed, the work log's goal 5, and this
  brief.

## Done last

- 2026-11-17: decided 1A, ADR-0075 (at exit, the console gets 2 s, then a
  warning goes to the log file). Decided backlog #113: the flight baseline
  is First flight 6 (2026-11-14), with a regression suite (goal 5 in the
  work log).
- 2026-11-16: pull request #23 merged (six project skills, this brief,
  the `tools/mistakes_log.py` fixes).

## In progress

Nothing.

## Next three

1. Commit the uncommitted docs above. Sonnet, low.
2. Build C1 of `drafts/2026-11-13-code-recommendations.md`: console output
   on a background thread (ADR-0035, ADR-0075). Tick-loop code, so
   `/project-review` before committing. Opus, Extra.
3. Decide 1 below, then build C5 part 1: program tests on the sim clock.
   Medium.

Items 2 and 3 follow that doc's suggested order, which Joe hasn't decided.

## Decisions waiting on Joe

Answer by number and letter, such as "1A". **Bold** is the recommendation.

1. (D9, for C5 part 1) The clock in program tests. **A.** The sim clock,
   except one real-clock test per program. B. As today.

The code doc's other decisions (D2 to D8, D10 to D20) come with their items.

## Last reviewed

`0846826`, 2026-11-04: the last row of `REVIEW.md`'s review log. The next
code review covers everything after it, as the first pull request into the
`reviewed` branch. The full line-by-line walk comes after the refactor (W9).
