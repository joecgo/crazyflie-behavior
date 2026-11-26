# Next up

The project's state on one page, read first by a fresh work session.
`/wrap-up` rewrites it at the end of each work session.

**Keep it current.** When an item here finishes (a decision made, a pull
request merged, a step built), update this page in the same step: remove or
move the item, renumber "Next three", and update "Last commit" and
"Uncommitted".

- **Date:** 2026-11-26 (Pacific)
- **Last commit:** `a03e207`, "Records after #157's D13: mistakes M-274
  to M-277, backlog #164, next-up brief", pushed. Uncommitted: #157's last
  two fitness functions, their project review's fixes and the records of
  both, this page included; the work log doesn't have them yet. The checks
  pass (1113 passed, 1 skipped).

## Done last

- **The project review of #157's last fitness functions (ADR-0093),
  uncommitted:** Joe chose the range: only the uncommitted work, since each
  earlier stage had its own. `/project-review max`, run inline (Joe's
  choice): no bug in the tests' logic, and 11 findings, all fixed as Joe
  chose. ADR-0093's Built said Yes while D15's cut to two or three
  transcripts isn't built: Built says "Partly", and backlog #165 cuts them
  before #158. A comment scanner reading only line 1 passed all 56 tests: a
  case with the comment on line 2 now fails it. `pyproject.toml`'s
  `[tool.pyright]` table is pinned (Joe's choice, a rule beyond ADR-0093's
  ask). Six docstrings reworded, a direct `import cflib` case, the importer
  list compared sorted, glossary rows for *Import scanner*, *Import
  follower* and *Comment scanner* (text approved), and "reaches" in the
  test's name. Six plants, all as expected. Mistakes M-280 to M-284.
- **#157's last two fitness functions (ADR-0093), uncommitted:** in
  `tests/architecture/test_import_rules.py`. Inside the Crazyflie adapter,
  only `adapter.py`, `commands.py`, `link.py` and `log_blocks.py` import
  cflib, as an exact list; take-off and landing reaches no cflib, even
  through another module (package `__init__.py` files, imports inside
  functions and under `TYPE_CHECKING` included), and has no `# pyright:` or
  `# type: ignore` comment. 16 planted bugs, all caught; P2, take-off and
  landing importing `commands.py`, only by the reach rule. Joe kept all
  three choices as built and approved the `ARCHITECTURE.md` and glossary
  edits (2026-11-26); `docs/coding-style.md`'s cflib boundary follows them.
  Built at low effort (the session ran on Opus low, not Max), so the
  project review reads these tests closely. Joe's PyCharm check answered
  the review queue's open item: the attribute docstrings show on hover at
  `_link`'s assignment in `_build_parts()`. Mistakes M-278 and M-279.
- **#157's D13 (ADR-0093), committed and pushed (`bedea58`):** Joe chose
  option A: one builder, `_build_parts()`, called by `__init__` and
  `connect()`, builds the four parts in order (the commands before take-off
  and landing) and clears the two once-per-streak flags. `connect()` still
  sets the unknown-state flag itself, since `__init__` wants it False.
  `/project-review max`, run inline: no correctness bug, 8 findings. No
  test guarded the flags' clearing (both plants passed every test), so two
  tests that connect again now do; the builder's docstring and `connect()`'s
  comment reworded; backlog #164 for `connect()` while a link is still
  open; E20 corrected. Mistakes M-274 to M-277.
- **#162's review (ADR-0095):** `/project-review max`, run inline: no
  correctness bug in the new cleanup, 12 findings. The lost link's error
  is now raised while handling the step's error, not with it as its cause,
  which Python printed as the step's error causing the loss. Four test
  gaps and four wording fixes, proven by 7 planted bugs. A race in cflib's
  full link close went to backlog #163 (not placed yet). Committed and
  pushed: `3f266eb` (Implements ADR-0095) and `50888c6`. Mistakes M-267
  to M-273.
- **ADR-0095 (#161), built as #162:** a link lost while connecting ends
  `connect()` with the lost link's error, raised by its cleanup after the
  link close. The connect tests' fake cflib loses its link the way cflib
  does, and one test loses it before each of the 71 cflib calls of a
  connect once the link is open. Mistakes M-264 to M-266.
- **#157's stages 4 to 6 (ADR-0093):** `take_off_and_landing.py`,
  `log_blocks.py` and `link.py`, each checked move-only by script, each
  with a `/project-review max` and its fixes, committed and pushed.
  Mistakes M-247 to M-263.
## In progress

- The review's pull request (Next three, 1): its project review and fixes
  are done; the commits, the push, the review branch, the packet and the
  pull request are left. C6 (#157) is built; its backlog row stays until
  #153.

## Next three

1. The rest of the code review's pull request, as Joe asked. Ask him
   before committing (small chunks, with the work log's row), before
   pushing, and before opening the pull request. Then, as `REVIEW.md`'s
   "My reviews" says: the branch `review/<date>` at `main`'s last commit,
   `/review-packet`, and the pull request into `reviewed`. `reviewed` isn't
   on GitHub yet: this first review creates it at `0846826`, so the range is
   everything after it (over 320 commits, 77 source and test files); check
   the packet's size with Joe first. `REVIEW.md`'s "Next" row still says
   #30 is open (it closed 2026-11-23): fix it with the log's row. Sonnet,
   medium for the commits and the branch; Opus, high for a packet over the
   whole range.
2. Build #153, the test for citations of removed backlog rows (ADR-0091),
   then remove row #157 (built; #158 to #160 cite it). It first needs Joe's
   OK on a glossary term: *Live doc* was proposed, *Live place* the
   alternative. Sonnet, medium.
3. #165, then #158: cut the transcript tests to those that guard an order
   an ADR requires (ADR-0093's D15), then #158's one shared cflib fake,
   which first needs a test-layout decision (`/decide`). Opus, high.

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

`0846826`, 2026-11-04: the last full row of `REVIEW.md`'s review log. The
next code review covers everything after it. Pull requests #24 to #30 read
single changes ahead of the full review; the last, #30, read up to
`fdcd31c` and closed 2026-11-23. The full line-by-line walk comes after the
refactor (W9). Drafted for its pull request: the blocking-call fitness
function's review comments (`drafts/2026-11-24-blocking-call-review-comments.md`)
and stage 4's (`drafts/2026-11-24-stage-4-review-comments.md`), which
`/review-packet` posts along with the review queue.

Review queue: 14 decisions, 57 findings waiting (`docs/review-queue.md`).
