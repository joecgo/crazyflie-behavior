# 0066: The hover program reports a cut-short hover by its exit code only

- **Status:** Accepted. Amends [ADR-0062](0062-hover-program-fails-when-the-hover-is-cut-short.md): no error line about the failure after the run. Closes backlog #86.
- **Date:** 2026-11-12
- **Origin:** AI recommendation overridden: the exit code alone was mine; the AI recommended a final error line through a `run_program` hook.

## Context

ADR-0062 says the hover program logs why at error level when it exits 1.
`run_program` closes the run's log file before it returns, so a line logged
after it would reach the console only. Every cause of a cut-short hover is
already in the log: the safety pre-check's failure (a warning with its
reasons), a stop request (info), and the hover test's own failures (errors).

## Options considered

- **A. A `run_program` hook:** an optional function called inside the run's
  log after a run without an error. A reason it returns is logged as an error,
  and the exit code is 1.
- **B. Log after `run_program` returns:** on the console only.
- **C. The hover program opens the log itself:** repeats `run_program`'s
  error handling.
- **D. No line:** `hover.py` returns 1 after the run, as the rescue landing and
  failsafe programs already do.

## Decision

Option D. The causes are already in the log, so a final line would only
repeat them, and the exit code is the verdict, as in the other two programs.

## Consequences

- **Risks I accept knowingly:** no single line in the log file says the hover
  test failed, and the exit code isn't written to it, so the test log records
  the exit code (PyCharm's Run window shows it). The log still shows the
  outcome: a full hover logs "hovered N s. Landing." and "landed"; a cut-short
  one logs the pre-check's failure or the stop request instead.
- `run_program` is unchanged.
- Tests: as ADR-0062.
