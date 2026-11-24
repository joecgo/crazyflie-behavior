# 0090: A bug-planting tool generates plants for every named limit and runs on demand

- **Status:** Accepted
- **Date:** 2026-11-24
- **Origin:** AI recommendation accepted (the tool generated from the code,
  run on demand, and the coding-style line).

## Context

The boundary audit's script (`drafts/2026-11-21-boundary-audit/mutate.py`)
planted 97 bugs from a hand-written list in about 9 minutes and found 20
limits no test catches. Reading the code had missed them (M-194, M-197,
M-202). A test one tick past a limit missed a limit plus 0.04 s twice
(M-206, M-217), so the escalation ladder asks for a mechanism. Backlog #142.

## Options considered

- **A. The audit's script, cleaned up, with its hand-written list:** simple
  and proven, but a new limit is checked only if someone adds it to the list.
  That is the reading step that missed the 20 gaps.
- **B. A tool that generates its plants from the code:** finds new limits by
  itself, but it's more code to write and test, and it sees named limits
  only, not a typed number.
- **C. An off-the-shelf mutation-testing tool:** the broadest coverage, but a
  new dependency, hundreds of harmless survivors to sort through, and a slow
  run. Windows support not checked. Joe had already said no to a
  mutation-testing dependency for this milestone on 2026-11-21 (D19 of the
  2026-11-13 code recommendations); B and D add no dependency.
- **D. No tool, a coding-style line only:** free, but it relies on the
  reading that missed the gaps.

## Decision

**B, run on demand, plus a coding-style line.**

- `tools/plant_bugs.py` scans `src/` for each comparison against a named
  UPPER_CASE limit. For each one it plants the other comparison (`>` ↔ `>=`,
  `<` ↔ `<=`), and a wrong value. For a time limit it also plants the limit
  plus 0.8 of a tick period, computed from the tick loop's `TICK_RATE`
  (0.8 / 20 Hz = 0.04 s), not typed as a number. That's just under one tick,
  so a test that checks a whole tick past the limit lets it pass. It runs
  the test suite once per plant in a scratch copy and never writes the repo.
- **On demand:** before one of Joe's code reviews, and after a change adds
  or moves a limit. A full run takes minutes, too slow for every push.
- **Known survivors:** a plant that survives on purpose (the value can never
  equal the limit, say) is listed with its reason. The tool fails only on a
  survivor that isn't listed, and reports a listed one that is now caught,
  so the list doesn't go stale.
- **It names the test that caught each plant.** A test that fails at random
  (backlog #139) would otherwise count a gap as caught.
- `docs/coding-style.md`: for a limit, plant the other comparison and, for a
  time limit, the limit plus 0.8 of a tick period. This covers what the tool
  can't see, such as a typed number.

## Consequences

- A new limit is checked the first time the tool runs after it's written.
  No list has to be kept up to date by hand.
- A gap is found only when someone runs the tool. Nothing in continuous
  integration runs it, so the review step has to call for it.
- The tool needs its own tests in `tests/tools/`, proven by bug planting
  like any other test.
- Not built: the tool, its tests, its known-survivors list, and the step
  that runs it before a review (backlog #152). The coding-style line is in.
- Glossary: Survivor (proposed with this ADR); Bug planting names the tool.
