# 0044: The Bench is flown with the propellers on

- **Status:** Accepted
- **Date:** 2026-11-03
- **Origin:** My decision, with the AI pushing back on the risk.

## Context

The Bench field test connects to the drone, ticks and logs every snapshot, and
never commands it ([ADR-0028](0028-programs-bench-first-plain-logging.md)). It
was planned with the propellers off, so that nothing could hurt anyone if the
motors spun. Taking the propellers off and putting them back is too much work
for a test that only reads telemetry.

## Options considered

- **A. Propellers off,** as the field-testing README said.
- **B. Propellers on.** No setup work, but the drone is armed and able to fly
  while it sits on the bench.

## Decision

B. The AI pushed back: stock Crazyflie 2.1+ firmware arms itself once its
pre-flight checks pass, so the drone is armed with its propellers on
([ADR-0037](0037-disconnect-does-not-disarm.md)). I accept that, for these
reasons:

- **The bench program sends the drone no command** through the drone interface
  (ADR-0028). Two things still reach it: connecting resets the position
  estimate, and closing the link on a drone known to be on the floor makes
  cflib send a zero-thrust setpoint first (ADR-0038). Zero thrust asks for no
  motor speed, but like the next point it holds only if the idle thrust is 0.
- **A stock 2.1+ drone's idle thrust is 0** (ADR-0037, checked in the firmware
  source on 2026-11-02, not yet on hardware): armed alone doesn't spin the
  motors.

## Failure modes

- **Inputs:** if the idle thrust isn't 0 on this firmware, an armed drone's
  propellers spin on the bench. Nothing in our code would stop it: the Bench's
  connect log shows whether the drone arms itself (ADR-0037), not its idle thrust.
- **Backups:** none for that case: nothing in our code stops it.
- **Never:** the bench program sends a command to the drone through the drone interface.
- **Always eventually:** nothing new.

## Consequences

- **Risk I accept knowingly:** a drone that arms itself, with its propellers
  on, on the bench.
- The field-testing README's Bench row, the bench program's docstring and the
  other comments that said "propellers off" for the Bench change to say the
  propellers are on.
