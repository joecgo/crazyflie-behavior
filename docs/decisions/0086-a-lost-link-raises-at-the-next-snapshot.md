# 0086: A lost link raises at the tick's next snapshot, not at every call

- **Status:** Accepted. Amends [ADR-0084](0084-a-lost-link-is-an-error-and-the-firmware-land-is-a-last-resort.md) ("The adapter raises on the tick's next call to it": now at its next snapshot).
- **Date:** 2026-11-22
- **Origin:** Mixed. That a check at the top of every call is easy to forget in a new command, and bloats the adapter: mine, from my review of pull request #29. Checking once, in `take_snapshot()`: AI recommendation accepted.

## Context

As built, each of the 14 Crazyflie adapter methods a tick calls starts with
`_raise_if_the_link_is_lost()`, and the mock adapter's do the same. A new
command that forgets the line sends to a dead link and raises nothing.

## Options considered

- A. Check once per tick, in `take_snapshot()`.
- B. Keep a check in every call, as a decorator, with an architecture test
  that every drone-interface method has it.
- C. The snapshot carries the lost link and the safety layer decides
  (ADR-0084's option B; it waits for backlog #137).

## Decision

A. After a lost link, `take_snapshot()` raises. Every tick starts with it
(the tick's order), so no command needs a check of its own. `_wait_until`
keeps its check, so `connect()`'s waits end at once, and `disconnect()`
still raises for a lost link that no call has raised yet. The mock adapter
does the same.

## Failure modes

- **Inputs:** a link lost after the tick's snapshot: that tick's commands
  are dropped by cflib, or skipped with a warning for a parameter write
  (backlog #61's race still raises cflib's `KeyError`), and the next
  snapshot raises, one tick later; `land()` in flight reads a snapshot of
  its own, so it raises at once. `emergency_stop()` after a lost link no
  longer raises; nothing reached the drone before either (ADR-0084).
- **Never:** a tick after a lost link that gets past its snapshot.

## Consequences

- One check per tick, where nothing can skip it; a new command needs none.
- Checked when built: that every tick step takes a snapshot on every tick,
  the bench's too.
- Tests: `take_snapshot()` raises after a lost link and a command doesn't.
  ADR-0084's tests (a lost link in flight and on the floor ends the run with
  exit 1 and the right log line) stay.
- Glossary: *Lost link* reworded when built (it says every later call a
  tick makes raises; a proposal then). `ARCHITECTURE.md`'s wording on it is
  checked then too.
