# 0043: Field tests are grouped by kind and repeated by rule, with no stage gate; a session is a trip, a field test is one test

- **Status:** Accepted
- **Date:** 2026-11-03 (the decisions are from 2026-11-02, and the words from 2026-11-03; recorded after the fact)
- **Origin:** Joe's decisions, recorded after the fact. Who suggested each part isn't recorded. The split between *field test* and *session*: my usage; the AI proposed the split.

## Context

The field-testing README ([`docs/field-testing/`](../field-testing/README.md))
had a ladder of stages, each passed before the next, a gate between two of
them, and a simulator run required before most field tests. Revising it on
2026-11-02, I changed how the tests are organized. The sources are that
README and its commits (`f001895`, `6622b8e`, `7ec3ec2`, `0cc9dff`).

## Options considered

- **A. Keep the stage ladder and its gate,** and require a simulator run before
  every field test (how the README was).
- **B. Group the tests by kind, pass each once in order, repeat by rule, and
  use the simulator where it adds something.**

## Decision

B.

- **No stage ladder, no gate.** Tests are grouped as *calibration* (Bench,
  Sensor characterization), *safety* (Failsafe low, Failsafe high, Safety
  validation) and *flight* (Hover, Mapping run, Hide-and-seek). The first time
  through, each is passed once, in order.
- **When to repeat:** calibration tests after changes to code that affects
  sensor readings, safety tests after changes to the safety layer, the
  Crazyflie adapter or the tick loop, flight tests when the work needs them.
- **A vertical slice:** one test environment, the living room (static while the
  drone flies), toward hide-and-seek ([ADR-0016](0016-first-game-hide-and-seek-drone-lands.md)).
- **The simulator is used a lot, but isn't a required step for every field
  test.** Calibration and safety tests that gain nothing from a simulator run
  skip it. The same code always runs on the mock adapter first. The Hover and
  Failsafe tests run on the mock adapter only, with no simulator.
- **The field-testing README keeps a dated status brief** (CLAUDE.md).
- **Environments are reusable docs** in `docs/field-testing/environments/`
  (see `living-room.md`): locations with floor and ceiling height, and lighting
  setups. A test log links to one and adds its own note (time of day, sunlight).
- **Words:** a **field test** is one test (Bench, Failsafe low, ...) and gets a
  **test log**. A **session** is a trip with one or more field tests (for
  example Bench, Failsafe low, Failsafe high, Hover, in order) and gets a
  **session doc**: the planned order, links to its test logs, and what the next
  session depends on. "Outing" isn't used.

## Consequences

- **Risk: no simulator prediction.** A test that skips the simulator has no
  simulator prediction to compare its flight against (focus area 5). The plan
  is to use the simulator wherever it adds something.
- **Risk I accept knowingly:** with no gate, a test passes once the first time
  through, so a lucky pass or a later regression is caught only when a repeat
  rule is followed. My reasoning: this is a side project, not a full-time job.
  A strict suite before every flight I want to do isn't practical, and the time
  is for learning, exploring and trying new things. I retest occasionally,
  guided by the repeat rules, without being bound by them.
- ADR-0010 and ADR-0028 still say "field-test stage 0". They stay as written:
  they're a historical record.
- Glossary: *Field test* is reworded to one test, and *Session* and *Test log*
  are new. They're proposed in the pull request that records this ADR, not yet
  in the glossary.
