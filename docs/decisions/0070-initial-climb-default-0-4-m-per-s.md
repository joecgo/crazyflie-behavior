# 0070: The initial climb's default speed is 0.4 m/s; the final descent keeps 0.2 m/s

- **Status:** Accepted. Amends [ADR-0059](0059-initial-climb-speed-set-per-hover-run.md): the default climb speed. Closes backlog #95 and #78.
- **Date:** 2026-11-13
- **Origin:** Mixed. 0.4 m/s as the default: mine. Splitting the constant: AI recommendation accepted. Closing #78: AI recommendation accepted.

## Context

ADR-0059 let the hover program set the initial climb's speed and kept
0.2 m/s as the default, which the failsafe program flies. Since the M1
propeller swap, ten flights at 0.4 m/s (Take-off speeds in First flight 4,
its Hover, and First flight 5's eight) all reached the hover. My call
(2026-11-13): "I think 0.4 m/s is going to be the one." One constant,
`LEVEL_VERTICAL_SPEED`, sets both the climb's default and the final
descent's speed.

## Options considered

- **A. Default 0.4 m/s, the final descent with its own constant (chosen).**
- **B. A `--climb-speed` flag on the failsafe program:** two programs to
  keep in step.
- **C. Keep 0.2 m/s:** the failsafe tests fly a climb no other flight uses.

## Decision

Option A.

- Both adapters' initial climb defaults to 0.4 m/s, so the failsafe program
  flies it. The hover program's `--climb-speed` keeps 0.1-0.4 m/s, with
  0.4 as its default.
- The final descent keeps 0.2 m/s, with its own constant.
- The initial climb's time limit follows ADR-0059's formula: 1.75 s.
- **Backlog #78 closes:** with the 43,000 thrust base, the climbs run at their
  commanded speed (lift-off at 0.37-0.53 s, the initial climb ending at
  0.70-0.80 s at 0.4 m/s).

## Failure modes

- **Inputs:** unchanged (ADR-0059). At 0.4 m/s the 0.2 s settle hold uses
  8 cm of climb.
- **Failsafe low:** its fault needs the down range at 0.05 m twice, about
  0.45-0.5 s after the take-off. That leaves 3-7 ticks before the initial
  climb ends. A fault after it lands the drone from the climb to the target
  instead, and the flight hasn't tested the landing during the initial
  climb: its log shows which.
- **Never:** a climb speed reaches the drone without its time limit
  (unchanged).
- **Always eventually:** unchanged.

## Consequences

- **Risks I accept knowingly:**
  - Failsafe low's thin margin, above.
  - The pause at about 0.3 m after the hand-over (backlog #69) comes with
    every take-off.
  - The busiest motor peaks at 61,000-62,700 of 65,535 at spin-up.
- Code: the two constants in `bad_flow_zone.py`, both adapters, `start_up`,
  the hover program's default, and tests.
- Glossary: no change (*Initial climb* names no speed).
