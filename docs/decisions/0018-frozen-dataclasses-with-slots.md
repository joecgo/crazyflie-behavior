# 0018: Data records are frozen dataclasses with slots

- **Status:** Accepted
- **Date:** 2026-10-23
- **Origin:** Mixed. Frozen by default was the AI's recommendation in ADR-0004, which I deferred; I accepted it, with slots, after reviewing the code.

## Context

ADR-0004 deferred whether dataclasses default to immutable, and ADR-0010 made
the snapshot frozen provisionally, until real code showed how it reads. After
reviewing the snapshot and drone interface code, the pattern reads cleanly.

## Options considered

- **A. Frozen only where needed** (the snapshot): less to remember, but nothing
  stops another record from being changed by accident.
- **B. Frozen and slots for every data record:** values can't change after
  they're made, and a misspelled field is an error. Changing a value means
  making a copy (`dataclasses.replace`).

## Decision

Option B. Every `@dataclass` in `src/` uses `frozen=True, slots=True`. Classes
whose state changes over time (the blackboard, the telemetry buffer, adapters,
the map) are ordinary classes, not dataclasses.

## Consequences

- **Enforced by a fitness function** in `tests/architecture/`: any dataclass in
  `src/` without both options fails. A justified exception goes on a list in
  that test, with its reason.
- **Frozen is shallow:** a frozen record holding a `list` can still have the
  list changed. Frozen records hold only immutable values (numbers, strings,
  enums, tuples, other frozen records).
- `__post_init__` can validate fields but can't assign them.
