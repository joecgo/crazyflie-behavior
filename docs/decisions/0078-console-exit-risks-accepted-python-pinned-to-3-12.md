# 0078: Three console exit cases are accepted risks; Python is pinned to 3.12

- **Status:** Accepted. Amends [ADR-0075](0075-console-gets-2-s-at-exit-then-a-warning.md): its "Not covered" case, measured, and its exit test.
- **Date:** 2026-11-17
- **Origin:** Mixed. Accepting the interrupt signal during the exit wait: mine, over the AI's recommendation to treat it as "stop waiting". Accepting a stuck exit with a buffered standard error, accepting log messages queued after the stop, and pinning Python: AI recommendations accepted.

## Context

C1's project review (2026-11-17) found exit cases that ADR-0075 doesn't
cover. The worst was measured (`docs/verified-facts.md`): with standard
error buffered (a terminal run; PyCharm's run configs set
`PYTHONUNBUFFERED`), a program whose console stopped reading logged the
warning, then was still running when checked 12 or 15 s later, in three
runs. The console's
thread is stuck in a write that holds standard error's buffer lock, and
Python's own flush of standard error waits on it. Once the pipe was read, it
ended with exit code 0 twice and 0xC0000409 (a crash) once. With
`PYTHONUNBUFFERED=1` it ended in 2.7-2.8 s with exit code 0. The review also
found that the no-lock console handler relies on Python 3.12 skipping a
`None` lock, not checked on later versions.

## Options considered

- **The stuck exit:** A1, accept and record it; A2, `os._exit` with the
  program's exit code when the console was given up on (skips all other exit
  cleanup, and `logging_for_run` must tell `run_program`); A3, the console's
  thread writes with `os.write` to its own copy of standard error's file
  descriptor (untested; raw bytes may garble non-ASCII text).
- **Newer Python:** B1, pin `>=3.12,<3.13`; B2, a lock object that does nothing.
- **The interrupt signal during the exit wait:** C1, accept it; C2, treat it
  as "stop waiting".
- **Log messages queued after the stop:** D1, accept them; D2, warn about them too.

## Decision

A1, B1, C1 and D1. Each case is rare, comes after the drone is disconnected,
and leaves the log file complete, so none is worth more code now.

- **A stuck exit** stays possible with a buffered standard error. ADR-0075's
  program-exit test runs with `PYTHONUNBUFFERED=1`, so it tests our code's part.
- **Python is pinned** to 3.12 in `pyproject.toml`. The facts register's
  Python rows were read in 3.12.10; an upgrade checks them again first.
- **The interrupt signal during the exit wait** leaves `run_program`: the
  warning isn't logged, and the program's own exit code is lost.
- **Log messages queued after the stop** by another thread are never shown
  on the console, and nothing warns.

## Failure modes

- **Inputs:** a buffered standard error that stops reading at exit: the
  program ends only once the console reads again, with exit code 0 or a
  crash code, by timing. Ctrl+C during the exit wait: Python's interrupt
  exit code, and a traceback to the console, which may wait behind it.
- **Backups:** the log file is written on the thread that logs and takes no
  lock of the console's, so it has every log message in each case.
- **Never:** the drone is connected during any of these waits:
  `run_tick_loop` disconnects before `logging_for_run` exits.
- **Always eventually:** the log file has every log message.
- **Risk accepted:** in these cases a program whose job is one outcome (the
  hover test, the failsafe test, the rescue landing) may not report it by its
  exit code (REVIEW.md Q-52). Its log file still has the causes.

## Consequences

- A test runs a program's exit with standard error going to a pipe nobody
  reads, with `PYTHONUNBUFFERED=1`: it ends within `EXIT_TIME_LIMIT` plus a
  margin, with exit code 0.
- Backlog #117: revisit if a session shows a program that doesn't end after
  the console warning, or a wrong exit code.
- Glossary: *Console* reworded, *Log file* added.
