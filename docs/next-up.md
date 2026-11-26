# Next up

The project's state on one page, read first by a fresh work session.
`/wrap-up` rewrites it at the end of each work session.

**Keep it current.** When an item here finishes (a decision made, a pull
request merged, a step built), update this page in the same step: remove or
move the item, renumber "Next three", and update "Last commit" and
"Uncommitted".

- **Date:** 2026-11-25 (Pacific)
- **Last commit:** "Records after #157's D13: mistakes M-274 to M-277,
  backlog #164, next-up brief", this page's own commit, after
  `bedea58`, pushed. Uncommitted: nothing. The checks pass (1080
  passed, 1 skipped).

## Done last

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
- **ADR-0094 (`419791c`):** connecting raises the interrupt signal that a
  CPython 3.12 threading lock error hides. Mistake M-246.

## In progress

- #157 (ADR-0093): stages 1 to 6, the blocking-call fitness function and
  D13's builder committed, with their reviews' fixes. Left: the last two
  fitness functions. No work order: backlog #157 and ADR-0093 hold the
  plan.

## Next three

1. Build #153, the test for citations of removed backlog rows (ADR-0091),
   before backlog row #157 is removed (#158 to #160 cite it). It first
   needs Joe's OK on a glossary term: *Live doc* was proposed, *Live place*
   the alternative. Sonnet, medium.
2. #157's last two fitness functions: the cflib importers by name, and
   take-off and landing free of cflib and `# pyright: basic`. Opus, Max.
3. #158, one shared cflib fake for the adapter tests, right after #157: it
   first needs a test-layout decision (`/decide`). Opus, high.

## Explain-backs waiting

Answer by number, such as "E1: ...", in any work session. Claude grades
from `drafts/explain-back-notes.md`; don't open it first.

- **E8.** ADR-0093 adds transcript tests (every cflib call, in order, for
  a scripted flight) before moving any adapter code. What can a move-only
  change break that tests checking the adapter's results might miss, what
  would that do to a flying drone, and why keep only two or three
  transcripts afterwards?
- **E9.** The transcript tests record every cflib call on one root mock.
  Why one root mock rather than checking each cflib object's calls on its
  own, and why must the code that writes a transcript line never call
  `str()` on a mock?
- **E10.** Stage 3 gives `CrazyflieCommands` two functions that return the
  drone and the telemetry buffer, called on every send, instead of the
  objects themselves. What would go wrong if a part kept the buffer it was
  built with, and why does putting the hand-over inside `go_to` make a
  forgotten hand-over impossible rather than just unlikely?
- **E11.** The blocking-call fitness function lists every function in
  `drone/crazyflie/` that sleeps or waits, and checks who calls each. Why
  must a tick never reach one, why build it before stage 4 rather than with
  the other fitness functions, and why does a check by function name miss
  `on_abandon=self.close_radio_link_only`?
- **E12.** The blocking-call fitness function matches calls by name alone.
  When bug planting added a join to `_HelperStep.start` (in `time_limit.py`,
  reached only from `connect()`), `take_off` also failed the rule that only
  `connect()` and `disconnect()` of the drone interface's methods may block.
  Why, is that a missed bug or a false alarm, and would you fix the test or
  the code?
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

## Last reviewed

`0846826`, 2026-11-04: the last full row of `REVIEW.md`'s review log. The
next code review covers everything after it. Pull requests #24 to #30 read
single changes ahead of the full review; the last, #30, read up to
`fdcd31c` and closed 2026-11-23. The full line-by-line walk comes after the
refactor (W9). Drafted for its pull request: the blocking-call fitness
function's review comments (`drafts/2026-11-24-blocking-call-review-comments.md`)
and stage 4's (`drafts/2026-11-24-stage-4-review-comments.md`), which
`/review-packet` posts along with the review queue.

Review queue: 12 decisions, 45 findings waiting (`docs/review-queue.md`).
