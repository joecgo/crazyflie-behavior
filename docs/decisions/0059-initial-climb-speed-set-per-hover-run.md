# 0059: The hover program sets the initial climb's speed, 0.1-0.4 m/s, for take-off speed tests

- **Status:** Accepted. Amends [ADR-0048](0048-level-through-the-bad-flow-zone.md): the initial climb's speed can differ from the final descent's, and the initial climb's time limit scales with it. Amended by [ADR-0070](0070-initial-climb-default-0-4-m-per-s.md), 2026-11-13: the default climb speed is 0.4 m/s.
- **Date:** 2026-11-09
- **Origin:** Mixed. Testing take-off speeds in low light, steady speeds first, and a flag on the hover program for the climb only: mine. The adapter setting, the 0.1-0.4 m/s range and the scaled time limit: AI recommendations accepted.

## Context

In First flight 2 the drone drifted 18-20 cm sideways, almost all of it during
the initial climb (backlog #68): a push of a few centimeters at spin-up, then
a steady 0.1 m/s that nothing corrects while the drone is held level. If the
drift comes from the speed left over after the push, a faster climb spends
less time level and drifts less. If the push itself grows with a faster
climb, it doesn't help. Session 3 tests that. One constant,
`LEVEL_VERTICAL_SPEED` (0.2 m/s), sets both the climb and the final descent,
so changing it would also change the landing.

## Options considered

- **A. Edit the constant per flight:** no new code, but two variables change
  (climb and landing), and every flight needs its own commit.
- **B. A `take_off()` parameter in the drone interface:** behaviors could pick
  the speed, but every behavior, the safety layer and both adapters change,
  for a knob only one test uses.
- **C. An adapter setting, set by a hover program flag (chosen).**

## Decision

Option C. Both adapters take an `initial_climb_speed` keyword (default
0.2 m/s, today's speed), passed through `make_drone`. The hover program's
`--climb-speed` sets it; values outside 0.1-0.4 m/s are refused before
connecting. The final descent stays at 0.2 m/s. The initial climb's time
limit becomes the cap height over the climb speed plus 1 s: 4 s at 0.1 m/s,
1.75 s at 0.4 m/s. Session 3 flies steady speeds (for example 0.1, 0.2 and
0.4 m/s); a slow-then-fast climb waits for that data.

## Failure modes

- **Inputs:** a speed outside the range never reaches the drone. At 0.4 m/s
  the 0.2 s settle hold uses 8 cm of climb, so the settle height may reach
  the cap: the drone lands, the safe outcome, and the flight shows it.
- **Backups:** unchanged from ADR-0048: if the setpoint stream stops, the
  firmware levels the drone after 0.5 s and cuts the motors after 2 s.
- **Never:** a climb speed reaches the drone without the time limit that
  matches it.
- **Always eventually:** the motors stop, as in ADR-0048.

## Consequences

- **Risks I accept knowingly:**
  - At 0.1 m/s the drone stays level twice as long, so it may drift more than
    today; the time limit allows 4 s.
  - A faster spin-up may give a bigger push. That's what the test measures.
- Code: the climb speed in both adapters, `initial_climb_time_limit()` in
  `bad_flow_zone.py`, `make_drone`, the hover program and their tests. The
  Failsafe and Bench programs keep the default.
- No glossary change: *Initial climb* already names the part whose speed this is.
