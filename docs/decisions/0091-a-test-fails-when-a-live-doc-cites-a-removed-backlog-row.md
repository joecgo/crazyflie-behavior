# 0091: A test fails when a live doc cites a removed backlog row

- **Status:** Accepted
- **Date:** 2026-11-24
- **Origin:** AI recommendation accepted.

## Context

Twice on 2026-11-22 removing a backlog row left a pointer to it behind
(M-213, then M-218: #133's removal left #142 waiting "after #133", a
trigger that had fired and that the next-up brief no longer showed). The
guard, searching for the number before removing a row, was a manual step and
failed the second time, so the escalation ladder asks for a mechanism.
Backlog #144.

## Options considered

- **A. A test that reads the live docs:** fails in continuous integration on
  every push, with no step to remember. It needs a rule for when "#N" means a
  backlog row.
- **B. A step in `/wrap-up` and `/decide`:** still a manual step, which is
  what failed twice.
- **C. Leave it to the guard:** no change; the ladder asks for more.

## Decision

**A.** A test fails when a live doc cites a backlog row that no longer
exists. The live places, the ones that say what is still to do:

- the backlog's "Needed by" column;
- the next-up brief, except "Done last";
- the ADR index's Built column;
- the glossary and `ARCHITECTURE.md`;
- `TODO:` comments in `src/`, `tests/` and `tools/`.

The places that are history are skipped, because they cite removed rows
on purpose: ADR bodies, the index's Origin column, the backlog's other
columns, the mistakes log, the work log, `REVIEW.md` and the backlog's notes
files. In the live places, "#N" means a backlog row unless the text calls it
a pull request (a GitHub link, or "pull request #N").

## Consequences

- Removing a row that something still waits on fails the tests, and the
  message names the place to update.
- Writing "#N" for a pull request in a live place needs the words "pull
  request". That's one more convention for whoever writes those docs.
- Backlog #143 (a test for the Built column's "Yes") reads the same index
  and could share its parsing.
- Not built: the test (backlog #153). Until it is, the M-213 guard (search
  for the number before removing a row) still applies.
