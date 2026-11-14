# Draft: first-flight-6

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

- **Commit to fly:** `<hash>`
- [ ] Mock adapter run of each test's program on that commit passed:
  - [ ] `.venv\Scripts\python -m crazyflie_behavior.programs.failsafe --fault-at climb`
  - [ ] `.venv\Scripts\python -m crazyflie_behavior.programs.failsafe --fault-at hover`
  - [ ] `.venv\Scripts\python -m crazyflie_behavior.programs.hover --hover-seconds 5 --take-off-log`, then the same with `--take-off-height` at each height flown
- [ ] Laptop on the charger, high-performance power plan (backlog #70)
- [ ] Joe's code review of what's new since the last entry in `REVIEW.md`'s "My reviews"

## Results
*From the operator or the recordings, never from an AI. One line per test: passed, failed or not flown.*

## Next session
*What the results decide: another session, or the milestone is done.*
