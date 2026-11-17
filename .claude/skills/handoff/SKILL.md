---
name: handoff
description: "Passes unfinished work in the crazyflie-behavior repo to a fresh work session: writes a work order to drafts/<item>-handoff.md (the goal, what to read, what's decided and what isn't, the steps, the tests, when to stop and ask, when it's done, the progress so far, and the title the next work session renames itself to, such as W13 (A)), points the next-up brief at it, and gives the user the one line to paste. Use it when the user asks for a hand-off, and at a stopping point once Messages pass about 100k tokens with work left. It never starts a session itself."
---

# Handoff

A fresh work session knows only what it reads. What this conversation
settled (the user's choices, wording they approved, what's done and what's
half done) is lost unless it's written down, and a work session that has to
rebuild it either asks the user again or guesses. A work order carries all
of it in one file, so the next work session starts cheaply and never reopens
a decision.

## When

- The user asks for a hand-off.
- At a stopping point once Messages (`get_usage`) pass about 100k tokens
  with work left (`CLAUDE.local.md`, "Usage limits"). With no work left,
  `/wrap-up brief` is the right tool instead.

## Steps

1. **Record what only this conversation knows.** Mistakes caught and not
   yet logged go in the log now, as `/wrap-up`'s step 2 says, since the next
   work session can't see them. Commit nothing: the order names the
   uncommitted files, and the next work session carries on from the working
   tree. If the user wants the finished parts committed first, that's
   `/wrap-up`'s step 4.
2. **Name the item and the title.** The item is a short kebab-case name for
   the work, such as `c1-console-thread`; the file is
   `drafts/<item>-handoff.md`. If it exists, read it first: the new order
   replaces it and carries over what still holds.
   The title is what the next work session renames itself to, so the user
   can find it in the app's sidebar: this work session's title
   (`get_session` with `self`), then the section's letter in parentheses,
   such as `W13 (A)`. An order with one piece of work is section A; an
   order split into sections, like `drafts/w13-w15-work-orders.md`, gives
   each its letter. A work session already following an order hands off
   the same section with a number: `W13 (B)` hands off as `W13 (B2)`. If
   this work session's title is long or one the app made up, ask the user
   for a short one, such as `W13`.
3. **Write the work order** in the shape below, for a reader who has none of
   this conversation: paths rather than "the file above", and the glossary's
   terms. Carry every decision the next work session needs: with its ADR,
   or, if made in this work session and not recorded yet, the user's choice
   and the date. Give exact text for anything approved (a glossary row, an
   ADR line, a before and after), so it never has to ask again. Keep every
   line, writing "none" where one doesn't apply, so the reader knows it
   wasn't forgotten. A step marked done needs its code and its test (working
   rule 3). The model and effort come from the guide in `CLAUDE.local.md`,
   for the hardest step left.
4. **Point the next-up brief at it.** In `docs/next-up.md`, the "In
   progress" line for this work names the order's path, and the header's
   date and "Uncommitted" are brought up to date. The rest of the brief is
   `/wrap-up`'s. The brief has one writer at a time (`CLAUDE.md`, "One
   writer"): if another work session holds it, say so and leave the brief
   alone.
5. **Give the user the line to paste**, alone in a plain code block, and
   before it the model and effort to switch to, if they differ from this
   work session's:

   ```
   Read drafts/<item>-handoff.md and follow it.
   ```

## The work order's shape

```markdown
# Work order: <item>

- **Written by:** Claude (<model>), <date, Pacific>, in the work session
  "<its title>". Last commit `<hash>`; uncommitted: <files, or nothing>.
- **Title:** `<title>`. Before anything else, rename this work session to it
  (`mcp__ccd_session_mgmt__set_session_title`, session `self`).
- **Goal:** one sentence.
- **Model and effort:** from the guide in CLAUDE.local.md.
- **Read first:** the files and ADRs, by path. Nothing else.
- **Decided already:** each decision with its ADR. Don't reopen these.
- **Not yours to decide:** the open points. Stop and ask Joe at each.
- **Out of scope:** what not to touch, even if it looks wrong. Add those to
  the backlog.
- **Steps:** in commit order. Which commits are move only.
- **Tests:** what to write, and the bugs to plant.
- **Stop and ask if:** the code doesn't match this order; a test you didn't
  change fails; an ADR and this order disagree.
- **Done when:** the checks pass, the review ran at <level>, and the ADR,
  glossary, backlog and mistakes log are up to date.
- **Report back:** what was built, what was left out and why, choices made
  for Joe to confirm, and usage before and after.
- **Progress:** what's done so far, and where (its commit, or uncommitted).
  The work session following this order updates this line after each step,
  and changes nothing else here.
```

Where the rest goes:

- **A decision waiting on the user** goes under "Not yours to decide",
  answerable with a letter and the recommendation marked, as in the brief's
  decision list, so they can answer from their phone. A glossary row waiting
  on their OK goes there with its exact before and after.
- **What this work session owes the user** (an explain-back not yet asked,
  something to tell them) goes under "Report back".

## Rules this keeps

- Never start a session. The next one starts from the line the user pastes.
- No commit, push or pull request without the user's yes.
- The user starts every program on the drone. An order that needs a flight
  gives the command; it never runs it.
- Observations come only from the user or recorded data. An order passes on
  what was observed as the user said it, apart from any analysis.
