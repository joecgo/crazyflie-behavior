# 0034: A recording is one JSON Lines file per run; chosen ones are committed compressed

- **Status:** Accepted
- **Date:** 2026-11-01
- **Origin:** AI recommendation accepted.

## Context

Replaying recorded flights in automated tests (focus area 5) needs the
recorded data somewhere, in a format a test can read back. Today the run log
writes the whole snapshot every tick at debug level: about 1.6 KB per tick,
about 13 MB for a 7-minute flight at 20 Hz (measured 2026-10-30), as text
meant for people, not for replay. `.gitignore` blocks recorded data. Backlog
#11 asked where it lives, in what format, and whether to use Git LFS.

## Options considered

- **A. Keep the text log** and parse it for replay: nothing new, but parsing
  log lines is fragile, and the log is already large.
- **B. JSON Lines, one file per run:** one JSON object per line, readable
  with the standard library, appendable as the run goes, and a crash loses
  at most the last line.
- **C. A binary format** (for example NumPy or Parquet): smaller, but a new
  dependency and not readable by eye.
- **Storage:** Git LFS for every recording, or a git-ignored folder with
  chosen recordings committed compressed.

## Decision

Option B, with a git-ignored folder.

- **One recording per run**, in `recordings/`: a header line (the git
  commit, the program, the adapter, the settings, the format version), then
  one line per tick: the snapshot, the command requests and their verdicts,
  the events and the tick's timing.
- **Chosen recordings are committed compressed**, for replay tests and as
  field-test evidence. No Git LFS: a few compressed files don't need it, and
  it adds a service and a quota.
- **The text log drops its per-tick snapshot line,** since the recording now
  holds it. The text log stays for people.

## Consequences

- **Pitfall: the format version.** A replay test reads recordings made by
  older code, so every format change must bump the version. What a reader
  does with an old version is decided with the first replay test.
- Writing the recording joins the logging question: it must never block the
  tick (ADR-0026, [ADR-0035](0035-console-output-on-a-background-thread.md)).
- `.gitignore` changes to ignore `recordings/` but allow the committed,
  compressed ones.
- Glossary: *Recording* added. Backlog #11 is closed.
