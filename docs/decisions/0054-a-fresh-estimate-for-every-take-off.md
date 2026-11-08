# 0054: Behaviors request estimate resets on the floor; the velocity uncertainty is checked at take-off and in flight

- **Status:** Accepted. Amends [ADR-0030](0030-minimal-safety-layer-for-first-flight.md): the safety pre-check also checks the velocity uncertainty while flying, and the take-off rule checks the estimate. Amends [ADR-0025](0025-safety-pre-check-and-command-slots.md): the estimate reset request has no command slot. Closes backlog #48. Amended 2026-11-07, before its code: behaviors request a reset when they want a clean launch, with no command slot and no wait after it; the reset command is built now, not with the round start; the adapter ignores a reset while the drone may be flying; the take-off rule's floor threshold moves to the drone interface module. Amended 2026-11-08, before its code: the drone takes off without flow in low light, and the flow is checked at the top of the initial climb instead (see "Amendment, 2026-11-08"). That also amends [ADR-0048](0048-level-through-the-bad-flow-zone.md) (the settle height needs a low velocity uncertainty) and [ADR-0029](0029-connecting-has-time-limits.md) (`connect()` no longer waits for the estimate), and closes backlog #53 and #60.
- **Date:** 2026-11-06
- **Origin:** Mixed. The velocity uncertainty and the landed-drone check, a reset command, landing on a high uncertainty in flight, and no hold or bad-flow-zone exemption: AI recommendations accepted. Proving it by cutting the flow in software, in its own test program: mine. On 2026-11-07, all mine: building the reset now, for a clean launch without restarting the program; behaviors deciding when to reset; no slot (over the AI's movement slot); no wait after a reset (over the AI's 5 s wait in the take-off rule). The adapter ignoring a reset while the drone may be flying, and moving the floor threshold to the drone interface module: AI recommendations accepted. On 2026-11-08, mine: taking off without flow in low light, trusting the climb to reach flow above the bad-flow zone, and the low-light warning as a log line. AI recommendations accepted: checking the flow at the top of the initial climb, the floor check only with flow, the snapshot saying when the initial climb runs, no wait in `connect()`, the warning from the Flow deck's image quality, and keeping the cap.

## Context

Without flow, the estimator has only the accelerometer, so the estimated
speed and position run away (*Estimate runaway*). After the Bench lift the
estimate reached -87 m with the drone on the floor; after the Hover landing,
in good light, it ran 0.65 m in 2 s. In flight the controller chases a
runaway speed, so the drone really moves. Nothing checks for it after
`connect()`. Hide-and-seek makes it likely: a child handles the landed drone,
and hiding spots are dark.

Checked in firmware 2026.08: `kalman.varPX`/`varPY` are the velocity
variances. The position variances (`varX`, `varY`) stay near their cap of
100 m² with the Flow deck alone, because nothing measures horizontal position
(`kalman_core.c` 144, 192, 630), so they say nothing about the flow. A reset
sets the velocity variance to 1e-4, which looks healthy (`kalman_core.c`
158-213).

## Options considered

- **What to check:** A, the velocity uncertainty (sees no flow, not wrong
  flow; comes from the estimator it judges); B, a landed drone's estimate
  against physics (motors off means still); the position variance (useless
  here); the Flow deck's quality and motion flag (rejected 2026-11-04).
- **The reset:** at `connect()` only (no new launch without restarting the
  program); inside `take_off` (blocks a tick for 5 s, hidden from the safety
  layer); a command request the safety layer judges.
- **Its slot (2026-11-07):** the movement slot (a reset and a take-off can't
  go out in one tick); its own slot; none.
- **After a reset (2026-11-07):** refuse a take-off until the reset is 5 s
  old, so a drone without flow can show it (the snapshot would carry the
  reset's time); also require a reset after every take-off; or no wait, with
  behaviors deciding when to reset.
- **In flight:** land on a high uncertainty, or only log it. Also: a 1 s hold
  before landing, and no check during the initial climb and final descent.

## Decision

A and B, and an estimate reset that behaviors request.

- **Velocity uncertainty:** the square root of the larger of `varPX` and
  `varPY`, in m/s, logged in the down-range log block (no new packets,
  backlog #47) and stamped in the snapshot like any value.
- **Estimate reset:** a command request a behavior makes when it wants a
  clean launch, such as a new round. Approved only when the drone status says
  not flying and the down range reads the floor; never in flight. It has no
  command slot: it's sent at the end of the tick, after the slots' commands.
  The adapter writes `kalman.resetEstimation` without waiting (the firmware
  clears it). It ignores a reset, logged once per streak, while it judges the
  drone may be flying (ADR-0039): just after a take-off, the drone status
  still says not flying and the down range still reads the floor. Before each
  reset, `connect()`'s too, the adapter logs the estimate, with a warning if
  it was implausible, so the reset doesn't erase the evidence (ADR-0020).
  Nothing waits after a reset, and the snapshot doesn't carry its time.
- **Take-off rule** (amended 2026-11-08): approved only with the down range
  reading the floor (`TOUCHDOWN_DOWN_RANGE`). With the velocity uncertainty
  under 0.03 m/s (flow is arriving), it also needs the estimated speed under
  0.05 m/s and the estimated position within 0.05 m of the reset point: flow
  that moves a still drone is wrong. With a higher uncertainty (no flow), the
  take-off goes ahead. `TOUCHDOWN_DOWN_RANGE` moves from the Crazyflie
  adapter's touchdown module to the drone interface module, so the safety
  layer doesn't import the adapter package.
- **The flow is checked at the top of the initial climb** (amended
  2026-11-08): the settle height also needs the velocity uncertainty under
  0.03 m/s. No settle by the cap (0.25 m), and the drone lands, as before.
- **In flight:** while the drone status says flying, a velocity uncertainty
  over 0.03 m/s, missing or stale fails the pre-check, and the failsafe lands.
  On the floor the pre-check ignores it: a failed pre-check ends the flight
  for good, so a drone landed at a dark hiding spot would end every round.
  It also ignores it during the initial climb (amended 2026-11-08): the
  snapshot says whether the initial climb is running, and the climb's own
  check covers that part.
- **No hold.** The uncertainty already grows with the time without flow; a
  1 s hold would add roughly 10-25 cm of chasing.
- **`connect()` doesn't wait for the estimate** (amended 2026-11-08): it
  writes `kalman.resetEstimation` like any reset, without cflib's
  `reset_estimator` and its 20 s time limit.
- **Low-light warning** (added 2026-11-08): at take-off, the adapter logs a
  warning when the Flow deck's image quality (`motion.squal`) is under 60:
  low light, so a risk of sideways drift during the take-off. Only a log
  line: it doesn't refuse.
- Placeholders to verify: 0.03 m/s, 0.05 m/s, 0.05 m, and the image quality
  of 60 (First flight 2: 22-42 on the dark floor, about 100 with a
  flashlight).

## Failure modes

- **Inputs:** a missing or stale uncertainty fails the pre-check in flight and
  refuses a take-off. Wrong flow keeps it low: B catches that on the floor
  once the estimate has moved, ADR-0048's level parts don't use the estimate,
  and above the bad-flow zone it goes unseen. A lost reset write leaves the
  old position, which B refuses unless it was already near the reset point.
- **Backups:** A fails with the estimator on wrong flow. B uses physics, and
  the down range, a separate sensor that works in the dark, confirms the
  floor. In flight there's no second velocity source.
- **Never:** an estimate reset in flight; a take-off with flow arriving and
  the estimate away from the reset point or moving; a hand-over to position
  hold above the initial climb without flow.
- **Always eventually:** in flight, missing flow lands the drone: at the cap
  during the initial climb, by the pre-check after it.

## Consequences

- **Risks I accept knowingly:**
  - Taking off without flow (amended 2026-11-08): the initial climb holds
    roll and pitch level with no position hold, so it drifts sideways, more
    in low light, where the settle height is higher (up to about 17 cm by
    the cap, ADR-0048). The low-light warning says so in the log.
  - The climb's flow check can pass without flow right after a reset: the
    reset sets the uncertainty to a healthy value, and how fast it grows
    without flow isn't measured (backlog #74).
  - The failsafe's landing approach is a `go_to`, so it holds position by the
    bad estimate until the final descent (backlog #58).
  - Wrong flow above the bad-flow zone isn't detected in flight.
  - The firmware resets the estimate itself past 100 m or 10 m/s, in flight
    too (`kalman_supervisor.c`). The adapter warns when the estimate jumps.
- A take-off requested in the same tick as a reset is judged on the estimate
  from before it, and is sent first, so the adapter then ignores the reset. A
  behavior takes off a tick or more after its reset.
- Hypothesis for ADR-0050's attitude log: the post-landing runaway is the
  estimator's flying model, used for 2 s after the motors stop
  (`supervisor.c` 56, `kalman_core.c` 506-540).
- **Field test:** hovers log the uncertainty in flight to set 0.03 m/s; then
  a new test program, Flow cut, sets `motion.disable` mid-hover
  (`flowdeck_v1v2.c` 157), expects the failsafe to land, and clears it in a
  `finally`. It's the second fault program (backlog #44).
- The mock adapter reports the uncertainty, with a fault that raises it.
- Tests: each take-off refusal, the floor-only reset, the reset ignored while
  the drone may be flying, the reset sent with the slots' commands, the
  pre-check ignoring the uncertainty on the floor, the down-range block
  fitting 26 bytes, and a land request during the final descent not
  restarting the landing approach.
- Built after ADR-0048's code, which changes the same files. The round start
  (backlog #5d) only uses the reset.
- Glossary: *Velocity uncertainty* and *Estimate reset* are new; *Safety
  pre-check* is reworded.

## Amendment, 2026-11-08

I want to fly in bad light whenever it isn't a safety problem, even with some
drift at take-off. As first written, this ADR refused to fly in dim light
(`connect()`'s 20 s settle, and the uncertainty in the take-off rule), which
isn't what I meant. In First flight 2 that refused four Hover attempts; two
flew only with a flashlight under the drone.

- Options: A, keep refusing without flow; B, take off without flow, with the
  settled speed at the top of the initial climb as the only flow check; C, B
  plus a low velocity uncertainty at the settle height. A runaway speed can
  pass under 0.15 m/s for 0.2 s by chance, so B can hand a drone without flow
  to position hold. **Chosen: C**, with the changes marked "amended
  2026-11-08" above.
- Kept: the cap. Without flow above it, position hold would chase a runaway
  estimate and really move the drone.
- Tests: a take-off with a high uncertainty approved; the moving-estimate
  refusal only with a low one; the settle height not found while the
  uncertainty is high, and the cap landing that follows; the pre-check
  ignoring the uncertainty during the initial climb; `connect()` resetting
  without waiting; the low-light warning logged under 60 and not over it.
  The mock adapter gets a dark floor: no flow below a height, set per
  scenario, so both a good climb and a cap landing run in continuous
  integration.
- Field test: take-offs without the flashlight, logging the uncertainty and
  image quality from the reset to the settle height (backlog #74).
