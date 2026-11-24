# 0089: A golden file of the current format version makes a format change fail the tests until the version goes up

- **Status:** Accepted.
- **Date:** 2026-11-23
- **Origin:** Mixed: the gap was mine (reading pull request #30: nothing
  reminded us to bump `FORMAT_VERSION`); the golden file and the review
  question were an AI recommendation accepted, and keeping only the current
  version's file was the AI's revised recommendation, accepted.

## Context

A recording's format lives in `recording/encoding.py`: an encoder and a
decoder for each record. Its round-trip tests catch a change to one side
only. Rename a field and both sides change together, so they pass while the
recordings made before can't be read back. ADR-0034 named the pitfall
("every format change must bump the version"), but nothing checked it: no
test and no review question (M-222).

## Options considered

- **A. A review question only:** no code, but it relies on the reviewer
  seeing that a change touches the format, and a field renamed in `Snapshot`
  doesn't look like one.
- **B. A golden file for the current format version, and a review
  question:** a test fails on any change to what the code writes; the
  question catches a golden file rewritten to make it pass.
- **C. Every version's golden file, kept and read by today's reader:** old
  recordings stay readable, but the reader must handle every old layout, and
  ADR-0034's open question (what a reader does with an older version) must
  be answered at the first format change.

## Decision

Option B: a mechanism, so a missed bump can't get through on a reviewer's
memory, and only the current version, since no recordings are committed yet
and ADR-0034 leaves older versions to the first replay test.

- **The golden file** is `tests/recording/golden/format_v<N>.jsonl` for the
  current `FORMAT_VERSION` N: made-up data holding every kind of line and
  every value a line can hold (each command request type, flight end reason
  and range status, both verdicts, each event, missing values, the
  non-finite floats, a tick with only its timing, a last line with an
  error). It isn't a real run: it has three flight end reasons.
- **Its tests**, in `tests/recording/test_encoding.py`: it's the only golden
  file, named for the current version; today's reader reads it back as its
  data; today's code, writing that data, gives the file byte for byte, and
  the recorder itself gives the lines one run can hold; and its data has
  each command request type, flight end reason and range status, so a new
  one must join it.
- **A format change** fails them until `FORMAT_VERSION` goes up and a file
  the new code writes replaces the old one. The file is written once per
  version and never edited in place.
- **Review question Q-57** asks about a change to what a recording holds,
  how it's written or what a recorded value means: did the version go up,
  and does the golden file's diff show only that change?

## Consequences

- Any change to the bytes written, even key order or spacing, needs a new
  version: a simple rule, for changes that are rare.
- A change to what a value means (its unit or frame) that leaves the bytes
  alone isn't caught by the tests. Q-57 asks about it.
- **Pitfall accepted:** nothing checks that recordings made under an older
  version still read back. ADR-0034's question of what a reader does with one
  had no backlog row (M-223): now #150, due with the first replay test of a
  committed recording.
- The golden file is written by a one-off command, not a kept script: a
  script that rewrites it on demand invites rewriting it instead of bumping
  the version.
- Focus areas 5 and 6: replay tests need recordings that read back as they
  were written, checked on every push.
- Glossary: *Golden file* added.
