# 0092: Cited analysis scripts are committed to `analysis/`, and the snapshot line goes after the first recorded session

- **Status:** Accepted. Amends [ADR-0034](0034-recorded-flights-as-json-lines.md): when the text log drops its snapshot line.
- **Date:** 2026-11-24
- **Origin:** Mixed: asking about every new analysis script was Joe's idea; the two tiers, the snapshot line's timing and reading recordings only were an AI recommendation accepted.

## Context

Field-test analysis scripts live in `drafts/`, which is git-ignored, so a test
log's numbers and charts can't be rerun from the repo (backlog #55). They
parse the text log's snapshot line, the printed snapshot that ADR-0034 said
the text log would drop once recordings exist. No real flight has made a
recording yet. Recordings don't yet hold the landing phases (backlog #146) or
the adapter's debug blocks, which stay in the text log. The old scripts' text
logs aren't committed, so committing those scripts would let no one rerun
them.

## Options considered

- **Where scripts live.** A: stay in `drafts/`. B: commit every script, type
  checked. C: two tiers, committing only scripts a committed doc cites.
- **When the snapshot line goes.** A: now, as ADR-0034 said. B: after the
  first session that records, once its recordings are checked. C: never, as
  a backup.
- **An analysis that needs the text log.** a: stays in `drafts/` until #146.
  b: the text log is committed beside its recording.

## Decision

**C, B and a.**

- **Two tiers.** Exploring stays in `drafts/<session>/`. A script whose
  number or chart a committed doc cites is committed to `analysis/` in the
  same change, and reads only committed recordings, through the project's
  recording reader. That way the doc, the script and its data are all in the
  repo, and analysis and replay tests share one reader instead of a second
  parser of log text.
- **Claude asks.** Each time Claude writes a new analysis script, it asks
  Joe whether to commit it: at the end of the task, in one choice dialog
  for all of them (working rule 8). A script a committed doc cites is marked
  so. If Joe keeps one out, the doc cites it as `drafts/` (not in the
  repository), as test logs did before this ADR.
- **Checks.** Scripts in `analysis/` pass ruff and pyright strict. Shared
  helpers have tests in `tests/analysis/`. Fitness functions: `src/` never
  imports `analysis/`, and `analysis/` never imports cflib. Continuous
  integration doesn't run the scripts yet.
- **Not `tools/`.** A tool may use cflib (glossary: Tool). Analysis never
  touches the drone, and its own folder lets a test forbid cflib there.
- **The snapshot line** stays through the first field session that records.
  That session's debrief checks the recordings against the text log: every
  tick is there, with the same values. Once they match, the line goes from
  the tick step and the bench program. If they don't match, the line stays
  until the recorder is fixed. A recorder bug stops the recording, not the
  flight (ADR-0088), so until a flight has proven the recorder, the text log
  keeps the snapshots.
- **Text-log analysis** (landing phases, debug blocks) stays in `drafts/`
  until #146 puts the landing phases in the recording.
- The old scripts stay in `drafts/`: their logs aren't committed.

## Consequences

- Any number a committed doc cites can be rerun from the repo, and a reader
  can check it (focus area 7).
- A debrief commits the recordings its numbers come from, and the cited
  scripts are strictly typed. That's slower and costs more usage than drafts.
- **Pitfall accepted:** "cite it, commit it" can be forgotten. The ask is
  the guard.
- **Pitfall accepted:** until #146, a landing analysis can't be rerun from
  the repo.
- **Pitfall accepted:** one more session pays for the snapshot line's write
  on the tick thread, about 1.6 KB per tick (ADR-0034, measured 2026-10-30).
- The reader opened plain `.jsonl` only; committed recordings are
  compressed, so it reads `.gz` too.
- The ask is in `CLAUDE.md` and `/debrief`. Built with it (backlog #154):
  the folder, its checks and fitness functions, and `.gz` reading. Not
  built: dropping the snapshot line (backlog #155); a test that runs every
  committed script (backlog #156).
- Glossary: *Analysis script* added.
