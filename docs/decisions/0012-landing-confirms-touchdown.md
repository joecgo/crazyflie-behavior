# 0012: Motors stop only on confirmed touchdown

- **Status:** Accepted
- **Date:** 2026-10-20
- **Origin:** AI recommendation accepted (from code review).

## Context

After the high-level commander lands, the motors keep running until the
adapter stops them. The first Crazyflie adapter stopped them when the planned
landing time ran out. The landing is planned from the height estimate, which
can be stale or drifted: if it says 0.4 m while the drone is really at 1.0 m,
the motors would be cut in mid-air. Found in code review.

## Options considered

### A. Confirm touchdown with the down range sensor
A fresh down range of about 5 cm or less means landed; the position estimate's
height is the backup when the sensor has nothing usable. If touchdown is never
confirmed, keep the motors at the landing target and report it.
- **Pros:** a direct measurement of the gap below, which doesn't drift.
- **Cons:** depends on the Flow deck's down sensor; thresholds need tuning.

### B. Use the drone's own "flying" flag (supervisor)
- **Pros:** simplest.
- **Cons:** how the firmware decides that flag is unverified.

### C. Keep the timer
- **Pros:** no new logic.
- **Cons:** keeps the mid-air cut risk.

## Decision

Option A, because it relies on a direct measurement rather than an estimate
that drifts.

## Consequences

- The touchdown check lives in `drone/crazyflie/touchdown.py`: no cflib, strict
  type checking, unit tests covering the drifted-estimate case.
- A fresh down-range distance decides. "Out of range" below means still in the
  air. Only a missing, stale or invalid reading lets the height estimate decide.
- Placeholder thresholds (5 cm, readings at most 0.5 s old); VERIFY at the bench.
- During flight, an unconfirmed touchdown is logged and the motors stay on at
  the landing target.
- At shutdown, `disconnect()` waits up to a grace period for touchdown. If it's
  never confirmed, it raises and leaves the link open instead of closing it,
  because cflib's `close_link()` sends a zero-thrust setpoint that would cut
  the motors.
