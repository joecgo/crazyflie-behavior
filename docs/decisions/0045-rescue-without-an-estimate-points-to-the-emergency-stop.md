# 0045: A rescue that gets no estimate points to the emergency stop

- **Status:** Accepted
- **Date:** 2026-11-03
- **Origin:** AI recommendation accepted (option B).

## Context

The rescue landing connects to a flying drone ([ADR-0038](0038-connecting-to-a-flying-drone.md)).
Like every connect, it waits up to 3 s for every telemetry value
([ADR-0031](0031-connect-waits-for-first-telemetry.md)), and the adapter drops
an estimate that isn't finite. So when the drone's estimate is NaN, the
take-over connect times out, and the adapter's landing for "no estimate"
(straight down) is never reached (backlog #41). Checked in the firmware source
(`master`, 2026-11-03): the Kalman estimator's bounds check
(`kalman_supervisor.c`) compares against limits, which a NaN passes, and its
NaN check exists only in debug builds (`kalman_core.c`). The firmware's
position controller flies on that same estimate, so a drone with a NaN
estimate can't follow a position command (`go_to`, hover), which is every
landing our code has. (Corrected 2026-11-03: this first said "any landing
command". A tilt-and-thrust descent doesn't use the position estimate; see
backlog #45.)

## Options considered

- **A. A take-over connect waits only for the drone status:** the pre-check
  then fails and the failsafe lands straight down. More paths, and the landing
  can't work on a NaN estimate.
- **B. Keep the wait; its time-out message points to the emergency stop**
  when an estimate is what's missing on a take-over.
- **C. Keep it as is:** safe, but the message ("check the Crazyflie is in
  range") points the wrong way.

## Decision

Option B. When a take-over connect times out with the position or velocity
estimate missing, the error says the drone can't land under control and to
use `tools/emergency_stop.py`, with something soft under the drone first.
Any other missing value, and any normal connect, keeps the old message.

## Failure modes

- **Inputs:** an estimate that never arrives is either NaN on the drone or
  lost on the radio. In both cases no landing our code has would work.
- **Never:** the rescue landing must not claim a landing it can't fly.
- **Always eventually:** the operator is told which last resort to use.

## Consequences

- The adapter's straight-down landing with no estimate isn't a rescue path.
  After `connect()`, an estimate that stops being finite leaves the last
  finite one in place (it goes stale), so that landing remains only a guard.
- VERIFY at the Bench: the firmware version on the drone, and that its
  estimator behaves as `master` does.
- Tests: `test_taking_over_a_drone_with_no_finite_estimate_points_to_the_emergency_stop`
  and the two tests that keep the old message elsewhere.
- Closes backlog #41. Backlog #45 explores two rescues that might land a
  drone with a NaN estimate: an estimator reset in flight, then the normal
  landing, and a descent on tilt and thrust with touchdown from the raw down
  range. Until one is built, the emergency stop is the last resort.
