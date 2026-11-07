# 0030: A minimal safety layer for First flight: a pre-check, one failsafe, the hover test's commands

- **Status:** Accepted. Amended 2026-11-02: a value that isn't finite counts as missing, and the Crazyflie adapter drops an estimate that isn't finite. Amended by [ADR-0039](0039-the-adapter-decides-may-be-flying.md): hover and land are approved whatever the drone status says, and the adapter decides whether the drone may be flying. Amended by [ADR-0041](0041-failsafe-tests-inject-a-fault-into-the-pre-check.md) (2026-11-03): the failsafe program's forged-battery wrapper passes commands on, an exemption for that one file. Amended by [ADR-0051](0051-battery-flight-limit-and-take-off-limit.md) (2026-11-05): the low-battery limit is 3.2 V in flight with a take-off limit of 3.62 V, and the firmware doesn't shut down at 3.0 V on a default build, so the "Backups" line below is wrong. Amended by [ADR-0054](0054-a-fresh-estimate-for-every-take-off.md) (2026-11-06): the pre-check also fails on a high velocity uncertainty while flying, a take-off needs a plausible estimate, and an estimate reset is approved only on the floor (amended 2026-11-07: no fresh reset needed for a take-off). Amended by [ADR-0053](0053-buzzer-commands-and-a-chirp-hover-test.md) (2026-11-06): a buzzer slot too, which approves every buzzer request.
- **Date:** 2026-10-30
- **Origin:** Mixed. Asking whether the safety layer needs more than a pre-check, to keep the code simple, and one failsafe for now: mine. Keeping it the only code that sends commands, the scope below and plain functions: AI recommendations accepted. Counting a value that isn't finite (NaN or infinite) as missing, and dropping such an estimate in the adapter: AI recommendations accepted in my second code review.

## Context

First flight needs the drone to take off, hover at 0.5 m and land, through
the project's own code. The ADRs give the safety layer four jobs: the safety
pre-check (ADR-0025), judging command requests and clamping them to the speed
envelope (ADR-0005), being the only code that sends commands (ADR-0008), and
failsafes (backlog #8). The question was how much of that First flight needs.

## Options considered

- **A. Minimal for First flight:** the pre-check, one failsafe, and sending the
  few commands a hover needs.
- **B. Pre-check only, with behaviors commanding the drone:** the least code,
  but it reverses ADR-0008, and the failsafe would have to fight behaviors
  for the drone.
- **C. The full safety layer now:** clamping, fast-mode approval, every slot
  and severity levels.

## Decision

Option A.

- **The safety pre-check** checks for missing or stale data, a low battery
  and a crashed or tumbled drone, plus the operator's "land now" and "hover" (ADR-0027).
- **One failsafe: land.** Any failed check lands the drone; the operator's
  "hover" holds it instead. Severity levels wait (backlog #8).
- **The safety layer stays the only code that sends commands** (ADR-0008). It
  approves arm, take off, hover and land by simple state rules, such as
  "take off only when armed and on the floor". Hover and land need a flying
  drone: on the floor, the firmware starts the move anyway and spins an armed
  drone's motors (checked in `planner.c`, 2026-10-30).
- **Velocity and fast-mode requests are refused** until steering mode and fast
  mode are built. Only the movement slot exists.
- **The pre-check and the request judging are plain functions:** a snapshot
  in, an answer out, nothing stored. Only the part that sends holds state.

## Failure modes

- **Inputs:** a stale or missing value fails the pre-check and lands the
  drone. A battery voltage or position estimate that isn't finite counts as
  missing. The Crazyflie adapter drops a position or velocity estimate that
  isn't finite, with a warning once per streak: the last finite one stays, goes
  stale within 0.25 s and fails the pre-check, and the landing goes to it
  instead of to a NaN. A NaN battery voltage isn't dropped: nothing steers by
  it, and dropping it would delay the failsafe by up to 3 s. A low battery reading does too; a noisy dip only lands it early,
  which is the safe direction. A lost link makes every value stale, but then
  the land command can't reach the drone either (backlog #26).
- **Backups:** the firmware's own battery handling comes later than ours: low
  at 3.2 V, and at 3.0 V for 5 s it shuts the drone down, which in flight is a
  drop (checked in `pm_stm32f4.c` and the platform defaults, 2026-10-30). Our
  landing must start well before.
- **Never:** a behavior's command reaching the drone without the safety
  layer; a velocity or fast-mode command before the speed envelope exists.
- **Always eventually:** a failed pre-check ends with the drone landed and its
  motors off.

## Consequences

- The speed envelope must exist before steering mode (backlog #30).
- Severity levels (backlog #8) wait until there's more than one failsafe
  worth having.
- The thresholds are placeholders in the code, to measure at the bench.
