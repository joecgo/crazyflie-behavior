# 0011: The mock adapter models the setpoint timeout

- **Status:** Accepted
- **Date:** 2026-10-20
- **Origin:** AI recommendation accepted (from code review).

## Context

In steering mode, velocity is a setpoint stream: sent every tick (ADR-0005,
ADR-0008). A real Crazyflie stops following setpoints that stop arriving. The
first mock adapter kept moving at the last velocity forever, so a bug that
forgets to stream every tick would pass every test and only show up in the air.
Found in code review.

## Options considered

### A. Model both timeout stages
No new velocity for a short time: the drone stops following. For longer: the
motors are cut and it drops.
- **Pros:** a forgotten stream fails in tests as loudly as it would in flight.
- **Cons:** the mock carries timings that must match the real firmware.

### B. Model only "stops following"
- **Pros:** simpler.
- **Cons:** the failure is quiet: the drone just stops, with no crash to notice.

### C. Keep the mock simple; catch it in the simulator later
- **Pros:** the mock stays trivial.
- **Cons:** no protection until the simulator exists.

## Decision

Option A. The mock exists to catch logic bugs, and a forgotten stream is
exactly the kind of bug that's easy to write and dangerous to fly.

## Consequences

- Placeholder timings: stops following after 0.5 s, drops after 2 s. They're
  based on our understanding of the firmware; VERIFY in field testing.
- The timeout only applies while streaming: take-off, `move_to`, `hover` and
  landing hand control to the drone and end the stream.
- The mock measures the gap on its own clock, so tests with a simulated clock
  control it exactly.
