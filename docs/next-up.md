# Next up

The project's state on one page, read first by a fresh work session.
`/wrap-up` rewrites it at the end of each work session.

**Keep it current.** When an item here finishes (a decision made, a pull
request merged, a step built), update this page in the same step: remove or
move the item, renumber "Next three", and update "Last commit" and
"Uncommitted".

- **Date:** 2026-11-17 (Pacific)
- **Last commit:** `c19e1e7` Records: mistake M-186, work log, on `main`,
  pushed with this brief. Uncommitted: C5 part 1's work so far in
  `programs/` (bench, failsafe, hover, rescue landing) and
  `tests/programs/`, not checked or reviewed yet. The program tests still
  flake on the real clock, with and without it.

## Done last

- 2026-11-17: Joe finished reviewing pull request #25. #24 and #25 are
  closed unmerged with review-log rows; their `review/*` branches are deleted,
  and their `review-base/*` branches are kept so the diffs stay viewable. The
  placeholder comment is gone from `bad_flow_zone.py` (ADR-0077 unchanged).
  Glossary: *Flow* and *Hand-over* added, and *Stale value* names fresh as
  its opposite (backlog #121 closed). Mistake M-186 logged.
- 2026-11-17: ADR-0077 committed (`f973e8a`; the staged tree passed alone:
  751 tests, Ruff, Pyright), then its mistakes M-174 to M-181. Review pull
  request #25 opened, ADR-0077 only, with
  `drafts/review-packets/2026-11-17-adr-0077.md`; its 12 findings are
  comments, rebuilt from the records of ADR-0077's two project reviews
  (backlog #125). Continuous integration passes.
- 2026-11-17: Joe reviewed C1 in pull request #24, now closed; his fixes
  are on `main` (`d404629`: `_CONSOLE_LEVEL` dropped, two coding-style
  rules). Mistakes M-182 to M-184 logged; backlog #126 (a mechanism against
  pushes to an open review branch) added.
- 2026-11-17: ADR-0077's two `/project-review` runs (Extra; Extra with a
  fresh read): 17 findings, all fixed but backlog #120 to #124.

## In progress

None.

## Next three

1. Build C5 part 1 of `drafts/2026-11-13-code-recommendations.md`: program
   tests on the sim clock (ADR-0076, backlog #114). Opus, medium.
2. `/decide` backlog #119, a mechanism against scripts changing line
   endings. Sonnet, medium.
3. `/decide` backlog #120, how fresh the initial climb's flow check must be
   (0.5 s now, or the safety layer's 0.25 s);
   needed before the next field session. Opus, high.

## Decisions waiting on Joe

Answer by number and letter, such as "1A". **Bold** is the recommendation.

1. The seven choices made in "Project review C1 (A)", listed in
   `drafts/c1-review-fixes-handoff.md` ("Report back"). **A.** All
   confirmed. B. Name the ones to revisit.
2. The tier questions in #24's packet: `programs/console_output.py` in tier
   1 (it was split out of `start_up.py`), `pyproject.toml` in tier 3.
   **A.** Both. B. Other tiers.

## Explain-backs waiting

None waiting. E1 and E2 and the eight in the review packets (#24's in
`drafts/review-packets/2026-11-17.md`, #25's in
`drafts/review-packets/2026-11-17-adr-0077.md`) were graded 2026-11-17.

## Last reviewed

`0846826`, 2026-11-04: the last row of `REVIEW.md`'s review log. The next
full code review covers everything after it, as the first pull request into
the `reviewed` branch, which doesn't exist yet. The full line-by-line walk
comes after the refactor (W9). Pull requests #24 and #25 review C1 and
ADR-0077 alone, ahead of that.
