# 0065: ADR-0063 as built: the take-off block runs 2 s from the end of connect and 2 s from each take-off

- **Status:** Accepted. Amends [ADR-0063](0063-take-off-and-controller-log-blocks.md): with `--take-off-log`, the take-off block also runs at connect in the hover and failsafe programs, not only in the Bench, and it's created last in connect, not with the other blocks. Closes backlog #85.
- **Date:** 2026-11-12
- **Origin:** AI recommendations accepted: option C, the tick thread for the stop, creating the block last in connect, and stopping it before the landing at disconnect.

## Context

Building ADR-0063: cflib 0.1.34 starts a log block as soon as the drone
confirms its create (`log.py` 551-563); the firmware's create alone doesn't
start it. So the take-off block can't be created at connect and left stopped
until the take-off. Created with the other blocks, about half of a 2 s run at
connect would fall in the wait for the battery's first sample (about 1 s),
before the first tick, where the Bench's snapshots can't see it.

## Options considered

- **A. Stop it at connect:** stop it once the drone confirms cflib's start (a
  few samples), start it at each take-off. The Bench needs a second setting to
  run it at connect, and connect waits for the confirmation.
- **B. Create it at take-off:** the create packet in flight that ADR-0063
  avoided.
- **C. 2 s from the end of connect and 2 s from each take-off:** what creating
  it does anyway. One mechanism, and no setting of the Bench's own.

For the stop: the tick thread; cflib's receive thread, in the block's
callback (a send blocked by a full radio queue would stall all telemetry for
up to 2 s); or a timer thread (a new thread sending packets, outside the fake
clock in tests).

## Decision

Option C, stopped by the tick thread.

- With `--take-off-log`, the take-off block is created last in connect, after
  the wait for the first telemetry, so its 2 s fall in the first ticks. They
  count from the create request.
- Each take-off sent starts it again, after the take-off's own commands, for
  2 s from then. If it's still running, its 2 s just restart, with no packet.
- The tick thread stops it in `update_take_off_and_landing`, once its 2 s are
  up and the drone has confirmed the start, so the stop can't overtake
  cflib's start. Up to a tick late.
- `disconnect()` stops it before its landing.
- The bench program needs nothing more: its 2 s at connect are ADR-0063's
  Bench check.

## Failure modes

- **Inputs:** a start the drone never confirms leaves the block running until
  the link close, which stops every block.
- **Never:** a take-off, a landing or a motor stop waits for the block; the
  landing at disconnect runs with the block on.
- **Always eventually:** the block stops, by the tick thread or at
  disconnect.

## Consequences

- **Risks I accept knowingly:** with the option, every program adds 2 s of
  10 ms samples on the floor at connect: about 100 more packets a second and
  200 debug lines. Without chirps, the hover's arm and take-off come within
  those 2 s, so the block runs on from connect to 2 s after the take-off. A
  stale-data failure from its load then shows on the floor first, where it
  ends the run before the take-off.
- Tests: created last in connect and only with the option; stopped 2 s later
  once the start is confirmed, never before; a take-off starts it again, or
  restarts the 2 s of a running one; `disconnect()` stops it before its
  landing; without the option, no block.
- Glossary: *Take-off block* updated (2026-11-12).
