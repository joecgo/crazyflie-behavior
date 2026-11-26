# 0095: A link lost while connecting ends `connect()` with the lost link's error

- **Status:** Accepted. Amends [ADR-0029](0029-connecting-has-time-limits.md): a step past its time limit after a lost link raises the lost link's error while handling the `TimeoutError`. Answers backlog #161.
- **Date:** 2026-11-25
- **Origin:** AI recommendation accepted: the fix (option A), the test that loses the link before each step, keeping the time limits, and no closing line. Found by the project review of #157 stage 5 (mistakes M-252, M-264); putting it at the link stage was mine. Raising it while handling the step's error, not with that error as its cause: an AI recommendation accepted after the project review of #162, before the first commit.

## Context

After a lost link, cflib's calls behave differently, and `connect()` reads
the changes as other failures (cflib 0.1.34, facts register). A log block
isn't added, so its `start()` raises `AttributeError`. The parameter values
are emptied but still count as fetched, so the Flow deck check finds no deck.
Opening the link and reading the parameters wait out their time limits. Only
the status and first-telemetry waits raise the lost link's
`ConnectionError`. Every case already fails safe: `connect()` closes the
link as ADR-0038 requires, and the lost link's error line is logged. But the
run's last line points at the wrong thing, and the run most exposed is the
rescue landing, which connects over a link that just failed, to a drone that
may be hovering.

## Options considered

- **A. `connect()`'s cleanup raises it:** one place, after the link close.
- **B. Each cflib call checks for itself** (`_add_log_block`,
  `is_deck_attached`): fixed at the source, but each new step needs its own
  check, ADR-0086's concern about commands.
- **C. A lost-link check between steps:** a loss during a step still ends
  with that step's error.
- **D. Leave it:** safe, with a misleading last line.

## Decision

A. When a step of `connect()` raises an `Exception` and cflib has reported a
lost link, `connect()` closes the link as now, then raises the lost link's
`ConnectionError` while handling the step's error, so the traceback shows
that error first. Not as its cause: Python would print the step's error as
the direct cause of the loss, the reverse of what happened. The lost link's
error that a wait raised passes through as it is, and so does anything else,
the interrupt signal included (ADR-0094). It's one place that no step can
skip, now or later: ADR-0086's reasoning, applied to `connect()`.

- **The test:** the fake cflib loses its link the way cflib does, each
  behavior from the facts register: the link set to `None`, parameter reads
  and writes raising `KeyError`, log blocks not added (their `start()`
  raising `AttributeError`), then the `disconnected` and `connection_lost`
  callbacks. One parametrized test loses it before each cflib call
  `connect()` makes once the link is open, and checks the error and the link
  close. A new step is covered with no new test: M-252's mechanism.
- **The time limits stay** for opening the link and reading the parameters
  (ADR-0029): up to 15 s or 10 s, then the lost link's error.
- **No closing line:** ADR-0084's line on whether the drone may still be
  flying stays in `disconnect()`.

## Failure modes

- **Inputs:** cflib reports a loss last, after it drops the link and runs its
  own cleanup callbacks, so a step that fails in that short gap (not
  measured) still ends with its own error. A real error that coincides with
  a loss is reported as the loss, raised while handling the real one: "The
  drone is still flying" then shows in the traceback, not on the last line.
- **Backups:** the link close doesn't read the lost link: only the radio link
  closes while the drone is airborne or its state is unknown (ADR-0038).
- **Never:** the new code runs before the link close or skips it; an
  interrupt signal comes out as a `ConnectionError`.
- **Always eventually:** `connect()` raises within its time limits, with the
  link closed.

## Consequences

- The Buzzer deck check can still log "No Buzzer deck" wrongly, before a
  later step or the first snapshot raises.
- Built by backlog #162: Crazyflie adapter code, so Max and
  `/project-review max`.
- Facts register: a row for parameter reads and writes after a lost link.
- Glossary: *Lost link* gains connecting when built (text approved, in
  backlog #162).
