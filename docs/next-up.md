# Next up

The project's state on one page, read first by a fresh work session.
`/wrap-up` rewrites it at the end of each work session.

**Keep it current.** When an item here finishes (a decision made, a pull
request merged, a step built), update this page in the same step: remove or
move the item, renumber "Next three", and update "Last commit" and
"Uncommitted".

- **Date:** 2026-11-18 (Pacific)
- **Last commit:** `b27ea67` Review packets list code that supports the
  tests and never a bare "the same"; mistakes M-190 and M-191, on `main`.
  Uncommitted: nothing of substance. `git status` lists about 113 files as
  modified with no content change, left from ADR-0079's renormalisation;
  not looked into.

## Done last

- 2026-11-18: review pull request #26 (ADR-0076 with ADR-0080) read by Joe
  with no comments and closed unmerged; `review/2026-11-18-adr-0076`
  deleted, `review-base/…` kept; its row is in `REVIEW.md`'s review log.
- 2026-11-18: `/project-review` (high) of ADR-0080's build, `f66702c`:
  seven findings, none fixed, now backlog #129.
- 2026-11-18: `/review-packet` lists code that supports the tests (a
  `conftest.py`, a shared fake) and names every row's change, never a bare
  "the same" (mistake M-191).
- 2026-11-18: ADR-0076, ADR-0079 and ADR-0080 decided and built (the
  program tests on the sim clock, LF line endings, the 120 s sim-time limit).

## In progress

- Nothing open. Noticed: `tools/mistakes_log.py write` saves the log with
  CRLF line endings, against ADR-0079 (git converts them on commit).

## Next three

1. `/decide` backlog #120, how fresh the initial climb's flow check must be
   (0.5 s now, or the safety layer's 0.25 s); needed before the next field
   session. Opus, high.
2. Backlog #129, ADR-0080's review findings: decide where the sim-time
   limit applies (the start-up tests, `tests/loop/`, one shared bounded
   clock, a fitness function), then the fixes. Opus, high.
3. D3 to D8 of `drafts/2026-11-13-code-recommendations.md` (C3 with C4).
   Opus, high.

## Decisions waiting on Joe

Answer by number and letter, such as "1A". **Bold** is the recommendation.

1. The seven choices made in "Project review C1 (A)", listed in
   `drafts/c1-review-fixes-handoff.md` ("Report back"). **A.** All
   confirmed. B. Name the ones to revisit.
2. The tier questions in #24's packet: `programs/console_output.py` in tier
   1, `pyproject.toml` in tier 3. **A.** Both. B. Other tiers.
3. ADR-0080's build choices: the private name `_fail_after`; one bench test
   advances the clock 10 s instead of starting it at 10 s; the bench
   tick-step tests take the fixture though they can't run forever; the
   workflow comment "Stops a hung run"; review findings 3 and 4 logged as
   one mistake, M-187. **A.** All confirmed. B. Name the ones to revisit.

## Explain-backs waiting

Answer by number, such as "E1: ...", in any work session. Claude grades
from `drafts/explain-back-notes.md`; don't open it first.

- **E1.** The program tests now run on a sim clock. What kind of bug can a
  sim-clock test never catch, and which tests still catch it?
- **E2.** The program tests' time-limited sim clock stops a test with
  `pytest.fail`, not an ordinary `AssertionError`. Why would an
  `AssertionError` let a program that never ends pass its test?

## Last reviewed

`0846826`, 2026-11-04: the last full row of `REVIEW.md`'s review log. The
next full code review covers everything after it, as the first pull
request into the `reviewed` branch, which doesn't exist yet; the full
line-by-line walk comes after the refactor (W9). Pull requests #24, #25 and
#26 reviewed C1, ADR-0077 and ADR-0076 (with ADR-0080) alone, ahead of it.
