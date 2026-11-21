# Next up

The project's state on one page, read first by a fresh work session.
`/wrap-up` rewrites it at the end of each work session.

**Keep it current.** When an item here finishes (a decision made, a pull
request merged, a step built), update this page in the same step: remove or
move the item, renumber "Next three", and update "Last commit" and
"Uncommitted".

- **Date:** 2026-11-21 (Pacific)
- **Last commit:** `2bf62ae` Review #27 fixes, on `main`, pushed.
  Uncommitted: this wrap-up's records (mistakes M-197 and M-198, backlog
  #133, `REVIEW.md`'s rows for #27 and #28, the work-log row, this brief),
  waiting on Joe's yes to commit; and about 113 files listed as modified
  with no content change, left from ADR-0079's renormalisation.

## Done last

- 2026-11-21: D3 to D6 of `drafts/2026-11-13-code-recommendations.md`
  decided (C3, the tick loop flies the whole flight): D3 B, D4 A, D5 A
  (60 s, raise an error), D6 B (1 s). No ADR written yet; the answers and
  their reasons are in `drafts/c3-c4-decisions-progress.md`.
- 2026-11-21: a boundary-test audit
  (`drafts/2026-11-21-boundary-test-audit.md`): 14 limits with no test at
  exactly the limit, or none near it. Backlog #133.
- 2026-11-21: Joe's two comments on review pull request #27 fixed on `main`
  (`2bf62ae`: the image quality is a `Stamped[int]`; `STALE_AFTER`'s
  placeholder comment gone). #27 and #28 closed unmerged, their `review/`
  branches deleted, their rows added to `REVIEW.md`'s review log.

## In progress

- C3 and C4: D7, D8 and C3's shape questions still to ask, then the
  records. Progress and the list: `drafts/c3-c4-decisions-progress.md`.
- Noticed: `tools/mistakes_log.py write` saves the log with CRLF line
  endings, against ADR-0079 (git converts them on commit).

## Next three

1. Finish C3 and C4: D7 (link lost), D8 (the last-resort landing: check the
   three firmware facts in the 2026.08 source first), C3's shape questions,
   then the ADRs (check the highest number first), ADR-0026's amendment,
   the index, glossary proposals, backlog and mistakes. Opus, high.
2. Joe checks the boundary-test audit (backlog #133) on Opus, Max; then the
   missing tests are written. Opus, high.
3. Build C3 and C4 from their ADRs: the tick step, the safety layer and the
   Crazyflie adapter. Opus, Extra or Max.

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
5. ADR-0081's build choices: a pointer comment in the safety layer's
   placeholder block; the "may be flying" test's status now goes old after
   the take-off grace; a `skip_to_a_whole_second` helper in each adapter
   test file, not a shared one; ADR-0081's Code line reworded; the
   fresh-context read run on Sonnet. **A.** All confirmed. B. Name the ones
   to revisit.
6. M-194 (age-limit tests past the limit but none at it, a third time; M-197
   a fourth). **A.** Add "for a limit, plant a wrong value and the other
   comparison" to the coding style's bug planting. B. Leave it to
   `REVIEW.md`'s question.
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
10. The #27 fixes' choices: the image quality uses the snapshot's existing
    `Stamped` type, with the diagnostic packet's drone time; the project
    review before the commit ran at medium with a 6-step budget, not high.
    **A.** Both confirmed. B. Name the one to revisit.

## Explain-backs waiting

Answer by number, such as "E1: ...", in any work session. Claude grades
from `drafts/explain-back-notes.md`; don't open it first.

- **E1.** For D6 you chose to put the silence in `disconnect()`, not in the
  tick step. Why wouldn't a silence from the tick step be enough for the
  Hover test's "Charge"?

## Last reviewed

`0846826`, 2026-11-04: the last full row of `REVIEW.md`'s review log. The
next full code review covers everything after it, as the first pull
request into the `reviewed` branch, which doesn't exist yet; the full
line-by-line walk comes after the refactor (W9). Pull requests #24 to #28
reviewed C1, ADR-0077, ADR-0076 (with ADR-0080), ADR-0081 and ADR-0082
alone, ahead of it.
