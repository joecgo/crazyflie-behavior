# Architecture decisions

Every architecture decision in this project, one line each. Each record
explains the context, the options considered and why this one was chosen.

**Origin** says where the decision came from. I make every decision; the
implementation is AI-assisted (Claude Code), and so are many of the options.
This column is honest about which ideas were mine.

| ADR | Decision | Origin |
|---|---|---|
| [0001](0001-record-architecture-decisions.md) | Record architecture decisions as ADRs | AI recommendation accepted |
| [0002](0002-behavior-depends-only-on-drone-interface.md) | Behavior depends only on the drone interface; only the Crazyflie adapter (and `tools/`) imports cflib | From the original plan |
| [0003](0003-tick-loop-timing-model.md) | Behaviors run in a fixed-rate tick loop | AI recommendation accepted |
| [0004](0004-strict-typing-ruff-and-units-in-names.md) | Strict typing, ruff, SI units inside; suffix only non-SI values and all angles | Mixed: the units rule was mine |
| [0005](0005-control-modes-steering-and-fast.md) | Two control modes: steering mode (velocity) and fast mode (`go_to`) | Mixed: fast mode and request-and-approve were mine |
| [0006](0006-crazyflie-focused-interface.md) | The drone interface is Crazyflie-focused, with generic vocabulary | My idea |
| [0007](0007-snapshot-blackboard-telemetry-buffer.md) | Telemetry buffer, per-tick snapshot, and a separate blackboard | AI recommendation accepted |
| [0008](0008-drone-interface.md) | The drone interface: commands, range readings, safety queries | Mixed: overrode the AI on two points |
| [0009](0009-clock-abstraction.md) | Injected clock; behaviors receive time in the snapshot | AI recommendation accepted |
| [0010](0010-code-foundations.md) | Code foundations: layout, interfaces, tests, first adapters | Mixed: overrode the AI on writing the Crazyflie adapter now |
| [0011](0011-mock-models-setpoint-timeout.md) | The mock adapter models the setpoint timeout | AI recommendation accepted |
| [0012](0012-landing-confirms-touchdown.md) | Motors stop only on confirmed touchdown; the fallback is superseded by 0019 | AI recommendation accepted |
| [0013](0013-operator-kill-switch.md) | The operator's kill switch bypasses the safety layer | Mixed: the need and the exception were mine |
| [0014](0014-debug-visualization-with-rerun.md) | Debug visualization uses Rerun | Mixed: an off-the-shelf tool for now was mine; Rerun was the AI's pick |
| [0015](0015-first-game-catch-the-bird.md) | The first game is Catch the bird (replaces hide-and-seek); now the second game, see 0016 | Mixed: the safety reasoning and flying above reach were mine; the game was the AI's suggestion |
| [0016](0016-first-game-hide-and-seek-drone-lands.md) | The first game is hide-and-seek, where the drone hides and lands | My idea |
| [0017](0017-hint-chirps-from-buzzer-deck.md) | Hint chirps come from a Buzzer deck, not the motors | Mixed: the hints were mine; the Buzzer deck was the AI's recommendation |
| [0018](0018-frozen-dataclasses-with-slots.md) | Data records are frozen dataclasses with slots | Mixed: the AI's earlier recommendation, accepted after my code review |
| [0019](0019-final-descent-when-touchdown-unconfirmed.md) | Only the down range confirms touchdown; otherwise a bounded final descent | Mixed: the review finding and "always land" were mine; the final descent was the AI's |
| [0020](0020-failures-degrade-gracefully.md) | Failures degrade gracefully, and are always logged | Mixed: keeping it going and logging were mine; failing safe was the AI's pushback |
| [0021](0021-drone-status-streams-with-the-state.md) | Drone status streams in one log block with position and velocity | Mixed: found in my review; streaming was the AI's; one full block was mine |
| [0022](0022-multi-ranger-keeps-stock-firmware-rate.md) | The Multi-ranger keeps the stock firmware's 10 Hz | Mixed: keeping it was the AI's recommendation; no follow-up item was mine |
| [0023](0023-tick-rate-20-hz.md) | The tick loop runs at 20 Hz, with telemetry periods matched to their sources | AI recommendation accepted, over my first preference for 30-60 Hz |
| [0024](0024-tick-timing-strategy.md) | Tick timing: due times on a fixed beat, plain sleep, measured jitter | Mixed: starting at once after an overrun was mine; the fixed beat was the AI's tweak |
| [0025](0025-safety-pre-check-and-command-slots.md) | Safety pre-check, requests answered at once, one command per slot per tick | Mixed: the single request call, pre-check and slots were mine |
| [0026](0026-tick-loop-calls-one-tick-step.md) | The tick loop keeps time and calls one tick step; hangs are detected; every tick is logged | Mixed: hang detection and logging every tick were mine; the split was the AI's |
| [0027](0027-operator-controls.md) | Operator controls: Windows hotkeys, an optional PS5 controller, no dead-man mode | Mixed: the inputs and no dead-man mode were mine |
| [0028](0028-programs-bench-first-plain-logging.md) | Programs: a bench program first, plain logging, the mock adapter by default | Mixed: plain logging was mine; the rest were AI recommendations |
| [0029](0029-connecting-has-time-limits.md) | Connecting has time limits: each step waits on a helper thread | AI recommendation accepted, after my question |
| [0030](0030-minimal-safety-layer-for-first-flight.md) | A minimal safety layer for First flight: a pre-check, one failsafe, the hover test's commands | Mixed: asking how small it could be, and one failsafe, were mine |
| [0031](0031-connect-waits-for-first-telemetry.md) | connect() returns only once every telemetry value has arrived | AI recommendation accepted |
| [0032](0032-landing-with-a-go-to.md) | Landing is a go_to down to the floor; our touchdown check stops the motors | My call, keeping in line with ADR-0012 and ADR-0019 (the AI recommended the firmware's landing) |
| [0033](0033-field-tests-choose-their-failure-rule.md) | Behaviors written for field tests choose their own failure rule | Mixed: each test choosing, and the hover test stopping at its first refusal, were mine |
| [0034](0034-recorded-flights-as-json-lines.md) | A recording is one JSON Lines file per run; chosen ones are committed compressed | AI recommendation accepted |
| [0035](0035-console-output-on-a-background-thread.md) | Console output runs on a background thread; log-file writes stay on the tick's thread | Mixed: measuring before deciding was mine; the console-only thread was the AI's |
| [0036](0036-game-logic-is-a-state-machine.md) | Game logic is a state machine per game; a behavior's tick reports an outcome | Mixed: a state machine now, a behavior tree later, was mine |
| [0037](0037-disconnect-does-not-disarm.md) | Disconnecting doesn't disarm; the Crazyflie adapter logs whether the drone arms itself | AI recommendation accepted; turning off auto-arming was mine, deferred |
| [0038](0038-connecting-to-a-flying-drone.md) | Connecting refuses a flying drone; a rescue landing takes over the flight | Mixed: AI recommendations accepted; the full version now and the manual emergency stop were mine |
| [0039](0039-the-adapter-decides-may-be-flying.md) | The adapter decides whether the drone may be flying; hover on the floor does nothing | AI recommendation accepted; splitting it off from backlog #8 was mine |
| [0040](0040-landing-progress-stays-in-take-snapshot.md) | Landing progress stays in take_snapshot for First flight | Mixed: option A was mine, against the AI's recommendation of D |
| [0041](0041-failsafe-tests-inject-a-fault-into-the-pre-check.md) | The Failsafe low and Failsafe high tests inject a fault into the safety pre-check | Mixed: the tests and names were mine; the choice of A was mine after a corrected description; amended for Failsafe high at 0.5 m, mine; the wrapper mechanism was an AI recommendation I accepted |
| [0042](0042-negative-ages-count-as-fresh.md) | Slightly negative ages count as fresh; a large one is a warning; superseded by 0046 | AI recommendation accepted |
| [0043](0043-how-field-tests-are-organized.md) | Field tests are grouped by kind and repeated by rule, with no stage gate; a session is a trip, a field test is one test | My decisions, recorded after the fact |
| [0044](0044-the-bench-is-flown-with-propellers-on.md) | The Bench is flown with the propellers on | My decision, with the AI pushing back on the risk |
| [0045](0045-rescue-without-an-estimate-points-to-the-emergency-stop.md) | A rescue that gets no estimate points to the emergency stop | AI recommendation accepted |
| [0046](0046-snapshot-time-read-after-the-copy.md) | The snapshot's time is read after its values are copied | My idea (ADR-0042's option D, which the AI had advised against) |
| [0047](0047-pinned-firmware-release-warn-on-mismatch.md) | The project pins Crazyflie firmware release 2026.10 (firmware 2026.08); the adapter warns on a mismatch | Mixed: updating first and warning only were mine, over the AI's recommendation to refuse; pinning was the AI's |
| [0048](0048-level-through-the-bad-flow-zone.md) | Take-off and landing cross the bad-flow zone level, above a height found during take-off | Mixed: moving only vertically, a speed, measuring the zone on take-off and the 5 cm margin were mine; the level setpoint, the speed estimate as the measure, the cap and 15 cm were the AI's |
| [0049](0049-failsafe-low-fires-its-fault-during-the-initial-climb.md) | Failsafe low forges its battery fault during the initial climb; a landing during the climb is a final descent | AI recommendation accepted; keeping the name, a new ADR and the climb-landing rule were mine |
| [0050](0050-diagnostic-log-block-to-the-debug-log.md) | A diagnostic log block streams attitude, motor power and flow quality to the debug log only | AI recommendation accepted |

Open questions waiting for a decision: [decision backlog](../decision-backlog.md).
