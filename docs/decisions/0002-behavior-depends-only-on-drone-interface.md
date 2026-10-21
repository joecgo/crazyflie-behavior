# 0002: Behavior depends only on the drone interface

- **Status:** Accepted
- **Date:** 2026-10-17
- **Origin:** Carried over from the project's original plan (the handoff document); the tools exemption was an AI recommendation accepted.

## Context

The drone hasn't been bought yet, but behavior work needs to start now. Even
once hardware arrives, real flights are slow to set up, limited to about 7
minutes per battery, and risky to the drone. Behavior logic has to be
developed and tested mostly without a real drone, then run unchanged on one.

## Options considered

### A. Behavior calls cflib directly
Behaviors use `MotionCommander`, `LogConfig` and so on themselves.
- **Pros:** least code, and matches the cflib examples.
- **Cons:** nothing runs without hardware, behaviors can't be unit tested, and
  cflib's threading and blocking quirks leak into every behavior.

### B. Behavior depends on a drone interface (ports and adapters)
Behaviors talk only to an abstract drone interface. Adapters implement it: a
mock now, a simulator later, and a Crazyflie adapter wrapping cflib.
- **Pros:** behaviors run and are tested with no hardware, backends can be
  swapped, and cflib details are confined to one place.
- **Cons:** an extra layer to design and maintain. The interface can hide
  real-world behavior (latency, drift) if the mock is too idealized.

### C. Behavior talks to a message bus (ROS 2 style)
Behaviors publish commands and subscribe to topics, and a bridge talks to cflib.
- **Pros:** industry-standard in robotics, and multi-process friendly.
- **Cons:** heavy infrastructure for one drone on Windows (ROS 2 means WSL2),
  and a large learning curve on top of Python and robotics.

## Decision

Option B. The deciding factor is developing without hardware: behaviors must be
fully runnable and testable before the drone exists. Keeping cflib behind one
adapter also means its quirks are solved once, not in every behavior. A message
bus (C) is overkill at this scale, and a well-designed interface leaves the door
open to wrapping one later.

**The rule:** no module outside the Crazyflie adapter imports `cflib`.

**One exemption: `tools/`.** Hardware diagnostic scripts (radio scans, raw
telemetry dumps) may use cflib directly. When the hardware is misbehaving, the
best check bypasses the project's own code. Tools are never imported by
project code, and the fitness function enforces both halves: cflib only in the
Crazyflie adapter and `tools/`, and nothing in `src/` imports `tools/`.

## Consequences

- The design of the drone interface is now the most important decision in the
  project, and gets its own ADRs (timing model, control modes, state and sensors).
- The mock or simulator has to be realistic enough (noise, drift, latency) that
  behaviors proven against it still work in the air.
- The rule is **enforced by an automated architecture test** (a fitness
  function) that fails if any module outside the Crazyflie adapter or `tools/`
  imports `cflib`.
  It's added with the first code and runs in continuous integration.
- **Open question:** how drone-agnostic should the interface be? Crazyflie-shaped
  (easy, honest) or generic across drones (more portable, more design work)?
  To be settled in a later ADR.
- Glossary terms: *Drone interface*, *Adapter*, *Crazyflie adapter*, *Mock adapter*.
