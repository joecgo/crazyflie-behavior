# Review queue

Decisions and review findings waiting for my next code review. `/decide`
and `/project-review` add to it as they go; `/review-packet` posts each
item as a comment on the review's pull request, then empties both lists.
One writer at a time (`CLAUDE.md`, "One writer").


## Decisions

One line each: date, ADR link, the choice in a few words.

## Findings

One line each: date, `file:line`, the finding in a few words, its outcome
(fixed in `<hash>`, open, or the user's call).

- 2026-11-26, `src/crazyflie_behavior/drone/crazyflie/log_blocks.py:287`: the comment says a dropped estimate goes stale and the safety pre-check fails on it, but the pre-check doesn't check the velocity estimate's age, so a dropped velocity alone doesn't fail it (found writing the project tour, M-288). Open, the user's call: fix the comment, or have the pre-check check the velocity estimate too.
