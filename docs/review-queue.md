# Review queue

Decisions and review findings waiting for my next code review. `/decide`
and `/project-review` add to it as they go; `/review-packet` posts each
item as a comment on the review's pull request, then empties both lists.
One writer at a time (`CLAUDE.md`, "One writer").


## Decisions

One line each: date, ADR link, the choice in a few words.

- 2026-11-27, [ADR-0096](decisions/0096-the-project-tour-is-one-html-page-per-chapter-pinned-to-one-commit.md): a glossary word in its everyday sense is marked `<span class="plain">`, which the dot check (`tests/docs/test_tour_dots.py`) skips.
- 2026-11-27, [ADR-0096](decisions/0096-the-project-tour-is-one-html-page-per-chapter-pinned-to-one-commit.md): a part's name before "part" ("the link part") is a use of *Part*, not of *Link* or *Command*.
- 2026-11-27, [ADR-0096](decisions/0096-the-project-tour-is-one-html-page-per-chapter-pinned-to-one-commit.md): a part's name alone, as in the list of the four, is dotted when the glossary has the term (*Link*, *Log block*, *Command*).
- 2026-11-27, [ADR-0096](decisions/0096-the-project-tour-is-one-html-page-per-chapter-pinned-to-one-commit.md): the tour's form, checks and publishing: a skill step copies it to the portfolio, with a visit-count line in the page.

## Findings

One line each: date, `file:line`, the finding in a few words, its outcome
(fixed in `<hash>`, open, or the user's call).

- 2026-11-26, `src/crazyflie_behavior/drone/crazyflie/log_blocks.py:287`: the comment says a dropped estimate goes stale and the safety pre-check fails on it, but the pre-check doesn't check the velocity estimate's age, so a dropped velocity alone doesn't fail it (found writing the project tour, M-288). Decided 2026-11-27 (see the `safety_layer.py:94` item): the pre-check checks the velocity estimate too, so the comment becomes true.
- 2026-11-27, `src/crazyflie_behavior/drone/crazyflie/adapter.py:143`: Joe asked whether `lambda: self._link.crazyflie` should be a named function (`get_crazyflie`) so the call says what it does. The name is on the receiving side, `current_crazyflie` (`commands.py:57`), and positional arguments hide it at the call. Open, the user's call: keyword arguments at the call, a named method, or as it is.
- 2026-11-27, `src/crazyflie_behavior/drone/crazyflie/take_off_and_landing.py:71`: Joe asked whether `FlightCommands` is used outside take-off and landing. It isn't: it lists only the five sends take-off and landing makes, and `CrazyflieCommands` fits it, but the name reads as general. Open, the user's call: a narrower name, or as it is.
- 2026-11-27, `src/crazyflie_behavior/safety/safety_layer.py:94`: Joe asked why the safety pre-check doesn't check the velocity estimate or the Multi-ranger's readings for staleness. No ADR gives a reason. The velocity estimate shares the position estimate's packet, so it goes stale with it, except when the adapter drops a velocity that isn't finite; the take-off judge (`safety_layer.py:278`) also reads it with no age check. Nothing in `src/` steers by the Multi-ranger yet. Joins the `log_blocks.py:287` finding. Decided 2026-11-27 by Joe: add a velocity staleness check (age and finiteness, like the position estimate's) after PR 31's review is done; no Multi-ranger check until a behavior steers by it (backlog #49). Backlog #171. Posted on PR 31 at `log_blocks.py:287` (`safety_layer.py` isn't in its diff).
- 2026-11-27, `src/crazyflie_behavior/drone/crazyflie/commands.py:110`: Joe asked whether the setpoint priority makes the system flimsy. The firmware's rule depends on order, but each order has one path: `go_to` and `go_to_relative` both hand over through `_handing_over_to_high_level`, every motor stop goes through `stop_motors`, and a planted wrong order fails tests (tour section 9). The last-resort landing keeps its own order (ADR-0084). Open, the user's call; no change proposed.
- 2026-11-27, `src/crazyflie_behavior/drone/crazyflie/adapter.py:167`: Joe asked why `connect()` and `disconnect()` block, and whether a background thread could wait for the drone. They run before the first tick and after the last, so no stream waits on them; cflib's own waits already run on helper threads with time limits (ADR-0029), and `connect()` returns a ready drone or its own error (ADR-0031). Connecting in the background would make every tick handle a drone that isn't ready. Open, the user's call; no change proposed.
