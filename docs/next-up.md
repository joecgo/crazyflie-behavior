# Next up

The project's state on one page, read first by a fresh work session.
`/wrap-up` rewrites it at the end of each work session.

**Keep it current.** When an item here finishes (a decision made, a pull
request merged, a step built), update this page in the same step: remove or
move the item, renumber "Next three", and update "Last commit" and
"Uncommitted".

- **Date:** 2026-11-17 (Pacific)
- **Last commit:** `839fb7a` Records: mistakes M-182 to M-184, work log,
  backlog #125 and #126, on `main`, pushed with this brief. Uncommitted:
  nothing.

## Done last

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

- **Pull request #25**, Joe's review of ADR-0077: from
  `review/2026-11-17-adr-0077` into `review-base/2026-11-17-adr-0077` (at
  `4204007`), so it shows ADR-0077 only. Read it in PyCharm beside the
  packet. Fixes go on `main`, never on the review branch (M-184). When done:
  close it unmerged, delete both branches, and add a row to `REVIEW.md`'s
  review log.

## Next three

1. Build C5 part 1 of `drafts/2026-11-13-code-recommendations.md`: program
   tests on the sim clock (ADR-0076, backlog #114). Opus, medium.
2. `/decide` backlog #119, a mechanism against scripts changing line
   endings. Sonnet, medium.
3. `/decide` backlog #120, how fresh the initial climb's flow check must be
   (0.5 s now, or the safety layer's 0.25 s), with #121's glossary terms;
   needed before the next field session. Opus, high.

## Decisions waiting on Joe

Answer by number and letter, such as "1A". **Bold** is the recommendation.

1. The seven choices made in "Project review C1 (A)", listed in
   `drafts/c1-review-fixes-handoff.md` ("Report back"). **A.** All
   confirmed. B. Name the ones to revisit.
2. The tier questions in #24's packet: `programs/console_output.py` in tier
   1 (it was split out of `start_up.py`), `pyproject.toml` in tier 3.
   **A.** Both. B. Other tiers.
3. Pull request #24's leftovers: its branches `review/2026-11-17` and
   `review-base/2026-11-17` on GitHub, and its row in `REVIEW.md`'s review
   log. **A.** Claude deletes both branches and adds the row. B. Later,
   with #25's.

## Explain-backs waiting

Answer by number, such as "E1: ...", in any work session. Claude grades
from `drafts/explain-back-notes.md`; don't open it first.

- **E1.** Our console handler takes no lock, yet a console write that got
  stuck still kept the program from ending, when standard error was
  buffered. What held it?
- **E2.** The climb's check read "no down range, or under 0.15 m: keep
  climbing; otherwise hand over". Why did a NaN down range hand over, when
  the old "at or above the height: hand over" kept climbing?

Each review packet has four more: #24's in
`drafts/review-packets/2026-11-17.md`, #25's in
`drafts/review-packets/2026-11-17-adr-0077.md`.

## Last reviewed

`0846826`, 2026-11-04: the last row of `REVIEW.md`'s review log. The next
full code review covers everything after it, as the first pull request into
the `reviewed` branch, which doesn't exist yet. The full line-by-line walk
comes after the refactor (W9). Pull requests #24 and #25 review C1 and
ADR-0077 alone, ahead of that.
