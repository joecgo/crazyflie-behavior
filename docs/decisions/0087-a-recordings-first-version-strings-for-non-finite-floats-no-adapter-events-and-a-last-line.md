# 0087: A recording's first version writes non-finite floats as strings, records no adapter events and ends with how the run ended; old logs are converted on demand

- **Status:** Accepted. Amends [ADR-0034](0034-recorded-flights-as-json-lines.md) (fills in details it left open).
- **Date:** 2026-11-22
- **Origin:** AI recommendation accepted, for all four parts (D10 to D12 of
  the 2026-11-13 codebase review, `drafts/2026-11-13-code-recommendations.md`,
  and backlog #137).

## Context

ADR-0034 fixed the recording's format: JSON Lines, a header, then one line per
tick. Before the recorder is built, four details need settling: how a value
that isn't finite is written, which events the first version records, whether
a lost link reaches the recording (backlog #137), and what happens to the
flights so far, which exist only as text logs. On 2026-11-22 there were 125
such logs with snapshot lines (2026-10-30 to 11-14, sessions 1 to 6), in 6
different snapshot formats, counted from the field names of each log's first
snapshot line.

## Options considered

- **Values that aren't finite:** (A) the strings `"nan"`, `"inf"`, `"-inf"`;
  (B) Python's `NaN` and `Infinity` tokens, which `json` writes and reads by
  default (checked in Python 3.12.10) but which aren't standard JSON; (C)
  `null`, which already means a missing value.
- **Events:** (A) only what the tick step and the safety layer know; (B) also
  the adapter's landing phases, which needs a drone interface addition.
- **A lost link:** a last line saying how the run ended, or keep #137 open.
- **Old logs:** (A) convert all now; (B) only new flights get recordings; (C)
  convert chosen flights when a replay test needs one.

## Decision

- **Values that aren't finite are the strings** `"nan"`, `"inf"` and `"-inf"`.
  Every JSON reader can read the file, and NaN stays different from missing
  (`null`), so a replay feeds the code exactly what it saw. ADR-0030's rule
  depends on that difference. The decoder knows each field's type, and the
  test that every snapshot field has an encoding guards this too.
- **Events: the tick step's and the safety layer's only.** These are the safety
  pre-check's failure reasons, the flight end reason and replaced requests. The
  drone interface doesn't change. The adapter's landing approach, final
  descent and touchdown aren't recorded yet: the snapshot carries only
  `is_in_initial_climb` and `may_be_flying`.
- **The last line says how the run ended:** normally, or the error that ended
  it, such as a lost link (ADR-0084, ADR-0086). The program writes it. The
  snapshot gets no lost-link field, since no tick runs after a lost link.
  This answers backlog #137.
- **Old logs are converted on demand:** a flight is converted when a replay
  test needs it, and the converter handles only that log's snapshot format.
  Its output is marked as converted, with its own format version.

## Consequences

- **Pitfall accepted:** the touchdown detector's replay has no recorded
  touchdown to compare with until the adapter's events are added. Adding
  them bumps the format version. Backlog #146: the adapter's events in
  recordings, before that replay test.
- A converted recording has no verdicts, and lacks the fields its log's format
  didn't have. It suits the detector replays and analysis, not decision
  replay, unless its format had every field.
- A tool reading the raw file without the decoder sees a string where a
  number should be.
- Backlog #137 is closed. The recorder itself isn't built: backlog #145.
- Glossary: *Recording* gains the last line and the converted mark.
