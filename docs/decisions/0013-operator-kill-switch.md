# 0013: The operator's kill switch bypasses the safety layer

- **Status:** Accepted. Amends decision 1 of [ADR-0008](0008-drone-interface.md).
- **Date:** 2026-10-20
- **Origin:** Mixed. The need for a manual override and making it an exception: my call. The design: the AI's.

## Context

ADR-0008 makes the safety layer the only code that commands the drone. But
the safety layer, the tick loop or a behavior can fail: hang, crash, or make a
wrong call (e.g. holding a hover while touchdown can't be confirmed, ADR-0012).
When I can see that it's safe, I need a way to stop the motors that doesn't
depend on any of that code working.

## Options considered

### A. Route the kill through the safety layer as its highest priority
- **Pros:** keeps ADR-0008's rule intact.
- **Cons:** if the safety layer or tick loop hangs, the kill hangs with it.
  Exactly when it's needed most.

### B. An explicit exception: the kill switch calls the drone directly
- **Pros:** works no matter what state the rest of the program is in.
- **Cons:** a second path to the drone, which must stay narrow.

## Decision

Option B. The kill switch is a command I execute, like a cheat command, to
manually stop everything. It deliberately bypasses the normal rules.

The exception is as narrow as possible:
- **Only one command bypasses the safety layer: cutting the motors**
  (`emergency_stop()`). Any other operator command (e.g. "land now", "hover")
  goes through the safety layer like everything else.
- **It runs on its own thread**, so it works even when the tick loop is stuck.

## Consequences

- ADR-0008's rule becomes: only the safety layer commands the drone, except
  the kill switch's emergency stop.
- An accidental kill drops the drone. Accepted: an e-stop must be quick to
  trigger, and a Crazyflie is light.
- A fitness function should pin the exception down: only the kill switch module
  may call the drone interface besides the safety layer and tick loop.
- Open (backlog, operator controls): how the command is executed, whether the kill
  latches (refusing further flight until restarted), a dead-man mode for first
  flights, and a `tools/` emergency-stop script for after the program exits.
