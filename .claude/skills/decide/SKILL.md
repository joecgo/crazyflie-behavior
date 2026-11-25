---
name: decide
description: "Turns an open question in the crazyflie-behavior repo into the user's decision and its records: searches the backlog, the ADR index and the glossary for the topic; gives lettered options, each with what it fixes and why to choose it, a recommendation and the pitfalls stated plainly; waits for the user's answer; then writes the ADR from the template, its index row with the Built column, the glossary proposal, the backlog change and a row for anything left unbuilt, and asks one explain-back question (or adds it to the next-up brief once the context is large). Use it whenever an architectural question needs deciding (an interface, a module boundary, data flow, timing and threading, units and frames, error and safety strategy, test strategy, a dependency), when a backlog row comes up for deciding, and when a request conflicts with an accepted ADR. It writes no code. Argument: the question in a few words, or a backlog row number such as #58."
---

# Decide

The user is the architect: every design decision is theirs, and the ADR is
its record. Each part of this skill guards against a way that goes wrong. A
decision made without searching first repeats or contradicts an earlier ADR.
Options without their pitfalls let the user agree to a risk they didn't see.
A choice settled while writing, not asked, is a decision the user never made.
And a decision left in the conversation is lost. So the order is fixed:
search, options, wait for the answer, then the records.

## Arguments

`/decide <question | #row>`: the open question in a few words, or a backlog
row number. With neither, ask which question.

## Keeping it cheap

Batch the search into one shell call: grep the backlog, its notes files, the
ADR index and the glossary for the topic's words and a few synonyms, and
print the backlog row if one was named. Then read in full only the ADRs and
code the hits point to.

## Steps

1. **Search** (working rules 5 and 6). Look in `docs/decision-backlog.md`
   and its notes files in `docs/decision-backlog/`, the index in
   `docs/decisions/README.md`, and `docs/glossary.md`. Read each ADR the
   search turns up, not its title or index line (working rule 2), and the
   code the question touches when the options depend on it. A fact about
   the firmware, cflib, Python, Windows or the hardware comes from the facts
   register, or the source, or is marked not checked (working rule 1).
   - If an accepted ADR already answers the question, say so and stop.
   - If the question would change an accepted ADR, say which; the new ADR
     supersedes it (`CLAUDE.md`, "Roles").
2. **The options.** Letter them A, B, C. For each: how it works, what it
   fixes, why to choose it, and what it costs. Then the recommendation and
   why. Name the focus areas the question touches (`CLAUDE.md`, "Focus
   areas") and say where an option ignores one. Use the glossary's terms; a
   term the options need and the glossary lacks is proposed with its exact
   row, as step 7 says.
3. **The pitfalls**, stated plainly: push back, then defer.
   - **For a safety decision** (flight, landing, failsafes, the safety
     layer): for each input, what happens if it's missing, stale or wrong;
     whether any backup fails together with what it backs up (a shared
     sensor, estimate or thread); what must never happen; and what must
     always eventually happen. This is where past safety designs failed, and
     it becomes the ADR's "Failure modes".
   - **Portability:** if an option would let a Crazyflie-only concept reach
     behavior code, raise it as a portability decision (`CLAUDE.md`,
     "Portability checkpoints").
4. **Wait for the user.** The user often answers from a phone, so each
   question is answerable with a letter or a word, the recommended option
   first and marked. A choice made while writing the options (a threshold,
   a name, a scope) is its own question, or listed for the user to confirm
   (working rule 8). If the user picks an option with a known pitfall, say
   so once, concretely; then record their choice and the risk they accepted.
   Write nothing until the answer.
5. **The ADR.** `docs/decisions/<NNNN>-<the-decision-in-kebab-case>.md`,
   numbered one past the highest in the folder, from `0000-template.md`.
   About one screen.
   - The title states the decision. Status Accepted; the date in Pacific.
   - **Origin**, honestly: whose idea each part was, in the shape of the
     index's lines (My idea; AI recommendation accepted; AI recommendation
     overridden; Mixed, saying which part was whose).
   - **Decision** in the user's reasoning and words, with any risk they
     accepted.
   - **Failure modes** for a safety decision, from step 3; otherwise delete
     the section.
   - **Consequences:** what gets easier or harder, the follow-ups (each also
     a backlog row, step 8), and the glossary changes.
   - **Superseding an ADR:** the old one's Status becomes "Superseded by
     [NNNN](...)"; its index row's Decision ends "; superseded by NNNN" and
     its Built becomes Superseded. The rest of the old ADR stays as history.
6. **The index row** in `docs/decisions/README.md`: the link, the decision
   in one line, the Origin in short, and Built as the index's top paragraph
   defines it. This skill writes no code, so a decision that needs code is
   "No", naming the backlog row from step 8; a process decision is n/a.
7. **The glossary.** Each term the decision adds, rewords or deprecates:
   show the exact before and after, and edit only on the user's OK. A
   deprecated term moves to "Deprecated terms" with the ADR that replaced
   it.
8. **The backlog.** It has one writer at a time (`CLAUDE.md`, "One
   writer"): if another work session holds it, write this step as text in
   `drafts/decide-<NNNN>-backlog.md` and say so.
   - Remove the row the decision answers. If it has a notes file, the ADR's
     Context links it, and the file stays as history.
   - Add a row for each follow-up, and for each part of the ADR not built
     yet (code, tests, a fitness function for a structural rule), saying
     where it came from (the ADR) and when it's needed. A new row takes the
     next number after the highest ever used, from git history if a higher
     row was removed: ADRs and commits cite rows by number.
   Then add the decision to `docs/review-queue.md` ("Decisions"), under the
   same one-writer rule.
9. **Report.** The files written, and the choices made while writing them,
   for the user to confirm (working rule 8).
10. **One explain-back question** about the decision, using only terms the
    user knows; define a new one briefly first. If the answer is incomplete,
    say what's right and give one hint, then let the user try once more.
    The full answer comes after the second try. Ask it now only while
    Messages are under about 50k tokens; otherwise add it to the next-up
    brief, as `CLAUDE.local.md`'s "Deferred explain-backs" says.

## Rules this keeps

- The user decides. Nothing is settled silently, in the ADR or anywhere
  else.
- It writes no code. The code comes in its own change, whose commit message
  names the ADR (`CLAUDE.md`, "Definition of done").
- No commit, push or pull request without the user's yes.
- It starts no session. Building the decision happens in this work session
  or through `/handoff`.
- Observations come only from the user or recorded data. An ADR that rests
  on a field result cites its test log; it never states one of its own.
