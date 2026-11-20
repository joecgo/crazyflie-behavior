# 0081: One age limit, `STALE_AFTER` (0.25 s), for every reading but the battery voltage; it moves to the drone interface

- **Status:** Accepted. Amends [ADR-0012](0012-landing-confirms-touchdown.md) (touchdown readings at most 0.5 s old), [ADR-0030](0030-minimal-safety-layer-for-first-flight.md) (where `STALE_AFTER` lives), [ADR-0054](0054-a-fresh-estimate-for-every-take-off.md) and [ADR-0077](0077-initial-climb-ends-at-a-fixed-0-15-m.md) (how fresh the initial climb's flow check must be). Closes backlog #120.
- **Date:** 2026-11-19
- **Origin:** Mixed. 0.25 s for the flow check, and for every other reading the Crazyflie adapter checks: mine, over the AI's recommendation to keep 0.5 s and pin with a test that the velocity uncertainty shares the down range's log block. Moving `STALE_AFTER` into the drone interface so there's one constant: AI recommendation accepted.

## Context

Backlog #120 asked whether the initial climb's flow check should take a
velocity uncertainty up to 0.5 s old (`MAX_READING_AGE`), when the safety
pre-check calls a value stale after 0.25 s (`STALE_AFTER`). No reason for
0.5 s was ever recorded: it was ADR-0012's placeholder for confirming
touchdown ("VERIFY at the bench"), which ADR-0054 reused for the flow check
and ADR-0077 kept. The row's risk, an uncertainty that stalls while the down
range keeps arriving, can't happen today: both come in one log block
(ADR-0054) and one callback writes both.

## Options considered

- **A. Keep 0.5 s, plus a test that the variances stay in the down range's
  log block:** no flight-code change before a field session, but the safety
  argument rests on a fact about the log block, not the check.
- **B. 0.25 s for the flow check only,** in a constant of its own or the
  shared one.
- **C. Check the uncertainty's age against the down range reading that ends
  the climb (within 0.05 s):** states "flow at 0.15 m" exactly, but it's a
  new kind of check and the most code.

## Decision

B, and further: one age limit everywhere. With no documented reason for
0.5 s, a second number is only an inconsistency, and fixing every use now
saves deciding the same question again for touchdown later.

- `STALE_AFTER` (0.25 s, still a placeholder for the bench, ADR-0030) moves
  from `safety_layer.py` to `drone/interface.py`, which both the safety
  layer and the Crazyflie adapter may already import, as with
  `FLOW_VELOCITY_UNCERTAINTY`. No change to the dependency rules.
- `MAX_READING_AGE` goes. Every reading it checked uses `STALE_AFTER`: the
  flow check and its log line, the down range in the initial climb, the
  landing and touchdown, "may be flying", the wait for "not flying" before
  the link closes, and the low-light warning's image quality.
- `BATTERY_STALE_AFTER` (3.0 s, a 1 s stream) stays in the safety layer, the
  only code that reads it.

## Failure modes

- **Inputs:** a reading 0.25-0.5 s old now counts as missing where it used to
  count. Every reader already treats missing the safe way:
  - flow check: no flow, so the drone lands (no change in practice: the
    uncertainty and the down range share a packet, checked every tick);
  - touchdown hold: broken, so the motors stop later, at worst at the final
    descent's time limit, never earlier;
  - landing and final descent: the height is unknown, so ADR-0019's slow
    descent and a longer time limit;
  - "may be flying": flying, so at most a needless landing;
  - waiting for "not flying": keeps waiting, up to its time limit;
  - low-light warning: image quality unknown. That block streams every
    100 ms, so two missed packets give a false warning, which is only a
    warning.
- **Backups:** unchanged. The pre-check and the adapter now read one
  constant, so a wrong value is wrong in both; they were never independent
  in their age limits.
- **Never:** the motors stop on a reading older than 0.25 s; the climb hands
  over on a velocity uncertainty older than 0.25 s.
- **Always eventually:** as ADR-0077 and ADR-0019: a hand-over or a landing
  within 1.5 s of the take-off, and the motors stop.

## Consequences

- **Risk I accept knowingly:** if radio gaps of 0.25-0.5 s happen in flight,
  landings take the slow descent and the motors stop later more often. How
  often such gaps happen hasn't been checked.
- Easier: one number for "too old to trust"; tuning it at the bench moves
  the pre-check, the flow check and touchdown together.
- Code (not built, backlog #130): `drone/interface.py`, `safety_layer.py`,
  `touchdown.py`, `bad_flow_zone.py`, the Crazyflie adapter, and the tests
  that import either constant. A change to the safety layer and the adapter,
  so `/project-review` first.
- Glossary: *Stale value* reworded (proposed with this ADR).
