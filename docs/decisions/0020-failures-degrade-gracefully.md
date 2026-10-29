# 0020: Failures degrade gracefully, and are always logged

- **Status:** Accepted. Amended by [ADR-0026](0026-tick-loop-calls-one-tick-step.md): every overrun gets its own warning, even several in a row.
- **Date:** 2026-10-24
- **Origin:** Mixed. Keeping the experience going and logging failures for examination afterward: my idea, from games. Failing safe when a failure makes flying unsafe: AI pushback I accepted.

## Context

In games, the player experience should never break: a failure is worked
around and logged for later. Reviewing the adapter's status polling showed both
sides of that on a robot. One failed status read would kill the polling thread
for the rest of the flight, and cflib's `read_bitfield()` "keeps going" on a
timeout by quietly returning old or zero data, so the caller never knows. On a
drone, carrying on after some failures means flying blind near people.

## Options considered

- **A. Fail fast:** stop on any error. Simple, but one glitch ends the flight.
- **B. Always keep going,** as in games. Safe in a game; on a drone it can mean
  flying on stale or missing data.
- **C. Keep going when it's safe, fail safe when it isn't, and always log.**

## Decision

Option C.

- **Keep going when it's safe.** A failure that doesn't make flying unsafe (a
  missed packet, a failed read, a missing hint sound) is logged, and the
  program carries on, retrying where it makes sense.
- **Fail safe when it isn't.** A failure that makes flying unsafe (a stale
  position, a lost link, a low battery) hands over to the safety layer's
  failsafe: hover, land or stop. For the player, the round ends gracefully: the
  drone lands and its LEDs turn red, never a crash. Before flight, refusing to
  start with a clear message (like "Flow deck not detected") is graceful too.
- **Never hide a failure.** Errors are never swallowed silently. Every failure
  is logged with why, once per streak rather than every tick, and saved for
  examination after the session.

## Consequences

- Earlier designs already follow it: the final descent always lands
  (ADR-0019), and status now streams instead of being polled (ADR-0021).
- Which faults are which, and the failsafe for each: backlog #8 (safety-layer
  severity levels). Saving logs per session: backlog #11 (recorded flight data).
- **Guarded by ruff:** `BLE001` flags catching every exception without
  re-raising or logging it, and `S110` flags `except Exception: pass`.
- Glossary term: *Failsafe*.
