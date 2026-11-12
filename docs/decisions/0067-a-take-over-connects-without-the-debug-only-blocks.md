# 0067: A take-over connects without the diagnostic and controller blocks

- **Status:** Accepted. Amends [ADR-0050](0050-diagnostic-log-block-to-the-debug-log.md) and [ADR-0063](0063-take-off-and-controller-log-blocks.md): with `take_over_flight`, the Crazyflie adapter starts neither block.
- **Date:** 2026-11-12
- **Origin:** Mixed: skipping the blocks was mine, over the AI's other option (correct ADR-0063's wording and accept the risk). Leaving the take-off block out of this was an AI choice while building, for me to confirm.

## Context

ADR-0050 and ADR-0063 say a missing variable in a debug-only block fails the
connect, "on the floor". The rescue landing's connect (`take_over_flight`,
[ADR-0038](0038-connecting-to-a-flying-drone.md)) may be to a
flying drone. A firmware without one of those variables would fail the
rescue, and the adapter would close the radio link with the drone still in
the air, leaving only the emergency stop. The controller block, always on,
added 10 variable names to that risk. The project review of ADR-0063's code
found it.

## Options considered

- **A. Keep the blocks and correct the ADRs:** accept the risk, since the
  firmware is pinned ([ADR-0047](0047-pinned-firmware-release-warn-on-mismatch.md)).
- **B. A take-over skips the debug-only blocks** (chosen).

## Decision

Option B.

- With `take_over_flight`, connect starts no diagnostic block and no
  controller block. The blocks the snapshot needs (state, battery, down range,
  Multi-ranger) are unchanged.
- The take-off block is unchanged: it runs only with `--take-off-log`, which
  the rescue landing program doesn't have.

## Failure modes

- **Inputs:** none new.
- **Never:** a missing diagnostic or controller variable fails a take-over's
  connect.
- **Always eventually:** unchanged.

## Consequences

- A rescue landing's debug log has no attitude, motor power, flow quality or
  controller lines. Its snapshots and its own log lines remain.
- No Flow deck image quality, which only the low-light warning uses, at a
  take-off from the floor. A rescue landing never sends one.
- ADR-0050's and ADR-0063's "fails the connect, on the floor" now holds:
  only a connect without take-over starts those blocks.
- Tests: a take-over's connect starts only the state, battery, down range and
  Multi-ranger blocks; without a take-over, both debug-only blocks start (as
  before).
- Glossary: no change (*Diagnostic block* and *Controller block* don't say
  when they run).
