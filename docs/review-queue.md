# Review queue

Decisions and review findings waiting for my next code review. `/decide`
and `/project-review` add to it as they go; `/review-packet` posts each
item as a comment on the review's pull request, then empties both lists.
One writer at a time (`CLAUDE.md`, "One writer").

Also post the comments saved before this queue existed (not in the
repository): `drafts/2026-11-24-blocking-call-review-comments.md` and
`drafts/2026-11-24-stage-4-review-comments.md`. Drop this note once
they're posted.

## Decisions

One line each: date, ADR link, the choice in a few words.

- 2026-11-25, [ADR-0094](decisions/0094-connecting-raises-the-interrupt-signal-that-a-cpython-lock-error-hides.md): connecting raises the interrupt signal that a CPython 3.12 lock error hides (option A), fixed before #157 stage 4's commits.

## Findings

One line each: date, `file:line`, the finding in a few words, its outcome
(fixed in `<hash>`, open, or the user's call).

- 2026-11-25, `src/crazyflie_behavior/drone/crazyflie/time_limit.py:112`: the hidden threading lock error was logged before the cleanup, so a second Ctrl+C there could skip it (Q-19); fixed in `419791c`: it's logged after the cleanup.
- 2026-11-25, `src/crazyflie_behavior/drone/crazyflie/time_limit.py:88`: "lock error" had no glossary row, and the glossary's "lock" is the drone lock (Q-38, Q-41); Joe chose "threading lock error", with no glossary row: fixed in `419791c`.
- 2026-11-25, `src/crazyflie_behavior/drone/crazyflie/time_limit.py:115`: the comment on the late raise read backwards; reworded in `419791c`.
- 2026-11-25, `src/crazyflie_behavior/drone/crazyflie/time_limit.py:122`: `_interrupt_hidden_in`'s docstring said CPython "turned" the interrupt into the error, and left out the None; reworded in `419791c`.
- 2026-11-25, `src/crazyflie_behavior/drone/crazyflie/take_off_and_landing.py:213`: `emergency_stop`'s docstring hid that it records no motor stop (ADR-0058); fixed in `91e1eeb`.
- 2026-11-25, `src/crazyflie_behavior/drone/crazyflie/take_off_and_landing.py:88`: the class docstring copied `connect()`'s "replaces it twice"; it points to ADR-0093 instead, in `91e1eeb`.
- 2026-11-25, `src/crazyflie_behavior/drone/crazyflie/time_limit.py:113`: the debug line put the capitalized step name mid-sentence ("during Opening the link"); the name comes first, in `419791c`.
