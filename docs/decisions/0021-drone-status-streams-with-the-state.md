# 0021: Drone status streams in one log block with position and velocity

- **Status:** Accepted
- **Date:** 2026-10-24
- **Origin:** Mixed. Found in my code review. Streaming status instead of polling it: AI recommendation accepted. Using one full block: my call.

## Context

The Crazyflie adapter polled drone status (armed, flying, crashed, tumbled) on
its own thread, because each read blocks for up to about 0.2 s. A failed read
would end the thread. Worse, cflib's `read_bitfield()` doesn't raise on a
timeout: it returns the last value, or 0 if it never had one, and the adapter
stamped that as fresh. A stale status looked current, and a missing one read
as "all flags false". Position and velocity also came in separate blocks, so a
snapshot could mix moments.

## Options considered

- **A. Keep polling, and make the loop survive errors:** still can't tell a
  timeout from a real reading without cflib's private state.
- **B. Stream status as a log variable:** the firmware logs the same bitfield
  as `supervisor.info` (bits checked against cflib's constants, 2026-10-24).
- **C. B, with position, velocity and status in one block.**

## Decision

Option C: one "state" block of 6 floats and the 2-byte bitfield, exactly the
26-byte limit. The polling thread is gone. All three values share one drone
timestamp, and one packet carries them instead of three.

## Failure modes

- **Inputs:** a lost packet loses all three at once; they go stale together,
  which staleness checks see. Before the first packet, status is `None`
  (unknown), not "all clear".
- **Backups:** none; the drone status is a report, not a backup for anything.
- **Never:** stale status that looks fresh.
- **Always eventually:** every packet updates all three.

## Consequences

- The telemetry buffer writes all three under one lock
  (`write_estimates_and_status`), so a snapshot never mixes two packets.
- A firmware without `supervisor.info` makes `connect()` fail before flight,
  with a message to update the firmware. A test checks the block's 26-byte
  budget. VERIFY at the bench.
- The block is full: anything added later (yaw, for rotation: backlog #14)
  goes in another block.
- The period (50 ms) stays a placeholder for backlog #2.
- Tested in `tests/drone/crazyflie/test_adapter_telemetry.py`.
- Glossary term: *State block*.
