# Field testing

> **Status: draft for the architect's review.** The stages, gates and
> environments below are a proposal. Adjust them before the first flight.

Real flights are where the design gets proven or broken. This folder is the
record: every test session gets a log, every log ties back to an exact code
version, and every surprise feeds back into the design. That record, the
progression from "can it hover" to "it runs its behavior in a stranger's house",
is the portfolio story.

## The iteration loop

```
   ┌─► Plan ──► Simulate ──► Fly ──► Record ──► Analyze ──┐
   │   (goal,    (passes in    (follow    (telemetry,  (sim vs real,
   │   checklist) sim first)   checklist)  video, notes) what surprised us)
   └──────────────── Change: code, sim model, or ADR ◄────┘
```

1. **Plan.** Write the session log's *Goal* and *Pass criteria* before flying.
2. **Simulate.** The same code passes in the simulator first. No first runs in the air.
3. **Fly.** Follow the pre-flight checklist. One variable changes per session.
4. **Record.** Telemetry logs, video, and notes written during the session, not after.
5. **Analyze.** Compare with what the simulator predicted. The **sim-to-real gap**
   is the most interesting thing to write about.
6. **Change.** Fix code, improve the simulator's noise and drift model from the
   recorded data, or write an ADR if a design assumption was wrong. Then loop.

UE5 analogy: a playtest loop. Build, playtest, capture, triage, fix. The
difference is that the "engine" (physics, sensors) is the real world, so you
measure it rather than configure it.

## Stages

Each stage has a gate: don't move on until the exit criteria are met in at
least two sessions.

| Stage | Goal | Exit criteria (draft) |
|---|---|---|
| **0. Bench** | Connected, **propellers off**. Telemetry, decks detected, arming and e-stop work. | All sensors stream. E-stop cuts motors every time. |
| **1. Hover** | Take off, hover at 0.5 m, land. | Lands within N cm of the takeoff point. Drift over 60 s measured. |
| **2. Sensor characterization** | Measure noise and drift: range sensors against different surfaces, flow deck over different floors and lighting. | Noise and drift numbers recorded and fed into the simulator. |
| **3. Safety validation** | Deliberately trigger each failsafe: geofence breach, link loss, low battery, stale data, e-stop. | Every failsafe behaves as designed, in flight. |
| **4. First behavior** | Patrol between waypoints and react to an obstacle in a known room. | Completes N patrols without intervention. |
| **5. New environments** | Same behavior in each test environment below. | Results compared across environments, failures explained. |

Stages 2 and 3 are what separate this from a hobby project. They show you
measured the real system and verified safety, instead of hoping.

## Test environments

Each environment gets a short profile, because flight quality depends on it
(the flow deck needs floor texture and light, and range sensors struggle with
glass, mirrors and dark surfaces).

| ID | Description | Why it's interesting |
|---|---|---|
| `home-<room>` | Home rooms | Baseline: known, repeatable. |
| `attic` | Attic | Low ceiling, dim light, uneven floor, heat (battery). A hard case. |
| `away-<n>` | Other people's homes | Unseen layouts, which test generalization. |

Profile each one in its first session log: size, ceiling height, floor
surface, lighting, obstacles, and anything reflective.

## Session logs

One file per session: `sessions/YYYY-MM-DD-<env>-<short-goal>.md`, from
[`session-template.md`](session-template.md).

Every session records the **git commit** (hash) that flew, so any result can be
traced to the exact code. Commit before flying, and never fly uncommitted code.

## Open decision

`.gitignore` currently excludes `logs/`, `flights/` and `*.csv`, so recorded
telemetry wouldn't be in the repo. Replay tests and the portfolio both need
some recorded flights committed. Where they live, in what format, and whether
large files use Git LFS is an architecture decision for an ADR before stage 1.
