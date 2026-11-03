# Next up (after the weekly usage reset)

Committed (lives in docs/, not the ignored drafts/) so cloud scheduled
tasks can read it. The weekly limit resets 2026-11-03 at
11:59 AM Pacific; the "Weekly next-up.md run" routine starts at 12:05 PM.

## Rules for an unattended run

The cloud run can't ask Joe anything, and it doesn't have his local-only
rules. On top of `CLAUDE.md`:

- **Joe makes every design decision.** Small local details (log level,
  message wording, helper names) you may choose: list each one in the pull
  request under "Choices for Joe to confirm". An architectural question
  (CLAUDE.md's definition) you don't decide: skip that part, add the
  question to `docs/decision-backlog.md`, and list it under "Questions for
  Joe". Never change `docs/glossary.md`: propose the before and after in the
  pull request.
- **Delivery:** one branch, `next-up-2026-11-03`, and one pull request
  against `main`. One commit per item, each message naming its ADR
  (`Implements ADR-0037`), with the trailer
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Author:
  `Joe <13664218+joecgo@users.noreply.github.com>`, never another address.
  Push the branch after each item, so finished items survive if the run
  stops. Never push to `main`.
- **Done for each item** (CLAUDE.md's definition of done): new tests proven
  by bug planting (`docs/coding-style.md`), and the same checks as
  continuous integration all green (`.github/workflows/checks.yml`: ruff
  format, ruff check, pyright, pytest).
- **The review matters most.** Run it **once**, after all the items are
  built and committed: `/project-review max fresh` on the whole branch
  (`main..next-up-2026-11-03`; `fresh` adds the fresh-context read, the
  skill's step 7). Not one review per item. Never skip it, lower the level or
  drop `fresh`: not when an item is only partly built, not when one has open
  questions, not when checks fail (then review anyway and say so in the pull
  request). Fix only plain bugs with an obvious fix, in one extra commit
  after the review, then re-run the checks. If those fixes are big enough
  to need it, run one more `/project-review max fresh` on the branch and
  handle its findings the same way. Every other finding (ADR
  conflicts, design, glossary, failure rules, anything that needs a
  decision) goes into the pull request description unfixed, with the full
  ranked findings list, since `ReportFindings` may not show anywhere in a
  cloud run.
- **Environment:** Linux, so `.venv/bin/python`, and the installed cflib
  source is in `.venv/lib/python3.12/site-packages/cflib/` (CLAUDE.md gives
  the Windows path). Set up as `checks.yml` does.
- **Logs Joe keeps:** add mistakes you catch yourself to
  `docs/claude-mistakes.md` as CLAUDE.md says. Don't touch `docs/worklog.md`
  or the review log in `REVIEW.md`: Joe adds those rows.
- Tick each item's box below in the same commit. If an item is blocked, say
  why next to it and go on to the next.

## Items, in order

1. [ ] **ADR-0037 C: the auto-arming log line.** The Crazyflie adapter
   (`src/crazyflie_behavior/drone/crazyflie/adapter.py`) logs once at
   connect whether the drone arms itself. Decode the bit from the
   `supervisor.info` bitfield the adapter already streams in the drone
   status log block (ADR-0021); cflib names it `BIT_IS_AUTO_ARMED` in
   `cflib/crazyflie/supervisor.py` (check it there). Don't use cflib's
   blocking `read_bitfield`. Auto-arming stays inside the adapter: adding it
   to the drone interface or `DroneStatus` is a portability decision for
   Joe. `connect()` already waits for the first telemetry (ADR-0031), so the
   status is there to read. Tests in the adapter's test files, with the fake
   cflib.
2. [ ] **ADR-0038: connecting to a flying drone.** Everything in its
   "To build" consequence: the reordered `connect()`, the safe link close,
   the `take_over_flight` setting in the Crazyflie adapter and the mock, the
   rescue-landing program in `src/crazyflie_behavior/programs/`, the
   emergency-stop script in `tools/`, the field-testing procedure note, and
   the tests it names. Item 1's log line has to keep working after the
   reorder.
3. [ ] **ADR-0039: the adapter decides whether the drone may be flying.**
   `judge()` approves `Hover` and `Land` whatever the drone status says; the
   failsafe always puts `Land` in the movement slot, and its log no longer
   says "no landing sent"; the Crazyflie adapter's `hover()` does nothing on
   the floor (not `_may_be_flying()`), logged once per streak at info level
   (Claude's suggestion, not yet confirmed: list it for Joe). Tests for all
   three, including the failsafe landing during the take-off grace period.
4. [ ] **Field tests by name, not "stage 0/1".** Joe's decisions of
   2026-11-02: the field-testing README has no stages any more, only
   calibration, safety and flight tests, each called by name. Everything
   else is already done (the README, the session template and drafts, the
   glossary, the main README). Left for this run: the comments, docstrings
   and argparse descriptions in `src/` and `tools/` that say "field-test
   stage 0" or "stage 1" become "the Bench field test" and "the Hover field
   test" (`programs/bench.py`, `programs/hover.py`,
   `behaviors/hover_test.py`, `drone/crazyflie/adapter.py`; search for
   others). Wording only, no behavior change.
5. [ ] **ADR-0041: the Failsafe low and Failsafe high program.** Joe's
   decision of 2026-11-02, needed for the hardware arriving 2026-11-03. Build
   it after items 1 to 3 (it relies on take-off, hover and the failsafe
   landing working). Run the checks and bug planting as usual; the one
   end-of-run review covers it with the rest of the branch. List any design
   doubts you have under "Questions for Joe".
   - **Program:** `src/crazyflie_behavior/programs/failsafe.py`, shaped like
     `programs/hover.py`: `--crazyflie` (default: the mock adapter) and a
     required `--height-meters`, which accepts only 0.1 (Failsafe low) or 0.5
     (Failsafe high, the Hover test's height; ADR-0041 amended
     2026-11-02). Add a `.run/` configuration for each height, as the
     hover program has.
   - **Behavior:** a field-test behavior in `behaviors/` (ADR-0033: its
     docstring states its failure rule; it stops at its first refused
     request): arm, take off to the height, hover, then report done only after
     the failsafe has landed the drone. Give it a time limit that lands the
     drone normally if the fault never takes effect (ADR-0041's input
     failure mode), logged as a failed test.
   - **The fault (ADR-0041 option A, how decided by Joe 2026-11-02):** a small
     wrapper class around the `DroneInterface`, in the same program module (or
     a file next to it), whose `take_snapshot()` returns the real snapshot
     unchanged until the drone has hovered for about 3 s (a named constant,
     units in the name), then returns it with `battery_voltage` replaced by a
     value below `LOW_BATTERY_VOLTAGE` (use `dataclasses.replace`; check the
     snapshot classes are frozen with slots, ADR-0018). Every other field,
     down range included, stays real: the landing uses it for touchdown
     (ADR-0032). The wrapper logs one warning, "FAULT INJECTED: battery
     voltage forged", when it starts, and delegates everything else to the
     real drone. **Do not change `safety_layer.py`:** the real pre-check and
     failsafe must run unmodified. No flag, hook or parameter in the safety
     layer, behaviors or the drone interface.
   - **Tests:** run the program on the mock adapter at both heights; check
     the pre-check fails with the battery message, a landing is sent, and the
     drone ends landed with its motors off. Bug-plant it: a wrapper that
     injects nothing must make the test fail (the time limit lands it).
     **Architecture test (fitness function):** the wrapper is imported only
     by the failsafe program, and never by `behaviors/`, `safety/`, `loop/`
     or `drone/`. Put it with the other architecture tests.
   - **Docs:** amend ADR-0041's decision with the mechanism above (origin
     line: Joe chose option A; the AI recommended the wrapper with a forged
     low battery), and remove backlog #38 (the ADR now closes it). Add the
     program to the README's "Run" section if it lists programs. Glossary:
     don't edit it; *Failsafe low / Failsafe high* is already there
     (0.1 m and 0.5 m).
6. [ ] **ADR-0042: slightly negative ages count as fresh.** Not needed for
   the hardware; do it last. `Stamped.age()` stays unclamped, and its
   docstring says the age can be slightly negative, meaning just arrived.
   The safety pre-check's staleness check logs a warning when an age is
   below `-MAX_NEGATIVE_AGE` (one tick period, 0.05 s at `TICK_RATE` 20 Hz;
   derive it from `TICK_RATE` if the import doesn't cross a boundary,
   otherwise a named constant, and say which in the pull request), once per
   streak per value. The warning never fails the pre-check. Tests: an age of
   about -0.01 s passes the pre-check with no warning; one of -1 s passes
   and warns once over several ticks, and again after a normal age ends the
   streak.

7. [ ] **ADR-0043: how field tests are organized** (docs only, after item
   6). Record the decisions Joe made on 2026-11-02 while revising
   `docs/field-testing/README.md`; that README and the commit messages
   (`f001895`, `6622b8e`, `7ec3ec2`, `0cc9dff`) are the source. Don't decide anything new:
   - The stage ladder and its gate go. Tests are grouped as calibration
     (Bench, Sensor characterization), safety (Failsafe low, Failsafe high,
     Safety validation) and flight (Hover, Mapping run, Hide-and-seek). The
     first time through, each is passed once, in order.
   - When to repeat: calibration tests after changes to code that affects
     sensor readings, safety tests after changes to the safety layer, the
     Crazyflie adapter or the tick loop, flight tests when the work needs them.
   - A vertical slice: one test environment (the living room, static while
     the drone flies) toward hide-and-seek (ADR-0016).
   - The simulator is used a lot, but it is not a required step for every
     field test: calibration and safety tests that gain nothing from a
     simulator run skip it. The same code always runs on the mock adapter
     first.
   - The README keeps a dated status brief (CLAUDE.md).
   Consequences must state the risk honestly: a test that skips the
   simulator has no simulator prediction to compare its flight against
   (focus area 5); the plan is to use the simulator wherever it adds
   something. Also record, as a risk Joe accepts knowingly: with no gate,
   a test passes once the first time through, so a lucky pass or a later
   regression is caught only when a repeat rule is followed. Joe's
   reasoning, in Joe's terms: this is a side project, not a full-time job;
   a strict suite before every flight Joe wants to do isn't practical, and
   the time is for learning, exploring and trying new things. Joe retests
   occasionally, guided by the repeat rules, without being bound by them. Origin line: "Joe's decisions,
   recorded after the fact"; list the origin under "Choices for Joe to
   confirm", since who suggested each part isn't recorded. Add the index
   row, and link the ADR from the field-testing README. Leave ADR-0010 and
   ADR-0028's "field-test stage 0" as written: they are a historical record.

Not for the cloud run (later, not urgent): a field-test list in
`docs/field-testing/` with two sections, **Hardware checks** (the `VERIFY`
notes: firmware and cflib assumptions, Bench and Hover) and **Safety tests**
(each designed failsafe tried for real, Safety validation, e.g. kill the program
mid-hover and run the rescue landing, ADR-0038).
