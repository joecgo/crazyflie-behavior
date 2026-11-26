# 0088: The recorder sits in the tick step, takes the tick's timing from a callable the tick loop calls, and never stops a flight

- **Status:** Accepted
- **Date:** 2026-11-22
- **Origin:** AI recommendation accepted, for all four parts (C5 part 2 of
  the 2026-11-13 codebase review, `drafts/2026-11-13-code-recommendations.md`,
  and backlog #145). The "As built" choices (2026-11-22, while coding): AI
  recommendations accepted.

## Context

[ADR-0034](0034-recorded-flights-as-json-lines.md) and
[ADR-0087](0087-a-recordings-first-version-strings-for-non-finite-floats-no-adapter-events-and-a-last-line.md)
fixed what a recording holds. Before the recorder is built, four questions
about how the code produces it need answers. Where does it get each tick's
requests, verdicts and events? How does the tick's timing reach it, when only
the tick loop knows that timing and the tick loop may import only the clock?
What are the header's settings? And how is the file written, and what does a
write error do in flight?

## Options considered

- **Where it plugs in:** (A) the tick step holds an optional recorder and
  wraps `ask`, and the safety layer gains a read-only property for this
  tick's events; (B) the safety layer records everything itself; (C) a
  recording tick step that wraps the real one.
- **The tick's timing:** (A) an optional callable the tick loop calls,
  `on_tick_measured(lateness, work_time)`, so each tick is one line; (B)
  record only `time` and `dt`; (C) a second line per tick for the timing.
- **The header's settings:** (A) the commit, whether the tree was clean, the
  program's command-line arguments, the adapter and the format version;
  (B) build C7 phase 1 now and record every tuning constant; (C) none in
  version 1.
- **Writing:** (A) write and flush on the tick's thread, and on an error
  log once, stop recording and keep flying; (B) the same, but an error rises
  and the drone lands; (C) a background writer thread.

## Decision

All four A.

- **The tick step holds an optional recorder.** It gives the behavior a
  wrapped `ask` that records each command request with its verdict, then,
  after the send, reads this tick's events from the safety layer: the
  pre-check's failure reasons and replaced requests, through one new
  read-only property, and the flight end reason, which it already exposes.
  The safety layer does no file work and doesn't know about recording, and
  one place sees the whole tick.
- **The tick loop takes an optional `on_tick_measured(lateness, work_time)`,**
  a plain callable the program points at the recorder. The recorder holds
  the tick step's part of the line and writes the whole line when the timing
  arrives. The tick loop still imports only the clock. The callable runs
  from the loop's `finally`, so a tick that raised still gets its line.
- **The header's settings are what a clean commit doesn't already fix:**
  the command-line arguments. With them go the commit, whether the tree was
  clean, the program, the adapter and the format version. Every constant
  follows from a clean commit, so grouping and logging the tuning values
  (C7) stays its own decision.
- **One write and a flush per tick, on the tick's thread.** That costs about
  what the snapshot log line it replaces costs: Python's log file handler
  already writes and flushes every line on the thread that logs. A write
  error is logged once, recording stops, and the flight goes on. The
  recording isn't needed for safety, so carrying on is safe (ADR-0020).
- **As built (2026-11-22):**
  - The file is opened as new only (Python's file mode "x"): a second run
    in the same second records nothing and logs why, so it never overwrites
    or mixes into another run's recording.
  - The recorder catches any `Exception`, not only a disk error, so a bug in
    the encoding can't end a flight either. It's logged with its stack trace.
  - The flight end reason is recorded once, on the tick it was set.
  - A tick whose snapshot raised still gets a line, with its timing only.
  - The reader is strict: exact keys, no format version newer than it knows,
    no NaN tokens. Only a cut-off last line is dropped.

## Failure modes

- **Inputs:** a write that fails (a full disk, a removed drive) stops the
  recording, not the flight. A disk that stalls delays the tick: the hang
  watchdog reports a stall past 1 s, and the next tick's lateness shows a
  shorter one.
- **Backups:** the text log is written on the same thread to the same disk,
  so a disk failure may take both. The console still shows warnings and
  above (ADR-0035).
- **Never:** a recorder error ends a flight or skips the tick's send.
- **Always eventually:** the drone lands as it would without a recorder.
  The last line is written if the file can still be written.

## Consequences

- **Pitfall accepted:** the write falls outside the tick's measured work
  time, so a slow write shows only as the next tick's lateness.
- **Pitfall accepted:** a flight from a dirty tree can't be tied to exact
  values. The header says the tree wasn't clean, and a replay test can
  refuse such a recording.
- The safety layer gains one read-only property, and the tick loop gains one
  optional argument. Without a recorder, both behave as they do now.
- A recording ends early after a write error. The text log says why.
- `ARCHITECTURE.md`'s target row for recordings changes once this is built.
- Backlog #145 (build it) now has these points settled. #147: the tuning
  values, grouped and logged with every run (C7).
- Glossary: *Recorder* added.
