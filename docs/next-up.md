# Next up

The project's state on one page, read first by a fresh work session.
`/wrap-up` rewrites it at the end of each work session.

**Keep it current.** When an item here finishes (a decision made, a pull
request merged, a step built), update this page in the same step: remove or
move the item, renumber "Next three", and update "Last commit" and
"Uncommitted".

- **Date:** 2026-11-17 (Pacific)
- **Last commit:** this brief, on `main`, after `f729668` Records: mistakes
  M-162 to M-173, work log, backlog #118 and #119. `main` isn't pushed (nine
  commits ahead of `origin/main`). Uncommitted: ADR-0077's code, tests and
  records (see In progress); another work session's edits to the `wrap-up`
  and `handoff` skills (they ask before clearing).

## Done last

- 2026-11-17: C1's second `/project-review` (high, `fresh`): 12 findings,
  7 fixed (ADR-0078's missing index row, wording, an unchecked claim
  marked); Joe kept the rest (A2, B none, C2, D2, E1). M-170 to M-173 logged;
  backlog #118 (a glossary section for Python terms?) and #119 (a mechanism
  for line endings) added.
- 2026-11-17: committed C1 (`93c8f5f`, ADR-0035, ADR-0075, ADR-0078; the
  staged tree passed alone), ADR-0076's records (`701a20f`) and the records
  (`f729668`). Review pull request #24 opened (C1 only), with
  `drafts/review-packet-2026-11-17.md`.
- 2026-11-17: ADR-0077 built, not yet reviewed; ADR-0075 to ADR-0078
  decided; First flight 6 set as the flight baseline (backlog #113).

## In progress

- **Pull request #24**, Joe's review of C1: from `review/2026-11-17` into
  `review-base/2026-11-17` (at `44b2406`), so it shows C1 only. Read it in
  PyCharm beside the packet. When done: close it unmerged, delete both
  branches, and add a row to `REVIEW.md`'s review log. `reviewed` doesn't
  exist yet; the full review after `0846826` is still to come (W9).
- **ADR-0077's code is built**; its `/project-review` (Extra, it changes the
  Crazyflie adapter and the safety layer) comes before its commit, which
  names ADR-0077. `start_up.py`'s uncommitted hunks are all ADR-0077's now
  (`make_drone` loses `initial_climb_speed`).

## Next three

1. ADR-0077's `/project-review`, then its fixes and commit. Opus, Extra.
2. Build C5 part 1 of `drafts/2026-11-13-code-recommendations.md`: program
   tests on the sim clock (ADR-0076, backlog #114). Opus, medium.
3. `/decide` backlog #119, a mechanism against scripts changing line
   endings. Sonnet, medium.

## Decisions waiting on Joe

Answer by number and letter, such as "1A". **Bold** is the recommendation.

1. The seven choices made in "Project review C1 (A)", listed in
   `drafts/c1-review-fixes-handoff.md` ("Report back"). **A.** All
   confirmed. B. Name the ones to revisit.
2. The packet's tier questions: `programs/console_output.py` in tier 1 (it
   was split out of `start_up.py`), `pyproject.toml` in tier 3. **A.** Both.
   B. Other tiers.

## Explain-backs waiting

Answer by number, such as "E1: ...", in any work session. Claude grades
from `drafts/explain-back-notes.md`; don't open it first.

- **E1.** Our console handler takes no lock, yet a console write that got
  stuck still kept the program from ending, when standard error was
  buffered. What held it?

The review packet has four more, for pull request #24.

## Last reviewed

`0846826`, 2026-11-04: the last row of `REVIEW.md`'s review log. The next
full code review covers everything after it, as the first pull request into
the `reviewed` branch. The full line-by-line walk comes after the refactor
(W9). Pull request #24 reviews C1 alone, ahead of that.
