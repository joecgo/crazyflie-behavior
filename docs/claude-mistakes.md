# Claude's mistakes

The implementation and many of the options in this project are AI-assisted
(Claude Code). This log records Claude's mistakes so I can see what kind of
work it finds hard: where to focus my own learning, where to double-check
Claude, and where a new skill for Claude might help.

A mistake is something wrong by what was known or written down at the time.
A recommendation I decide against, or a rule I change later, isn't one.

Two sections, newest first in each:
- **Mistakes I had to point out.** Entries before 2026-11-16 also say
  whether a later Claude review would probably have caught it anyway.
- **Mistakes Claude caught itself**, at a later step (a code review, planting
  bugs to prove the tests, or while writing the code).

This file holds the current month's entries. Older months are in
[claude-mistakes/](claude-mistakes/), and the index below lists every entry.

Each entry has a mistake ID, a kind, a pattern and a guard. Takeaways that
apply to code reviews become questions in the [review
checklist](../REVIEW.md), and each question names the entries it came from.

**Kinds of work:** *design* (how parts fit together), *safety design*,
*recommendation* (an option Claude pushed on a false fact, a missed
constraint, or no real reason), *environment*
(assumptions about my machine, time zone or tools), *testing*, *process* (how
decisions are recorded), *communication* (how Claude explains things).

**Patterns:**

- *said-without-checking*: a fact, number or claim from memory.
- *records-ahead-of-code*: a doc, comment or ADR says more than the code.
- *safety-judgment*: a backup shares the failure, or a check fails the
  unsafe way.
- *weak-test*: a test that can't fail, a kind fake, no test at the limit.
- *how-I-work*: acting before a go-ahead, skipping a step, usage.
- *recommendation*: an option with no reason, or one already ruled out.
- *window-between-steps*: cleanup gaps, loop edges, a status's lag.
- *vocabulary*: a term that isn't in the glossary, or is used for something
  else.
- *message-misstates-outcome*: a log line or exit code says the wrong thing.
- *environment*: Windows, PyCharm, the time zone.
- *reading-field-data*: a number taken from the wrong part of a log.
- *leftover-state*: state from an earlier connection, a streak that never
  ends.

**Escalation ladder.** When a new entry's pattern already has entries, its
takeaway climbs a step instead of only adding a question:

1. First time: the entry and a review question.
2. Second time: a helper, a test or a template line that makes the mistake
   harder.
3. Third time: a fitness function, a lint or a design change that makes it
   impossible or caught by a machine. The question retires, and the
   entries' guard names the mechanism.

Only mechanisms that are cheap to set up and keep are built; for a pattern
where none is, the entry says so and the question stays. Most patterns
are past their third entry already; the mechanisms planned for them are in
the 2026-11-13 workflow and code recommendations.

**Upkeep.** `python tools/mistakes_log.py write` gives new entries their IDs
and rebuilds the tables below; a test fails when they're out of date. New
entries go at the top of their section without an ID.

## At a glance

<!-- generated: kinds -->
| Kind | I pointed it out | Claude caught it later |
|---|---|---|
| design | 5 | 25 |
| safety design | 5 | 22 |
| recommendation | 7 | 10 |
| environment | 4 | 11 |
| communication | 14 | 79 |
| testing | 2 | 38 |
| process | 7 | 44 |
| **Total** | **44** | **229** |
<!-- end generated -->

<!-- generated: patterns -->
| Pattern | Entries |
|---|---|
| said-without-checking | 56 |
| records-ahead-of-code | 35 |
| weak-test | 33 |
| how-I-work | 31 |
| vocabulary | 26 |
| safety-judgment | 18 |
| window-between-steps | 17 |
| recommendation | 15 |
| reading-field-data | 15 |
| message-misstates-outcome | 14 |
| environment | 10 |
| leftover-state | 3 |
<!-- end generated -->

Of the 33 I pointed out up to 2026-11-16, a later Claude review would
probably have caught none, maybe 7, and probably not 26 (that question
isn't asked for new entries). Up to then, 7 of the 13 recommendation
mistakes needed me, and 8 of the 46 communication mistakes. The first
hardware session (2026-11-04) added four hardware facts said in chat from
memory, against the review checklist's first rule. Claude's own reviews, planted bugs and
source checks find mistakes in code, tests and records, including Windows
details and a firmware claim that two ADRs rested on. A repeating
pattern: an interruption landing between two lines of cleanup code (five
times so far).

## Index

<!-- generated: index -->
| ID | Date | Title | Kind | Pattern | Guard |
|---|---|---|---|---|---|
| M-273 | 2026-11-25 | The first fix for #162's case-index finding checked something a planted off-by-one left unchanged | testing | weak-test | a check meant to pin where something happened compares the place noted at the event, and the plant that moves the event runs before the fix is called done |
| M-272 | 2026-11-25 | The review's failure scenario for the fake's assert was a loss the adapter never hears of | communication | said-without-checking | a review finding's failure scenario is traced to its end, or planted, before it's reported (Q-20) |
| M-271 | 2026-11-25 | cflib's full link close can hang on a lost link, and no review asked whether its check could change on another thread | design | window-between-steps | Q-03's question about a guard that changes on another thread is asked of a library's own check-then-wait code too, with the answer in the facts register |
| M-270 | 2026-11-25 | ADR-0095 chained the step's error as the lost link's cause, which Python prints as the reverse of what happened | communication | message-misstates-outcome | an error raised while handling another keeps it as its context, with no `from`, unless the other really caused it; read the traceback Python prints before choosing (Q-43) |
| M-269 | 2026-11-25 | #162's lost-link tests didn't check where each case lost the link, and three more gaps | testing | weak-test | a test whose cases come from a listed run checks in each case that it acted where its ID says, and each Never line of the ADR gets a planted bug |
| M-268 | 2026-11-25 | #162's records and docstrings said more than its code | communication | records-ahead-of-code | before a record says what a test covers, read its parametrize and first case, and count tests with `pytest --collect-only` |
| M-267 | 2026-11-25 | "Recording" for the call list made at collection | communication | vocabulary | working rule 6 for every noun in a new name or docstring, everyday words included: a glossary term's word means that term (Q-41) |
| M-266 | 2026-11-25 | Test data computed at collection would have stopped the whole run when connect() raised | testing | said-without-checking | code that runs while pytest collects a test file catches its errors and fails a test with them, proved by planting a raise there |
| M-265 | 2026-11-25 | The bug-planting script for #162 wrote CRLF into adapter.py and reported it restored | testing | environment | a planting script reads, writes and compares bytes (M-169), and `git ls-files --eol` shows `w/lf` after it |
| M-264 | 2026-11-25 | Backlog #161 named one step of a link lost while connecting and missed the others | design | window-between-steps | Q-03 asked of every library call in the function, not only the one that showed the problem, with each answer in the facts register |
| M-263 | 2026-11-25 | Two names in stage 6's link part meant something other than their code | communication | vocabulary | working rule 6 for every new name, keyword arguments included: a name that spells a glossary term means that term exactly, and a yes-or-no name says when it's true, in-between states included (Q-38) |
| M-262 | 2026-11-25 | The facts register kept pointing at adapter.py after its code moved | process | records-ahead-of-code | each move searches the facts register for the old file's name and re-reads every row it finds against both files, as part of the move's records |
| M-261 | 2026-11-25 | Stage 6's move-only report named one difference and missed two | communication | records-ahead-of-code | a move-only claim lists, beside the check's verdict, each moved call whose place in its caller changed and each callback whose owner changed, read off the caller's diff (ADR-0093's D14) |
| M-260 | 2026-11-25 | Three cflib facts behind stage 6's move were read but not registered | process | how-I-work | working rule 1: a fact read in source to back a claim goes into the register in the same step, before the claim is written down |
| M-259 | 2026-11-25 | The link part's rename left the old name in a waiting explain-back | process | records-ahead-of-code | a rename is searched for across the whole repository, the git-ignored `drafts/` included (ripgrep skips ignored files unless given `--no-ignore`) |
| M-258 | 2026-11-25 | The adapter's URI, cache directory and disconnect with no link had no test | testing | weak-test | bug planting covers each argument the adapter passes on to cflib and each early return, not only the logic between them |
| M-257 | 2026-11-25 | The move-only check's first run reported a change that wasn't there | testing | weak-test | a check script's verdict counts only once it has passed on the real change and failed on planted ones; stage 6's plants put two changes in moved code that only the check can catch |
| M-256 | 2026-11-25 | A Python fix sent through a Bash heredoc lost half its backslashes | environment | environment | code that holds a backslash escape is written with the editor tools, never sent through a heredoc |
| M-255 | 2026-11-25 | The take-over list change went against ADR-0093's move-only rule, unflagged | recommendation | recommendation | an option that touches code an ADR governs is checked against that ADR's Never and Always lines before it's offered (CLAUDE.md: point out a conflict with an accepted ADR and ask) |
| M-254 | 2026-11-25 | Stage 5's comments and records said more than the code | communication | records-ahead-of-code | before marking an import test-only, search `src/` and `tools/` for its importers, not only `tests/`; a fact another module owns is pointed to, not copied (`docs/coding-style.md`); a record never says what the commit carrying it makes false (Q-46) |
| M-253 | 2026-11-25 | "Session", "drone time" and "part" in the Crazyflie adapter's comments | communication | vocabulary | working rule 6, applied to each word of a new or rewritten comment, including words the glossary already uses in another sense (Q-38, Q-41) |
| M-252 | 2026-11-25 | A link lost while connecting surfaces as cflib's AttributeError | design | window-between-steps | Q-03, for each cflib call `connect()` relies on: what it does once the link is already gone, read in the source, with the fact in the register |
| M-251 | 2026-11-25 | A recommended constructor keyword broke the take-over fitness function | recommendation | recommendation | working rule 5, for a name or keyword an option adds: search `tests/architecture/` for it too, not only the backlog and the ADR index |
| M-250 | 2026-11-25 | Two docstrings in stage 4's take-off and landing part said more than the code | communication | records-ahead-of-code | a docstring that says "as X does" is checked against both methods line by line, and a fact another module owns is pointed to, not copied (`docs/coding-style.md`) |
| M-249 | 2026-11-25 | A comment that read backwards and a docstring that said "turned into", in ADR-0094's fix | communication | vocabulary | read each new comment as someone who knows only the code and the glossary, before the review does (`/project-review` step 4) |
| M-248 | 2026-11-25 | "Lock error" in ADR-0094's code, where the glossary's "lock" is the drone lock | communication | vocabulary | working rule 6, for words the glossary already uses in another sense, not only for missing terms (Q-41) |
| M-247 | 2026-11-25 | ADR-0094's fix logged the threading lock error before the cleanup | design | window-between-steps | in an `except` block that cleans up, the cleanup comes first and any logging after it (`time_limit.py`, its order pinned by a test; and Q-19, which names log lines) |
| M-246 | 2026-11-25 | The interrupt signal landing inside a threading wait came out as CPython's lock error | design | window-between-steps | ADR-0094: `run_with_time_limit` raises the interrupt signal that CPython hides in a lock error, with a test that sends no real signal; and Q-19 (an interruption landing between two lines) |
| M-245 | 2026-11-24 | A work order's bug-planting script was copied from a scratch file a failed edit had broken | process | how-I-work | the handoff skill's step 3: name a script in an order only after running it from where it's saved (added with Joe's OK, 2026-11-24); and M-233's: after a script writes or copies a file, read or run what it wrote |
| M-244 | 2026-11-24 | The blocking-call fitness function missed a blocking call imported under another name | testing | weak-test | a scanner that matches by name lists every way a name can change (an import alias, an assignment, a stored callable) and has a test for each (`REVIEW.md` Q-32) |
| M-243 | 2026-11-24 | The fitness function read the drone interface's methods by one decorator spelling | testing | weak-test | a fitness function's reader of real code doesn't depend on how the code is spelled, or has a test for each spelling (Q-32) |
| M-242 | 2026-11-24 | Two forms the blocking-call scanner handles had no test | testing | weak-test | before calling a scanner's tests complete, list each `case` of its `match` and name the test that reaches it (Q-32) |
| M-241 | 2026-11-24 | The Blocking call glossary row read as covering locks the check skips | communication | records-ahead-of-code | a definition with "only" is checked against a search for its exceptions in the code, as M-235's guard asks of docstrings (Q-32) |
| M-240 | 2026-11-24 | A fitness function's test name said "only" where it checked reachability | communication | records-ahead-of-code | M-235's guard, for test names too: an "only" in a name is checked against what its assert does (Q-32) |
| M-239 | 2026-11-24 | ADR-0093 narrowed two older rules without marking either | process | how-I-work | before an ADR is accepted, check its design against CLAUDE.md's Never and Always lists, and mark the status line of every ADR it narrows (Q-33) |
| M-238 | 2026-11-24 | ADR-0093 and `commands.py` used Hand-over for more than the glossary's meaning | communication | vocabulary | working rule 6: read a glossary term's row, not only its name, before using it in a new sense; `REVIEW.md` Q-41 |
| M-237 | 2026-11-24 | The glossary's Transcript test row repeated the overclaim M-232 fixed in ADR-0093 | testing | weak-test | a fix for an overclaim searches the records written with it (the glossary, the index, the backlog) for the same claim; `REVIEW.md` Q-40 |
| M-236 | 2026-11-24 | `ARCHITECTURE.md` kept a module name and a Built status that ADR-0093 had changed | process | records-ahead-of-code | working rule 3, for `ARCHITECTURE.md` too: when a decision names a module or a stage is built, search `ARCHITECTURE.md` for the old name and update its row's Needs cell |
| M-235 | 2026-11-24 | `commands.py`'s docstrings said more than its code does | communication | records-ahead-of-code | an "every" or "only" in a docstring is checked against a search for its exceptions (`REVIEW.md` Q-32), and a "because" names the step that makes it true |
| M-234 | 2026-11-24 | The transcript fake relied on two cflib facts with no facts-register rows | process | how-I-work | CLAUDE.md's facts-register rule applies to a test fake's docstrings too; `REVIEW.md` Q-01 |
| M-233 | 2026-11-24 | A script copied E9's heading into the explain-back notes for E10 | process | how-I-work | after a script writes to a file, read the lines it wrote |
| M-232 | 2026-11-24 | ADR-0093 said the transcripts catch a reorder of three orders, but none of its flights reaches the third | testing | weak-test | a claim that tests catch a list of cases names the test or flight that reaches each one, and bug planting a swap of each order proves it |
| M-231 | 2026-11-24 | ADR-0093 counted 45 test lines that set the adapter's log level, but there are 49 | process | said-without-checking | working rule 1 applied to counts: search every form the code uses (a name, a string, a constant), and say which forms a count covers |
| M-230 | 2026-11-24 | `.gz` reading broke `read_recording`'s promise of a ValueError | testing | weak-test | a new way to read input gets a test for each way it can fail, checked against the errors its function's docstring names |
| M-229 | 2026-11-24 | `/debrief`'s new step for committing scripts left out their recordings | process | records-ahead-of-code | working rule 3: before an ADR says a step is in a skill, read the step against each bullet of the Decision |
| M-228 | 2026-11-24 | The glossary called an unbuilt tool real, and ADR-0092 called built work unbuilt | process | records-ahead-of-code | working rule 3; for a tool decided but not built, the glossary says "once it's built" and names the backlog row |
| M-227 | 2026-11-24 | Searches that skipped `drafts/` reported C6 missing and missed Joe's no to a mutation-testing dependency | process | said-without-checking | working rule 1: when a search for a term Joe uses finds nothing, search `drafts/` too (ripgrep's `--no-ignore`) before saying it doesn't exist |
| M-226 | 2026-11-23 | The closing comment on pull request #30 wrote backlog rows as GitHub links | communication | vocabulary | in text GitHub renders (comments, pull request bodies), write "backlog row 149", never a bare `#149` |
| M-225 | 2026-11-23 | Two docstrings rewritten after Joe's reply said they read fine | process | how-I-work | working rule 7: before fixing a review finding, read every reply in its thread; a reply that says it's fine closes it |
| M-224 | 2026-11-23 | A backlog row offered a fix that doesn't fix it | recommendation | window-between-steps | working rule 2: read the code an option touches (here `finish`) before listing it as a fix |
| M-223 | 2026-11-23 | ADR-0034 left an open question with no backlog row | process | how-I-work | backlog #150; `/decide`'s step 8, a row for each follow-up |
| M-222 | 2026-11-23 | The format version's bump left with nothing to catch a missed one | testing | weak-test | the golden file's tests in `tests/recording/test_encoding.py` (ADR-0089) and `REVIEW.md` Q-57 |
| M-221 | 2026-11-22 | The next-up brief said 84 planted bugs for the recorder; it was 87 | communication | said-without-checking | working rule 4: a count in a record comes from the whole run, recounted when the record is written |
| M-220 | 2026-11-22 | New mock test names used terms not in the glossary | communication | vocabulary | working rule 6: check a new name's words against the glossary before using them |
| M-219 | 2026-11-22 | `TICK_PERIOD`'s docstring promised exactness that depends on `STALE_AFTER` | communication | said-without-checking | a docstring for a value computed from another module's constant states what its claim depends on |
| M-218 | 2026-11-22 | Backlog #133 removed while #142 still waited on it | process | said-without-checking | before removing a backlog row, search the docs for its number (M-213), and update each row that waits on it |
| M-217 | 2026-11-22 | Two mock "too long" tests checked a whole tick past the motor cut | testing | weak-test | a test past a time limit checks 0.01 s past it, and a planted limit plus 0.04 s proves it |
| M-216 | 2026-11-22 | Two "mid hover" tick-step tests set up mid-climb | testing | weak-test | a test reaches the state its name says by ticking until a condition holds, not by a fixed count of ticks |
| M-215 | 2026-11-22 | Said the draft filed every PR #29 entry under "I had to point out" | communication | said-without-checking | working rule 2: read the whole document before saying what it says, not a line found by search |
| M-214 | 2026-11-22 | Two tick-loop tests expected a tick's log line without a garbage-collector pause | testing | weak-test | a test that compares a log line exactly holds fixed every optional part the line can carry |
| M-213 | 2026-11-22 | A backlog row's removal drafted without searching for pointers to it | process | said-without-checking | before removing a backlog row, search the code and the docs for its number |
| M-212 | 2026-11-22 | New names for the wait after the silence and the lost-link flag that said more or less than their code | communication | vocabulary | after a change, reread every name and comment it touched or relied on against what the code now does (M-207's guard) |
| M-211 | 2026-11-22 | "Only the snapshot raises" for a lost link, though `land()` reads a snapshot of its own | communication | said-without-checking | rule 1: before writing that only one function does something, search for every caller of it, its own module's included |
| M-210 | 2026-11-22 | Removing the mock's lost-link checks let its next update play a tone a real drone never got | testing | window-between-steps | when a change removes a check, list everything the check stopped, in the adapters and their fakes, and keep each one stopped or decide otherwise |
| M-209 | 2026-11-22 | A lost-link check copied into every adapter method, with nothing to catch a method without it | design | weak-test | a check every method of a kind needs goes in one place every call passes through; where it can't, a test that takes its list of methods from the class fails for a method without it (`docs/coding-style.md`, "A check every call needs goes in one place") |
| M-208 | 2026-11-22 | The fix for M-207 said "It keeps ticking", with no clear subject | communication | vocabulary | M-207's guard, and after rewording a docstring, check that each "it" points at the part that does the thing |
| M-207 | 2026-11-22 | A tick-loop docstring that said "goes to the tick step, before the next tick" | communication | vocabulary | name the call and why its timing matters ("the loop calls `request_stop()` on its own thread, so the tick step needs no lock"), never a vague verb such as "goes to" or "gets it" |
| M-206 | 2026-11-22 | A checked audit's row that left out a planted bug that passed | testing | said-without-checking | working rule 2: a table written from results is checked against every result, not the ones in mind |
| M-205 | 2026-11-21 | A backlog number cited in code before its row, and already taken | process | said-without-checking | working rule 2: read the backlog's last row before naming a new row's number, and add the row before code cites it |
| M-204 | 2026-11-21 | Asked whether to remove `SILENCE_HOLD` without finding the ADR that records it | recommendation | recommendation | working rule 5: search the ADRs for the topic in words too, not only for a name from the code |
| M-203 | 2026-11-21 | A float limit called unreachable for both tolerances, from one's results | communication | said-without-checking | working rule 1: quote a computed result case by case; "the same" across cases needs each case computed |
| M-202 | 2026-11-21 | A test audit's coverage judged by reading, not by planting | testing | said-without-checking | plant a bug before saying whether a test catches it (the audit's scripts, `drafts/2026-11-21-boundary-audit/`) |
| M-201 | 2026-11-21 | An assert on a verdict, which is always true | testing | weak-test | REVIEW.md Q-54: assert a verdict's `.is_approved`, never the verdict; bug planting (`docs/coding-style.md`) shows an assert that can't fail |
| M-200 | 2026-11-21 | A last-resort landing that released the setpoint priority before the land | safety design | said-without-checking | working rule 2: before proposing an order of commands to the firmware, read the ADRs and code that already fix that order |
| M-199 | 2026-11-21 | A question asked with a term the glossary lacks | communication | vocabulary | working rule 6: check the glossary before naming something, and propose a missing term before using it, in questions too |
| M-198 | 2026-11-21 | A fallback said to share a failure it doesn't share | communication | said-without-checking | before saying a fallback fails together with what it backs up, name what they share: code, sensor, estimate or thread (`/decide` step 3) |
| M-197 | 2026-11-21 | Boundary tests proposed both on the firing side of a `>=` limit | testing | weak-test | for a limit, name the side of the boundary each test is on: one at exactly the limit and one on the other side, near it (REVIEW.md Q-48) |
| M-196 | 2026-11-20 | A planted bug undone with `git checkout` on a file with uncommitted changes | process | how-I-work | undo a planted bug by reversing the edit or restoring a copy taken first, never with `git checkout` or `git restore` |
| M-195 | 2026-11-20 | Tests counted by the lines that build a clock | communication | said-without-checking | working rule 1: count tests by the `def test_` lines that reach the code, following helpers |
| M-194 | 2026-11-19 | Age-limit tests one tick past the limit, none at it | testing | weak-test | REVIEW.md Q-48; for a limit, plant both a wrong value and the other comparison |
| M-193 | 2026-11-19 | Built "Yes" with no test citing the ADR | process | records-ahead-of-code | REVIEW.md Q-39 and `/project-review` step 3, against the index's note on Built |
| M-192 | 2026-11-19 | A stall of the velocity uncertainty alone, which its log block rules out | safety design | said-without-checking | working rule 1: before naming a failure of one input, read where it comes from and what shares its stream |
| M-191 | 2026-11-18 | A review packet's "the same" read as "unchanged" | communication | vocabulary | `/review-packet` step 3: every row names its change, as "the same change as `hover.py`", never a bare "the same" |
| M-190 | 2026-11-18 | A review pull request misdescribed its copied commits | communication | said-without-checking | working rule 2; `git range-diff` compares copied commits with their originals |
| M-189 | 2026-11-18 | Sim-clock program tests with no time limit | testing | weak-test | the `sim_clock` fixture in `tests/conftest.py` (ADR-0080, ADR-0082), and REVIEW.md Q-10 |
| M-188 | 2026-11-18 | A chirp test left loose for slow ticks the sim clock doesn't have | testing | weak-test | REVIEW.md Q-49 |
| M-187 | 2026-11-18 | ADR-0076's records left behind by two build choices | process | records-ahead-of-code | working rule 3, and `/project-review` step 3 |
| M-186 | 2026-11-17 | A Flow definition from ADR-0060 without its amendment | communication | said-without-checking | working rule 2: read an ADR's status line for amendments before quoting its rule |
| M-185 | 2026-11-17 | A review packet's tier 1 files read as diffs | process | how-I-work | working rule 7: read a rule plainly, and when two parts of it disagree, say so before writing from one |
| M-184 | 2026-11-17 | Review fixes pushed to the open review branch | process | how-I-work | working rule 2: read REVIEW.md's "My reviews" before committing anything during a review |
| M-183 | 2026-11-17 | A "here" that didn't say where | communication | vocabulary | the new rule in `docs/coding-style.md`, "Name both places in a contrast" |
| M-182 | 2026-11-17 | Reasons for changed tests guessed from their names | communication | said-without-checking | working rule 2 |
| M-181 | 2026-11-17 | The flow check let a negative or infinite uncertainty through | safety design | safety-judgment | REVIEW.md Q-14, and a test for each non-finite value and a negative one |
| M-180 | 2026-11-17 | "No flow" logged for an old velocity uncertainty | communication | message-misstates-outcome | REVIEW.md Q-43, and the stale test's check of the line |
| M-179 | 2026-11-17 | Wording ADR-0077 left behind, again | communication | records-ahead-of-code | REVIEW.md Q-35 |
| M-178 | 2026-11-17 | Words outside the glossary in ADR-0077's fix lines and test names | communication | vocabulary | `/project-review`'s fresh-context read (step 7) |
| M-177 | 2026-11-17 | A NaN down range could hand over the initial climb | safety design | safety-judgment | REVIEW.md Q-14, and a test for each non-finite value |
| M-176 | 2026-11-17 | Wording ADR-0077 left behind | communication | records-ahead-of-code | REVIEW.md Q-35 and Q-43 |
| M-175 | 2026-11-17 | ADR-0077's record out of step with its work | process | records-ahead-of-code | `/project-review` step 3 and REVIEW.md Q-39, Q-48 |
| M-174 | 2026-11-17 | A boundary test that stepped over its boundary | testing | weak-test | REVIEW.md Q-48 and Q-53 |
| M-173 | 2026-11-17 | Docstrings and comments only their author could follow | communication | vocabulary | `/project-review`'s fresh-context read (step 7) |
| M-172 | 2026-11-17 | An unchecked claim about timed waits in a test comment | communication | said-without-checking | REVIEW.md Q-01 |
| M-171 | 2026-11-17 | An index row written with the wrong line endings, again | environment | environment | `git diff --stat` after each scripted edit |
| M-170 | 2026-11-17 | ADR-0078's index row recorded as written but missing | process | records-ahead-of-code | `/project-review` step 3 and REVIEW.md Q-39 |
| M-169 | 2026-11-17 | The bug-planting script changed a file's line endings | testing | environment | the checksum comparison around the planting |
| M-168 | 2026-11-17 | The stuck exit's exit code given from one run | communication | said-without-checking | none yet; the facts register row gives every run |
| M-167 | 2026-11-17 | Backlog edits written while another work session held the backlog | process | how-I-work | none yet |
| M-166 | 2026-11-17 | Backlog #104's settle heights from part of the logs | communication | reading-field-data | working rule 4 |
| M-165 | 2026-11-17 | A docstring said nothing waits on a stuck console write | communication | records-ahead-of-code | Q-02 |
| M-164 | 2026-11-17 | ADR-0075 marked built without the test its Consequences name | process | records-ahead-of-code | Q-39 |
| M-163 | 2026-11-17 | Two planted bugs counted from the exit code, not the failure | testing | weak-test | none yet |
| M-162 | 2026-11-17 | A comment gave an ordering a reason the code doesn't have | communication | records-ahead-of-code | a planted bug for each claim a comment makes |
| M-161 | 2026-11-16 | The mistakes log's check passed malformed entries | testing | weak-test | `tests/tools/test_mistakes_log.py` |
| M-160 | 2026-11-16 | A pull request's changes read from local `main` | communication | said-without-checking | working rule 1 |
| M-159 | 2026-11-16 | "Was lost" for a script the hand-off said may be gone | communication | said-without-checking | working rule 2 |
| M-158 | 2026-11-16 | A log's program line placed by one sample | communication | said-without-checking | working rule 1 |
| M-157 | 2026-11-14 | One flight's battery line filed under other flights | communication | reading-field-data | working rule 4 |
| M-156 | 2026-11-14 | Motor outputs read as the thrust command | communication | reading-field-data | working rule 4 |
| M-155 | 2026-11-14 | The forged drone changed, but not its ADR or glossary row | process | records-ahead-of-code | Q-35 |
| M-154 | 2026-11-14 | A helper and a test whose names said something else | communication | vocabulary | none yet |
| M-153 | 2026-11-14 | A flight command without `--crazyflie` | communication | how-I-work | working rule 9 |
| M-152 | 2026-11-13 | Two backlog rows said ADR-0035's console thread was built | process | records-ahead-of-code | Q-39 |
| M-151 | 2026-11-13 | A flight started without reading how the last one ended | process | reading-field-data | `/field-session` |
| M-150 | 2026-11-13 | A chance worked out for a battery reading that arrives at a fixed time | communication | reading-field-data | `/debrief` |
| M-149 | 2026-11-13 | An option offered for the landing approach that the code already has | recommendation | recommendation | working rule 5 |
| M-148 | 2026-11-13 | Hover heights taken from the moment the hover started | communication | reading-field-data | working rule 4 |
| M-147 | 2026-11-12 | A time limit quoted from memory | communication | said-without-checking | working rule 1 |
| M-146 | 2026-11-12 | The hover test waited for a drone status that comes too late | design | window-between-steps | Q-15 |
| M-145 | 2026-11-12 | "Fails the connect, on the floor" for a block the rescue landing starts too | safety design | safety-judgment | Q-22 |
| M-144 | 2026-11-12 | Wording that ADR-0062 and ADR-0064 left behind | communication | records-ahead-of-code | Q-35 |
| M-143 | 2026-11-12 | A second copy of the staleness rule | design | safety-judgment | none yet |
| M-142 | 2026-11-12 | A work-log total that missed three changes to a day's hours | process | how-I-work | none yet |
| M-141 | 2026-11-12 | ADR-0064's test list said the take-off rule refuses at 0.03 | communication | records-ahead-of-code | Q-37 |
| M-140 | 2026-11-12 | A recommended run at connect that the Bench would only half see | recommendation | recommendation | Q-29 |
| M-139 | 2026-11-12 | ADR-0063 designed around a log block created but not started | design | said-without-checking | Q-04 |
| M-138 | 2026-11-12 | A recap that called the torque a match for the battery move | communication | said-without-checking | none yet |
| M-137 | 2026-11-12 | An estimate reset described as starting with large uncertainty | communication | said-without-checking | Q-01 |
| M-136 | 2026-11-12 | Two glossary rows for ADR-0061 that didn't match it | communication | vocabulary | Q-40 |
| M-135 | 2026-11-12 | A thrust base report logged the same whether it confirmed or not | communication | message-misstates-outcome | Q-45 |
| M-134 | 2026-11-12 | "Estimate reset." logged before a write that can fail | communication | message-misstates-outcome | none yet |
| M-133 | 2026-11-12 | A two-cause failure branch tested for one cause | testing | weak-test | none yet |
| M-132 | 2026-11-12 | A review finding against the adapter's VERIFY convention | communication | how-I-work | none yet |
| M-131 | 2026-11-12 | "No glossary change" for a term whose meaning grew | process | vocabulary | Q-38 |
| M-130 | 2026-11-12 | An ADR that took up an older ADR's rejected option, unmarked | process | records-ahead-of-code | Q-33 |
| M-129 | 2026-11-12 | The reset's link check could go stale before the write | design | window-between-steps | Q-03 |
| M-128 | 2026-11-12 | A boundary fix with no test at the boundary | testing | weak-test | Q-48 |
| M-127 | 2026-11-12 | "As soon as the motors stop" for a flag that knows only our stop | communication | safety-judgment | Q-50 |
| M-126 | 2026-11-12 | A recording started before Joe was ready | process | how-I-work | working rule 9 |
| M-125 | 2026-11-10 | One no-flow limit for an uncertainty that grows with height | safety design | safety-judgment | Q-08 |
| M-124 | 2026-11-10 | The altHold climb chosen without reading what its controller does at a switch | design | said-without-checking | Q-07 |
| M-123 | 2026-11-10 | One limit read two ways, and messages that seemed to contradict it | design | message-misstates-outcome | Q-48 |
| M-122 | 2026-11-10 | A comment and an ADR line that promised more than the code | process | records-ahead-of-code | Q-49 |
| M-121 | 2026-11-10 | Choices made while building, not recorded, and new terms not proposed | process | how-I-work | working rule 8 |
| M-120 | 2026-11-10 | The mock found the settle height again every tick | testing | weak-test | Q-09 |
| M-119 | 2026-11-10 | An old status logged as current, and a reset logged before it was sent | communication | message-misstates-outcome | none yet |
| M-118 | 2026-11-10 | A cut-off extraction read as the touchdown | communication | reading-field-data | working rule 4 |
| M-117 | 2026-11-10 | Session 2's light blamed on a check that didn't exist yet | communication | reading-field-data | `/debrief` |
| M-116 | 2026-11-09 | A 0.05 s margin on the climb time limit, not flagged | safety design | reading-field-data | `/debrief` |
| M-115 | 2026-11-09 | ADR-0054 described from its number, not its text | communication | said-without-checking | working rule 2 |
| M-114 | 2026-11-08 | "In this light it never did", for a run with no flow data | communication | reading-field-data | `/debrief` |
| M-113 | 2026-11-08 | "First flight 1 didn't hit it", with cflib's close unchecked | communication | said-without-checking | working rule 1 |
| M-112 | 2026-11-08 | The level final descent's motor stop locks the drone | safety design | said-without-checking | Q-06 |
| M-111 | 2026-11-07 | "About 4.5 s" for the no-flow uncertainty, read from an upper bound | communication | reading-field-data | working rule 4 |
| M-110 | 2026-11-07 | Extra usage spent without a cost estimate or a usage check | process | how-I-work | none yet |
| M-109 | 2026-11-07 | Landing work hidden in take_snapshot, never decided | design | how-I-work | Q-34 |
| M-108 | 2026-11-06 | "About 8" parameter writes for "Charge", counted one per note | communication | said-without-checking | none yet |
| M-107 | 2026-11-06 | A pre-check rule that would end the game at a dark hiding spot | safety design | safety-judgment | Q-24 |
| M-106 | 2026-11-06 | A sound effect's number read from an out-of-date comment | communication | said-without-checking | working rule 2 |
| M-105 | 2026-11-06 | A hand-over order justified by a cflib call it doesn't match | safety design | said-without-checking | Q-02 |
| M-104 | 2026-11-06 | ADR-0041 amended twice without its status line saying so | process | records-ahead-of-code | Q-33 |
| M-103 | 2026-11-05 | The Crazyflie's weight in the glossary, with no source | environment | said-without-checking | Q-01 |
| M-102 | 2026-11-05 | A firmware shutdown at 3.0 V that the default build leaves out | safety design | said-without-checking | Q-03 |
| M-101 | 2026-11-05 | `kalman.varPX` called the position variance | communication | said-without-checking | Q-01 |
| M-100 | 2026-11-05 | "Touchdown never confirmed", read from a log line that wasn't there | testing | reading-field-data | `/debrief` |
| M-099 | 2026-11-05 | Explaining a finding with words the glossary doesn't have | communication | vocabulary | working rule 6 |
| M-098 | 2026-11-04 | A go/no-go rule of "the motion flag set in most samples" | communication | reading-field-data | `/debrief` |
| M-097 | 2026-11-04 | A Bench criterion of 0.5 s for a value that streams at 1 Hz | testing | reading-field-data | `/debrief` |
| M-096 | 2026-11-04 | The Flow deck's maximum shutter read as "too dark" | communication | reading-field-data | `/debrief` |
| M-095 | 2026-11-04 | "A red LED that keeps blinking means a failed self-test" | environment | said-without-checking | Q-01 |
| M-094 | 2026-11-04 | WinUSB for the Crazyradio, and "the README says WinUSB" | environment | said-without-checking | Q-01 |
| M-093 | 2026-11-04 | A battery connector named from memory | environment | said-without-checking | working rule 1 |
| M-092 | 2026-11-04 | ADR-0046 applied without searching for the old wording | process | records-ahead-of-code | Q-35 |
| M-091 | 2026-11-04 | A shortened log line that dropped the outcome | communication | message-misstates-outcome | Q-44 |
| M-090 | 2026-11-04 | Restoring a planted bug with `git checkout` discarded edits | testing | how-I-work | none yet |
| M-089 | 2026-11-04 | "No test enforces it" said without looking at the tests | communication | said-without-checking | none yet |
| M-088 | 2026-11-04 | "Can only be a clock bug", and a cost overstated | design | said-without-checking | none yet |
| M-087 | 2026-11-04 | "Isn't known to be flying", the opposite of the rule | communication | safety-judgment | Q-50, Q-51 |
| M-086 | 2026-11-04 | Comments that said more than their code | communication | records-ahead-of-code | working rule 3 |
| M-085 | 2026-11-04 | A time-limit message that read the telemetry again after the check | design | message-misstates-outcome | Q-26 |
| M-084 | 2026-11-04 | A take-over message that assumed the drone was flying | communication | message-misstates-outcome | Q-43 |
| M-083 | 2026-11-04 | A "known risk" that cflib's own guard rules out | recommendation | said-without-checking | Q-03 |
| M-082 | 2026-11-04 | Records that claimed more than the code or the source showed | communication | message-misstates-outcome | Q-52 |
| M-081 | 2026-11-04 | An ADR amendment without the documents and the test that follow from it | process | records-ahead-of-code | Q-36 |
| M-080 | 2026-11-04 | The battery placed under the board, from memory | environment | said-without-checking | none yet |
| M-079 | 2026-11-04 | A right understanding "corrected" | communication | how-I-work | working rule 7 |
| M-078 | 2026-11-04 | A commit rule that says "before" a review, read as "during" | process | how-I-work | working rule 7 |
| M-077 | 2026-11-03 | Crazyflie adapter code committed without `/project-review` | process | how-I-work | working rule 10 |
| M-076 | 2026-11-03 | Docstrings that a change left behind | communication | records-ahead-of-code | working rule 3 |
| M-075 | 2026-11-03 | An emergency stop that said "not delivered" when it may have been | communication | message-misstates-outcome | Q-43 |
| M-074 | 2026-11-03 | A once-per-streak log line whose streak never ended | design | leftover-state | Q-18 |
| M-073 | 2026-11-03 | A new connection that kept the last one's landing | safety design | leftover-state | Q-17 |
| M-072 | 2026-11-03 | Fitness functions with blind spots | testing | weak-test | Q-32 |
| M-071 | 2026-11-03 | Two constants that must agree, with no test between them | testing | weak-test | Q-47 |
| M-070 | 2026-11-03 | A taken-over flight given the take-off grace period | safety design | safety-judgment | none yet |
| M-069 | 2026-11-03 | An emergency stop that said "Sent." when nothing was | safety design | message-misstates-outcome | Q-52 |
| M-068 | 2026-11-03 | A rescue landing that exited 0 when the rescue failed | design | message-misstates-outcome | Q-52 |
| M-067 | 2026-11-03 | A mitigation in ADR-0044 that the code didn't provide | safety design | records-ahead-of-code | none yet |
| M-066 | 2026-11-03 | ADR-0043 described the old field-testing README wrongly | process | said-without-checking | working rule 2 |
| M-065 | 2026-11-03 | A test fake that streamed only once | testing | weak-test | Q-09 |
| M-064 | 2026-11-03 | New vocabulary in code names before proposing it | process | vocabulary | working rule 6 |
| M-063 | 2026-11-03 | "No landing command can work" on a NaN estimate | safety design | said-without-checking | Q-02 |
| M-062 | 2026-11-03 | An idea of mine credited to the AI | process | how-I-work | none yet |
| M-061 | 2026-11-02 | A work-log row raised without its total | process | how-I-work | none yet |
| M-060 | 2026-11-02 | A tick period quoted from memory | communication | said-without-checking | working rule 1 |
| M-059 | 2026-11-02 | A watchdog recommended that the backlog already ruled out | recommendation | recommendation | working rule 5 |
| M-058 | 2026-11-02 | A refusal that drops the drone it protects | safety design | safety-judgment | Q-21 |
| M-057 | 2026-11-02 | Manual arming called a barrier that doesn't rely on our code | safety design | safety-judgment | Q-12 |
| M-056 | 2026-11-02 | A pushed commit that doesn't pass its own tests | process | how-I-work | working rule 10 |
| M-055 | 2026-11-02 | A failsafe whose landing used the value that failed it | safety design | safety-judgment | Q-12 |
| M-054 | 2026-11-02 | Wording in the NaN change that missed the project's rules | communication | records-ahead-of-code | none yet |
| M-053 | 2026-11-02 | The gap between two lines, a fifth time | design | window-between-steps | Q-19 |
| M-052 | 2026-11-02 | A Windows call whose failure went unnoticed | environment | environment | Q-05 |
| M-051 | 2026-11-02 | A log message and a docstring narrower than the code | communication | message-misstates-outcome | Q-43 |
| M-050 | 2026-11-02 | A review skill whose steps clashed with the skill it runs | process | how-I-work | none yet |
| M-049 | 2026-11-02 | Follow-up commits pushed to a pull request already merged | process | how-I-work | none yet |
| M-048 | 2026-11-02 | "Nothing is scheduled" said without checking | environment | said-without-checking | none yet |
| M-047 | 2026-11-02 | Options offered that didn't fix the problem | recommendation | recommendation | working rule 5 |
| M-046 | 2026-11-01 | A safety gap deferred without checking the planned control that opens it | safety design | safety-judgment | Q-23 |
| M-045 | 2026-11-01 | A rename recommended without checking how the project already says it | recommendation | recommendation | working rule 5 |
| M-044 | 2026-11-01 | Code called dead without following every path to it | recommendation | recommendation | none yet |
| M-043 | 2026-11-01 | A parameter named with a glossary term that means something else | communication | vocabulary | Q-41 |
| M-042 | 2026-11-01 | Cloud setup advice from memory | environment | said-without-checking | none yet |
| M-041 | 2026-11-01 | Code reviews that skipped the review checklist | process | how-I-work | working rule 10 |
| M-040 | 2026-11-01 | The gap between two lines, a fourth time | design | window-between-steps | Q-19 |
| M-039 | 2026-11-01 | A tick that raised left no timing behind | design | window-between-steps | none yet |
| M-038 | 2026-11-01 | A cost from Linux in a comment, with no source | environment | environment | none yet |
| M-037 | 2026-11-01 | A gap described without reading the code that closes it | safety design | safety-judgment | Q-20 |
| M-036 | 2026-11-01 | A backlog item written and dropped without checking or measuring | recommendation | recommendation | working rule 5 |
| M-035 | 2026-11-01 | A key named where the code handles a signal | communication | vocabulary | Q-42 |
| M-034 | 2026-11-01 | A local named for when it was fetched, not what it holds | communication | vocabulary | none yet |
| M-033 | 2026-11-01 | A behavior's failure rule chosen without asking | design | how-I-work | Q-13 |
| [M-032](claude-mistakes/2026-10.md) | 2026-10-31 | A battery check that a NaN voltage would pass | safety design | safety-judgment | Q-14 |
| [M-031](claude-mistakes/2026-10.md) | 2026-10-31 | A glossary definition the code outgrew | process | vocabulary | Q-38 |
| [M-030](claude-mistakes/2026-10.md) | 2026-10-31 | A landing guard that trusted an old drone status | safety design | safety-judgment | Q-14 |
| [M-029](claude-mistakes/2026-10.md) | 2026-10-31 | A quiz instead of an answer | communication | how-I-work | none yet |
| [M-028](claude-mistakes/2026-10.md) | 2026-10-31 | Unclear docstrings that lean on terms not in the glossary | communication | vocabulary | Q-38 |
| [M-027](claude-mistakes/2026-10.md) | 2026-10-31 | Recommending against accepted ADRs for vague reasons | recommendation | recommendation | none yet |
| [M-026](claude-mistakes/2026-10.md) | 2026-10-31 | An option with no reason to choose it | recommendation | recommendation | none yet |
| [M-025](claude-mistakes/2026-10.md) | 2026-10-30 | A wait that a previous connection could satisfy | design | leftover-state | Q-16 |
| [M-024](claude-mistakes/2026-10.md) | 2026-10-30 | A reason copied from cflib's waits to a plain sleep | environment | said-without-checking | none yet |
| [M-023](claude-mistakes/2026-10.md) | 2026-10-30 | A safety pre-check that only passed with the mock adapter | design | weak-test | Q-09 |
| [M-022](claude-mistakes/2026-10.md) | 2026-10-30 | Rules stated in code that no fitness function checked | testing | weak-test | Q-32 |
| [M-021](claude-mistakes/2026-10.md) | 2026-10-30 | Two ADRs built on an unchecked firmware claim | safety design | said-without-checking | Q-01 |
| [M-020](claude-mistakes/2026-10.md) | 2026-10-30 | The same gap between two lines, again | design | window-between-steps | Q-19 |
| [M-019](claude-mistakes/2026-10.md) | 2026-10-30 | Edge cases in the connect time limits | design | window-between-steps | Q-25 |
| [M-018](claude-mistakes/2026-10.md) | 2026-10-29 | Cleanup gaps around connecting | design | window-between-steps | Q-19 |
| [M-017](claude-mistakes/2026-10.md) | 2026-10-29 | Windows details in the start-up code | environment | environment | Q-05 |
| [M-016](claude-mistakes/2026-10.md) | 2026-10-29 | Debug logging for every library, and a logger named `__main__` | design | environment | Q-31 |
| [M-015](claude-mistakes/2026-10.md) | 2026-10-29 | Tests that couldn't fail cleanly | testing | weak-test | Q-53 |
| [M-014](claude-mistakes/2026-10.md) | 2026-10-29 | Ctrl+C described two ways in one ADR | safety design | window-between-steps | Q-28 |
| [M-013](claude-mistakes/2026-10.md) | 2026-10-29 | Gaps at the edges of the tick loop | design | window-between-steps | Q-27 |
| [M-012](claude-mistakes/2026-10.md) | 2026-10-29 | Test fakes that hang instead of failing | testing | weak-test | Q-10 |
| [M-011](claude-mistakes/2026-10.md) | 2026-10-29 | An exception to an older ADR without marking it | process | records-ahead-of-code | Q-33 |
| [M-010](claude-mistakes/2026-10.md) | 2026-10-29 | A logging recommendation that ignored what was already known | recommendation | recommendation | none yet |
| [M-009](claude-mistakes/2026-10.md) | 2026-10-29 | Stretched UE analogies | communication | how-I-work | none yet |
| [M-008](claude-mistakes/2026-10.md) | 2026-10-29 | A stop control designed for a terminal, not for PyCharm | environment | environment | Q-30 |
| [M-007](claude-mistakes/2026-10.md) | 2026-10-29 | Only one command request per tick | design | said-without-checking | Q-32 |
| [M-006](claude-mistakes/2026-10.md) | 2026-10-29 | Holding back measurements because of an undecided item | recommendation | recommendation | none yet |
| [M-005](claude-mistakes/2026-10.md) | 2026-10-29 | A hang can't be detected | safety design | safety-judgment | Q-11 |
| [M-004](claude-mistakes/2026-10.md) | 2026-10-27 | Dates in the wrong time zone | environment | environment | none yet |
| [M-003](claude-mistakes/2026-10.md) | 2026-10-27 | Waiting for the next slot after an overrun | recommendation | recommendation | none yet |
| [M-002](claude-mistakes/2026-10.md) | 2026-10-24 | Trusting a cflib read that returns old data on a timeout | design | said-without-checking | Q-03 |
| [M-001](claude-mistakes/2026-10.md) | 2026-10-24 | A backup that fails together with what it backs up | safety design | safety-judgment | Q-12 |
<!-- end generated -->

---

## Mistakes I had to point out

### M-222, 2026-11-23: The format version's bump left with nothing to catch a missed one

- **What happened:** ADR-0034 named the pitfall: "every format change must bump the version." Building the recorder (ADR-0087, ADR-0088), Claude wrote `FORMAT_VERSION = 1` and round-trip tests. Those pass when a change reaches the encoder and the decoder together, as a renamed field does, so a format change could ship without a bump and recordings made before it would stop reading back. Q-32 asks what enforces a rule about the code; neither the build nor its project review asked it for this rule. Joe caught it reading #30: "Is there a note in Review.md to maintain this encode.py file as anything changes that it references?", then "an oversight that we didn't even have a reminder to increase the FORMAT_VERSION".
- **Kind:** testing.
- **Pattern:** weak-test.
- **Guard:** the golden file's tests in `tests/recording/test_encoding.py` (ADR-0089) and `REVIEW.md` Q-57.
- **Takeaway:** a repeat of M-209: Q-32 wasn't asked, at the build or in the review. A rule an ADR states as a pitfall ("every format change must") is a rule about the code, and the change that builds it needs the guard that enforces it. The ladder's second step, a "Guards" line in the ADR template's Consequences, was proposed; Joe kept Q-32 alone (2026-11-23).

### M-209, 2026-11-22: A lost-link check copied into every adapter method, with nothing to catch a method without it

- **What happened:** building ADR-0084 ("the adapter raises on the tick's next call to it"), Claude put `_raise_if_the_link_is_lost()` at the top of each of the Crazyflie adapter's 14 tick-facing methods, and the same in the mock adapter. The tests list those methods by hand (`TICK_CALLS`, `LOST_LINK_CALLS`), so a new command without the line would send to a dead link, and no test would notice unless its author also added it to the list. Q-32 asks what enforces a rule about the code; neither the build nor its `/project-review max` asked it. Joe caught it reviewing #29: "what if a new function forgets to add this?" ADR-0086 moves the check to `take_snapshot()`.
- **Kind:** design.
- **Pattern:** weak-test.
- **Guard:** a check every method of a kind needs goes in one place every call passes through; where it can't, a test that takes its list of methods from the class fails for a method without it (`docs/coding-style.md`, "A check every call needs goes in one place").
- **Takeaway:** Q-32 already asks what enforces a rule about the code, so reviews need no new question: it just wasn't asked. The guard goes where code is written: the coding-style rule, added with Joe's OK on 2026-11-22 and committed with ADR-0086's build. A matching Q-32 line was dropped as overkill (Joe, 2026-11-22).

### M-207, 2026-11-22: A tick-loop docstring that said "goes to the tick step, before the next tick"

- **What happened:** building ADR-0083, Claude wrote `TickLoop`'s docstring as "A stop request goes to the tick step once, before the next tick, and the loop keeps ticking until the tick step is done", with "the tick step gets it before the next tick" and "just before a tick" in the two `request_stop()` docstrings. Reviewing #29, Joe couldn't tell what it meant: "goes to" hid the call (`request_stop()`), and "before the next tick" hid why the timing matters (the loop makes the call on its own thread, so the tick step needs no lock).
- **Kind:** communication.
- **Pattern:** vocabulary.
- **Guard:** name the call and why its timing matters ("the loop calls `request_stop()` on its own thread, so the tick step needs no lock"), never a vague verb such as "goes to" or "gets it".
- **Takeaway:** a repeat of M-173 (docstrings only their author could follow), and `/project-review max`'s fresh-context read passed it. Added with Joe's OK on 2026-11-22: `REVIEW.md` Q-55.

### M-199, 2026-11-21: A question asked with a term the glossary lacks

- **What happened:** asking C3's shape questions, Claude wrote question 2 as "when the latch clears", for the new record that the flight is over, which had no glossary term. Joe asked whether it meant the glossary's *Kill latch*. Claude then proposed *Flight end*, which Joe approved.
- **Kind:** communication.
- **Pattern:** vocabulary.
- **Guard:** working rule 6: check the glossary before naming something, and propose a missing term before using it, in questions too.
- **Takeaway:** a working name in a question reads as the glossary term it resembles. Not a code-review takeaway, so no step on the escalation ladder.

### M-197, 2026-11-21: Boundary tests proposed both on the firing side of a `>=` limit

- **What happened:** proposing tests for D5's 60 s backstop (a `>=` rule) in the C3 decisions, Claude wrote "one tick past and exactly at the limit". Both fire, so neither shows that the rule stays quiet just before its limit, and a smaller limit would pass. Joe asked why two tests were needed; answering, Claude saw the pair was on one side. The pair is exactly at the limit (fires) and one tick before it (doesn't).
- **Kind:** testing.
- **Pattern:** weak-test.
- **Guard:** for a limit, name the side of the boundary each test is on: one at exactly the limit and one on the other side, near it (REVIEW.md Q-48).
- **Takeaway:** a fourth boundary-test entry (M-128, M-174, M-194), this one in a proposal rather than code. The mechanism question is already open: next-up brief decision 6 and backlog #133's audit, so no new step on the ladder.

### M-191, 2026-11-18: A review packet's "the same" read as "unchanged"

- **What happened:** the reading order in ADR-0076's review packet gave `hover.py`'s change as "`main()` takes an optional clock: three lines", then "the same" for the other three programs, and "What changed" said "the same change" for each. Meant as "the same three lines as `hover.py`", it reads as "nothing changed". Joe pointed it out; each row and line now says the change in full.
- **Kind:** communication.
- **Pattern:** vocabulary.
- **Guard:** `/review-packet` step 3: every row names its change, as "the same change as `hover.py`", never a bare "the same".
- **Takeaway:** a second *vocabulary* entry about shorthand that leans on a line elsewhere (M-183, "here"), so the ladder's second step: a template line, the guard above (Joe, 2026-11-18).

### M-186, 2026-11-17: A Flow definition from ADR-0060 without its amendment

- **What happened:** proposing a glossary row for *Flow*, I wrote that flow arrives only while the velocity uncertainty is under 0.03 m/s, citing ADR-0060. ADR-0060's status line says ADR-0064 amends it: in flight, the limit grows with height above 0.3 m, up to 0.1 m/s. Joe pointed it out.
- **Kind:** communication.
- **Pattern:** said-without-checking.
- **Guard:** working rule 2: read an ADR's status line for amendments before quoting its rule.

### M-185, 2026-11-17: A review packet's tier 1 files read as diffs

- **What happened:** the review packet for ADR-0077 said "the diff" for three of its four tier 1 files, though REVIEW.md's table says tier 1 is read "every line". I followed the paragraph above the table ("changed files as diffs") and never noticed it clashed with the table. Joe asked why only one of four said every line. The rule was then clarified: a tier 1 file is read whole. I had also added an exception for a comments-only diff that Joe never asked for, and used it on `safety_layer.py`; Joe pointed that out too, and the exception was removed. The earlier packet, `2026-11-17.md`, has the same wording for `start_up.py`.
- **Kind:** process.
- **Pattern:** how-I-work.
- **Guard:** working rule 7: read a rule plainly, and when two parts of it disagree, say so before writing from one.
- **Takeaway:** the rule itself was ambiguous. I also changed it in `555157b` without proposing the glossary's *Review tier* change it needed. Joe then dropped reading instructions altogether: tiers now set only Claude's review, and the packet gives each file's scale of change.

### M-184, 2026-11-17: Review fixes pushed to the open review branch

- **What happened:** asked to "commit and push" the fixes from Joe's comments on pull request #24, I committed them to `review/2026-11-17` and pushed (`a99a4d5`). REVIEW.md says nothing is pushed to the review branch once it's open; fixes go on `main` and into the next review. Joe pointed it out. The fix was then put on `main` as `d404629`.
- **Kind:** process.
- **Pattern:** how-I-work.
- **Guard:** working rule 2: read REVIEW.md's "My reviews" before committing anything during a review.
- **Takeaway:** a repeat of M-049 (commits pushed to a pull request already merged), so the escalation ladder calls for a mechanism. Proposal: `/review-packet` or a pre-push hook refuses a push to a `review/*` branch that has an open pull request (backlog #126).

### M-183, 2026-11-17: A "here" that didn't say where

- **What happened:** `console_output.py` set the console's level with the comment `# here, so debug messages never enter the queue`. "Here" stood for "on the queue's handler, not the console's", but the other handler was never named, so the word read as filler. Two project reviews, one of them a fresh-context read, missed it; Joe caught it reviewing pull request #24. Fixed on `main` in `d404629`.
- **Kind:** communication.
- **Pattern:** vocabulary.
- **Guard:** the new rule in `docs/coding-style.md`, "Name both places in a contrast".
- **Takeaway:** the same pattern as M-173, which the fresh-context read was the guard for, came back in the same change. By the log's escalation ladder a repeat calls for a mechanism: the written rule gives the reviews something to check against.

### M-160, 2026-11-16: A pull request's changes read from local `main`

- **What happened:** asked how well the workflow changes cut token use, I diffed the branch against local `main` and told Joe the pull request was the six skills plus the next-up brief (W13, W15). Local `main` already held W1 to W12; pull request #23 compares against GitHub's `main` and holds all of W1 to W16. Joe pointed it out.
- **Kind:** communication.
- **Pattern:** said-without-checking.
- **Guard:** working rule 1.
- **Takeaway:** what a pull request holds comes from the pull request (`gh pr view`, or a diff from `origin/main`), not from local `main`.

### M-153, 2026-11-14: A flight command without `--crazyflie`

- **What happened:** for session 6's test 3 I gave Joe the hover command copied from the mock-run checklist, with no `--crazyflie`, so it would have run the mock adapter, not the drone. Joe reported "it didn't do anything". His terminal tab was also still busy with a fourth propeller test waiting to connect.
- **Would a Claude review have caught it?** No: it's a command given in chat, not code.
- **Kind:** communication.
- **Pattern:** how-I-work.
- **Guard:** working rule 9.
- **Takeaway:** a command for a real flight is checked against the program's own usage lines (the `--crazyflie` flag) before it's given, never copied from the mock-run list.

### M-126, 2026-11-12: A recording started before Joe was ready

- **What happened:** after Joe said the next bench would use `--take-off-log`, I started the bench at once. Joe was not at the window yet and only held the drone there at the end, so most of that run was unusable ("I didn't realize you started"). Earlier I had told Joe to say "start" first.
- **Would a Claude review have caught it?** No: it's a conversation step, not code.
- **Kind:** process.
- **Pattern:** how-I-work.
- **Guard:** working rule 9.
- **Takeaway:** for a run that needs Joe's hands (a bench, a flight), start it only after Joe says go, not when they name the test.

### M-112, 2026-11-08: The level final descent's motor stop locks the drone

- **What happened:** the level final descent (ADR-0048, ADR-0056) ends with
  `send_stop_setpoint`, which keeps the firmware's setpoint priority above
  the high-level planner's, and the link closes about 10 ms later. With no
  fresh setpoint while the supervisor still counts the drone as flying, the
  2026.08 firmware moves to Locked, which needs a reboot. In First flight 2
  every arm after a flight was refused until a power cycle (backlog #67).
  Nobody checked the supervisor's state machine for what follows a motor
  stop, and backlog #62 assumed the firmware source couldn't be checked,
  though it is one download away. Fixed by ADR-0058.
- **Would a later Claude review have caught it?** Maybe: only a review that
  read the firmware's supervisor for "what state does the drone end in".
- **Kind:** safety design.
- **Pattern:** said-without-checking.
- **Guard:** Q-06.
- **Takeaway:** for every way a flight ends, check in the firmware source
  which supervisor state the drone ends in, and that it can arm again.

### M-110, 2026-11-07: Extra usage spent without a cost estimate or a usage check

- **What happened:** the project review's brief said to check `get_usage`
  now and then and stop if a limit got tight. With the 5-hour limit used up,
  Claude recommended waiting but gave no cost estimate in dollars. When I
  said continue, it ran about 40 tool calls on Opus without checking usage
  again, each one re-reading a context of 100k to 200k tokens: about $8 of
  extra usage in 10 minutes (my figure), until I stopped it.
- **Would a later Claude review have caught it?** No: it isn't in the code
  or the docs.
- **Kind:** process.
- **Pattern:** how-I-work.
- **Guard:** none yet.
- **Takeaway:** before working on extra usage, give a cost estimate in
  dollars, then check usage every few steps. Every step re-reads the whole
  context, so fewer, bigger steps cost less.

### M-109, 2026-11-07: Landing work hidden in take_snapshot, never decided

- **What happened:** the first code (2026-10-20) made `take_snapshot` move
  the landing on: it stopped the motors when the landing was due, and later
  also started the final descent. ADR-0008 says `take_snapshot()` copies the
  telemetry buffer into a snapshot, and no ADR decided the extra work.
  ADR-0040 (2026-11-02) only asked whether to keep it there for First
  flight. It called a separate per-tick call cleaner, but didn't say the
  placement had never been decided. On 2026-11-07 Claude recommended putting
  ADR-0048's level climb and descent there too.
- **Would a later Claude review have caught it?** Probably not: writing
  ADR-0040, Claude looked straight at it and didn't flag it.
- **Kind:** design.
- **Pattern:** how-I-work.
- **Guard:** Q-34.
- **Takeaway:** a function does what its name and its ADR say. Extra work
  that needs a place to run (here, every tick) is a design decision to
  raise, not a reason to hide it in a function that already runs.

### M-099, 2026-11-05: Explaining a finding with words the glossary doesn't have

- **What happened:** explaining why touchdown looked unconfirmed (backlog
  #51), Claude used words that aren't in the glossary ("replay",
  "hysteresis", "the hold", "estimate runaway") and "normal landing", which
  the glossary already uses for something else (the usual landing, in
  *Rescue landing*). Claude meant a landing whose height estimate was right.
  I couldn't follow the cause or the options.
- **Would a later Claude review have caught it?** Probably not: reviews read
  code and docs, not the conversation.
- **Kind:** communication.
- **Pattern:** vocabulary.
- **Guard:** working rule 6.
- **Takeaway:** before explaining, check each term against the glossary;
  define a missing one in a sentence and offer it for the glossary. Draw
  anything that depends on timing.

### M-080, 2026-11-04: The battery placed under the board, from memory

- **What happened:** walking me through the hardware setup, Claude said the
  battery goes underneath the Crazyflie, between the board and the Flow
  deck, "fairly sure but not certain". It didn't fit there. Bitcraze's docs
  put it on top of the board, under the top decks, which hold it down.
- **Would a Claude review have caught it?** Probably not: reviews read the
  code and the docs, not what Claude said in the chat.
- **Kind:** environment.
- **Pattern:** said-without-checking.
- **Guard:** none yet.
- **Takeaway:** for hardware setup steps, look up the maker's docs before
  answering, not after I find the answer doesn't fit. A hedge doesn't make
  a guess safe to act on.

### M-079, 2026-11-04: A right understanding "corrected"

- **What happened:** reviewing the adapter's `hover()` on the floor
  (ADR-0039), I said I hadn't realized a drone would fail if it hovered on
  the floor. Claude "corrected" me: the drone doesn't fail, it obeys too
  literally. But I was right. On the floor, the position controller isn't in
  control: the floor pushes back and the air cushion near it adds lift,
  neither of which the controller expects, so the drone can hop or skid.
  Claude's correction pushed me away from the real reason.
- **Would a Claude review have caught it?** Probably not: reviews read the
  code and the docs, not what Claude said in the chat.
- **Kind:** communication.
- **Pattern:** how-I-work.
- **Guard:** working rule 7.
- **Takeaway:** before correcting me, check whether my words, read in
  everyday terms, are right. If they are, confirm them and add the
  technical detail.

### M-078, 2026-11-04: A commit rule that says "before" a review, read as "during"

- **What happened:** in the middle of my third code review, a stop hook in
  the cloud environment asked Claude to commit and push. Claude committed
  and pushed two commits, and justified it with my rule's exception
  ("before one of my code reviews, commit and push right away"). That
  exception is for *before* a review, so I can read the code on GitHub.
  During a review, the normal rule applies: hold commits until the end and
  ask before pushing.
- **Would a Claude review have caught it?** Probably not: reviews read the
  code and the docs, not what Claude said in the chat.
- **Kind:** process.
- **Pattern:** how-I-work.
- **Guard:** working rule 7.
- **Takeaway:** a hook's request doesn't override my rules. When the two
  conflict, follow my rule and tell me about the conflict, and quote a rule
  exactly before citing it.

### M-063, 2026-11-03: "No landing command can work" on a NaN estimate

- **What happened:** for backlog #41, Claude said a drone whose position
  estimate is NaN "can't follow any landing command", and wrote it into
  ADR-0045 and a code comment. It's true only for position commands, which
  is every landing our code has. A descent on tilt and thrust, with
  touchdown from the raw down range, doesn't use the position estimate.
- **Why it was wrong:** the firmware source showed the position controller
  depends on the estimate; it didn't show that every way of flying does.
  The claim went one step past the evidence.
- **How I caught it:** I asked why not just descend slowly until a sensor
  detects touchdown.
- **Would a Claude review have caught it?** Probably not: the claim was
  sourced and the decision stayed right, so a review would likely have
  accepted it.
- **Kind:** safety design.
- **Pattern:** said-without-checking.
- **Guard:** Q-02.
- **Takeaway:** when a source shows one path fails, say "this path", not
  "every path", unless the other paths were checked too.

### M-062, 2026-11-03: An idea of mine credited to the AI

- **What happened:** `docs/next-up.md` (written by Claude on 2026-11-03)
  said "Origin: Joe's usage; the AI proposed the split" for the split
  between *field test* and *session*. The cloud run copied it into
  ADR-0043's origin line, and Claude then offered it back to me as an
  option. The split was my idea.
- **Why it was wrong:** an origin line must record who suggested what, and
  nothing in the conversation or the commits showed the AI proposing it.
- **How I caught it:** I said it was all my idea.
- **Would a Claude review have caught it?** Probably not: only I know who
  suggested it.
- **Kind:** process.
- **Pattern:** how-I-work.
- **Guard:** none yet.
- **Takeaway:** when who suggested something isn't recorded, say so and
  ask; don't fill in an origin.

### M-049, 2026-11-02: Follow-up commits pushed to a pull request already merged

- **What happened:** I merged pull request #5 seconds after Claude opened
  it. Claude then pushed three more commits to its branch and rewrote its
  description to include them, without checking whether it was still open.
  The commits never reached `main`, and the merged pull request's
  description listed changes it didn't contain.
- **Why it was wrong:** the session's own rules say a merged pull request
  is finished: follow-up work goes in a new pull request.
- **How I caught it:** I said I'd merged it and couldn't see the new one.
- **Would a Claude review have caught it?** Probably not: reviews look at
  the code and records, not at a pull request's state.
- **Kind:** process.
- **Pattern:** how-I-work.
- **Guard:** none yet.
- **Takeaway:** before pushing to a pull request's branch or editing its
  description, check that it's still open.

### M-048, 2026-11-02: "Nothing is scheduled" said without checking

- **What happened:** I asked whether there was enough information for the
  cloud run at noon on 2026-11-03 to work without me. Claude answered that
  nothing was scheduled and offered to create a routine, without checking.
  A weekly routine that works through `docs/next-up.md` already existed, and
  `next-up.md` itself said it was committed for cloud scheduled tasks.
- **Why it was wrong:** a claim about my setup must come from checking it
  (the routines list, the file the question was about), not from what this
  conversation had seen.
- **How I caught it:** I said I was confused and explained that the task
  runs through `next-up.md`.
- **Would a Claude review have caught it?** Probably not: it was said in
  conversation, and reviews look at code and records.
- **Kind:** environment.
- **Pattern:** said-without-checking.
- **Guard:** none yet.
- **Takeaway:** before saying something does or doesn't exist (a schedule,
  a session, a file), look it up, and read the file the question is about.

### M-047, 2026-11-02: Options offered that didn't fix the problem

- **What happened:** for backlog #36, after finding that closing the link
  drops a flying drone, Claude offered three ways to close it. B (always take
  over and land) and C (don't close the link, let the process exit) were
  listed as alternatives, though neither stops the drop: B left the other
  `connect()` failures, and with C a later `disconnect()` still sends the
  zero-thrust setpoint.
- **Why it was wrong:** an option must solve the problem being decided.
  These two only looked like alternatives.
- **How I caught it:** I asked why B and C were suggested if they don't fix it.
- **Would a Claude review have caught it?** Probably not: the options were in
  conversation, and reviews look at code and records.
- **Kind:** recommendation.
- **Pattern:** recommendation.
- **Guard:** working rule 5.
- **Takeaway:** check each option against the problem before listing it. If
  only one option fixes it, say so instead of inventing alternatives.

### M-037, 2026-11-01: A gap described without reading the code that closes it

- **What happened:** in my second code review, Claude described a gap in the
  hover test (gap (a), my explain-back question): after a failed pre-check,
  "the take-off continues to 0.5 m and the drone only lands at shutdown".
  Claude hadn't read `run_tick_loop`, which disconnects, and so lands, right
  after the tick loop returns.
- **Why it was wrong:** a safety claim made from memory of the design, not
  from the code. It sent my review after a gap that, in that form, wasn't
  there.
- **How I caught it:** I read `run_tick_loop` while answering the question.
- **Would a Claude review have caught it?** Maybe: a review that reads
  `start_up.py` would see the shutdown, but the claim was in conversation,
  not in a file a review reads.
- **Kind:** safety design.
- **Pattern:** safety-judgment.
- **Guard:** Q-20.
- **Takeaway:** before describing what happens after a failure, read the
  code path to its end, including the program's shutdown.

### M-036, 2026-11-01: A backlog item written and dropped without checking or measuring

- **What happened:** Claude wrote backlog #33 (logging runs inside the tick)
  without checking ADR-0028, which had already chosen plain logging and
  planned a switch to background threads if writes proved slow. Later Claude
  proposed removing #33 before anything was measured.
- **Why it was wrong:** both steps skipped what was known: an accepted ADR
  on the same question, and the project's rule to measure before deciding.
  When I pushed back, the measurement showed console output into a pipe
  stalling ticks for up to 0.44 s (ADR-0035).
- **How I caught it:** I asked to measure before removing it.
- **Would a Claude review have caught it?** Probably not: it was a
  recommendation.
- **Kind:** recommendation.
- **Pattern:** recommendation.
- **Guard:** working rule 5.
- **Takeaway:** before writing or dropping a backlog item, check the ADRs on
  the same question, and measure a performance risk before calling it small.

### M-035, 2026-11-01: A key named where the code handles a signal

- **What happened:** code, tests and log messages said "Ctrl+C" for what the
  program actually receives: the operating system's interrupt signal
  (SIGINT), which other tools can send too. The tests sent it with
  `signal.raise_signal` while their docstrings said "pressing Ctrl+C", and
  the start-up code logged "Ctrl+C pressed again" as a fact.
- **Why it was wrong:** it's like naming a game's quit command after one of
  its key bindings. A field-test log is evidence, and it would record a key
  press that may not have happened: PyCharm's Stop button may send the same
  signal (ADR-0027 still has to check).
- **How I caught it:** reading the adapter's comments in my second code
  review. Coming from games, I expected commands, not raw inputs.
- **Would a Claude review have caught it?** Probably not: the wording was the
  same everywhere, accepted ADRs included, and "Ctrl+C" is the everyday name
  for this signal in command-line programs.
- **Kind:** communication.
- **Pattern:** vocabulary.
- **Guard:** Q-42.
- **Takeaway:** name what the code receives (a signal, a command), not the
  raw input that usually sends it; only instructions for the operator name
  the key. The glossary now has *Interrupt signal*, and the coding style has
  the rule.

### M-034, 2026-11-01: A local named for when it was fetched, not what it holds

- **What happened:** in the Crazyflie adapter, three functions called the
  position estimate `latest`, although the coding style already said to
  name things after what they hold, not how they were obtained. The
  `_may_be_flying()` docstring in the same diff was also hard to follow.
- **Why it was wrong:** `latest` says when a value was fetched, not what it
  is, so the reader has to look back to know it's the position estimate.
- **How I caught it:** reading the adapter's diff in my second code review.
- **Would a Claude review have caught it?** Maybe: the rule was written down,
  but no review question asks about local names.
- **Kind:** communication.
- **Pattern:** vocabulary.
- **Guard:** none yet.
- **Takeaway:** the naming rule applies to local variables too. The coding
  style now says so, with `latest` as the example.

### M-033, 2026-11-01: A behavior's failure rule chosen without asking

- **What happened:** Claude wrote the hover test so that its first refused
  request ends the test, and pinned that with a test, without asking me and
  without noting that it goes against ADR-0020 ("keep going when it's safe,
  retrying where it makes sense").
- **Why it was wrong:** how a behavior handles a failure is error strategy,
  which CLAUDE.md counts as architectural, and an exception to an accepted ADR
  needs a decision. I kept the rule, for my own reason (the hover test is a
  test), and ADR-0033 now lets each field test choose.
- **How I caught it:** in my second code review, Claude said the hover test
  treats any refusal as a failure, and I asked why the whole flight would fail
  over a refusal that isn't a safety concern.
- **Would a Claude review have caught it?** Probably not: the rule looked
  deliberate and had its own test, and no review question asked whether a
  behavior's failure handling follows ADR-0020.
- **Kind:** design.
- **Pattern:** how-I-work.
- **Guard:** Q-13.
- **Takeaway:** a rule for what code does on a failure (stop, retry or carry
  on) is a decision: check it against ADR-0020 and ask.

---

## Mistakes Claude caught itself

### M-273, 2026-11-25: The first fix for #162's case-index finding checked something a planted off-by-one left unchanged

- **What happened:** fixing the review's finding that no case checked where the link was lost, Claude first asserted only that the call at the case's index in `link.mock_calls` is the listed call, with a comment saying the link was therefore lost just before it. That compares the run's calls with the list, not where the loss came: a planted off-by-one in the fake failed only 6 tests in the whole file. Caught by Claude's bug planting before the fix was reported. The fake now notes the index at the loss and each case checks it, so the same plant fails all 71 cases.
- **Kind:** testing.
- **Pattern:** weak-test.
- **Guard:** a check meant to pin where something happened compares the place noted at the event, and the plant that moves the event runs before the fix is called done.
- **Takeaway:** weak-test is past its third entry: the bug-planting tool (backlog #152) is where a plant for each new check becomes a mechanism.

### M-272, 2026-11-25: The review's failure scenario for the fake's assert was a loss the adapter never hears of

- **What happened:** the project review of #162 reported that the fake's `assert` in `_wait_for_params` would come out behind the lost link's error, with "a test that calls `fake_cflib.lose_the_link()` before `adapter.connect()`" as its scenario. In that scenario the adapter never hears of the loss: its `connection_lost` callback isn't registered until `connect()` opens the link, so the AssertionError comes out as it is. Caught by Claude's bug planting for the fix: the planted misuse failed with the old `assert` too. The hole is real for a link lost after the callback is registered, such as while the link opens: planted that way, the misuse passes with the `assert` and fails with `pytest.fail`.
- **Kind:** communication.
- **Pattern:** said-without-checking.
- **Guard:** a review finding's failure scenario is traced to its end, or planted, before it's reported (Q-20).
- **Takeaway:** Q-20 asks it of claims about failures in the code; it holds for a review's own scenarios too.

### M-271, 2026-11-25: cflib's full link close can hang on a lost link, and no review asked whether its check could change on another thread

- **What happened:** the facts register said `SyncCrazyflie.close_link()` does nothing once `disconnected` has been called (2026-11-21), and `connect()`'s cleanup and `disconnect()` relied on it after a lost link. The project review of #162 asked Q-03 of cflib's own code: the close checks `is_link_open()`, then creates the event its `disconnected` callback sets, and a lost link's callback that runs on cflib's radio thread between the two removes itself without setting it, so the close waits with no end. ADR-0095's "connect() raises within its time limits" assumed the close returns. Read in the source, never seen. Backlog #163.
- **Kind:** design.
- **Pattern:** window-between-steps.
- **Guard:** Q-03's question about a guard that changes on another thread is asked of a library's own check-then-wait code too, with the answer in the facts register.
- **Takeaway:** window-between-steps is past its third entry; no cheap mechanism finds races in a library's code, so the question stays.

### M-270, 2026-11-25: ADR-0095 chained the step's error as the lost link's cause, which Python prints as the reverse of what happened

- **What happened:** Claude's recommendation for ADR-0095, built in #162, raised the lost link's error `from` the failed step's error. Python prints that as "The above exception was the direct cause of the following exception", so a rescue landing over a dropped link would read "Flow deck not detected" as the cause of the loss, a deck problem that never happened. Caught by Claude's project review of #162 (Q-43). Joe chose to raise it while handling the step's error, which keeps that error as its context, and to reword ADR-0095 and ADR-0029's status before their first commit.
- **Kind:** communication.
- **Pattern:** message-misstates-outcome.
- **Guard:** an error raised while handling another keeps it as its context, with no `from`, unless the other really caused it; read the traceback Python prints before choosing (Q-43).
- **Takeaway:** the test now pins the chain (`__context__` set, no `__cause__`, the context not suppressed), so the change can't come back unseen.

### M-269, 2026-11-25: #162's lost-link tests didn't check where each case lost the link, and three more gaps

- **What happened:** the project review of #162 found four gaps in Claude's tests: no case checked that the link was lost just before the call its ID names, so a drift in the call count would move cases with every test still passing (a planted off-by-one in the fake now fails all 71 cases); the fake's `assert` came out behind the lost link's error, so a misused fake passed; ADR-0095's Never line "the new code runs before the link close" was guarded only against a skipped close, not one moved after the check in a `finally`; and the fake didn't run the `disconnected` callbacks. All fixed, each proven by a planted bug except the last, which no code registers yet.
- **Kind:** testing.
- **Pattern:** weak-test.
- **Guard:** a test whose cases come from a listed run checks in each case that it acted where its ID says, and each Never line of the ADR gets a planted bug.
- **Takeaway:** weak-test is past its third entry: the bug-planting tool (backlog #152) is where planting each Never line becomes a mechanism.

### M-268, 2026-11-25: #162's records and docstrings said more than its code

- **What happened:** the project review of #162 found that ADR-0095 said the fake runs the `disconnected` callbacks, which it didn't; the parametrized test's name, the ADR index row and the brief said the link is lost before each of `connect()`'s cflib calls, where the cases start once the link is open; the brief counted 76 new tests for 77; `connect()`'s docstring promised the step's error as the cause, which a wait's own lost-link error lacks; `_added_block_ids`' docstring spoke of a block "added once the link is lost", which cflib doesn't add; and the drone interface's `connect()` docstring still named only a flying drone among its errors after *Lost link* widened (Q-35).
- **Kind:** communication.
- **Pattern:** records-ahead-of-code.
- **Guard:** before a record says what a test covers, read its parametrize and first case, and count tests with `pytest --collect-only`.
- **Takeaway:** records-ahead-of-code is past its third entry; the question stays (Q-39), as no cheap mechanism reads records against tests.

### M-267, 2026-11-25: "Recording" for the call list made at collection

- **What happened:** building #162, Claude named the cflib calls listed while pytest collects the test file a "recording" (`RECORDED_CALLS`, "the error the recording raised"), and the records repeated it, where the glossary's *Recording* is a run's JSON Lines file. Caught by Claude's project review of #162 (Q-41); Joe chose "list" (`LISTED_CALLS`).
- **Kind:** communication.
- **Pattern:** vocabulary.
- **Guard:** working rule 6 for every noun in a new name or docstring, everyday words included: a glossary term's word means that term (Q-41).
- **Takeaway:** vocabulary is past its third entry; the question stays.

### M-266, 2026-11-25: Test data computed at collection would have stopped the whole run when connect() raised

- **What happened:** building #162, Claude recorded the cflib calls for ADR-0095's parametrized test by running a connect when pytest collects the test file, assuming a failure there would stop only that file. pytest runs no test at all once collection has an error (facts register). Caught by Claude's bug planting: a new step in `connect()` that raised on the fake ended the run at collection. The recording now keeps its error, and `test_a_connect_with_every_block_is_recorded` raises it.
- **Kind:** testing.
- **Pattern:** said-without-checking.
- **Guard:** code that runs while pytest collects a test file catches its errors and fails a test with them, proved by planting a raise there.
- **Takeaway:** what a test tool does on an error is a fact about it too: check it in its source (working rule 1).

### M-265, 2026-11-25: The bug-planting script for #162 wrote CRLF into adapter.py and reported it restored

- **What happened:** Claude's bug-planting script read `adapter.py` with `read_text` and restored it with `write_text`, which writes CRLF on Windows, so the LF working copy (ADR-0079) came back CRLF. Its check compared text, which hides line endings, and printed "restored: True". Caught by Git's line-ending warning on the next diff, checked with `git ls-files --eol`; converted back to LF before any commit, which `.gitattributes` would have normalized anyway. M-169's takeaway, bytes and a checksum, wasn't followed. `docs/next-up.md` was CRLF in the working copy too, from the previous work session's edit (cause not found); converted to LF.
- **Kind:** testing.
- **Pattern:** environment.
- **Guard:** a planting script reads, writes and compares bytes (M-169), and `git ls-files --eol` shows `w/lf` after it.
- **Takeaway:** a third line-endings slip, after M-169 and M-171. ADR-0079 accepted that a script can still write CRLF, with no fitness function; the bug-planting tool (backlog #152) is where restoring bytes becomes a mechanism.

### M-264, 2026-11-25: Backlog #161 named one step of a link lost while connecting and missed the others

- **What happened:** the project review of #157 stage 5 found that a link lost while connecting ends `connect()` with cflib's `AttributeError` from a log block (M-252), and backlog #161 described that one step. Its guard, Q-03 for each cflib call `connect()` relies on, wasn't asked of the other calls, and stage 6's review, which moved the deck check, didn't report them either: after a lost link cflib empties its parameter values but still counts them as fetched, so the Flow deck check reads "no deck" and the run ends with "Flow deck not detected"; opening the link and reading the parameters wait out their time limits; and the Buzzer deck check logs "No Buzzer deck". Caught by Claude tracing every step of `connect()` for `/decide` #161 (2026-11-25), before the options; ADR-0095 covers them.
- **Kind:** design.
- **Pattern:** window-between-steps.
- **Guard:** Q-03 asked of every library call in the function, not only the one that showed the problem, with each answer in the facts register.
- **Takeaway:** the mechanism M-252 asked for is decided: ADR-0095's test loses the link before each of `connect()`'s cflib calls (backlog #162).

### M-263, 2026-11-25: Two names in stage 6's link part meant something other than their code

- **What happened:** building #157 stage 6, Claude named the link close's keyword `may_be_flying`, the glossary's *May be flying*, for "airborne or the drone's state unknown", where `TakeOffAndLanding.may_be_flying()` is False during a connect with the state unknown; and named a property `is_open` that is also true while the link opens and after a lost link, which `disconnect()` relies on. Caught by Claude's project review of the stage (2026-11-25); Joe chose `radio_link_only` and `has_link_to_close`, in the move commit `f38578b`.
- **Kind:** communication.
- **Pattern:** vocabulary.
- **Guard:** working rule 6 for every new name, keyword arguments included: a name that spells a glossary term means that term exactly, and a yes-or-no name says when it's true, in-between states included (Q-38).
- **Takeaway:** the pattern is past its third entry, and no cheap mechanism exists: a lint can't tell what a name means. The question stays.

### M-262, 2026-11-25: The facts register kept pointing at adapter.py after its code moved

- **What happened:** five rows (`send_packet`, the incoming handler's callbacks, `LogConfig`, `HighLevelCommander`, `Commander`) still named only `adapter.py` after the refactor's stages moved that code out of it. Stage 6's own update then swapped `adapter.py` for `link.py` on two rows whose adapter code stayed (`_close_link`, `disconnect()`) and missed the parameter writes row. Caught by Claude's project review of stage 6 (2026-11-25); fixed in the stage's records.
- **Kind:** process.
- **Pattern:** records-ahead-of-code.
- **Guard:** each move searches the facts register for the old file's name and re-reads every row it finds against both files, as part of the move's records.
- **Takeaway:** the pattern is past its third entry, and no cheap mechanism exists: a test can check that a named file exists, and `adapter.py` still does.

### M-261, 2026-11-25: Stage 6's move-only report named one difference and missed two

- **What happened:** Claude reported stage 6's build as move-only except for the link's creation moving inside `connect()`'s `try`. It missed two more: cflib's driver set-up now runs after the flag resets and the parts' rebuild, and a late cflib callback from an earlier link now reaches that link's part, not the adapter's own fields. The move check passed because it compares moved bodies, not when or from where they run. Caught by Claude's project review (2026-11-25); the move commit `f38578b` names all three.
- **Kind:** communication.
- **Pattern:** records-ahead-of-code.
- **Guard:** a move-only claim lists, beside the check's verdict, each moved call whose place in its caller changed and each callback whose owner changed, read off the caller's diff (ADR-0093's D14).
- **Takeaway:** the pattern is past its third entry, and no cheap mechanism exists: the move check compares bodies, and where they run needs reading.

### M-260, 2026-11-25: Three cflib facts behind stage 6's move were read but not registered

- **What happened:** to show that a raise in the link's creation finds no link to close, Claude read in cflib's source that a `Crazyflie` made with no link starts no thread, that `SyncCrazyflie.__init__` only stores what it's given and that `Caller.add_callback` only appends, but didn't add them to the facts register, as CLAUDE.md asks of a fact not there. Caught by Claude's project review (Q-01, 2026-11-25); added with the stage's records.
- **Kind:** process.
- **Pattern:** how-I-work.
- **Guard:** working rule 1: a fact read in source to back a claim goes into the register in the same step, before the claim is written down.
- **Takeaway:** the pattern is past its third entry, and no cheap mechanism exists; Q-01 catches it at review.

### M-259, 2026-11-25: The link part's rename left the old name in a waiting explain-back

- **What happened:** renaming `_close_radio_link_only` to `close_radio_link_only` in stage 6, Claude updated the code, the fitness function and the glossary, but E11 in the next-up brief and its notes in `drafts/explain-back-notes.md` still quoted `on_abandon=self._close_radio_link_only`. Caught by Claude's project review (2026-11-25); fixed in the stage's records.
- **Kind:** process.
- **Pattern:** records-ahead-of-code.
- **Guard:** a rename is searched for across the whole repository, the git-ignored `drafts/` included (ripgrep skips ignored files unless given `--no-ignore`).
- **Takeaway:** the pattern is past its third entry, and no cheap mechanism exists: a test can't tell a stale quote from a quote of history.

### M-258, 2026-11-25: The adapter's URI, cache directory and disconnect with no link had no test

- **What happened:** bug planting for #157 stage 6 found three plants no test failed, on the code before the move too: `connect()` passing cflib the default URI or the default cache directory instead of the adapter's, and `disconnect()` going on with no link, which the start-up's `finally` calls after a failed `connect()`. Caught by Claude's bug planting (2026-11-25); tests in `1d51b96`.
- **Kind:** testing.
- **Pattern:** weak-test.
- **Guard:** bug planting covers each argument the adapter passes on to cflib and each early return, not only the logic between them.
- **Takeaway:** bug planting is the pattern's mechanism; this widens what it plants.

### M-257, 2026-11-25: The move-only check's first run reported a change that wasn't there

- **What happened:** for #157 stage 6, Claude's move-only check compared `CrazyflieLink.open()` with the lines it came from in `connect()`, but dropped `open()`'s first line without dedenting the rest, so its first run reported one difference, in indentation only. Caught by Claude reading the check's output (2026-11-25); after the fix it reported 70 items moved or kept unchanged.
- **Kind:** testing.
- **Pattern:** weak-test.
- **Guard:** a check script's verdict counts only once it has passed on the real change and failed on planted ones; stage 6's plants put two changes in moved code that only the check can catch.
- **Takeaway:** the pattern is past its third entry, and bug planting is its mechanism; this extends it to the check script. Nothing new to build.

### M-256, 2026-11-25: A Python fix sent through a Bash heredoc lost half its backslashes

- **What happened:** building #157 stage 6's move-only check, Claude rewrote one of its functions as a Python string inside a Bash heredoc. The Bash tool passed each doubled backslash on as a single one, so two newline escapes became real line breaks and the script wouldn't parse (checked afterwards: a doubled backslash in a heredoc reaches Python as one). Caught by Python's syntax error (2026-11-25); fixed with the editor.
- **Kind:** environment.
- **Pattern:** environment.
- **Guard:** code that holds a backslash escape is written with the editor tools, never sent through a heredoc.
- **Takeaway:** no cheap mechanism: the guard is a habit, and a syntax error or the checks catch a slip.

### M-255, 2026-11-25: The take-over list change went against ADR-0093's move-only rule, unflagged

- **What happened:** for #157 stage 5, Claude offered listing `adapter.py` in the take-over fitness function as a pass-through (M-251) without saying that it changes a test body in the move commit, which ADR-0093's D14 and Never line rule out. Stage 4's move commit (`6710a79`) had done the same to `BLOCKING_FUNCTIONS`, also unflagged. Caught by Claude's project review of stage 5 (2026-11-25), in the architecture audit's move-only question; Joe chose to note it in the move commit's message and leave ADR-0093 as it is.
- **Kind:** recommendation.
- **Pattern:** recommendation.
- **Guard:** an option that touches code an ADR governs is checked against that ADR's Never and Always lines before it's offered (CLAUDE.md: point out a conflict with an accepted ADR and ask).
- **Takeaway:** the pattern is past its third entry; here the mechanism was the architecture audit's move-only question, which caught it before any commit. Nothing new to build.

### M-254, 2026-11-25: Stage 5's comments and records said more than the code

- **What happened:** building #157 stage 5 (2026-11-25), Claude marked the adapter's log-block re-exports test-only, though `programs/start_up.py` imports two of them, `TAKE_OFF_BLOCK_DURATION` and `TAKE_OFF_PERIOD_MS`; gave `LogBlocks` a docstring that copied `connect()`'s order ("`connect()` opens the link after building this"), M-250's pattern a day later; and wrote "not yet reviewed or committed" into backlog row #157, which the records commit would carry. Caught by Claude's project review of stage 5 (2026-11-25): `start_up.py` now imports them from `log_blocks.py`, the docstring points to ADR-0093, and the clause is gone.
- **Kind:** communication.
- **Pattern:** records-ahead-of-code.
- **Guard:** before marking an import test-only, search `src/` and `tools/` for its importers, not only `tests/`; a fact another module owns is pointed to, not copied (`docs/coding-style.md`); a record never says what the commit carrying it makes false (Q-46).
- **Takeaway:** the docstring repeats M-250 within a day, and `/project-review`'s step 4 read is what catches it; no cheap mechanism. The test-only labels go with #158's forwards, so a check for them isn't worth building.

### M-253, 2026-11-25: "Session", "drone time" and "part" in the Crazyflie adapter's comments

- **What happened:** Claude's comments in `connect()` called a new connection "a new session" (stage 5 rewrote one of them), and `take_off_and_landing.py` said "sent this session", where the glossary's *Session* is a trip of field tests; stage 5's rewrite added "no drone time", which the glossary calls the drone's timestamp; and since stage 3 the code has used *part* as a term with no glossary row, against CLAUDE.md's rule to propose a term first. Caught by Claude's project review of #157 stage 5 (2026-11-25): reworded to "link" and "no earlier drone timestamp", and Joe approved a glossary row for *Part*.
- **Kind:** communication.
- **Pattern:** vocabulary.
- **Guard:** working rule 6, applied to each word of a new or rewritten comment, including words the glossary already uses in another sense (Q-38, Q-41).
- **Takeaway:** the pattern is past its third entry, with no cheap mechanism: a lint can't tell a glossary word used in another sense. The questions stay.

### M-252, 2026-11-25: A link lost while connecting surfaces as cflib's AttributeError

- **What happened:** the Crazyflie adapter's `_add_log_block` (now in `log_blocks.py`) relies on cflib's `Log.add_config` raising for a block it can't add, but without a link it only logs and returns, so the block's `start()` raises AttributeError (cflib 0.1.34, `log.py` 461-464). A link lost just after `connect()`'s status wait succeeds ends the run with that error instead of the lost link's; it still fails safe, since `connect()` closes the link. Caught by Claude's project review of #157 stage 5 (2026-11-25), in code older than the split; Joe put it in the backlog (#161) for the link stage.
- **Kind:** design.
- **Pattern:** window-between-steps.
- **Guard:** Q-03, for each cflib call `connect()` relies on: what it does once the link is already gone, read in the source, with the fact in the register.
- **Takeaway:** the pattern is past its third entry; the cheap mechanism is a test whose fake cflib drops the link between two steps of `connect()`, which backlog #161 asks for.

### M-251, 2026-11-25: A recommended constructor keyword broke the take-over fitness function

- **What happened:** for #157 stage 5, Claude recommended passing the take-over setting to the new log-block part as a constructor keyword, `LogBlocks(..., take_over_flight=...)`, so the moved body stays unchanged. It didn't search for rules already written about that name: `test_only_the_rescue_landing_program_asks_to_take_over_a_flight` (ADR-0038) pins which files pass `take_over_flight=` in a call, and the adapter became a third. Caught by the first test run after the move (2026-11-25); Joe chose to list the adapter in the test as a pass-through, like `start_up.py`.
- **Kind:** recommendation.
- **Pattern:** recommendation.
- **Guard:** working rule 5, for a name or keyword an option adds: search `tests/architecture/` for it too, not only the backlog and the ADR index.
- **Takeaway:** the pattern is past its third entry, and here the mechanism worked: the fitness function caught the option at its first test run, before any commit. Nothing new to build.

### M-250, 2026-11-25: Two docstrings in stage 4's take-off and landing part said more than the code

- **What happened:** writing #157 stage 4 (2026-11-24), Claude gave `TakeOffAndLanding.emergency_stop` the docstring "clear the flight state together, as `stop_motors` does", though unlike `stop_motors` it records no motor stop, on purpose (ADR-0058). The class docstring also copied a count that `connect()` owns, "replaces it twice", which later stages change. Caught by Claude's project review of stage 4 (2026-11-25); both reworded, in commit E.
- **Kind:** communication.
- **Pattern:** records-ahead-of-code.
- **Guard:** a docstring that says "as X does" is checked against both methods line by line, and a fact another module owns is pointed to, not copied (`docs/coding-style.md`).
- **Takeaway:** records-ahead-of-code is past its third entry, and no cheap mechanism checks a docstring's comparison, so it stays a review check (`/project-review` step 4).

### M-249, 2026-11-25: A comment that read backwards and a docstring that said "turned into", in ADR-0094's fix

- **What happened:** the comment on `run_with_time_limit`'s late raise said "so the lock error doesn't become its context, as if the interrupt signal had come while an error was being handled", which reads as if the raise were meant to look that way. `_interrupt_hidden_in`'s docstring said CPython "turned" the interrupt into the error, when the error only carries it as its context, and left out the None it returns otherwise. The new debug line also put the capitalized step name mid-sentence ("during Opening the link"). Caught by Claude's project review (2026-11-25); all three reworded before the commit.
- **Kind:** communication.
- **Pattern:** vocabulary.
- **Guard:** read each new comment as someone who knows only the code and the glossary, before the review does (`/project-review` step 4).
- **Takeaway:** the comment that explains why code is shaped oddly is the one whose misreading undoes the code. M-173's mechanism, the fresh-context read, didn't run on this change (Joe chose to skip it, to save usage), so the review's own read caught it.

### M-248, 2026-11-25: "Lock error" in ADR-0094's code, where the glossary's "lock" is the drone lock

- **What happened:** ADR-0094's code called CPython's `RuntimeError: release unlocked lock` a "lock error" in a test name, a debug line and two docstrings, with no glossary row, though in the glossary "lock" means the drone lock (*Drone lock*, and "locked" in the drone status). Caught by Claude's project review (Q-38, Q-41); Joe chose "threading lock error", with no glossary row (2026-11-25).
- **Kind:** communication.
- **Pattern:** vocabulary.
- **Guard:** working rule 6, for words the glossary already uses in another sense, not only for missing terms (Q-41).
- **Takeaway:** in this codebase a word the glossary owns (lock, flying, stop) reads in its glossary sense, whatever the code means by it. Vocabulary is past its third entry, and no cheap mechanism can tell which sense a word is used in, so Q-41 stays.

### M-247, 2026-11-25: ADR-0094's fix logged the threading lock error before the cleanup

- **What happened:** the fix's first version logged the hidden threading lock error, with its traceback, at the top of `run_with_time_limit`'s `except` block, before `step.abandon()` and `on_abandon`. A second interrupt signal landing in that log call would have left the block without the cleanup. Caught by Claude's project review (Q-19); the log now comes after the cleanup, with a comment saying why.
- **Kind:** design.
- **Pattern:** window-between-steps.
- **Guard:** in an `except` block that cleans up, the cleanup comes first and any logging after it (`time_limit.py`, its order pinned by a test; and Q-19, which names log lines).
- **Takeaway:** Q-19 already asks about log lines; the build didn't ask it, the same day as M-246 and about the same window. No cheap mechanism knows which calls clean up, so the question stays.

### M-246, 2026-11-25: The interrupt signal landing inside a threading wait came out as CPython's lock error

- **What happened:** three tests written 2026-11-02 (`878c16f`) send the interrupt signal from the helper thread as a step starts. CPython 3.12 can raise the KeyboardInterrupt while `Thread.start()`'s wait has its lock released, and `Event.wait`'s `with` block then raises `RuntimeError: release unlocked lock` instead. The tests failed at random (once in 117 runs on its own on `479f64f`), and a Ctrl+C while connecting could end the program as an error, with exit code 1 instead of 130. `run_with_time_limit` caught every exception, so its cleanup was right; only the exception's type was wrong. Caught by Claude when the check run before #157 stage 4's review failed. Fixed by ADR-0094.
- **Kind:** design.
- **Pattern:** window-between-steps.
- **Guard:** ADR-0094: `run_with_time_limit` raises the interrupt signal that CPython hides in a lock error, with a test that sends no real signal; and Q-19 (an interruption landing between two lines).
- **Takeaway:** the pattern is past its third entry, and here the mechanism is ADR-0094's code. The interruption landed between the standard library's lines, not the project's.

### M-245, 2026-11-24: A work order's bug-planting script was copied from a scratch file a failed edit had broken

- **What happened:** writing #157 stage 4's hand-off, Claude copied its first bug-planting script from the scratchpad to `drafts/157-stage-4/` without checking it, though a failed edit had broken that scratch copy earlier in the work session (a syntax error). Caught when Claude re-ran the script for the order's expected results; rewritten and re-run before the order named it.
- **Kind:** process.
- **Pattern:** how-I-work.
- **Guard:** the handoff skill's step 3: name a script in an order only after running it from where it's saved (added with Joe's OK, 2026-11-24); and M-233's: after a script writes or copies a file, read or run what it wrote.
- **Takeaway:** the second time a script's output went unchecked (M-233), so it climbed the ladder's second step: a template line, in the handoff skill.

### M-244, 2026-11-24: The blocking-call fitness function missed a blocking call imported under another name

- **What happened:** the scanner matched a call by the name written where it's called and recorded no import alias, so `from time import sleep as pause`, then `pause(0.1)` in a tick method, passed all six rules. Found by `/project-review` of `1cc5081`. Fixed in `531c638`: an alias counts as its original name, with three tests, proven by planting.
- **Kind:** testing.
- **Pattern:** weak-test.
- **Guard:** a scanner that matches by name lists every way a name can change (an import alias, an assignment, a stored callable) and has a test for each (`REVIEW.md` Q-32).
- **Takeaway:** matching by name needs every renaming closed, not only the stored callable ADR-0093 named.

### M-243, 2026-11-24: The fitness function read the drone interface's methods by one decorator spelling

- **What happened:** `drone_interface_methods` counted a method only under a bare `@abstractmethod`, and its guard test named 5 of the 15 methods, so one written with `@abc.abstractmethod` would have dropped out of rule 1 unnoticed. Found by `/project-review` of `1cc5081`. Fixed in `531c638`: it reads every method but the double-underscore ones, with a test on made-up code.
- **Kind:** testing.
- **Pattern:** weak-test.
- **Guard:** a fitness function's reader of real code doesn't depend on how the code is spelled, or has a test for each spelling (Q-32).
- **Takeaway:** a guard that checks a few names can't catch the ones it leaves out.

### M-242, 2026-11-24: Two forms the blocking-call scanner handles had no test

- **What happened:** code outside any function (filed as the file's `<module>`) and a class defined inside a function had no test, though `REVIEW.md` Q-32 asks for one per form. Found by `/project-review` of `1cc5081`. Fixed in `531c638`: three tests, proven by planting.
- **Kind:** testing.
- **Pattern:** weak-test.
- **Guard:** before calling a scanner's tests complete, list each `case` of its `match` and name the test that reaches it (Q-32).
- **Takeaway:** list the scanner's branches, not the forms that come to mind.

### M-241, 2026-11-24: The Blocking call glossary row read as covering locks the check skips

- **What happened:** the row defined a blocking call as one that waits until "something happens" and said only `connect()` and `disconnect()` may reach one, but every tick's `take_snapshot` takes the telemetry buffer's lock, and the fitness function counts no lock. Found by `/project-review` of `1cc5081`. Fixed in `531c638`, with Joe's OK: the row and the test's "Not counted" list name the locks.
- **Kind:** communication.
- **Pattern:** records-ahead-of-code.
- **Guard:** a definition with "only" is checked against a search for its exceptions in the code, as M-235's guard asks of docstrings (Q-32).
- **Takeaway:** a general definition ("until something happens") reaches further than the list after it.

### M-240, 2026-11-24: A fitness function's test name said "only" where it checked reachability

- **What happened:** `test_every_blocking_function_runs_only_inside_connect_or_disconnect` checked only that `connect()` or `disconnect()` reaches each blocking function; the "only" comes from rules 1 and 3 together. Found by `/project-review` of `1cc5081`. Fixed in `531c638`: renamed `..._is_reached_from_connect_or_disconnect`, with a docstring that says how the three rules combine.
- **Kind:** communication.
- **Pattern:** records-ahead-of-code.
- **Guard:** M-235's guard, for test names too: an "only" in a name is checked against what its assert does (Q-32).
- **Takeaway:** the pattern's second entry today. No cheap mechanism checks what a name claims, so the question stays.

### M-239, 2026-11-24: ADR-0093 narrowed two older rules without marking either

- **What happened:** ADR-0093's status line said it narrows ADR-0002, but ADR-0002's own status line wasn't marked (`REVIEW.md` Q-33). Its design also has the parts pass a cflib object between modules, against ADR-0004's rule and CLAUDE.md's "Never: Pass a cflib object or an untyped value across a module boundary", which the ADR didn't name. Found by `/project-review` of #157's stage 3. Joe chose to scope the rule to the modules that import cflib, now in ADR-0093, both older ADRs' status lines, CLAUDE.md and `ARCHITECTURE.md` section 3.
- **Kind:** process.
- **Pattern:** how-I-work.
- **Guard:** before an ADR is accepted, check its design against CLAUDE.md's Never and Always lists, and mark the status line of every ADR it narrows (Q-33).
- **Takeaway:** a design that needs an exception to a standing rule says so in its own ADR, not in a later review.

### M-238, 2026-11-24: ADR-0093 and `commands.py` used Hand-over for more than the glossary's meaning

- **What happened:** The glossary's Hand-over was only the switch at the end of the initial climb. ADR-0093 ("three orders matter: the hand-over"), `commands.py`'s heading and the brief's E10 used it for any high-level move after a setpoint stream. Found by the fresh-context read and `/project-review` (Q-41). Joe widened the glossary's row.
- **Kind:** communication.
- **Pattern:** vocabulary.
- **Guard:** working rule 6: read a glossary term's row, not only its name, before using it in a new sense; `REVIEW.md` Q-41.
- **Takeaway:** a code name older than the glossary row can carry a wider meaning than the row gives it.

### M-237, 2026-11-24: The glossary's Transcript test row repeated the overclaim M-232 fixed in ADR-0093

- **What happened:** The new row said a transcript test "fails when a change reorders or alters a send". It was written in the same change that fixed M-232 in ADR-0093: no flight reaches the last-resort landing, so its order isn't caught. Found by `/project-review` (Q-40). Fixed with Joe's OK: the row now says a send no flight reaches needs its own test.
- **Kind:** testing.
- **Pattern:** weak-test.
- **Guard:** a fix for an overclaim searches the records written with it (the glossary, the index, the backlog) for the same claim; `REVIEW.md` Q-40.
- **Takeaway:** one claim is often written in several records at once, and a fix in one leaves the rest.

### M-236, 2026-11-24: `ARCHITECTURE.md` kept a module name and a Built status that ADR-0093 had changed

- **What happened:** ADR-0093 named the take-off and landing module `take_off_and_landing.py`, but `ARCHITECTURE.md` section 7 kept `flight_phases.py`. Its Needs cell, set to "not built" with the decision, stayed that way after stages 1 to 3 were built. Found by `/project-review`. Fixed with Joe's OK.
- **Kind:** process.
- **Pattern:** records-ahead-of-code.
- **Guard:** working rule 3, for `ARCHITECTURE.md` too: when a decision names a module or a stage is built, search `ARCHITECTURE.md` for the old name and update its row's Needs cell.
- **Takeaway:** the architecture map's target table is a record like the index, and goes stale the same way.

### M-235, 2026-11-24: `commands.py`'s docstrings said more than its code does

- **What happened:** #157's stage 3 wrote "every send" in `commands.py`'s module and class docstrings and in the adapter's `_commands` field. But the thrust base write, the log blocks and both link closes stay in `adapter.py`, as ADR-0093's table plans. `go_to_relative`'s docstring said `linear` is passed on, when it goes only when True. The class docstring's reason for the lookups ("connect() replaces both") hid the real one: `connect()` replaces them after building the part. Found by `/project-review`. Fixed before the first commit.
- **Kind:** communication.
- **Pattern:** records-ahead-of-code.
- **Guard:** an "every" or "only" in a docstring is checked against a search for its exceptions (`REVIEW.md` Q-32), and a "because" names the step that makes it true.
- **Takeaway:** a moved module's "every" needs checking against what stayed behind.

### M-234, 2026-11-24: The transcript fake relied on two cflib facts with no facts-register rows

- **What happened:** The transcript tests' fake says cflib's `param.get_value` returns text and raises `KeyError`, and that `SyncCrazyflie` keeps its `Crazyflie` as `.cf`. Neither was in the facts register, which CLAUDE.md asks for ("one not there is checked, then added"). Found by `/project-review` (Q-01). Checked in source the same day and added.
- **Kind:** process.
- **Pattern:** how-I-work.
- **Guard:** CLAUDE.md's facts-register rule applies to a test fake's docstrings too; `REVIEW.md` Q-01.
- **Takeaway:** a fake states facts about the library it stands in for.

### M-233, 2026-11-24: A script copied E9's heading into the explain-back notes for E10

- **What happened:** A script that added E10 to `drafts/explain-back-notes.md` copied E9's heading for it, text and all ("#157 stage 1"). Caught and fixed at once.
- **Kind:** process.
- **Pattern:** how-I-work.
- **Guard:** after a script writes to a file, read the lines it wrote.
- **Takeaway:** a copy-and-edit script carries over whatever it doesn't replace.

### M-232, 2026-11-24: ADR-0093 said the transcripts catch a reorder of three orders, but none of its flights reaches the third

- **What happened:** ADR-0093's Failure modes name three send orders that matter (the hand-over, the motor stop then the release, the land then the release) and say "The transcripts catch a reorder". None of D15's five scripted flights reaches the last-resort landing, so no transcript covers its land, then release (ADR-0084): only the unit test `test_a_landing_that_raises_sends_the_firmwares_land_then_the_release_then_closes_only_the_radio_link` guards it. Found while designing #157's transcript tests, before any was built. Joe kept five flights, with the unit test as that order's guard, and ADR-0093 now says so (edited before its first commit).
- **Kind:** testing.
- **Pattern:** weak-test.
- **Guard:** a claim that tests catch a list of cases names the test or flight that reaches each one, and bug planting a swap of each order proves it.
- **Takeaway:** a list of cases in a Failure mode gets checked one case at a time against the tests meant to reach it.

### M-231, 2026-11-24: ADR-0093 counted 45 test lines that set the adapter's log level, but there are 49

- **What happened:** ADR-0093's D14 says a prep commit moves "the 45 test lines that set the log level on the adapter's logger". 45 counts two forms, `logger=adapter_module.logger.name` (33 lines) and `logger=adapter_module.__name__` (12), and misses a third: `test_adapter_telemetry.py` sets it four times through its constant `ADAPTER_LOGGER`. Found by counting every form for #157's logger prep. Fixed: ADR-0093 now says 49 (edited before its first commit).
- **Kind:** process.
- **Pattern:** said-without-checking.
- **Guard:** working rule 1 applied to counts: search every form the code uses (a name, a string, a constant), and say which forms a count covers.
- **Takeaway:** one search pattern rarely finds every form of the same thing.

### M-230, 2026-11-24: `.gz` reading broke `read_recording`'s promise of a ValueError

- **What happened:** the #55 work session added `.gz` reading to `read_recording` with a test for a whole file only. `/project-review high` found that a cut-off `.gz` raises `EOFError` and a file that isn't gzip raises `BadGzipFile`, an `OSError`, where the docstring promises `ValueError`, and that a cut-off compressed file can't be read at all while a cut-off plain one drops its last line. Fixed: `_read_text` raises `ValueError` for each, with a test per case, proven by bug planting.
- **Kind:** testing.
- **Pattern:** weak-test.
- **Guard:** a new way to read input gets a test for each way it can fail, checked against the errors its function's docstring names. `REVIEW.md`'s map now sends `recording/` to Failures (Q-11, Q-13), which caught this.
- **Takeaway:** a second format behind the same reader brings the second format's errors with it.

### M-229, 2026-11-24: `/debrief`'s new step for committing scripts left out their recordings

- **What happened:** ADR-0092 says a committed analysis script reads only committed recordings and a debrief commits them, and its Consequences said "the ask is in `CLAUDE.md` and `/debrief`". The step added to `/debrief` asked about the scripts only and never mentioned recordings. `/project-review high` found it.
- **Kind:** process.
- **Pattern:** records-ahead-of-code.
- **Guard:** working rule 3: before an ADR says a step is in a skill, read the step against each bullet of the Decision.
- **Takeaway:** a rule copied into a skill gets checked against the whole Decision, not only the line it came from.

### M-228, 2026-11-24: The glossary called an unbuilt tool real, and ADR-0092 called built work unbuilt

- **What happened:** the glossary's Bug planting said it's "done by hand, or by the bug-planting tool (`tools/plant_bugs.py`)", which isn't built (#152). ADR-0092's Consequences still said the `analysis/` folder and `.gz` reading weren't built (#154) after the same change built them. `/project-review high` found both.
- **Kind:** process.
- **Pattern:** records-ahead-of-code.
- **Guard:** working rule 3; for a tool decided but not built, the glossary says "once it's built" and names the backlog row. After building part of an ADR, reread its Consequences as well as the index's Built column.
- **Takeaway:** ADR-0091's test (#153) and #143 are the mechanisms this pattern is waiting on.

### M-227, 2026-11-24: Searches that skipped `drafts/` reported C6 missing and missed Joe's no to a mutation-testing dependency

- **What happened:** Joe named C6 as his priority. Claude searched with ripgrep, which skips git-ignored files, and said "c6" wasn't anywhere in the repo's markdown. C6 (split the Crazyflie adapter) is defined in `drafts/2026-11-13-code-recommendations.md`. The same blind spot let `/decide #142` offer an off-the-shelf mutation-testing tool without saying that Joe had declined one on 2026-11-21 (D19 in that file). Claude found both later in the session, reading `drafts/` for another reason; ADR-0090 now cites D19.
- **Kind:** process.
- **Pattern:** said-without-checking.
- **Guard:** working rule 1: when a search for a term Joe uses finds nothing, search `drafts/` too (ripgrep's `--no-ignore`) before saying it doesn't exist.
- **Takeaway:** decisions still waiting to become ADRs live in `drafts/` (the 2026-11-13 code and workflow recommendations), so a search of the records alone can miss Joe's earlier answers.

### M-226, 2026-11-23: The closing comment on pull request #30 wrote backlog rows as GitHub links

- **What happened:** closing review pull request #30, Claude's comment said the findings moved to the backlog as "#149-#151". On GitHub, `#149` links to issue or pull request 149, not to backlog row 149. Claude noticed it right after posting.
- **Kind:** communication.
- **Pattern:** vocabulary.
- **Guard:** in text GitHub renders (comments, pull request bodies), write "backlog row 149", never a bare `#149`.
- **Takeaway:** a number's meaning depends on where it's read; the backlog's `#` and GitHub's `#` collide.

### M-225, 2026-11-23: Two docstrings rewritten after Joe's reply said they read fine

- **What happened:** Joe answered the review finding on `start_up.py:36` (the `RECORDING_DIRECTORY` and `command_line_arguments` docstrings) with "this reads fine to me", but an earlier work session's fixes rewrote both anyway. Claude found it comparing the working tree with the pull request's replies; Joe chose to revert them.
- **Kind:** process.
- **Pattern:** how-I-work.
- **Guard:** working rule 7: before fixing a review finding, read every reply in its thread; a reply that says it's fine closes it.
- **Takeaway:** a review finding is Joe's to confirm; the fix list comes from his replies, not from the findings as posted.

### M-224, 2026-11-23: A backlog row offered a fix that doesn't fix it

- **What happened:** backlog #149 (from the review of pull request #30) listed "move `start` inside the `try`" as a fix for a recording left without a header. With `start` inside the `try`, the interrupt signal between opening the file and writing the header reaches `finish`, which adds a last line to the file with no header, so `read_recording` still refuses it. Claude found it when Joe asked whether moving it was enough; the row is corrected.
- **Kind:** recommendation.
- **Pattern:** window-between-steps.
- **Guard:** working rule 2: read the code an option touches (here `finish`) before listing it as a fix.
- **Takeaway:** a fix for a cleanup gap is traced through every step after the gap, not only the step that opens it.

### M-223, 2026-11-23: ADR-0034 left an open question with no backlog row

- **What happened:** ADR-0034 says "What a reader does with an old version is decided with the first replay test", but no backlog row ever tracked it (the backlog and its git history searched on 2026-11-23). `CLAUDE.md` has asked for a row for each deferral since 2026-10-18. Claude found it while weighing ADR-0089's options.
- **Kind:** process.
- **Pattern:** how-I-work.
- **Guard:** backlog #150; `/decide`'s step 8, a row for each follow-up.
- **Takeaway:** an ADR's "decided later" is a follow-up, and gets its backlog row when the ADR is written.

### M-221, 2026-11-22: The next-up brief said 84 planted bugs for the recorder; it was 87

- **What happened:** the brief's "Done last" line for the recorder gave 84 planted bugs, a count taken before the last few were planted. The project review of the recorder caught it before the commit; fixed to 87.
- **Kind:** communication.
- **Pattern:** said-without-checking.
- **Guard:** working rule 4: a count in a record comes from the whole run, recounted when the record is written.

### M-220, 2026-11-22: New mock test names used terms not in the glossary

- **What happened:** three new tests in `tests/drone/test_mock_adapter.py` were named with "the motor cut limit" and "a velocity exactly its wait old", and a helper's docstring with "a setpoint timeout's limit". None is a glossary term, and "its wait old" is hard to parse. Caught by the project review of #133 part 2 (Q-38). Renamed in plain words: "the wait before the motors cut", "its wait before it stops following".
- **Kind:** communication.
- **Pattern:** vocabulary.
- **Guard:** working rule 6: check a new name's words against the glossary before using them.

### M-219, 2026-11-22: `TICK_PERIOD`'s docstring promised exactness that depends on `STALE_AFTER`

- **What happened:** `tests/loop/test_tick_step.py`'s `TICK_PERIOD = STALE_AFTER / 2.0`, chosen so it follows a change to `STALE_AFTER`, said "half of it stays exact in binary". That holds only while `STALE_AFTER` is exact, and the hover test compared its hover length with an exact float equality that relied on it. Caught by the project review of #133 part 2. The docstring now states the condition, and the comparison uses `pytest.approx`.
- **Kind:** communication.
- **Pattern:** said-without-checking.
- **Guard:** a docstring for a value computed from another module's constant states what its claim depends on.

### M-218, 2026-11-22: Backlog #133 removed while #142 still waited on it

- **What happened:** removing #133 (the boundary tests, done) left #142's "when" as "After the boundary tests (#133)": a trigger that had fired, pointing to a row that no longer exists, and missing from the next-up brief. M-213's guard, from the same day, says to search for a row's number before removing it. Caught by the project review of #133 part 2. #142's trigger now says it's due, and it's second in Next three.
- **Kind:** process.
- **Pattern:** said-without-checking.
- **Guard:** before removing a backlog row, search the docs for its number (M-213), and update each row that waits on it.
- **Takeaway:** repeats M-213, so the escalation ladder asks for a mechanism: backlog #144.

### M-217, 2026-11-22: Two mock "too long" tests checked a whole tick past the motor cut

- **What happened:** for #133 part 2 (rows 18 and 19), `test_an_initial_climb_without_updates_for_too_long_drops_the_drone` and `test_the_drone_drops_when_velocities_stop_arriving_for_too_long` checked the mock's motor cut one tick (0.05 s) past `SETPOINT_CUT_MOTORS_AFTER`, so a cut limit up to 2.049 s passed. Joe had chosen 0.01 s past for rows 14 and 20 because the same gap let a limit plus 0.04 s pass there (M-206). The plants run for the rows didn't include a limit plus 0.04 s. Caught by the project review; both tests now check 0.01 s past, and planting 2.04 s fails each one.
- **Kind:** testing.
- **Pattern:** weak-test.
- **Guard:** a test past a time limit checks 0.01 s past it, and a planted limit plus 0.04 s proves it.
- **Takeaway:** repeats M-206, so the escalation ladder asks for a mechanism: a limit plus 0.04 s among the bug-planting tool's plants (backlog #142).

### M-216, 2026-11-22: Two "mid hover" tick-step tests set up mid-climb

- **What happened:** `test_a_low_battery_mid_hover_lands_the_drone_before_the_run_ends` and `test_a_link_gone_quiet_mid_hover_lands_the_drone` ticked a fixed 4 times, commented "arm, take off, hovering". That held when written (`c4872d5`), but once ADR-0048's build gave the mock its initial climb (`9deb5a4`, 2026-11-07), the drone was still climbing at 0.1 m after those ticks, and nobody updated the count. Caught by Claude while halving the tests' tick period for backlog #140, by checking the drone's state after each setup tick. Fixed with a helper that ticks until the drone is at its take-off height.
- **Kind:** testing.
- **Pattern:** weak-test.
- **Guard:** a test reaches the state its name says by ticking until a condition holds, not by a fixed count of ticks.
- **Takeaway:** the weak-test pattern is past its third entry; the mechanism here is the helper, `tick_until_hovering`. Close to `REVIEW.md` Q-49 (comments that relied on a changed step), so no new question.

### M-215, 2026-11-22: Said the draft filed every PR #29 entry under "I had to point out"

- **What happened:** asked whether the flaky-test fix (`40a5397`) was in the mistakes log, Claude said the draft `drafts/2026-11-22-pr29-shared-records.md` told the writer to file all its entries under "Mistakes I had to point out", so M-214 would land in the wrong section. Claude had read only the draft's first instruction line; the draft splits them correctly, with M-214 under "Mistakes Claude caught itself". Caught by Claude reading the whole draft to apply it.
- **Kind:** communication.
- **Pattern:** said-without-checking.
- **Guard:** working rule 2: read the whole document before saying what it says, not a line found by search.
- **Takeaway:** not a code-review takeaway, so no step on the escalation ladder.

### M-214, 2026-11-22: Two tick-loop tests expected a tick's log line without a garbage-collector pause

- **What happened:** `test_every_tick_is_logged_at_debug_level_with_its_lateness_and_work_time` and `test_a_tick_that_raises_is_still_timed_and_logged` compared each tick's debug line exactly, but the line ends with a pause whenever Python's garbage collector runs during that tick. The second failed 3 runs in 4 when the ADR-0085-only commit was tested on its own, since the suite's other tests shift when the collector runs. Fixed in `40a5397`: a fixture turns the automatic collector off for those two tests.
- **Kind:** testing.
- **Pattern:** weak-test.
- **Guard:** a test that compares a log line exactly holds fixed every optional part the line can carry.
- **Takeaway:** found only because a commit's tree was tested on its own: testing each commit's tree also catches tests that pass by luck. The weak-test pattern is past its third entry; added with Joe's OK on 2026-11-22: `REVIEW.md` Q-56.

### M-213, 2026-11-22: A backlog row's removal drafted without searching for pointers to it

- **What happened:** drafting the removal of backlog #138 (answered by the facts register), Claude didn't search the code for "#138": the last-resort landing's comment still cited it. `/project-review high` caught it. Fixed in `92d0ceb`: the comment points at ADR-0084.
- **Kind:** process.
- **Pattern:** said-without-checking.
- **Guard:** before removing a backlog row, search the code and the docs for its number.
- **Takeaway:** Q-35 already asks whether the old wording was searched for.

### M-212, 2026-11-22: New names for the wait after the silence and the lost-link flag that said more or less than their code

- **What happened:** building ADR-0085 and ADR-0086, Claude spelled the wait after the silence four ways, named `_silence_and_wait()` beside `_land_silence_and_wait()` (whose wait is the wait for not flying), kept "a call has raised" where only a snapshot or a wait raises now, and left test helpers whose names said more than they did (`lose_the_link_at_the_next_wait`, `sent_to_the_drone`). `/project-review high`'s fresh-context read caught them before the commit.
- **Kind:** communication.
- **Pattern:** vocabulary.
- **Guard:** after a change, reread every name and comment it touched or relied on against what the code now does (M-207's guard).
- **Takeaway:** a repeat of M-173, M-207 and M-208, and the fresh-context read caught every one before the commit, so it's working as the mechanism; no new question.

### M-211, 2026-11-22: "Only the snapshot raises" for a lost link, though `land()` reads a snapshot of its own

- **What happened:** ADR-0086's failure modes said a link lost after the tick's snapshot raises one tick later, and the build's docstrings said no command checks. But `land()` in flight reads a snapshot of its own (`_latest_fresh_down_distance()`), so it raises at once. The new coding-style rule also said the check goes "where every call passes through", though calls don't pass through `take_snapshot()`: each tick starts with it. The review and its fresh-context read caught both. Fixed in `e8f7e10`, with Joe's OK for the ADR and rule wording.
- **Kind:** communication.
- **Pattern:** said-without-checking.
- **Guard:** rule 1: before writing that only one function does something, search for every caller of it, its own module's included.
- **Takeaway:** Q-02 already asks whether a claim says only what its source showed.

### M-210, 2026-11-22: Removing the mock's lost-link checks let its next update play a tone a real drone never got

- **What happened:** building ADR-0086, Claude took `_raise_if_the_link_is_lost()` out of the mock adapter's `update_take_off_and_landing()` along with the commands' checks. That check had also stopped the update from delivering buzzer commands still on their way after a lost link, so a link lost after the tick's snapshot now let the update play a tone that the Crazyflie adapter would have skipped and cflib thrown away. `/project-review high` caught it before the commit (Q-09). Fixed in `e8f7e10`, with a test proven by bug planting.
- **Kind:** testing.
- **Pattern:** window-between-steps.
- **Guard:** when a change removes a check, list everything the check stopped, in the adapters and their fakes, and keep each one stopped or decide otherwise.
- **Takeaway:** Q-09 caught it at review, so no new question.

### M-208, 2026-11-22: The fix for M-207 said "It keeps ticking", with no clear subject

- **What happened:** rewording `TickStep.request_stop`'s docstring for #29, Claude wrote "The loop calls this only once, on its own thread, right before calling `run()`, so the tick step needs no lock. It keeps ticking until `run()` reports done". "It" reads as the tick step, though the loop is what ticks, and "on its own thread" didn't say it's `run()`'s thread, which is why no lock is needed. `/project-review high`'s fresh-context read caught it before the commit.
- **Kind:** communication.
- **Pattern:** vocabulary.
- **Guard:** M-207's guard, and after rewording a docstring, check that each "it" points at the part that does the thing.
- **Takeaway:** a repeat of M-207 inside its own fix. Backs Q-55.

### M-206, 2026-11-22: A checked audit's row that left out a planted bug that passed

- **What happened:** the checked boundary-test audit says its "passes" column lists exactly what was planted and passed. Row 14 (the failsafe test's hover time limit) lists only `>=`, but its results (`results.json`) show the limit plus 0.04 s passed too: the tests sit at the limit and 0.05 s past it, so any limit in between passes. Joe chose row 14's tests from that row. Caught by Claude planting row 14's bugs to prove the new tests (#133, part 1); put back to Joe as a decision.
- **Kind:** testing.
- **Pattern:** said-without-checking.
- **Guard:** working rule 2: a table written from results is checked against every result, not the ones in mind.
- **Takeaway:** a summary written from a results file dropped one of its rows. The boundary-test pattern is already at the mechanism step (next-up brief decision 6); a tool that writes the table from the results would rule this out. No new step.

### M-205, 2026-11-21: A backlog number cited in code before its row, and already taken

- **What happened:** building ADR-0083, Claude planned the first-0 confirmation's case as a new backlog row #139 and cited "backlog #139" in the adapter's `_on_sound_effect_reported` comment and in the build's progress record. Rows #139 and #140 had been added earlier that day (`ea5c7fb`), so the comment pointed to "A test that failed once under load". Caught by Claude while updating the backlog after bug planting: the row is #141, and the comment cites it.
- **Kind:** process.
- **Pattern:** said-without-checking.
- **Guard:** working rule 2: read the backlog's last row before naming a new row's number, and add the row before code cites it.
- **Takeaway:** a row number taken from memory of the backlog, not from the file. A fitness function could check that a cited row exists, not that it's the right one, so no step on the escalation ladder.

### M-204, 2026-11-21: Asked whether to remove `SILENCE_HOLD` without finding the ADR that records it

- **What happened:** building ADR-0083, Claude asked Joe whether to remove the Hover test's `SILENCE_HOLD` now that `disconnect()` waits for the silence's confirmation, after searching the ADRs only for the constant's name. ADR-0053's "As built" records the 1 s wait in words ("After its silence, the Hover test waits 1 s before it's done"), so Joe chose "remove it now" without knowing it was an accepted decision. Caught by Claude before changing the code; asked again with ADR-0053 quoted, Joe kept it.
- **Kind:** recommendation.
- **Pattern:** recommendation.
- **Guard:** working rule 5: search the ADRs for the topic in words too, not only for a name from the code.
- **Takeaway:** a name search misses a decision written in words. Not a code-review takeaway, so no step on the escalation ladder.

### M-203, 2026-11-21: A float limit called unreachable for both tolerances, from one's results

- **What happened:** putting choice 3 of the checked boundary audit to Joe (how to test the two height tolerances), Claude wrote that no real height sits exactly 0.1 m from a hover test take-off height in floats, "and the failsafe test's tolerance has the same problem at 0.05 m". The computation Claude had just run said otherwise for one pair: with the failsafe test's 0.1 m take-off height, a height of 0.05 m is exactly 0.05 m away (0.1 is twice 0.05 in binary). Joe chose 1 mm either side on that premise. Caught by Claude at the wrap-up, re-reading the computation; put back to Joe as a decision.
- **Kind:** communication.
- **Pattern:** said-without-checking.
- **Guard:** working rule 1: quote a computed result case by case; "the same" across cases needs each case computed.
- **Takeaway:** a generalization from the hover test's cases to the failsafe test's, against a printed result. Not a code-review takeaway, so no step on the escalation ladder.

### M-202, 2026-11-21: A test audit's coverage judged by reading, not by planting

- **What happened:** the boundary-test audit (`drafts/2026-11-21-boundary-test-audit.md`, backlog #133) judged each limit's tests by grep and reading. Checked by planting the bugs it named, rows 5, 7, 8 and 10 to 14 of its 14 were wrong in part: the reset log's floor speed called untested (it's tested at the limit), the climb's flow check said to lack a test at its limit (it has one), approved and refused swapped in the take-off rule's row, typed-number tests of the mock missed, and a 0.06 s touchdown hold not seen to pass. Its "at the limit" take-off grace tests are 0.4 s past the limit; two limits in its Good list aren't pinned (an always-true assert, and a time checked with `pytest.approx`); it missed the landing approach skipped at the final descent height, the take-off rule's age limit (pinned only by chance) and the mock's climb end. Caught by Claude checking the audit for Joe, before any test was written. The check's own first report, before planting, did it once more: it called the take-off rule's age limit untested at its limit, which three tick-step tests pin by chance.
- **Kind:** testing.
- **Pattern:** said-without-checking.
- **Guard:** plant a bug before saying whether a test catches it (the audit's scripts, `drafts/2026-11-21-boundary-audit/`).
- **Takeaway:** reading finds the tests that name a limit, not those that pin it with a typed number or by chance, nor those that only seem to (an assert that's always true, a time within `pytest.approx`). The boundary-test pattern is already at the mechanism step (next-up brief decision 6, M-194); this check adds its cost, about 9 minutes for 97 planted bugs with three copies at once. No new step.

### M-201, 2026-11-21: An assert on a verdict, which is always true

- **What happened:** `test_a_take_off_is_refused_unless_the_down_range_reads_the_floor` (`tests/safety/test_safety_layer.py:765`, from ADR-0054's build, `152d456`, 2026-11-09) checks a down range at exactly `TOUCHDOWN_DOWN_RANGE` with `assert judge(...)`. A `Verdict` has no `__bool__`, so the assert is always true, and planting `>=` in the take-off rule's floor check passes every test. Caught by Claude's bug planting while checking the boundary-test audit.
- **Kind:** testing.
- **Pattern:** weak-test.
- **Guard:** REVIEW.md Q-54: assert a verdict's `.is_approved`, never the verdict; bug planting (`docs/coding-style.md`) shows an assert that can't fail.
- **Takeaway:** the line was never proven by planting. A code-review takeaway, the first of its kind, so the ladder's first step: the question Q-54 (Joe, 2026-11-21).

### M-200, 2026-11-21: A last-resort landing that released the setpoint priority before the land

- **What happened:** `drafts/2026-11-13-code-recommendations.md` (C4, D8's option A) said the last resort "releases the setpoint priority, sends the firmware's land". The adapter's recorded order is the high-level command first, then the release (ADR-0048, ADR-0056, `_handing_over_to_high_level`'s docstring): released first, the idle planner's motors-off setpoint gets through until the land arrives. Caught by Claude while checking the firmware facts for D8, before Joe chose; ADR-0084 has the right order and a test of it.
- **Kind:** safety design.
- **Pattern:** said-without-checking.
- **Guard:** working rule 2: before proposing an order of commands to the firmware, read the ADRs and code that already fix that order.
- **Takeaway:** a command sequence written from memory of what it does, not from the adapter's own rule. ADR-0084's test pins the order, so no step on the escalation ladder.

### M-198, 2026-11-21: A fallback said to share a failure it doesn't share

- **What happened:** arguing for D3's option B in the C3 decisions, Claude said `disconnect()` "runs the same landing logic, so it may fail the same way" as a landing inside the tick loop. It shares the adapter's landing, but none of the new tick-step code (the latch, the stop request's handling), where a new bug would most likely be. Caught by Claude on a re-read, and corrected before Joe chose.
- **Kind:** communication.
- **Pattern:** said-without-checking.
- **Guard:** before saying a fallback fails together with what it backs up, name what they share: code, sensor, estimate or thread (`/decide` step 3).
- **Takeaway:** an argument about a backup's independence needs the shared part named, not assumed. Not a code-review takeaway, so no step on the escalation ladder.

### M-196, 2026-11-20: A planted bug undone with `git checkout` on a file with uncommitted changes

- **What happened:** building ADR-0082, Claude planted a bug in `src/crazyflie_behavior/loop/tick_loop.py` and undid it with `git checkout`, though `git status` had just shown the file as modified. Any uncommitted change in it would have been lost. Every other file under `src/` marked modified had an empty `git diff` (line-ending normalization only), and so very likely did this one; no copy of the file as it was exists. Caught by Claude from the next `git status`.
- **Kind:** process.
- **Pattern:** how-I-work.
- **Guard:** undo a planted bug by reversing the edit or restoring a copy taken first, never with `git checkout` or `git restore`.
- **Takeaway:** bug planting changes files Claude didn't write in this change; it puts back exactly what was there. Not a code-review takeaway, so no step on the escalation ladder.

### M-195, 2026-11-20: Tests counted by the lines that build a clock

- **What happened:** backlog #129, written in ADR-0080's project review, said 12 tests in `tests/programs/test_start_up.py` build a plain `SimClock()`. 12 is the number of `SimClock()` lines: one is the helper `run_test_program`, which 5 tests call, so 16 tests run without the limit. Caught by Claude listing the tests for Joe; corrected in ADR-0082.
- **Kind:** communication.
- **Pattern:** said-without-checking.
- **Guard:** working rule 1: count tests by the `def test_` lines that reach the code, following helpers.
- **Takeaway:** a grep hit is a line, not a test. Not a code-review takeaway, so no step on the escalation ladder.

### M-194, 2026-11-19: Age-limit tests one tick past the limit, none at it

- **What happened:** building ADR-0081, Claude tightened the tests of four age checks in the Crazyflie adapter ("may be flying", the wait for "not flying", the low-light warning, the initial climb's stale-reading log) to one tick past `STALE_AFTER`, and proved them by planting the old 0.5 s, but wrote no test at exactly the limit, which REVIEW.md asks of every limit. A `>` turned into `>=` in any of the four would have passed. Caught by Claude's project review of the build; fixed before the commit with four exact-limit tests, each proven by planting `>=`.
- **Kind:** testing.
- **Pattern:** weak-test.
- **Guard:** REVIEW.md Q-48; for a limit, plant both a wrong value and the other comparison.
- **Takeaway:** a third boundary-test entry (M-128, M-174), so the ladder's third step asks for a mechanism. None is cheap: mutation testing would plant the other comparison everywhere, but it's a new dependency and slow, so Q-48 stays. Proposed for Joe: a line in the coding style's bug planting, "for a limit, plant a wrong value and the other comparison".

### M-193, 2026-11-19: Built "Yes" with no test citing the ADR

- **What happened:** after finding ADR-0081's code and tests, Claude set its Built cell in the ADR index to "Yes", but no test cited ADR-0081. The index's note on Built calls that case "Yes, no test cites it". Caught by Claude's project review of the build; fixed by citing ADR-0081 in the tightened and new tests.
- **Kind:** process.
- **Pattern:** records-ahead-of-code.
- **Guard:** REVIEW.md Q-39 and `/project-review` step 3, against the index's note on Built.
- **Takeaway:** the project review caught it, as designed. A cheap mechanism exists: a test that each ADR whose Built cell is a plain "Yes" is cited by at least one test. Proposed for Joe.

### M-192, 2026-11-19: A stall of the velocity uncertainty alone, which its log block rules out

- **What happened:** backlog #120, written in ADR-0077's project review, said that if the velocity uncertainty's stream stalled, the initial climb's flow check could hand over on evidence from near the floor. The uncertainty rides in the down range's log block and one callback writes both (ADR-0054), so it can't stall while the down range keeps arriving; a whole-block stall fails the safety pre-check's down range check at 0.25 s. Stated without reading which log block carries the value. Caught by Claude while deciding #120 (ADR-0081); the decision went ahead on consistency instead.
- **Kind:** safety design.
- **Pattern:** said-without-checking.
- **Guard:** working rule 1: before naming a failure of one input, read where it comes from and what shares its stream.
- **Takeaway:** a failure case for one reading needs that reading's own path; a value that shares a packet stalls with its partner. A code-review takeaway, for Joe to say whether it becomes a REVIEW.md question.

### M-190, 2026-11-18: A review pull request misdescribed its copied commits

- **What happened:** pull request #26's description said the copies of ADR-0080's two commits differed from `main`'s only in where ADR-0080's row sits in the ADR index. The copy of the ADR commit also carries ADR-0076's index-row fixes, which reached `main` in ADR-0079's commit `1f482dc`, made by the line-endings work session while this one's index edits were uncommitted in the same working copy. Said from the files the copies leave, without comparing the copies with the originals. Caught by Claude with `git range-diff` during the wrap-up; the description was corrected before Joe read it.
- **Kind:** communication.
- **Pattern:** said-without-checking.
- **Guard:** working rule 2; `git range-diff` compares copied commits with their originals.
- **Takeaway:** what a commit contains comes from its diff, not from the files it leaves. Not a code-review takeaway, so no step on the escalation ladder.

### M-189, 2026-11-18: Sim-clock program tests with no time limit

- **What happened:** ADR-0076 moved the program tests onto the sim clock with no time limit. On it, a program that never ends doesn't hang: each wait returns at once, so the tick loop runs about 3,000 ticks and writes about 6.6 MB of log per real second, without end; the hang watchdog counts real time, and neither pytest nor the workflow had a time limit. Caught by ADR-0076's project review (Q-10); fixed by ADR-0080: a sim clock that fails the test after 120 s of sim time, and a 15-minute limit on the continuous integration job.
- **Kind:** testing.
- **Pattern:** weak-test.
- **Guard:** the `sim_clock` fixture in `tests/conftest.py` (ADR-0080, ADR-0082), and REVIEW.md Q-10.
- **Takeaway:** a repeat of M-012 (test fakes that hang instead of failing), so the escalation ladder's second step: a helper, which the fixture is. Q-10 stays. On a sim clock a hang becomes a loop that fills the disk, so any sim clock that runs a loop to its end needs a limit.

### M-188, 2026-11-18: A chirp test left loose for slow ticks the sim clock doesn't have

- **What happened:** ADR-0076 moved the hover program's chirp test onto the sim clock but kept its real-clock comment, "A slow tick may skip a short note", and checked only the first and last notes of "Charge". On the sim clock no tick is late, so a bug that dropped or repeated a middle note passed. Caught by ADR-0076's project review (Q-49); fixed: the test checks every buzzer command and every pitch, proven by two planted bugs (a wrong middle note, a dropped one).
- **Kind:** testing.
- **Pattern:** weak-test.
- **Guard:** REVIEW.md Q-49.
- **Takeaway:** moving a test onto the sim clock removes every reason it gave for slow ticks; Q-49 covers it. No new question.

### M-187, 2026-11-18: ADR-0076's records left behind by two build choices

- **What happened:** building ADR-0076, the hover program's "interrupt signal while connecting" test moved onto the sim clock (it sends no real signal), but the ADR still said the interrupt signal tests stay on the real clock; and after Joe chose no real-clock test for the failsafe program, noted in the ADR, its index row still said "one real-clock test per program". Caught by ADR-0076's project review (step 3, the records); fixed.
- **Kind:** process.
- **Pattern:** records-ahead-of-code.
- **Guard:** working rule 3, and `/project-review` step 3.
- **Takeaway:** a build choice that changes what an ADR says changes its index row too, in the same step. No cheap mechanism checks an ADR's wording against its tests, so the review step stays the guard.

### M-182, 2026-11-17: Reasons for changed tests guessed from their names

- **What happened:** ADR-0077's review packet first said seven hover-program tests changed "for the description line without a climb speed", and ten tests elsewhere "for the one final descent height": reasons guessed from the tests' names. Their diffs showed the seven changed mainly because their stand-in `make_drone` lost `initial_climb_speed`, and some of the ten for the climb speed's constant too. Caught by reading the diffs before the review was posted; fixed before Joe saw the packet.
- **Kind:** communication.
- **Pattern:** said-without-checking.
- **Guard:** working rule 2.
- **Takeaway:** the packet lists tests by name; a reason beyond the name comes from the diff. No new question.

### M-181, 2026-11-17: The flow check let a negative or infinite uncertainty through

- **What happened:** ADR-0077's `has_fresh_flow` counted any fresh velocity uncertainty under 0.03 m/s as flow, so −inf or a negative value would hand over the initial climb; only NaN and +inf failed. M-177's takeaway, written in the same change, said a safety check should let only a finite value pass, but its fix covered the down range only. Not reachable from the Crazyflie adapter, whose conversion gives NaN for a negative or non-finite variance. Caught by ADR-0077's second project review (Q-14); fixed with `0.0 <= value < limit` and tests for each infinity, a negative value and zero.
- **Kind:** safety design.
- **Pattern:** safety-judgment.
- **Guard:** REVIEW.md Q-14, and a test for each non-finite value and a negative one.
- **Takeaway:** the second safety-judgment miss in this change: a fix's takeaway applies to the whole change, so search it for the fix's siblings (every comparison against a limit). Backlog #123 is the down range's helper; no cheap mechanism yet for checks written fresh, so Q-14 stays.

### M-180, 2026-11-17: "No flow" logged for an old velocity uncertainty

- **What happened:** ADR-0077's no-flow landing logged "No flow at the end of the initial climb" also when the velocity uncertainty was low but older than 0.5 s, so a telemetry stall would read as darkness in a debrief. Caught by ADR-0077's second project review (Q-43); fixed with its own line for an old reading, and a test.
- **Kind:** communication.
- **Pattern:** message-misstates-outcome.
- **Guard:** REVIEW.md Q-43, and the stale test's check of the line.
- **Takeaway:** when one branch reaching a log line has a different cause, it gets its own line. No new question.

### M-179, 2026-11-17: Wording ADR-0077 left behind, again

- **What happened:** after M-176's fixes, ADR-0068's Decision still glossed its aim as "the settle height", with no note from ADR-0077, and `bad_flow_zone.py`'s placeholder header still covered the 0.4 m/s climb speed that ADR-0077 decided. Caught by ADR-0077's second project review (ADR-0068 by a search of the ADRs for "settle height", Q-35; the header by the fresh-context read); fixed.
- **Kind:** communication.
- **Pattern:** records-ahead-of-code.
- **Guard:** REVIEW.md Q-35.
- **Takeaway:** M-176's search covered docstrings and backlog notes but not every ADR naming the old term: search all of `docs/decisions/` for it. No new question.

### M-178, 2026-11-17: Words outside the glossary in ADR-0077's fix lines and test names

- **What happened:** a review fix in `land()` brought in "ADR-0049's climb landing", a term the glossary doesn't have; `FINAL_DESCENT_HEIGHT`'s docstring called a ValueError "refused", the glossary's word for a verdict; and new test names and comments leaned on the removed design ("still hands over", "no longer an option"), with `test_no_flow` naming none of its cases. Caught by ADR-0077's fresh-context read; fixed.
- **Kind:** communication.
- **Pattern:** vocabulary.
- **Guard:** `/project-review`'s fresh-context read (step 7).
- **Takeaway:** as in M-173, the fresh-context read caught what the author's review missed, review fixes included (Q-51). No new question.

### M-177, 2026-11-17: A NaN down range could hand over the initial climb

- **What happened:** ADR-0077's climb check, `down is None or down.value < FINAL_DESCENT_HEIGHT`, kept climbing only on a number under 0.15 m, so a NaN or infinite down range fell through to the hand-over. The settle detector's `>=` had kept climbing. Not reachable from cflib's whole-millimeter readings. Caught by ADR-0077's project review (Q-14); fixed with a finite check and a test.
- **Kind:** safety design.
- **Pattern:** safety-judgment.
- **Guard:** REVIEW.md Q-14, and a test for each non-finite value.
- **Takeaway:** flipping a comparison flips which way NaN goes: write a safety check so only a finite value can pass it. Backlog #123 is the helper the escalation ladder asks for: `fresh_down_distance` dropping non-finite values for every user.

### M-176, 2026-11-17: Wording ADR-0077 left behind

- **What happened:** after ADR-0077, `land()`'s comment gave a reason that's false on the new no-flow landing ("the down range hasn't reached the final descent height"). ADR-0049 still gave "no final descent height" as its reason, the hover test's time limit spoke of "the default initial climb speed" and a 4.5 s worst case from the old 1.75 s limit, and backlog #68's notes still offered "a lower settle speed". Found by ADR-0077's project review and the doc pass after it; fixed.
- **Kind:** communication.
- **Pattern:** records-ahead-of-code.
- **Guard:** REVIEW.md Q-35 and Q-43.
- **Takeaway:** Q-35's search for old wording covers other packages' docstrings and backlog notes too; no new question.

### M-175, 2026-11-17: ADR-0077's record out of step with its work

- **What happened:** ADR-0077 still said its glossary changes were "proposed for my OK" while the glossary already had them (whether the OK came first isn't known; Joe approved them in the review). It pointed at backlog #115 after the row was removed, its index row called 0.15 m "the lowest take-off target" though a target of 0.15 m is refused, and its Decision left an uncertainty of exactly 0.03 m/s unsaid. Caught by ADR-0077's project review; fixed.
- **Kind:** process.
- **Pattern:** records-ahead-of-code.
- **Guard:** `/project-review` step 3 and REVIEW.md Q-39, Q-48.
- **Takeaway:** once a decision is built, reread its ADR's Consequences for what was planned and is now done; no new question.

### M-174, 2026-11-17: A boundary test that stepped over its boundary

- **What happened:** the mock's dark-floor test set the dark floor at exactly 0.15 m, but the climb stepped from 0.14 to 0.16 m, so the boundary was never checked: `>` for `>=` in `_has_flow` would have passed. In the same change, the climb speed's log test copied 0.4 instead of using `INITIAL_CLIMB_SPEED`. Caught by ADR-0077's project review (Q-48); fixed, and the boundary test proven by planting `>`.
- **Kind:** testing.
- **Pattern:** weak-test.
- **Guard:** REVIEW.md Q-48 and Q-53.
- **Takeaway:** a test at a limit must land on it: compute the value the stepped code will see, then plant the off-by-one comparison. No new question.

### M-173, 2026-11-17: Docstrings and comments only their author could follow

- **What happened:** C1's second project review (fresh-context read) found `_ConsoleListener`'s docstring naming a `stop` it doesn't override, `stop_within`'s leaving out that it's also True when the thread never started, "Python's logging cleanup at exit" not naming `logging.shutdown`, and two comments (the warning's count, the removed handler) that needed the conversation to follow. Fixed in "Project review C1 (A2)".
- **Kind:** communication.
- **Pattern:** vocabulary.
- **Guard:** `/project-review`'s fresh-context read (step 7).
- **Takeaway:** review fixes are new code, wording included (Q-51 already asks); no new question.

### M-172, 2026-11-17: An unchecked claim about timed waits in a test comment

- **What happened:** in C1's review fixes (finding 7) I gave "A lock wait can return a little early" as the reason for the exit test's 0.05 s margin. It wasn't checked or in the facts register; the clock's resolution on Windows may be the cause. Caught by C1's second project review (Q-01); the comment now says it isn't checked.
- **Kind:** communication.
- **Pattern:** said-without-checking.
- **Guard:** REVIEW.md Q-01.
- **Takeaway:** the reason for a test's margin is a claim about Python too: check it or say it isn't checked (working rule 1).

### M-171, 2026-11-17: An index row written with the wrong line endings, again

- **What happened:** adding ADR-0078's index row, my script found its place by a bare line feed in a CRLF working copy and inserted a row ending in LF after a stray CR, so Git saw mixed line endings and the whole file as changed. Caught by the diff stat (189 lines for one row); rewritten with CRLF throughout. Repeats M-169.
- **Kind:** environment.
- **Pattern:** environment.
- **Guard:** `git diff --stat` after each scripted edit.
- **Takeaway:** a script that edits a file keeps the file's line endings and checks the diff stat after. A second time, so the escalation ladder asks for a mechanism: backlog #119.

### M-170, 2026-11-17: ADR-0078's index row recorded as written but missing

- **What happened:** the C1 work order and the next-up brief both said ADR-0078's index row was written; the index had no row for it. Caught by C1's second project review (step 3, the records check); added in "Project review C1 (A2)".
- **Kind:** process.
- **Pattern:** records-ahead-of-code.
- **Guard:** `/project-review` step 3 and REVIEW.md Q-39.
- **Takeaway:** before a work order or the brief says a record is written, find it in the file.

### M-169, 2026-11-17: The bug-planting script changed a file's line endings

- **What happened:** planting bugs for C1's review fixes, my script read each source file with `read_text` and restored it with `write_bytes`, which turned `start_up.py`'s CRLF line endings into LF. Caught by comparing checksums from before and after the planting; writing CRLF back made the checksum match.
- **Kind:** testing.
- **Pattern:** environment.
- **Guard:** the checksum comparison around the planting.
- **Takeaway:** a script that plants bugs saves and restores each file's bytes, not its text, and compares checksums after.

### M-168, 2026-11-17: The stuck exit's exit code given from one run

- **What happened:** C1's project review (finding 1) and its work order said that a program stuck at exit with a buffered standard error ends with a crash exit code (0xC0000409) once the console reads again. That came from one run. I repeated it to Joe as D-A's pitfall. Two reruns ended with exit code 0: the code depends on timing. Caught by rerunning the exit test before writing its facts register row; Joe kept A1 with the corrected facts (ADR-0078).
- **Kind:** communication.
- **Pattern:** said-without-checking.
- **Guard:** none yet; the facts register row gives every run.
- **Takeaway:** an outcome measured once where threads race is reported as one run's result, and run again before a decision rests on it.

### M-167, 2026-11-17: Backlog edits written while another work session held the backlog

- **What happened:** recording ADR-0077 with `/decide`, I wrote the backlog (removed #89, #98 and #104, added #115 and #116) without checking whether another work session held the shared records. The C1 work session had written the backlog, the mistakes log and the next-up brief during my session. Nothing was lost; caught when `git diff --stat` showed files I hadn't touched. I reverted my backlog edits and left them in `drafts/decide-0077-records.md`.
- **Kind:** process.
- **Pattern:** how-I-work.
- **Guard:** none yet.
- **Takeaway:** before writing a shared record, compare `git status` with the session's start; files changed that I didn't touch mean another writer.

### M-166, 2026-11-17: Backlog #104's settle heights from part of the logs

- **What happened:** writing backlog #104 (2026-11-15), I gave every recorded settle height as 0.102-0.117 m and the final descent heights as 0.15-0.17 m. Across all 39 climbs in the logs that settled, they were 0.101-0.144 m and 0.151-0.194 m; most of the higher ones are from First flights 5 and 6. Caught by tallying every log before giving #104's options; the decision (ADR-0077) uses the full range.
- **Kind:** communication.
- **Pattern:** reading-field-data.
- **Guard:** working rule 4.
- **Takeaway:** a range given for "every" flight is tallied over every log, not carried over from an earlier analysis.

### M-165, 2026-11-17: A docstring said nothing waits on a stuck console write

- **What happened:** in `programs/console_output.py`, `UnlockedConsoleHandler`'s docstring says "so nothing waits on a stuck write", and a test is named `test_python_exit_cleanup_does_not_wait_on_a_stuck_console_write`, while ADR-0075 says Python's last flush of the console "may still wait". The project review's run showed it does wait, when standard error is buffered.
- **Kind:** communication.
- **Pattern:** records-ahead-of-code.
- **Guard:** Q-02.
- **Takeaway:** a docstring or test name says only what its test showed; "nothing" covers code the test never ran.

### M-164, 2026-11-17: ADR-0075 marked built without the test its Consequences name

- **What happened:** building C1, I changed ADR-0075's Built column in the ADR index to "Yes". Its Consequences name "a test that a program with its console blocked ends within a time limit"; the test I wrote times `logging_for_run`'s exit inside pytest, which can't see Python's final flush of standard error. The project review found it (2026-11-17): a program whose standard error pipe isn't read doesn't end while it stays unread.
- **Kind:** process.
- **Pattern:** records-ahead-of-code.
- **Guard:** Q-39.
- **Takeaway:** a Built "Yes" needs each test the ADR's Consequences name, matched by what the test runs, not by its topic.

### M-163, 2026-11-17: Two planted bugs counted from the exit code, not the failure

- **What happened:** bug planting for C1 (ADR-0035, ADR-0075), my script printed "CAUGHT" for any failing run. The plant "the level on the listener's handler only" failed with an `UnboundLocalError` my edit caused, not the assertion; the plant "the exit warning before the handler is removed" deleted the removal instead of moving it. Caught by running both again and reading the failures. Redone, the first is caught by the exit and console-level tests.
- **Kind:** testing.
- **Pattern:** weak-test.
- **Guard:** none yet.
- **Takeaway:** a planted bug counts as caught only when the test fails on the assertion it targets; read the failure, not the exit code.

### M-162, 2026-11-17: A comment gave an ordering a reason the code doesn't have

- **What happened:** in `programs/console_output.py` I wrote that the console's handler comes off the root logger first "so the warning below goes to the log file only". Planting the other order showed no difference: the console's thread stops at the sentinel before the warning is queued. Reworded to the real reason, that no line is queued behind the stop.
- **Kind:** communication.
- **Pattern:** records-ahead-of-code.
- **Guard:** a planted bug for each claim a comment makes.
- **Takeaway:** a comment's "so that" is a claim; plant its opposite before writing it.

### M-161, 2026-11-16: The mistakes log's check passed malformed entries

- **What happened:** in a review of pull request #23, I found four ways `tools/mistakes_log.py`, which I wrote for W6, let a bad log pass. An entry heading with a typo dropped out of the counts, and its fields went to the entry above it. A misspelled pattern became a new row in the pattern table. Two entries could share an ID. A mistyped command ran `check` and exited 0. `check` reported none of them.
- **Kind:** testing.
- **Pattern:** weak-test.
- **Guard:** `tests/tools/test_mistakes_log.py`.
- **Takeaway:** a check script needs a test for each malformed input it exists to catch, not only for good input.

### M-159, 2026-11-16: "Was lost" for a script the hand-off said may be gone

- **What happened:** drafting `/debrief` (W13, section F), I wrote that session 6's analysis script "was lost" in a scratchpad. Session 6's hand-off says it was in the old session's scratchpad "and may be gone"; nobody checked. Caught by re-reading the hand-off's line before reporting the skill.
- **Kind:** communication.
- **Pattern:** said-without-checking.
- **Guard:** working rule 2.
- **Takeaway:** when a doc hedges, the paraphrase keeps the hedge.

### M-158, 2026-11-16: A log's program line placed by one sample

- **What happened:** drafting `/field-session` (W13, section E), I wrote that a flight's log names "the Crazyflie" on its third line, from one real hover log. In a mock run's log the program line is the second: the "QuickEdit is off" line before it isn't always written. Caught by checking a mock run's log before reporting the skill.
- **Kind:** communication.
- **Pattern:** said-without-checking.
- **Guard:** working rule 1.
- **Takeaway:** a claim about what the code writes is checked against each case it covers (a mock run and a flight), not one sample.

### M-157, 2026-11-14: One flight's battery line filed under other flights

- **What happened:** recording session 6's night flights, I left a line about the 14:51 turned-around flight ("Battery 3.94 V before; 3.39 V at spin-up; 3.50-3.56 V in the hover. Image quality 23 at take-off.") after "Logs not yet analyzed." under the night flights, where it read as their battery. Its spin-up value was also the dip's second reading, not its lowest (3.27 V). Caught while analyzing the night flights, whose logs read 4.01-4.10 V before each flight.
- **Kind:** communication.
- **Pattern:** reading-field-data.
- **Guard:** working rule 4.
- **Takeaway:** after editing a session log, read each analysis line back against its heading and its log.

### M-156, 2026-11-14: Motor outputs read as the thrust command

- **What happened:** in session 6 I told Joe the hover's "thrust command" averaged about 46,300-47,000, above the plan's 44,500 check and well above session 4's 43,000-43,500. I'd averaged the diagnostic block's `motors` values, which are motor outputs, not the thrust command the plan and session 4 measured. Session 4's motor outputs were 47,900-50,300, so today's are not higher. Caught while comparing the logs across sessions.
- **Kind:** communication.
- **Pattern:** reading-field-data.
- **Guard:** working rule 4.
- **Takeaway:** before comparing a number with a threshold or an earlier session, check that it's the same logged variable.

### M-155, 2026-11-14: The forged drone changed, but not its ADR or glossary row

- **What happened:** building ADR-0069, I made the forged low battery drone
  forge both battery readings. ADR-0041's "as built" still said it replaces
  only `battery_voltage`, its status line had no "Amended by ADR-0069" (and
  ADR-0069's status didn't name ADR-0041), and the glossary's *Fault
  injection* row still says it "replaces one value in the snapshot".
- **How it was caught:** `/project-review` of ADR-0069's code.
- **Kind:** process.
- **Pattern:** records-ahead-of-code.
- **Guard:** Q-35.
- **Takeaway:** when code changes what an older ADR's "as built" describes,
  search the ADRs and the glossary for the old wording. The review checklist
  already asks this.

### M-154, 2026-11-14: A helper and a test whose names said something else

- **What happened:** the safety pre-check's helper for the previous battery
  reading was named `_was_battery_low`, though it returns true for a missing
  reading, and its docstring called the previous reading "the low-battery
  limit's second reading in a row", when it's the first of the two. A new
  test named "above the limit" used a reading at the limit.
- **How it was caught:** `/project-review` of ADR-0069's code.
- **Kind:** communication.
- **Pattern:** vocabulary.
- **Guard:** none yet.
- **Takeaway:** check a new name against every case it returns true for, and
  a test's name against its values.

### M-152, 2026-11-13: Two backlog rows said ADR-0035's console thread was built

- **What happened:** ADR-0035 (accepted 2026-11-01) puts console output
  behind a `QueueHandler` on a background thread. It was never built:
  `logging_for_run` adds a plain `StreamHandler`, and no commit under `src/`
  or `tests/` has contained `QueueHandler`. Backlog #25 said "Console output
  now runs on a background thread", and #87 (2026-11-12) said the console's
  lines "already are" on one. Backlog #70's stall hunt and #87's options were
  written on that belief.
- **How it was caught:** the 2026-11-13 codebase review, reading
  `start_up.py` beside the ADR index, then `git log -S"QueueHandler"`.
- **Kind:** process.
- **Pattern:** records-ahead-of-code.
- **Guard:** Q-39.
- **Takeaway:** before a record says a decision is built, find its code and
  its test. An accepted ADR is a decision, not a build.

### M-151, 2026-11-13: A flight started without reading how the last one ended

- **What happened:** in First flight 5 I started flight 8 after reading only
  the last three lines of flight 7's terminal output ("Disconnected"). Flight
  7 had ended on a failed safety pre-check ("the drone reports it has
  tumbled"), and its tick loop stopped before "Charge". The README says no
  more flights after an abnormal end until it is written up. It turned out
  harmless: Joe had picked the drone up after it landed. That wasn't known
  when flight 8 started.
- **How it was caught:** the First flight 5 analysis, reading flight 7's log.
- **Kind:** process.
- **Pattern:** reading-field-data.
- **Guard:** `/field-session`.
- **Takeaway:** before starting another flight, read how the last one ended:
  the tick loop's and the safety layer's last lines, not only the disconnect.

### M-150, 2026-11-13: A chance worked out for a battery reading that arrives at a fixed time

- **What happened:** the First flight 4 analysis and backlog #91 said the
  once-a-second battery reading falls in the dip at spin-up in "roughly 5-15%
  of take-offs". In all six flights that reading came 0.07-0.17 s before the
  take-off and the next about 0.9 s after it: `connect()` ends on the first
  battery reading, and the programs take off right after. Today's programs
  miss the dip by their timing; only a take-off at another moment could read
  it. The same note said the voltage was back above 3.20 V within 0.1-0.15 s;
  two flights had two readings in a row under it.
- **How it was caught:** listing each flight's battery readings by time, to
  weigh the options for #91.
- **Kind:** communication.
- **Pattern:** reading-field-data.
- **Guard:** `/debrief`.
- **Takeaway:** before giving a chance that a reading falls somewhere, list
  when the readings fell.

### M-149, 2026-11-13: An option offered for the landing approach that the code already has

- **What happened:** the handoff and backlog #93 listed "end the approach when
  the down range reaches the final descent height" as the change to make. The
  adapter's `_update_landing` already ends the approach on that reading; the
  plan's time runs out first because the drone lags the plan.
- **How it was caught:** reading the adapter before weighing the options.
- **Kind:** recommendation.
- **Pattern:** recommendation.
- **Guard:** working rule 5.
- **Takeaway:** read the code path before writing an option for it.

### M-148, 2026-11-13: Hover heights taken from the moment the hover started

- **What happened:** First flight 4's Take-off speeds log said the flights
  hovered at 0.42, 0.41 and 0.40 m, and the Hover log at 0.41 m. Those are the
  heights in the hover test's "at ... m" line, logged when the drone first came
  within 0.1 m of 0.5 m. By the down range the drone hovered at 0.50-0.52 m.
- **How it was caught:** the First flight 4 analysis, computing each hover's
  mean down range.
- **Kind:** communication.
- **Pattern:** reading-field-data.
- **Guard:** working rule 4.
- **Takeaway:** a number in "Computed from the logs" comes from the data over
  the part it describes, not from a log line written at one moment of it.

### M-147, 2026-11-12: A time limit quoted from memory

- **What happened:** I said a 0.6 m/s initial climb would have a time limit of about 1.2 s. The code's formula (`MAX_FINAL_DESCENT_HEIGHT / climb_speed + 1.0`) gives 1.5 s. I corrected it in the next message.
- **How it was caught:** reading `initial_climb_time_limit` while checking the climb speed limit.
- **Kind:** communication.
- **Pattern:** said-without-checking.
- **Guard:** working rule 1.
- **Takeaway:** when quoting a number the code computes, read the formula first.

### M-146, 2026-11-12: The hover test waited for a drone status that comes too late

- **What happened:** ADR-0062's `has_failed` counted the hover test's
  landing only once the drone status said landed. That status keeps saying
  flying for 2 s after the motors stop (ADR-0058), and a failed safety
  pre-check ends the run for good. A stale value in those 2 s, as a laptop
  stall gives (backlog #70), would have turned a full, landed hover into
  exit 1.
- **How it was caught:** `/code-review` in the project review of the
  session 4 code, checked against the tick step. The landing now counts once
  the snapshot's *may be flying* turns false (ADR-0062 clarified).
- **Kind:** design.
- **Pattern:** window-between-steps.
- **Guard:** Q-15.
- **Takeaway:** a verdict read from the drone status: can the run end during
  the status's lag, before the verdict is recorded?

### M-145, 2026-11-12: "Fails the connect, on the floor" for a block the rescue landing starts too

- **What happened:** ADR-0063 said a missing controller variable fails the
  connect on the floor, as ADR-0050 said for the diagnostic block. Both
  blocks were always on, also in the rescue landing's connect to a flying
  drone, where a missing variable would fail the rescue and leave the drone
  in the air.
- **How it was caught:** the project review of the session 4 code.
  ADR-0067: a take-over starts neither block.
- **Kind:** safety design.
- **Pattern:** safety-judgment.
- **Guard:** Q-22.
- **Takeaway:** a claim that a failure happens on the floor: does every
  program that reaches it start on the floor?

### M-144, 2026-11-12: Wording that ADR-0062 and ADR-0064 left behind

- **What happened:** `FLOW_VELOCITY_UNCERTAINTY`'s docstring still said a
  velocity uncertainty under it means flow, with no word of ADR-0064's
  in-flight limit that grows with height. A comment in `hover.py` named one
  cause of exit 1 where `has_failed` has three.
- **How it was caught:** the project review of the session 4 code.
- **Kind:** communication.
- **Pattern:** records-ahead-of-code.
- **Guard:** Q-35.
- **Takeaway:** the review checklist already asks for the old wording to be
  searched when a value's meaning changes; this was that miss.

### M-143, 2026-11-12: A second copy of the staleness rule

- **What happened:** `_known_height` in the safety layer compared the
  position estimate's age with `STALE_AFTER` itself, next to `_staleness`,
  which judges every other pre-check value. A later change to the stale rule
  (backlog #70's options) could have missed it.
- **How it was caught:** `/code-review` in the project review of the
  session 4 code. It now calls `_staleness`.
- **Kind:** design.
- **Pattern:** safety-judgment.
- **Guard:** none yet.
- **Takeaway:** a new check on a value the pre-check already judges: reuse
  that judgment instead of restating it.

### M-142, 2026-11-12: A work-log total that missed three changes to a day's hours

- **What happened:** three updates to the work log changed a row's hours
  without the milestone total: 2026-11-09 raised by 0.5, then 2026-11-12
  added at 1.25 and raised by 0.5. The total read ~61.75 where the rows add
  up to 64.0. The 2026-11-02 row had already fixed one such miss.
- **How it was caught:** summing the rows before adding a session's hours.
- **Kind:** process.
- **Pattern:** how-I-work.
- **Guard:** none yet.
- **Takeaway:** after changing any row's hours, recompute the total from
  every row, not from the change alone.

### M-141, 2026-11-12: ADR-0064's test list said the take-off rule refuses at 0.03

- **What happened:** ADR-0064's Consequences listed the test "the take-off
  rule still refuses at 0.03". The take-off rule never refuses for the
  velocity uncertainty: at 0.03 or more it counts no flow and approves
  without the estimate check (ADR-0054). The Decision itself was right (the
  take-off rule keeps 0.03). Built as written, the test would have asked for
  a take-off rule that refuses a dark floor.
- **How it was caught:** reading the take-off rule before building ADR-0064.
  The test now checks that the threshold stays 0.03 at any height, and the
  ADR's line says so.
- **Kind:** communication.
- **Pattern:** records-ahead-of-code.
- **Guard:** Q-37.
- **Takeaway:** describe a test by what the code does at that value
  (approves, refuses, skips a check), read from its branches.

### M-140, 2026-11-12: A recommended run at connect that the Bench would only half see

- **What happened:** backlog #85's recommended option C ran the take-off
  block for 2 s at connect so the Bench could measure its radio load. Created
  with the other blocks, about 1 s of that run would fall in the wait for the
  battery's first sample, before the first tick, where the Bench's snapshots
  can't see it.
- **How it was caught:** tracing the connect sequence before asking Joe.
  ADR-0065 creates the block last in connect.
- **Kind:** recommendation.
- **Pattern:** recommendation.
- **Guard:** Q-29.
- **Takeaway:** for a window meant to be measured, check that whatever
  measures it is already running, given every wait before it.

### M-139, 2026-11-12: ADR-0063 designed around a log block created but not started

- **What happened:** ADR-0063 said the take-off block is created at connect
  and started at the take-off. cflib 0.1.34 starts every block as soon as the
  drone confirms its create (`log.py` 551-563), so there's no create without
  a start. The handoff for the build also counted six log blocks; it's seven
  with the Multi-ranger.
- **How it was caught:** the source check the handoff asked for before the
  build. ADR-0065 records the fix.
- **Kind:** design.
- **Pattern:** said-without-checking.
- **Guard:** Q-04.
- **Takeaway:** for a library call a design relies on for one step, read what
  the library does on its own afterwards too, such as when the reply arrives.

### M-138, 2026-11-12: A recap that called the torque a match for the battery move

- **What happened:** a wrap-up said the 2026-11-09 front-right torque was
  "matching the battery move" when Joe had only said the battery moved, not
  which way; the same message asked him the direction to check it. His answer
  (left and back, or centred after a left-back counterbalance) fits only the
  second reading.
- **How it was caught:** reading Joe's answer against the data.
- **Kind:** communication.
- **Pattern:** said-without-checking.
- **Guard:** none yet.
- **Takeaway:** a recap says only what's established; a claim still waiting
  on a check stays a question.

### M-137, 2026-11-12: An estimate reset described as starting with large uncertainty

- **What happened:** asked what moving the estimate reset to just before the
  take-off (#81) would cause, Claude said the reset starts "with large
  uncertainty" and that a take-off soon after it flies on an estimate that
  "hasn't converged yet". The firmware starts the velocity and attitude
  uncertainty at 0.01 (`kalman_core_params_defaults.h` 65-68), and the
  glossary's *Estimate reset* row already said it starts small. Joe found
  the option too complicated from that list.
- **How it was caught:** checking the source after Joe asked whether #81 is
  needed at all.
- **Kind:** communication.
- **Pattern:** said-without-checking.
- **Guard:** Q-01.
- **Takeaway:** check every firmware claim in an explanation against the
  source and the glossary, the side points as well as the main one.

### M-136, 2026-11-12: Two glossary rows for ADR-0061 that didn't match it

- **What happened:** *Thrust base* said the adapter sets it "just under"
  the hover thrust, though ADR-0061 accepts it may sit above, and left out
  that the integral also restarts on the floor. *Thrust command* said the
  motor outputs average to it, but the logged outputs include the battery
  compensation: the analysis had to undo it.
- **How it was caught:** the project review of 9f98d17..f35aa64.
- **Kind:** communication.
- **Pattern:** vocabulary.
- **Guard:** Q-40.
- **Takeaway:** check each new glossary row against its ADR's accepted risks
  and the analysis it came from.

### M-135, 2026-11-12: A thrust base report logged the same whether it confirmed or not

- **What happened:** the adapter logged "The drone reports a thrust base of
  X." at INFO for any X, so a wrong value showed only in the take-off
  warning.
- **How it was caught:** the project review of 9f98d17..f35aa64.
- **Kind:** communication.
- **Pattern:** message-misstates-outcome.
- **Guard:** Q-45.
- **Takeaway:** a log line about a check says its outcome.

### M-134, 2026-11-12: "Estimate reset." logged before a write that can fail

- **What happened:** the review fix for the reset's link race (f35aa64) added
  a failure path after the "Estimate reset. Before it: ..." line, so a failed
  write logged a reset and then "not sent".
- **How it was caught:** the project review of 9f98d17..f35aa64.
- **Kind:** communication.
- **Pattern:** message-misstates-outcome.
- **Guard:** none yet.
- **Takeaway:** when a fix adds a failure path, re-read the log lines before
  it.

### M-133, 2026-11-12: A two-cause failure branch tested for one cause

- **What happened:** the same fix gave the reset's failure two causes ("the
  link is closed", "the firmware can't write it") but tested only the first,
  so always naming the link passed every test.
- **How it was caught:** the project review of 9f98d17..f35aa64.
- **Kind:** testing.
- **Pattern:** weak-test.
- **Guard:** none yet.
- **Takeaway:** a branch that picks between messages needs a test per
  message.

### M-132, 2026-11-12: A review finding against the adapter's VERIFY convention

- **What happened:** a low-effort project review of 9f98d17..f35aa64 said
  THRUST_BASE's "VERIFY from each hover's motor outputs" should start with
  `TODO:`. The Crazyflie adapter's module docstring makes VERIFY the marker
  for assumptions still to check in field tests; the review didn't read it.
- **How it was caught:** the same review, run again at a higher effort.
- **Kind:** communication.
- **Pattern:** how-I-work.
- **Guard:** none yet.
- **Takeaway:** before flagging a marker or a wording style, check whether
  the file or the coding style already sets a convention for it.

### M-131, 2026-11-12: "No glossary change" for a term whose meaning grew

- **What happened:** ADR-0060 said *May be flying* needed no glossary change,
  but the snapshot now carries it from every adapter, while the glossary
  still called it the Crazyflie adapter's judgment. *Safety pre-check* still
  said its velocity uncertainty check runs "while flying", the drone status
  reading ADR-0060 replaced.
- **How it was caught:** the project review of fdad2db.
- **Kind:** process.
- **Pattern:** vocabulary.
- **Guard:** Q-38.
- **Takeaway:** when a decision moves a value to a new place or changes when
  a check runs, re-read the glossary rows that name it.

### M-130, 2026-11-12: An ADR that took up an older ADR's rejected option, unmarked

- **What happened:** ADR-0060 (2026-11-10) put the adapter's "may be
  flying" in the snapshot for the safety pre-check. That's part of
  ADR-0039's option B, which ADR-0039 rejected, and it goes against backlog
  #8's "flight state from the drone, not from what was sent". Neither ADR's
  status line nor #8 said so, though the review checklist asks for it.
- **How it was caught:** the project review of fdad2db.
- **Kind:** process.
- **Pattern:** records-ahead-of-code.
- **Guard:** Q-33.
- **Takeaway:** before writing an ADR, check the options the ADRs it touches
  rejected, and the backlog items on the same subject.

### M-129, 2026-11-12: The reset's link check could go stale before the write

- **What happened:** the review fixes for ADR-0054's code (fdad2db) moved the
  estimate reset's log after its "link closed" check, but left the write
  unguarded. cflib's receive thread can lose the link between the check and
  `param.set_value`, which then raises `KeyError` or `AttributeError` into
  the tick loop. The thrust base write (95693eb) already caught both.
- **How it was caught:** the project review of fdad2db.
- **Kind:** design.
- **Pattern:** window-between-steps.
- **Guard:** Q-03.
- **Takeaway:** a check before a library call can go false on another thread
  before the call runs; handle the call's own failure too.

### M-128, 2026-11-12: A boundary fix with no test at the boundary

- **What happened:** fdad2db changed the reset log's floor speed comparison
  from "up to" to "under", but its only test used 0.3 m/s, far over the
  limit. Planting the old `<=` back passed every test.
- **How it was caught:** the project review of fdad2db, then planting the
  bug.
- **Kind:** testing.
- **Pattern:** weak-test.
- **Guard:** Q-48.
- **Takeaway:** a change to a comparison needs a test at exactly the limit.

### M-127, 2026-11-12: "As soon as the motors stop" for a flag that knows only our stop

- **What happened:** fdad2db's docstring for the snapshot's `may_be_flying`
  said it turns false as soon as the motors stop. It turns false when our
  motor stop is sent; after a stop the firmware makes, it follows the drone
  status, lag included.
- **How it was caught:** the project review of fdad2db.
- **Kind:** communication.
- **Pattern:** safety-judgment.
- **Guard:** Q-50.
- **Takeaway:** in a docstring about a safety judgment, say whose action
  changes it.

### M-125, 2026-11-10: One no-flow limit for an uncertainty that grows with height

- **What happened:** ADR-0054 set one velocity uncertainty limit for "no
  flow", 0.03 m/s, at every height. The firmware's flow model, read on
  2026-11-05 for the bad-flow zone, divides speed by height, so with good
  flow the uncertainty grows with height. It reaches 0.03 m/s at about
  0.53 m, and the safety pre-check landed every hover at 0.5 m about 1 s in.
- **How it was caught:** analyzing First flight 3, then the firmware source
  (backlog #80). Logged on 2026-11-12, after three hovers flown for fun on
  2026-11-10, two with a flashlight under the drone, followed the same curve.
- **Kind:** safety design.
- **Pattern:** safety-judgment.
- **Guard:** Q-08.
- **Takeaway:** before setting a fixed limit on an estimator's uncertainty,
  read its model for what else the uncertainty depends on, and check the
  limit at every height where it's used.

### M-124, 2026-11-10: The altHold climb chosen without reading what its controller does at a switch

- **What happened:** ADR-0048 (2026-11-05) described the altHold option as
  "the height controller tracks the vertical speed estimate", citing
  `controller_pid.c` for ignoring the horizontal estimate. The same file
  restarts every controller integral at a setpoint mode change, and the
  vertical speed controller starts from a fixed thrust base (36,000) that
  this drone needs about 7,300 more than to hover. Neither was checked, so
  ADR-0056's and ADR-0059's time limits and Take-off speeds' prediction
  assumed the climb runs at the commanded speed. In First flights 2 and 3 the
  climbs ran far slower, the time limit landed most of them, and every
  hand-over dipped.
- **How it was caught:** analyzing First flight 3, by fitting the firmware's
  formula to the thrust command reconstructed from the motor logs.
- **Kind:** design.
- **Pattern:** said-without-checking.
- **Guard:** Q-07.
- **Takeaway:** before relying on a firmware setpoint type, read what its
  controller does when that setpoint starts and stops (integrals, base
  values, the planner's start), not only which inputs it ignores.

### M-123, 2026-11-10: One limit read two ways, and messages that seemed to contradict it

- **What happened:** in ADR-0054's code, the safety pre-check passed a
  velocity uncertainty of exactly 0.03 m/s, while the take-off rule and the
  settle height counted it as no flow. The 0.05 m/s floor speed was two
  constants that compared differently (the take-off rule's and the reset
  log's). Messages such as "0.030 m/s in flight (no flow over 0.03)" and
  "0.050 m/s (under 0.05)" read as if the value were within its limit.
- **How it was caught:** the project review of ADR-0054's code.
- **Kind:** design.
- **Pattern:** message-misstates-outcome.
- **Guard:** Q-48.
- **Takeaway:** define each limit once, compare it the same way everywhere,
  and have each message say which side the value must be on.

### M-122, 2026-11-10: A comment and an ADR line that promised more than the code

- **What happened:** after ADR-0054 removed the wait for the estimate at
  connect, a comment still said no position from before the reset is used,
  but values from before it can still arrive. ADR-0054 also said the adapter
  warns when the estimate jumps; that wasn't built (backlog #76), and the ADR
  didn't say so.
- **How it was caught:** the project review of ADR-0054's code.
- **Kind:** process.
- **Pattern:** records-ahead-of-code.
- **Guard:** Q-49.
- **Takeaway:** when a change removes a wait, re-read the comments that
  relied on it; when code leaves part of an ADR unbuilt, mark that line with
  its backlog item.

### M-121, 2026-11-10: Choices made while building, not recorded, and new terms not proposed

- **What happened:** ADR-0054's code put `FLOW_VELOCITY_UNCERTAINTY` in the
  drone interface module, chose the reset log's "implausible" threshold, and
  made the low-light warning fire when the image quality is unknown. The ADR
  stated none of these. Its messages and comments also used "reset point",
  "image quality" and "low light", which weren't glossary terms.
- **How it was caught:** the project review of ADR-0054's code.
- **Kind:** process.
- **Pattern:** how-I-work.
- **Guard:** working rule 8.
- **Takeaway:** before the commit, list each rule, threshold and new word the
  code uses that the ADR and glossary don't, and bring them to me.

### M-120, 2026-11-10: The mock found the settle height again every tick

- **What happened:** the Crazyflie adapter keeps the settle height once
  found, but the mock adapter recomputed it every tick, so a flow cut after
  the settle height would land the mock drone at the cap and not the real
  one.
- **How it was caught:** the project review of ADR-0054's code.
- **Kind:** testing.
- **Pattern:** weak-test.
- **Guard:** Q-09.
- **Takeaway:** for each state the real adapter keeps once set, check that
  the mock keeps it too.

### M-119, 2026-11-10: An old status logged as current, and a reset logged before it was sent

- **What happened:** the arm log said "The drone reports" for a drone status
  of any age. The estimate reset logged the estimate it erases, then "not
  sent: the link is closed". The mock's `FLOW_VELOCITY_UNCERTAINTY_VALUE` (a
  reading) was named almost like the interface's `FLOW_VELOCITY_UNCERTAINTY`
  (the limit), and a docstring quoted First flight 2's readings.
- **How it was caught:** the project review of ADR-0054's code.
- **Kind:** communication.
- **Pattern:** message-misstates-outcome.
- **Guard:** none yet.
- **Takeaway:** a log line about telemetry gives its age, and an action is
  logged only on the path where it happens.

### M-118, 2026-11-10: A cut-off extraction read as the touchdown

- **What happened:** Claude's printout of Take-off speeds flight 1's
  estimate stopped at 3.15 s, 0.25 s before touchdown, and Claude logged
  those values as the shift at touchdown (32 cm right, 19 cm forward; it was
  37 cm right, 23 cm forward). In chat it then said flight 2's drift was
  half on the landing "like flight 1"; flight 1's was about a third.
- **How it was caught:** re-reading the flight's log for the handoff.
- **Kind:** communication.
- **Pattern:** reading-field-data.
- **Guard:** working rule 4.
- **Takeaway:** check that an extraction reaches the moment it's quoted
  for, and compare flights only from numbers already checked.

### M-117, 2026-11-10: Session 2's light blamed on a check that didn't exist yet

- **What happened:** reporting the velocity uncertainty limit that landed a
  0.5 m hover in First flight 3 (backlog #80), Claude said it "may also
  explain why the session 2 Hover needed more light". The check was built
  on 2026-11-09, after session 2; session 2's light problem was the estimate
  settle at connect.
- **How it was caught:** checking the timeline for the handoff.
- **Kind:** communication.
- **Pattern:** reading-field-data.
- **Guard:** `/debrief`.
- **Takeaway:** before linking a finding to an earlier session, check the
  code that session flew had the feature.

### M-116, 2026-11-09: A 0.05 s margin on the climb time limit, not flagged

- **What happened:** analyzing First flight 2's Failsafe high, Claude
  recorded that the initial climb ended 2.45 s after the take-off, but didn't
  point out that the time limit (ADR-0056) was 2.5 s, so the one full climb
  so far passed with 0.05 s to spare. ADR-0059 then kept 2.5 s for 0.2 m/s.
  In First flight 3 the climb was slower and the time limit landed the drone
  before the hover, so Failsafe high didn't test the failsafe.
- **How it was caught:** analyzing First flight 3's Failsafe high log.
- **Kind:** safety design.
- **Pattern:** reading-field-data.
- **Guard:** `/debrief`.
- **Takeaway:** when a flight shows how long a step took, compare it with
  that step's time limit and say the margin.

### M-115, 2026-11-09: ADR-0054 described from its number, not its text

- **What happened:** arguing for the owed `/project-review` before First
  flight 3's Failsafe low, Claude said ADR-0054 changed how the initial
  climb lands the drone at the settle cap. ADR-0054 is a fresh position
  estimate for every take-off; it kept the cap from ADR-0048. The take-off
  does run ADR-0054's code, so the case for the review still held, but the
  reason given was wrong, and I chose to fly first on it.
- **How it was caught:** linking the ADR in the drafted test log, where its
  file name didn't match.
- **Kind:** communication.
- **Pattern:** said-without-checking.
- **Guard:** working rule 2.
- **Takeaway:** before citing what an ADR decides, read its title and
  Decision section, not a code comment that mentions it.

### M-114, 2026-11-08: "In this light it never did", for a run with no flow data

- **What happened:** First flight 3's Failsafe low run stopped at connect
  ("Settling the position estimate took longer than 20 s"). Claude told me the
  cause was too little room light for the Flow deck, as fact. That run's log
  has no flow data: the diagnostic log stream starts only after connect waits
  for the estimate. I had added light for the Hover run that came next, and
  it connected with a surface quality around 95, so darkness is likely but
  not shown by the data.
- **How it was caught:** reading the Hover run's log, which had flow data the
  failsafe run's log lacked.
- **Kind:** communication.
- **Pattern:** reading-field-data.
- **Guard:** `/debrief`.
- **Takeaway:** before naming the cause of a field failure, check the log
  holds the data that shows it; otherwise say it's a likely cause.

### M-113, 2026-11-08: "First flight 1 didn't hit it", with cflib's close unchecked

- **What happened:** explaining the lock behind backlog #67, Claude said
  First flight 1's landings couldn't have locked the drone. It hadn't read
  cflib's `close_link()`, which sends a zero-thrust setpoint that can lock it
  the same way. Whether those flights locked isn't known. The same message
  said the firmware files answer the second half of backlog #62, which
  wasn't checked. Corrected in chat before the ADR was written.
- **How it was caught:** reading `close_link()` while writing ADR-0058.
- **Kind:** communication.
- **Pattern:** said-without-checking.
- **Guard:** working rule 1.
- **Takeaway:** before explaining why an earlier case worked, check every
  call on its path, the library's close and cleanup included.

### M-111, 2026-11-07: "About 4.5 s" for the no-flow uncertainty, read from an upper bound

- **What happened:** explaining ADR-0054's 5 s wait, Claude told me a no-flow
  drone's velocity uncertainty takes about 4.5 s to pass 0.03 m/s. Bench run
  3 shows only that it passed about 0.03 m/s within about 5 s of the reset:
  cflib's settle check compares 10 samples, 500 ms apart, so a failed settle
  is an upper bound. It may pass much sooner. Corrected in chat before
  anything was decided on it.
- **How it was caught:** answering my question whether the 5 s can be shorter.
- **Kind:** communication.
- **Pattern:** reading-field-data.
- **Guard:** working rule 4.
- **Takeaway:** when a number comes from a pass/fail check, say whether it's a
  bound or a measurement.

### M-108, 2026-11-06: "About 8" parameter writes for "Charge", counted one per note

- **What happened:** ADR-0053 said each chirp or note is one parameter write,
  about 8 for "Charge". A tone writes the pitch and then the effect, as the
  same ADR decides, so "Charge" is 13 writes: two for each of its 6 notes,
  and the silence. Fixed in the ADR before any code ran on the drone.
- **How it was caught:** writing the Crazyflie adapter's tone command.
- **Kind:** communication.
- **Pattern:** said-without-checking.
- **Guard:** none yet.
- **Takeaway:** a count of writes or packets is taken from the calls the
  code makes for each event, not from the number of events.

### M-107, 2026-11-06: A pre-check rule that would end the game at a dark hiding spot

- **What happened:** for backlog #48, Claude recommended that a high
  velocity uncertainty fail the safety pre-check, without saying what it does
  on the floor. A failed pre-check ends the flight for good (ADR-0030), and a
  drone landed at a dark hiding spot gets no flow, so the check would have
  ended every hide-and-seek round. Fixed before the ADR: the pre-check checks
  it only in flight, and the take-off rule on the floor (ADR-0054).
- **How it was caught:** answering my question about when the two checks run.
- **Kind:** safety design.
- **Pattern:** safety-judgment.
- **Guard:** Q-24.
- **Takeaway:** for each new pre-check condition, ask what it does on a
  landed drone. A condition that can fail on the floor belongs in the
  take-off rule.

### M-106, 2026-11-06: A sound effect's number read from an out-of-date comment

- **What happened:** Claude told me that `sound.effect` 11 plays the steady
  tone at `sound.freq`. That number came from the parameter's doc comment in
  `sound_cf2.c` (firmware 2026.08), which lists 11 as "Bypass". The effects
  table the number indexes has "Ride of the Valkyries" at 11, so the steady
  tone is 12, and the comment is out of date. No code or ADR used it.
- **How it was caught:** reading the effects table to choose the end-of-test
  tune.
- **Kind:** communication.
- **Pattern:** said-without-checking.
- **Guard:** working rule 2.
- **Takeaway:** a number that indexes a table is read from the table, not
  from a comment that describes it.

### M-105, 2026-11-06: A hand-over order justified by a cflib call it doesn't match

- **What happened:** since the first adapter code (2026-10-20),
  `_release_velocity_streaming()` has released the setpoint stream before
  the high-level command, with a comment saying cflib's `MotionCommander`
  does the same before landing. It doesn't: `MotionCommander.land()`
  releases after its stop setpoint, with the motors already off. In flight,
  the firmware commands the motors off from the release until the high-level
  command arrives (backlog #56). Nothing streams in flight yet, so it never
  flew.
- **How it was caught:** checking cflib's `motion_commander.py` while
  explaining backlog #56.
- **Kind:** safety design.
- **Pattern:** said-without-checking.
- **Guard:** Q-02.
- **Takeaway:** when code cites a library as precedent, check that the
  library does it in the same situation. The review checklist's first two
  questions already ask for this.

### M-104, 2026-11-06: ADR-0041 amended twice without its status line saying so

- **What happened:** ADR-0049 (Failsafe low forges its fault during the
  climb, and the program takes `--fault-at` instead of a height) and ADR-0051
  (the forged battery voltage becomes 3.0 V) both amend ADR-0041, and say so
  themselves. ADR-0041's status line mentioned neither, so it still read as
  if both tests flew to a height argument with a forged 3.2 V.
- **How it was caught:** Claude, building ADR-0051 (the forged value) and
  then marking the status line (ADR-0049).
- **Kind:** process.
- **Pattern:** records-ahead-of-code.
- **Guard:** Q-33.
- **Takeaway:** none new: the checklist already asks whether the older ADR's
  status line is marked. Mark it in the same commit as the new ADR.

### M-103, 2026-11-05: The Crazyflie's weight in the glossary, with no source

- **What happened:** the glossary's first version (2026-10-18) gives the
  Crazyflie 2.1+ as 27 g. Bitcraze's product page and datasheet for the 2.1+
  give a take-off weight of 29 g.
- **How it was caught:** reading Bitcraze's specs for backlog #50.
- **Kind:** environment.
- **Pattern:** said-without-checking.
- **Guard:** Q-01.
- **Takeaway:** the review checklist's first rule already covers it: hardware
  facts are checked, not recalled, glossary entries included.

### M-102, 2026-11-05: A firmware shutdown at 3.0 V that the default build leaves out

- **What happened:** ADR-0030 lists a firmware backup, and the docstring of
  `LOW_BATTERY_VOLTAGE` repeats it: after 5 s at 3.0 V the firmware shuts
  the drone down. That branch does call `pmSystemShutdown()`, but the
  function's body is inside `#ifdef CONFIG_PM_AUTO_SHUTDOWN`. That option is
  off by default (`src/hal/src/Kconfig`), and `cf2_defconfig` doesn't turn it
  on (firmware 2026.08 and `master`). On a default build nothing happens at
  3.0 V. The firmware's only reaction to a low battery is its low state at
  3.2 V for 5 s: a red M1 LED and a sound. The check read the call, not
  the function.
- **How it was caught:** checking the firmware's battery handling at 2026.08
  for backlog #50.
- **Kind:** safety design.
- **Pattern:** said-without-checking.
- **Guard:** Q-03.
- **Takeaway:** a claim that the firmware "does X" needs the body of the
  function called, and any `#ifdef` or build option around it, checked
  against the build flashed. The review checklist's question about the
  guarding `if` now covers build options.

### M-101, 2026-11-05: `kalman.varPX` called the position variance

- **What happened:** in backlog #48, four test logs of 2026-11-04 and a
  takeaway below, Claude called `kalman.varPX` the position variance. The
  firmware logs the velocity variance in the drone's x direction there
  (`estimator_kalman.c` 471-474, firmware 2026.08). The conclusions held: it
  grows when the Flow deck gives no flow. But it stays small when flow
  arrives and is wrong, which ruled it out as the measure for ADR-0048.
- **How it was caught:** checking the firmware source for ADR-0048.
- **Kind:** communication.
- **Pattern:** said-without-checking.
- **Guard:** Q-01.
- **Takeaway:** name a log variable by what the firmware source says it
  holds, not by its name. The review checklist's first question already
  asks for this.

### M-100, 2026-11-05: "Touchdown never confirmed", read from a log line that wasn't there

- **What happened:** analyzing the first flights, Claude wrote in three test
  logs and backlog #51 that touchdown was never confirmed, and that the
  motors kept running on the floor for 2 s. The evidence was the final
  descent's warning and no confirmation line, but the adapter logs nothing
  when touchdown is confirmed. Replaying the Hover log through the real
  touchdown check confirms it 0.3 s into the final descent; "landed" came
  2 s later because the drone status says flying for 2 s after the motors
  stop, which ADR-0032 already recorded.
- **How it was caught:** starting on the fix for #51, by replaying the logged
  snapshots through `TouchdownDetector`.
- **Kind:** testing.
- **Pattern:** reading-field-data.
- **Guard:** `/debrief`.
- **Takeaway:** a missing log line shows nothing until the code is checked to
  log that outcome. Before naming a cause from a flight log, replay the
  recorded data through the real code.

### M-098, 2026-11-04: A go/no-go rule of "the motion flag set in most samples"

- **What happened:** for the pre-flight Flow deck check, Claude said the
  drone was fit to fly when the motion flag was set in most samples. With a
  flashlight giving a clear view, the flag read "no motion" in most samples,
  which is right for a drone sitting still, while the velocity variance held
  steady. The flag being set while still had been sensor noise.
- **How it was caught:** the next check's data, before the flight.
- **Kind:** communication.
- **Pattern:** reading-field-data.
- **Guard:** `/debrief`.
- **Takeaway:** a go/no-go rule names the quantity that matters (here, the
  velocity variance staying small), not a sign that only went with it once.

### M-097, 2026-11-04: A Bench criterion of 0.5 s for a value that streams at 1 Hz

- **What happened:** the Bench test log's pass criterion said no value may be
  older than 0.5 s. The battery voltage streams once a second by design
  (ADR-0023), and the safety layer allows it 3 s, so it failed the criterion
  on half the ticks of a healthy run.
- **How it was caught:** computing the oldest age of each value from the
  Bench logs, then checking the safety layer's limits.
- **Kind:** testing.
- **Pattern:** reading-field-data.
- **Guard:** `/debrief`.
- **Takeaway:** a pass criterion about telemetry ages takes each value's
  limit from the code, not one round number.

### M-096, 2026-11-04: The Flow deck's maximum shutter read as "too dark"

- **What happened:** analyzing why the estimate wouldn't settle, Claude said
  `motion.shutter = 8191` (the maximum) meant the Flow deck hardly saw any
  light. In the next check, with the problem gone, the shutter still read
  8191. The real difference was the motion flag and the surface quality.
- **How it was caught:** the next check's data.
- **Kind:** communication.
- **Pattern:** reading-field-data.
- **Guard:** `/debrief`.
- **Takeaway:** call a reading the cause only after a case where it differs;
  until then, call it a hypothesis.

### M-095, 2026-11-04: "A red LED that keeps blinking means a failed self-test"

- **What happened:** during the first power-on, Claude said a red LED that
  keeps blinking probably means the self-test failed. Bitcraze's docs say a
  steadily blinking red LED is the normal heartbeat; a failure is five fast
  red blinks and a pause.
- **How it was caught:** looking up the LED sequences when I described the
  pattern, before telling me what it meant.
- **Kind:** environment.
- **Pattern:** said-without-checking.
- **Guard:** Q-01.
- **Takeaway:** the same as for the battery placement: hardware facts come
  from the maker's docs, also in chat.

### M-094, 2026-11-04: WinUSB for the Crazyradio, and "the README says WinUSB"

- **What happened:** Claude told me to install the WinUSB driver with Zadig,
  and later said the README asks for WinUSB. It doesn't name a driver. cflib
  0.1.34 finds the radio through the libusb0 backend on Windows
  (`crazyradio.py:72`), which needs libusb-win32; with WinUSB cflib wouldn't
  find the dongle.
- **How it was caught:** checking the installed cflib source before I picked
  the driver.
- **Kind:** environment.
- **Pattern:** said-without-checking.
- **Guard:** Q-01.
- **Takeaway:** check the installed cflib source, as CLAUDE.md says, and quote
  the repo's docs only after reading them.

### M-093, 2026-11-04: A battery connector named from memory

- **What happened:** Claude said the Crazyflie's battery connector is a 2-pin
  JST-PH 2.0 mm. My battery's datasheet says Molex 51005, and it fits.
- **How it was caught:** the datasheet I pasted.
- **Kind:** environment.
- **Pattern:** said-without-checking.
- **Guard:** working rule 1.
- **Takeaway:** for connectors and polarity, the check is the physical fit and
  the + marking, and the maker's docs; never a part number from memory.

### M-092, 2026-11-04: ADR-0046 applied without searching for the old wording

- **What happened:** ADR-0046 changed the snapshot's time from the tick's
  start to a clock reading after the copy. Claude updated the code it named
  but left the old meaning in ADR-0009's Consequences (its status line not
  marked as amended), the glossary's *Clock* entry, `clock.py`'s docstring
  and three "tick time" docstrings. Trimming `Stamped.age()`'s docstring also
  dropped "never divide by an age", which still holds: an age can be 0.
- **How it was caught:** `/project-review` (its `/code-review` step and the
  ADR check) before committing my third code review's fixes.
- **Kind:** process.
- **Pattern:** records-ahead-of-code.
- **Guard:** Q-35.
- **Takeaway:** when a change alters what a value means, search for the old
  wording everywhere (code, glossary, ADRs) before calling it done. When
  trimming a docstring, keep each piece of guidance that's still true.

### M-091, 2026-11-04: A shortened log line that dropped the outcome

- **What happened:** the short-message sweep turned the failsafe test's last
  line, "landed. Done (the test failed).", into "landed. Done.". That step is
  reached only after a failure, so the operator's last line read like a pass.
- **How it was caught:** `/project-review`, before committing.
- **Kind:** communication.
- **Pattern:** message-misstates-outcome.
- **Guard:** Q-44.
- **Takeaway:** shortening a message removes reasons, never the outcome
  (failed, not confirmed, refused).

### M-090, 2026-11-04: Restoring a planted bug with `git checkout` discarded edits

- **What happened:** while proving a new test by bug planting, Claude
  restored the planted file with `git checkout`, which also threw away that
  file's uncommitted review fixes. Claude saw the diff vanish at once and
  re-applied them.
- **How it was caught:** Claude, checking the file's diff right after.
- **Kind:** testing.
- **Pattern:** how-I-work.
- **Guard:** none yet.
- **Takeaway:** before planting a bug in a file with uncommitted work, copy
  it and restore from the copy; never `git checkout` it.

### M-089, 2026-11-04: "No test enforces it" said without looking at the tests

- **What happened:** reviewing the rescue landing program in my third code
  review, Claude said that only the rescue landing passing
  `take_over_flight=True` was a stated rule with no test, and offered a
  fitness function for it. That fitness function already existed
  (`test_only_the_rescue_landing_program_asks_to_take_over_a_flight`, in the
  architecture tests).
- **How it was caught:** Claude, listing the test names for the same review.
- **Kind:** communication.
- **Pattern:** said-without-checking.
- **Guard:** none yet.
- **Takeaway:** before saying a rule has no test, search the tests for it.

### M-088, 2026-11-04: "Can only be a clock bug", and a cost overstated

- **What happened:** ADR-0042, the glossary's *Negative age* and the safety
  layer's warning said an age more negative than a tick period can only be a
  clock bug. A stall between reading the tick's time and copying the buffer
  (a garbage-collector pause, Windows scheduling) can cause one too. The same
  ADR turned down reading the time after the copy (option D) as a change to
  the tick timing model; it isn't one, since the tick loop keeps its own start
  time.
- **How it was caught:** Claude, answering my question about how values can
  come from the future, during my third code review. ADR-0046 now reads the
  time after the copy, so negative ages can't happen.
- **Kind:** design.
- **Pattern:** said-without-checking.
- **Guard:** none yet.
- **Takeaway:** "can only be" needs every path checked, threads and stalls
  included. Weigh an option's cost against what it would really change.

### M-087, 2026-11-04: "Isn't known to be flying", the opposite of the rule

- **What happened:** the `hover()` docstring in the drone interface, the
  adapter's "Hover ignored" log message and the docstring of its streak flag
  said hover does nothing when the drone "isn't known to be flying". The rule
  (ADR-0039, *May be flying*) is the opposite: when unsure, the adapter says
  flying, so the hover goes through. The code was right; only the words were
  backwards. They came from two review-fix commits (`4c1ef1f`, `045c0be`)
  in the next-up run, which no later review read.
- **How it was caught:** Claude, showing me the diffs for my third code
  review. Fixed: the docstrings use *may be flying*, and the log message is
  now one short sentence.
- **Kind:** communication.
- **Pattern:** safety-judgment.
- **Guard:** Q-50, Q-51.
- **Takeaway:** wording that describes a safety judgment must say which way
  it fails when unsure. Review fixes are new code and need a review too.

### M-086, 2026-11-04: Comments that said more than their code

- **What happened:** fixing the take-over message, Claude wrote a comment
  saying none of the estimates was finite, though the branch runs when either
  one is missing. The comment on dropped estimates kept saying the failsafe's
  landing "has a real position to go to", which ADR-0045 had already shown
  doesn't help a drone whose own estimate is NaN.
- **How it was caught:** Claude, in the `/project-review` before committing.
  Both comments are fixed, and backlog #45 now notes the in-flight case.
- **Kind:** communication.
- **Pattern:** records-ahead-of-code.
- **Guard:** working rule 3.
- **Takeaway:** when a decision shows a reason is wrong, search for the
  comments that give that reason, not only the code it changed.

### M-085, 2026-11-04: A time-limit message that read the telemetry again after the check

- **What happened:** for ADR-0045, `_first_telemetry_time_limit_message`
  called `missing_values()` again after the wait's last check. A value
  arriving in between could make the message say "Still missing: ." or, on a
  take-over, switch the advice from the emergency stop to "check the range".
  The old message had the same race, but then it only chose wording.
- **How it was caught:** Claude, in `/project-review` (the code review). Fixed:
  the message now uses the list from the check that timed out, with a test
  proven by bug planting.
- **Kind:** design.
- **Pattern:** message-misstates-outcome.
- **Guard:** Q-26.
- **Takeaway:** a wait's error message describes the state that timed out:
  hand it the result of the last check, not a fresh read. Now a question in
  the review checklist.

### M-084, 2026-11-04: A take-over message that assumed the drone was flying

- **What happened:** the ADR-0045 message said "The drone can't land under
  control", and its comment and a test comment said the drone was flying.
  But a take-over also accepts a drone on the floor (ADR-0039). The
  dropped-estimate warning said "the last finite one stays", when on that
  path none may ever have arrived.
- **How it was caught:** Claude, in `/project-review`. Fixed: the message says
  "If the drone is in the air", and the warning says "any earlier finite one".
- **Kind:** communication.
- **Pattern:** message-misstates-outcome.
- **Guard:** Q-43.
- **Takeaway:** the checklist's "Does each log message's stated cause hold on
  every path?" already asks this; follow the paths into the case the
  message's author didn't picture.

### M-083, 2026-11-04: A "known risk" that cflib's own guard rules out

- **What happened:** for the next-up run's question 4, Claude said that
  cflib's `SyncCrazyflie.open_link` calls `close_link()` after a failed
  download of the parameter and log tables, and that `close_link()` sends a
  zero-thrust setpoint that drops a flying drone. I accepted it as a known
  risk. It went into ADR-0038, backlog #43 (a max-level rewrite of how the
  adapter opens the link) and the field-testing README, and the note named no
  source file.
- **Why it was wrong:** `close_link()` sends the setpoint only
  `if self.link is not None`, and every path from `open_link` to it has set
  `link` to None first (cflib 0.1.34, `crazyflie/__init__.py`).
- **How it was caught:** Claude, in `/project-review` (a fresh code review
  reading cflib's source). Backlog #43 is removed and ADR-0038 says so.
- **Kind:** recommendation.
- **Pattern:** said-without-checking.
- **Guard:** Q-03.
- **Takeaway:** a claim that a library "does X when Y fails" needs the
  condition around the call checked, not only the function's body. The
  review checklist's library-call question now says so.

### M-082, 2026-11-04: Records that claimed more than the code or the source showed

- **What happened:** ADR-0041's amendment and the failsafe program's
  docstring said exit code 0 means the landing finished "with the motors
  stopped". It means `disconnect()` returned: once the radio link is lost,
  cflib drops outgoing packets without an error, so the motor stop may never
  have left the PC. ADR-0045 said a missing estimate could also be "lost on
  the radio", which can't happen on a take-over (the status that ends the
  status wait arrives in the same packet as the estimates).
- **How it was caught:** Claude, in `/project-review`. The exit code's claim
  is corrected; detecting a lost link is backlog #46.
- **Kind:** communication.
- **Pattern:** message-misstates-outcome.
- **Guard:** Q-52.
- **Takeaway:** when a record says an action "stopped" or "landed", name what
  observed it. A command sent over the radio is not a command that arrived.
  The checklist question about success and exit codes now says so.

### M-081, 2026-11-04: An ADR amendment without the documents and the test that follow from it

- **What happened:** after ADR-0041 was amended (the program judges the pass,
  and exit code 0 includes `disconnect()` returning), the Failsafe low and
  Failsafe high test log drafts still said "the program reports done" and had
  no line for whether touchdown was confirmed; no test covered "a landing
  that raises makes the exit code 1"; ADR-0036 and ADR-0038 were amended
  without their status lines saying so (a question the checklist already
  asks); and the field-testing README said any failed connect drops the
  drone, which went further than even ADR-0038's claim.
- **How it was caught:** Claude, in `/project-review`.
- **Kind:** process.
- **Pattern:** records-ahead-of-code.
- **Guard:** Q-36.
- **Takeaway:** an amendment is done when every document that restates the
  rule matches it (test log drafts, README procedures, status lines) and the
  test for the new rule exists. The checklist now asks about test log drafts.

### M-077, 2026-11-03: Crazyflie adapter code committed without `/project-review`

- **What happened:** building ADR-0045, Claude changed the Crazyflie
  adapter (a new time-out message for a take-over connect, then a comment)
  and committed and pushed it with tests and bug planting, but without the
  `/project-review` that `CLAUDE.md` requires before committing adapter
  changes. The stop hook's push-every-change rule made it easy to forget.
- **Why it was wrong:** the rule has no size exception, and the change is on
  the rescue landing's path.
- **How it was caught:** Claude, at the end of the session.
- **Kind:** process.
- **Pattern:** how-I-work.
- **Guard:** working rule 10.
- **Takeaway:** before each commit, check whether it touches the safety
  layer, the Crazyflie adapter or the tick loop. If it does, review first,
  or ask before committing without one.

### M-076, 2026-11-03: Docstrings that a change left behind

- **What happened:** after ADR-0038 and ADR-0039, the `DroneInterface`
  docstrings still said `disconnect()` always leaves the drone on the
  ground and `hover()` always holds the position. The failsafe program's
  `main()` still said its exit code meant "the failsafe landed the drone",
  after the first review had fixed the same claim elsewhere. A test
  docstring credited `judge()` with the adapter's "unsure counts as
  flying". `_close_radio_link_only` said it did "the rest of" cflib's
  `close_link()`, though it skips three steps. The first review had fixed
  six more of the same kind (in `start_up.py`, the adapter and the safety
  layer).
- **Caught at:** the end-of-run reviews of the next-up run (pull request
  #8), the second one by the fresh-context read.
- **Kind:** communication.
- **Pattern:** records-ahead-of-code.
- **Guard:** working rule 3.
- **Takeaway:** when a decision changes what a function does, search for
  every docstring that describes it, the interface's included, and fix a
  claim everywhere it was copied, not only where it was found.

### M-075, 2026-11-03: An emergency stop that said "not delivered" when it may have been

- **What happened:** `tools/emergency_stop.py` printed "the radio did not
  deliver the emergency stop" whenever the stop wasn't confirmed, also when
  the radio took every packet and only reported a link error on the way.
- **Caught at:** the second end-of-run review of pull request #8.
- **Kind:** communication.
- **Pattern:** message-misstates-outcome.
- **Guard:** Q-43.
- **Takeaway:** a failure message names every way to reach it (REVIEW.md:
  the stated cause holds on every path).

### M-074, 2026-11-03: A once-per-streak log line whose streak never ended

- **What happened:** the adapter's "Hover ignored" line (ADR-0039) was
  limited to once per streak, but the flag was cleared only by `connect()`
  and `take_off()`, not by a hover that went through. After the first
  ignored hover, a taken-over flight, which never sends a take-off, would
  never log another.
- **Caught at:** the second end-of-run review of pull request #8, reproduced
  with a script.
- **Kind:** design.
- **Pattern:** leftover-state.
- **Guard:** Q-18.
- **Takeaway:** a once-per-streak flag is cleared on every path that ends
  the streak (now a REVIEW.md question).

### M-073, 2026-11-03: A new connection that kept the last one's landing

- **What happened:** `connect()` started resetting per-connection state for
  ADR-0038 (airborne, the drone status, the telemetry) but not the landing
  phase. A landing left half-done by a failed disconnect resumed on the next
  connection's first snapshot: a motor stop for a taken-over flying drone,
  or a `go_to` that spins up an armed drone on the floor (ADR-0039's
  "Never"). Only reachable when one adapter connects twice, which only the
  tests do today.
- **Caught at:** the second end-of-run review of pull request #8, reproduced
  with the tests' fake cflib.
- **Kind:** safety design.
- **Pattern:** leftover-state.
- **Guard:** Q-17.
- **Takeaway:** state reset for a new connection is checked against the
  constructor's field list (now a REVIEW.md question).

### M-072, 2026-11-03: Fitness functions with blind spots

- **What happened:** the scanner behind ADR-0041's fitness function handled
  four import forms, but tests exercised only one: planting a bug in the
  others left every test green, so a game program importing the fault as
  `from crazyflie_behavior.programs import failsafe_fault` would have
  passed. And ADR-0038's rule that only the rescue landing may take over a
  flight had no fitness function at all, though `make_drone()` offers the
  setting to every program.
- **Caught at:** the first end-of-run review of pull request #8 (left
  unfinished), fixed after the second.
- **Kind:** testing.
- **Pattern:** weak-test.
- **Guard:** Q-32.
- **Takeaway:** a fitness function's scanner gets a test for each form it
  handles, on a made-up file; every structural "only" in a new ADR gets its
  fitness function in the same change.

### M-071, 2026-11-03: Two constants that must agree, with no test between them

- **What happened:** the failsafe test's `FAULT_TIME_LIMIT` (10 s) must
  exceed the wrapper's `HOVER_DURATION_BEFORE_FAULT` (3 s), or the test
  lands before the fault is injected. Nothing related them, and two
  docstrings copied "3 s".
- **Caught at:** the first end-of-run review of pull request #8, fixed after
  the second.
- **Kind:** testing.
- **Pattern:** weak-test.
- **Guard:** Q-47.
- **Takeaway:** when one placeholder only works relative to another, a test
  says so, and the docstrings point to the constant instead of copying it.

### M-070, 2026-11-03: A taken-over flight given the take-off grace period

- **What happened:** taking over a flight (ADR-0038) started the 1 s take-off
  grace period without reading the status, so a rescue run on an armed
  drone already on the floor would send a floor-height `go_to` (ADR-0039's
  "Never").
- **Caught at:** the first end-of-run review of pull request #8.
- **Kind:** safety design.
- **Pattern:** safety-judgment.
- **Guard:** none yet.
- **Takeaway:** a new way into a state ("as if we had sent the take-off")
  is checked against every rule that state's usual entry carries.

### M-069, 2026-11-03: An emergency stop that said "Sent." when nothing was

- **What happened:** `tools/emergency_stop.py` ignored `send_packet()`'s
  result and printed "Sent." after about 38 s of silence when nothing
  reached the drone (reproduced against cflib's real `RadioDriver`).
- **Caught at:** the first end-of-run review of pull request #8.
- **Kind:** safety design.
- **Pattern:** message-misstates-outcome.
- **Guard:** Q-52.
- **Takeaway:** a tool whose job is one outcome reports success only when
  that outcome happened (now a REVIEW.md question).

### M-068, 2026-11-03: A rescue landing that exited 0 when the rescue failed

- **What happened:** the rescue landing program returned exit code 0 after
  a refused landing or its time limit.
- **Caught at:** the first end-of-run review of pull request #8.
- **Kind:** design.
- **Pattern:** message-misstates-outcome.
- **Guard:** Q-52.
- **Takeaway:** the same as the emergency stop's: the exit code is part of
  the report.

### M-067, 2026-11-03: A mitigation in ADR-0044 that the code didn't provide

- **What happened:** ADR-0044 said "nothing in our code sends it a
  setpoint" during the Bench, but `disconnect()` on a drone on the floor
  makes cflib send a zero-thrust setpoint, and `connect()` resets the
  estimate.
- **Caught at:** the first end-of-run review of pull request #8.
- **Kind:** safety design.
- **Pattern:** records-ahead-of-code.
- **Guard:** none yet.
- **Takeaway:** a safety claim in an ADR is checked against the code path
  it describes, end to end, before it's recorded.

### M-066, 2026-11-03: ADR-0043 described the old field-testing README wrongly

- **What happened:** ADR-0043 said the old README's gate and simulator rule
  were different from what it said (the gate belonged to each stage; the
  simulator was required except for Bench and Hover).
- **Caught at:** the first end-of-run review of pull request #8.
- **Kind:** process.
- **Pattern:** said-without-checking.
- **Guard:** working rule 2.
- **Takeaway:** when an ADR describes what it replaces, quote or re-read
  the old text rather than summarizing it from memory.

### M-065, 2026-11-03: A test fake that streamed only once

- **What happened:** the first `FakeCflib` sent each log block's sample once,
  but `connect()` swaps the telemetry buffer after the estimate reset and
  relies on the drone streaming on, so the fake couldn't model it.
- **Caught at:** while building it.
- **Kind:** testing.
- **Pattern:** weak-test.
- **Guard:** Q-09.
- **Takeaway:** REVIEW.md's "how does the real adapter differ from the
  fake?" applies to timing too: a real drone keeps streaming.

### M-064, 2026-11-03: New vocabulary in code names before proposing it

- **What happened:** the unattended run named code with terms the glossary
  lacks (Failsafe test, Forged low battery drone, Take over, Streak, and
  others), then proposed them in the pull request afterwards.
- **Why it was wrong:** CLAUDE.md says to propose a term before introducing
  it in code.
- **Caught at:** the first end-of-run review of pull request #8.
- **Kind:** process.
- **Pattern:** vocabulary.
- **Guard:** working rule 6.
- **Takeaway:** in an unattended run, propose the term in the pull request
  and use a plain description in code until it's accepted, or record the
  name as a choice for Joe to confirm before using it.


### M-061, 2026-11-02: A work-log row raised without its total

- **What happened:** the work-log commit for ADR-0040 and ADR-0042 raised the
  2026-11-02 row from ~2.5 to ~3 hours but left the milestone total at
  ~36.75; the rows summed to ~37.25.
- **Caught at:** adding the next row to the same day, by summing the rows
  with a script.
- **Kind:** process.
- **Pattern:** how-I-work.
- **Guard:** none yet.
- **Takeaway:** when a work-log row's hours change, recompute the milestone
  total from the rows, not by adding the change to the old total.

### M-060, 2026-11-02: A tick period quoted from memory

- **What happened:** explaining the negative-ages options, Claude gave one
  tick period as 20 ms at 50 Hz.
- **Why it was wrong:** the tick loop runs at 20 Hz (`TICK_RATE`), so a tick
  is 50 ms.
- **Caught at:** looking up `TICK_RATE` while writing ADR-0042, before it was
  recorded.
- **Kind:** communication.
- **Pattern:** said-without-checking.
- **Guard:** working rule 1.
- **Takeaway:** look up project constants before quoting them, even in
  conversation.

### M-059, 2026-11-02: A watchdog recommended that the backlog already ruled out

- **What happened:** for where landing progress runs (backlog #8), Claude
  recommended D, a hang watchdog thread that lands the drone, and listed a
  hang inside cflib only as something to check later.
- **Why it was wrong:** backlog #26 already recorded that a watchdog thread on
  the PC is no real backup, because its land command waits behind the same
  blocked cflib send. D still helps with hangs outside cflib, but it was
  presented as covering more than it does.
- **Caught at:** writing up the decision (A, with D backlogged), when Claude
  found #26 before adding a new backlog item.
- **Kind:** recommendation.
- **Pattern:** recommendation.
- **Guard:** working rule 5.
- **Takeaway:** before proposing options, search the backlog and ADRs for the
  same problem; an earlier finding may already rule an option out.

### M-058, 2026-11-02: A refusal that drops the drone it protects

- **What happened:** for backlog #36, Claude recommended that `connect()`
  refuse a flying drone, right after noting that any `connect()` failure
  closes the link and drops it, and the draft ADR said the refusal closes the
  link "without a drop".
- **Why it was wrong:** the refusal is a `connect()` failure too. cflib's
  `close_link()` sends a zero-thrust setpoint before closing, so the refusal
  would drop the flying drone (the adapter's own `disconnect()` comment says
  so).
- **Caught at:** checking `close_link()` in the cflib source while writing the
  ADR, before it was recorded.
- **Kind:** safety design.
- **Pattern:** safety-judgment.
- **Guard:** Q-21.
- **Takeaway:** for a new failure path, follow it through its cleanup, and
  check what that cleanup sends to a drone that may be flying.

### M-057, 2026-11-02: Manual arming called a barrier that doesn't rely on our code

- **What happened:** for backlog #37, Claude said manual arming (our own
  firmware build) gives hide-and-seek "a second barrier that doesn't rely on
  our code staying correct".
- **Why it was wrong:** the arm request comes from our code too. A bug that
  sends an arm request and then a flight command still spins the motors. It
  is a second step a bug must hit, not a barrier independent of our code.
- **Caught at:** explaining the claim when I asked what it meant.
- **Kind:** safety design.
- **Pattern:** safety-judgment.
- **Guard:** Q-12.
- **Takeaway:** before calling a backup independent, name what triggers it
  and check that the primary's failure can't trigger it too.

### M-056, 2026-11-02: A pushed commit that doesn't pass its own tests

- **What happened:** the review's work was committed by topic, but
  `878c16f` uses `Vector3.is_finite()` and a renamed safety-layer property
  that only arrive in the next commit, so it fails 25 tests on its own. The
  tests ran only before the first commit, and Claude's brief for the commit
  session asked for nothing more.
- **Caught at:** running the tests at each commit after they were made, but
  the commits had been pushed by then. I left the history as it is: the
  commits before and after it pass.
- **Kind:** process.
- **Pattern:** how-I-work.
- **Guard:** working rule 10.
- **Takeaway:** commit in dependency order and run the tests at every commit
  before pushing, so any commit can be rolled back to.

### M-055, 2026-11-02: A failsafe whose landing used the value that failed it

- **What happened:** Claude recommended that the safety pre-check fail on a
  NaN position estimate and land, and built it. But the Crazyflie adapter's
  landing flies to the estimated position, so it would have sent a NaN
  `go_to`, and the NaN end time skipped the planned landing. Claude saw the
  landing problem and put it in the backlog (#38) as later work, although the
  new check made it the planned path.
- **Caught at:** Claude's `/project-review`, at a high level, the same day.
  Now the adapter drops an estimate that isn't finite, so the landing goes to
  the last finite one (ADR-0030); tests are proven by bug planting.
- **Kind:** safety design. A backup sharing the primary's failure.
- **Pattern:** safety-judgment.
- **Guard:** Q-12.
- **Takeaway:** when a check sends a bad value into a failsafe, follow that
  value through the failsafe in the same change. The review checklist
  already asked; the check was skipped while recommending.

### M-054, 2026-11-02: Wording in the NaN change that missed the project's rules

- **What happened:** in the same change, `Verdict`'s new check packed two
  rules into one comparison, although `judge()` had just moved to plain `if`
  statements; `Behavior.tick`'s docstring still promised only "present and
  fresh"; and a comment restated ADR-0030's rule without pointing to it, as
  the coding style asks.
- **Caught at:** the same review.
- **Kind:** communication.
- **Pattern:** records-ahead-of-code.
- **Guard:** none yet.
- **Takeaway:** a new rule also changes the docstrings that promise what
  callers can rely on; check them in the same change.

### M-053, 2026-11-02: The gap between two lines, a fifth time

- **What happened:** the start-up code put the old interrupt signal handler
  back before logging the end of a run. An interrupt signal during those last
  log lines raised KeyboardInterrupt, which the program then logged as
  "Interrupt signal while connecting", ending with exit code 130 after a
  flight that had landed normally. The program's description was also logged
  one line before the `try`, so an interrupt signal there escaped as an
  uncaught KeyboardInterrupt.
- **Caught at:** Claude's `/project-review`, at a high level, before
  committing my second code review's fixes. Both now happen in the right
  order, with two new tests proven by bug planting.
- **Kind:** design. Windows of time between two steps.
- **Pattern:** window-between-steps.
- **Guard:** Q-19.
- **Takeaway:** log lines are lines too: keep a signal handler in place until
  the last line it protects, and log inside the `try`.

### M-052, 2026-11-02: A Windows call whose failure went unnoticed

- **What happened:** `quick_edit_off` ignored what `SetConsoleMode` returned.
  If turning QuickEdit off failed, the log still said it was off, and
  selecting text could pause a tick with no warning. A failed restore went
  unnoticed too.
- **Caught at:** the same review. Both calls are checked now, and a failure is
  a warning with the Windows error; two new tests (Windows only), proven by
  bug planting.
- **Kind:** environment.
- **Pattern:** environment.
- **Guard:** Q-05.
- **Takeaway:** check every Windows call's result: called through ctypes, a
  failure is only a return value, never an exception.

### M-051, 2026-11-02: A log message and a docstring narrower than the code

- **What happened:** an abandoned connect step's late error was logged as
  coming "after its time limit", but a step is also abandoned when the
  interrupt signal stops connecting. And `_HelperStep`'s docstring said a
  thread ends only when its code returns, leaving out raising.
- **Caught at:** the same review. Now "after it was abandoned" and "returns
  or raises".
- **Kind:** communication.
- **Pattern:** message-misstates-outcome.
- **Guard:** Q-43.
- **Takeaway:** check that a log message's cause holds on every path that
  reaches it.

### M-050, 2026-11-02: A review skill whose steps clashed with the skill it runs

- **What happened:** `/project-review` runs `/code-review` and keeps its
  findings for one merged report, but `/code-review`'s own instructions say
  to report them itself. A run that followed `/code-review` would have
  reported twice, with the merged list shown as a re-report.
- **Caught at:** running `/project-review` in the same review. Its step 2 now
  says not to report `/code-review`'s findings separately.
- **Kind:** process.
- **Pattern:** how-I-work.
- **Guard:** none yet.
- **Takeaway:** when a skill runs another skill, read the inner skill's
  instructions for steps that clash with the outer one's.

### M-046, 2026-11-01: A safety gap deferred without checking the planned control that opens it

- **What happened:** after the gap (a) correction, Claude proposed deferring
  the fix for a hover command that can start the motors of a drone on the
  floor (backlog #8), without checking ADR-0027, whose operator controls
  include a "hover" key that would send exactly that command.
- **Why it was wrong:** the deferral assumed nothing sends a hover command
  on the floor before the safety-layer work; the accepted operator controls
  do.
- **Caught at:** the review session, checking the deferral against the ADRs.
- **Kind:** safety design.
- **Pattern:** safety-judgment.
- **Guard:** Q-23.
- **Takeaway:** before deferring a safety gap, check the accepted ADRs for
  planned features that would open it, and tie the fix to the first of them.

### M-045, 2026-11-01: A rename recommended without checking how the project already says it

- **What happened:** in my second code review, Claude recommended renaming
  `missing_values`' "front range" to "front range reading", the glossary
  term. But "down range" is the project's shorthand everywhere: the safety
  layer's stale-data messages, the touchdown code and ADR-0019's title. The
  rename would have made the operator's messages disagree. I accepted it.
- **Caught at:** searching for the old names before making the change.
- **Kind:** recommendation.
- **Pattern:** recommendation.
- **Guard:** working rule 5.
- **Takeaway:** before recommending a rename, search how the rest of the
  project already says it.

### M-044, 2026-11-01: Code called dead without following every path to it

- **What happened:** in my second code review, Claude recommended dropping
  the writes in the mock adapter's `set_range_reading` and
  `set_battery_voltage`, calling them dead because each snapshot rewrites
  every value first. But after `stop_telemetry()` a snapshot rewrites
  nothing, so the hook's write is the last value before the link goes quiet.
  I accepted on that reasoning.
- **Caught at:** the test run after the change: a bench summary test that
  sets a reading and then stops the telemetry failed. The writes are back,
  with a one-line comment saying why they're needed.
- **Kind:** recommendation.
- **Pattern:** recommendation.
- **Guard:** none yet.
- **Takeaway:** before calling code dead, follow every path to where its
  result is read, including early returns.

### M-043, 2026-11-01: A parameter named with a glossary term that means something else

- **What happened:** `run_with_time_limit` called the "what to check" part of
  its timeout message `hint`, but the glossary's *Hint* is the drone's LED
  flash and chirp while it's hidden (ADR-0017). The docstring called the same
  text "what to check" and a comment called it "the fix": three names for
  one thing.
- **Caught at:** walking me through `time_limit.py` in my second code review.
  It's now `what_to_check`, keyword-only, so every call shows the name.
- **Kind:** communication.
- **Pattern:** vocabulary.
- **Guard:** Q-41.
- **Takeaway:** before naming something, look the word itself up in the
  glossary, not only the concept.

### M-042, 2026-11-01: Cloud setup advice from memory

- **What happened:** to get `CLAUDE.local.md` into cloud sessions, Claude
  described the cloud setup script from memory: where to find it, and a line
  that downloads the file into the repo folder. The docs say the script runs
  before Claude Code starts, is cached for about seven days, and should write
  `~/.claude/CLAUDE.md` instead.
- **Caught at:** looking up the docs after I couldn't find the setup script.
- **Kind:** environment.
- **Pattern:** said-without-checking.
- **Guard:** none yet.
- **Takeaway:** check how a tool works in its docs before giving
  step-by-step instructions, the same as checking cflib against its source.

### M-041, 2026-11-01: Code reviews that skipped the review checklist

- **What happened:** CLAUDE.md says every `/code-review` also works through
  `REVIEW.md`. The skill's own steps don't include it, and Claude's two
  high-level reviews on 2026-11-01 followed the skill's steps only.
- **Caught at:** answering my question about why some findings come up only
  in my reviews.
- **Kind:** process.
- **Pattern:** how-I-work.
- **Guard:** working rule 10.
- **Takeaway:** the skill doesn't know this project's checklist, ADRs or
  glossary; a review here must bring them in itself. The project skill
  `/project-review` now does.

### M-040, 2026-11-01: The gap between two lines, a fourth time

- **What happened:** the tick loop added its garbage-collector hook before
  the `try` whose `finally` removes it, with a log call in between. Safe in
  practice (Ctrl+C can't raise by then), but it's the same shape as the
  earlier cleanup gaps.
- **Caught at:** walking me through `tick_loop.py` in my second code review.
  The hook is now added inside the `try`, and removed only if present.
- **Kind:** design. Windows of time between two steps.
- **Pattern:** window-between-steps.
- **Guard:** Q-19.
- **Takeaway:** start anything that needs cleaning up inside the `try` that
  cleans it up.

### M-039, 2026-11-01: A tick that raised left no timing behind

- **What happened:** when the tick step raised, the tick loop skipped
  recording that tick, so the log and the summary left out its work time and
  any overrun warning, against ADR-0026's "every tick is logged". A test
  pinned the old count.
- **Caught at:** walking me through `tick_loop.py` in my second code review.
  The tick is now recorded in a `finally`; a new test is proven by bug
  planting.
- **Kind:** design. Edge cases at the start, end and between ticks.
- **Pattern:** window-between-steps.
- **Guard:** none yet.
- **Takeaway:** on an error path, check that what the normal path records is
  still recorded.

### M-038, 2026-11-01: A cost from Linux in a comment, with no source

- **What happened:** a comment said arming the hang watchdog costs "about
  0.1 ms on Linux", with no source, and the program runs on Windows.
- **Caught at:** walking me through `tick_loop.py` in my second code review.
  Measured on my laptop (0.09 ms median, 0.8 ms worst), and the comment now
  says so.
- **Kind:** environment. Code that was only run on Linux.
- **Pattern:** environment.
- **Guard:** none yet.
- **Takeaway:** a performance figure says where it was measured, on the
  machine the program runs on.

