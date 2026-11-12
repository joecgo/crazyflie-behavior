# 0064: The in-flight flow limit grows with height above 0.3 m

- **Status:** Accepted. Amends [ADR-0060](0060-pre-check-flow-while-the-drone-may-be-flying.md): flow means a velocity uncertainty under 0.03 m/s in every check except the safety pre-check's in-flight check above 0.3 m. Closes backlog #80.
- **Date:** 2026-11-12
- **Origin:** Mixed: the formula and using the height estimate were mine; the 0.1 m/s cap was an AI recommendation I accepted; the strictest limit for an unknown height and no extra filter were AI recommendations accepted.

## Context

In First flight 3's Take-off speeds, flight 5, the safety pre-check landed the
drone about 1 s into the hover at 0.5 m: the velocity uncertainty reached
0.030 m/s while the Flow deck's image quality stayed about 90-110. In the
firmware source, the Flow deck's flow noise is fixed (2 pixels) and the flow
model divides speed by height, so with good flow the uncertainty still grows
with height. A fixed 0.03 fits one height. The hide-and-seek game will fly above
0.5 m, but probably not above 1 m.

## Options considered

- **A height-dependent limit** (chosen).
- **A higher fixed limit:** loosens the check near the floor too, where 0.03
  has worked.
- **Another sign of flow** (image quality): a new input, with its own noise.

## Decision

- In-flight limit = max(0.03, 0.1 × height), capped at **0.1 m/s**: 0.03 up
  to 0.3 m, then 0.1 × height, reaching 0.1 at 1 m. The formula is continuous
  at 0.3 m.
- Height is the position estimate's height (z): the firmware already fuses
  and smooths the range readings, so there's no filter of ours.
- A missing, stale or non-finite height uses 0.03, the strictest. (A stale
  position estimate already fails the pre-check.)
- Only the safety pre-check's in-flight check changes. The take-off rule (on
  the floor) and the bad-flow zone's flow check (below 0.3 m) keep 0.03.
- The failure message states the limit it used and the height.

## Failure modes

- **Inputs:** a wrong high height estimate loosens the limit, to at most 0.1.
- **Never:** the in-flight limit is under 0.03 or over 0.1.
- **Always eventually:** unchanged.

## Consequences

- **Risks I accept knowingly:** at 1 m a real runaway is caught later than
  at 0.03. The cap stays until the geofence gives a real ceiling.
- The 0.1 per meter isn't measured: no hover at 0.5 m lasted over 1 s. Session
  4's Hover checks where the uncertainty settles against the limit.
- Tests: 0.03 at and below 0.3 m; 0.05 at 0.5 m; 0.1 at 1 m and above; 0.03
  for a missing or NaN height; a hover at 0.5 m with uncertainty 0.04 passes
  the pre-check; the take-off rule still refuses at 0.03.
- Glossary: no change (*Velocity uncertainty* and *Safety pre-check* don't
  state the limit).
