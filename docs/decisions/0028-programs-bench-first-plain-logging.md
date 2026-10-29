# 0028: Programs: a bench program first, plain logging, the mock adapter by default

- **Status:** Accepted
- **Date:** 2026-10-29
- **Origin:** Mixed. Plain logging rather than background threads: mine, on a fast laptop with an SSD, after I asked why the simpler option wasn't recommended (the AI then changed its recommendation). The bench program, the `programs/` package and the mock adapter by default: AI recommendations accepted.

## Context

The tick loop (ADR-0026) needs a program around it: logging to the console
and a log file, the Ctrl+C handler, the operator controls (ADR-0027), and
connecting and disconnecting the drone. Backlog #27 asked how to keep a log
write from stalling a tick.

## Options considered

- **Logging:** background threads (robust, but more moving parts, and the
  last lines are lost when the program is killed); plain logging, with
  QuickEdit turned off in an old console window, where selecting text pauses
  the program; plain logging and a rule not to fly from such a window.
- **First program:** a bench program that never commands the drone; a hover
  program, which needs the safety layer first.
- **Where programs live:** `src/crazyflie_behavior/programs/`, one module
  each; one entry point with subcommands; `tools/`, ruled out because it's
  exempt from the cflib rule (ADR-0002).
- **Choosing the drone:** the mock adapter by default, with `--crazyflie` for
  the real one; a separate program for each adapter.

## Decision

- **Programs live in `src/crazyflie_behavior/programs/`**, one module each,
  with the start-up code they share. Run one with
  `python -m crazyflie_behavior.programs.bench`, or its PyCharm run
  configuration.
- **The first is the bench program.** It connects, runs the tick loop and
  logs every snapshot, but never commands the drone: the telemetry half of
  field-test stage 0. It runs today with the mock adapter.
- **The mock adapter is the default.** `--crazyflie` uses the real drone, so
  the hardware is never used by accident.
- **Plain logging**, so every line reaches the file as it's written. The
  console shows info and above; the log file, one per run in `logs/`, gets
  everything. In an old Windows console window, the program turns QuickEdit
  off, and back on when it exits. Python warnings and errors in other threads
  go to the log too.

## Failure modes

- **Inputs:** a slow log write stalls the tick. It shows as lateness and
  overruns, and the hang watchdog reports one over 1 s.
- **Never:** the real drone used without `--crazyflie`; the bench program
  commanding the drone.
- **Always eventually:** a program that connected disconnects, which lands a
  flying drone (ADR-0026).

## Consequences

- If the bench shows slow log writes, switch to background threads.
  Measuring write times joins backlog #25. A shipping mode with less logging
  is backlog #28.
- Ctrl+C makes a stop request from the moment the drone is connected. While
  connecting, nothing is flying, so Ctrl+C still stops the program. On
  Windows it takes effect only when cflib's connect waits end: Python 3.12
  can't interrupt a wait with no time limit (backlog #29).
- Arming and the bench e-stop test wait for the minimal safety layer: only
  the safety layer may command the drone (ADR-0008).
- With the mock adapter, the bench program is where to check what PyCharm's
  Stop button does (ADR-0027).
- Backlog #27 is closed.
- Glossary: *Program*, *Bench program*.
