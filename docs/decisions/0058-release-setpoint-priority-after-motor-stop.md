# 0058: After a motor stop, the adapter releases the setpoint priority and closes the link only once the drone isn't flying

- **Status:** Accepted
- **Date:** 2026-11-08
- **Origin:** Mixed. Releasing the priority, waiting for "not flying" before closing, and decoding the supervisor's locked and can-be-armed bits in the same change: AI recommendations accepted. Keeping the Crazyflie term "locked" in the drone status: mine, over the AI's generic "needs restart".

## Context

In First flight 2 every arm request right after a completed flight was
refused (`success=False, is_armed=False`) until a power cycle (backlog #67).
The 2026.08 firmware source shows why (`supervisor.c`,
`supervisor_state_machine.c`, `commander.c`, `crtp_commander_high_level.c`):

- A streamed setpoint, the stop setpoint included, raises the commander's
  priority above the high-level planner's. Until `notify_setpoint_stop`
  releases it, the stopped planner's "motors off" setpoints are rejected, so
  the setpoint's age keeps growing.
- The supervisor counts the drone as flying for 2 s after the motors stop.
  A setpoint older than 0.5 s while flying moves it to "Warning, level out",
  which has no way to "Landed". Older than 2 s, it goes to "Exception, free
  fall", then **Locked**, which refuses every arm request until a reboot.
- cflib's `Crazyflie.close_link()` sends a zero-thrust setpoint
  (`send_setpoint(0, 0, 0, 0)`), which raises the priority again. The radio
  driver's `close()` throws away packets still queued.

The level final descent (ADR-0048, ADR-0056) ends with `send_stop_setpoint`,
and the link closes about 10 ms after touchdown. Both lock the drone.

## Options considered

- **A. Release the priority after the stop (chosen).** The stopped planner then
  feeds "motors off" setpoints, the way the firmware's own comment says to
  hand back to it.
- **B. Disarm right after touchdown.** "Flying" without arming goes straight
  to Reset. But the drone arms itself, and the disarm has the same timing
  problem at the link close.

How the link closes after A:

- **Wait for "not flying" (chosen).** Keep the link open until a fresh drone
  status says not flying, with a time limit.
- **Close without the zero setpoint** (the radio-only close of ADR-0038). Fast,
  but a release still queued when the link closes is thrown away.

## Decision

- Every motor stop sends, in this order: the stop setpoint (only while a
  setpoint stream is running, as now), the high-level stop, then
  `send_notify_setpoint_stop`.
- After a flight, `disconnect()` keeps the link open until a fresh drone
  status says not flying, up to `NOT_FLYING_TIME_LIMIT` (3 s, a placeholder:
  2 s of the firmware's hysteresis plus margin). On a time-out it logs a
  warning and closes anyway.
- The drone status gains two flags decoded from the supervisor bitfield:
  `can_arm` and `is_locked`, keeping the Crazyflie's term "locked" (the
  drone refuses to arm until it's power cycled). Every arm request logs both
  (a warning when locked), because the drone refuses an arm without saying
  why. The end of the wait logs them too.
- "After a flight" means after any motor stop this session, so a program
  that never flew closes at once.
- The emergency stop still locks the drone on purpose. No change there.

## Failure modes

- **Inputs:** a missing or stale drone status during the wait: the time limit
  ends it, the link closes, and the drone may lock. The next connect's status
  shows it, instead of a bare arm refusal.
- **Backups:** the stop setpoint itself stops the high-level planner (any
  setpoint above the planner's priority does, `commander.c`), so a lost
  high-level stop still leaves it stopped. Both share the radio link, so a
  lost link loses both, and the release too. On a lost link no zero setpoint
  arrives either, and the drone's state is unknown until the next connect.
- **Never:** the motors run after the motor stop. The release must come after
  the stop: a released priority with a running planner would let it fly its
  trajectory again. Packets on one link arrive in the order sent.
- **Always eventually:** the link closes and the program exits, within the
  time limit.

## Consequences

- Each flying program ends up to about 2 s later.
- **Risk accepted knowingly:** the wait proves only that the status said not
  flying. That rests on the bitfield decode, checked against cflib's bit
  positions, and on the firmware source above; the next field session shows
  it on hardware.
- A relaunch on the same link (hide-and-seek) needs only the release: the
  drone goes Flying → Landed → Reset, then can arm. How long that takes
  (the `supervisor.landedTimeout` parameter) isn't checked yet: backlog.
- **Portability, accepted knowingly:** `is_locked` is a Crazyflie term that
  reaches behavior code through the drone status (ADR-0006's checkpoint).
  Another drone would need it renamed or mapped onto its own state.
- Mock adapter: it reports the new flags; it never locks.
- Glossary: "Drone status" lists the two new flags; new term "Setpoint priority".
- Closes backlog #67.
