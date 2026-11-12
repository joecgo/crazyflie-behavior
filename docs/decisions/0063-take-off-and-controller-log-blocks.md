# 0063: A switchable 10 ms take-off block and an always-on controller block, to the debug log

- **Status:** Accepted. Extends [ADR-0050](0050-diagnostic-log-block-to-the-debug-log.md) (debug log only, never the snapshot). Amended by [ADR-0065](0065-take-off-block-runs-from-connect-and-each-take-off.md) (2026-11-12): cflib starts a block once it's created, so with the option the take-off block also runs 2 s from the end of connect in every program; the tick thread stops it. Amended by [ADR-0067](0067-a-take-over-connects-without-the-debug-only-blocks.md) (2026-11-12): a take-over starts no controller block.
- **Date:** 2026-11-12
- **Origin:** Mixed: both blocks, the take-off block behind a switch, and testing its radio load with the Bench were mine (over the AI's recommendation of the controller block alone); the variables, FP16, the `--take-off-log` option and starting it at connect in the Bench were AI recommendations accepted.

## Context

On 2026-11-09 the drone tilted 0.4-0.9° right and nose down in the first
0.5 s after lift-off, while the motors cancelled a front-right torque (backlog
#68). The diagnostic block samples at 10 Hz: it shows the tilt's direction over
0.5 s, but not the first 100 ms, the peak or its timing, and nothing about what
the attitude and rate controllers did (their integrals). Firmware 2026.08 logs
those, and cflib's shortest period is 10 ms (`log.py:151`).

## Options considered

- **B. A take-off block:** attitude and motor power every 10 ms for the first
  2 s of a take-off. About 100 more packets a second for those 2 s.
- **C. A controller block:** the controllers' integrals, commands and
  setpoints, and the gyro, every 100 ms for the whole flight. About 10 more
  packets a second.

## Decision

Both.

- **Take-off block (B), off unless asked.**
  - `stateEstimate.roll`, `pitch`, `yaw` (float) and `motor.m1`-`m4`
    (uint16): 20 bytes, every **10 ms**.
  - Created at connect with the other blocks; started when the take-off is
    sent and stopped 2 s later, once per take-off. Nothing waits for it.
  - The hover and failsafe programs get a `--take-off-log` option, off by
    default. The bench program never takes off, so with the same option the
    adapter starts the block once at connect, for 2 s, motors off: the Bench
    measures its radio load.
- **Controller block (C), always on.**
  - `pid_attitude.roll_outI`, `pitch_outI`; `pid_rate.roll_outI`,
    `pitch_outI`; `controller.cmd_roll`, `cmd_pitch`; `controller.roll`,
    `pitch` (the attitude setpoint); `gyro.x`, `gyro.y`. Fetched as FP16
    (2 bytes each, cflib `log.py:359`): 20 of 26 bytes, every **100 ms**,
    started at connect like the diagnostic block.
- Each sample from either block is one debug line with the drone time, as in
  ADR-0050. Neither reaches the snapshot.

## Failure modes

- **Inputs:** a missing variable fails the connect, on the floor (as
  ADR-0050).
- **Never:** either block delays a take-off, a landing or a motor stop.
- **Risk:** the link already carries about 130 packets a second (backlog
  #25); B adds about 100 more for 2 s, right when the stale-data check (0.25 s)
  matters most. A stale-data landing during those 2 s, with the option on,
  points at B first.

## Consequences

- **Risks I accept knowingly:** B's radio load at take-off. The Bench check
  sends no setpoints, so its load isn't exactly a flight's: a good first
  check, not proof.
- FP16 keeps about 3 significant digits: enough to see an integral's size and
  sign, not small changes in it.
- The debug log grows by 10 lines a second, plus 200 per take-off with the
  option on.
- Tests: both blocks fit 26 bytes with periods the firmware accepts; the
  controller block starts at connect; the take-off block starts only with the
  option, when the take-off is sent, and stops after 2 s; with the option, the
  bench starts it once at connect; a sample becomes one debug line; nothing
  waits for either block.
- Glossary: adds *Take-off block* and *Controller block* (2026-11-12).
