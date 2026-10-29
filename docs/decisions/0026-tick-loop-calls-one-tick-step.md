# 0026: The tick loop keeps time and calls one tick step; hangs are detected; every tick is logged

- **Status:** Accepted
- **Date:** 2026-10-29
- **Origin:** Mixed. Splitting the tick loop from the tick step, and stopping through the `with drone:` block: AI recommendations accepted after my questions. Detecting hangs (as UE does), logging every tick immediately, and a warning for every overrun: mine. The `faulthandler` watchdog and its 1 s limit: the AI's.

## Context

ADR-0024 says how the tick loop keeps time, and ADR-0025 what a tick does.
This decides where one ends and the other begins, how the loop stops, what
happens on an error or a hang, and where the measurements go.

## Options considered

- **What the loop calls:** the whole pipeline itself (it then depends on the
  drone, behaviors and safety layer, and timing tests need all three); or one
  tick step, so the loop is only a timer.
- **Errors:** caught by the loop, which tells the safety layer to land (landing
  logic in two places, and the safety layer may be what failed); or not
  caught, so they reach the `with drone:` block, whose `disconnect()` lands.
- **Measurements:** kept in memory with a summary at the end; or logged every
  tick, as it happens.

## Decision

- **The tick loop is a timer.** It keeps the due times (ADR-0024), measures
  each tick, watches for hangs, and calls one **tick step** with the tick's
  time and `dt`. It doesn't know what a tick does.
- **The tick step holds the order**, like `UWorld::Tick` and its tick groups:
  snapshot, safety pre-check, behaviors, send (ADR-0025). Behaviors are
  optional; the snapshot and the safety layer always run while flying. A test
  pins the order.
- **Stopping:** the tick step reports when it's done, or any thread makes a
  **stop request** (Ctrl+C, an operator command). The loop finishes the
  current tick and returns. Leaving the `with drone:` block lands.
- **Errors aren't caught in the loop.** They rise to the `with drone:` block,
  which lands, and are logged with their stack trace before the program exits
  (ADR-0020).
- **Hangs are detected.** `faulthandler.dump_traceback_later` is armed at the
  start of each tick and cancelled at its end. A tick still running after
  **1 s** writes every thread's stack trace to the log file. It runs in C, so
  it works even when Python is stuck. Acting on a hang stays in backlog #26.
- **Every tick is logged immediately** with Python's `logging`: lateness and
  work time at debug level, every overrun as a warning (ADR-0024), and a
  summary at the end of the flight (worst case and 99th percentile, overrun
  count, garbage-collector pauses). Overruns in a row each get their own
  warning: an exception to ADR-0020's once-per-streak rule (my call). Output
  goes to the console and to a log file per run in `logs/` (git-ignored).
  Which recordings get committed is still backlog #11.

## Failure modes

- **Inputs:** an exception or Ctrl+C anywhere in a tick reaches the `with`
  block, which lands. A hung tick reaches nothing; the watchdog only reports it.
- **Backups:** landing on error goes over the same radio. If the link itself
  is what failed, only the firmware's setpoint timeout remains, and it cuts
  the motors. The kill switch runs on its own thread (ADR-0013).
- **Never:** an error that skips landing (except a hang or a dead link); a
  hang with no stack trace in the log.
- **Always eventually:** leaving the loop, for any reason but a hang, lands.

## Consequences

- Tests drive the loop with `SimClock` and a fake tick step: due times,
  overruns, stop requests, "done", errors passing through, and the logging.
  Tests drive the tick step with hand-built snapshots and no clock.
- The 1 s limit is well below the firmware's ~2 s motor cut, so the stack
  trace is written before a drop.
- If ticks overrun constantly, nearly every tick logs a warning, on the
  console too. A constant overrun means the loop isn't keeping its rate, so
  the noise is the signal.
- Glossary: *Tick step*, *Stop request* and *Hang watchdog* proposed; *Tick
  loop* reworded.
