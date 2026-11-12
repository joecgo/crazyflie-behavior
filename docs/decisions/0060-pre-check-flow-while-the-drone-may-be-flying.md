# 0060: The pre-check checks the flow while the drone may be flying; one floor speed limit

- **Status:** Accepted. Amends [ADR-0054](0054-a-fresh-estimate-for-every-take-off.md): the in-flight velocity uncertainty check runs while the drone may be flying ([ADR-0039](0039-the-adapter-decides-may-be-flying.md)), not while the drone status says flying; flow means an uncertainty under 0.03 m/s in every check; the take-off rule and the reset log share one floor speed limit. Amends [ADR-0039](0039-the-adapter-decides-may-be-flying.md) (noted 2026-11-12): the snapshot carries the adapter's "may be flying", part of ADR-0039's option B, which it rejected; hover and land are unchanged. Closes the after-touchdown part of backlog #75 and the safety layer part of #79.
- **Date:** 2026-11-10
- **Origin:** AI recommendations accepted, from the project review of ADR-0054's code.

## Context

ADR-0054 checks the velocity uncertainty only while the drone status says
flying, so a drone landed at a dark hiding spot doesn't fail the pre-check for
good. But the status says flying for 2 s after the motors stop
([ADR-0058](0058-release-setpoint-priority-after-motor-stop.md)). In First
flight 3's Failsafe high, after the adapter's own climb time-limit landing,
the pre-check failed on the uncertainty of a drone already on the floor and
sent a landing (backlog #79). The adapter's "may be flying" turns false as
soon as our motor stop goes out.

The review also found the 0.03 m/s limit read two ways: the pre-check passed
at exactly 0.03, while the take-off rule and the settle height count 0.03 as
no flow. And the 0.05 m/s floor speed was two constants: the take-off rule's
(refuses at 0.05) and the reset log's (warned only over 0.05).

## Options considered

- **The in-flight gate:** the drone status (as built); "may be flying",
  carried in the snapshot (ADR-0039's option B, for this check); a failsafe landing that ends on the floor clears
  the failed pre-check (#75's other option); or leave it for backlog #8.
- **The limits:** one rule and one constant; the same comparisons but two
  constants; as built.

## Decision

- The snapshot carries the adapter's "may be flying" from when it took the
  snapshot, like `is_in_initial_climb`. The mock adapter's is its flying
  flag. The safety pre-check checks the velocity uncertainty only while it's
  true, outside the initial climb. Judging arm, take-off and reset requests
  still uses the drone status: refusing them for 2 s after a landing is the
  safe side.
- Flow is arriving only with the velocity uncertainty under 0.03 m/s, in
  every check. The pre-check now also fails at exactly 0.03.
- One floor speed, `FLOOR_MAX_SPEED` (0.05 m/s), in the drone interface
  module: a still drone's horizontal speed estimate is under it. The take-off
  rule refuses at or over it, and the reset log calls the estimate it erases
  implausible at or over it.

## Failure modes

- **Inputs:** "may be flying" says flying when unsure (a missing or old drone
  status), so then the check runs.
- **Backups:** unchanged from ADR-0054.
- **Never:** the pre-check skips the velocity uncertainty while the drone may
  be flying, outside the initial climb.
- **Always eventually:** as in ADR-0054.

## Consequences

- **Risks I accept knowingly:** a dark final descent can still fail the
  pre-check for good; #75 stays open for that part.
- The snapshot now carries what the adapter sent (its motor stop), which
  ADR-0039 avoided. The adapter still uses its own "may be flying" for hover,
  land and disconnecting. It goes against backlog #8's "flight state from the
  drone, not from what was sent", so deciding #8 revisits this.
- Behaviors can read "may be flying" too. Whether they should, to see a
  landing they didn't ask for, stays open in #79.
- Tests: the pre-check ignoring the uncertainty after the motors stop while
  the status still says flying, and checking it while the drone may be
  flying whatever the status; failing at exactly 0.03; the Crazyflie
  adapter's and the mock's snapshot flag.
- Glossary (updated 2026-11-12): *May be flying* says every snapshot carries
  it, and *Safety pre-check* checks the velocity uncertainty while the drone
  may be flying.
