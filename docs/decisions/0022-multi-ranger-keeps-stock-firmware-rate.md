# 0022: The Multi-ranger keeps the stock firmware's 10 Hz

- **Status:** Accepted
- **Date:** 2026-10-28
- **Origin:** Mixed. Keeping the stock rate: AI recommendation accepted. No follow-up item to revisit it: my call.

## Context

Checking sensor rates for the tick rate (backlog #2) showed that the stock
firmware reads the Multi-ranger every 100 ms (10 Hz), with the sensor driver's
default timing. The sensor (ST VL53L1x) is rated up to about 50 Hz, and the
Flow deck's down sensor, the same chip, runs at 40 Hz. So 10 Hz is a firmware
choice, not a hardware limit.

## Options considered

- **A. Keep the stock 10 Hz:** no firmware of our own; the driver's default
  timing keeps its range and noise. Readings are 100 ms apart.
- **B. Custom firmware, about 30-40 Hz:** fresher obstacle readings, but a
  shorter timing budget collects less light (less range, more noise), and we
  build, flash and maintain our own firmware.

## Decision

Option A. Hide-and-seek flies slowly through a mapped, empty room, where
10 Hz is enough: at 0.3 m/s the drone moves 3 cm between readings. Stock
firmware keeps the project on what Bitcraze supports.

No backlog item to revisit this. If a later need (fast mode, or detecting
someone entering the play area) wants faster readings, that becomes a new ADR
that supersedes this one.

## Consequences

- The Multi-ranger's readings are at most 10 Hz. A log period below 100 ms for
  the `range.*` variables only repeats readings; its period is set with the
  tick rate (backlog #2).
- A Multi-ranger reading can be up to 100 ms old before latency is added.
  Behaviors and the safety layer must allow for that in stopping distances.
- Risk accepted knowingly: with no backlog item, nothing reminds us to check
  this rate when fast mode's approval criteria (backlog #10) are written.
- No glossary change.
