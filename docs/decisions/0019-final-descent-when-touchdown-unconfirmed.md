# 0019: Only the down range confirms touchdown; otherwise a bounded final descent

- **Status:** Accepted. Supersedes part of [ADR-0012](0012-landing-confirms-touchdown.md): the height-estimate fallback, and holding at the landing target when touchdown isn't confirmed.
- **Date:** 2026-10-24
- **Origin:** Mixed. Finding that the fallback can drop the drone, and requiring that it always lands rather than hovering until the battery dies: mine, from code review. The bounded final descent and its safeguards: AI recommendations accepted.

## Context

ADR-0012 let the position estimate's height confirm touchdown when the down
range had nothing usable. On a Crazyflie that height comes mostly from the same
down sensor, so when the sensor fails the backup fails too, and the motors could
be cut in mid-air. Removing the backup alone would leave the drone hovering
until its battery dies, and then it drops anyway.

## Options considered

- **A. Keep the height fallback:** always stops, but can drop the drone from height.
- **B. No fallback:** never drops it, but can hover until the battery dies.
- **C. Confirm with several independent signals** (no vertical movement, low
  motor power): the most robust, but needs bench data to tune.
- **D. Only the down range confirms, plus a bounded final descent.**

## Decision

Option D. Cutting the motors in mid-air is the danger; descending isn't.

- **Touchdown** is confirmed only when fresh down readings stay at or below the
  touchdown distance for a short hold time, so one noisy reading can't.
- If the planned landing ends without that, the drone starts the **final
  descent**: one slow, straight-down move by the high-level commander. It needs
  no streamed setpoints, so it keeps going if ticks stop (ADR-0011).
- The motors stop when touchdown is confirmed, or at the final descent's time
  limit, when the drone must be on the floor. The limit is set once, when the
  final descent starts, from the highest down reading in the last second (so a
  short outlier can't shorten it), or from the most the drone could be above the
  floor (about the ceiling) without one.

## Consequences

- `touchdown.py` holds the rules: `TouchdownDetector` (the hold time and recent
  readings) and `final_descent_deadline`. The motors always stop, so shutdown no
  longer raises or leaves the link open, and shutdown during a landing finishes
  it instead of starting over.
- Placeholders to verify at the bench: a 0.3 s hold, 0.1 m/s, a 2 s margin, and
  2.0 m when the height is unknown (up to 22 s of final descent). VERIFY that a
  relative `go_to` is accepted after the high-level landing finishes.
- **Risks I accept knowingly:**
  - The time limit assumes the drone really descends at 0.1 m/s. With a failed
    down sensor, the estimate the controller uses is degraded too, so the real
    rate is unknown.
  - Shutdown can block for up to about 29 s. Interrupting it (Ctrl-C) closes the
    link, which cuts the motors: use the kill switch, not Ctrl-C.
  - In a space taller than about 2 m, the time limit can be too short when the
    down range reads out of range. Fine for ordinary rooms; matters for the
    attic.
- Option C stays in the backlog as a later improvement.
- Tested with a fake cflib (`tests/drone/crazyflie/test_adapter_landing.py`);
  planted bugs (no time limit, no hold time, outliers kept) each fail tests.
- Glossary term: *Final descent*.
