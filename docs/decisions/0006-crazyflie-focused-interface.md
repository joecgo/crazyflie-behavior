# 0006: Drone interface is Crazyflie-focused, with generic vocabulary

- **Status:** Accepted
- **Date:** 2026-10-18
- **Origin:** My idea: don't design for what isn't used yet or can't be tested.

## Context

[ADR-0002](0002-behavior-depends-only-on-drone-interface.md) left open how
drone-agnostic the drone interface should be. The Crazyflie is the only drone
planned, and no other platform is available to test against. A generic
interface would have to guess at the needs of hardware that isn't chosen.

## Options considered

### A. Crazyflie-shaped
The interface mirrors the Crazyflie's capabilities and vocabulary.
- **Pros:** simplest, and everything in it can be tested.
- **Cons:** Crazyflie concepts leak into behaviors, so supporting another drone
  later means touching every behavior.

### B. Fully generic
Capability queries, optional sensors, a frame and unit contract for any drone.
- **Pros:** portable on paper.
- **Cons:** designed for hardware that can't be tested. Most of it would be
  speculative and likely wrong.

### C. Generic core with Crazyflie-specific extensions
- **Pros:** a middle path.
- **Cons:** still requires guessing where the generic/specific line falls,
  without a second drone to check against.

### D. Crazyflie-focused, with generic vocabulary
Design for the Crazyflie only, but name things generically wherever a common
term exists across drones. Crazyflie-only concepts stay inside the Crazyflie
adapter.

## Decision

Option D. I don't design for things that aren't used yet or can't be tested.
The interface targets the Crazyflie. I don't expect to bring this project to
other hardware. If that ever happens, it will likely be branched into a separate
project, keeping this one's design intact, rather than generalizing this one. Where most drones share a term, use it.
Otherwise use the Crazyflie-specific term.

Vocabulary rule:
- **Generic, visible to behaviors:** range readings, position estimate, arm,
  take off, land, battery voltage.
- **Crazyflie-only, inside the Crazyflie adapter:** decks (Flow, Multi-ranger),
  log blocks, TOC, CRTP, URIs, cflib units.

## Consequences

- Leakage is the accepted risk: some interface *shapes* will be
  Crazyflie-shaped (e.g. five fixed range directions, the Crazyflie arming
  flow). Since other hardware isn't expected, and would likely become a
  separate project, the cost of this risk is low.
- The mock and simulator are the interface's second implementation from day
  one. They catch accidental coupling to cflib, which is generality that is
  used and tested.
- Portability checkpoints (CLAUDE.md) no longer stop every Crazyflie-specific
  choice. They apply this vocabulary rule and only escalate when a
  Crazyflie-only concept would reach behavior code.
