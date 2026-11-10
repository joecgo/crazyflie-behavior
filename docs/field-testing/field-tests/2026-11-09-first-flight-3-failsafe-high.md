# 2026-11-09-first-flight-3-failsafe-high

- **Session:** [First flight 3](../sessions/2026-11-09-first-flight-3.md)
- **Test:** Failsafe high (safety)
- **Environment:** [Living room](../environments/living-room.md), hide-and-seek launch point, low light (the room's usual night lighting, no flashlight)
- **Git commit:** `876ba6d`
- **Hardware:** Crazyflie 2.1+, decks: Flow / Multi-ranger / Buzzer, battery #
- **Firmware / cflib:** 2026.08, release 2026.10, unmodified ([ADR-0047](../../decisions/0047-pinned-firmware-release-warn-on-mismatch.md)) / 0.1.34

## Goal and pass criteria
*Written before flying.*

- Goal: Prove the real failsafe lands the drone from a hover, on the code
  with a fresh estimate for every take-off ([ADR-0054](../../decisions/0054-a-fresh-estimate-for-every-take-off.md))
  and the setpoint priority release ([ADR-0058](../../decisions/0058-release-setpoint-priority-after-motor-stop.md)).
  The failsafe program (`programs.failsafe --crazyflie --fault-at hover`,
  ADR-0041) takes off to 0.5 m, hovers about 3 s, then a wrapper forges a low
  battery reading. The real pre-check fails and the failsafe lands the drone.
- Fly it right after Failsafe low with **no power cycle**: a third arm in a
  row checks ADR-0058 again, now after a landing from 0.5 m.
- Also record the take-off: the settle height and final descent height from
  the log, whether the cap tripped, and the sideways shift at take-off
  (session 2: about 18-21 cm right, backlog #68).
- Known gaps, Joe's call: the Bench wasn't flown, and the `/project-review`
  of ADR-0054, ADR-0058 and ADR-0059 hasn't run yet.
- Pass if:
  - [ ] The drone arms with no power cycle since Failsafe low (`locked no`).
  - [ ] The initial climb ends normally: the log shows `Initial climb done:
        settle height ___ m, final descent height ___ m`, with no warning that
        the speed hasn't settled (the cap) or that the climb ran out of time.
  - [ ] The log shows `FAULT INJECTED: battery voltage forged`.
  - [ ] The pre-check fails with the battery message, and a landing is sent.
  - [ ] The drone lands and its motors stop (seen by the operator: the exit
        code can't show it, ADR-0041), and the program exits with code 0.
  - [ ] The log has no "Failsafe test failed" error (the time limit landing
        the drone is a failed test).
  - [ ] The landing needed no help from the kill switch or rescue landing.
  - [ ] The final descent was level (`Final descent: level, from ___ m by the
        down range`) and ended with `Touchdown confirmed`. The slow descent or
        the final descent's time limit still passes, but is recorded as a finding.
  - [ ] At the end, the log says `The drone reports not flying and isn't
        locked`.
- Simulator prediction: no simulator run. The mock run on `876ba6d` went
  arm, take-off, hover, fault, pre-check failed, land, exit 0.

## Pre-flight checklist

- [ ] Bench passed: **skipped** (Joe's call). Failsafe low passed by the log
- [ ] Code committed, hash recorded above, the same commit as the session doc's mock runs
- [ ] Propellers undamaged, battery charged (voltage: ___; below 3.62 V the take-off is refused, [ADR-0051](../../decisions/0051-battery-flight-limit-and-take-off-limit.md))
- [ ] Soft landing patch under the drone, flight area clear of people and pets, at least 0.3 m clear on every side
- [ ] Geofence configured for this space
- [ ] Video recording on

## During the test

- [ ] Mark the take-off point on the floor
- [ ] Start, with no power cycle since Failsafe low: `.venv\Scripts\python -m crazyflie_behavior.programs.failsafe --crazyflie --fault-at hover`
- [ ] Watch the take-off and hover, then the landing; note anything unexpected while it happens (a turn during the climb, a dip after it)
- [ ] Note how far the drone shifted sideways during the take-off: from the take-off mark to below the drone at 0.5 m (the video helps)
- [ ] After landing, measure from the take-off mark to the drone
- [ ] If the arm is refused: don't power cycle yet, note the arm request's log line, then power cycle and fly once more

## Flights

| # | What was run | Result | Data file | Notes |
|---|---|---|---|---|
| 1 | `failsafe --crazyflie --fault-at hover`, no power cycle since Failsafe low | Armed with no power cycle. Landed by the initial climb's time limit at about 0.13 m; the fault was never injected | `logs/2026-11-09_16-47-01_failsafe.log` | |

## Observations

### Joe

- It landed early, 20 cm forward and to the right.

### Computed from the logs (Claude)

- **Arm:** `locked no`, and the arm succeeded: the third arm in a row with no
  power cycle (ADR-0058).
- **Estimate reset at connect:** before it, the estimate said (-0.96, -1.15)
  m and 0.11 m/s sideways, on the floor; about 3.5 minutes had passed since
  Failsafe low's link closed. ADR-0054's reset cleared it.
- **Light:** image quality 9-15 on the floor before the take-off, lower than
  Failsafe low's 20-36; the low-light warning appeared (12). Velocity
  uncertainty 0.11-0.15 m/s until 0.40 s after the take-off, then 0.016 by
  0.45 s, when the position estimate jumped 13 cm in x.
- **Initial climb, 0.2 m/s commanded:** the height estimate went 0.02 to
  0.137 m in the 2.55 s to the time limit, about 0.05 m/s on average. It
  climbed to 0.082 m by 1.1 s, sagged to 0.061 m at 1.4 s, then climbed at
  about 0.07-0.09 m/s. No `Initial climb done` line: the climb never reached a
  final descent height (at least 0.15 m).
- **Time limit:** `The initial climb hasn't ended 2.5 s after the take-off.
  Landing.` Then `Final descent: level, from 0.134 m by the down range` and
  `Touchdown confirmed` 0.95 s later.
- **Sideways shift by the estimate**, take-off to touchdown: 23 cm forward and
  9 cm right, 13 cm of the forward part in the one jump at 0.45 s. After the
  motors stopped, the estimate kept moving forward at about 0.15 m/s on the
  floor (image quality 10-15).
- **After touchdown:** the failsafe test was still waiting for the hover, as it
  never sees the adapter's landing. 0.85 s after the motors stopped, the
  safety layer's pre-check failed (`velocity uncertainty 0.031 m/s in flight`)
  and sent a landing, which ended the run. The drone status still said flying
  then (the firmware counts the drone as flying for 2 s after the motors stop,
  ADR-0058).
- **End:** `The drone reports not flying and isn't locked`. No `FAULT
  INJECTED`, no "Failsafe test failed" error. The program's exit code needs the
  forged battery, so it should have been 1; it isn't in the log.
- **Session 2 for comparison:** that initial climb ended 2.45 s after the
  take-off, 0.05 s inside the same 2.5 s limit.

## Next
- Code changes and ADRs:
- Next session's goal:
