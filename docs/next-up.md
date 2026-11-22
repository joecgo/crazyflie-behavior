# Next up

The project's state on one page, read first by a fresh work session.
`/wrap-up` rewrites it at the end of each work session.

**Keep it current.** When an item here finishes (a decision made, a pull
request merged, a step built), update this page in the same step: remove or
move the item, renumber "Next three", and update "Last commit" and
"Uncommitted".

- **Date:** 2026-11-21 (Pacific)
- **Last commit:** this brief, after `585266a` (REVIEW.md Q-54, work log), on
  `main`. Uncommitted: the ADR-0083 and ADR-0084 build, in progress in
  another work session (`src/`: the adapter, interface, tick loop, tick step,
  safety layer, bench); about 113 files modified with no content change
  (ADR-0079's renormalisation).

## Done last

- 2026-11-21: the boundary-test audit checked by planting 97 bugs
  (`drafts/2026-11-21-boundary-test-audit.md`; scripts in
  `drafts/2026-11-21-boundary-audit/`): 20 limits where a planted bug passes
  every test, among them a 0.06 s touchdown hold. Joe chose the tests (backlog
  #133), 1 mm either side for the height tolerances, and `REVIEW.md` Q-54.
  Mistakes M-201 to M-203; backlog #139, #140.
- 2026-11-21: C3's and C4's records committed (`fb2a68f` to `ea5c7fb`):
  ADR-0083 and ADR-0084 (Built: No, backlog #134, #135), the facts register,
  M-199 and M-200.

## In progress

- **The ADR-0083 and ADR-0084 build** (backlog #134, #135), in another work
  session in this working copy, then `/project-review max`. That work session
  writes the shared records after this brief; re-read them first.
- Noticed: `tools/mistakes_log.py write` saves the log with CRLF line
  endings, against ADR-0079 (git converts them on commit).

## Next three

1. Boundary tests, part 1 (#133), in files the build doesn't touch:
   rows 1-3, 7, 12-15 and 17 of the checked audit's "Test to add"
   (`test_touchdown.py`, `test_bad_flow_zone.py`, the three behavior tests).
   Time each step from 0.0; prove each by planting its row's bugs
   (`recheck.py`). Opus, high.
2. Boundary tests, part 2, once the build is committed: rows 4-6, 8-11 and
   18-20 (adapter, safety layer and mock tests), with #140. Opus, high.
3. Decide D10 to D12 (C5's recordings and replay tests,
   `drafts/2026-11-13-code-recommendations.md`). Opus, high.

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

## Explain-backs waiting

Answer by number, such as "E1: ...", in any work session. Claude grades
from `drafts/explain-back-notes.md`; don't open it first.

- **E1 (ADR-0083).** After a stop request in flight, the tick step keeps
  ticking until the drone is down. Why must it still run the safety
  pre-check and the take-off and landing update on those ticks, but not the
  behaviors? And if a bug in that new code leaves the drone hovering, what
  ends the program?
- **E2 (ADR-0084).** Why does the last-resort landing send the firmware's
  land before it releases the setpoint priority? And name two cases where it
  doesn't help at all.
- **E3 (boundary tests).** A `>=` time limit needs two tests to pin it.
  Which two, which planted bug does each catch, and why must the step be
  timed from 0.0 (or a test can't tell `>` from `>=`)?

## Last reviewed

`0846826`, 2026-11-04: the last full row of `REVIEW.md`'s review log. The next
full code review covers everything after it, as the first pull request into
the `reviewed` branch, which doesn't exist yet; the full line-by-line walk
comes after the refactor (W9). Pull requests #24 to #28 reviewed C1,
ADR-0077, ADR-0076 (with ADR-0080), ADR-0081 and ADR-0082 alone, ahead of it.
