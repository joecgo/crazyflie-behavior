# First flight 6

> A draft plan, written 2026-11-13 by Claude from Joe's goals for the session
> (below). Lines marked **Open** are Joe's to decide. When the session has a
> date, this file is renamed `YYYY-MM-DD-first-flight-6.md` and its test logs
> are drafted from the template.
>
> **Revised 2026-11-13 against session 5**
> ([First flight 5](2026-11-13-first-flight-5.md), flown 2026-11-13 between
> this plan's goal and its first draft). Session 5's numbers here are Claude's
> analysis of its logs.

A session is one trip with one or more field tests, flown in order. Each
field test has its own log in [`../field-tests/`](../field-tests/).

- **Milestone:** First flight, session 6
- **Environment:** [Kitchen](../environments/kitchen.md), center of the room, all lights on, at night: the setup of session 4's last four flights (**Open:** see "Low light")

## Plan
*Written before flying. The tests in order, each linked to its log.*

**Joe's goal (2026-11-13):** wrap up First flight. Take-offs and landings
within 5 cm in low light; the initial climb at 0.4 m/s, with no more take-off
speed tests; 5 s hovers at different heights; both failsafe tests. Joe's open
question: whether to test different landing speeds or setups.

### What session 4 says about the goal (analysis, Claude)

- After the M1 propeller swap, session 4's four flights landed 3.5, 6, 7 and
  9 cm from the mark (Joe): one of four within 5 cm.
- By the logs the take-off moved the drone 2.5-6 cm and the landing 2-6 cm,
  and it wandered 2-4 cm in the hover
  ([First flight 4](2026-11-12-first-flight-4.md), "Analysis"). The logs can't
  check 5 cm themselves: their totals differ from the tape by 5-12 cm.

### What session 5 adds (analysis, Claude)

Eight hover flights at 0.4 m/s in daylight, on commit `c7ecffe`. Every flight
took off, hovered and landed. Joe: "I would say it failed due to propeller
issues." No landing distances are recorded so far.

- **The motor balance changed from flight to flight.** In two flights M1 was
  commanded about 16% more thrust than M3, in two others about 2%. Session 4's
  four flights after the swap were balanced in roll and pitch.
- **The hover needed more thrust:** a thrust command of 44,600-46,300, against
  43,000-43,500 in sessions 3 and 4 and a thrust base of 43,000.
- **M4's vibration in the propeller test rose** to 25-61 (session 4: 9-18).
- **The climb paused at about 0.3 m,** just after the hand-over to the
  high-level climb: under 0.10 m/s for 0.34-0.40 s, sinking up to 1 cm
  (session 4: 0.26 s, never sinking). Joe saw it (backlog #69).
- **The drone left the initial climb at 0.01-0.16 m/s sideways** (session 4
  after the swap: 0.04-0.11) and slid 3-12 cm before the position hold brought
  it back to within 1-3.5 cm.
- **The landing approach ended 11-17 cm above the final descent height** in
  all eight landings, as in session 4 (backlog #93). By the position estimate,
  which is unreliable near the floor, the final descent then moved the drone
  3-28 cm (session 4's two flights by the same script: 0-4 cm).
- **Prediction, revised:** the first draft's "landings 3-8 cm from the mark,
  about half within 5 cm" assumed session 4's balance after the swap. On the
  drone as it flew in session 5, landings within 5 cm aren't expected, and no
  landing change fixes a balance that differs between flights. If the hardware
  work (below) brings back session 4's balance, the first prediction stands:
  no change planned here touches the take-off's part (backlog #68).

### Before the session: hardware, decisions and code

Decided by Joe on 2026-11-13. Built and checked by `/project-review` on
2026-11-13 and 11-14. The Crazyflie adapter and the safety layer change, so
Joe's code review comes before flying. Mock runs on 2026-11-14 (mock, not
field results): `failsafe --fault-at climb` and `--fault-at hover` failed the
pre-check on the forged battery and landed; `hover --hover-seconds 5
--take-off-log` took off, hovered and landed.

0. **The hardware** (backlog #83): one time-boxed pass, then stop. New
   propellers on all four motors, one propeller test, one hover; the M4 motor
   swapped only if it still reads high. The propeller test and the hover are
   this session's tests 1 and 3. It replaces the first draft's "replace M2's
   propeller after the 5 cm flights": landings on a balance that changes
   between flights can't show whether a landing change helped.
1. **The landing approach**
   ([ADR-0068](../../decisions/0068-landing-approach-aims-below-the-final-descent-height.md)):
   aimed 5 cm below the final descent height, ended by the down range, with
   the plan's time plus 1 s as a backup.
2. **The initial climb's default speed, 0.4 m/s**
   ([ADR-0070](../../decisions/0070-initial-climb-default-0-4-m-per-s.md)),
   so the failsafe tests fly it too.
3. **The hover program's take-off height**
   ([ADR-0071](../../decisions/0071-hover-program-sets-the-take-off-height.md)):
   `--take-off-height`, 0.4-1.0 m.
4. **The battery dip at spin-up**
   ([ADR-0069](../../decisions/0069-low-battery-needs-two-readings-in-a-row.md)):
   two low readings in a row; the sag value stays 0.42 V. These programs miss
   the dip by their timing, so this one can follow the others if time is
   short.
5. **The thrust base** stays 43,000
   ([ADR-0061](../../decisions/0061-thrust-base-set-at-connect.md)), with its
   VERIFY note. If test 3's hover thrust stays above about 44,500 after the
   hardware pass, it's decided again before the 5 cm flights.

### Tests, in order

0. **Set-up.** The take-off mark on the floor, with a line for the drone's
   heading; a tape measure. Battery at 4.0 V or more at rest. Change or charge
   it under 3.85 V at rest: in session 5 the spin-up dip went under 3.20 V
   from 3.84 V at rest and below, a landing from 3.76 V at rest reached 3.23 V,
   and one reading under 3.20 V ends the flight's tick loop. A flight with a
   10 s hover cost about 0.03 V at rest, and the first battery was at 3.84 V
   after four flights, so plan on the second battery and a charge.
1. **Propeller test,** on the floor, as the hardware check (backlog #83).
2. **Bench**, 20 s, as a link and sensor check. Optional.
3. **Hover at 0.5 m**, 5 s, one flight: the hardware check in the air.
   Proposed: Claude reads the hover's thrust command and the balance between
   M1 and M3 from the log before the next flight; if they look like session
   5's (thrust command over about 44,500, or M1 more than about 5% above or
   below M3), the measured flights wait. **Open.**
4. **Failsafe low**, one flight.
5. **Failsafe high**, one flight. Neither has flown on the code since session
   4 (`e6ec43f`, `edaa6e0`, `1d4ae8f`) or on this session's changes.
6. **Hover at 0.5 m**, 5 s, three flights: the 5 cm baseline.
7. **Hover heights**, 5 s each: 0.75 m and 1.0 m, two flights each
   (**Open:** which heights).
8. **Turned around**, optional: two more 0.5 m flights with the drone turned
   180° on the mark. In session 4 the drone left every take-off moving to its
   own right. If it still moves to its own right, the cause is on the drone;
   if it moves the other way, the cause is in the room. Only worth flying if
   the balance repeats from flight to flight: two flights can't show a
   direction through session 5's spread.
9. **Rescue landing** (**Open:** Joe's call of 2026-11-13 was to fly it in
   the next session; session 5 didn't, and it isn't in the new goal). If
   flown, last: it ends with the hover program killed in the air.

Tests 3 to 7 are ten flights; with test 8, twelve. Each test needs the ones
before it to pass (README, "Sessions and test logs").

### Pass criteria (**Open:** Joe sets them)

- **Failsafe low and Failsafe high:** as in session 4's logs (the fault
  fires, the pre-check fails on the battery, the drone lands and its motors
  stop, exit code 0). Proposed: the landing distance is recorded for both, and
  the 5 cm goal applies to Failsafe high only. Failsafe low lands from the
  initial climb, before any position hold.
- **Hover at 0.5 m and Hover heights:** every flight reaches its height,
  hovers 5 s and lands, exit code 0. Proposed for the distance: each landing
  measured from the mark with the tape; the session passes if at least five
  of the seven are within 5 cm and none is over 10 cm.
- The README's Hover row says the distance is recorded with no pass or fail.
  A 5 cm criterion changes that row, or stays this session's own goal.
  **Open.**

### What to record

- For every flight: where it landed from the mark on both axes (forward or
  back, left or right, in the drone's direction at the take-off), by the
  tape; the exit code (PyCharm's Run window; sessions 4 and 5 captured none).
- What Joe does to the propellers or the battery between flights, and when:
  session 5's balance can't be matched to a cause without it.
- `--take-off-log` on the hover flights, as in sessions 4 and 5 (no tick
  overrun in session 5's eight flights). **Risk accepted knowingly in
  session 4:** backlog #87 is still open.

### Low light

The low-light warning's reading doesn't tell day from night. On the floor the
image quality was 11-41 in session 5's daylight and 12-26 in session 4's
night flights, both under the warning's 60, so the warning fired at every
take-off. In the hover it was 131-139 in daylight and 124-126 at night with
all four kitchen lights on. To the Flow deck, the kitchen at night with its
lights on is close to daylight.

Proposed: the same kitchen setup, so sessions 4 and 5 are the comparison.
**Open:** whether that counts as the goal's "low light". The living room,
where hide-and-seek will be played, has two lights and is darker; nothing is
measured there.

### Landing speeds and setups (Joe's question)

Not as a separate test in this session. One landing change is planned (the
landing approach), and every flight here measures it against session 4's four
landings. A second landing variable in the same session would hide which one
helped. If the landing still moves the drone more than about 3 cm after the
change, the next single variables are the final descent's speed (0.2 m/s
today) and a short settle at the final descent height before the drone goes
level.

### Predictions (analysis, Claude)

The mock adapter can't show these (backlog #84); they come from session 4's
and session 5's logs.

- The initial climb ends 0.70-0.80 s after the take-off. The hover test
  counts the drone as at 0.5 m about 1.7 s after it if the hover thrust is
  back near the thrust base (session 4), and about 1.9 s if not (session 5,
  with the pause at 0.3 m).
- Velocity uncertainty about 0.031-0.033 m/s at 0.5 m (both sessions), 0.044
  at 0.75 m and 0.057 at 1.0 m, against limits of 0.05, 0.075 and 0.10: a
  straight line through session 4's 0.1-0.5 m, not measured above 0.52 m.
- With the landing approach changed (A2): the final descent starts at the
  final descent height (about 0.16 m) with the drone descending at about
  0.36 m/s, about 1.4 s after the landing request from 0.5 m. Session 5's
  approaches ran a little faster than session 4's (0.47-0.50 m/s at their
  end, against 0.45), so the 0.36 m/s may be low.
- Failsafe low at 0.4 m/s: the fault at about 0.45-0.5 s, with the initial
  climb ending at 0.70-0.80 s, so 3 to 7 ticks to spare. If the log doesn't
  show "Landing during the initial climb", the flight didn't test that
  landing.

## Before the session
*Done at the desk, not at the session. If any code changes after these runs, run them again.*

- **Commit to fly:** `d12975a`
- [x] Mock adapter run of each test's program on that commit passed (2026-11-14, exit code 0, no tick overruns):
  - [x] `.venv\Scripts\python -m crazyflie_behavior.programs.failsafe --fault-at climb`
  - [x] `.venv\Scripts\python -m crazyflie_behavior.programs.failsafe --fault-at hover`
  - [x] `.venv\Scripts\python -m crazyflie_behavior.programs.hover --hover-seconds 5 --take-off-log`, then the same with `--take-off-height` 0.75 and 1.0
- [x] Laptop on the charger, high-performance power plan (backlog #70): both confirmed by Joe 2026-11-14
- [ ] Joe's code review of what's new since the last entry in `REVIEW.md`'s "My reviews": **deferred by Joe on 2026-11-14** to the next milestone, because of a planned refactor. Risk accepted knowingly: this session flies Crazyflie adapter and safety layer changes that only `/project-review` has checked.

## Results
*From the operator or the recordings, never from an AI. One line per test: passed, failed or not flown.*

### Propeller test runs

After Joe replaced M4's propeller only (2026-11-14). Run by Joe; console
output pasted by Joe. Sideways vibration variance X+Y (Z in brackets), voltage
sag per motor, and the noise floor X+Y.

| Run | M1 | M2 | M3 | M4 | Sag M1-M4 (V) | Noise floor |
|---|---|---|---|---|---|---|
| 1 | 4.12 (3.39) | 8.33 (11.29) | 6.21 (0.85) | 8.95 (14.22) | 0.47 0.49 0.52 0.52 | 0.0037 |
| 2 | 5.11 (3.08) | 8.97 (10.69) | 7.40 (0.85) | 10.02 (21.37) | 0.48 0.49 0.52 0.52 | 0.0042 |
| 3 | 4.09 (3.03) | 7.45 (8.49) | 8.32 (1.08) | 10.09 (18.25) | 0.48 0.48 0.50 0.51 | 0.0035 |
| 4 | 2.92 (2.58) | 13.30 (10.96) | 4.73 (0.95) | 9.97 (9.24) | 0.41 0.43 0.45 0.45 | 0.0038 |
| 5 | 3.89 (1.43) | 10.83 (9.75) | 5.47 (1.13) | 10.30 (8.75) | 0.42 0.44 0.44 0.45 | 0.0035 |
| 6 | 4.44 (1.70) | 15.33 (14.02) | 4.01 (1.20) | 10.68 (10.45) | 0.42 0.44 0.45 0.45 | 0.0037 |

"Kalman prediction rate off" was printed after every run (74, 39, 86, 91, 24,
53). Runs 4-6 were pasted by Joe after test 3. Joe: "M4 just sounds louder,
like there is more vibration".

### Test 3, hover at 0.5 m (14:45)

- Joe: "significant drift to the right (23 cm)". Joe: about 10 cm at the
  take-off and 10 cm at the landing, both in the bad-flow zone.
- Two earlier attempts (14:43, 14:44) timed out opening the link: stuck
  propeller test processes from 14:38 held the radio.
- Analysis (Claude, from the log): hover motor outputs (the diagnostic
  block's `motors`, not the thrust command) M1 about 52,700, M2 41,500, M3
  50,500, M4 40,500 (mean about 46,300; session 4's hovers 47,900-50,300). Battery 4.04 V before,
  3.59-3.65 V in the hover. Image quality 49 at take-off, 122-139 in the hover.
- Next (Joe's call, 2026-11-14): first Joe chose to replace the other three
  propellers and skip test 8, then changed it to flying test 8 (turned
  around): one 0.5 m hover with the drone turned 180° on the mark.

### Test 8, turned around, hover at 0.5 m (14:51)

- Joe: take-off "relatively straight, maybe 3-5 cm drift"; landing "about
  10-15 cm drift, for a total of 20 cm to the right (relative to the drone)".
- Analysis (Claude, from the log): hover motor outputs M1 about 52,600, M2
  41,900, M3 51,600, M4 40,800 (mean about 46,700), the same split between
  the pairs as test 3. Battery 3.94 V before; 3.27 V at spin-up; 3.50-3.56 V
  in the hover. Image quality 23 at take-off.

### Level check across sessions 4-6 (analysis, Claude, 2026-11-14)

From the diagnostic block of every real hover log since session 4. Roll is
the mean in each phase, in degrees.

| Flights | Roll on the floor | Roll in the initial climb | Roll in the final descent | Right side's share (M1+M2) in the hover |
|---|---|---|---|---|
| Session 4 (4) | +0.02 to +0.04 | +0.01 to +0.27 | -0.40 to +0.17 | 0.500-0.502 |
| Session 5 (8) | -0.17 to +0.29 | -0.05 to +0.78 | -0.08 to +0.98 | 0.502-0.510 |
| Session 6 (2) | -0.25 to +0.05 | +0.42 to +0.89 | +0.56 to +1.76 | 0.506-0.509 |

- On the floor the drone reads level, so the level calibration looks fine.
- Since session 5 the drone rolls one way in both bad-flow-zone phases, most
  in the final descent, and the right side's motors (M1 front-right, M2
  back-right, by session 4's analysis) work harder in the hover. Which way a
  positive roll leans hasn't been checked in the firmware source.
- The diagonal split (M1+M3)/(M2+M4) is 1.14-1.40 in all three sessions.

### After test 8

- Joe: the battery is centered. Joe replaced M2's propeller (M3's not yet).
- Propeller test runs 7-9, after M2's new propeller (pasted by Joe; same
  columns as the table above):

| Run | M1 | M2 | M3 | M4 | Sag M1-M4 (V) | Noise floor |
|---|---|---|---|---|---|---|
| 7 | 4.66 (2.32) | 7.90 (1.60) | 3.23 (2.0) | 8.09 (2.47) | 0.45 0.45 0.49 0.49 | 0.0039 |
| 8 | 5.63 (2.52) | 9.52 (1.52) | 2.65 (1.67) | 6.78 (3.46) | 0.45 0.47 0.50 0.50 | 0.0038 |
| 9 | 3.45 (3.64) | 5.07 (0.89) | 2.32 (1.60) | 7.67 (2.74) | 0.48 0.48 0.50 0.51 | 0.0043 |

  Joe: "the prop tests are making things look more balanced now."

### Hover at 0.5 m after M2's propeller (15:02 and 15:03)

- Flight 1 (15:02), Joe: "went way off to the right and failed". The log:
  image quality 16 at take-off; "The horizontal speed estimate hasn't
  settled by 0.25 m. Landing." at 0.26 m in the initial climb; touchdown
  confirmed; the hover test then reported "not at 0.50 m after 5 s". An
  abnormal end by the README's rule; flight 2 was flown after it.
- Flight 2 (15:03), Joe: "only went slightly to the right and back equally
  about 9 cm". Hovered 5 s and landed.
- Analysis (Claude, flight 2's log): image quality 15 at take-off. Roll +0.52°
  in the initial climb and +0.40° in the final descent (test 3: +0.89° and
  +1.76°). Right side's share 0.506. Motor outputs mean about 48,500.
- Joe's call (2026-11-14): flies on after flight 1's abnormal end, with more
  light added at the take-off mark. Risk accepted knowingly, against the
  README's rule to stop and write it up first.

### Hover at 0.5 m with more light (15:05)

- Joe: "still drifting right this time about 25 cm, half on take-off and half
  on landing (about)".
- Analysis (Claude, from the log): image quality 27-40 on the floor (38 at
  take-off), 113-144 from about 0.1 m up. Roll -0.24° on the floor, +0.43° in
  the initial climb, +0.07° in the hover, +1.12° in the final descent. Right
  side's share 0.507.
- Joe: "the yaw change about 15 degrees counter clockwise on take-off, then
  twist back".
- Analysis (Claude): the logged yaw rises 20-26° in the first 1.5 s after the
  take-off request in this flight, 14:45 and 15:03, and in session 4 and 5
  flights checked (16:21 on 11-12, 11:09 on 11-13), then turns back.

### Controller analysis (Claude, 2026-11-14)

From the Controller block lines (roll rate integral, the controller's
standing roll trim). Not yet checked in the firmware source.

- Mid-hover trim: session 4 -690 to +500; session 5 -900 to -4,200;
  session 6 -1,800 to -3,200. Same sign in every flight since session 5.
- 15:05 flight: about -1,280 at the hand-over from the initial climb, then
  -335, rebuilt to about -1,600 over about 0.8 s; about -2,400 before the
  level final descent, then -490. The two drops come at the two phases where
  the drone drifts (backlog #101).
- Pitch is balanced (front share 0.498-0.503), so the imbalance is side to
  side, not at one corner.

### Battery shifted left

- Joe: the battery was already as far left as it can go; it couldn't be
  moved further.
- Next (Joe's call, 2026-11-14): replace the M1 motor with the one spare.

### After the M1 motor swap

Propeller test runs 10-11 (pasted by Joe):

| Run | M1 | M2 | M3 | M4 | Sag M1-M4 (V) | Noise floor |
|---|---|---|---|---|---|---|
| 10 | 5.60 (3.61) | 6.84 (10.08) | 1.48 (0.54) | 7.09 (9.05) | 0.49 0.48 0.49 0.50 | 0.0033 |
| 11 | 5.55 (4.01) | 5.52 (7.59) | 1.84 (0.68) | 7.65 (10.07) | 0.48 0.48 0.49 0.49 | 0.0034 |

Run 10 also printed "ESTKALMAN: State out of bounds, resetting".

Three hovers at 0.5 m (15:15, 15:17, 15:18). Joe: "the take-off has been
pretty smooth with 0-5 cm of movement, but the landing has been rough, ending
first 9 cm to the back left, then 7 cm back right, then 16 cm back left, the
last landing was the worst".

Analysis (Claude, from the logs):

- Right side's share 0.496-0.499 (before the swap 0.506-0.509). Roll trim in
  the hover +660 to +1,380 (before: -1,800 to -3,200). Roll in the initial
  climb -0.20° to -0.04° (before: +0.42° to +0.89°).
- Pitch trim in the hover now -1,700 to -2,050 (15:05 flight: about -60 to
  +350); front share 0.495. At the start of the final descent the pitch trim
  fell to about 0 and rebuilt over about 0.5 s, as the roll trim did before.
- Image quality 15-17 at take-off.
- 15:18 flight: battery 3.81 V before, 3.15 V at spin-up.

One more hover (15:20). Joe: "landed 7 cm left back, with a pretty even
take-off". Analysis (Claude): right side's share 0.500, front share 0.494;
pitch +0.68° in the initial climb and +0.63° in the final descent. Battery
3.79 V before, lowest reading 3.05 V. Image quality 26 at take-off.

### Local test change: faster final descent

Joe raised `FINAL_DESCENT_SPEED` (`drone/crazyflie/bad_flow_zone.py`) from
0.2 to 0.3 m/s to try to reduce the landing error. Uncommitted, no ADR; for
this session's tests only. Every flight below uses 0.3 m/s unless noted.

### Lighting

Joe: "i would say it was daylight for all previous tests in session 6 and now
it is night with all the lights on in kitchen center". The flights above were
in daylight; the flights below are at night under the kitchen-center lights.

Joe: the battery is charged "a little bit, but it isnt full".

### Remaining tests (night, 0.3 m/s final descent)

Propeller test output (pasted by Joe):

| M1 | M2 | M3 | M4 | Sag M1-M4 (V) | Noise floor |
|---|---|---|---|---|---|
| 9.39 (5.85) | 12.38 (14.92) | 2.91 (0.71) | 8.89 (6.35) | 0.41 0.40 0.42 0.41 | 0.0033 |

It also printed "ESTKALMAN: WARNING: Kalman prediction rate off (39)".

One flight per condition (the plan had three at 0.5 m and two each at 0.75 m
and 1.0 m). Joe: "failsafe low 7cm back right / failsafe high 7cm back right /
bench 0.5 10cm back right / bench 0.75 8cm back right / bench 1 10cm back
right".

Analysis (Claude, from the logs and the firmware source, 2026-11-14):

- Battery 4.01-4.10 V before each flight; image quality 10-31 at take-off;
  no tick overruns.
- **The trim is lost at the start of every final descent after a landing
  approach.** The switch from the high-level commander to the level
  setpoints is a setpoint mode change, and firmware 2026.08 then restarts
  every controller integral, the rate integrals that hold the trim included
  (`controllerPid`, `controllerPidReinitialize`; the same restart as the
  thrust's, backlog #69). In all eight such final descents since the M1
  motor swap, the pitch trim fell from -1,480 to -3,340 to between -450 and
  +150 within 0.1 s, then rebuilt over about 0.5 s (the firmware's rate gains,
  250 and 500, give a 0.5 s time constant): the whole level part at 0.3 m/s.
  Failsafe low, whose final descent continues the initial climb's level
  setpoints with no mode change, kept its trim (-805, then -692). A negative
  pitch trim holds the nose down against a nose-up push, so without it the
  drone tilts back. The hover's pitch trim since the swap: about -1,500 to
  -2,700 (Failsafe high about -900).
- **The final descent starts mid-correction.** In the last 0.3 s of the four
  landing approaches, the position hold was rolling the drone right (attitude
  setpoint +1.4 to +4.0°, against ±0.5° in the hovers), and in the three
  hovers the speed estimate at the start of the final descent was 0.05-0.10
  m/s. The level part brakes neither.
- **The level part was shorter at 0.3 m/s:** in the three hovers, 0.45 s
  from the final descent start to a down range under 2 cm, against
  0.85-0.95 s at 0.2 m/s (15:15-15:20).
- **Dead reckoning of the level part** (the logged tilt at 10 Hz plus the
  speed estimate at its start): 2-6 cm at 0.3 m/s, 5-12 cm at 0.2 m/s. On its
  larger axis it points the way Joe measured in 12 of the 13 flights since
  14:45 with a measured landing. The exception is Failsafe low: about 2 cm by dead reckoning
  against Joe's 7 cm back right, so several cm of a landing error can come
  from outside the level flight (the spin-up on the floor, the touchdown) or
  from tilt the 10 Hz samples miss.
- Signs, checked in the firmware source: a positive roll lowers the right
  side and a positive pitch raises the nose (`kalman_core.c`'s legacy
  attitude, `power_distribution_quadrotor.c`).

## Next session
*What the results decide: another session, or the milestone is done.*

Joe (2026-11-14): out of time for more flights, so the session ends here. He
judged the faster landing successful: the final descent is now 0.3 m/s
([ADR-0072](../../decisions/0072-final-descent-0-3-m-per-s.md), with the
confounds recorded there). After the analysis, Joe accepted the landing
drift: the 5 cm goal is dropped, a landing target needs 25 cm clear in every
direction, and **First flight is done**
([ADR-0073](../../decisions/0073-landing-drift-accepted-25-cm-clearance.md)).
