# Glossary

The project's shared language. Every term here means exactly one thing, and it
means the same in conversation, docs and code. The UE5 column gives the
nearest equivalent, with a note where the analogy breaks, or says "No UE
analogy" when none fits.

Every term here is approved by the architect. Most describe how the drone
and robotics world works. Terms in **Architecture** and in the game sections
(**Hide-and-seek**, **Catch the bird**) are project design: their **ADR**
column links to the decisions behind them. A term replaced by a later decision
moves to **Deprecated terms** at the bottom, so old ADRs still make sense.
Don't use those in new docs or code.

To add or change a term: propose it in conversation, agree on it, then edit
this file in the same commit as the code or ADR that uses it.

---

## Hardware and platform

| Term | Definition | UE5 analogy |
|---|---|---|
| **Crazyflie** | The physical drone: Crazyflie 2.1+, 27 g, about 7 min of flight per battery. | The possessed Pawn. |
| **Crazyradio** | USB radio dongle the PC uses to talk to the Crazyflie. | The network connection to a remote client. |
| **Deck** | Plug-in expansion board on the Crazyflie. | A component added to the Pawn. |
| **Flow deck** | Deck with a downward optical-flow camera and height sensor. Needed to hold position. | Gives the Pawn a sense of its own movement. |
| **Multi-ranger deck** | Deck with 5 laser distance sensors (front, back, left, right, up). Each sensor sees a cone about 27° wide and reports a single distance for the whole cone. | Like five line traces fired every sample, but each gives back a blurry distance reading from a sensor in the shape of a cone. |
| **Buzzer deck** | Deck with a small piezo buzzer that plays tones and short melodies, so a sound comes from where the drone is. | A sound component on the Pawn: the sound plays at the Actor's location. |
| **Firmware** | Code running on the drone itself: stabilization, estimation, motor control at about 1 kHz. | The engine's physics and movement component. You don't rewrite it, you give it inputs. |
| **cflib** | Bitcraze's official Python library for talking to the Crazyflie. | An engine-provided API module. |
| **URI** | Address of a specific drone, e.g. `radio://0/80/2M/E7E7E7E7E7`. | A server address to connect to. |
| **CRTP** | The packet protocol between PC and drone. Everything in cflib is built on it. | The replication wire protocol. You almost never touch it directly. |

## Communication

| Term | Definition | UE5 analogy |
|---|---|---|
| **Link** | An open connection to one drone. | A net connection for one client. |
| **TOC** (table of contents) | List of every log variable and parameter the firmware exposes, by name, downloaded on connect. | Reflection data: the set of `UPROPERTY`s you can query by name. |
| **Telemetry** | Data streamed from the drone to the PC. | Replicated properties arriving from the server. |
| **Log block** | A cflib `LogConfig`: a named group of variables streamed at a fixed period (max 26 bytes per block). | A replicated struct with its own net update frequency. |
| **State block** | The Crazyflie adapter's log block that carries the position estimate, velocity estimate and drone status together (6 floats and a 2-byte bitfield: the full 26 bytes), so all three come from the same moment ([ADR-0021](decisions/0021-drone-status-streams-with-the-state.md)). | One replicated struct holding the transform, velocity and state flags, so they always update together. |
| **Parameter** | Named firmware setting you can read or write at run time, e.g. `kalman.resetEstimation`. | A console variable (CVar). |
| **Callback** | Function cflib calls when an event or data arrives. Runs on cflib's background thread. | A bound multicast delegate, but fired **off the game thread**. |

## Space and motion

| Term | Definition | UE5 analogy |
|---|---|---|
| **World frame** | Fixed coordinate frame: meters, +X forward (at takeoff), +Y left, +Z up. Right-handed. Origin at the takeoff point. | World space, **but** UE5 is left-handed, +Y **right**, in **centimeters**. |
| **Body frame** | Frame attached to the drone: +X out the drone's front, +Y left, +Z up. Rotates with yaw. | Actor local space (with the same handedness caveat). |
| **Yaw** | Rotation about +Z (heading). cflib uses degrees in some places and radians in others. Always check. | `FRotator::Yaw`. |
| **Setpoint** | A target the firmware's controller tries to reach: a position, a velocity or a hover height. | A MoveTo goal, or the input vector given to `AddMovementInput`. |
| **Setpoint stream** | Sending low-level setpoints continuously (≥ every few hundred ms). If they stop, the firmware stops following. | Input you must feed every Tick or the Pawn stops. |
| **High-level commander** | Firmware feature that plans a smooth trajectory to a goal on the drone itself (`takeoff`, `go_to`, `land`). | `MoveTo` with path following done by the movement component. |
| **Trajectory** | A planned path through time from the current state to a goal. | A spline the movement component follows. |

## State and estimation

| Term | Definition | UE5 analogy |
|---|---|---|
| **State estimate** | The drone's best guess of its own position, velocity and attitude, fused from sensors (`stateEstimate.*`). Not independent of those sensors: with a Flow deck, height comes mostly from the down range. | The Pawn's transform, **except it is a guess, not ground truth**. |
| **Estimator** | Firmware algorithm (a Kalman filter) that produces the state estimate. | Client-side smoothing of replicated movement, but for real sensor data. |
| **Drift** | Slow, growing error in the state estimate over a flight (flow deck has no absolute reference). | No equivalent: in a game, `GetActorLocation()` never lies. |
| **Sensor noise** | Random error on each reading. | Like adding random jitter to every line trace hit distance. |
| **Ground truth** | The *actual* position, known only in simulation or with external tracking. | `GetActorLocation()`. |

## Safety

| Term | Definition | UE5 analogy |
|---|---|---|
| **Arming** | Explicitly enabling the motors before flight (`supervisor.send_arming_request`). | No equivalent; closest is a "can move" gate on the Pawn. |
| **Emergency stop** (e-stop) | Immediately cut all motors. The drone falls. | Destroying the Pawn's movement component mid-air. |
| **Supervisor** | Firmware subsystem tracking safety state (armed, flying, tumbled, crashed). | A gameplay state machine guarding what the Pawn may do. |
| **Failsafe** | The safety layer's automatic response to a failure that makes flying unsafe: hover, land or stop, depending on how serious it is ([ADR-0020](decisions/0020-failures-degrade-gracefully.md)). | A gameplay fallback that ends the match cleanly when a critical system fails, instead of crashing. |

## Architecture

| Term | Definition | UE5 analogy | ADR |
|---|---|---|---|
| **Drone interface** | The abstraction behavior code uses to sense and command a drone, with no knowledge of cflib. | A `UInterface` (`IDroneInterface`) both real and fake Pawns implement. | [0002](decisions/0002-behavior-depends-only-on-drone-interface.md) |
| **Adapter** | An implementation of the drone interface for one backend. | A concrete class implementing the `UInterface`. | [0002](decisions/0002-behavior-depends-only-on-drone-interface.md) |
| **Crazyflie adapter** | Adapter that talks to a physical Crazyflie through cflib. The only module in `src/` allowed to import cflib. | A concrete `UInterface` implementation that wraps a hardware SDK. | [0002](decisions/0002-behavior-depends-only-on-drone-interface.md) |
| **Tool** | A standalone diagnostic script in `tools/` (e.g. `first_flight.py`) that may use cflib directly, bypassing the drone interface. Never imported by project code. | A commandlet or editor utility: useful for debugging, never part of gameplay code. | [0002](decisions/0002-behavior-depends-only-on-drone-interface.md) |
| **Mock adapter** | Adapter that is itself a simple fake drone: it answers commands and makes up telemetry in-process, with no physics, for tests and development. | A dummy Pawn used in an automation test. | [0002](decisions/0002-behavior-depends-only-on-drone-interface.md), renamed in [0010](decisions/0010-code-foundations.md) |
| **Simulator** | A physics-ish model of the drone and room, including noise and drift. | PIE with a simulated world. | [0002](decisions/0002-behavior-depends-only-on-drone-interface.md) |
| **Behavior** | Decision-making logic that turns sensed state into commands. Never imports cflib. | The AIController's Behavior Tree. | [0002](decisions/0002-behavior-depends-only-on-drone-interface.md) |
| **Tick** | One iteration of the behavior update loop. | `Tick(DeltaTime)`. | [0003](decisions/0003-tick-loop-timing-model.md) |
| **Tick loop** | The loop that runs ticks at the tick rate: it calls the tick step, then waits for the next due time. It keeps time, measures each tick and watches for hangs, but doesn't know what a tick does. | The engine loop with a frame-rate cap. | [0003](decisions/0003-tick-loop-timing-model.md), [0024](decisions/0024-tick-timing-strategy.md), [0026](decisions/0026-tick-loop-calls-one-tick-step.md) |
| **Tick step** | What one tick does, in a fixed order: snapshot, safety pre-check, behaviors, send. The tick loop calls it once per tick. | `UWorld::Tick` running its tick groups in order. | [0026](decisions/0026-tick-loop-calls-one-tick-step.md) |
| **Stop request** | A request from any thread (Ctrl+C, an operator command) for the tick loop to stop after the current tick. Leaving the `with drone:` block then lands. | `RequestExit`: the engine finishes the frame, then shuts down. | [0026](decisions/0026-tick-loop-calls-one-tick-step.md) |
| **Hang watchdog** | Detects a tick that runs longer than 1 s and writes every thread's stack trace to the log. It only reports; acting on a hang is backlog #26. | UE's hang detector, which dumps the call stack when the game thread stops responding. | [0026](decisions/0026-tick-loop-calls-one-tick-step.md) |
| **Console** | The text window the program runs in: PyCharm's Run window, or a terminal window. Shows log messages at info level and above; the log file gets everything. | The Output Log window. Not UE's `~` console, where you type commands. | [0026](decisions/0026-tick-loop-calls-one-tick-step.md) |
| **Log level** | How important a log message is: debug (every detail, such as each tick's timing), info (normal events), warning (something went wrong but the program carries on), error (something failed), critical (the most severe). The console and the log file each show messages at or above a chosen level. | `UE_LOG` verbosity (`Verbose`, `Log`, `Warning`, `Error`). Unlike UE's `Fatal`, critical doesn't stop the program. | [0026](decisions/0026-tick-loop-calls-one-tick-step.md) |
| **Program** | A runnable entry point, such as the bench program. It sets up logging, the drone and the tick loop, then runs until it's done or stopped. | Like UE's `Source/Programs`: standalone executables built from the same code. | [0028](decisions/0028-programs-bench-first-plain-logging.md) |
| **Bench program** | The program for field-test stage 0. It connects to the drone, runs the tick loop and logs every snapshot, but never commands the drone. | No UE analogy. | [0028](decisions/0028-programs-bench-first-plain-logging.md) |
| **Tick rate** | Ticks per second: 20 Hz. | `t.MaxFPS`. | [0023](decisions/0023-tick-rate-20-hz.md) |
| **Due time** | When a tick should start: the previous due time plus one tick period, or, after an overrun, the moment the late tick ends. | When the next frame is due under a frame cap. | [0024](decisions/0024-tick-timing-strategy.md) |
| **Overrun** | A tick still working at the next due time. The next tick starts at once; missed ticks are skipped, never caught up. Always logged. | A hitch: a frame that took too long. | [0024](decisions/0024-tick-timing-strategy.md) |
| **Lateness** | How long after its due time a tick actually started. | Frame start delay. | [0024](decisions/0024-tick-timing-strategy.md) |
| **Work time** | How long a tick's own work took, not counting the wait. | Game thread time in `stat unit`. | [0024](decisions/0024-tick-timing-strategy.md) |
| **Telemetry buffer** | Thread-safe store of the latest value of each telemetry variable, written in the background as data arrives (by the Crazyflie adapter, or by the mock or simulator). | The net driver's incoming buffer of replicated values. | [0007](decisions/0007-snapshot-blackboard-telemetry-buffer.md) |
| **Snapshot** | Read-only copy of the telemetry buffer, taken at the start of each tick. Every behavior in that tick sees the same snapshot. Each value carries its arrival time (PC clock) and the drone's timestamp. | A consistent frame of state that the game thread works from while packets keep arriving. | [0007](decisions/0007-snapshot-blackboard-telemetry-buffer.md) |
| **Blackboard** | Behavior memory: what behaviors remember across ticks (next waypoint, where an obstacle was last seen). Written by behaviors, persists between ticks. | UE Blackboard (AI memory keys). | [0007](decisions/0007-snapshot-blackboard-telemetry-buffer.md) |
| **Safety layer** | The layer between behaviors and the drone interface. It runs the safety pre-check on each snapshot, answers command requests at once, and is the only code that sends commands to the drone, apart from the kill switch ([ADR-0013](decisions/0013-operator-kill-switch.md)): it approves, clamps to the speed envelope, or overrides command requests. | Server authority validating client movement requests. | [0008](decisions/0008-drone-interface.md), [0013](decisions/0013-operator-kill-switch.md), [0025](decisions/0025-safety-pre-check-and-command-slots.md) |
| **Kill switch** | The operator's command to cut the motors immediately, executed at any moment, like a cheat command. The one thing that bypasses the safety layer; everything else goes through it. | A console cheat command that bypasses the gameplay rules. | [0013](decisions/0013-operator-kill-switch.md) |
| **Kill latch** | The program's refusal to arm or take off after the kill switch, until the program is restarted. It backs up the drone lock and says why it refuses. | No UE analogy. | [0027](decisions/0027-operator-controls.md) |
| **Drone lock** | The drone's own state after an emergency stop: its firmware refuses to fly until the drone is restarted (switched off and on). | No UE analogy. | [0027](decisions/0027-operator-controls.md) |
| **Final descent** | After the planned landing, the slow descent that continues until the down range confirms touchdown, or until a time limit says the drone must be on the floor. Then the motors stop. | A fallback "settle to ground" state when the landing animation ended but the character isn't grounded. | [0019](decisions/0019-final-descent-when-touchdown-unconfirmed.md) |
| **Landing phase** | Where a landing is: not landing, the planned landing (the high-level landing, planned from the height estimate), or the final descent. The Crazyflie adapter holds it. | The current state of a small landing state machine. | [0019](decisions/0019-final-descent-when-touchdown-unconfirmed.md) |
| **Command request** | What a behavior asks the drone to do this tick (e.g. a velocity, or fast mode to a point). The safety layer answers at once (approved, clamped or refused, with the reason). At the end of the tick, each command slot's approved request is sent. Never goes directly to the drone. | A client asking the server to move. | [0008](decisions/0008-drone-interface.md), [0025](decisions/0025-safety-pre-check-and-command-slots.md) |
| **Command slot** | A group of commands where only one can be active at a time: movement (take off, land, velocity, move to, hover), buzzer, LEDs. A later approved request in the same tick replaces the earlier one, and the replacement is logged as a warning. Each slot's request is sent at the end of the tick. | An animation montage slot. | [0025](decisions/0025-safety-pre-check-and-command-slots.md) |
| **Safety pre-check** | The safety layer's check of each snapshot at the start of the tick, before behaviors run (stale data, battery, geofence). If it passes, behaviors run and their requests are judged against it; if it fails, behaviors are skipped and the failsafe takes over. | A behavior tree root decorator that aborts the tree when its condition fails. | [0025](decisions/0025-safety-pre-check-and-command-slots.md) |
| **Stamped value** | A telemetry value together with its arrival time (PC clock) and the drone's timestamp (converted to seconds). Every value in a snapshot is stamped, so its age can always be checked. | A replicated property plus "when the server sent it" and "when we received it". | [0007](decisions/0007-snapshot-blackboard-telemetry-buffer.md) |
| **Range readings** | The set of six range readings in a snapshot, one per named direction (front, back, left, right, up, down). | The results of a fixed set of line traces fired every tick. | [0008](decisions/0008-drone-interface.md) |
| **Drone status** | Flags describing the drone's state as the drone reports it: armed, flying, crashed, tumbled. Part of the snapshot. | Replicated state flags on the Pawn (alive, ragdolled…). | [0008](decisions/0008-drone-interface.md) |
| **Range reading** | The distance a range sensor measures in one direction (front, back, left, right, up, down): either a distance, out of range (clear) or invalid (unknown). | Like a line trace, but instead we get back a blurry distance reading from a sensor in the shape of a cone. | [0008](decisions/0008-drone-interface.md) |
| **Range status** | Whether a range reading is a *distance* (something detected at a known distance), *out of range* (clear) or *invalid* (unknown). In code: `RangeStatus`, and the reading's field is `status`. Named after the "range status" that the VL53 laser sensors report with each measurement. | Whether a line trace hit, missed, or failed. | [0008](decisions/0008-drone-interface.md) |
| **Range direction** | One of the six named directions a range reading points: front, back, left, right, up, down. Relative to the drone. In code: `RangeDirection`. | The fixed directions of a Pawn's sensor traces. | [0008](decisions/0008-drone-interface.md) |
| **Clock** | The source of time for the tick loop, adapters and safety layer. A *real clock* reads the computer's monotonic time; a *sim clock* only advances when told to, so tests and simulations run faster than real time and repeat exactly. Behaviors don't read the clock directly: they receive the tick's time in the snapshot. | World time (game time) rather than OS time: pausable, dilatable and constant within a frame. Behaviors get it like `Tick(DeltaTime)`. | [0009](decisions/0009-clock-abstraction.md) |
| **Control mode** | How behaviors command motion at a given moment: either steering mode or fast mode. | Which movement driver is in charge: AI steering or a scripted move. | [0005](decisions/0005-control-modes-steering-and-fast.md) |
| **Steering mode** | The default control mode: velocity commands with obstacle-avoidance steering, slow and controlled. | `AddMovementInput` each Tick from steering behaviors. | [0005](decisions/0005-control-modes-steering-and-fast.md) |
| **Fast mode** | Control mode for moving quickly to a target using position commands (`go_to`), with obstacle-avoidance steering disabled. The safety layer stays active and can interrupt it. | A scripted `MoveTo` with steering off, but collision still on. | [0005](decisions/0005-control-modes-steering-and-fast.md) |
| **Speed envelope** | The maximum speed and acceleration allowed in a control mode. The safety layer may tighten it in the moment but never widen it. | `MaxWalkSpeed` and `MaxAcceleration` on the movement component, clamped by gameplay rules. | [0005](decisions/0005-control-modes-steering-and-fast.md) |

## Hide-and-seek

Terms for the first game ([ADR-0016](decisions/0016-first-game-hide-and-seek-drone-lands.md)).

| Term | Definition | UE5 analogy | ADR |
|---|---|---|---|
| **Launch point** | The marked spot every round starts from. The drone takes off from it facing a fixed direction, the map is stored relative to it, and it stands in for the waiting area. | PlayerStart: every round spawns here. | [0016](decisions/0016-first-game-hide-and-seek-drone-lands.md) |
| **Waiting area** | Where the player waits during a hiding flight: right behind the launch point, with a safety gate between it and the play area. | A pre-round lobby the player can't leave until the round starts. | [0016](decisions/0016-first-game-hide-and-seek-drone-lands.md) |
| **Play area** | The space the drone flies and hides in. Nobody is in it while the drone flies. | The playable level, locked during the setup phase. | [0016](decisions/0016-first-game-hide-and-seek-drone-lands.md) |
| **Mapping run** | A flight before play, with the play area clear, that builds the map the hiding flights use. Up to about 5 minutes. | Building the navmesh before play, except the drone has to fly the level to see it. | [0016](decisions/0016-first-game-hide-and-seek-drone-lands.md) |
| **Hiding spot** | A place on the floor where the drone lands to hide, with at least one wall between it and the launch point. | An EQS result: a point that fails the line-of-sight test from the PlayerStart. | [0016](decisions/0016-first-game-hide-and-seek-drone-lands.md) |
| **Found** | The player picks up the hidden drone, which shows as the down reading jumping and the motion sensors spiking. The drone lights its LEDs and the PC plays a fanfare. | An interact event on a hidden collectible. | [0016](decisions/0016-first-game-hide-and-seek-drone-lands.md) |
| **Hint** | Every 15 s until the drone is found, it flashes its LEDs and chirps, so the player can find it. | A ping that reveals where an objective is. | [0017](decisions/0017-hint-chirps-from-buzzer-deck.md) |

## Catch the bird

Terms for the second game ([ADR-0015](decisions/0015-first-game-catch-the-bird.md), [rules](catch-the-bird.md)).

| Term | Definition | UE5 analogy | ADR |
|---|---|---|---|
| **Sky layer** | The height band the drone plays in: above a child's reach, below the ceiling with a margin (about 1.5-2.0 m in a room with a 2.4 m ceiling). | A nav volume restricted to a height range, like flying units that keep to an air layer. | [0015](decisions/0015-first-game-catch-the-bird.md) |
| **Clearance rule** | The drone always keeps about 1 m of clearance below. If something rises toward it, it moves away sideways. | A keep-out radius enforced by the movement component, regardless of what the AI wants. | [0015](decisions/0015-first-game-catch-the-bird.md) |
| **Catch** | Scored when the child gets directly under the bird, as seen by the down sensor. The bird reacts and flies to a new spot. | An overlap trigger under the Pawn that scores a point. | [0015](decisions/0015-first-game-catch-the-bird.md) |

## Deprecated terms

> **Deprecated. Don't use these in new docs or code.** They're kept only so
> older ADRs and commits still make sense. Each one links to the decision
> that replaced it.

| Term | Definition (as it was) | UE5 analogy | Replaced by |
|---|---|---|---|
| **Safety query** | A read-only question a behavior asks the safety layer during its decision, e.g. "can I enter fast mode?" It's answered immediately and has no side effects. | A BT decorator checking a condition. | [0025](decisions/0025-safety-pre-check-and-command-slots.md) |

<!-- Terms still to define as decisions land: command,
     geofence, recording/replay, ... -->
