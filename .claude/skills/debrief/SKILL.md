---
name: debrief
description: "Turns a field-test session's flight data into analysis in the crazyflie-behavior repo: matches each flight to its log, writes the analysis scripts in drafts/<session>/, computes every number from the whole log over the part it describes and names its script and log, draws charts with the dataviz skill on a dark theme, asks the user what the data can't tell, writes the test logs and the session doc with the user's observations kept apart from Claude's analysis, updates the field-testing README's status brief, and hands the findings that need a decision to /decide. Use it after a session's flights (\"debrief\", \"analyze the logs\", \"what did session 7 show\"), and when /field-session's last step points here. It never writes an observation or a result. Argument: the session doc's path (default: the newest)."
---

# Debrief

Field data is where a wrong number does the most harm: it goes into a test
log, and the next session's plan is built on it. The mistakes log's
*reading-field-data* entries show how it happens: a hover height taken from
one log line instead of the whole hover (M-148), an extraction cut off before
the moment it was quoted for (M-118), motor outputs compared with the thrust
command (M-156), a cause named from a log line the code never writes (M-100).
This skill puts the checks those entries ask for in the order a debrief needs
them. The README's rule holds throughout: observations and results come from
the user or the recorded data; Claude's analysis is labeled and kept apart.

## Arguments

`/debrief [session doc]`: the session doc's path. Default: the newest in
`docs/field-testing/sessions/`. Say which one before starting.

## Keeping it cheap

Logs are long, and every step re-reads the conversation.

- Start from the questions the session was flown to answer: its pass
  criteria, its predictions, the backlog rows it was planned for, and what
  the user asks. Other analysis waits; list it as a possible question.
- Scripts print compact tables (a row per flight, or per part of a flight),
  never raw samples. One question per run.
- Build on the existing helpers (`drafts/ff3/flightlog.py`'s parser,
  `drafts/ff4/ff4.py`'s `event()` and friends) rather than writing a new
  parser.
- Check `get_usage` halfway. Past about 100k tokens of Messages, `/handoff`
  with the scripts' paths and the findings done so far.

## Steps

1. **What's in.**
   - Read the session doc (its plan, pass criteria, predictions and
     "Results") and its test logs.
   - Match every flight to its log in `logs/` by time, and each log to its
     row in the test log's Flights table. A log whose program line names the
     mock adapter is a mock run, not a flight. A flight with no log, or a log
     with no flight, is asked about, not guessed.
   - What `/field-session` listed for after the flights: the hand
     measurements, the battery voltage at rest, the user's notes and each
     test's result in their words. List what's missing and ask for it. A gap
     stays marked **Open**, never filled in.
   - The commit each flight flew. Where a flight flew uncommitted code, the
     analysis says so wherever it uses that flight.
2. **The scripts.**
   - In `drafts/<session>/` (such as `drafts/ff6/`) while exploring. Never
     the scratchpad: session 6's analysis script was left in one and may be
     gone.
   - At the end of the task, ask in one choice dialog whether to commit each
     new script to `analysis/`, marking those a committed doc cites. One
     kept out is cited as `drafts/` (not in the repository) (ADR-0092).
     A committed script reads only committed recordings: commit each one it
     reads, compressed as `recordings/<name>.jsonl.gz`, in the same change.
   - Run with `.venv\Scripts\python`. Each script's docstring names what it
     computes, its logs and its time base (such as seconds from the take-off
     send, drone clock), as `drafts/ff5/ff5.py` does.
   - The parts of a flight (the initial climb, the hover, the final descent)
     are bounded by the lines the code logs at each step. A script that relies
     on a log line first checks, in the source, that the code writes it in
     every case the script covers, a mock run and a flight (M-100, M-158).
   - Where the cause of a finding can be checked by replay, replay it: the
     logged snapshots through the real code, as
     `drafts/replays/replay_touchdown.py` does (M-100).
3. **The numbers.** Every number written down names its script and its log; a
   table or section whose numbers all come from one script and log names them
   once, at its top, as `drafts/ff5/findings.md` does. Before writing one:
   - **The whole part it describes** (working rule 4): every sample of the
     hover, the climb or the descent, not a line logged at one moment of it
     (M-148); and the extraction reaches the moment it's quoted for (M-118).
   - **The same variable:** before comparing with a threshold, the plan or an
     earlier session, check it's the same logged variable (M-156).
   - **Bound or measurement:** a number from a pass/fail check is a bound, and
     says so (M-111).
   - **Margins:** a step's duration is compared with that step's time limit,
     and the margin said (M-116).
   - **Timing, not chance:** before giving a chance that a reading falls
     somewhere, list when the readings fell (M-150).
   - **Earlier sessions:** before linking a finding to one, check that the
     code it flew had the feature (M-117); compare only numbers already
     checked (M-118).
   - **Predictions:** each prediction in the session doc gets its number from
     the data: met, missed or not tested.

   Before calling something a cause: the log holds the data that shows it,
   or it's a likely cause (M-114); a missing log line shows nothing until the
   code is checked to log that outcome (M-100); a reading is a cause only
   after a case where it differs, and a hypothesis until then (M-096).
4. **Charts.** Only for a finding a table can't show: drift over time, noise
   by surface, a sim-vs-real overlay, one part of the flight across flights.
   Use the `dataviz` skill, on a dark theme (the black surface of
   `drafts/ff3/charts.py`'s `CHART_THEME=black`). The SVG goes in
   `docs/field-testing/field-tests/figures/`, named
   `YYYY-MM-DD-<milestone>-<session#>-<what>.svg` like the ones there; the
   script that draws it goes with the others. Render it and look before
   linking it.
5. **Questions for the user.** What the data can't tell: what they saw, what
   they changed between flights and when, and any number of theirs the data
   disagrees with. Where an observation and the data differ, both are
   written down side by side, and the difference is a question. Make each
   answerable with a letter or a word where possible: the user often answers
   from a phone.
6. **The test logs and the session doc**, in `docs/field-testing/`. Nothing is
   committed until the user says so.
   - **Flights table:** what was run, the log file, and the user's result and
     notes, marked as theirs.
   - **Observations:** only the user's words, marked as theirs, and numbers
     computed from the data.
   - **Analysis:** under its own heading, "(analysis, Claude, <date>)", as
     session 6's doc does: each finding with its numbers and how sure it is.
   - **Sim vs real:** only if a simulator run was made; otherwise the section
     goes, as the template says.
   - **Next:** the code, simulator and ADR changes the findings point to,
     and the next session's goal as a question for the user. A pass criterion
     proposed for it takes each value's limit from the code (M-097) and names
     the quantity that matters, not a sign that went with it once (M-098).
   - **The session doc's "Results":** the user's words only, per test:
     passed, failed or not flown. Claude never writes a result.
   - Then read every analysis line back against its heading and its log
     (M-157).
7. **Findings that need a decision.** A finding that would change the code,
   the simulator or an ADR is an open question: add it to
   `docs/decision-backlog.md` (one writer at a time), then offer each to
   `/decide`, one at a time. A finding that goes against an accepted ADR says
   so, with its number. Nothing is decided here.
8. **The README's status brief.** `docs/field-testing/README.md` opens with a
   status brief and its last-updated date. Add the session in a few lines
   (what was flown, the results in the user's words, the main findings with
   their links) and update the date. Show the user the new lines.

## Rules this keeps

- Observations and results come only from the user or the recorded data.
  Claude's analysis is labeled and kept apart.
- Every number names its script and its log, and comes from the whole log
  over the part it describes.
- It decides nothing: open questions go to the backlog and `/decide`.
- No commit, push or pull request without the user's yes. It starts no work
  session; `/handoff` passes on unfinished analysis.
