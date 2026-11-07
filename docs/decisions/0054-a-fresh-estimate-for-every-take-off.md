# 0054: Behaviors request estimate resets on the floor; the velocity uncertainty is checked at take-off and in flight

- **Status:** Accepted. Amends [ADR-0030](0030-minimal-safety-layer-for-first-flight.md): the safety pre-check also checks the velocity uncertainty while flying, and the take-off rule checks the estimate. Amends [ADR-0025](0025-safety-pre-check-and-command-slots.md): the estimate reset request has no command slot. Closes backlog #48. Amended 2026-11-07, before its code: behaviors request a reset when they want a clean launch, with no command slot and no wait after it; the reset command is built now, not with the round start; the adapter ignores a reset while the drone may be flying; the take-off rule's floor threshold moves to the drone interface module.
- **Date:** 2026-11-06
- **Origin:** Mixed. The velocity uncertainty and the landed-drone check, a reset command, landing on a high uncertainty in flight, and no hold or bad-flow-zone exemption: AI recommendations accepted. Proving it by cutting the flow in software, in its own test program: mine. On 2026-11-07, all mine: building the reset now, for a clean launch without restarting the program; behaviors deciding when to reset; no slot (over the AI's movement slot); no wait after a reset (over the AI's 5 s wait in the take-off rule). The adapter ignoring a reset while the drone may be flying, and moving the floor threshold to the drone interface module: AI recommendations accepted.

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
- **Take-off rule:** approved only with the velocity uncertainty under
  0.03 m/s, the estimated speed under 0.05 m/s, the estimated position within
  0.05 m of the reset point, and the down range reading the floor
  (`TOUCHDOWN_DOWN_RANGE`). That constant moves from the Crazyflie adapter's
  touchdown module to the drone interface module, so the safety layer doesn't
  import the adapter package. The first launch is also checked by
  `connect()`'s own settle: cflib waits at least 5 s for the velocity variances to settle,
  and a drone without flow doesn't settle (Bench run 3).
- **In flight:** while the drone status says flying, a velocity uncertainty
  over 0.03 m/s, missing or stale fails the pre-check, and the failsafe lands.
  On the floor the pre-check ignores it: a failed pre-check ends the flight
  for good, so a drone landed at a dark hiding spot would end every round.
- **No hold, no exemption.** The uncertainty already grows with the time
  without flow; a 1 s hold would add roughly 10-25 cm of chasing. Exempting
  the initial climb and final descent would need the adapter's landing phase
  in the snapshot and buys nothing (ADR-0049).
- Placeholders to verify: 0.03 m/s, 0.05 m/s, 0.05 m.

## Failure modes

- **Inputs:** a missing or stale uncertainty fails the pre-check in flight and
  refuses a take-off. Wrong flow keeps it low: B catches that on the floor
  once the estimate has moved, ADR-0048's level parts don't use the estimate,
  and above the bad-flow zone it goes unseen. A lost reset write leaves the
  old position, which B refuses unless it was already near the reset point.
- **Backups:** A fails with the estimator on wrong flow. B uses physics, and
  the down range, a separate sensor that works in the dark, confirms the
  floor. In flight there's no second velocity source.
- **Never:** an estimate reset in flight; a take-off with the estimate away
  from the reset point, moving, or with a high uncertainty.
- **Always eventually:** in flight, missing flow lands the drone.

## Consequences

- **Risks I accept knowingly:**
  - A launch right after a reset doesn't check the flow: the reset makes
    every take-off check pass until flow proves otherwise. From a spot darker
    than the first launch's (a hiding spot, a darker room), the drone takes
    off without flow, and the in-flight check lands it a few seconds later. I'll
    fix it if it shows up (backlog #60).
  - The failsafe's landing approach is a `go_to`, so it holds position by the
    bad estimate until the final descent (backlog #58).
  - Wrong flow above the bad-flow zone isn't detected in flight.
  - The firmware resets the estimate itself past 100 m or 10 m/s, in flight
    too (`kalman_supervisor.c`). The adapter warns when the estimate jumps.
- A take-off requested in the same tick as a reset is judged on the estimate
  from before it, and is sent first, so the adapter then ignores the reset. A
  behavior takes off a tick or more after its reset.
- Without the flashlight in dim light, `connect()`'s settle refuses to fly:
  the safe direction.
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
