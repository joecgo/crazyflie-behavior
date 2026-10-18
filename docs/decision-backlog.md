# Decision backlog

Open architecture questions, in rough order of when they need deciding. When
one is decided it becomes an ADR in [`decisions/`](decisions/) and is removed
from this list. The ADRs keep their follow-up notes as history; this file is
the live list.

| # | Open question | Came from | Needed by |
|---|---|---|---|
| 1 | **How drone-agnostic is the interface?** Crazyflie-shaped, generic, or a generic core with Crazyflie extensions? | [ADR-0002](decisions/0002-behavior-depends-only-on-drone-interface.md) | Before the drone interface |
| 2 | **Blackboard design:** one snapshot per tick? How is data age tracked (arrival time vs drone timestamp)? Is behavior memory separate from sensed state? | [ADR-0003](decisions/0003-tick-loop-timing-model.md) | Before the drone interface |
| 3 | **Safety-layer severity levels:** which faults are minor (blend back to steering mode), serious (stop and hover) or critical (land or e-stop), and the response for each. | [ADR-0005](decisions/0005-control-modes-steering-and-fast.md) | Before the safety layer |
| 4 | **Fast-mode approval criteria:** measurable definitions for visibility, tightness of the space, latency and battery. | [ADR-0005](decisions/0005-control-modes-steering-and-fast.md) | Before fast mode is implemented |
| 5 | **Tick rate**, and telemetry periods per log block (the bandwidth budget). | [ADR-0003](decisions/0003-tick-loop-timing-model.md) | Before the first behavior |
| 6 | **Clock abstraction:** how real vs simulated time is provided, so tests and the simulator run faster than real time. | [ADR-0003](decisions/0003-tick-loop-timing-model.md) | Before the first tests |
| 7 | **Frozen dataclasses by default?** Decide once real code shows how it reads. Likely together with #2. | [ADR-0004](decisions/0004-strict-typing-ruff-and-units-in-names.md) | With #2 |
| 8 | **Recorded flight data:** where it lives, what format, Git LFS or not (`.gitignore` currently blocks it). | [field-testing](field-testing/README.md) | Before field-test stage 1 |
| 9 | **Onboard reflex layer (hybrid):** move time-critical safety (obstacle stop, link-loss land) onto the drone as a firmware app, with behaviors staying on the PC. | Conversation, 2026-10-18 | After first real flights show where latency hurts |
| 10 | **Fast-mode override flag** that skips the approval checks (never the safety layer). Only if a real need appears; tests and simulation only. | [ADR-0005](decisions/0005-control-modes-steering-and-fast.md) | Only if needed |
| 11 | **Glossary terms to define** as decisions land: command, snapshot, geofence, failsafe, recording/replay. | [glossary](glossary.md) | Alongside the related decisions |
