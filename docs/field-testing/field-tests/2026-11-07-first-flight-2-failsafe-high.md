# 2026-11-07-first-flight-2-failsafe-high

- **Session:** [First flight 2](../sessions/2026-11-07-first-flight-2.md)
- **Test:** Failsafe high (safety)
- **Environment:** [Living room](../environments/living-room.md), hide-and-seek launch point, night
- **Git commit:** `189a0e1`
- **Hardware:** Crazyflie 2.1+, decks: Flow / Multi-ranger / Buzzer, battery #
- **Firmware / cflib:** 2026.08, release 2026.10, unmodified ([ADR-0047](../../decisions/0047-pinned-firmware-release-warn-on-mismatch.md)) / 0.1.34

## Goal and pass criteria
*Written before flying.*

- Goal: Prove the real failsafe lands the drone, now with the new take-off
  and landing ([ADR-0048](../../decisions/0048-level-through-the-bad-flow-zone.md)).
  The failsafe program (`programs.failsafe --crazyflie --fault-at hover`,
  ADR-0041) takes off to 0.5 m, hovers about 3 s, then a wrapper forges a low
  battery reading. The real pre-check fails and the failsafe lands the drone.
- Also check the take-off: this is the first full initial climb (Failsafe low
  lands during it, [ADR-0056](../../decisions/0056-adr-0048-as-built.md)).
  Record the settle height and the final descent height from the log, whether
  the cap tripped, and the sideways shift at take-off.
- Pass if:
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
- Simulator prediction, if simulated: ___

## Pre-flight checklist

- [ ] Bench and Failsafe low passed
- [ ] Code committed, hash recorded above, the same commit as the session doc's mock runs
- [ ] Propellers undamaged, battery fully charged (voltage: ___; below 3.62 V the take-off is refused, [ADR-0051](../../decisions/0051-battery-flight-limit-and-take-off-limit.md))
- [ ] Soft landing patch under the drone, flight area clear of people and pets
- [ ] Geofence configured for this space
- [ ] Video recording on

## During the test

- [ ] Mark the take-off point on the floor
- [ ] Start: `.venv\Scripts\python -m crazyflie_behavior.programs.failsafe --crazyflie --fault-at hover`
- [ ] Watch the take-off and hover, then the landing; note anything unexpected while it happens
- [ ] Note how far the drone shifted sideways during the take-off: from the take-off mark to below the drone at 0.5 m (the video helps)
- [ ] Note whether the drone landed by the failsafe or by the time limit (the log says which)
- [ ] Note whether touchdown was confirmed (the log warns if it wasn't)

## Flights

Flown 2026-11-07, after Failsafe low and before the Bench. No geofence.

| # | What was run | Result | Data file | Notes |
|---|---|---|---|---|
| 1 | `failsafe --crazyflie --fault-at hover`, no restart since Failsafe low | Arm refused, exit 1, motors never ran | `logs/2026-11-07_16-38-10_failsafe.log` | |
| 2 | Same, after a power cycle | Landed by the failsafe, exit 0 | `logs/2026-11-07_16-40-06_failsafe.log` | |

## Observations

### Joe

- Flight 2: it worked, but it moved 18 cm to the right and bounced slightly
  on the landing.
- Battery voltage, video: not recorded yet.

### Computed from the logs (Claude)

- **Flight 2:** `Initial climb done: settle height 0.113 m, final descent
  height 0.163 m`, with no cap or time-limit warning. At 0.46 m 4.0 s after
  the take-off; fault forged 3 s later; the pre-check failed with the battery
  message and a landing was sent. `Final descent: level, from 0.288 m by the
  down range`, then `Touchdown confirmed`. No "Failsafe test failed" error,
  exit 0. 142 ticks, 0 overruns.
- **Sideways shift by the estimate:** 19.7 cm right by the end of the initial
  climb (2.45 s), 21.2 cm right at the hover, 1.5 cm back. It held within
  about 1 cm of that until the fault. Close to the 18 cm Joe saw.
- **How it drifted:** as the motors spun up (0.35-0.55 s after the take-off),
  the down range read 0.000 and the estimate moved about 4 cm right. After
  that the estimate moved right at a nearly steady 0.1 m/s through the whole
  initial climb. Analysis, not observed: a sideways push at lift-off that
  nothing corrects while roll and pitch are held level (backlog #68).
- **Dip after the initial climb:** the height estimate rose to 0.178 m, then
  fell to 0.115 m within 0.45 s of the switch to the high-level climb, then
  climbed to 0.5 m. An earlier, smaller sag during the initial climb: 0.089 m
  down to 0.069 m at 1.0-1.45 s (backlog #69).
- **Battery** (diagnostic block): 4.022 V at rest before the take-off.
- **Flight 1:** refused to arm (`success=False, is_armed=False`) right after
  Failsafe low's flight, with no restart (backlog #67).

## Next
- Code changes and ADRs: backlog #67-#69.
- Next session's goal:
