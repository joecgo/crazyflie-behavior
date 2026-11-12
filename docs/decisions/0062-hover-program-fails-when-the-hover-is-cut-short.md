# 0062: The hover program exits with an error when the hover is cut short

- **Status:** Accepted. Closes backlog #71.
- **Date:** 2026-11-12
- **Origin:** AI recommendation accepted.

## Context

First flight 2's Hover test was landed by the stale-data failsafe at 44 s
of 60. The hover program logged no error from the hover test and exited 0,
as if the test had passed. The failsafe programs rightly pass on a failsafe
landing, since that is what they test. The hover program tests the hover,
so a hover the safety layer cut short is a failed test. Test logs and any
later script that runs the programs read the exit code.

## Options considered

- **A. Exit 1 when the hover didn't run in full:** the same pattern as the
  rescue landing (`has_failed`, then `EXIT_ERROR` from the program).
- **B. A separate exit code for a failsafe landing:** tells a cut-short
  hover apart from other errors, but adds a code every caller must know.

## Decision

Option A.

- The hover test has `has_failed`: true unless it hovered for the whole
  requested time and then landed by its own request. A safety layer landing,
  a refused request or an interrupted run all count as failed.
- The hover program returns `EXIT_ERROR` when the run itself returned
  `EXIT_OK` but `has_failed` is true, and logs why at error level.
- Other exit codes from the run (an error, the interrupt signal) pass through
  unchanged.

## Failure modes

- **Inputs:** none new; the test only reads its own steps.
- **Never:** a hover the safety layer landed early exits 0.
- **Always eventually:** unchanged; this only changes what is reported after
  the motors stop.

## Consequences

- The Hover and Take-off speeds test logs can take the exit code as the
  pass or fail of "hovered in full", next to the operator's observations.
- Tests: a mock run cut short by the safety layer exits 1; a full mock hover
  exits 0.
