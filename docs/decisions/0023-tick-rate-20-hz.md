# 0023: The tick loop runs at 20 Hz, with telemetry periods matched to their sources

- **Status:** Accepted
- **Date:** 2026-10-28
- **Origin:** AI recommendation accepted, over my first preference for 30-60 updates per second.

## Context

The tick loop ([ADR-0003](0003-tick-loop-timing-model.md)) needs a rate, and
each log block needs a period. My priority is responsiveness, especially to
safety issues. Checked in the firmware source (2026-10-27/28): the position
estimate is computed at 100 Hz, the down range is read every 25 ms (40 Hz),
the Multi-ranger every 100 ms (10 Hz, kept by
[ADR-0022](0022-multi-ranger-keeps-stock-firmware-rate.md)), and log periods
go in 10 ms steps from 10 to 2540 ms.

## Options considered

- **A. 10 Hz:** light on the radio, but up to 100 ms of waiting for the tick.
- **B. 20 Hz:** a fresh position estimate every tick and a down range on about
  every other one; up to 50 ms of waiting.
- **C. 50 Hz:** up to 20 ms of waiting, but most ticks repeat the same range
  readings, the radio carries 2.5 times the commands, and Python on Windows
  has 20 ms for each tick, so jitter and garbage collection matter more.

## Decision

Option B. The 100 Hz estimate is the firmware's own control loop, which runs
on the drone and keeps it stable between ticks; the tick is the decision rate.
Waiting for the tick is only part of the reaction time (the radio and the
drone's physical response add the rest, unmeasured), and at hide-and-seek
speeds (0.3 m/s) the drone moves 1.5 cm per tick. A lighter radio load also
keeps room for the emergency stop, since a full cflib queue can block a send
for up to 2 s. The rate is one setting, so measurements can change it cheaply.

Log periods: **state block 20 ms, down range 20 ms, Multi-ranger 100 ms,
battery 1000 ms.** The state block and the down range stream faster than the
tick, so the latest value in a snapshot is at most about 20 ms old. The
Multi-ranger matches its readings; anything faster only repeats them.

## Consequences

- About 130 packets a second: 50 state, 50 down range, 10 Multi-ranger,
  1 battery, and 20 setpoints. The radio's real capacity is unmeasured.
- The tick loop implementation uses 20 Hz (backlog #3 decides how it keeps
  time). Behaviors still use the measured `dt`, never an assumed 50 ms.
- Revisit the rate once the full reaction time (sensor to tick to command to
  movement), radio load and tick jitter are measured on the real drone.
- A test checks every log period is one the firmware accepts, and that the
  Multi-ranger isn't logged faster than it reads.
- No glossary change.
