# 0025: Safety pre-check, requests answered at once, one command per slot per tick

- **Status:** Accepted. Supersedes decision 6 of [ADR-0008](0008-drone-interface.md) (safety queries).
- **Date:** 2026-10-29
- **Origin:** Mixed. One request function that answers at once, the pre-check before behaviors run, and slots where a later request replaces the earlier one with a warning: mine (slots grew from the AI's "channels"). Sending once at the end of the tick, and logging replacements once per streak: AI recommendations accepted.

## Context

ADR-0008 gave behaviors two calls: a read-only safety query ("can I enter
fast mode?") and then a command request. Designing the tick loop showed that
two calls are more than needed. The safety checks also depend only on the
snapshot, so running them again for every query repeated work (backlog #21).

## Options considered

- **A. Keep ADR-0008:** queries, then requests.
- **B. One request call that answers at once** (approved, clamped or refused,
  with the reason), with the checks done once per tick before behaviors run.

## Decision

Option B. A tick runs in this order:

1. **Snapshot.**
2. **Safety pre-check.** The safety layer checks the snapshot once (stale
   data, battery, geofence). If it fails, behaviors are skipped this tick and
   the failsafe takes the movement slot.
3. **Behaviors make command requests.** Each one is answered at once, judged
   against the pre-check. "Approved" means the safety layer accepted it, not
   that the drone did it: physical outcomes arrive in later snapshots. A
   refused request takes nothing.
4. **Send.** One command per **command slot** (movement; later buzzer and
   LEDs): the slot's approved request, or the failsafe's.

A later approved request in the same slot replaces the earlier one and logs a
warning, once per streak ([ADR-0020](0020-failures-degrade-gracefully.md)),
with every replacement at debug level. The kill switch still bypasses all of
this ([ADR-0013](0013-operator-kill-switch.md)).

## Failure modes

- **Inputs:** a stale or missing snapshot value fails the pre-check, so
  behaviors don't run on it.
- **Backups:** the failsafe runs in the safety layer, on the tick loop's
  thread, so a hung tick stops both (backlog #26). Only the kill switch
  doesn't share that thread.
- **Never:** a command reaching the drone without the safety layer (except
  the kill switch); behaviors running on a failed pre-check; two commands in
  one slot in one tick.
- **Always eventually:** each tick ends with at most one command per slot.

## Consequences

- Which faults fail the pre-check, and each failsafe, are still backlog #8.
  Minor faults might later let behaviors run with limits.
- A behavior that tries options only to compare them must make its real
  request last; if comparing becomes common, a pure check can come back.
- The drone interface has no buzzer or LED commands yet (backlog #5e).
- Backlog #21 (safety-query caching) is closed by the pre-check.
- Glossary: *Safety pre-check* and *Command slot* are new; *Command request*
  and *Safety layer* are reworded; *Safety query* is superseded.
