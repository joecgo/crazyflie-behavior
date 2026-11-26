# Next up

The project's state on one page, read first by a fresh work session.
`/wrap-up` rewrites it at the end of each work session.

**Keep it current.** When an item here finishes (a decision made, a pull
request merged, a step built), update this page in the same step: remove or
move the item, renumber "Next three", and update "Last commit" and
"Uncommitted".

- **Date:** 2026-11-26 (Pacific)
- **Last commit:** the records after the tour's pass one, on `4632d1f`
  (tour `b7192e4`). Not pushed yet. Uncommitted: nothing.

## Done last

- **Project tour, chapter 1 (the Crazyflie adapter), pass one:**
  `docs/tour/adapter.html`, `tour.css` and `tour.js`: sections 1, 2, 3 and
  5, with pass-two cards for 4 and 6-9. Every repository link is pinned to
  `5050718` and checked by `tests/docs/test_tour_links.py` (4 tests, proven
  by four plants); continuous integration now fetches the full history.
  Glossary row *Chapter*; two facts-register rows (cflib's 24-bit log
  timestamp, the 26-byte log block). Checked in headless Edge at 1280 and
  390 px (the built-in browser wasn't available). Private preview:
  https://claude.ai/artifact/XWPWS3fCf52696zXq6ZkJp. Joe kept all four
  build choices as built (new-tab links, remembered depth, ½× and 0.2×
  speeds, phone figures scroll sideways). Mistakes M-287 and M-288.
- **#157's D13 and last fitness functions (ADR-0093)**, committed and
  pushed; review pull request #31 opened.

## In progress

- Joe judges the tour preview's look and feel. Feedback edits go in
  `docs/tour/`; the preview is republished from a copy without the nine
  document-skeleton lines (the work order, `drafts/project-tour-adapter-handoff.md`).
- Joe's review of #31. When he's done: fix what he asks on `main`, close
  #31 unmerged like #24 to #30, and give `REVIEW.md`'s log its row.

## Next three

1. Once Joe accepts pass one: the ADR for the tour's form (the work
   order's decided items 1-4 and 10), its index row and Built column.
   Sonnet, medium.
2. Joe's review of #31, then its fixes. Opus, high.
3. Build #153, the test for citations of removed backlog rows (ADR-0091),
   then remove row #157. It first needs Joe's OK on a glossary term: *Live
   doc* proposed, *Live place* the alternative. Sonnet, medium.

After those: tour pass two; #165, then #158 (needs a test-layout decision,
`/decide`). Opus, high.

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
- **E18.** #162's fake cflib runs a hook before every cflib call, and the
  test's 71 cases are listed from a connect while pytest collects the
  test file. Why does that cover a cflib call added to `connect()` later
  with no new test, why must the listing catch its own error, and why do
  two of the cases end with the first snapshot raising rather than
  `connect()`?
- **E19.** #162's review changed `raise lost_link_error from step_error`
  to raising the lost link's error inside the `except` block, with no
  `from`. What does Python print between the two errors in each case, why
  does the first mislead an operator reading a failed rescue landing, and
  what in the tests fails if someone puts the `from` back?
- **E20.** D13 gives `__init__` and `connect()` one builder,
  `_build_parts()`. Why does building take-off and landing before the
  commands now fail every test at once, where with two copies the same
  mistake in `connect()`'s copy failed only one test, and why does
  `connect()` set the unknown-state flag itself rather than the builder?
- **E21.** #157's last fitness functions check that only four named modules
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

## Last reviewed

`fdcd31c`, #30, closed 2026-11-23. #31 reads everything after it.

Review queue: 0 decisions, 1 finding waiting (`docs/review-queue.md`:
the comment at `log_blocks.py:287`, M-288).
