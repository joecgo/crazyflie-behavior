# 0036: Game logic is a state machine per game; a behavior's tick reports an outcome

- **Status:** Accepted. Amends [ADR-0026](0026-tick-loop-calls-one-tick-step.md): the tick step reports an outcome, not only "done".
- **Date:** 2026-11-01
- **Origin:** Mixed. A state machine now and a behavior tree later: mine. `Behavior` as the shared base instead of a new brain class, and the outcome: AI recommendations accepted.

## Context

The first game behavior needs a structure (backlog #6). Hide-and-seek has a
few clear states (waiting, hiding flight, hidden, found). My second code
review also found that `Behavior.tick` reports only done or not done, so a
failed hover test, or a flight the failsafe ended, exits with code 0 like a
pass.

## Options considered

- **A. A state machine per game:** small and readable for a few states, but
  states can't be shared across games without copying.
- **B. A behavior tree now:** shares subtrees and stacks interrupts, but is
  more framework than one small game needs.
- **C. A new brain class** above behaviors, holding either.

## Decision

Option A now; a behavior tree later, when an agent is complex enough: states
shared across games (fly home, land, react), or game-level interrupts piling
up. That move gets its own ADR.

- **No brain class.** `Behavior` already plays `UBrainComponent`'s role: a
  state machine is a `Behavior`, and a later behavior tree is one too.
- **`tick` returns an outcome:** running, succeeded or failed, like UE's
  `EBTNodeResult`. A program exits with a nonzero code when a test fails or
  the failsafe ends the flight, unless the program tests that failsafe: then
  the program defines its own pass (amended 2026-11-03; the Failsafe low and
  Failsafe high tests, [ADR-0041](0041-failsafe-tests-inject-a-fault-into-the-pre-check.md)).
- **Robotics rules for states:** every state that waits on the world has a
  time limit and a failure path; a transition on noisy readings needs a hold
  time (backlog #4); interrupts for safety stay in the safety layer beneath
  behaviors, not in game states.

## Consequences

- The tick step and the tick loop pass the outcome up to the program, which
  picks the exit code. The hover test and its tests change to match.
- **Still open:** how states are written (an enum and `match`, like the hover
  test, or a class per state with enter, tick and exit). Decided with the
  first game behavior.
- Glossary: *Outcome* added; *Behavior*'s UE analogy changed. Backlog #6 is
  closed.
