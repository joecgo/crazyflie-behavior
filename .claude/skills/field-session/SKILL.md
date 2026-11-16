---
name: field-session
description: "Starts a field-test session in the crazyflie-behavior repo: drafts the session doc and its test logs from the templates with the user's goal and pass criteria, reads how the last flight ended, settles the commit to fly, offers and runs the mock runs, gives the run buttons (the rescue landing and the emergency stop first), keeps the steps before and during the flights, and lists the data and measurements needed after, for /debrief. Use it whenever the user is about to fly the drone or plans a session (\"let's fly\", \"session 7\", \"field test today\"). It never starts a program on the drone. Argument: the session doc's path, if it exists."
---

# Field session

A session is where the design meets the drone, and where a slip costs the
most: a crash, a lost flight's data, or a result nobody can trace to its
code. Most steps here come from a session that went wrong without them. Session
5 flew with no plan written; session 6 flew with its pass criteria still open
and one flight on uncommitted code; a flight was started without reading how
the one before it ended (M-151); a flight command went out without
`--crazyflie` (M-153); and Claude's terminal tool cancelled a program before
it connected. The rules are the README's (`docs/field-testing/README.md`);
this skill puts them in the order a session needs them.

## Arguments

`/field-session [session doc]`: the session doc's path, if it's drafted.
With none, ask the user for the milestone, the session number, the tests in
order and the goal, and draft it in step 1.

## Keeping it cheap

Between flights the user is waiting with the drone on the floor. Read only
what step 8 needs: the end of the newest log, filtered to the project's own
lines, and the terminal's last lines. Analysis beyond how a flight ended
waits for `/debrief`, unless the user asks for it.

## Before the session (at the desk)

1. **The plan.** The session doc in `docs/field-testing/sessions/` and one
   test log per test in `field-tests/`, from their templates and named as
   the README's "Sessions and test logs" says, if they don't exist yet.
   - **Goal and pass criteria** are the user's, written before flying
     (README, "The iteration loop"). Read the last session's "Next session"
     and the backlog rows needed before this session's tests. Ask for the
     goal; propose pass criteria answerable with a letter, the
     recommendation marked. What the user doesn't set stays marked
     **Open**, never filled in.
   - One variable changes per session. If the plan changes two, say so.
   - The pre-flight checklist: the template's, minus what the user flies
     without (no geofence, soft landing patch or video). A line the user may
     not do, ask about rather than drop.
2. **How the last flight ended** (M-151). The newest log in `logs/` whose
   program line, near the top, says "the Crazyflie", not "the mock adapter"
   (mock runs write their logs there too). Its
   last lines from `crazyflie_behavior` loggers, not cflib's "Disconnected":
   did the tick loop stop on its own after "Touchdown confirmed", or on a
   failed safety pre-check? An abnormal end that isn't written up comes
   first.
3. **The commit to fly.** `HEAD`, with nothing uncommitted under `src/` or
   `tools/`: a result is only worth something if it traces to its code. If
   code is uncommitted, list it and ask; commit only on the user's yes, with
   the `Co-Authored-By: Claude` trailer and the noreply author
   (`CLAUDE.local.md`, "Git"). Write the hash in the session doc and each
   test log.
4. **The code review, one line.** If anything under `src/` or `tools/`
   changed between the last "Reviewed up to" in `REVIEW.md`'s review log and
   the commit to fly, say so in one line and suggest the user's code review
   (`CLAUDE.md`'s review points). It's not a gate (W10). If the user flies
   without one, the session doc's "Before the session" records it as their
   call, as session 6's does.
5. **Mock runs.** Offer them. On a yes, run each test's program with the
   PowerShell tool on the commit to fly: the command without `--crazyflie`,
   each to completion. A mock run catches a plain bug at the desk; it can't
   predict the flight (the mock adapter has no physics). Report them as mock
   results, never field results: the exit code, the tick overruns, and how
   it ended. Tick them off in the session doc's "Before the session" with
   the date. If any code changes after them, they run again.

## At the session

6. **The run buttons, up front.** Before the first flight, the two rescue
   commands, with the README's order ("If a program dies with the drone in
   the air"): the rescue landing first; if it fails with "Still missing:
   position estimate" (or "velocity estimate"), or can't bring the drone
   down, something soft under the drone, then the emergency stop.

   ```bash
   .venv\Scripts\python -m crazyflie_behavior.programs.rescue_landing --crazyflie
   ```

   ```bash
   .venv\Scripts\python tools\emergency_stop.py
   ```

   Then each test's command, built from the program's own arguments (its
   `argparse` lines or `--help`), never copied from the mock-run list
   (M-153). Every command to the drone has `--crazyflie`, is complete, and
   stands alone in a single-line `bash` block.
7. **Before each run.** The user's terminal is back at its prompt
   (`read_terminal`): a program still waiting to connect holds the radio,
   and the next one times out opening the link (session 6, 14:43). The
   checklist's lines for this flight are done. Then the user clicks the run
   button. The user starts every program on the drone: the terminal tool
   sends Ctrl-C before the link opens, so Claude never starts one.
8. **After each flight, before the next.**
   - Read the user's terminal and the end of the flight's log, as step 2
     does: how it ended, and any warning or failed pre-check.
   - Record the flight in its test log as it happens: what was run, the
     data file, and the user's result and words, marked as theirs. The
     measurements the test log asks for per flight are taken before the
     drone is moved. Analysis goes apart and is labeled as Claude's; the
     test log's observations come only from the user or the recorded data.
   - Anything the user changes between flights (a propeller, the battery,
     the light, the mark) is written down with its time: without it a
     change in the data can't be matched to a cause.
9. **After an abnormal end** (README: a crash, an unexpected landing, a
   failsafe that fired when it shouldn't have): no more flights this
   session; write it up first. If the user chooses to fly on, record that
   as their call and the risk they accepted, with the time.
10. **Code changed at the session.** Never fly uncommitted code: commit on
    the user's yes and mock-run it again. If the user flies it anyway,
    record which flights used it, as session 6's doc does.

## The data and measurements needed after

11. **Before the user packs up**, list what the debrief will need and check
    off what's in:
    - each flight's log file in `logs/`, by its time, matched to its row in
      the test log's Flights table;
    - the hand measurements each test log asks for;
    - the battery voltage at rest after the last flight;
    - the user's notes: what they saw and haven't said yet, and the result
      of each test (passed, failed or not flown) for the session doc's
      "Results", in their words.

    Then `/debrief`.

## Rules this keeps

- The user starts every program on the drone, from a run button. Mock runs
  are the only programs Claude runs.
- Observations and results come only from the user or the recorded data.
  Claude's analysis is labeled and kept apart.
- Never fly uncommitted code. No commit, push or pull request without the
  user's yes.
- It starts no work session. If this work session runs out of context
  partway through a session, `/handoff` passes on the session doc's path and
  the commands.
