# 0008: The drone interface

- **Status:** Accepted. Decision 1 amended by [ADR-0013](0013-operator-kill-switch.md): the operator's kill switch is an exception.
- **Date:** 2026-10-20
- **Origin:** Mixed. Mostly AI recommendations accepted. Overrode the AI on reporting refusals (behavior trees need answers within the same tick) and on keeping the downward reading in range readings.

## Context

ADRs 0002–0007 settled that behaviors depend only on a drone interface, run in
a tick loop on per-tick snapshots, use steering mode and fast mode, and that
the interface is Crazyflie-focused with generic vocabulary. This ADR defines
the interface itself: who calls it, what it offers, what range readings look
like, and how refusals and failures are reported.

## Options considered and decisions

### 1. Who calls the drone interface?
- A. Behaviors call it directly, and the safety layer interrupts after the fact.
- **B. Behaviors produce command requests; only the safety layer calls the
  drone interface** (approve, clamp to the speed envelope, or override).

**Chosen: B.** Safety rules become structure, not convention: fast mode can't
happen unapproved and the speed envelope can't be exceeded, because behaviors
have no path to the drone except through the safety layer.

### 2. How does the tick get its snapshot?
- A. The tick loop owns the telemetry buffer and hands it to adapters.
- B. Each adapter owns its own buffer, behind `take_snapshot()`.
- **C. `take_snapshot()` on the interface, with one shared `TelemetryBuffer`
  class used by every adapter.**

**Chosen: C.** A clean interface, and the single lock is written and tested
once.

### 3. Range readings
- **Shape: named fixed directions** (`front`, `back`, `left`, `right`, `up`,
  `down`) rather than a generic list, per ADR-0006.
- **Each reading is a distance, out of range (clear) or invalid (unknown).**
  Unknown must never be treated as clear.
- **`down` is a range reading like the others.** Altitude comes from the
  position estimate's z, so there's no separate height field. Horizontal
  avoidance uses the four horizontal directions; `up` and `down` get their own
  rules (don't climb into the ceiling, don't descend into what's below).

### 4. Command set
| Command | Purpose |
|---|---|
| `connect()` / `disconnect()` | Session, used as a `with` block so landing is guaranteed |
| `arm()` / `disarm()` | Enable or disable the motors |
| `take_off(height)` | Rise to a height and hover |
| `land()` | Descend and stop the motors |
| `set_velocity(velocity, yaw_rate)` | Steering mode. A setpoint stream, sent every tick |
| `move_to(position, duration)` | Fast mode. A smooth trajectory flown onboard |
| `hover()` | Stop and hold position |
| `emergency_stop()` | Cut the motors immediately |
| `take_snapshot()` | Copy the telemetry buffer into a snapshot |

### 5. Frame and yaw
- **Velocities and positions are in the world frame**, as I'd direct an agent
  in Unreal.
- **Yaw is held fixed for now**, so body and world directions coincide and no
  conversions are needed. A quadcopter moves in any direction by tilting, so
  nothing requires turning. Yaw control is a backlog item for when a behavior
  needs it.

### 6. Reporting refusals and failures
- A. Return values from each call.
- B. Exceptions.
- C. Everything reported in the next tick's inputs.
- **D. Synchronous safety queries plus next-tick status for physical outcomes.**

**Chosen: D.** Behavior trees need refusals *during* the same tick's search,
so C's one-tick delay per rejection would slow every fallback. The safety
layer offers side-effect-free queries (e.g. `can_enter_fast_mode()`) that
behaviors call while searching, like a BT decorator. The final verdict uses the
same snapshot, so it matches the query. Physical outcomes (take-off finished,
link lost, crash) take real time and arrive in the next snapshot, like a BT task
returning Running. Exceptions are reserved for abnormal problems (bugs, can't
connect), never normal refusals.

## Consequences

- Fitness functions: behavior modules never import the drone interface; only
  the safety layer and the tick loop do.
- The snapshot carries drone status (armed, flying, link quality, crashed)
  alongside telemetry.
- The safety layer has two faces: read-only queries for behaviors, and the
  single command path to the drone.
- `TelemetryBuffer` gets its own unit tests for thread safety.
- The Crazyflie adapter maps this interface onto cflib (world-frame velocity
  setpoints, high-level commander for `move_to`, supervisor for arming and
  status, unit conversion to SI).
