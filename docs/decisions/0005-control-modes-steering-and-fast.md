# 0005: Two control modes: steering mode and fast mode

- **Status:** Accepted
- **Date:** 2026-10-18

## Context

Behaviors need to command motion. cflib offers velocity streaming (the PC runs
the control loop every tick) and high-level `go_to` trajectories (the drone
plans and flies the move itself). Reactive behaviors like obstacle avoidance
fit velocity control, but velocity puts the radio link inside the control loop,
so latency, drift and noise matter more, especially at speed. Some situations
(transits, evasion, known static spaces) call for fast, smooth, accurate moves
instead. Comparing the two approaches with real data is also a goal in itself.

## Options considered

### A. Velocity only
- **Pros:** reacts every tick, natural for steering behaviors and avoidance.
- **Cons:** the PC is the path follower, so speed and accuracy are limited by
  latency. Stalls or link hiccups become flight problems.

### B. Position (`go_to`) only
- **Pros:** smooth trajectories flown onboard, so latency is not in the loop.
- **Cons:** reacting mid-move means replacing commands, and overlapping `go_to`s
  can produce erratic paths.

### C. Carrot chasing (frequent short `go_to`s)
- **Pros:** fails safe on a stall, one mode for everything.
- **Cons:** likely choppy, and fights cflib's warning against overlapping `go_to`s.

### D. Two modes: velocity by default, position for fast moves
- **Pros:** each mode used where it is strongest. Enables direct velocity vs
  `go_to` comparison experiments.
- **Cons:** mode switching and interruptions must be designed carefully.

## Decision

Option D, with two named control modes:

- **Steering mode (default).** Velocity control with obstacle-avoidance
  steering. Slow and controlled. Avoidance reacts to relative range data, which
  doesn't drift.
- **Fast mode.** Position control (`go_to`) with avoidance steering disabled,
  for getting somewhere quickly: transits, evasion, known static spaces, and
  comparison tests against steering mode. Moving fast and accurately is exactly
  when the onboard trajectory beats a PC-side loop.

Rules:

- **The safety layer stays active in every mode**, including fast mode, and can
  interrupt any move.
- **Behaviors request fast mode; the safety layer approves it**, based on
  visibility, how tight the space is, current latency and battery remaining.
- **Each mode has a speed envelope** (maximum speed and acceleration). The
  safety layer may tighten a mode's envelope in the moment but never widen it.
- **On interruption, the response depends on severity.** Usually blend back
  into steering mode. For serious faults, stop.

Carrot chasing (C) was rejected as likely too choppy.

## Consequences

- The drone interface exposes both velocity and position commands, plus mode
  requests that can be refused.
- Steering mode needs arrival and acceleration limiting in project code (the
  firmware won't shape velocity commands).
- The safety layer needs severity levels and a defined response for each.
- Fast-mode approval criteria need measurable definitions.
- **Deferred:** an override flag that skips the fast-mode approval checks (never
  the safety layer itself), only if a real need appears, and then limited to
  tests and simulation.
- Glossary: *Control mode*, *Steering mode* and *Speed envelope* proposed;
  *Fast mode* moves to Decided.
