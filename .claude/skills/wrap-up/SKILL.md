---
name: wrap-up
description: "Ends a work session in the crazyflie-behavior repo: the work-log row with its hours, the mistakes logged, the backlog updated, the commits proposed in small chunks, a usage note, and the next-up brief (docs/next-up.md) rewritten, with the line the user pastes to start the next work session. Use it whenever the user says they're done, stopping for the day, wrapping up or taking a long break, and at a stopping point once Messages pass about 100k tokens. Argument: brief, to log any mistakes not yet logged, rewrite the next-up brief and give the line to paste, for a stopping point mid-day."
---

# Wrap-up

A work session leaves things the next one needs: hours for the work log,
mistakes for the log, open questions for the backlog, commits, and the
project's state. Recorded at the end, from the conversation at hand, they
cost little. Rebuilt later by a fresh work session, they cost a lot or get
lost. The next-up brief is what a fresh work session reads first, so it can
start from one page instead of the backlog, the glossary and the mistakes
log.

## Arguments

`/wrap-up [brief]`:

- **none:** all six steps.
- **brief:** steps 2 and 6, with no commit. The mistakes go in the log now,
  since the next work session can't see them, and the brief lists what's
  uncommitted. For a stopping point while the day's work goes on, such as
  when the context has grown past about 100k tokens of Messages
  (`CLAUDE.local.md`, "Usage limits").

## Before the steps

**Who writes the shared records.** `CLAUDE.md` gives the mistakes log, the
backlog, `REVIEW.md`, the work log and the next-up brief one writer at a
time, because two work sessions writing one file lose edits. If another work
session is writing them (the user says so, or `git status` shows changes to
them that this work session didn't make), put steps 1, 2, 3 and 6 as text in
`drafts/wrap-up-<date>.md` for that work session to apply, and say so.

**Keep it cheap.** The context is at its largest now, so each step costs
the most it ever will. Take what you can from the conversation you already
have rather than re-reading docs. Batch the reads: one shell call for
`git status`, the diff stat, the work log's top and bottom, and the backlog
rows this work session touched. Do steps 1 to 3, then ask the user
everything at once: the hours figure, the commit list, and a Details entry
if one is worth suggesting.

## Steps

1. **The work-log row** (`docs/worklog.md`), as `CLAUDE.local.md`'s "Work
   log" says. Hours run from the first to the last message, minus any break
   the user announced (from "brb" until they're back) and any gap over 45
   minutes, rounded to the nearest quarter hour. The times are the
   `timestamp` fields, in UTC, of every transcript with messages that day
   (the `.jsonl` files in `~/.claude/projects/<this project's folder>/`);
   convert them to Pacific. Today's row then holds the whole day, so a work
   session that skipped its wrap-up still counts, and none counts twice. A
   day with two milestones has a row for each, with the hours split by what
   each work session worked on. Update the "Time per milestone" table at
   the bottom. The
   summary is very brief: what was worked on, with ADR numbers. Tell the
   user the figure, since time away from the chat isn't in the transcript.
   Suggest a Details entry only for a moment worth revisiting for the
   portfolio, and add it only on a yes.
2. **The mistakes.** Look back over the work session for mistakes caught
   and not yet logged: the user corrected a claim, a bug or a missed case,
   or you found one in a review, a planted bug or a re-read. `CLAUDE.md`'s
   "Integrity" says what counts; a recommendation the user decided against
   doesn't. Add each to `docs/claude-mistakes.md` in the section for who
   caught it, shaped like the newest entry there. Then run
   `.venv\Scripts\python tools/mistakes_log.py write`, which gives the IDs
   and rebuilds the tables, and the script with no argument, which prints
   any problem. If a takeaway applies to code reviews, follow the log's
   escalation ladder. Name the new mistake IDs to the user.
3. **The backlog** (`docs/decision-backlog.md`). Add each open question
   this work session raised (a deferral, an ADR follow-up, an idea for
   later) and each ADR not fully built (`CLAUDE.md`'s definition of done),
   with where it came from and when it's needed. Remove each question
   decided this work session, once its ADR exists; if it has none yet, say
   so and leave the row. A row keeps its question in a line or two; history
   goes to a notes file in `docs/decision-backlog/`.
4. **The commit list.** Propose commits in small, logical chunks: for each,
   the files and the message, which names the ADR it implements. The
   work-log row goes in the chunk it belongs to, or its own. A code chunk
   meets `CLAUDE.md`'s definition of done, or the list says what it lacks:
   run the checks continuous integration runs
   (`.github/workflows/checks.yml`), and a change to the safety layer, the
   Crazyflie adapter or the tick loop needs its `/project-review` (working
   rule 10). `drafts/` is git-ignored, so nothing there is committed. The
   list ends with the brief's own commit, made after step 6. Commit only on
   the user's yes, with the `Co-Authored-By: Claude` trailer and the
   noreply author address `CLAUDE.local.md` gives (check
   `git config user.email` first).
5. **A usage note.** Call `get_usage`, then in a line or two: the 5-hour
   and weekly limits with their reset times in Pacific, the size of
   Messages, and the model and effort the next step needs, from the guide
   in `CLAUDE.local.md`. Warn if a limit passed 80% or weekly use runs
   ahead of the week.
6. **The next-up brief** (`docs/next-up.md`). Rewrite it whole, in the shape
   below, in about 40 lines. It's a snapshot, not a log: drop what's no
   longer true, but keep each undecided question until it's decided,
   however old. A line saying something is built needs its code and test
   (working rule 3). Then make its commit, if step 4's list was approved,
   and ask whether to push. End with the line the user pastes to start the
   next work session, alone in a plain code block:

   ```
   Read docs/next-up.md, then <the next step>.
   ```

## The brief's shape

```markdown
# Next up

The project's state on one page, read first by a fresh work session.
`/wrap-up` rewrites it at the end of each work session.

- **Date:** <date, Pacific>
- **Last commit:** `<hash>` <subject>. Uncommitted: <what, or nothing>.

## Done last

<Two to five bullets: the last work session or day, with ADR numbers.>

## In progress

<Each unfinished piece, with the path of its work order.>

## Next three

1. <The next step, with its model and effort.>
2. <...>
3. <...>

## Decisions waiting on Joe

Answer by number and letter, such as "1A". **Bold** is the recommendation.

1. <The question.> **A.** <option>. B. <option>.

## Last reviewed

`<hash>`, <date>: the last row of `REVIEW.md`'s review log. The next code
review covers everything after it.
```

Each decision is answerable with a letter, so the user can answer from their
phone, several at once. When the questions live in a longer list elsewhere
(a draft's decision list), carry only those the next three things need, and
point to the rest.

## Rules this keeps

- The next work session starts from the line the user pastes. Never start a
  session yourself.
- No commit, push or pull request without the user's yes.
- The work-log row and the brief say what was done. Field results in them
  come only from the user or recorded data.
