# Field testing

> **Status: accepted 2026-11-02.** Reviewed by the architect before First
> flight. Exit criteria are deliberately light for now: add pass or fail
> criteria later, if they're needed at all.

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
   Exempt: **Bench** and **Hover**. Their recordings are what the simulator's
   noise and drift model is built from, so they can't be simulated first. They
   are rehearsed on the mock adapter only.
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

Each stage has a gate: don't move on until its exit criteria are met once.

| Stage | Goal | Exit criteria (draft) |
|---|---|---|
| **Bench** | Connected, **propellers off**. Telemetry and decks detected. | All sensors stream. |
| **Failsafe low** | A program takes off to 0.1 m and injects a fault into the safety pre-check, so the failsafe lands the drone ([ADR-0041](../decisions/0041-failsafe-tests-inject-a-fault-into-the-pre-check.md)). | The drone lands and its motors stop. |
| **Failsafe high** | The same program, from 0.3 m. | The drone lands and its motors stop. |
| **Hover** | Take off, hover at 0.5 m, land. | Any take-off and landing is a success. Drift over 60 s and the take-off-to-landing distance are recorded (no pass or fail on distance). |
| **Sensor characterization** | Measure noise and drift: range sensors against different surfaces, flow deck over different floors and lighting. | Noise and drift numbers recorded and fed into the simulator. |
| **Safety validation** | Deliberately trigger each failsafe: geofence breach, link loss, low battery, stale data, e-stop. | Every failsafe behaves as designed, in flight. |
| **First behavior** | Patrol between waypoints and react to an obstacle in a known room. | Set when this stage is planned. |
| **New environments** | Same behavior in each test environment below. | Results compared across environments, failures explained. |

Sensor characterization and Safety validation are what separate this from a hobby project. They show you
measured the real system and verified safety, instead of hoping.

**After a change** to the safety layer, the Crazyflie adapter or the tick loop,
run Bench, then Failsafe low, then Failsafe high, then Hover again before anything else.

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
surface, lighting (including time of day and sunlight through windows),
obstacles, and anything reflective.

**First flights** (Bench, Failsafe low, Failsafe high, Hover) are flown in a
room at least 3 x 3 m with a textured hard floor (the flow deck needs texture),
a soft landing patch (a mat or carpet) under the drone, and one operator, with
nobody else in the room, no people and no pets.

**The attic and the `away-<n>` homes come only after Safety validation.**
Flying near other people's property before every failsafe is proven is a risk
to them and to the project.

## Session logs

One file per test: `sessions/YYYY-MM-DD-<env>-<short-goal>.md`, from
[`session-template.md`](session-template.md). An outing with several tests
(Bench, Failsafe low, Failsafe high, Hover, flown one after another) gets one
log per test, all with the same date.

The observations and measurements in a log come from the operator or from
recorded data, never from an AI. Analysis is written apart from what was
observed.

Every session records the **git commit** (hash) that flew, so any result can be
traced to the exact code. Commit before flying, and never fly uncommitted code.

After an abnormal end (a crash, an unexpected landing, a failsafe that fired
when it shouldn't have), no more flights that outing. Write it up first.

## Recordings

Each run writes one *recording* (JSON Lines) to the git-ignored `recordings/`
folder. Recordings worth keeping, for replay tests and as field-test evidence,
are committed compressed, without Git LFS
([ADR-0034](../decisions/0034-recorded-flights-as-json-lines.md)).
