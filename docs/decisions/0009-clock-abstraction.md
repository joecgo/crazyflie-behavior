# 0009: Injected clock; behaviors receive time in the snapshot

- **Status:** Accepted
- **Date:** 2026-10-20
- **Origin:** AI recommendation accepted.

## Context

The tick loop, telemetry buffer and safety layer all need the time: tick
deadlines, arrival timestamps, staleness checks. If they read the computer's
real clock, tests run at real speed, timing varies run to run, and simulated
scenarios can't run faster than real time in continuous integration.

## Options considered

### A. Read the real clock directly; patch it in tests
- **Pros:** simplest to write.
- **Cons:** a hidden dependency. Every test must know what to patch, and
  patching is fragile with background threads.

### B. Injected `Clock` interface
`now()` and `sleep_until(deadline)`, with a `RealClock` (monotonic clock,
deadline scheduling) and a `SimClock` (moves only when told to; sleeping jumps
time forward instantly). Components receive the clock they should use.
- **Pros:** fast, repeatable tests; simulation faster than real time.
- **Cons:** the clock must be passed to everything that needs time.

### C. B, plus behaviors don't read the clock directly
The tick loop puts the current time and `dt` into the snapshot, and behaviors
receive time that way, like `Tick(DeltaTime)`. Only the tick loop, adapters and
safety layer hold the clock.
- **Pros:** behaviors stay pure: *(snapshot, blackboard) → requests*. Behavior
  tests need no clock at all. Consistent with ADR-0007.
- **Cons:** time is frozen within a tick. Behaviors can't use sleeps or timer
  callbacks; waits become tick-based state (store a start time in the
  blackboard, compare each tick).

## Decision

Option C. It's essentially Unreal's world-time model: time is passed into
Tick, world time is constant within a frame, and gameplay runs on game time
rather than the OS clock, which is what makes pause, time dilation and
fixed-step tests possible. Timer callbacks are deliberately left out of
behaviors, because a callback firing between ticks would act on data outside
the snapshot.

## Consequences

- `Clock` interface with `RealClock` and `SimClock` implementations.
- Snapshots carry the tick's time and `dt`.
- Fitness function: behavior modules never import `time` (or other clock
  sources).
- With `SimClock`, the simulator writes telemetry as the clock advances on the
  same thread, so simulated flights are fully deterministic: the same inputs
  give the same flight every run.
- `RealClock` is where the tick timing strategy (deadline scheduling, sleep
  then spin) is implemented. See the backlog.
