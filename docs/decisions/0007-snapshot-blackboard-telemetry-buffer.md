# 0007: Telemetry buffer, per-tick snapshot, and a separate blackboard

- **Status:** Accepted
- **Date:** 2026-10-19

## Context

[ADR-0003](0003-tick-loop-timing-model.md) put telemetry into a "blackboard"
read by the tick loop, but left its design open. Telemetry arrives on cflib's
background thread at its own rates, while behaviors run on the tick. Behaviors
also need memory that persists across ticks. Data age must always be tracked,
because even matched rates don't guarantee fresh data every tick.

## Options considered

### How telemetry reaches behaviors
- **A. Live store:** behaviors read shared values as they change. Simple, but a
  tick can see an inconsistent mix of old and new values, and locking spreads
  through behavior code.
- **B. Snapshot per tick:** at the start of each tick, copy the latest values
  into a read-only snapshot that every behavior in that tick uses.

### How data age is tracked
- **A. Arrival time (PC clock) only:** simple, enough for staleness checks, but
  ignores time in flight.
- **B. Drone timestamp only:** true measurement time, but in the drone's clock,
  so it needs clock-offset estimation.
- **C. Store both, use arrival time for staleness:** drone timestamps kept for
  latency measurement, recording and replay. Prediction deferred.

### Behavior memory
- **A. One store** for sensed state and memory (like a UE Blackboard).
  Conflicts with a read-only snapshot and muddies tests and replays.
- **B. Separate stores:** read-only sensed state, plus writable memory owned by
  behaviors.

### Naming
- **X:** keep "blackboard" for the store callbacks write into (as ADR-0003 used it).
- **Y:** match UE5: "blackboard" means behavior memory.

## Decision

- **Snapshot per tick (B).** Consistent within a tick, with thread safety
  confined to one handoff, and easy to build by hand in tests and to replay.
- **Both timestamps, arrival time for staleness (C).** Recording uses the
  drone timestamps from day one. Prediction is added only if real flights show
  it's needed.
- **Separate memory (B).** Each tick is *(snapshot, blackboard) → (commands,
  updated blackboard)*.
- **Naming Y.** Matches how I read game-AI code, and what a game-AI reviewer
  expects:
  - **Telemetry buffer:** thread-safe latest values, written in the background.
  - **Snapshot:** read-only per-tick copy of the telemetry buffer.
  - **Blackboard:** behavior memory.

This refines ADR-0003's use of "blackboard", which there meant the telemetry
buffer.

## Consequences

- Thread safety lives in one place: the copy from telemetry buffer to snapshot
  at tick start.
- Behaviors see data up to one tick old, plus link latency. Staleness checks
  use arrival time.
- Behavior tests construct a snapshot and a blackboard directly, with no drone,
  mock or threads needed.
- Replay tests feed recorded snapshots through behaviors deterministically.
- Sensor filtering needs history across ticks. Where that lives (blackboard,
  or a perception step between snapshot and behaviors) is decided with the
  sensor pipeline.
- Frozen dataclasses (backlog) now has a natural first candidate: the snapshot.
