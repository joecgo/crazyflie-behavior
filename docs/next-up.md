# Next up

The project's state on one page, read first by a fresh work session.
`/wrap-up` rewrites it at the end of each work session.

**Keep it current.** When an item here finishes (a decision made, a pull
request merged, a step built), update this page in the same step: remove or
move the item, renumber "Next three", and update "Last commit" and
"Uncommitted".

- **Date:** 2026-11-22 (Pacific)
- **Last commit:** this brief, with the work-log row and the backlog, after
  `3833131` (mistake M-206), on `main`, pushed. Uncommitted: nothing.

## Done last

- 2026-11-22: boundary tests, part 1 (#133, `a900cb6`): rows 1-3, 7, 12-15
  and 17, every planted bug caught but the hover tolerance's `<` (as
  chosen). Row 14's "after" test moved to 0.01 s past the limit (Joe's
  choice; M-206).
- 2026-11-22: Joe's review of #29 fixed (`4a97e68`); ADR-0085 and ADR-0086
  decided and built (`92d0ceb`, `e8f7e10`); #29 closed and logged in
  `REVIEW.md`. Mistakes M-207 to M-215, Q-55 and Q-56.
- 2026-11-21: ADR-0083 and ADR-0084 built (`1b673f9`): every flight end
  lands inside the tick loop, and a lost link ends the run with an error,
  with the firmware's land as the last-resort landing. `/project-review max`
  found 13 problems, all fixed (`0363756`); its three code fixes have new
  tests, each proven by bug planting.
- 2026-11-21: review pull request #29 opened for both ADRs, with 36 comments
  (the 13 findings and 23 build notes). Packet:
  `drafts/review-packets/2026-11-21-adr-0083-0084.md`.
- 2026-11-21: the boundary-test audit checked by planting 97 bugs
  (`drafts/2026-11-21-boundary-test-audit.md`; scripts in
  `drafts/2026-11-21-boundary-audit/`): 20 limits where a planted bug passes
  every test. Joe chose the tests (backlog #133). Explain-backs E1 to E3
  answered.

## In progress

- Noticed: `tools/mistakes_log.py write` saves the log with CRLF line
  endings, against ADR-0079 (git converts them on commit).

## Next three

1. Boundary tests, part 2 (#133): rows 4-6, 8-11 and 18-20 (adapter, safety
   layer and mock tests), with #140. ADR-0083 to ADR-0086 moved lines in
   those files: re-find each row's code first. Time each step from 0.0;
   prove each by planting its row's bugs (`recheck.py`, in a scratch copy).
   Check each row's results file entries, not just its table row (M-206).
   Opus, high.
2. Decide D10 to D12 (C5's recordings and replay tests,
   `drafts/2026-11-13-code-recommendations.md`). Opus, high.
3. The decisions waiting below (answer by number). Sonnet, medium.

## Decisions waiting on Joe

Answer by number and letter, such as "1A". **Bold** is the recommendation.

1. The seven choices made in "Project review C1 (A)"
   (`drafts/c1-review-fixes-handoff.md`, "Report back"). **A.** All
   confirmed. B. Name the ones to revisit.
2. #24's packet tiers: `programs/console_output.py` in tier 1,
   `pyproject.toml` in tier 3. **A.** Both. B. Other tiers.
3. ADR-0080's build choices (`_fail_after`, gone since ADR-0082; one bench
   test advances the clock 10 s; the bench tick-step tests take the fixture;
   the comment "Stops a hung run"; findings 3 and 4 as one mistake, M-187).
   **A.** All confirmed. B. Name the ones to revisit.
4. M-192 (a failure named for one reading without checking its log block).
   **A.** Add a `REVIEW.md` question. B. No question.
5. ADR-0081's build choices (the pointer comment in the safety layer; the
   "may be flying" test's status going old after the grace; a
   `skip_to_a_whole_second` per adapter test file; the reworded Code line;
   the fresh read on Sonnet). **A.** All confirmed. B. Name the ones to revisit.
6. M-194, boundary tests (now M-197 and M-202 too). A. Add "for a limit, plant
   a wrong value and the other comparison" to the coding style. B. Leave it to
   `REVIEW.md` Q-48. **C.** `/decide` a bug-planting tool from the audit's
   script: it found what reading missed, in about 9 minutes.
7. M-193 (Built "Yes" with no test citing the ADR). **A.** A test that each
   plain "Yes" in the ADR index is cited by a test. B. Leave it to the
   project review.
8. ADR-0082's build choices (`SIM_TIME_LIMIT`; the tests hard-code 120 s;
   one test's two loops share a clock; `clock = sim_clock` kept). **A.** All
   confirmed. B. Name the ones to revisit.
9. M-196: check PyCharm's Local History of `loop/tick_loop.py` for a change
   lost on 2026-11-20 (very likely line endings only). **A.** Checked,
   nothing lost. B. Something was lost (say what).
10. The #27 fixes' choices (the image quality as a `Stamped` value; that
    review at medium, 6 steps). **A.** Both confirmed. B. Name the one.
11. A release that raises in the last-resort landing (a project review fix in
    `0363756`). **A.** Keep the 6.7 s wait with the link open once the land
    went out, as built. B. Skip the wait, as before the fix.

## Explain-backs waiting

Answer by number, such as "E1: ...", in any work session. Claude grades
from `drafts/explain-back-notes.md`; don't open it first.

- **E1.** ADR-0086 checks for a lost link only in `take_snapshot()`. Why
  does that still stop every tick after a lost link before it does anything,
  and which command still raises on its own after one, and why?

## Last reviewed

`0846826`, 2026-11-04: the last full row of `REVIEW.md`'s review log. The next
full code review covers everything after it, as the first pull request into
the `reviewed` branch, which doesn't exist yet; the full line-by-line walk
comes after the refactor (W9). Pull requests #24 to #28 reviewed C1,
ADR-0077, ADR-0076 (with ADR-0080), ADR-0081 and ADR-0082 alone, ahead of it;
#29 read ADR-0083 to ADR-0086, up to `e8f7e10`, and is closed unmerged.
