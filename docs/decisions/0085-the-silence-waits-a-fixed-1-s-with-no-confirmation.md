# 0085: `disconnect()` silences, then waits a fixed 1 s with the link open, with no confirmation

- **Status:** Accepted. Amends [ADR-0083](0083-every-flight-end-lands-inside-the-tick-loop.md) ("A tone (B)": the wait no longer looks for the drone's confirmation, and nothing warns). Not built yet.
- **Date:** 2026-11-22
- **Origin:** Mixed. Dropping the confirmation and its warning, since I hear a tone left on: mine, from my review of pull request #29. Keeping a fixed wait, since closing the link throws away packets not yet sent: the AI's pushback, accepted.

## Context

ADR-0083's silence waits up to 1 s for cflib's parameter update callback and
warns when it doesn't come. That takes an update callback, a flag set on
cflib's thread, and backlog #141 (a confirmation from an earlier write). A
tone left on after a run is heard at the field test, so the warning adds
little. But cflib 0.1.34's `RadioDriver.close()` empties the radio's send
queue (`cflib/crtp/radiodriver.py`, facts register, 2026-11-22): with no wait at all, a silence written
just before the close can be lost.

## Options considered

- A. A fixed 1 s wait with the link open, no confirmation.
- B. No wait: write the silence and close.
- C. As built: wait for the confirmation, up to 1 s, then a warning.

## Decision

A. After its landing, `disconnect()` writes the silence, waits 1 s with the
link open, then closes. Nothing listens for the drone's answer, and nothing
is logged when it doesn't come. The 1 s is ADR-0083's time limit kept as a
fixed wait: a placeholder, not measured. Blocking is fine here: only
`connect()` and `disconnect()` may block.

## Failure modes

- **Inputs:** a silence still queued after 1 s (writes ahead of it, a slow
  radio) is lost: the tone plays until the drone is switched off, and
  nothing logs it. A drone without `sound.effect` keeps its warning (backlog
  #136). After a lost link, no silence, as before.
- **Never:** the link closed straight after the silence write.

## Consequences

- **Risk I accept knowingly:** a tone left on after a run isn't logged; I
  find it by ear.
- Every disconnect with the link up takes 1 s longer, a tone or not.
- Removed when built: the update callback, the confirmation flag, the
  "didn't confirm" warning, their tests, and backlog #141.
- Tests: the silence is written before the close, and the link stays open
  for the 1 s after it. The mock adapter still delivers the writes still
  waiting at `disconnect()`, then silences.
- Glossary: *Silence* reworded when built (a proposal then).
