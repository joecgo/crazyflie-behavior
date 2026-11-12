# 2026-11-12-first-flight-4

A session is one trip with one or more field tests, flown in order. Each
field test has its own log in [`../field-tests/`](../field-tests/).

- **Milestone:** First flight, session 4
- **Environment:** [Living room](../environments/living-room.md), hide-and-seek launch point, {lighting setup}

## Plan
*Written before flying. The tests in order, each linked to its log.*

[First flight 3](2026-11-09-first-flight-3.md) passed Failsafe low; Failsafe
high and the Hover failed. The firmware's thrust base made the initial climbs
slow (fixed by [ADR-0061](../../decisions/0061-thrust-base-set-at-connect.md),
not yet flown), and the safety pre-check's fixed velocity uncertainty limit
landed both flights that reached 0.5 m about 1 s into the hover. Session 4
flies the code built since:

- [ADR-0064](../../decisions/0064-in-flight-flow-limit-grows-with-height.md):
  the in-flight flow limit grows with height, 0.05 m/s at 0.5 m. Its 0.1 per
  meter isn't measured; the Hover shows where the velocity uncertainty
  settles against the limit.
- [ADR-0062](../../decisions/0062-hover-program-fails-when-the-hover-is-cut-short.md)
  and [ADR-0066](../../decisions/0066-hover-program-reports-by-exit-code-only.md):
  the hover program exits 1 when the hover is cut short. The exit code alone
  reports it, so each Hover flight records its exit code (PyCharm's Run
  window).
- [ADR-0063](../../decisions/0063-take-off-and-controller-log-blocks.md) and
  [ADR-0065](../../decisions/0065-take-off-block-runs-from-connect-and-each-take-off.md):
  the controller block, always on, and the take-off block with
  `--take-off-log`, for the take-off tilt and torque (backlog #68). The take-off
  block runs 2 s from the end of connect and 2 s from each take-off. The Bench
  measures its radio load first.
- [ADR-0067](../../decisions/0067-a-take-over-connects-without-the-debug-only-blocks.md):
  a rescue landing connects without the diagnostic and controller blocks.
  Flown only if a program dies with the drone in the air (README).
- Backlog #70 (laptop stalls): option A only. The laptop runs on the charger
  with a high-performance power plan; the Claude app stays open. Each test log
  records the tick loop summary.
- Backlog #83 (yaw torque imbalance): the propeller test, on the floor, before
  the Bench. The propeller swap and the spare motor wait.

0. Propeller test, motors spinning on the floor, no flight (no log; results
   in this doc)
1. Bench, with `--take-off-log` (log to be drafted)
2. Failsafe low, with `--take-off-log` (log to be drafted)
3. Failsafe high, with `--take-off-log` (log to be drafted)
4. Take-off speeds, with `--take-off-log`: 0.1, 0.2 and 0.4 m/s (0.6 waits
   on ADR-0059's range, below) (log to be drafted)
5. Hover, 60 s, with chirps and `--take-off-log`, at a climb speed chosen
   from Take-off speeds' results (log to be drafted)

Each test needs the ones before it to pass. If one fails, stop and write it
up before flying the next (README, "Sessions and test logs"). The safety
tests fly again because the Crazyflie adapter changed (README, "When to
repeat a test"). Take-off speeds comes before the Hover, as in session 3: it
flies the speed comparison again after ADR-0061 (backlog #68), and its
results choose the Hover's climb speed.

**Joe's choices (2026-11-12):**

- `--take-off-log` on every test, if the Bench shows no latency issues with
  it. If the Bench does, the flying tests run without it. **Risk accepted
  knowingly:** backlog #87 (the block's log lines are written on cflib's
  receive thread) is still open, so a stale-data landing with the option on
  can't be put down to the radio load or to those lines. The Bench measures
  both together, without setpoints (ADR-0063).
- The Hover's climb speed is chosen after Take-off speeds.
- The Hover chirps (`--chirp`). **Risk accepted knowingly:** in session 3 the
  chirp's 5 s on the floor let the estimate run away 2.2 m before the
  take-off (backlog #81, deferred until before the geofence).
- Take-off speeds: 0.1, 0.2, 0.4 and 0.6 m/s.

**Open:**

- 0.6 m/s is outside ADR-0059's 0.1-0.4 m/s, which the hover program
  refuses. Flying it needs a new ADR that amends ADR-0059.
- The Bench's pass line for "no latency issues" with `--take-off-log`.
- How many flights per speed (session 3 flew two rounds).

## Before the session
*Done at the desk, not at the session. If any code changes after these runs, run them again.*

- **Commit to fly:** `<hash>`
- [ ] Mock adapter run of each test's program on that commit passed:
  - [ ] Bench: `.venv\Scripts\python -m crazyflie_behavior.programs.bench --take-off-log`
  - [ ] Failsafe low: `.venv\Scripts\python -m crazyflie_behavior.programs.failsafe --fault-at climb --take-off-log`
  - [ ] Failsafe high: `.venv\Scripts\python -m crazyflie_behavior.programs.failsafe --fault-at hover --take-off-log`
  - [ ] Take-off speeds: `.venv\Scripts\python -m crazyflie_behavior.programs.hover --hover-seconds 5 --take-off-log --climb-speed 0.1`, then the same with `0.2` and `0.4`
  - [ ] Hover: `.venv\Scripts\python -m crazyflie_behavior.programs.hover --hover-seconds 60 --chirp --take-off-log`, exit code 0, then the same with each climb speed it might fly
  - [ ] Rescue landing: `.venv\Scripts\python -m crazyflie_behavior.programs.rescue_landing`
- [ ] Laptop on the charger, high-performance power plan (backlog #70)
- [ ] Joe's code review of what's new since `0846826` (the last entry in
      `REVIEW.md`'s "My reviews"): it covers the safety layer and Crazyflie
      adapter changes this session flies

## Results
*From the operator or the recordings, never from an AI. One line per test: passed, failed or not flown.*

## Next session
*What the results decide: another session, or the milestone is done.*
