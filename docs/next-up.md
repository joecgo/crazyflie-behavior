# Next up

The project's state on one page, read first by a fresh work session.
`/wrap-up` rewrites it at the end of each work session.

- **Date:** 2026-11-16 (Pacific)
- **Last commit:** `17ab8b5` Mistakes log: M-160, M-161, on branch
  `w13-project-skills`, in pull request #23 into `main` for Joe's review.
  Uncommitted: nothing.

## Done last

- 2026-11-16: a small review of pull request #23's code. Four fixes to
  `tools/mistakes_log.py`: `check` now reports stray `### ` headings,
  unknown patterns and duplicate IDs, and refuses an unknown command. Five
  tests, each proven by bug planting. M-160 and M-161 logged.
- 2026-11-16: W13 and W15 built: six project skills (`/wrap-up`,
  `/handoff`, `/review-packet`, `/decide`, `/field-session`, `/debrief`) and
  this brief. `/project-review` and `/wrap-up brief` have now been used once.
- The 2026-11-13 workflow recommendations (W1 to W16) are all applied,
  deferred or dropped.
- 2026-11-15: `ARCHITECTURE.md` and ADR-0074, when to split a module.

## In progress

- Pull request #23 (`w13-project-skills`): Joe reviews, then it merges into
  `main`.
- Three findings left from the review of `tools/mistakes_log.py`: `archive`
  doesn't validate its month (`2026-1` would match three months); no test
  for the unknown-kind and no-ID reports or the pattern table; IDs past
  M-999 don't parse (`check` should now report them).
- Joe may turn off the `anthropic-skills` plugin in the Claude app to save
  context. With it on, `get_usage` showed Skills at 7,776 tokens.

## Next three

1. Joe's review of pull request #23, then merge. Sonnet, low.
2. Decide 1 below, then build C1 of `drafts/2026-11-13-code-recommendations.md`:
   console output on a background thread (ADR-0035, decided, never built).
   Opus, high.
3. Decide 2 below, then build C5 part 1: program tests on the sim clock.
   Medium.

Items 2 and 3 follow that doc's suggested order, which Joe hasn't decided.

## Decisions waiting on Joe

Answer by number and letter, such as "1A". **Bold** is the recommendation.

1. (D1, for C1) At exit, the console is still blocked. What does shutdown
   do? **A.** Give up after 2 s and warn in the log file. B. Wait until it
   drains.
2. (D9, for C5 part 1) The clock in program tests. **A.** The sim clock,
   except one real-clock test per program. B. As today.
3. (Backlog #113) Airworthy's goal 5 needs a flight baseline before the
   refactor. **A.** First flight 6 (2026-11-14), which flew the whole suite:
   `src/` has one commit since, `18ecb7a`, the 0.3 m/s final descent it flew
   uncommitted. B. A new session on the commit before the refactor's first
   change, which costs a session but flies exactly that commit.

The code doc's other decisions (D2 to D8, D10 to D20) come with their items.

## Last reviewed

`0846826`, 2026-11-04: the last row of `REVIEW.md`'s review log. The next
code review covers everything after it, as the first pull request into the
`reviewed` branch. The full line-by-line walk comes after the refactor (W9).
