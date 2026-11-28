# Next up

The project's state on one page, read first by a fresh work session.
`/wrap-up` rewrites it at the end of each work session.

**Keep it current.** When an item here finishes (a decision made, a pull
request merged, a step built), update this page in the same step: remove or
move the item, renumber "Next three", and update "Last commit" and
"Uncommitted".

- **Date:** 2026-11-27 (Pacific)
- **Last commit:** the records after the tour's copy to the portfolio,
  pushed. Uncommitted: ADR-0091's test and its records.

## Done last

- **ADR-0091's test built** (2026-11-27, #153):
  `tests/docs/test_work_dependencies.py`, with *Work dependency* in the
  glossary. Rows #153 and #157 removed. Not committed.
- **The tour's publishing built** (2026-11-27, ADR-0096): the visit-count
  line and the skill's copy step. Copied to joecgo.com from `06c4d2d`
  (`joecgo/portfolio` `85be341`), the footer's first-draft line dropped;
  the live page matched.
- **The tour's first chapter accepted** (2026-11-27) and
  [ADR-0096](decisions/0096-the-project-tour-is-one-html-page-per-chapter-pinned-to-one-commit.md)
  written: the tour's form, checks and publishing.
- **The tour linked** (2026-11-27): one line under the README's title, and on
  the joecgo.com project card as the first link (repository second), with a
  screenshot of section 5's flight animation (`media/tour-flight.png` in
  `joecgo/portfolio`). The screenshot is a hand copy, like the tour (#168).
- **Tour feedback pass, #166 and #167** (`0251d46`, `8625016`, `bd956cc`),
  pushed, with continuous integration passing. The pin is `0251d46`. The
  pop-ups and module sizes come from the pinned commit, and
  `tests/docs/test_tour_dots.py` fails on a missing dot.
- **Published to joecgo.com/crazyflie-project-tour:** `bd956cc`'s three files,
  pushed to `joecgo/portfolio` as `1be1e1c`; the live files matched.

## In progress

- The private preview (version 8,
  https://claude.ai/artifact/XWPWS3fCf52696zXq6ZkJp) is behind: its links name
  the old pin, `5050718`. Republishing it needs a Read of every line of its
  saved copy first (about 55k tokens), so only do it if Joe wants a preview.
- Joe's review of pull request #31. When he's done: fix what he asks on
  `main`, close it unmerged like the earlier review pull requests, and give
  `REVIEW.md`'s log its row.

## Next three

1. Joe's review of pull request #31, then its fixes. Opus, high.
2. #165, cutting the transcript tests to two or three. Sonnet, medium.
3. #158, one shared cflib fake, which needs a test-layout decision first
   (`/decide`). Opus, high.

## Explain-backs waiting

Answer by number, such as "E1: ...", in any work session. Claude grades
from `drafts/explain-back-notes.md`; don't open it first.

- **E13.** Stage 4's take-off and landing part keeps the commands object it
  was built with. What would go wrong if `connect()` built the part before
  its new commands, in which flight would it show, and why did the five
  transcript flights miss it?
- **E14.** A Ctrl+C while connecting can come out of `Thread.start()` as
  `RuntimeError: release unlocked lock` (ADR-0094). Why did the radio link
  still close, why does `run_with_time_limit` raise the KeyboardInterrupt
  after its `except` block rather than inside it, and why did the test that
  sends a real signal fail only about once in a hundred runs?
- **E15.** Stage 5 moved the log blocks into `log_blocks.py`, and
  `connect()` now builds a fresh log-block part instead of resetting four
  fields by hand. Why do the other parts read the telemetry buffer through
  `log_blocks.telemetry` on every call instead of keeping it, which two
  places replace the buffer, and why could the clearing of the log blocks at
  the link close be dropped?
- **E16.** Stage 6 moved the link into `link.py`. `CrazyflieLink.close()`
  takes `radio_link_only` as a required keyword argument, which the
  adapter's `_close_link()` works out as `is_airborne` or the
  unknown-state flag. Which flight would end with a dropped drone if
  `_close_link()` ignored `is_airborne`, why doesn't the link part work it
  out itself, and what catches the mistake?
- **E17.** ADR-0095 makes `connect()`'s cleanup raise the lost link's
  error, rather than a check in each cflib call. Why would a check in each
  call go wrong the way ADR-0086 said a check in every command would, why
  must the new code run after the link close and never before it, and why
  does a step that fails just before cflib reports the loss still end with
  its own error?
- **E18.** The connect cleanup test's fake cflib runs a hook before every
  cflib call, and the test's 71 cases are listed from a connect while
  pytest collects the test file. Why does that cover a cflib call added to
  `connect()` later with no new test, why must the listing catch its own
  error, and why do two of the cases end with the first snapshot raising
  rather than `connect()`?
- **E19.** The review of that cleanup changed
  `raise lost_link_error from step_error` to raising the lost link's error
  inside the `except` block, with no
  `from`. What does Python print between the two errors in each case, why
  does the first mislead an operator reading a failed rescue landing, and
  what in the tests fails if someone puts the `from` back?
- **E20.** D13 gives `__init__` and `connect()` one builder,
  `_build_parts()`. Why does building take-off and landing before the
  commands now fail every test at once, where with two copies the same
  mistake in `connect()`'s copy failed only one test, and why does
  `connect()` set the unknown-state flag itself rather than the builder?
- **E21.** The adapter split's last fitness functions check that only four named modules
  import cflib, and that take-off and landing reaches no cflib, even through
  another module. Why does the second rule follow imports when the first
  already fails on a cflib import in take-off and landing, which planted bug
  showed the difference, and why does the first rule also fail when a module
  stops importing cflib?
- **E22.** The project review planted a comment scanner that reads only a
  file's first line, and all 56 tests in the file still passed. Why did the
  one-line cases and the real-file guard both miss it, and what does that
  say about choosing a test's cases?
- **E23.** The review pinned `pyproject.toml`'s whole `[tool.pyright]`
  table, not just `typeCheckingMode`. Why does take-off and landing need
  that when it has no type-check comment, why pin the whole table rather
  than a list of risky settings, and what does the pin cost?
- **E24.** The project tour's numbers are read at the pinned commit, and
  `tests/docs/test_tour_numbers.py` fails while a page differs from what
  `tools/tour_numbers.py` writes. Why would reading today's code instead
  leave a link showing a different number than the page, why can no change
  to a constant in today's code fail the page test, and what does the test
  of each unit against its docstring catch that the page test can't?
- **E25.** Section 9 of the tour plants "trust a stale status" in may be
  flying, and only one test fails. Why does rule 2 count a stale
  on-the-floor status as flying, what would `land()` do without it, and is
  one test enough?
- **E26.** The tour's pop-ups now come from the glossary at the pinned
  commit, so the commit plan is two commits: the glossary alone, then the
  tour with its pin moved to that first commit. Why can't one commit hold
  both, with the pin naming itself, and why does the first commit still
  pass its tests when the second would fail without it?
- **E27.** The tour's dot check reads each lede, card and drop-down on its
  own, and checks only the terms the page dots somewhere. Why read each on
  its own rather than the page top to bottom, why does a table need a break
  between its cells (what did "Final descent height" beside "0.15 m" turn
  into), and what would checking every glossary term have cost?
- **E28.** The tour's link test reads the pinned commit with git. Why does
  continuous integration need the full git history for that, and after the
  pin moves, what kind of wrong link can the test still miss?

- **E29.** The work-dependency test reads the next-up brief but skips its
  "Done last" section. Why is a deleted row's number wrong in one part and
  fine in the other, and how could this test pass while checking nothing,
  and what stops that?

## Last reviewed

`fdcd31c`, pull request #30, closed 2026-11-23. Pull request #31 reads
everything after it.

Review queue: 4 decisions (ADR-0096 and its dot check), 6 findings
waiting (`docs/review-queue.md`: the comment at `log_blocks.py:287`, M-288,
and Joe's five questions on pull request #31 from the tour feedback, 2026-11-27).
