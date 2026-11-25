# Next up

The project's state on one page, read first by a fresh work session.
`/wrap-up` rewrites it at the end of each work session.

**Keep it current.** When an item here finishes (a decision made, a pull
request merged, a step built), update this page in the same step: remove or
move the item, renumber "Next three", and update "Last commit" and
"Uncommitted".

- **Date:** 2026-11-24 (Pacific)
- **Last commit:** "Next-up brief after the review of #157's stages 1 to
  3", on `main`, after `3f1221e`. Not pushed: the six commits after
  `eca324c` (the first five each pass their tests on their own).
  Uncommitted: nothing. The continuous integration checks pass (948 passed,
  1 skipped).

## Done last

- 2026-11-24: `/project-review` (xhigh, with the fresh-context read) of
  #157's stages 1 to 3: no safety or correctness bugs, 10 findings, all
  fixed except the blocking-call guard, which is decided. Joe's decisions,
  in ADR-0093: only the adapter's modules that import cflib pass cflib
  objects to each other (narrows ADR-0002, ADR-0004 and CLAUDE.md's rule),
  and a blocking-call fitness function comes before stage 4. Glossary:
  Hand-over widened, Level setpoint added, Transcript test reworded.
  Mistakes M-233 to M-239. The fresh read's other items are in
  `drafts/2026-11-24-fresh-read-c6-stage-3.md`, for the full review (W9).
- 2026-11-24: committed ADR-0093 and #157's stages 1 to 3: the transcript
  tests (five scripted flights), the logger prep, and `commands.py`
  (`CrazyflieCommands`: the commands sent to the drone, with the hand-over
  inside `go_to` and `go_to_relative`).
- 2026-11-24: decided #142 as ADR-0090 (the bug-planting tool, not built:
  #152), #144 as ADR-0091 (not built: #153) and #55 as ADR-0092 (partly
  built: #155, #156 open).

## In progress

- #157 (ADR-0093): stages 1 to 3 committed. Next, the blocking-call fitness
  function, then stage 4, take-off and landing.

## Next three

1. #157's blocking-call fitness function (ADR-0093's Failure modes and the
   backlog row): every function in `drone/crazyflie/` that sleeps, waits or
   joins is listed, and called only from `connect()`, `disconnect()` or
   another listed one, with an allow-list for calls through a stored
   callable and a test for each form the scanner handles, proven by bug
   planting. Opus, high.
2. #157's stage 4: take-off and landing to `take_off_and_landing.py`
   (ADR-0093), move-only, then its strict-typing fixes in their own commit.
   Read `drafts/2026-11-13-code-recommendations.md`, C6. Opus, Max.
3. Build #153, the test for citations of removed backlog rows (ADR-0091),
   before the next backlog row is removed. Sonnet, medium.

## Explain-backs waiting

Answer by number, such as "E1: ...", in any work session. Claude grades
from `drafts/explain-back-notes.md`; don't open it first.

- **E1.** ADR-0086 checks for a lost link only in `take_snapshot()`. Why
  does that still stop every tick after a lost link before it does anything,
  and which command still raises on its own after one, and why?
- **E2.** A recording writes a NaN battery voltage as the string `"nan"`,
  not as `null`. What would go wrong in a replay test if it wrote `null`?
- **E3.** The tick's timing reaches the recorder through a callable the
  tick loop calls (ADR-0088). Why can't the tick step measure a tick's
  lateness and work time itself?
- **E4.** A behavior raises halfway through a tick, after one command
  request. What does that tick's line in the recording hold, and what makes
  sure the line, and the recording's last line, still get written?
- **E5.** Change the name a recording uses for a flight end reason, in the
  one table both the encoder and the decoder read. Why do the round-trip
  tests still pass, which golden file tests fail (ADR-0089), and what
  does the golden file deliberately not catch?
- **E6.** The bug-planting tool (ADR-0090) runs on demand, but the test for
  citations of removed backlog rows (ADR-0091) runs in continuous
  integration on every push. Why the difference, and what does the tool
  need so that its report doesn't become noise people learn to ignore?
- **E7.** ADR-0092 keeps the text log's snapshot line until the first
  recorded session's recordings match it. What could be lost in that
  session if the line were already gone, and why is the text log still no
  help if the laptop's disk fails?
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
  `on_abandon=self._close_radio_link_only`?

## Last reviewed

`0846826`, 2026-11-04: the last full row of `REVIEW.md`'s review log. Pull
requests #24 to #30 read single changes ahead of the full review; the last,
#30, read up to `fdcd31c` and closed 2026-11-23. The full line-by-line walk
comes after the refactor (W9).
