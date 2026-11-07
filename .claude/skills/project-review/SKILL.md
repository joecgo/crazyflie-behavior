---
name: project-review
description: "Code review for the crazyflie-behavior repo: runs /code-review for bugs, then this project's own checks (its ADRs, glossary, failure-handling rules and REVIEW.md checklist) and reports one ranked list. Use it instead of a plain /code-review whenever you review changes in this repo, and always before committing changes to the safety layer, the Crazyflie adapter or the tick loop. Arguments: a level (default high), fresh for a fresh-context clarity read, a step budget (default 20), and an optional target (a commit, range or path)."
---

# Project review

`/code-review` is good at bugs, but it doesn't know this project: it never
reads the ADRs or the glossary, and it skips `REVIEW.md`. Most of what it
missed before the user's second code review was exactly that: a behavior's
failure rule that went against ADR-0020, terms missing from the glossary,
docstrings only their author could follow. This skill runs `/code-review` and
then the project's own checks, and reports them together.

## Arguments

`/project-review [level] [fresh] [budget N] [target]`, in any order:

- **level:** low, medium, high, xhigh or max, passed to `/code-review`.
  Default high, which CLAUDE.md asks for on safety code.
- **fresh:** also run the fresh-context read (step 7). Off unless asked,
  because it starts a separate agent and costs more.
- **target:** a commit, a range or a path, passed to `/code-review`. Default:
  the uncommitted changes, since reviews here run before committing.
- **budget N:** the most steps the review takes, where a step is one round
  of tool calls. Default 20. Check `get_usage` halfway through. At the
  budget, stop and report what you have.

## Keeping it cheap

Every step re-reads the whole conversation, so each one costs more than the
last.

- **Batch reads.** One shell call that prints every diff and function the
  review needs, not one call per file. Read the functions around each hunk,
  not whole unrelated files.
- **Verify only safety and correctness.** Spend steps confirming a finding
  (reading a path to its end, planting a bug, checking a library's source)
  only when it could affect safety or correctness. Report the rest as found:
  verified if the diff itself shows it, plausible otherwise.
- **Ask before subagents.** At xhigh or max, `/code-review` starts subagents
  that the step budget doesn't count. Before running it at those levels, tell
  the user and wait for a yes. Seven of them used up the 5-hour limit on the
  first review of the unpushed ADR-0048 work.

## Steps

Work through them in order, keeping one list of findings. Each finding needs a
file, a line, the claim, and what it costs if it stays.

1. **Scope.** Get the diff the way `/code-review` does, and list the touched
   files. Read new files whole, and changed files by their diff and the
   functions around it.
2. **Bugs.** Run `/code-review` at the level, on the target. Keep its findings
   for step 8 and don't call `ReportFindings` for them: step 8 reports
   everything once.
3. **ADRs.** Find the ADRs that govern the touched code: the ones it cites
   (`ADR-NNNN` in its docstrings and comments), and the ones the index
   (`docs/decisions/README.md`) or the glossary's ADR column ties to its
   module. Read each one, and any later ADR its status line says amends or
   supersedes it. Check the changes against each one's Decision, Never and
   Always eventually. Also flag any rule the code follows that no ADR records,
   such as when to stop, retry or carry on: CLAUDE.md says the user makes
   those decisions, so a rule chosen silently is a finding even if it's good.
4. **Names and comments.** Every term in new or changed names, docstrings and
   comments should be in `docs/glossary.md`, and no definition there should
   contradict what the code now does. A comment that copies a fact owned by
   another module, an ADR or the glossary should point to it instead
   (`docs/coding-style.md`). Read each new docstring as someone who knows only
   the code and the glossary: would it make sense to them?
5. **Failure handling.** For each failure or refusal the changed code handles,
   say whether it stops, retries or carries on, and check that against the
   rules. Most code follows ADR-0020: keep going when it's safe, fail safe
   when it isn't, and always log. A behavior written for a field test chooses
   its own rule and says which in its docstring (ADR-0033).
6. **The checklist.** Read `REVIEW.md` now, since it grows with every review,
   and go through each of its questions for the touched files. Note which ones
   apply.
7. **Fresh-context read, only with `fresh`.** Start one general-purpose agent
   with this brief and nothing else from the conversation: the paths of the
   touched files, and "You haven't seen any discussion of this code. Read
   these files and `docs/glossary.md`. Report every docstring or comment you
   can't understand from the code and the glossary alone, every term that
   isn't in the glossary, and every name that says more or less than its code
   does. Don't look for bugs." Add what it reports to the findings. The point
   is a reader without the author's context, which is what the user brings.
8. **Report.** Merge everything into one list, most severe first: safety and
   correctness, then ADR conflicts, then names, comments and the rest. Drop
   duplicates, and mark each one verified or plausible. Call `ReportFindings`
   once with the full list, including the
   `/code-review` findings, using categories such as `correctness`, `adr`,
   `glossary`, `failure-handling`, `review-checklist` and `clarity`. Don't fix
   anything unless asked: design findings are the user's call.

## Afterwards

- When a finding is confirmed (fixed, or the user agrees it's real) and the
  code was Claude's, add it to `docs/claude-mistakes.md` under "Mistakes
  Claude caught itself" and update its at-a-glance table, as CLAUDE.md asks.
  If its takeaway applies to reviews, add it to `REVIEW.md` as a question.
- After fixes, call `ReportFindings` again with each finding's outcome.
