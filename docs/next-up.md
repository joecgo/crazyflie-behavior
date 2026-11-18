# Next up

The project's state on one page, read first by a fresh work session.
`/wrap-up` rewrites it at the end of each work session.

**Keep it current.** When an item here finishes (a decision made, a pull
request merged, a step built), update this page in the same step: remove or
move the item, renumber "Next three", and update "Last commit" and
"Uncommitted".

- **Date:** 2026-11-18 (Pacific)
- **Last commit:** `5d1181f` Next-up brief: review #25 closed, on `main`.
  The next commits (ADR-0076 built; ADR-0079 and this brief) are pushed
  with it.

## Done last

- 2026-11-18: ADR-0079 decided: every text file uses LF line endings, in
  the repository and the working copy (`.gitattributes`, `.editorconfig`);
  no fitness function, a risk Joe accepted. Backlog #119 closed; #127 builds
  it (the two files, then a renormalise of the 119 CRLF working files on a
  clean tree). Joe skipped the explain-back (line endings aren't a topic he
  wants to be tested on).
- 2026-11-18: ADR-0076 built: `main()` takes an optional clock in the four
  programs, and their tests run on the sim clock with the real waits. Suite
  38.5 s to 19.5 s; 751 passed; five planted bugs caught. Joe confirmed the
  four build choices and chose no failsafe real-clock test (noted in the
  ADR).
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

1. Build backlog #127 (ADR-0079: `.gitattributes`, `.editorconfig`, the
   renormalise), on a clean tree. Sonnet, low.
2. `/decide` backlog #120, how fresh the initial climb's flow check must be
   (0.5 s now, or the safety layer's 0.25 s);
   needed before the next field session. Opus, high.
3. `/decide` D3 to D8 of `drafts/2026-11-13-code-recommendations.md`, for
   C3 with C4 (the tick loop flies the whole flight; link lost as a
   state), next in its suggested order. Opus, high.

## Decisions waiting on Joe

Answer by number and letter, such as "1A". **Bold** is the recommendation.

1. The seven choices made in "Project review C1 (A)", listed in
   `drafts/c1-review-fixes-handoff.md` ("Report back"). **A.** All
   confirmed. B. Name the ones to revisit.
2. The tier questions in #24's packet: `programs/console_output.py` in tier
   1 (it was split out of `start_up.py`), `pyproject.toml` in tier 3.
   **A.** Both. B. Other tiers.

## Explain-backs waiting

Answer by number, such as "E1: ...", in any work session. Claude grades
from `drafts/explain-back-notes.md`; don't open it first.

- **E1.** The program tests now run on a sim clock. What kind of bug can a
  sim-clock test never catch, and which tests still catch it?

## Last reviewed

`0846826`, 2026-11-04: the last row of `REVIEW.md`'s review log. The next
full code review covers everything after it, as the first pull request into
the `reviewed` branch, which doesn't exist yet. The full line-by-line walk
comes after the refactor (W9). Pull requests #24 and #25 review C1 and
ADR-0077 alone, ahead of that.
