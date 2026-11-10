# 2026-11-09-first-flight-3-failsafe-low

- **Session:** [First flight 3](../sessions/2026-11-09-first-flight-3.md)
- **Test:** Failsafe low (safety)
- **Environment:** [Living room](../environments/living-room.md), hide-and-seek launch point, low light (the room's usual night lighting, no flashlight)
- **Git commit:** `876ba6d`
- **Hardware:** Crazyflie 2.1+, decks: Flow / Multi-ranger / Buzzer, battery #
- **Firmware / cflib:** 2026.08, release 2026.10, unmodified ([ADR-0047](../../decisions/0047-pinned-firmware-release-warn-on-mismatch.md)) / 0.1.34

## Goal and pass criteria
*Written before flying.*

- Goal: Prove again that the real failsafe lands the drone from the initial
  climb ([ADR-0049](../../decisions/0049-failsafe-low-fires-its-fault-during-the-initial-climb.md),
  [ADR-0057](../../decisions/0057-failsafe-low-fires-at-5-cm.md)), now on the
  code with a fresh estimate for every take-off ([ADR-0054](../../decisions/0054-a-fresh-estimate-for-every-take-off.md))
  and the setpoint priority release ([ADR-0058](../../decisions/0058-release-setpoint-priority-after-motor-stop.md)).
  Then fly it a second time **without a power cycle**, to check that the
  drone no longer locks after a flight (backlog #67, closed by ADR-0058).
- Known gaps, Joe's call: the Bench wasn't flown first, and the
  `/project-review` of ADR-0054, ADR-0058 and ADR-0059 hasn't run yet, so
  this flies code that hasn't been reviewed.
- Pass if, for each flight:
  - [ ] The log shows `FAULT INJECTED: battery voltage forged`, and the
        battery that tripped the pre-check is the forged 3.00 V, not the real one.
  - [ ] The pre-check fails with the battery message, and a landing is sent.
  - [ ] The log says `Landing during the initial climb: no landing approach.`
  - [ ] The drone lands and its motors stop (seen by the operator), and the
        program exits with code 0.
  - [ ] The log has no "Failsafe test failed" error.
  - [ ] The landing needed no help from the kill switch or rescue landing.
  - [ ] At the end, the log says `The drone reports not flying and isn't
        locked`, not the time-out or "locked" warning.
- And for flight 2:
  - [ ] Its arm request logs `locked no`, and the drone arms with no power
        cycle since flight 1.
- Simulator prediction: no simulator run. The mock run on `876ba6d` went
  arm, take-off, fault, pre-check failed, land, exit 0; the mock never locks,
  so it can't predict the second flight.

## Pre-flight checklist

- [ ] Bench passed: **skipped** (Joe's call)
- [ ] Code committed, hash recorded above, the same commit as the session doc's mock runs
- [ ] Propellers undamaged, battery charged (voltage: ___; below 3.62 V the take-off is refused, [ADR-0051](../../decisions/0051-battery-flight-limit-and-take-off-limit.md))
- [ ] Soft landing patch under the drone, flight area clear of people and pets
- [ ] Geofence configured for this space
- [ ] Video recording on

## During the test

- [ ] Flight 1: `.venv\Scripts\python -m crazyflie_behavior.programs.failsafe --crazyflie --fault-at climb`
- [ ] Flight 2: put the drone back on the mark, **no power cycle**, and run the same command
- [ ] Watch the climb and the landing; note anything unexpected while it happens (sideways drift during the climb, where it stopped climbing, a bounce)
- [ ] Note whether the drone landed by the failsafe, or by the climb's time limit or settle cap (the log says which)
- [ ] Note whether touchdown was confirmed or the final descent ran out its time limit
- [ ] If flight 2's arm is refused: don't power cycle yet, note the arm request's log line (armed, can arm, locked), then power cycle and fly once more

## Flights

| # | What was run | Result | Data file | Notes |
|---|---|---|---|---|
| 1 | `failsafe --crazyflie --fault-at climb` | Landed by the failsafe | `logs/2026-11-09_16-42-57_failsafe.log` | |
| 2 | Same, no power cycle since flight 1 | Armed with no power cycle, landed by the failsafe | `logs/2026-11-09_16-43-24_failsafe.log` | |

## Observations

### Joe

- Flights 1 and 2: each landed 6 cm to the right.

### Computed from the logs (Claude)

- **Both flights:** the forged 3.00 V tripped the pre-check ("land below
  3.20 V") 0.85 s after the take-off was sent, a landing was sent, and the
  log says "Landing during the initial climb: no landing approach". The
  final descent was level, from 0.064 m (flight 1) and 0.068 m (flight 2) by
  the down range, and ended with `Touchdown confirmed`. No "Failsafe test
  failed" error. The exit code isn't in the log.
- **No lock (ADR-0058):** after each touchdown, about 2.0 s later, the log
  says "The drone reports not flying and isn't locked". Flight 2's arm
  request logged `locked no` and the arm succeeded. The drone's clock
  (`drone_time`, 443 s then 470 s) shows no reboot between the flights.
  Backlog #67's lock didn't happen.
- **Sideways shift by the estimate, take-off to fault:** flight 1, 2.4 cm
  right and 2.8 cm forward; flight 2, 5.5 cm right and 1.1 cm forward. The
  log has no estimate after the tick loop stops, so the final descent isn't
  in it. Flight 1's 2.4 cm is well short of the 6 cm Joe saw. Analysis, not
  observed: the rest came either during the final descent or from the
  estimate being off; this log can't tell which.
- **Yaw:** both flights turned about 13-14 degrees during the climb (yaw
  from 0 to 13.5 by the fault), and stayed there through the landing.
  Session 2's logs weren't checked for this.
- **Light:** the low-light warning appeared both times (image quality 20
  and 36 at the take-off); the quality rose above 90 once the drone was a
  few centimeters up.
- **Battery** (diagnostic block): 4.06 V at rest before both take-offs.

## Next
- Code changes and ADRs:
- Next session's goal:
