# 0072: The final descent's speed is 0.3 m/s

- **Status:** Accepted. Amends [ADR-0070](0070-initial-climb-default-0-4-m-per-s.md): the final descent's speed.
- **Date:** 2026-11-14
- **Origin:** Mine. The AI pushed back on the evidence (below); I accepted the risks.

## Context

ADR-0070 kept the level final descent at 0.2 m/s. In First flight 6, after
the M1 motor swap, four hovers at 0.2 m/s landed 7-16 cm from the mark,
mostly toward the back. I raised `FINAL_DESCENT_SPEED` to 0.3 m/s as a local
test. The five flights that followed (both failsafes, hovers at 0.5, 0.75 and
1.0 m) landed 7-10 cm from the mark, all back right. My call (2026-11-14):
"I think the faster landing is successful".

## Options considered

- **A. 0.3 m/s (chosen).**
- **B. Keep 0.2 m/s and fly more at both speeds** under the same light and
  battery before deciding.

## Decision

Option A. The final descent flies at 0.3 m/s. Its time limit follows from the
speed, as before.

## Failure modes

- **Evidence (AI pushback):** one flight per condition; the 0.3 m/s flights
  were at night under the kitchen-center lights, the 0.2 m/s ones in daylight;
  the battery was only partly charged. Light and battery could explain the
  difference as well as the speed.
- **Touchdown:** 50% faster at contact: a harder impact on the motors,
  propellers and frame, and a higher chance of a bounce.
- **Never / always eventually:** unchanged (ADR-0070).

## Consequences

- **Risks I accept knowingly:** the confounded evidence and the harder
  touchdown, above.
- Code: the constant in `bad_flow_zone.py`. The tests read the constant, so
  none change.
- Glossary: no change (*Final descent* names no speed).
