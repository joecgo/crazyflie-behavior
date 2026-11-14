# Glossary

The project's shared language. Every term here means exactly one thing, and it
means the same in conversation, docs and code.

Every term here is approved by the architect. Most describe how the drone
and robotics world works. Terms in **Architecture** and in the game sections
(**Hide-and-seek**, **Catch the bird**) are project design: their **ADR**
column links to the decisions behind them. A term replaced by a later decision
moves to **Deprecated terms** at the bottom, so old ADRs still make sense.
Don't use those in new docs or code.

To add or change a term: propose it in conversation, agree on it, then edit
this file in the same commit as the code or ADR that uses it.

Definitions leave out specifics (a measured value, a milestone) unless they're
only an example: "For example, about 43,300 for this drone".

---

## Hardware and platform

| Term | Definition |
|---|---|
| **Crazyflie** | The physical drone: Crazyflie 2.1+, 29 g, about 7 min of flight per battery (Bitcraze's figure; our decks add 5.7 g). |
| **Sag** | The drop in battery voltage while the motors draw current. Most of it goes within a second after they stop. On 2026-11-04: 0.32-0.42 V one second after take-off, up to 0.51 V after 20 s ([ADR-0051](decisions/0051-battery-flight-limit-and-take-off-limit.md)). |
| **Resting voltage** | The battery voltage with the motors off. It keeps rising for minutes after a flight ([ADR-0051](decisions/0051-battery-flight-limit-and-take-off-limit.md)). |
| **Crazyradio** | USB radio dongle the PC uses to talk to the Crazyflie. |
| **Deck** | Plug-in expansion board on the Crazyflie. |
| **Flow deck** | Deck with a downward optical-flow camera and height sensor. Needed to hold position. |
| **Image quality** | How much detail the Flow deck's camera sees (`motion.squal`). Low in dim light or over a plain floor. |
| **Multi-ranger deck** | Deck with 5 laser distance sensors (front, back, left, right, up). Each sensor sees a cone about 27° wide and reports a single distance for the whole cone. |
| **Buzzer deck** | Deck with a small piezo buzzer that plays tones and short melodies, so a sound comes from where the drone is. |
| **Firmware** | Code running on the drone itself: stabilization, estimation, motor control at about 1 kHz. |
| **cflib** | Bitcraze's official Python library for talking to the Crazyflie. |
| **URI** | Address of a specific drone, e.g. `radio://0/80/2M/E7E7E7E7E7`. |
| **CRTP** | The packet protocol between PC and drone. Everything in cflib is built on it. |

## Communication

| Term | Definition |
|---|---|
| **Link** | An open connection to one drone. |
| **TOC** (table of contents) | List of every log variable and parameter the firmware exposes, by name, downloaded on connect. |
| **Telemetry** | Data streamed from the drone to the PC. |
| **Log block** | A cflib `LogConfig`: a named group of variables streamed at a fixed period (max 26 bytes per block). |
| **State block** | The Crazyflie adapter's log block that carries the position estimate, velocity estimate and drone status together (6 floats and a 2-byte bitfield: the full 26 bytes), so all three come from the same moment ([ADR-0021](decisions/0021-drone-status-streams-with-the-state.md)). |
| **Diagnostic block** | The Crazyflie adapter's log block for the debug log only: attitude, motor power and Flow deck quality at 10 Hz, never in the snapshot ([ADR-0050](decisions/0050-diagnostic-log-block-to-the-debug-log.md)). |
| **Take-off block** | The Crazyflie adapter's log block for the debug log only: attitude and motor power every 10 ms, on only with `--take-off-log`: for 2 s from the end of connect, and for the first 2 s of each take-off ([ADR-0063](decisions/0063-take-off-and-controller-log-blocks.md), [ADR-0065](decisions/0065-take-off-block-runs-from-connect-and-each-take-off.md)). |
| **Controller block** | The Crazyflie adapter's log block for the debug log only: the attitude and rate controllers' integrals, the controller's commands and attitude setpoint, and the gyro, at 10 Hz ([ADR-0063](decisions/0063-take-off-and-controller-log-blocks.md)). |
| **Parameter** | Named firmware setting you can read or write at run time, e.g. `kalman.resetEstimation`. |
| **Callback** | Function cflib calls when an event or data arrives. Runs on cflib's background thread. |

## Space and motion

| Term | Definition |
|---|---|
| **World frame** | Fixed coordinate frame: meters, +X forward (at takeoff), +Y left, +Z up. Right-handed. Origin at the takeoff point. |
| **Body frame** | Frame attached to the drone: +X out the drone's front, +Y left, +Z up. Rotates with yaw. |
| **Yaw** | Rotation about +Z (heading). cflib uses degrees in some places and radians in others. Always check. |
| **Setpoint** | A target the firmware's controller tries to reach: a position, a velocity or a hover height. |
| **Setpoint stream** | Sending low-level setpoints continuously (≥ every few hundred ms). If they stop, the firmware stops following. |
| **Setpoint priority** | The firmware follows one source of setpoints at a time, and a setpoint stream outranks the high-level commander. After a stream, the adapter releases the priority so the high-level commander is followed again; until then the drone refuses its setpoints ([ADR-0058](decisions/0058-release-setpoint-priority-after-motor-stop.md)). |
| **High-level commander** | Firmware feature that plans a smooth trajectory to a goal on the drone itself (`takeoff`, `go_to`, `land`). |
| **Trajectory** | A planned path through time from the current state to a goal. |
| **Thrust command** | The thrust the firmware's controller asks for, in its own units: 0 to 65,535, where 65,535 is each motor's maximum thrust. The firmware adjusts each motor's output for the battery voltage, so a thrust command gives the same thrust at any charge; the logged motor outputs average to it only once that adjustment is undone. |
| **Hover thrust** | The thrust command that holds the drone at a steady height, the same at any battery charge. It depends on the drone's weight, so on its decks and propellers. For example, about 43,300 for this drone with the Flow, Multi-ranger and Buzzer decks (First flight 3). |
| **Thrust base** | The thrust command the firmware's vertical speed controller starts from (`posCtlPid.thrustBase`); its integral adds the rest, and restarts at zero at every setpoint mode change and on the floor. The Crazyflie adapter sets it near the hover thrust at connect ([ADR-0061](decisions/0061-thrust-base-set-at-connect.md)). |

## State and estimation

| Term | Definition |
|---|---|
| **State estimate** | The drone's best guess of its own position, velocity and attitude, fused from sensors (`stateEstimate.*`). Not independent of those sensors: with a Flow deck, height comes mostly from the down range. |
| **Estimator** | Firmware algorithm (a Kalman filter) that produces the state estimate. |
| **Drift** | Slow, growing error in the state estimate over a flight (flow deck has no absolute reference). |
| **Estimate runaway** | The state estimate's position and velocity growing fast and without limit because the estimator gets no usable flow: the Flow deck in low light or right at the floor, or the drone lifted by hand. Unlike drift, it happens in seconds, not over a whole flight. |
| **Bad-flow zone** | The heights just above the floor where the Flow deck's flow can't be trusted, so the estimated horizontal speed and position go wrong. It reaches at least 0.1 m in any light (the firmware's flow model), higher in dim light. Take-off and landing cross it level ([ADR-0048](decisions/0048-level-through-the-bad-flow-zone.md)). |
| **Velocity uncertainty** | How far off the estimator thinks its horizontal velocity estimate may be: its standard deviation in meters per second, the larger of the drone's forward and sideways directions (`kalman.varPX`, `varPY`). It grows while the estimator gets no flow and stays small while flow arrives, even wrong flow. |
| **Estimate reset** | Restarting the estimator with the drone on the floor: position (0, 0, 0) where it sits, velocity zero, level, and the velocity uncertainty back at its starting value, which looks healthy until flow proves otherwise. Never in flight. The firmware also resets by itself when the estimate passes 100 m or 10 m/s. |
| **Reset point** | Where the drone sat at its latest estimate reset: (0, 0) in the horizontal position estimate. |
| **Sensor noise** | Random error on each reading. |
| **Ground truth** | The *actual* position, known only in simulation or with external tracking. |
| **Hysteresis** | A deliberate lag in a flag or switch, so a noisy input can't flip it back and forth. The flag changes only after the input has stayed changed for a while, or it switches at different thresholds going up and going down. Example: the drone status keeps saying flying for 2 s after the motors stop. |

## Safety

| Term | Definition |
|---|---|
| **Arming** | Enabling the motors before flight: the drone ignores flight commands until it's armed. Armed alone doesn't spin the motors. Stock Crazyflie 2.1+ firmware arms itself once its pre-flight checks pass (auto-arming); otherwise an arm request does it (`supervisor.send_arming_request`). |
| **Emergency stop** (e-stop) | Immediately cut all motors. The drone falls. |
| **Supervisor** | Firmware subsystem tracking safety state (armed, flying, tumbled, crashed). |
| **Failsafe** | The safety layer's automatic response to a failure that makes flying unsafe: hover, land or stop, depending on how serious it is ([ADR-0020](decisions/0020-failures-degrade-gracefully.md)). |

## Architecture

| Term | Definition | ADR |
|---|---|---|
| **Drone interface** | The abstraction behavior code uses to sense and command a drone, with no knowledge of cflib. | [0002](decisions/0002-behavior-depends-only-on-drone-interface.md) |
| **Adapter** | An implementation of the drone interface for one backend. | [0002](decisions/0002-behavior-depends-only-on-drone-interface.md) |
| **Crazyflie adapter** | Adapter that talks to a physical Crazyflie through cflib. The only module in `src/` allowed to import cflib. | [0002](decisions/0002-behavior-depends-only-on-drone-interface.md) |
| **Tool** | A standalone diagnostic script in `tools/` (e.g. `first_flight.py`) that may use cflib directly, bypassing the drone interface. Never imported by project code. | [0002](decisions/0002-behavior-depends-only-on-drone-interface.md) |
| **Mock adapter** | Adapter that is itself a simple fake drone: it answers commands and makes up telemetry in-process, with no physics, for tests and development. | [0002](decisions/0002-behavior-depends-only-on-drone-interface.md), renamed in [0010](decisions/0010-code-foundations.md) |
| **Simulator** | A physics-ish model of the drone and room, including noise and drift. | [0002](decisions/0002-behavior-depends-only-on-drone-interface.md) |
| **Behavior** | Decision-making logic that turns sensed state into commands. Never imports cflib. | [0002](decisions/0002-behavior-depends-only-on-drone-interface.md), [0036](decisions/0036-game-logic-is-a-state-machine.md) |
| **Outcome** | What a behavior's tick reports: running, succeeded or failed. Not built yet: today `tick` returns whether the behavior is done, and a behavior reports failure through its own `has_failed`. | [0036](decisions/0036-game-logic-is-a-state-machine.md) |
| **Failure rule** | What a behavior does when a command request is refused or a step runs out of time: stop, land or retry. Game behaviors follow ADR-0020; a behavior written for a field test chooses its own and says so in its docstring. | [0020](decisions/0020-failures-degrade-gracefully.md), [0033](decisions/0033-field-tests-choose-their-failure-rule.md) |
| **Tick** | One iteration of the behavior update loop. | [0003](decisions/0003-tick-loop-timing-model.md) |
| **Tick loop** | The loop that runs ticks at the tick rate: it calls the tick step, then waits for the next due time. It keeps time, measures each tick and watches for hangs, but doesn't know what a tick does. | [0003](decisions/0003-tick-loop-timing-model.md), [0024](decisions/0024-tick-timing-strategy.md), [0026](decisions/0026-tick-loop-calls-one-tick-step.md) |
| **Tick step** | What one tick does, in a fixed order: snapshot, safety pre-check, the take-off and landing update, behaviors, send. The update runs even when the pre-check fails; behaviors don't. The tick loop calls it once per tick. | [0026](decisions/0026-tick-loop-calls-one-tick-step.md), [0055](decisions/0055-take-off-and-landing-update-each-tick.md) |
| **Stop request** | A request from any thread (the interrupt signal, an operator command) for the tick loop to stop after the current tick. The program then disconnects, which lands the drone. | [0026](decisions/0026-tick-loop-calls-one-tick-step.md) |
| **Interrupt signal** | The operating system's request for the program to stop (SIGINT). Ctrl+C in the console sends it, and other tools can too. Python raises it as KeyboardInterrupt on the main thread unless the program handles it. While connecting it stops the program; once connected it makes a stop request. | [0026](decisions/0026-tick-loop-calls-one-tick-step.md), [0028](decisions/0028-programs-bench-first-plain-logging.md) |
| **Hang watchdog** | Detects a tick that runs longer than 1 s and writes every thread's stack trace to the log. It only reports; acting on a hang is backlog #26. | [0026](decisions/0026-tick-loop-calls-one-tick-step.md) |
| **Console** | The text window the program runs in: PyCharm's Run window, or a terminal window. Shows log messages at info level and above; the log file also gets our own debug messages (libraries such as cflib only from info level). | [0026](decisions/0026-tick-loop-calls-one-tick-step.md) |
| **Log level** | How important a log message is: debug (every detail, such as each tick's timing), info (normal events), warning (something went wrong but the program carries on), error (something failed), critical (the most severe). The console and the log file each show messages at or above a chosen level. | [0026](decisions/0026-tick-loop-calls-one-tick-step.md) |
| **Program** | A runnable entry point, such as the bench program. It sets up logging, the drone and the tick loop, then runs until it's done or stopped. | [0028](decisions/0028-programs-bench-first-plain-logging.md) |
| **Bench program** | The program for the Bench field test. It connects to the drone, runs the tick loop and logs every snapshot, but never commands the drone. | [0028](decisions/0028-programs-bench-first-plain-logging.md) |
| **Hover test** | The behavior for the Hover field test: arm, take off (to 0.5 m unless the hover program sets another height), hover, land, then report done. | [0030](decisions/0030-minimal-safety-layer-for-first-flight.md), [0071](decisions/0071-hover-program-sets-the-take-off-height.md) |
| **Hover program** | The program that runs the hover test, like the bench program but flying. | [0030](decisions/0030-minimal-safety-layer-for-first-flight.md) |
| **Failsafe test** | The behavior for the Failsafe low and Failsafe high field tests: arm, take off to the height, and wait for the failsafe to land the drone, during the climb (Failsafe low) or after a hover (Failsafe high). If the fault never takes effect, it lands the drone itself after a time limit and fails. | [0041](decisions/0041-failsafe-tests-inject-a-fault-into-the-pre-check.md), [0049](decisions/0049-failsafe-low-fires-its-fault-during-the-initial-climb.md) |
| **Failsafe program** | The program that runs the failsafe test on the forged low battery drone, with the fault forged during the initial climb (Failsafe low) or after a hover (Failsafe high). The program, not the behavior, judges whether the test passed. | [0041](decisions/0041-failsafe-tests-inject-a-fault-into-the-pre-check.md), [0049](decisions/0049-failsafe-low-fires-its-fault-during-the-initial-climb.md) |
| **Rescue landing program** | The program that does a rescue landing: it takes over the flight and runs a behavior that only lands. The only program allowed to take over a flight. | [0038](decisions/0038-connecting-to-a-flying-drone.md) |
| **Game program** | A program that plays a game (hide-and-seek, catch the bird), as opposed to running a field test. It never takes over a flight and never uses fault injection; fitness functions enforce both. | [0038](decisions/0038-connecting-to-a-flying-drone.md), [0041](decisions/0041-failsafe-tests-inject-a-fault-into-the-pre-check.md) |
| **Test program** | A program that runs a test: the bench, hover and failsafe programs. Only test programs may use fault injection. | [0041](decisions/0041-failsafe-tests-inject-a-fault-into-the-pre-check.md) |
| **Forged low battery drone** | A wrapper around the drone, used only by the failsafe program. It passes everything on unchanged, but once its trigger fires (during the initial climb, or after a hover of a few seconds), it hands out snapshots whose battery voltage is below the low-battery limit. | [0041](decisions/0041-failsafe-tests-inject-a-fault-into-the-pre-check.md), [0049](decisions/0049-failsafe-low-fires-its-fault-during-the-initial-climb.md) |
| **Tick rate** | Ticks per second: 20 Hz. | [0023](decisions/0023-tick-rate-20-hz.md) |
| **Due time** | When a tick should start: the previous due time plus one tick period, or, after an overrun, the moment the late tick ends. | [0024](decisions/0024-tick-timing-strategy.md) |
| **Overrun** | A tick still working at the next due time. The next tick starts at once; missed ticks are skipped, never caught up. Always logged. | [0024](decisions/0024-tick-timing-strategy.md) |
| **Lateness** | How long after its due time a tick actually started. | [0024](decisions/0024-tick-timing-strategy.md) |
| **Work time** | How long a tick's own work took, not counting the wait. | [0024](decisions/0024-tick-timing-strategy.md) |
| **Telemetry buffer** | Thread-safe store of the latest value of each telemetry variable, written in the background as data arrives (by the Crazyflie adapter, or by the mock or simulator). | [0007](decisions/0007-snapshot-blackboard-telemetry-buffer.md) |
| **Snapshot** | Read-only copy of the telemetry buffer, taken at the start of each tick. Every behavior in that tick sees the same snapshot. Each value carries its arrival time (PC clock) and the drone's timestamp. Its time is read after the copy, so no value in it arrived later than that time. | [0007](decisions/0007-snapshot-blackboard-telemetry-buffer.md), [0046](decisions/0046-snapshot-time-read-after-the-copy.md) |
| **Blackboard** | Behavior memory: what behaviors remember across ticks (next waypoint, where an obstacle was last seen). Written by behaviors, persists between ticks. | [0007](decisions/0007-snapshot-blackboard-telemetry-buffer.md) |
| **Safety layer** | The layer between behaviors and the drone interface. It runs the safety pre-check on each snapshot, answers command requests at once, and is the only code that sends commands to the drone, apart from the kill switch ([ADR-0013](decisions/0013-operator-kill-switch.md)) and the forged low battery drone, which only passes them on ([ADR-0041](decisions/0041-failsafe-tests-inject-a-fault-into-the-pre-check.md)): it approves, clamps to the speed envelope, or overrides command requests. | [0008](decisions/0008-drone-interface.md), [0013](decisions/0013-operator-kill-switch.md), [0025](decisions/0025-safety-pre-check-and-command-slots.md) |
| **Operator** | The person supervising a flight from the PC, who can stop or override the drone at any moment. In hide-and-seek, the adult running the game. | [0027](decisions/0027-operator-controls.md) |
| **Operator controls** | The operator's commands during a flight: "land now", "hover" and the kill switch, through Windows hotkeys or an optional PS5 controller. "Land now" and "hover" fail the safety pre-check, so the failsafe lands or holds the drone and no behavior can override them. | [0027](decisions/0027-operator-controls.md) |
| **Kill switch** | The operator's command to cut the motors immediately, executed at any moment, like a cheat command. The one thing that bypasses the safety layer; everything else goes through it. | [0013](decisions/0013-operator-kill-switch.md) |
| **Kill latch** | The program's refusal to arm or take off after the kill switch, until the program is restarted. It backs up the drone lock and says why it refuses. | [0027](decisions/0027-operator-controls.md) |
| **Drone lock** | The drone's own state after an emergency stop: its firmware refuses to fly until the drone is restarted (switched off and on). | [0027](decisions/0027-operator-controls.md) |
| **Initial climb** | The first part of every take-off: a level climb through the bad-flow zone that finds the settle height, then ends at the final descent height. A high-level move then climbs to the target. If the speed hasn't settled just below the cap, or the climb hasn't ended within a time limit, the drone lands. Land, the motor stop, arm and buzzer commands go through; the rest are ignored. It can start without flow, in low light; the safety pre-check doesn't check the velocity uncertainty during it. | [0048](decisions/0048-level-through-the-bad-flow-zone.md), [0054](decisions/0054-a-fresh-estimate-for-every-take-off.md), [0056](decisions/0056-adr-0048-as-built.md) |
| **Settle height** | The down range where, during the initial climb, the horizontal speed estimate first goes under a threshold and stays under it, with the velocity uncertainty low: where flow arrives and becomes trustworthy. Measured on every take-off, and only above 0.10 m, where the firmware's flow model can be right. | [0048](decisions/0048-level-through-the-bad-flow-zone.md), [0054](decisions/0054-a-fresh-estimate-for-every-take-off.md), [0056](decisions/0056-adr-0048-as-built.md) |
| **Low-light warning** | A warning the Crazyflie adapter logs at take-off when the Flow deck's image quality is under a limit, or unknown: the take-off may drift sideways until flow arrives. It never refuses a take-off. | [0054](decisions/0054-a-fresh-estimate-for-every-take-off.md) |
| **Final descent height** | The down range where the final descent starts: the settle height plus a margin, never below a minimum or above a cap. Set on every take-off. Without a take-off (a taken-over flight), the cap. | [0048](decisions/0048-level-through-the-bad-flow-zone.md), [0056](decisions/0056-adr-0048-as-built.md) |
| **Landing approach** | The first landing phase: a high-level move straight down at the estimated position, aimed 5 cm below the final descent height. The final descent starts when the down range reaches that height, or at a backup time if it never does. Skipped when a landing is requested during the initial climb: the final descent starts at once. Was called the planned landing. | [0032](decisions/0032-landing-with-a-go-to.md), [0048](decisions/0048-level-through-the-bad-flow-zone.md), [0049](decisions/0049-failsafe-low-fires-its-fault-during-the-initial-climb.md), [0068](decisions/0068-landing-approach-aims-below-the-final-descent-height.md) |
| **Final descent** | The last part of every landing, after the landing approach (none for a landing during the initial climb): a level descent through the bad-flow zone from the final descent height, until the down range confirms touchdown or a time limit says the drone must be on the floor. Then the motors stop. With no usable down range, a slow high-level descent instead. Land, the motor stop, arm and buzzer commands go through; the rest are ignored. | [0019](decisions/0019-final-descent-when-touchdown-unconfirmed.md), [0048](decisions/0048-level-through-the-bad-flow-zone.md), [0056](decisions/0056-adr-0048-as-built.md) |
| **Landing phase** | Where a landing is: not landing, the landing approach, or the final descent. The Crazyflie adapter holds it. | [0019](decisions/0019-final-descent-when-touchdown-unconfirmed.md), [0048](decisions/0048-level-through-the-bad-flow-zone.md) |
| **Touchdown** | The drone resting on the floor, confirmed by the down range, or assumed when the final descent's time limit runs out. Then the motors stop. | [0012](decisions/0012-landing-confirms-touchdown.md), [0032](decisions/0032-landing-with-a-go-to.md) |
| **Touchdown hold** | How long the down range must stay at or below the touchdown threshold before touchdown is confirmed, so one noisy reading can't confirm it. A higher, missing or stale reading starts it over. | [0019](decisions/0019-final-descent-when-touchdown-unconfirmed.md) |
| **May be flying** | An adapter's judgment of whether the drone could be in the air, so that stopping it needs a landing, not a motor stop. Every snapshot carries it, and the safety pre-check checks the velocity uncertainty only while it's true. In the Crazyflie adapter: not flying if our code hasn't started or taken over a flight since our last motor stop was sent. Otherwise flying, unless a drone status that isn't stale says not flying and the take-off grace is over. In the mock adapter, it always matches the mock's drone status, which has no delay. | [0039](decisions/0039-the-adapter-decides-may-be-flying.md), [0060](decisions/0060-pre-check-flow-while-the-drone-may-be-flying.md) |
| **Take-off grace** | The short time after a take-off is sent when the Crazyflie adapter counts the drone as flying, because the drone status shows a take-off only after a delay. | [0039](decisions/0039-the-adapter-decides-may-be-flying.md) |
| **Command request** | What a behavior asks the drone to do this tick (e.g. a velocity, or fast mode to a point). The safety layer answers at once (approved, clamped or refused, with the reason). At the end of the tick, each command slot's approved request is sent. Never goes directly to the drone. | [0008](decisions/0008-drone-interface.md), [0025](decisions/0025-safety-pre-check-and-command-slots.md) |
| **Command slot** | A group of commands where only one can be active at a time: movement (arm, take off, land, velocity, move to, hover), buzzer, LEDs. A later approved request in the same tick replaces the earlier one, and the replacement is logged as a warning. Each slot's request is sent at the end of the tick. | [0025](decisions/0025-safety-pre-check-and-command-slots.md) |
| **Safety pre-check** | The safety layer's check of each snapshot at the start of the tick, before behaviors run (missing or stale values, a value that isn't finite, low battery, a crash or tumble the drone reports, too much velocity uncertainty while the drone may be flying, outside the initial climb; a geofence later). If it passes, behaviors run and their requests are judged against it; if it fails, behaviors are skipped and the failsafe takes over. | [0025](decisions/0025-safety-pre-check-and-command-slots.md), [0054](decisions/0054-a-fresh-estimate-for-every-take-off.md), [0060](decisions/0060-pre-check-flow-while-the-drone-may-be-flying.md) |
| **Low-battery limit** | The battery voltage below which two battery readings in a row fail the safety pre-check, so the drone lands: 3.2 V. In flight, the reading includes the sag. | [0051](decisions/0051-battery-flight-limit-and-take-off-limit.md), [0069](decisions/0069-low-battery-needs-two-readings-in-a-row.md) |
| **Take-off limit** | The lowest resting voltage at which the safety layer approves a take-off: the low-battery limit plus a sag value, 3.62 V. | [0051](decisions/0051-battery-flight-limit-and-take-off-limit.md) |
| **Verdict** | The safety layer's answer to a command request: approved, clamped (approved with changed values) or refused, with the reason. | [0030](decisions/0030-minimal-safety-layer-for-first-flight.md) |
| **Stamped value** | A telemetry value together with its arrival time (PC clock) and the drone's timestamp (converted to seconds). Every value in a snapshot is stamped, so its age can always be checked. | [0007](decisions/0007-snapshot-blackboard-telemetry-buffer.md) |
| **Stale value** | A stamped value older than the age limit of the code reading it, so too old to trust. Each reader sets its own limit: the safety pre-check's `STALE_AFTER` (`BATTERY_STALE_AFTER` for battery voltage), the Crazyflie adapter's `MAX_READING_AGE`. A stale value stays in the snapshot until a newer one arrives. | [0007](decisions/0007-snapshot-blackboard-telemetry-buffer.md), [0030](decisions/0030-minimal-safety-layer-for-first-flight.md) |
| **Range readings** | The set of six range readings in a snapshot, one per named direction (front, back, left, right, up, down). | [0008](decisions/0008-drone-interface.md) |
| **Drone status** | Flags describing the drone's state as the drone reports it: armed, flying, crashed, tumbled, can arm, locked. Part of the snapshot. Its "flying" lags: it shows a take-off a little late and keeps saying flying for 2 s after the motors stop. "Locked" is the Crazyflie's term: the drone refuses to arm until it's power cycled. | [0008](decisions/0008-drone-interface.md) |
| **Range reading** | The distance a range sensor measures in one direction (front, back, left, right, up, down): either a distance, out of range (clear) or invalid (unknown). Named by its direction for short: the down range. | [0008](decisions/0008-drone-interface.md) |
| **Range status** | Whether a range reading is a *distance* (something detected at a known distance), *out of range* (clear) or *invalid* (unknown). In code: `RangeStatus`, and the reading's field is `status`. Named after the "range status" that the VL53 laser sensors report with each measurement. | [0008](decisions/0008-drone-interface.md) |
| **Range direction** | One of the six named directions a range reading points: front, back, left, right, up, down. Relative to the drone. In code: `RangeDirection`. | [0008](decisions/0008-drone-interface.md) |
| **Clock** | The source of time for the tick loop and adapters. A *real clock* reads the computer's monotonic time; a *sim clock* only advances when told to, so tests and simulations run faster than real time and repeat exactly. Behaviors and the safety layer don't read the clock: they use the snapshot's time. | [0009](decisions/0009-clock-abstraction.md), [0030](decisions/0030-minimal-safety-layer-for-first-flight.md) |
| **Control mode** | How behaviors command motion at a given moment: either steering mode or fast mode. | [0005](decisions/0005-control-modes-steering-and-fast.md) |
| **Steering mode** | The default control mode: velocity commands with obstacle-avoidance steering, slow and controlled. | [0005](decisions/0005-control-modes-steering-and-fast.md) |
| **Fast mode** | Control mode for moving quickly to a target using position commands (`go_to`), with obstacle-avoidance steering disabled. The safety layer stays active and can interrupt it. | [0005](decisions/0005-control-modes-steering-and-fast.md) |
| **Speed envelope** | The maximum speed and acceleration allowed in a control mode. The safety layer may tighten it in the moment but never widen it. | [0005](decisions/0005-control-modes-steering-and-fast.md) |
| **Rescue landing** | Landing a drone a program lost. A new program connects, takes over the flight without resetting the position estimate, and lands it with the normal landing. | [0038](decisions/0038-connecting-to-a-flying-drone.md) |
| **Take over (a flight)** | Connect to a drone that may be flying, without resetting its position estimate, and treat it as flying until it lands. Only the rescue landing program does it. | [0038](decisions/0038-connecting-to-a-flying-drone.md) |
| **Streak** | An unbroken run of the same condition, counted in whatever repeats (ticks, command requests, state packets). It ends the first time the condition doesn't hold. A warning comes once per streak, so a long fault logs once, not every tick. | [0020](decisions/0020-failures-degrade-gracefully.md), [0042](decisions/0042-negative-ages-count-as-fresh.md) |

## Buzzer deck

| Term | Definition | ADR |
|---|---|---|
| **Chirp** | One short sound from the Buzzer deck, about 1 s: the firmware's built-in two-note tune, which stops by itself. A buzzer command, like tone and silence. | [0053](decisions/0053-buzzer-commands-and-a-chirp-hover-test.md) |
| **Tone** | A steady sound from the Buzzer deck at a chosen pitch, until a silence command stops it. | [0053](decisions/0053-buzzer-commands-and-a-chirp-hover-test.md) |

## Testing

| Term | Definition |
|---|---|
| **Fitness function** | A test that enforces a structural rule from an ADR, such as "only the Crazyflie adapter imports cflib". It reads the code, for example its imports, instead of running it, and fails continuous integration when the rule is broken. Fitness functions live in `tests/architecture/`. |
| **Field test** | One test of the real drone (Bench, Failsafe low, Hover, ...), with a goal and pass criteria, planned and recorded in a test log as [docs/field-testing/](field-testing/README.md) describes ([ADR-0033](decisions/0033-field-tests-choose-their-failure-rule.md), [ADR-0043](decisions/0043-how-field-tests-are-organized.md)). |
| **Session** | One trip with one or more field tests, flown in order (for example Bench, Failsafe low, Failsafe high, Hover). Its session doc has the planned order, links to its test logs, and what the next session depends on ([ADR-0043](decisions/0043-how-field-tests-are-organized.md)). |
| **Test log** | The record of one field test: goal, pass criteria, checklist, observations and analysis, tied to the git commit that flew. Observations come from the operator or recorded data, never from an AI. |
| **Failsafe low / Failsafe high** | The field tests that fly the failsafe program: it takes off to 0.5 m (the Hover test's default height), then forges a low battery so the safety layer's failsafe lands the drone. Failsafe low forges it during the initial climb; Failsafe high after a hover of about 3 s ([ADR-0041](decisions/0041-failsafe-tests-inject-a-fault-into-the-pre-check.md), [ADR-0049](decisions/0049-failsafe-low-fires-its-fault-during-the-initial-climb.md)). |
| **Fault injection** | Causing a failure on purpose in a test, to check how the unchanged safety layer responds. The one kind built so far forges values: it replaces values in the snapshot (the forged low battery drone replaces both battery readings, [ADR-0041](decisions/0041-failsafe-tests-inject-a-fault-into-the-pre-check.md), [ADR-0069](decisions/0069-low-battery-needs-two-readings-in-a-row.md)). |
| **Recording** | A file of one run: a header (the git commit, the program, the adapter, the settings, the format version), then each tick's snapshot, command requests and verdicts, events and timing, as JSON Lines. Kept in `recordings/`; chosen ones are committed ([ADR-0034](decisions/0034-recorded-flights-as-json-lines.md)). |
| **Replay** | Feeding a real run's snapshots, tick by tick, through the project's real code without a drone, to see what the code decides and when. Replay tests will do this automatically from recordings ([ADR-0007](decisions/0007-snapshot-blackboard-telemetry-buffer.md), [ADR-0034](decisions/0034-recorded-flights-as-json-lines.md)). |
| **Bug planting** | Deliberately breaking the code a test guards, to check that the test fails. One small change at a time, always removed afterwards and never committed. A test that still passes has a gap. A hand-made form of mutation testing. |

## Milestones

| Term | Definition |
|---|---|
| **First flight** | The project's first milestone: everything up to the drone's first hover through the project's own code (the Hover field test). Code "minimal for First flight" does only what that hover needs. |

## Hide-and-seek

Terms for the first game ([ADR-0016](decisions/0016-first-game-hide-and-seek-drone-lands.md)).

| Term | Definition | ADR |
|---|---|---|
| **Launch point** | The marked spot every round starts from. The drone takes off from it facing a fixed direction, the map is stored relative to it, and it stands in for the waiting area. | [0016](decisions/0016-first-game-hide-and-seek-drone-lands.md) |
| **Waiting area** | Where the player waits during a hiding flight: right behind the launch point, with a safety gate between it and the play area. | [0016](decisions/0016-first-game-hide-and-seek-drone-lands.md) |
| **Play area** | The space the drone flies and hides in. Nobody is in it while the drone flies. | [0016](decisions/0016-first-game-hide-and-seek-drone-lands.md) |
| **Mapping run** | A flight before play, with the play area clear, that builds the map the hiding flights use. Up to about 5 minutes. | [0016](decisions/0016-first-game-hide-and-seek-drone-lands.md) |
| **Hiding spot** | A place on the floor where the drone lands to hide, with at least one wall between it and the launch point. | [0016](decisions/0016-first-game-hide-and-seek-drone-lands.md) |
| **Found** | The player picks up the hidden drone, which shows as the down reading jumping and the motion sensors spiking. The drone lights its LEDs and the PC plays a fanfare. | [0016](decisions/0016-first-game-hide-and-seek-drone-lands.md) |
| **Hint** | Every 15 s until the drone is found, it flashes its LEDs and chirps, so the player can find it. | [0017](decisions/0017-hint-chirps-from-buzzer-deck.md) |

## Catch the bird

Terms for the second game ([ADR-0015](decisions/0015-first-game-catch-the-bird.md), [rules](catch-the-bird.md)).

| Term | Definition | ADR |
|---|---|---|
| **Sky layer** | The height band the drone plays in: above a child's reach, below the ceiling with a margin (about 1.5-2.0 m in a room with a 2.4 m ceiling). | [0015](decisions/0015-first-game-catch-the-bird.md) |
| **Clearance rule** | The drone always keeps about 1 m of clearance below. If something rises toward it, it moves away sideways. | [0015](decisions/0015-first-game-catch-the-bird.md) |
| **Catch** | Scored when the child gets directly under the bird, as seen by the down sensor. The bird reacts and flies to a new spot. | [0015](decisions/0015-first-game-catch-the-bird.md) |

## Deprecated terms

> **Deprecated. Don't use these in new docs or code.** They're kept only so
> older ADRs and commits still make sense. Each one links to the decision
> that replaced it.

| Term | Definition (as it was) | Replaced by |
|---|---|---|
| **Safety query** | A read-only question a behavior asks the safety layer during its decision, e.g. "can I enter fast mode?" It's answered immediately and has no side effects. | [0025](decisions/0025-safety-pre-check-and-command-slots.md) |
| **Negative age** | The age of a value that arrived just after the tick's time, so it's slightly below zero. It counts as fresh. One more negative than a tick period can only be a clock bug, so it's logged as a warning. | [0046](decisions/0046-snapshot-time-read-after-the-copy.md) |
| **Planned landing** | The first landing phase: a high-level move straight down to the floor at the estimated position, timed from the height estimate. When its time is up, the motors stop if touchdown is already confirmed; otherwise the final descent starts. | [0048](decisions/0048-level-through-the-bad-flow-zone.md) |

<!-- Terms still to define as decisions land: command,
     geofence, ... -->
