# 0052: The mock adapter's down range follows its height

- **Status:** Accepted. Closes backlog #34.
- **Date:** 2026-11-06
- **Origin:** AI recommendation accepted: #34's first option, with the floor reading and the test override.

## Context

The mock adapter's down range read out of range on the floor and in the air
(backlog #34, seen 2026-10-30), while a real drone reads a few centimeters on
the floor and about its height when flying. So nothing that uses the down
range could run on the mock. Failsafe low's climb trigger
([ADR-0049](0049-failsafe-low-fires-its-fault-during-the-initial-climb.md))
needs it: on 2026-11-05 its mock rehearsal never fired the fault and failed by
the time limit.

## Options considered

- **A. The mock reports its height as the down range:** small, and enough for
  the tests that need it; a perfect reading, with no noise.
- **B. Wait for the simulator** (focus area 5): realistic readings, but
  Failsafe low can't be rehearsed on the mock until then.

## Decision

A. The floor is flat at height 0.

- The down range reads the mock's height, never less than 0.02 m, its reading
  on the floor. The real drone read 0.019-0.024 m at rest (Bench, 2026-11-04).
- A test that sets the down range with `set_range_reading` fixes it from then
  on, as for the other directions.
- No noise, no maximum range and no delay: the mock stays a simple fake, and
  realistic readings are the simulator's job.

## Consequences

- Failsafe low's mock rehearsal passes (`programs.failsafe --fault-at climb`).
- The mock still teleports on take-off and landing, so it never shows a
  climb through the bad-flow zone; ADR-0048's level parts in the mock are
  separate work (ADR-0011).
- **Risk:** a perfect reading can hide code that fails on real ones, such as
  near-zero junk (backlog #49). Tests that need bad readings set them.
- The bench program's summary on the mock shows the down range at 0.02 m.
