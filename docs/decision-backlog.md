# Decision backlog

Open architecture questions, in rough order of when they need deciding. When
one is decided it becomes an ADR in [`decisions/`](decisions/) and is removed
from this list. The ADRs keep their follow-up notes as history; this file is
the live list.

| # | Open question | Came from | Needed by |
|---|---|---|---|
| 1 | **Control modes:** position targets, velocity, or both? How does switching between them work? | [ADR-0003](decisions/0003-tick-loop-timing-model.md) | Before the drone interface |
| 2 | **How drone-agnostic is the interface?** Crazyflie-shaped, generic, or a generic core with Crazyflie extensions? | [ADR-0002](decisions/0002-behavior-depends-only-on-drone-interface.md) | Before the drone interface |
| 3 | **Blackboard design:** one snapshot per tick? How is data age tracked (arrival time vs drone timestamp)? Is behavior memory separate from sensed state? | [ADR-0003](decisions/0003-tick-loop-timing-model.md) | Before the drone interface |
| 4 | **Tick rate**, and telemetry periods per log block (the bandwidth budget). | [ADR-0003](decisions/0003-tick-loop-timing-model.md) | Before the first behavior |
| 5 | **Clock abstraction:** how real vs simulated time is provided, so tests and the simulator run faster than real time. | [ADR-0003](decisions/0003-tick-loop-timing-model.md) | Before the first tests |
| 6 | **Frozen dataclasses by default?** Decide once real code shows how it reads. Likely together with #3. | [ADR-0004](decisions/0004-strict-typing-ruff-and-units-in-names.md) | With #3 |
| 7 | **Recorded flight data:** where it lives, what format, Git LFS or not (`.gitignore` currently blocks it). | [field-testing](field-testing/README.md) | Before field-test stage 1 |
| 8 | **Onboard reflex layer (hybrid):** move time-critical safety (obstacle stop, link-loss land) onto the drone as a firmware app, with behaviors staying on the PC. | Conversation, 2026-10-18 | After first real flights show where latency hurts |
| 9 | **Glossary terms to define** as decisions land: command, snapshot, control mode, geofence, failsafe, recording/replay. | [glossary](glossary.md) | Alongside the related decisions |
