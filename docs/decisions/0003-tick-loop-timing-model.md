# 0003: Behaviors run in a fixed-rate tick loop

- **Status:** Accepted
- **Date:** 2026-10-18
- **Origin:** AI recommendation accepted.

## Context

Behavior code and the drone have to take turns: the behavior reads state,
decides, and commands. Telemetry arrives asynchronously on cflib's background
thread, commands take time to carry out, and the radio link adds latency. The
timing model decides whether behaviors can react mid-move, where safety checks
run, how telemetry reaches behavior code safely, and whether tests can run
faster than real time.

## Options considered

### A. Tick loop
A loop runs at a fixed rate. Each tick reads the latest state, runs the
behavior, and sends commands that return immediately.
- **Pros:** reacts mid-move. Failsafes and the geofence check every tick.
  Filtering and staleness checks have a natural home. With a controllable clock,
  tests and the simulator run faster than real time and reproduce exactly.
  Matches game-AI practice (UE5 `Tick` driving a Behavior Tree).
- **Cons:** every command must be non-blocking. Choosing a tick rate is a
  trade-off. Telemetry from the background thread must be handed over safely.

### B. Blocking calls
Each command waits until finished (cflib's `PositionHlCommander` style).
- **Pros:** simplest code, reads like a script.
- **Cons:** blind while moving, so no mid-move reaction to obstacles. Safety
  checks are awkward. Tests run in real time.

### C. async/await (coroutines)
Commands are awaited while other tasks keep running.
- **Pros:** sequential-looking code that can still react.
- **Cons:** adds `asyncio` on top of learning Python. cflib is thread-based, not
  async, so a bridge is needed. Deterministic testing is harder.

## Decision

Option A. A tick loop lets behaviors react every cycle, gives safety layers a
guaranteed point to check and override, and makes the system testable with a
controlled clock. It's also the model I already use for game AI, so the
behavior design can draw directly on that experience.

## Consequences

- **All drone-interface commands are non-blocking.** Nothing a behavior calls
  may sleep or wait for a move to finish.
- Telemetry from cflib callbacks lands in a **blackboard**, and each tick reads
  from it, so behaviors never touch cflib threads.
- Known risks, accepted knowingly:
  - **Tick overrun:** a slow tick delays the next one. The loop must detect and
    report overruns, not silently drift.
  - **Timer jitter on Windows:** `time.sleep` can be off by several
    milliseconds, so the loop must use measured `dt`, not an assumed one.
  - **Thread safety:** the blackboard is written by cflib's thread and read by
    the tick, so the handover needs a deliberate design.
  - **High-level commander overlap:** issuing a new `go_to` every tick causes
    erratic paths (see `docs/cflib-primer.md`). Commands must be issued on
    change, not every tick, or use velocity streaming.
- **Follow-up decisions:**
  - Tick rate.
  - Clock abstraction (real vs simulated time).
  - Blackboard design: one snapshot per tick? Is behavior memory separate from
    sensed state?
  - Control modes (position, velocity or both).
- Glossary: *Tick* and *Blackboard* move from Proposed to Decided.
