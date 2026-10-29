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

Open questions waiting for a decision: [decision backlog](../decision-backlog.md).
