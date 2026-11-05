# Field testing

> **Status, updated 2026-11-04:** a vertical slice: one room (the living
> room), working toward hide-and-seek. Pass criteria are light for now. First
> hardware session on 2026-11-04 ([First flight 1](sessions/2026-11-04-first-flight-1.md)):
> the Bench, then three short failsafe flights, each landed by the real
> low-battery failsafe before the forged fault. The rescue landing and the
> emergency-stop script are built
> ([ADR-0038](../decisions/0038-connecting-to-a-flying-drone.md)) and not yet
> run on hardware.

Real flights are where the design gets proven or broken. This folder is the
record: every field test gets a test log and every session a session doc,
every test log ties back to an exact code version, and every surprise feeds
back into the design. That record, the
progression from "can it hover" to "it plays hide-and-seek in the living
room", is the portfolio story.

## The iteration loop

```
   ┌─► Plan ──► Rehearse ──► Fly ──► Record ──► Analyze ──┐
   │   (goal,    (mock run,    (follow    (telemetry,  (prediction vs
   │   checklist) sim if used) checklist)  video, notes) real, surprises)
   └──────────────── Change: code, sim model, or ADR ◄────┘
```

1. **Plan.** Write the test log's *Goal* and *Pass criteria* before flying.
2. **Rehearse.** The same code runs on the mock adapter first, so a plain bug
   fails on the desk, not in the air. A simulator run is optional.
3. **Fly.** Follow the pre-flight checklist. One variable changes per session.
4. **Record.** Telemetry logs, video, and notes written during the session, not after.
5. **Analyze.** Compare with what was predicted. When the simulator was used,
   the **sim-to-real gap** is the most interesting thing to write about.
6. **Change.** Fix code, improve the simulator's noise and drift model from the
   recorded data, or write an ADR if a design assumption was wrong. Then loop.

## Tests

Three kinds: calibration tests measure the drone, safety tests make its
failsafes fire on purpose, and flight tests fly it. The first time through,
each is passed once, in order. [ADR-0043](../decisions/0043-how-field-tests-are-organized.md)
records how the tests are organized, and why there is no gate between them.

### Calibration tests

| Test | Goal | Passed when |
|---|---|---|
| **Bench** | Connected, propellers on ([ADR-0044](../decisions/0044-the-bench-is-flown-with-propellers-on.md)). Telemetry and decks detected. | All sensors stream. |
| **Sensor characterization** | Measure noise and drift in the living room: range sensors against its walls and furniture, the flow deck over its floor, in its usual lighting. | Noise and drift numbers recorded and fed into the simulator. |

### Safety tests

| Test | Goal | Passed when |
|---|---|---|
| **Failsafe low** | A program takes off to 0.1 m and injects a fault into the safety pre-check, so the failsafe lands the drone ([ADR-0041](../decisions/0041-failsafe-tests-inject-a-fault-into-the-pre-check.md)). | The drone lands and its motors stop. |
| **Failsafe high** | The same program, from 0.5 m (the Hover test's height). | The drone lands and its motors stop. |
| **Safety validation** | Deliberately trigger each failsafe: geofence breach, link loss, low battery, stale data, e-stop. | Every failsafe behaves as designed, in flight. |

### Flight tests

| Test | Goal | Passed when |
|---|---|---|
| **Hover** | Take off, hover at 0.5 m, land. | Any take-off and landing is a success. Drift over 60 s and the take-off-to-landing distance are recorded (no pass or fail on distance). |
| **Mapping run** | Map the living room in a mapping run. | Set when this test is planned. |
| **Hide-and-seek** | Play rounds of [hide-and-seek](../hide-and-seek.md) in the living room. | Set when this test is planned. |

## When to repeat a test

- **Calibration tests:** after a change to code that affects the sensor
  readings.
- **Safety tests:** after a change to the safety layer, the Crazyflie adapter
  or the tick loop.
- **Flight tests:** whenever the work on them needs it. Flying one never means
  flying the others again first.

## Test environment

One for now: the living room (ID `living-room`). It's static: nothing moves
while the drone flies.

Flight quality depends on the room (the flow deck needs floor texture and
light, and range sensors struggle with glass, mirrors and dark surfaces), so
the first test log profiles it: size, ceiling height, floor surface,
lighting (including time of day and sunlight through windows), obstacles, and
anything reflective.

**First flights** (Bench, Failsafe low, Failsafe high, Hover) are flown in a
room at least 3 x 3 m with a textured hard floor (the flow deck needs texture),
a soft landing patch (a mat or carpet) under the drone, and one operator, with
nobody else in the room, no people and no pets.

**If a program dies with the drone in the air**
([ADR-0038](../decisions/0038-connecting-to-a-flying-drone.md)): run the
rescue landing (`crazyflie_behavior.programs.rescue_landing --crazyflie`), not
the program that was flying: that one refuses to connect to a flying drone.
If the rescue landing can't bring it down, slide something soft under the drone
and run `tools/emergency_stop.py`: the motors stop at once. The rescue landing
tells you when it is the estimate: if it fails with "Still missing: position
estimate" (or "velocity estimate") and "it can't land under control without
its estimate", go straight to the emergency stop
([ADR-0045](../decisions/0045-rescue-without-an-estimate-points-to-the-emergency-stop.md)).
Both use the radio link, so if the link is why the drone was lost, only the physical backup is
left: fly the early sessions low over a soft mat.

## Sessions and test logs

A **session** is one trip with one or more field tests, flown in order. It has
a doc in `sessions/` (`YYYY-MM-DD-<milestone>-<session#>.md`, from
[`sessions/session-template.md`](sessions/session-template.md)): the plan, the
results and what comes next.

Each **field test** has its own log in `field-tests/`
(`YYYY-MM-DD-<milestone>-<session#>-<test-name>.md`, from
[`field-tests/field-test-template.md`](field-tests/field-test-template.md)). A session of Bench,
Failsafe low, Failsafe high and Hover has four logs and one session doc, all
with the same date.

The observations and measurements in a log come from the operator or from
recorded data, never from an AI. Analysis is written apart from what was
observed.

Every session records the **git commit** (hash) that flew, so any result can be
traced to the exact code. Commit before flying, and never fly uncommitted code.

After an abnormal end (a crash, an unexpected landing, a failsafe that fired
when it shouldn't have), no more flights that session. Write it up first.

## Recordings

Each run writes one *recording* (JSON Lines) to the git-ignored `recordings/`
folder. Recordings worth keeping, for replay tests and as field-test evidence,
are committed compressed, without Git LFS
([ADR-0034](../decisions/0034-recorded-flights-as-json-lines.md)).
