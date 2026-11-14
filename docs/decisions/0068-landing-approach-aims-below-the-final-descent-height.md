# 0068: The landing approach aims 5 cm below the final descent height; the down range ends it

- **Status:** Accepted. Amends [ADR-0048](0048-level-through-the-bad-flow-zone.md) and [ADR-0056](0056-adr-0048-as-built.md): the landing approach's aim, and its time limit, now a backup. Closes backlog #93.
- **Date:** 2026-11-13
- **Origin:** Mixed. Aiming at the settle height and letting the down range end the approach (A2): AI recommendation accepted. A backup of the plan's time plus 1 s: mine, over the AI's 0.5 s.

## Context

In all 12 landings from a hover in First flights 4 and 5, the landing
approach ended by its time at 0.26-0.33 m, still descending at 0.45-0.50 m/s,
11-17 cm above the final descent height (0.15-0.19 m). The drone trails the
`go_to`'s plan: the firmware's position controller has no feed-forward of the
planned speed (firmware 2026.08, `position_controller_pid.c` 229-231). The
level final descent, which holds no position, then lasted about 1.35 s
instead of about 0.8 s, carrying any sideways speed on. The adapter already
ends the approach when the down range reaches the final descent height; the
plan's time ran out first.

## Options considered

From a model fitted to session 4's four landings (position gain 2.0 per
second, fitted to the logs, not read from the firmware; `drafts/ff4/approach.py`),
for a landing from 0.51 m:

- **A1. Same aim, the down range ends it:** reaches the height 0.34 s after
  the plan's end at only 0.12 m/s, so a small model error leaves it waiting
  for the backup.
- **A2. Aim at the settle height, the down range ends it (chosen):** crosses
  the final descent height at 1.42 s (the plan ends at 1.32 s), at 0.36 m/s;
  the level final descent lasts about 0.7-0.8 s.
- **B. A slower approach, ended by time:** at 0.2 m/s it ends 3.4 cm high,
  0.6 s later. No logic change.
- **C. Accept it.**

## Decision

Option A2.

- The `go_to` aims 0.05 m below the final descent height: the settle height
  in every flight so far.
- The final descent starts when the down range reaches the final descent
  height (unchanged), or at the backup: the `go_to`'s duration plus 1 s. The
  same rule with no position estimate (the move straight down from the
  commander's own position).
- At or below the final descent height at the landing request: the final
  descent at once (unchanged).

## Failure modes

- **Inputs:** with no usable down range, the `go_to` ends at its aim (about
  0.11 m by the estimate) and holds position there by flow, in the bad-flow
  zone, until the backup, then ADR-0019's slow descent. A height estimate
  reading high puts the aim lower in reality; the down range ends the
  approach first, and without it the `go_to` may reach the floor, where the
  slow descent's time limit stops the motors. A short down range (something
  below) ends the approach early, as before.
- **Backups:** the backup time runs on the clock, sharing neither the down
  range nor the estimate. A hung tick leaves the drone holding at the aim, now
  inside the bad-flow zone (backlog #26).
- **Never:** the motors stop before touchdown is confirmed or the final
  descent's time limit (unchanged).
- **Always eventually:** the final descent starts, and the motors stop
  (ADR-0048).

## Consequences

- **Risks I accept knowingly:**
  - The mock adapter teleports the approach, so it can't show the lag
    (backlog #84): the first flight is the first proof.
  - The 0.36 m/s and the 0.7-0.8 s are a model's, with a fitted gain, not
    refitted to session 5's eight landings (their approaches ended a little
    faster, 0.47-0.50 m/s against 0.45).
  - The level final descent starts faster than its own 0.2 m/s, so the
    touchdown may be harder. Nothing logs a bounce after the tick loop stops
    (backlog #72).
  - With no usable down range, up to 1 s holding at about 0.11 m before the
    slow descent.
- Code: `_start_landing_approach` (the aim and the backup) and the adapter's
  tests. The mock adapter is unchanged.
- Glossary: *Landing approach* reworded (my OK, 2026-11-13).
