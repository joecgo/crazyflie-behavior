# 0071: The hover program sets the take-off height, 0.4-1.0 m

- **Status:** Accepted. Closes backlog #94.
- **Date:** 2026-11-13
- **Origin:** Mixed. 5 s hovers at several heights: mine. The flag, its range and the unchanged time limit: AI recommendations accepted.

## Context

My goal for session 6 includes 5 s hovers at several heights. The hover test
always takes off to 0.5 m (`TAKE_OFF_HEIGHT`), and the failsafe program uses
the same constant.

## Options considered

- **A. A hover program flag (chosen),** as ADR-0059 did for the climb speed.
- **B. Edit the constant per flight:** a commit per flight, and the failsafe
  program changes with it.
- **C. Up to 1.5 m, with the time limit growing with the height.**

## Decision

Option A.

- `--take-off-height`, 0.4-1.0 m, default 0.5 m. A height outside it is
  refused before connecting. The hover test takes off to it and hovers at it.
- The hover test's 5 s limit to reach the height is unchanged: at the
  0.3 m/s climb to the target it fits 1.0 m.
- The failsafe program stays at 0.5 m.

## Failure modes

- **Inputs:** a height outside the range never reaches the drone.
- **Velocity uncertainty:** not measured above 0.52 m. A straight line
  through session 4's 0.1-0.5 m predicts 0.044 m/s at 0.75 m and 0.057 at
  1.0 m, against [ADR-0064](0064-in-flight-flow-limit-grows-with-height.md)'s
  limits of 0.075 and 0.10. If it's higher, the safety pre-check lands the
  drone and the program exits 1.
- **Never:** the hover test waits for a height other than the one it asked
  for.
- **Always eventually:** unchanged.

## Consequences

- No ceiling check yet (backlog #8): 1.0 m fits the rooms flown so far.
- Code: the hover program, the hover test and their tests.
- Glossary: *Hover test* and *Failsafe low / Failsafe high* reworded (my
  OK, 2026-11-13).
