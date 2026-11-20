# Next up

The project's state on one page, read first by a fresh work session.
`/wrap-up` rewrites it at the end of each work session.

**Keep it current.** When an item here finishes (a decision made, a pull
request merged, a step built), update this page in the same step: remove or
move the item, renumber "Next three", and update "Last commit" and
"Uncommitted".

- **Date:** 2026-11-20 (Pacific)
- **Last commit:** `edbc4a9` Build ADR-0082 (its records in `46c231b`),
  on `main`, pushed, with today's work-log row. Uncommitted: nothing but
  about 113 files listed as modified with no content change, left from
  ADR-0079's renormalisation; not looked into.

## Done last

- 2026-11-20: backlog #129 decided and built as ADR-0082: every test that
  runs the tick loop on a sim clock has the 120 s limit (the fixture moved
  to `tests/conftest.py`); a fitness function bans a plain `SimClock()` or
  a new subclass in `tests/programs/` and `tests/loop/` (`LateWakingClock`
  excepted, Joe's choice); a test of the limit. 760 tests pass; every
  planted bug failed a test. New backlog #132. Glossary: *Sim time*.
- 2026-11-20: review pull request #27 opened for ADR-0081's build
  (`9914b68..fab1d5d`), with its packet and the project review's findings
  as comments; continuous integration green.
- 2026-11-19 and 20: ADR-0081 built (`fab1d5d`; its records in `9914b68`):
  `STALE_AFTER` (0.25 s) in `drone/interface.py`, `MAX_READING_AGE` gone.
  Every age check is tested one tick past and at exactly the limit; four
  couldn't tell 0.25 s from 0.5 s before. The glossary's *Stale value*
  reworded. Backlog #120 and #130 closed.
- 2026-11-19: `/project-review` (high, fresh) of the build: nine findings,
  four fixed. No fitness function for "one age limit" for now and no backlog
  row; ARCHITECTURE.md left as it is (Joe's choices). The fresh read's 32
  items in older code: `drafts/2026-11-19-fresh-read-pre-existing.md`.

## In progress

- Review pull request #28 (ADR-0082's build, `fab1d5d..edbc4a9`), open
  for Joe, with no project review run on it. Packet:
  `drafts/review-packets/2026-11-20-adr-0082.md`.
- Review pull request #27 (ADR-0081's build), open for Joe. Packet:
  `drafts/review-packets/2026-11-20-adr-0081.md`.
- Noticed: `tools/mistakes_log.py write` saves the log with CRLF line
  endings, against ADR-0079 (git converts them on commit).

## Next three

1. After Joe reads #27: fixes for his comments on `main`, then close it
   unmerged, delete `review/2026-11-20-adr-0081` (keep `review-base/…`) and
   add its row to `REVIEW.md`'s review log. Sonnet, medium (Opus, high if a
   comment asks for a code change).
2. After Joe reads #28: the same as step 1, for `review/2026-11-20-adr-0082`.
   Sonnet, medium.
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
   one mistake, M-187. (`_fail_after` is gone in ADR-0082's build.) **A.** All confirmed. B. Name the ones to revisit.
4. M-192 (a failure named for one reading without checking what shares its
   log block): a code-review takeaway. **A.** Add a `REVIEW.md` question. B.
   No question.
5. ADR-0081's build choices: `STALE_AFTER` after `FLOOR_MAX_SPEED` with its
   own placeholder comment; a pointer comment in the safety layer's
   placeholder block; the "may be flying" test's status now goes old after
   the take-off grace; a `skip_to_a_whole_second` helper in each adapter
   test file, not a shared one; ADR-0081's Code line reworded; the
   fresh-context read run on Sonnet. **A.** All confirmed. B. Name the ones
   to revisit.
6. M-194 (age-limit tests past the limit but none at it, a third time).
   **A.** Add "for a limit, plant a wrong value and the other comparison" to
   the coding style's bug planting. B. Leave it to `REVIEW.md`'s question.
7. M-193 (Built "Yes" with no test citing the ADR). **A.** A test that each
   plain "Yes" in the ADR index is cited by a test. B. Leave it to the
   project review.

8. ADR-0082's build choices: the limit renamed `SIM_TIME_LIMIT`; the
   tests of the limit hard-code 120 s (`conftest.py` can't be imported);
   `test_the_log_says_why_the_loop_stopped`'s two loops share one clock;
   each changed test keeps `clock = sim_clock`. **A.** All confirmed. B.
   Name the ones to revisit.
9. M-196: before trusting `src/crazyflie_behavior/loop/tick_loop.py`,
   check PyCharm's Local History for an uncommitted change lost on
   2026-11-20 (very likely line endings only). **A.** Checked, nothing
   lost. B. Something was lost (say what).

## Explain-backs waiting

Answer by number, such as "E1: ...", in any work session. Claude grades
from `drafts/explain-back-notes.md`; don't open it first.

- **E1.** The program tests now run on a sim clock. What kind of bug can a
  sim-clock test never catch, and which tests still catch it?
- **E2.** The program tests' time-limited sim clock stops a test with
  `pytest.fail`, not an ordinary `AssertionError`. Why would an
  `AssertionError` let a program that never ends pass its test?
- **E3.** ADR-0081 shortens the age limit for confirming touchdown from
  0.5 s to 0.25 s. Why can that make the motors stop later, but never
  earlier?
- **E4.** Bug planting found four age checks whose tests still passed with
  the old 0.5 s limit put back. Why couldn't those tests tell 0.25 s from
  0.5 s, and what does a test at exactly the limit catch that a test one
  tick past it doesn't?

## Last reviewed

`0846826`, 2026-11-04: the last full row of `REVIEW.md`'s review log. The
next full code review covers everything after it, as the first pull
request into the `reviewed` branch, which doesn't exist yet; the full
line-by-line walk comes after the refactor (W9). Pull requests #24 to #26
reviewed C1, ADR-0077 and ADR-0076 (with ADR-0080) alone, ahead of it; #27
(ADR-0081) is open.
