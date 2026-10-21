# Glossary

The project's shared language. Every term here means exactly one thing, and it
means the same in conversation, docs and code. The UE5 column gives the
nearest equivalent, with a note where the analogy breaks.

Most terms describe how the drone and robotics world works. Terms in
**Architecture** are project design and carry a status:
- **Decided**: chosen by the architect. Links to its ADR.
- **Proposed**: a candidate term waiting on a design decision. It may change or
  disappear.

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
| **Multi-ranger deck** | Deck with 5 laser distance sensors (front, back, left, right, up). | Five fixed line traces fired every sample. |
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
| **State estimate** | The drone's best guess of its own position, velocity and attitude, fused from sensors (`stateEstimate.*`). | The Pawn's transform, **except it is a guess, not ground truth**. |
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

## Architecture

| Term | Definition | UE5 analogy | Status |
|---|---|---|---|
| **Drone interface** | The abstraction behavior code uses to sense and command a drone, with no knowledge of cflib. | A `UInterface` (`IDroneInterface`) both real and fake Pawns implement. | Decided ([0002](decisions/0002-behavior-depends-only-on-drone-interface.md)) |
| **Adapter** | An implementation of the drone interface for one backend. | A concrete class implementing the `UInterface`. | Decided ([0002](decisions/0002-behavior-depends-only-on-drone-interface.md)) |
| **Crazyflie adapter** | Adapter that talks to a physical Crazyflie through cflib. The only module in `src/` allowed to import cflib. | A concrete `UInterface` implementation that wraps a hardware SDK. | Decided ([0002](decisions/0002-behavior-depends-only-on-drone-interface.md)) |
| **Tool** | A standalone diagnostic script in `tools/` (e.g. `first_flight.py`) that may use cflib directly, bypassing the drone interface. Never imported by project code. | A commandlet or editor utility: useful for debugging, never part of gameplay code. | Decided ([0002](decisions/0002-behavior-depends-only-on-drone-interface.md)) |
| **Mock adapter** | Adapter that is itself a simple fake drone: it answers commands and makes up telemetry in-process, with no physics, for tests and development. | A dummy Pawn used in an automation test. | Decided ([0002](decisions/0002-behavior-depends-only-on-drone-interface.md), renamed in [0010](decisions/0010-code-foundations.md)) |
| **Simulator** | A physics-ish model of the drone and room, including noise and drift. | PIE with a simulated world. | Decided ([0002](decisions/0002-behavior-depends-only-on-drone-interface.md)) |
| **Behavior** | Decision-making logic that turns sensed state into commands. Never imports cflib. | The AIController's Behavior Tree. | Decided ([0002](decisions/0002-behavior-depends-only-on-drone-interface.md)) |
| **Tick** | One iteration of the behavior update loop. | `Tick(DeltaTime)`. | Decided ([0003](decisions/0003-tick-loop-timing-model.md)) |
| **Telemetry buffer** | Thread-safe store of the latest value of each telemetry variable, written in the background as data arrives (by the Crazyflie adapter, or by the mock or simulator). | The net driver's incoming buffer of replicated values. | Decided ([0007](decisions/0007-snapshot-blackboard-telemetry-buffer.md)) |
| **Snapshot** | Read-only copy of the telemetry buffer, taken at the start of each tick. Every behavior in that tick sees the same snapshot. Each value carries its arrival time (PC clock) and the drone's timestamp. | A consistent frame of state that the game thread works from while packets keep arriving. | Decided ([0007](decisions/0007-snapshot-blackboard-telemetry-buffer.md)) |
| **Blackboard** | Behavior memory: what behaviors remember across ticks (next waypoint, where an obstacle was last seen). Written by behaviors, persists between ticks. | UE Blackboard (AI memory keys). | Decided ([0007](decisions/0007-snapshot-blackboard-telemetry-buffer.md)) |
| **Safety layer** | The layer between behaviors and the drone interface. It answers behaviors' safety queries and is the only code that sends commands to the drone: it approves, clamps to the speed envelope, or overrides command requests. | Server authority validating client movement requests. | Decided ([0008](decisions/0008-drone-interface.md)) |
| **Command request** | What a behavior asks the drone to do this tick (e.g. a velocity, or fast mode to a point). It goes to the safety layer, never directly to the drone. | A client asking the server to move. | Decided ([0008](decisions/0008-drone-interface.md)) |
| **Safety query** | A read-only question a behavior asks the safety layer during its decision, e.g. "can I enter fast mode?" It's answered immediately and has no side effects. | A BT decorator checking a condition. | Decided ([0008](decisions/0008-drone-interface.md)) |
| **Stamped value** | A telemetry value together with its arrival time (PC clock) and the drone's timestamp (converted to seconds). Every value in a snapshot is stamped, so its age can always be checked. | A replicated property plus "when the server sent it" and "when we received it". | Decided ([0007](decisions/0007-snapshot-blackboard-telemetry-buffer.md)) |
| **Range readings** | The set of six range readings in a snapshot, one per named direction (front, back, left, right, up, down). | The results of a fixed set of line traces fired every tick. | Decided ([0008](decisions/0008-drone-interface.md)) |
| **Drone status** | Flags describing the drone's state as the drone reports it: armed, flying, crashed, tumbled. Part of the snapshot. | Replicated state flags on the Pawn (alive, ragdolled…). | Decided ([0008](decisions/0008-drone-interface.md)) |
| **Range reading** | The distance a range sensor measures in one direction (front, back, left, right, up, down): either a distance, out of range (clear) or invalid (unknown). | A line trace result: hit at a distance, no hit, or the trace failed. | Decided ([0008](decisions/0008-drone-interface.md)) |
| **Clock** | The source of time for the tick loop, adapters and safety layer. A *real clock* reads the computer's monotonic time; a *sim clock* only advances when told to, so tests and simulations run faster than real time and repeat exactly. Behaviors don't read the clock directly: they receive the tick's time in the snapshot. | World time (game time) rather than OS time: pausable, dilatable and constant within a frame. Behaviors get it like `Tick(DeltaTime)`. | Decided ([0009](decisions/0009-clock-abstraction.md)) |
| **Control mode** | How behaviors command motion at a given moment: either steering mode or fast mode. | Which movement driver is in charge: AI steering or a scripted move. | Decided ([0005](decisions/0005-control-modes-steering-and-fast.md)) |
| **Steering mode** | The default control mode: velocity commands with obstacle-avoidance steering, slow and controlled. | `AddMovementInput` each Tick from steering behaviors. | Decided ([0005](decisions/0005-control-modes-steering-and-fast.md)) |
| **Fast mode** | Control mode for moving quickly to a target using position commands (`go_to`), with obstacle-avoidance steering disabled. The safety layer stays active and can interrupt it. | A scripted `MoveTo` with steering off, but collision still on. | Decided ([0005](decisions/0005-control-modes-steering-and-fast.md)) |
| **Speed envelope** | The maximum speed and acceleration allowed in a control mode. The safety layer may tighten it in the moment but never widen it. | `MaxWalkSpeed` and `MaxAcceleration` on the movement component, clamped by gameplay rules. | Decided ([0005](decisions/0005-control-modes-steering-and-fast.md)) |

<!-- Terms still to define as decisions land: command,
     geofence, failsafe, recording/replay, ... -->
