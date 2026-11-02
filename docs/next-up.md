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
- **The review matters most.** Before each item's commit, run
  `/project-review max fresh` on that item's uncommitted changes (`fresh`
  adds the fresh-context read, the skill's step 7). Never skip it, lower the
  level or drop `fresh`: not when the item is only partly built, not when it has
  open questions, not when its checks fail (then review it and say so in the
  pull request). Fix only plain bugs with an obvious fix, then re-run the
  checks. Every other finding (ADR conflicts, design, glossary, failure
  rules, anything that needs a decision) goes into the pull request
  description unfixed, with the full ranked findings list for each item,
  since `ReportFindings` may not show anywhere in a cloud run.
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
4. [ ] **Field-test stages become names, and hover drift is measured, not
   passed.** Joe's decisions of 2026-11-02, while drafting the first session
   logs (`docs/field-testing/sessions/YYYY-MM-DD-home-bench.md` and
   `...-home-hover.md`, already written with these changes):
   - Call the stages by name, **bench** and **hover** (the ladder's order stays
     in the README table), not "stage 0", "stage 1". Do it in
     `docs/field-testing/README.md` (stage table, session-log text),
     `docs/field-testing/session-template.md` (the `Stage:` field) and the
     comments and docstrings in `src/` and `tools/` that say "stage 0/1".
     `docs/glossary.md` also says "field-test stage 0/1" (Bench program,
     Hover test, Hover program, First flight): don't edit it, propose the
     exact before and after in the pull request.
   - The README's hover exit criterion "Lands within N cm of the takeoff
     point" goes: Joe wants the drift measured, with no pass or fail on
     distance. Reword it to "Drift over 60 s and the take-off-to-landing
     distance are measured and recorded."
   - The bench exit criteria no longer test arming (the firmware arms itself)
     or the emergency stop (no operator control exists yet, ADR-0013,
     ADR-0027). Adjust the README's bench row to match: "All sensors stream."
   - Another session may still be editing the README: re-read it first, and
     change only these lines.

Not for the cloud run (later, not urgent): a field-test list in
`docs/field-testing/` with two sections, **Hardware checks** (the `VERIFY`
notes: firmware and cflib assumptions, stages 0-1) and **Safety tests**
(each designed failsafe tried for real, stage 3, e.g. kill the program
mid-hover and run the rescue landing, ADR-0038).
