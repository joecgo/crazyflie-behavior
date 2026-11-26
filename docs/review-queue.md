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
- 2026-11-25, [ADR-0093](decisions/0093-the-crazyflie-adapter-splits-into-parts-with-take-off-and-landing-free-of-cflib.md): #157 stage 5 before the build: C6 before #153 (#153 waits until row #157 is removed); the log-block part's interface as proposed (`LogBlocks`, its callbacks private, reached by tests through test-only forwards; `_take_off_log` stays in the adapter); the take-over setting reaches it through its constructor.
- 2026-11-25, [ADR-0093](decisions/0093-the-crazyflie-adapter-splits-into-parts-with-take-off-and-landing-free-of-cflib.md): #157 stage 5 after the build: the clearing of the log blocks at the link close is dropped now, not in the rebuild stage (bug planting showed a fresh part on every connect made it redundant); it goes in its own commit after the move. `ARCHITECTURE.md` section 7's row names `log_blocks.py` (text approved). The other choices stand as built: the link callable is `current_crazyflie`, two "The adapter's own." comments in the import block, the callback forwards as properties, the bit positions re-exported for tests (TODO #158), and `commands.py`'s docstring pointing to `log_blocks.py`.
- 2026-11-25, [ADR-0038](decisions/0038-connecting-to-a-flying-drone.md): the take-over fitness function lists `adapter.py` as a pass-through to its log-block part, like `start_up.py` (option A; M-251).
- 2026-11-25, [ADR-0093](decisions/0093-the-crazyflie-adapter-splits-into-parts-with-take-off-and-landing-free-of-cflib.md): #157 stage 5's review: a move-only commit's change to a fitness function's lists (the take-over list here, `BLOCKING_FUNCTIONS` in stage 4) is noted in its commit message, ADR-0093 unchanged; `start_up.py` imports the take-off block's constants from `log_blocks.py`; a glossary row for *Part* (text approved); the link lost while connecting goes to backlog #161.
- 2026-11-25, [ADR-0093](decisions/0093-the-crazyflie-adapter-splits-into-parts-with-take-off-and-landing-free-of-cflib.md): #157 stage 6 before the build: the link part's interface as proposed (`CrazyflieLink(clock, uri, cache_directory, *, take_over_flight)`, built in `__init__` and in every `connect()`; `is_deck_attached`, renamed from `_deck_attached` for backlog #100); the adapter keeps the order of `connect()`'s steps and works out the close's keyword; `close()` takes a required keyword, and the take-over's skip stays inside `write_thrust_base()`; the glossary's *Stored callable* example follows the rename (text approved).
- 2026-11-25, [ADR-0093](decisions/0093-the-crazyflie-adapter-splits-into-parts-with-take-off-and-landing-free-of-cflib.md): #157 stage 6's review: `close(*, radio_link_only)` and `has_link_to_close` for the two names the review found, and `connect()`'s comment above the fresh link reworded; the three test gaps from before the move are tested now, in a commit before the move (`1d51b96`); `ARCHITECTURE.md` section 7's row names `link.py` (text approved).

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
- 2026-11-25, `src/crazyflie_behavior/drone/crazyflie/log_blocks.py:255`: pre-existing: a link lost just after `connect()`'s status wait ends it with cflib's AttributeError from `LogConfig.start()`, not the lost link's error (Q-03); Joe's call: backlog #161.
- 2026-11-25, `src/crazyflie_behavior/drone/crazyflie/adapter.py:44`: the re-exports' TODO says test-only, but `programs/start_up.py` imports `TAKE_OFF_BLOCK_DURATION` and `TAKE_OFF_PERIOD_MS` from the adapter; fixed, uncommitted: `start_up.py` imports them from `log_blocks.py`.
- 2026-11-25, `tests/architecture/test_import_rules.py:253`: the move commit changes this fitness function's body, which ADR-0093's D14 and Never line rule out (stage 4's move did the same to `BLOCKING_FUNCTIONS`); Joe's call: noted in the move commit's message, ADR-0093 unchanged.
- 2026-11-25, `docs/decision-backlog.md:96`: row #157 says stage 5 is "not yet reviewed or committed"; fixed, uncommitted: the clause is dropped.
- 2026-11-25, `src/crazyflie_behavior/drone/crazyflie/adapter.py:197`: "a new session" for a new connection, where the glossary's *Session* is a field-test trip (Q-41; also line 191 and `take_off_and_landing.py:132`); fixed, uncommitted: "link".
- 2026-11-25, `src/crazyflie_behavior/drone/crazyflie/adapter.py:198`: "no drone time" isn't a glossary term, which says "the drone's timestamp" (Q-38); fixed, uncommitted: "no earlier drone timestamp".
- 2026-11-25, `src/crazyflie_behavior/drone/crazyflie/log_blocks.py:6`: *part* is used as a term with no glossary row (Q-38); fixed, uncommitted: a glossary row for *Part*, text Joe approved.
- 2026-11-25, `src/crazyflie_behavior/drone/crazyflie/log_blocks.py:132`: `LogBlocks`'s docstring copies `connect()`'s order, a fact it doesn't own (M-250's pattern); fixed, uncommitted: it points to ADR-0093.
- 2026-11-25, `src/crazyflie_behavior/drone/crazyflie/link.py:114`: pre-existing: the two radio-only closes passed as values (`open()`'s `on_abandon`, and the close `_land_silence_and_wait` gives the last-resort landing) had no behavior test, only the blocking-call fitness function's allow-list; fixed in `1d51b96`: each is checked to close the radio link before the cleanup does, which closes only the radio link too, so dropping either had changed nothing else a test saw.
- 2026-11-25, `src/crazyflie_behavior/drone/crazyflie/adapter.py:175`: pre-existing: no test checked that the URI and the cache directory reach cflib (the fake ignored them); fixed in `1d51b96`.
- 2026-11-25, `src/crazyflie_behavior/drone/crazyflie/adapter.py:198`: pre-existing: no test called `disconnect()` with no link, as the start-up's `finally` does after a failed `connect()`; fixed in `1d51b96`.
- 2026-11-25, `docs/verified-facts.md:17`: pre-existing: five rows still named only `adapter.py` for code the refactor's stages moved out of it (Q-01); fixed in the stage's records commit.
- 2026-11-25, `src/crazyflie_behavior/drone/crazyflie/link.py:124`: `close(*, may_be_flying)` and `_close_link`'s docstring gave the glossary's *May be flying* a second meaning, airborne or the state unknown (Q-38); Joe's call: `radio_link_only`, in `f38578b`.
- 2026-11-25, `src/crazyflie_behavior/drone/crazyflie/link.py:78`: `is_open` is also true while the link opens and after a lost link, which `disconnect()` relies on; Joe's call: `has_link_to_close`, in `f38578b`.
- 2026-11-25, `docs/verified-facts.md:16`: stage 6's update dropped `adapter.py` from the rows for `close_link()`'s zero thrust and `SyncCrazyflie.close_link()`, whose adapter code stayed, and missed the parameter writes row (Q-01); fixed in the stage's records commit.
- 2026-11-25, `src/crazyflie_behavior/drone/crazyflie/adapter.py:178`: the move-only report missed two differences: cflib's driver set-up now runs after the flag resets and the parts' rebuild, and a late cflib callback from an earlier link reaches that link's part, not the adapter's fields; no cflib call changes order; fixed: the move commit `f38578b` names them.
- 2026-11-25, `src/crazyflie_behavior/drone/crazyflie/link.py:98`: three cflib facts the move relies on weren't in the facts register (Q-01); fixed in the stage's records commit.
- 2026-11-25, `docs/next-up.md:113`: E11 quoted `on_abandon=self._close_radio_link_only`, a name stage 6 removed, and its notes too; fixed in the stage's records commit.
