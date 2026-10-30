# 0031: connect() returns only once every telemetry value has arrived

- **Status:** Accepted
- **Date:** 2026-10-30
- **Origin:** AI recommendation accepted (from the cloud session's code review, and again on the laptop).

## Context

The Crazyflie adapter's `connect()` returned as soon as its log blocks
started, before any value had arrived (backlog #32). The safety pre-check
(ADR-0030) counts a missing value as a failure, and a failure ends the flight,
so on the real drone a program would stop at its first tick without flying:
safe, but useless. The mock adapter hid this, because it writes every value
as it connects.

## Options considered

- **A. `connect()` waits for the first value of every stream,** with a time
  limit like the other connect steps (ADR-0029).
- **B. The pre-check lets behaviors wait while values are missing and the
  drone is on the floor.** Knowing it's on the floor needs the drone status,
  one of the values that may be missing.
- **C. The tick step waits for a complete snapshot** before its first
  pre-check: the same wait, in every program instead of in one place.

## Decision

Option A. When `connect()` returns, every telemetry value has arrived at
least once, on every adapter: a promise in the drone interface, kept by the
mock adapter already. The pre-check stays strict.

- "Arrived" means the telemetry buffer has a value, even "invalid": without a
  Multi-ranger, the adapter writes "invalid" for its five directions itself.
- **Time limit: 3 s,** a placeholder to measure at the bench with the other
  connect limits. The battery streams once a second, the slowest stream.
- Past the limit, `connect()` closes the link and raises `TimeoutError`,
  naming the values still missing (ADR-0020: refusing to start).

## Failure modes

- **Inputs:** a stream that never starts is named in the error. A stream that
  starts and later stops is a different failure: its value gets older, and
  the pre-check's staleness limits catch it on every tick.
- **Backups:** none; the wait only checks the telemetry buffer.
- **Never:** a flight starts with a value missing; `connect()` waits forever.
- **Always eventually:** connected with every value present, or refused with
  a message, within the time limits.

## Consequences

- The wait checks the telemetry buffer every 0.1 s, on the main thread. Unlike
  cflib's waits (ADR-0029), a plain sleep is interrupted by Ctrl+C at once, so
  it needs no helper thread (shown by a test with a planted bug: one long sleep
  instead of short ones).
- `TelemetryBuffer.missing_values()` names what hasn't arrived yet. Each
  connect starts a fresh telemetry buffer, so values from an earlier
  connection can't satisfy the wait.
- Tests check the promise on both adapters, and the Crazyflie adapter's tests
  deliver telemetry late, or never, through a fake cflib.
- Backlog #32 is closed.
