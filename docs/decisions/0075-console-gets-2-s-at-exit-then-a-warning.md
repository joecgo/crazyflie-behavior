# 0075: At exit, the console gets 2 s to finish, then a warning goes to the log file

- **Status:** Accepted. Amends [ADR-0035](0035-console-output-on-a-background-thread.md) for the exit. Amended by [ADR-0078](0078-console-exit-risks-accepted-python-pinned-to-3-12.md), 2026-11-17: the "Not covered" case was measured and is an accepted risk, with two more exit cases; the exit test runs with `PYTHONUNBUFFERED=1`.
- **Date:** 2026-11-17
- **Origin:** AI recommendation accepted: the 2 s limit (D1 in the 2026-11-13 code review) and the console handler that takes no lock (found while writing this ADR).

## Context

ADR-0035 moves console output to a background thread. When the program
ends while the console still isn't reading, that thread is stuck in a write
with lines still queued. `QueueListener.stop()` waits for it with no time
limit (`docs/verified-facts.md`). Python's own exit cleanup waits too:
`logging.shutdown`, run at exit, takes each handler's lock with no time
limit, and `Handler.handle` and `StreamHandler.flush` hold that lock during
the write (Python 3.12.10's source, read 2026-11-17).

## Options considered

- **A1. Give up after 2 s, and the console handler takes no lock:** the
  program ends; the console's last lines may be lost.
- **A2. Give up after 2 s only:** our code ends, but Python's exit cleanup
  can still wait forever on the stuck write.
- **B. Wait until the console has printed everything:** every line reaches
  the console, but the program may never end.

## Decision

A1. At exit, the console's thread gets 2 s to print what's queued. If it
hasn't finished, a warning goes to the log file and the program carries on
ending. The log file already has every line, so nothing is lost as evidence.
The console handler takes no lock, since only the console's thread writes
through it, and isn't flushed by Python's exit cleanup.

## Failure modes

- **Inputs:** a console that stops reading delays the exit by 2 s, then its
  queued lines are dropped with the warning. A slow console prints what it
  can in 2 s.
- **Backups:** the log file backs up the console, and it's written on the
  caller's thread, so a stuck console doesn't stop it.
- **Never:** our logging code keeps the program from ending.
- **Always eventually:** the log file has every line, and the warning when
  console lines were dropped.
- **Not covered:** Python's own last flush of the console at exit is C code,
  not checked; it may still wait. The drone is disconnected by then:
  `run_tick_loop` runs inside `logging_for_run`.

## Consequences

- Testable without a console: a fake console that blocks, and a test that a
  program with its console blocked ends within a time limit.
- The no-lock handler is safe only while one thread writes through it.
- Built with ADR-0035 (C1 in the code review).
