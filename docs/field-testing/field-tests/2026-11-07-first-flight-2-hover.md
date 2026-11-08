# 2026-11-07-first-flight-2-hover

- **Session:** [First flight 2](../sessions/2026-11-07-first-flight-2.md)
- **Test:** Hover (flight)
- **Environment:** [Living room](../environments/living-room.md), hide-and-seek launch point, night
- **Git commit:** `189a0e1`
- **Hardware:** Crazyflie 2.1+, decks: Flow / Multi-ranger / Buzzer, battery #
- **Firmware / cflib:** 2026.08, release 2026.10, unmodified ([ADR-0047](../../decisions/0047-pinned-firmware-release-warn-on-mismatch.md)) / 0.1.34

## Goal and pass criteria
*Written before flying.*

- Goal: Hover through the project's own code with the new take-off and
  landing ([ADR-0048](../../decisions/0048-level-through-the-bad-flow-zone.md)):
  arm, take off to 0.5 m, hover 60 s, land. Land closer to the take-off point
  than in [session 1](2026-11-04-first-flight-1-hover.md) (about 4 cm).
- Also measure (not passed or failed): the mid-air swing from session 1, a
  0.85 Hz circle about 1.2 cm in radius. Compare it with the diagnostic
  block's debug lines ([ADR-0050](../../decisions/0050-diagnostic-log-block-to-the-debug-log.md)):
  attitude (roll, pitch, yaw), the four motor outputs, and the Flow deck's
  surface quality and shutter time.
- Also record the take-off: the settle height and the final descent height
  from the log, whether the cap tripped, and the sideways shift at take-off.
  Compare them with Failsafe high's.
- Pass if:
  - [ ] The initial climb ends normally: the log shows `Initial climb done:
        settle height ___ m, final descent height ___ m`, with no warning that
        the speed hasn't settled (the cap) or that the climb ran out of time.
  - [ ] The hover test reports done: armed within 2 s, reached 0.5 m (within
        0.1 m) within 5 s, hovered, landed, no error logged.
  - [ ] A 60 s hover is flown, and the drift over it is measured from the
        recording and by eye, and recorded.
  - [ ] **The landing is within 3 cm of the take-off point**, measured with a
        tape measure from the take-off mark to the drone (the drone's own
        estimate drifts).
  - [ ] Motors stop only after touchdown is confirmed, at the end of a level
        final descent (`Final descent: level, from ___ m by the down range`).
        The slow descent or the final descent's time limit still passes, but
        is recorded as a finding.
  - [ ] Each `VERIFY` item still open is confirmed or turned into a code change
        or backlog item. *List to be written from the First flight 1 findings.*
- Simulator prediction, if simulated: ___

## Pre-flight checklist

- [ ] Bench, Failsafe low and Failsafe high passed
- [ ] Code committed, hash recorded above, the same commit as the session doc's mock runs
- [ ] Propellers undamaged, battery fully charged (voltage: ___; below 3.62 V the take-off is refused, [ADR-0051](../../decisions/0051-battery-flight-limit-and-take-off-limit.md))
- [ ] Soft landing patch under the drone, flight area clear of people and pets
- [ ] Geofence configured for this space
- [ ] Video recording on

## During the test

- [ ] Mark the take-off point on the floor
- [ ] Start: `.venv\Scripts\python -m crazyflie_behavior.programs.hover --crazyflie --hover-seconds 60`
- [ ] Watch the flight; note anything unexpected while it happens
- [ ] After landing, measure from the take-off mark to the drone with a tape measure
- [ ] Note how far the drone shifted sideways during the take-off: from the take-off mark to below the drone at 0.5 m (the video helps)
- [ ] Note whether the final descent was level or the slow descent (the log says so)
- [ ] Note whether the drone slid, and whether before or after the propellers stopped
- [ ] Note whether it swings mid-air, and which way it circles seen from above

## Flights

Flown 2026-11-07, after Failsafe high and before the Bench. No geofence.

| # | What was run | Result | Data file | Notes |
|---|---|---|---|---|
| 1 | `hover --crazyflie --hover-seconds 60`, after a power cycle | Stopped at connect: the position estimate didn't settle in 20 s | `logs/2026-11-07_16-43-54_hover.log` | |
| 2 | Same | Same | `logs/2026-11-07_16-44-51_hover.log` | Flight 1's log stream still running (backlog #53) |
| 3 | Same, a flashlight on the floor under the drone | Same | `logs/2026-11-07_16-46-54_hover.log` | Same leftover stream |
| 4 | Same, after a restart | Hovered 44 s, then landed by the failsafe on stale data; exit 0 | `logs/2026-11-07_16-49-42_hover.log` | |
| 5 | `hover --crazyflie --hover-seconds 60 --chirp` | Hovered the full 60 s, landed, played "Charge", done; exit not checked | `logs/2026-11-07_17-11-24_hover.log` | The buzzer flight. Joe: "worked". Logs 17-09-30 and 17-10-34 are not listed here |

## Observations

### Joe

- Flight 4: drifted to the right and slightly forward, about 20 cm from the
  start overall. Most of the drift was at the take-off. A little dip at about
  10 cm before it climbed to the 50 cm hover height.
- None of the buzzer sounds worked.
- Flight 5 (with `--chirp`): the chirps worked but were hard to hear while
  the motors were running.
- Battery voltage, video: not recorded yet.

### Computed from the log (Claude)

- **Flight 4, take-off:** `Initial climb done: settle height 0.102 m, final
  descent height 0.152 m`, with no cap or time-limit warning. "At 0.42 m.
  Hovering for 60 s" 3.9 s after arming.
- **The hover was cut short at 44 s:** the safety pre-check failed with
  "position estimate is 0.25 s old (stale after 0.25 s); drone status is
  0.25 s old". `Final descent: level, from 0.282 m by the down range`, then
  `Touchdown confirmed`. The hover test logged no error, and the program
  exited 0 (backlog #71). So the 60 s hover wasn't flown.
- **Why the data went stale:** 4 tick overruns, at 16:49:55.8, 16:50:10.8,
  16:50:25.8 and 16:50:40.9, 15.0 s apart; the last was 140 ms late. At each,
  telemetry stopped arriving for 0.12-0.34 s while the drone's own timestamps
  stayed steady and then arrived in a burst: delayed on the laptop, not lost
  on the radio. The same stalls, 15 s apart on the same wall-clock seconds
  (:10, :25, :40, :55), are in today's mock-adapter Bench run (15:56) and a
  mock hover run at 17:00, with no drone or radio. So the cause is on the
  laptop, outside the drone and the radio. Not found yet (backlog #70).
- **Sideways shift by the estimate:** 26 cm right by the end of the initial
  climb (2.6 s), about 1 cm forward; 24-25 cm right through the hover, where
  it held within about 3 cm. The same pattern as Failsafe high: about 2 cm
  right as the motors spun up, then a steady 0.1 m/s right through the
  initial climb (backlog #68). Joe saw about 20 cm.
- **The dip:** the height estimate rose to 0.166 m, then fell to 0.102 m
  within 0.45 s of the switch to the high-level climb, then climbed to 0.5 m.
  Failsafe high dipped the same way (backlog #69). An earlier, smaller sag
  during the initial climb: 0.089 m down to 0.077 m at 1.1-1.4 s.
- **Landing bounce:** not in the log. The snapshots stop with the tick loop,
  before the final descent (backlog #72).
- **Buzzer:** no buzzer command was sent. The hover program chirps only with
  `--chirp`, and this test's command doesn't pass it; the failsafe programs
  send none. "Buzzer deck detected" was logged.
- **Motors in the hover:** M1 and M3 about 51,000, M2 and M4 about 45,000 (in
  Failsafe high, 49,000 against 42,000). Analysis: one diagonal pair working
  harder usually means the drone is countering a yaw twist, for example a
  worn propeller or motor. Worth a look at the propellers.
- **Battery** (diagnostic block): 3.916 V at rest before the take-off.
- **Flight 5, buzzer commands sent** (`17-11-24` log; sent, not heard): 1
  chirp on the floor 5.0 s before arming; 11 chirps in flight, 5.000 s apart
  (one 4.954 s gap after the tick-448 overrun, so the schedule runs on ticks);
  the first came 10.1 s after the floor chirp, 1.3 s after reaching hover
  height. A 12th went out 0.05 s into the final descent (about 0.27 m) and the
  landing went on normally. One chirp 1.0 s after landing was confirmed, then
  "Charge": 6 tones (392, 523, 659, 784, 659, 784 Hz) from 17:12:52.55, a
  `Silence()` at 17:12:54.10, done at 17:12:55.15 with the link closed cleanly.
  Tick lateness at every buzzer send was under 0.4 ms. The run's one overrun
  (154 ms) wasn't at a buzzer send.
- **Flight 5, battery vs buzzer:** the voltage can't separate the buzzer's cost
  from the normal sag and recovery. Means: 4.063 V on the floor before arming
  (chirping), 3.529 V in the hover (3.49-3.60), 3.842 V just after landing
  (motors off, no sound), 3.871 V in the chirp phase, 3.889 V during the
  tones, 3.894 V after the silence. The voltage rises in 5 mV steps all the
  way after landing, with no visible step at tone onset or at the silence. In
  the hover the mean was 3.527 V within 0.5 s after a chirp and 3.530 V
  otherwise. Measuring the buzzer's cost needs a longer on/off comparison at a
  constant load.
- **Flight 5, position after landing:** the position estimate moved about
  0.09 m/s in x with the motors at 0, at x about -1.0 m, during "Charge".
  Cause not known (carried?); Joe to say.
- **Flights 1-3:** the logs end at the estimate reset, with no estimate values
  in them, so the cause isn't in the data. Flights 2 and 3 logged "Error no
  LogEntry to handle id=1": the leftover stream from flight 1 (backlog #53).

## Next
- Code changes and ADRs: backlog #53, #67-#72.
- Next session's goal:
