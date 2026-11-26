# Next up

The project's state on one page, read first by a fresh work session.
`/wrap-up` rewrites it at the end of each work session.

**Keep it current.** When an item here finishes (a decision made, a pull
request merged, a step built), update this page in the same step: remove or
move the item, renumber "Next three", and update "Last commit" and
"Uncommitted".

- **Date:** 2026-11-25 (Pacific)
- **Last commit:** "Records after #157 stage 6: mistakes M-258 to M-263,
  next-up brief", on `main`, after `f38578b`. Uncommitted: nothing. The
  checks pass (1001 passed, 1 skipped). Not pushed.

## Done last

- 2026-11-25: committed #157's stage 6 (ADR-0093): four tests for the
  link's wiring (`1d51b96`), passing on the code before the move, then
  the move to `link.py` (`f38578b`, move-only but for the two
  differences its message names), and the records.
- 2026-11-25: `/project-review max` of #157's stage 6, run inline without
  the fresh-context read (Joe's choice): no correctness bugs, and the move
  is move-only by script (70 items). 10 findings, in
  `docs/review-queue.md`. Joe's calls: `close(*, radio_link_only)` and
  `has_link_to_close` (the first names gave the glossary's *May be
  flying* a second meaning and said less than the code), the three test
  gaps from before the move tested now, and ARCHITECTURE.md section 7's
  row. Two of those gaps are radio-only closes that the cleanup right
  after repeats, so their tests check that each comes first. Mistakes
  M-258 to M-263.
- 2026-11-25: built #157's stage 6 (ADR-0093): the link moves to
  `link.py` (`CrazyflieLink`, with the interface Joe approved), checked
  move-only by script. Of 30 planted wiring bugs, 28 are caught; the
  survivors are `__init__`'s take-over flag, never read, and a reworded
  comment that only the move check sees.
- 2026-11-25: committed #157's stage 5 (ADR-0093): the move to
  `log_blocks.py` (`6651fb6`), the clearing's drop (`c19831b`), the review
  fixes (`06a432f`) and the records.
- 2026-11-25: `/project-review max` of #157's stage 5, run inline without the
  fresh-context read (Joe's choices): no correctness bugs; the move is
  move-only, and the clearing's drop is safe (`disconnect()` returns at once
  after a close, and cflib's `stop()` does nothing once the link is closed).
  8 findings, in `docs/review-queue.md`, fixed in `06a432f`:
  `start_up.py` imports the take-off block's constants from `log_blocks.py`;
  wording in `adapter.py`, `log_blocks.py` and `take_off_and_landing.py`; a
  glossary row for *Part* (Joe approved the text); backlog #157's clause.
  Joe's calls: the move commit's message notes its change to the take-over
  fitness function's body (ADR-0093's D14), and a pre-existing lost-link
  error while connecting is backlog #161. Mistakes M-252 to M-255.
- 2026-11-25: built #157's stage 5 (ADR-0093):
  the log blocks move to `log_blocks.py` (`LogBlocks`, with the interface
  Joe approved), checked move-only by script (43 moved items match). Then
  the clearing at the link close goes (Joe's choice: a fresh part on every
  connect made it redundant). The take-over fitness function now lists
  `adapter.py` as a pass-through (Joe's choice; M-251). 15 wiring bugs
  planted, 14 caught; the survivor, `__init__`'s take-over flag, is never
  read. Joe put C6 before #153.

- 2026-11-25: `/project-review` (max, run inline, without the
  fresh-context read) of #157's stage 4 and ADR-0094's fix: no
  correctness bugs, and the move is move-only (every moved body, constant
  and the landing phase enum match the originals after the renames). 7
  findings, all nits, all fixed (`419791c`, `91e1eeb`); they're in
  `docs/review-queue.md`. Mistakes M-247 to M-250.
- 2026-11-25: committed #157's stage 4 (ADR-0093): the two new tests
  (`9e0338d`), the move to `take_off_and_landing.py` (`6710a79`,
  move-only), its strict typing (`2aa215d`) and the review's docstring
  fixes (`91e1eeb`). Each commit passed the checks on its own.
- 2026-11-25: decided and built ADR-0094 (`419791c`): connecting raises
  the interrupt signal that a CPython 3.12 threading lock error hides. The
  three tests that send the interrupt signal no longer fail at random (300
  runs, no failure; the fix caught the race twice). Mistake M-246.
- 2026-11-24: `/project-review` (high) of the blocking-call fitness
  function: 5 findings, all fixed in `531c638` (an import alias hid a
  blocking call; the interface was read by one decorator spelling; two
  scanner forms had no test; the glossary's Blocking call row and a test
  name said more than the check). Mistakes M-240 to M-244.
- 2026-11-24: built and committed #157's blocking-call fitness function
  (ADR-0093, `1cc5081`): 14 blocking functions listed, 4 stored callables
  allow-listed, 39 tests, 23 planted bugs all caught.
- 2026-11-24: `/project-review` (xhigh, with the fresh-context read) of
  #157's stages 1 to 3: no safety or correctness bugs, 10 findings, all
  fixed except the blocking-call guard, which is decided. Joe's decisions,
  in ADR-0093: only the adapter's modules that import cflib pass cflib
  objects to each other (narrows ADR-0002, ADR-0004 and CLAUDE.md's rule),
  and a blocking-call fitness function comes before stage 4. Glossary:
  Hand-over widened, Level setpoint added, Transcript test reworded.
  Mistakes M-233 to M-239. The fresh read's other items are in
  `drafts/2026-11-24-fresh-read-c6-stage-3.md`, for the full review (W9).

## In progress

- #157 (ADR-0093): stages 1 to 6 and the blocking-call fitness function
  committed, with their reviews' fixes. Left: rebuilding the parts in
  `connect()` (D13), and the last two fitness functions.

## Next three

1. `/decide` #161: a link lost while connecting ends `connect()` with
   cflib's AttributeError, not the lost link's error. Its row puts it at
   the link stage, now built. Opus, high.
2. #157's next stage: rebuilding the parts in `connect()` (ADR-0093's
   D13). Opus, Max.
3. Build #153, the test for citations of removed backlog rows (ADR-0091),
   before backlog row #157 is removed (#158 to #160 cite it). It first needs
   Joe's OK on a glossary term: *Live doc* was proposed, *Live place* the
   alternative. Sonnet, medium.

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
- **E11.** The fitness function decided today lists every function in
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

## Last reviewed

`0846826`, 2026-11-04: the last full row of `REVIEW.md`'s review log. Pull
requests #24 to #30 read single changes ahead of the full review; the last,
#30, read up to `fdcd31c` and closed 2026-11-23. The full line-by-line walk
comes after the refactor (W9). Drafted for its pull request: the
blocking-call fitness function's review comments, one per decision or
finding from its build and its review
(`drafts/2026-11-24-blocking-call-review-comments.md`), and stage 4's, in
the same shape (`drafts/2026-11-24-stage-4-review-comments.md`). Stage 4's
to 6's project reviews (2026-11-25) put their findings in `docs/review-queue.md`,
which `/review-packet` posts along with both drafts.
