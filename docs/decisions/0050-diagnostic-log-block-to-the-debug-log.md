# 0050: A diagnostic log block streams attitude, motor power and flow quality to the debug log only

- **Status:** Accepted. Amended by [ADR-0053](0053-buzzer-commands-and-a-chirp-hover-test.md) (2026-11-06): the block also carries the battery voltage (`pm.vbatMV`), 25 of 26 bytes. Extended by [ADR-0063](0063-take-off-and-controller-log-blocks.md) (2026-11-12): two more debug-log blocks.
- **Date:** 2026-11-05
- **Origin:** AI recommendation accepted (the values, and the debug log only).

## Context

In First flight 1's Hover test, the drone swung in a small circle the whole
hover: 0.85 Hz, about 1.2 cm, in x and y
([test log](../field-testing/field-tests/2026-11-04-first-flight-1-hover.md)).
The logs can't say why. They have the position and velocity estimates but no
attitude (yaw would show an x-y coupling), no motor power (a weak motor or a
damaged propeller works harder), and no Flow deck quality (surface and light).

The values exist in firmware 2026.08 ([ADR-0047](0047-pinned-firmware-release-warn-on-mismatch.md)):
`stateEstimate.roll`, `pitch`, `yaw` (floats, degrees; pitch has the legacy
inverted sign), `motor.m1`-`m4` (uint16, 0-65535), `motion.squal` (uint8,
surface features) and `motion.shutter` (uint16, the Flow deck's shutter time,
which goes up in low light). That's 23 bytes, which fits one log block (26).

## Options considered

- **A. Debug log only.** The Crazyflie adapter writes each sample as a debug
  line. Nothing reaches the snapshot, so motor power and flow quality,
  Crazyflie-only concepts, stay in the adapter
  ([ADR-0006](0006-crazyflie-focused-interface.md)). Behaviors can't use them.
- **B. Into the snapshot.** Behaviors and the simulator could use them, but
  it changes the drone interface, the mock adapter and the simulator, and
  motor power and flow quality would reach behavior code.

## Decision

Option A. A fourth log block, the diagnostic block, at **100 ms** (10 Hz),
started with the battery and range blocks, on every connect. Each sample is
one debug line from the adapter, with the drone time. Connecting doesn't wait
for it (it isn't telemetry, [ADR-0031](0031-connect-waits-for-first-telemetry.md)),
and a missing variable fails the connect like any other block, on the floor.

## Consequences

- About 10 more packets a second from the drone, on top of about 110
  ([ADR-0023](0023-tick-rate-20-hz.md)). Backlog #47 is the
  drone's queue of incoming packets, which this doesn't add to; unmeasured.
- 10 Hz shows a swing up to 5 Hz and each motor's average power. It can't
  show propeller vibration (hundreds of Hz).
- The debug log grows by 10 lines a second.
- Behaviors that later need attitude get a new decision (option B, for
  attitude alone).
- Tests: the block fits 26 bytes, its period is one the firmware accepts, it
  starts on connect, connecting doesn't wait for it, and a sample becomes one
  debug line.
- Glossary: adds *Diagnostic block*.
