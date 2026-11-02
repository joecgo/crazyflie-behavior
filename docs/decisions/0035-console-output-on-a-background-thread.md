# 0035: Console output runs on a background thread; log-file writes stay on the tick's thread

- **Status:** Accepted. Amends [ADR-0028](0028-programs-bench-first-plain-logging.md) (plain logging) for the console.
- **Date:** 2026-11-01
- **Origin:** Mixed. Keeping backlog #33 open and measuring before deciding: mine (Claude had proposed removing it unmeasured). A background thread for the console only: AI recommendation accepted after the measurements.

## Context

ADR-0028 chose plain logging: every write happens on the tick loop's thread.
Backlog #33 asked whether that blocks the tick. Measured: a log call takes
about 0.05 ms (worst about 0.3 ms); with no console the worst tick was
5.7 ms; but console output into a pipe stalled ticks for up to 0.44 s,
almost nine tick periods. A console that stops reading (QuickEdit, a paused
pipe) can freeze the tick loop mid-flight.

## Options considered

- **A. Keep plain logging** (ADR-0028): simplest, but the measured stall is
  real.
- **B. Everything on a background thread** (`QueueHandler` and
  `QueueListener`): no write blocks the tick, but the log file then loses
  its last lines when the program is killed, which is when they matter most.
- **C. Only the console on a background thread:** the console is what
  stalled; the log-file writes were fast.

## Decision

Option C. The console handler sits behind a `QueueHandler`, written by a
`QueueListener` thread. The log file stays synchronous, so every line
reaches it as it's written, as ADR-0028 chose.

## Failure modes

- **A stopped console:** the queue grows while the console isn't read. The
  tick isn't blocked; memory use rises slowly.
- **A kill:** console lines still in the queue are late or lost. The log
  file has them, so nothing is lost as evidence.
- **Never:** a console write blocks the tick loop.
- **Always eventually:** every log message reaches the log file.

## Consequences

- Testable without a real console: a fake console that blocks, and a test
  that the tick still runs on time and the file still gets every line.
- Backlog #33 is closed; #25 keeps the measured command-tick numbers.
