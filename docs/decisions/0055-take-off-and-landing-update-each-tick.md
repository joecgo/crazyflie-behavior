# 0055: Take-off and landing run in a per-tick drone call after the safety pre-check; take_snapshot only copies

- **Status:** Accepted. Supersedes [ADR-0040](0040-landing-progress-stays-in-take-snapshot.md). Amends [ADR-0008](0008-drone-interface.md) and [ADR-0026](0026-tick-loop-calls-one-tick-step.md): a new drone interface call and a new step in the tick step. Amends [ADR-0011](0011-mock-models-setpoint-timeout.md): the mock moves its fake drone in the new call. Settles where [ADR-0048](0048-level-through-the-bad-flow-zone.md)'s level parts run.
- **Date:** 2026-11-07
- **Origin:** Mixed. A separate per-tick call (over the AI's recommendation of `take_snapshot`), `take_snapshot` doing only what its name says, the snapshot before the call, the call after the safety pre-check, and the name: mine. Keeping take-off and landing below behaviors (after my question whether they're behaviors), the mock moving in the call, and the mock importing the Crazyflie adapter's numbers: AI recommendations accepted.

## Context

ADR-0048's level parts (the initial climb and the final descent) need one
setpoint per tick: the firmware levels the drone after 0.5 s without one and
cuts the motors after 2 s. ADR-0040 kept landing progress in `take_snapshot`
for First flight. But `take_snapshot` should only copy the telemetry into a
snapshot (ADR-0008). Take-off and landing are state machines over ticks, like
behaviors, but two landings run with no behavior: the failsafe's (a failed
pre-check skips behaviors) and `disconnect()`'s (no tick loop).

## Options considered

- **Where:** A, in `take_snapshot` (ADR-0040's way); B, a separate per-tick
  call on the drone interface; C, a helper thread in the adapter (on a hang it
  finishes the climb with nobody in charge, and races with commands).
- **As behaviors:** rejected. The failsafe and shutdown landings would have no
  final descent, and the Flow deck's bad-flow zone would reach behavior code.
- **When in the tick:** first, after the snapshot, after the safety pre-check,
  or after send. Commands act at once inside the adapter, so the order changes
  only which data the call sees.

## Decision

B: `update_take_off_and_landing(snapshot)`.

- Take-off and landing stay below behaviors. Behaviors still only request
  take off and land; the Crazyflie adapter carries them out as state machines
  that this call ticks: the level parts' setpoints, the settle check, the
  hand-overs and the touchdown check.
- **Tick step:** snapshot, safety pre-check, `update_take_off_and_landing`,
  behaviors (only if the pre-check passed), send. The call always runs, a
  failed pre-check too, and decides from the tick's snapshot.
- `take_snapshot` only copies, in both adapters.
- **Mock:** the call also moves the fake drone by the snapshot's `dt`, for
  every command; its docstring says so. The snapshot then shows where the drone
  was at the end of the previous tick.
- The mock imports ADR-0048's numbers from the Crazyflie adapter package: it is
  a mock of the Crazyflie adapter. With another drone, it may be renamed after
  the adapter it mocks.

## Failure modes

- **Inputs:** a missing or stale value in the snapshot: the state machines'
  own rules (ADR-0048's fallback, ADR-0019's time limit).
- **Backups:** the firmware levels the drone and cuts the motors when the
  stream stops (ADR-0048); the kill switch (ADR-0027).
- **Never:** a failed pre-check stops the setpoint stream; `take_snapshot`
  sends anything to the drone.
- **Always eventually:** the motors stop (ADR-0048).

## Consequences

- **Risk I accept knowingly:** a hung tick still stops the call, as in
  ADR-0040. In a level part the firmware cuts the motors within 2 s; in the
  landing approach the drone holds above the bad-flow zone (ADR-0048). Acting
  on a hang stays in backlog #26.
- The bench's tick step calls it too, and the forged low battery drone
  (ADR-0041) passes it on. `disconnect()` still lands in its own loop, running
  the same progress (ADR-0026).
- Tests: the tick step's order, the call on a failed pre-check, and
  `take_snapshot` sending nothing to the drone. Mock tests that advanced the
  drone with `take_snapshot` call the new call.
- Glossary: *Tick step* reworded (proposed for my OK).
