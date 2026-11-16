# Architecture

How the parts fit together, and the rules every change keeps. This file
summarizes the accepted ADRs in [docs/decisions/](docs/decisions/README.md)
and decides nothing itself: where it and an accepted ADR disagree, the ADR
wins and this file is fixed. It changes only when the architect asks, in the
same commit as the ADR that changes the architecture. A task that conflicts
with it stops and asks first. Terms are the [glossary](docs/glossary.md)'s.

Each rule is marked with where it comes from:

- **(ADR-nnnn):** decided there.
- **[fitness]:** also enforced by a fitness function in `tests/architecture/`.
- **[target]:** planned by the refactor (section 7), not decided. Until its
  ADR is accepted, the rule beside it holds and nothing is built from it.

## 1. Data flow

```text
 drone ══ radio ══► cflib's receive thread: log callbacks convert to SI and write
                                   │
                                   ▼
                     TelemetryBuffer (the only lock)
                                   │ copied once per tick
                                   ▼
 the tick's thread: the TickLoop calls one TickStep at 20 Hz
   1  take_snapshot(dt)                       → Snapshot: frozen, every value stamped
   2  SafetyLayer.pre_check(snapshot)         → if it fails: Land, and the flight is over
   3  update_take_off_and_landing(snapshot)   → every tick, after a failed pre-check too
   4  Behavior.tick(snapshot, ask)            → ask(CommandRequest) returns a Verdict at once
   5  SafetyLayer.send()                      → one command per command slot
                                   │ DroneInterface: commands that don't block
                                   ▼
 drone ◄══ radio ══ the adapter: setpoints, high-level moves, parameters
```

The tick's order is fixed (ADR-0025, ADR-0026, ADR-0055). Telemetry flows one
way, from the drone to a snapshot; commands flow one way, from a command
request through the safety layer to the drone. Nothing skips a step.

## 2. Modules and what each owns

| Module, under `src/crazyflie_behavior/` | Owns |
|---|---|
| `geometry.py`, `snapshot.py` | The values every layer shares: `Vector3`, `Stamped`, the range readings, `DroneStatus`, `Snapshot`. All frozen (ADR-0018). |
| `timing/clock.py` | `Clock`, with the real clock and the sim clock: the only source of time (ADR-0009). |
| `drone/interface.py` | `DroneInterface`, which every adapter implements (ADR-0008), and the limits the safety layer and the adapters share. |
| `drone/telemetry_buffer.py` | The latest telemetry: written from any thread, copied out once per tick. The only lock in the data path (ADR-0007). |
| `drone/crazyflie/` | The Crazyflie adapter, the only code that imports cflib (ADR-0002): the link, the log blocks, unit conversion, every send, take-off, landing, touchdown, and "may be flying" (ADR-0039). Crazyflie-only concepts stop here (ADR-0006). |
| `drone/mock_adapter.py` | A fake drone with no physics, behind the same interface and the same buffer (ADR-0010, ADR-0011, ADR-0052). |
| `safety/requests.py` | The command request types and `Verdict`: all that a behavior may import from `safety/`. |
| `safety/safety_layer.py` | The safety pre-check, the judging of command requests, the command slots, and the sending of commands (ADR-0025, ADR-0030). |
| `behaviors/` | Decisions: a snapshot in, command requests out. Each is a state machine (ADR-0036); a field-test behavior states its failure rule (ADR-0033). |
| `loop/tick_loop.py` | Keeping time, and nothing else: due times, measurements, the hang watchdog, stop requests (ADR-0024, ADR-0026). |
| `loop/tick_step.py` | The order of one tick. |
| `programs/` | Putting it together: the clock, the drone, the safety layer, the behavior and the loop; logging; the interrupt signal; exit codes (ADR-0028). `failsafe_fault.py` holds fault injection, for test programs only (ADR-0041). |
| `tools/` (repository root) | Standalone scripts that may use cflib. `src/` never imports them (ADR-0002). |

## 3. Boundaries and contracts

| Boundary | Contract | Rules |
|---|---|---|
| Behavior to safety layer | `Behavior.tick(snapshot, ask) -> bool` (done). `ask(CommandRequest) -> Verdict`. | Requests are frozen records in SI units and the world frame. A verdict is approved or refused with a reason, at once (ADR-0025). A behavior holds no drone, no clock and no safety layer. **[target]** `tick` reports an outcome (ADR-0036, accepted, not built). |
| Safety layer to drone | `DroneInterface`: `arm`, `disarm`, `take_off`, `land`, `set_velocity`, `move_to`, `hover`, `emergency_stop`, `reset_estimate`, `chirp`, `play_tone`, `silence`. | A command starts an action and returns; what happened shows in later snapshots (ADR-0003, ADR-0008). Exceptions are for bugs and broken connections, never for a refusal. |
| Tick step to drone | `take_snapshot(dt) -> Snapshot`. `update_take_off_and_landing(snapshot)`. | The first only copies. The second moves a take-off or landing on by one tick (ADR-0055). |
| Program to drone | `connect()`, `disconnect()`. | The only calls that may block. `connect()` has time limits and returns with every telemetry value present (ADR-0029, ADR-0031). `disconnect()` lands a drone that may be flying (ADR-0038). |
| Drone to every layer | `Snapshot`. | Read-only. Each telemetry value is `Stamped` with its arrival time and the drone's, and is `None` until it first arrives. It also carries the adapter's `is_in_initial_climb` and `may_be_flying` (ADR-0054, ADR-0060) and the previous battery reading (ADR-0069). Its `time` is read after the copy (ADR-0046). |
| cflib's thread to the tick's | `TelemetryBuffer`: its writers and `snapshot()`. | Values that arrive together are written together, so no snapshot mixes two samples (ADR-0007, ADR-0021). |
| Tick loop to tick step | `TickStep.run(time, dt) -> bool` (done). | The loop knows nothing else about a tick (ADR-0026). |
| Any thread to tick loop | `TickLoop.request_stop()`. | Safe from any thread. The loop returns after the current tick, and the program's `disconnect()` lands (ADR-0026). |
| Everything to time | `Clock.now()`, `Clock.sleep_until()`. | Injected, never read from the system directly (ADR-0009). |

Only project types cross a boundary. No cflib object, `dict` of raw values or
untyped value does (ADR-0004).

## 4. Dependency rules

Imports point one way: programs, then the loop, behaviors and the safety
layer, then the drone, then the shared values.

| Module | May import, from the project |
|---|---|
| `geometry.py`, `timing/clock.py` | nothing |
| `snapshot.py`, `safety/requests.py` | `geometry` |
| `drone/interface.py` | `geometry`, `snapshot` |
| `drone/telemetry_buffer.py` | `geometry`, `snapshot`, `timing.clock` |
| `drone/crazyflie/` | the four rows above, its own modules, and cflib |
| `drone/mock_adapter.py` | the same four rows, and `drone/crazyflie/bad_flow_zone.py` for the numbers it mimics |
| `safety/safety_layer.py` | `safety.requests`, `snapshot`, `drone.interface` |
| `behaviors/` | `safety.requests`, `snapshot`, `geometry`, other behaviors |
| `loop/tick_loop.py` | `timing.clock` |
| `loop/tick_step.py` | `loop.tick_loop`, `behaviors.behavior`, `safety.safety_layer`, `drone.interface` |
| `programs/` | anything in `src/` |

Forbidden:

1. cflib anywhere but `drone/crazyflie/` and `tools/` (ADR-0002). **[fitness]**
2. `tools/` from `src/` (ADR-0002). **[fitness]**
3. In a behavior: the drone package (ADR-0002); anything in `safety/` but
   `requests.py`; a clock, meaning `time`, `datetime` or `timing/`
   (ADR-0009). **[fitness]**, all three.
4. A drone command called from outside `safety/` and `drone/` (ADR-0008,
   ADR-0030). **[fitness]** Two exceptions: the forged low battery drone
   passes commands on unchanged (ADR-0041), and the kill switch (ADR-0013,
   accepted, not built).
5. In `loop/tick_loop.py`: any project code but the clock (ADR-0026).
   **[fitness]**
6. `programs/failsafe_fault.py` imported by anything but the failsafe program
   (ADR-0041); a take-over asked for by anything but the rescue landing
   program (ADR-0038). **[fitness]**, both.
7. A dataclass that isn't frozen with slots (ADR-0018). **[fitness]**
8. A clock in the safety layer (ADR-0030). By review: no fitness function.
9. `safety/`, `behaviors/`, `loop/` or `programs/` from `drone/`; `behaviors/`,
   `loop/` or `programs/` from `safety/`. True of the code today, with no ADR
   line or fitness function of its own. **[target]** give it both.

## 5. Timing and threads

- **Tick rate:** 20 Hz, `TICK_RATE` (ADR-0023). Each due time is the previous
  one plus a tick period. After an overrun the next tick starts at once, and
  missed ticks are never caught up (ADR-0024).
- **Hangs:** a tick longer than `HANG_TIMEOUT` writes every thread's stack
  trace to the log. It only reports (ADR-0026, backlog #26).
- **Telemetry periods** are matched to their sources: the state block and the
  down range faster than a tick, the Multi-ranger at the firmware's 10 Hz,
  the battery once a second (ADR-0021, ADR-0022, ADR-0023).
- **The firmware's setpoint timeout:** it stops following a setpoint stream
  that goes quiet for about 0.5 s and cuts the motors after about 2 s
  (ADR-0011). So whatever streams setpoints is fed on every tick, and nothing
  in a tick may wait.
- **No waiting:** no sleep, wait or blocking read in a tick, a command or a
  cflib callback (ADR-0003). Known exception: a cflib send can wait up to 2 s
  during radio trouble (ADR-0027).
- **Threads:** the tick's thread, which is the main thread and runs the
  signal handler; cflib's receive thread, where a callback converts, writes
  to the telemetry buffer and returns; cflib's own radio and parameter
  threads; helper threads only while connecting (ADR-0029). Data crosses
  threads through the telemetry buffer, and `request_stop()` is the only call
  into the loop from another thread.
- **Time:** behaviors and the safety layer take time from the snapshot
  (ADR-0009, ADR-0030, ADR-0046). Only programs, the tick loop and the drone
  package hold a clock. A value is stale when its age is over the reader's
  limit, counted from its arrival.
- **Logging:** log-file writes run on the caller's thread (ADR-0028). Console
  output moves to a background thread (ADR-0035, accepted, not built).

## 6. Safety: never and always

**Never:**

- A command request reaches the drone unjudged (ADR-0025).
- A behavior runs on a tick whose safety pre-check failed, or on any tick
  after it: a failed pre-check ends the flight for good (ADR-0030).
- A missing, stale or non-finite value counts as safe (ADR-0030).
- The motors stop before the down range confirms touchdown or the final
  descent's time limit runs out (ADR-0012, ADR-0019).
- cflib's `close_link()` is called on a drone that may be flying: it sends
  zero thrust first (ADR-0038).
- An estimate reset or a new thrust base goes to a drone that may be flying
  (ADR-0054, ADR-0061).
- Fault injection or a take-over is reachable from a game program (ADR-0038,
  ADR-0041). **[fitness]**
- An interrupt signal cuts a landing short (ADR-0026).

**Always:**

- The safety pre-check runs before behaviors, on every tick, on that tick's
  snapshot (ADR-0025).
- `update_take_off_and_landing` runs on every tick, after the pre-check,
  failed or not (ADR-0055).
- Every way out of the tick loop but a hang ends in `disconnect()`, which
  lands a drone that may be flying (ADR-0026).
- Unsure whether the drone is flying, the adapter says it is (ADR-0039).
- Connecting refuses a drone that's already flying; only the rescue landing
  takes one over (ADR-0038).
- A failure is logged. The code carries on when that's safe and fails safe
  when it isn't (ADR-0020).

## 7. The refactor's target

Proposed by the codebase review of 2026-11-13. Every row is **[target]**: it
binds nothing until its ADR is accepted, and then this file changes with it.
The options for each row are in the review's working notes, which stay out of
the repository until they're decided. Module names are working names.

| Target | Changes here | Needs |
|---|---|---|
| The Crazyflie adapter becomes parts inside `drone/crazyflie/`: `link.py`, `log_blocks.py` and `commands.py`, which with `adapter.py` are the only cflib importers; and `flight_phases.py`, the take-off and landing logic with no cflib import and strict typing. `DroneInterface` stays as it is. | Section 2; rule 1 narrows to the named modules | An ADR; the glossary's *Crazyflie adapter* |
| The tick loop flies the whole flight. After a failed pre-check, a stop request or a behavior that ends in flight, the tick step keeps ticking until the snapshot says the drone isn't flying. `disconnect()` lands only after an error. | Section 3 (the two tick loop rows); section 6; the glossary's *Stop request* | An ADR that amends ADR-0026 |
| A link lost in flight is a state the adapter reports, and a landing that fails has a last resort sharing no code with it. | Section 6 | An ADR with failure modes |
| A tick reports an outcome, up to the program. | Section 3 | ADR-0036 is accepted; how the outcome travels is open |
| Recordings, replay tests, and program tests on the sim clock. | A recorder beside the tick step | ADR-0034 is accepted; its details are open |
| Tuning values are grouped, passed in, and logged with every run. | Where constants live | An ADR |
| The mock adapter runs the Crazyflie adapter's take-off and landing code. | Section 4, the mock's row | An ADR |

During a refactor, structure moves only toward this table, and only for a row
whose ADR is accepted. A move-only commit changes no behavior, no boundary
and no test body.
