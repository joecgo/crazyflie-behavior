# Review checklist

Questions every code review asks, on top of looking for ordinary bugs: in
Claude's `/project-review` (step 6) and in my own reviews.
Each one comes from a takeaway in the [mistakes log](docs/claude-mistakes.md),
so reviews look for the kinds of mistakes Claude has made before. When a new
takeaway applies to reviews, it's added here as a question, unless the
escalation ladder in the mistakes log calls for a mechanism instead.

Each question has a question ID and ends with the mistake IDs it came from.
A new question takes the next free number; a retired one keeps its number,
struck through, with the mechanism that replaced it.

A review walks only the sections for the paths it touches:

| Touched paths | Sections to walk |
|---|---|
| `drone/crazyflie/`, `tools/` | Facts about the hardware and libraries; Fakes and the real drone; Failures; Time; Rules and records |
| `safety/`, `loop/`, `timing/`, `drone/interface.py`, `drone/telemetry_buffer.py`, `snapshot.py`, `geometry.py` | Failures; Time; Rules and records |
| `behaviors/` | Failures; Rules and records |
| `programs/` | Failures; Time; How I run things; Rules and records |
| `drone/mock_adapter.py`, test fakes | Fakes and the real drone |
| `tests/` | Rules and records (the questions about tests) |
| docs only | Rules and records |

## Facts about the hardware and libraries

- **Q-01.** Was each claim about how the firmware, cflib, Python or Windows behaves
  checked, not recalled? If a decision or safety code rests on it, its ADR
  names the file it was checked in, and the fact has a row in the facts
  register (`docs/verified-facts.md`). Docstrings and comments don't cite
  sources. (M-021, M-094, M-095, M-101, M-103, M-137)
- **Q-02.** Does a checked claim say only what its source showed? "This path fails" is
  not "every path fails" unless the other paths were checked too. (M-063, M-105)
- **Q-03.** For each library call the code relies on: what does it do on a timeout or
  an error? Is that checked in the source, including the `if` that guards the
  call (not only what the function does when it runs)? For firmware, also the
  `#ifdef` or build option around the function's body, in the build flashed.
  Can what a guard checks (the link is up) change on another thread before
  the call runs? (M-002, M-083, M-102, M-129)
- **Q-04.** A library call relied on for one step (create a log block, not start it):
  what does the library do on its own afterwards, such as when the drone's
  reply arrives? (M-139)
- **Q-05.** Windows-only code: is it checked against Windows' documented behavior, and
  is every Windows call's result checked? Continuous integration runs on
  Linux. (M-017, M-052)
- **Q-06.** For each way a flight ends (landing, failsafe, disarm, link close): which
  firmware supervisor state does the drone end in, checked in the source, and
  can it arm again without a reboot? (M-112)
- **Q-07.** Code that switches the firmware between setpoint types (a setpoint stream,
  the high-level commander): was the controller's source read for what the
  switch does (integrals restarted, base values, where a planned move
  starts), and does the code or its ADR allow for it? (M-124)
- **Q-08.** A fixed limit on an estimator's output (an uncertainty, a speed): was the
  firmware's model read for what else the output depends on (height, time
  since a reset), and does the limit hold at every height where it's checked? (M-125)

## Fakes and the real drone

- **Q-09.** For each fake (the mock adapter, a test's fake): how does the real adapter
  differ at start-up, and in the moments after each command? Are those
  moments tested? (M-023, M-065, M-120)
- **Q-10.** Can a fake loop forever? It needs a limit, so a broken test fails instead of
  hanging. (M-012)

## Failures

- **Q-11.** For each failure mode: how is it detected, how is it logged, and what
  handles it? (M-005)
- **Q-12.** For each backup: what is it computed from, and is that the thing that just
  failed? For a failsafe a check triggers, follow the failed value through
  the failsafe's own action. (M-001, M-055, M-057)
- **Q-13.** For each failure or refusal the code handles: does it stop, retry or carry
  on, and does that follow ADR-0020 (or ADR-0033, for a field test)? (M-033)
- **Q-14.** A decision made from telemetry: what does it do when the value is missing,
  old or not a number? Is that the safe choice for that decision? (M-030, M-032)
- **Q-15.** A verdict read from the drone status (landed, armed): can the run end
  during the status's lag, such as its 2 s of flying after a motor stop,
  before the verdict is recorded? (M-146)
- **Q-16.** For a check like "has it arrived?" or "is it ready?": could state left by
  an earlier run or connection satisfy it? (M-025)
- **Q-17.** Code that resets state for a new connection or run: is every field the
  constructor sets either reset or kept on purpose? Check against the field
  list, not memory. (M-073)
- **Q-18.** A flag that limits a log line to once per streak: is it cleared on every
  path that ends the streak, not only the usual one? (M-074)
- **Q-19.** For each cleanup path: what if an interruption lands between two lines (log
  lines included), or comes twice? Is everything that needs cleaning up started inside the `try`
  that cleans it up? (M-018, M-020, M-040, M-053)
- **Q-20.** A claim about what happens after a failure: is the code path read to its
  end, through the program's shutdown? (M-037)
- **Q-21.** For each error or cleanup path that closes the link: could the drone be
  flying then? cflib's `close_link()` sends a zero-thrust setpoint first,
  while its link is still open (ADR-0038; the condition was checked in the
  source on 2026-11-04). (M-058)
- **Q-22.** A claim that a failure happens on the floor: does every program that
  reaches it start on the floor? The rescue landing connects to a flying
  drone. (M-145)
- **Q-23.** A safety gap that's deferred: does an accepted ADR plan a feature that
  would open it first? (M-046)
- **Q-24.** A new safety pre-check condition: what does it do on a landed drone? A
  failed pre-check ends the flight for good (ADR-0030), so a condition that
  can fail on the floor (a drone landed in the dark) belongs in the take-off
  rule. (M-107)

## Time

- **Q-25.** A wait with a deadline: what happens just before and just after it, and
  what does a failing cleanup do to the error meant to be shown? (M-019)
- **Q-26.** A wait whose error message reads live state: does the message use the
  result of the check that timed out, not a fresh read? (M-085)
- **Q-27.** A loop: check the first tick, the last tick and the time between ticks, not
  just the middle. (M-013)
- **Q-28.** A mechanism such as the interrupt signal or a timeout: what does it do by
  default, and what does a second one do? (M-014)
- **Q-29.** A window meant to be measured or watched (a log block run at connect): is
  whatever measures it already running, given every wait before it? (M-140)

## How I run things

- **Q-30.** Controls and failure paths: do they work the way I run the program
  (PyCharm's Run window, a terminal window, the phone)? (M-008)
- **Q-31.** Logging: is it checked with a real library attached, and with the program
  started the way I start it? (M-016)

## Rules and records

- **Q-32.** "Only", "never", "always": what exactly does it apply to? If it's a rule
  about the code, is there a fitness function, and does it read at least one
  real file? Is each form its scanner handles exercised by a test? (M-007, M-022, M-072)
- **Q-33.** A decision that makes an exception to an older ADR: is the older ADR's
  status line marked? Does it take up an option an older ADR rejected, or
  go against an open backlog item on the same subject? (M-011, M-104, M-130)
- **Q-34.** Does each function do only what its name and its ADR say? Extra work in a
  query (a snapshot that moves the landing on) is a design decision: which
  ADR approved it? (M-109)
- **Q-35.** A change to what a value or term means: was the old wording searched for
  across the code, the glossary and the ADRs? (M-092, M-144, M-155)
- **Q-36.** An ADR amendment that changes how a test passes: do the test log drafts'
  pass criteria and checklists match it, and is there a test for the new rule? (M-081)
- **Q-37.** Does each test an ADR lists say what the code does at that value
  (approves, refuses, skips a check), as its branches read? (M-141)
- **Q-38.** Does every term in a new name or comment appear in the glossary, even one
  that other docs already use? Does its definition still match the code? (M-028, M-031, M-131)
- **Q-39.** A record that says a decision is built ("now runs", "already"): were its
  code and its test found, not taken from the ADR's status? (M-152)
- **Q-40.** Does each new glossary row agree with its ADR, including the risks the ADR
  accepts, and with the analysis its facts come from? (M-136)
- **Q-41.** Does a new name use a glossary term's word for something else? (M-043)
- **Q-42.** Does a name, comment or log message name a raw input (a key) where the
  code receives a signal or command? (M-035)
- **Q-43.** Does each log message's stated cause hold on every path that reaches it? (M-051, M-075, M-084)
- **Q-44.** Is every new log or console message one short sentence an operator could
  read mid-flight, with the reasons left in a comment or the ADR? Does a
  shortened message still say the outcome (failed, not confirmed, refused)? (M-091)
- **Q-45.** Does each outcome a test log needs (touchdown confirmed, motors stopped)
  log its own line, success included? A log that only speaks up on trouble
  reads as if the good outcome never happened. (M-135)
- **Q-46.** Does new wording name a milestone, quote a constant's value, or describe
  something temporary without `TODO:`? (An assumption still to check in a
  field test is marked VERIFY instead, as the Crazyflie adapter's docstring
  says. The glossary may give a specific value, but only as an example.) (source not recorded)
- **Q-47.** Is any new constant a copy of a value that follows from another one? (M-071)
- **Q-48.** Is each limit defined once, and compared the same way ("under" or "up
  to") in every check that uses it? Does each message about it say which
  side the value must be on? Does each check have a test at exactly the
  limit? (M-123, M-128)
- **Q-49.** When a change removes a wait or a check, do the comments and ADR lines
  that relied on it still hold? Is each ADR line the code leaves unbuilt
  marked, with its backlog item? (M-122)
- **Q-50.** A docstring, comment or message that describes a safety judgment: which
  way does the judgment fail when unsure, and does the wording say the same? (M-087, M-127)
- **Q-51.** Review fixes are new code: did anything review the lines a fix commit
  added, wording included? (M-087)
- **Q-52.** A tool or program whose job is one outcome (a stop, a rescue, a pass): does
  it report success only when that outcome happened, through its exit code
  as well as its message? When a record says an action "stopped" or "landed",
  does it say what observed that? A command the adapter sent is not a command
  that arrived: cflib drops packets without an error once the link is lost. (M-068, M-069, M-082)
- **Q-53.** New tests: are they proven by bug planting
  ([coding style](docs/coding-style.md))? (M-015)
- **Q-54.** Does every assert check a bool or a comparison, not an object that's
  always true (a `Verdict` rather than its `.is_approved`)? (M-201)
- **Q-55.** Does a docstring about a hand-off between two parts name the call,
  and say why its thread or timing matters? (M-207, M-208)
- **Q-56.** Does a test that compares a log line or message exactly hold fixed
  every optional part it can carry (a garbage-collector pause, a warning, a
  timing)? (M-214)

Takeaways about recommendations and explanations stay in the mistakes log
only: they're for me, when I weigh Claude's options.

## Architecture and boundary audit

Run after every refactor phase, on `git diff <phase start>..HEAD`, with
[ARCHITECTURE.md](ARCHITECTURE.md) open. Unlike the questions above, these
come from its rules, not from the mistakes log.

- **Imports.** Do the fitness functions pass (`pytest tests/architecture`)?
  Does the diff add an import that points the wrong way in ARCHITECTURE.md's
  table: cflib or a clock in a behavior, the safety layer or the tick loop;
  `safety/`, `behaviors/` or `loop/` from `drone/`; `tools/` from `src/`?
  Does a rule the phase adds have a fitness function?
- **Boundaries.** Did a signature at a boundary change (`DroneInterface`,
  `Snapshot`, the request types, `Verdict`, `Behavior.tick`, `TickStep.run`,
  `Clock`)? Was that the phase's stated job? Does a cflib object, a raw
  `dict` or an untyped value now cross one?
- **The tick.** Is its order unchanged, with the safety pre-check before
  behaviors and the take-off and landing update on every tick? Can any call
  the diff adds to a tick, a command or a cflib callback wait?
- **Safety gates.** Does every command still pass through the safety layer?
  Does every way a flight ends still land or stop, and is the link of a drone
  that may be flying still closed without cflib's `close_link()`?
- **Move-only commits.** Are the test bodies unchanged, and the cflib calls
  in the same order?
- **Scope.** Does `git diff --stat` show ARCHITECTURE.md, or a file outside
  the phase's list? Was each asked for? Does the diff build something
  ARCHITECTURE.md marks [target] before its ADR is accepted?

## My reviews

Each review covers only what's new since the one before. A path's review
tier says which review Claude runs on it:

| Tier | Paths | Claude's review |
|---|---|---|
| 1 | `safety/`, `loop/`, `drone/crazyflie/`, `drone/interface.py`, `drone/telemetry_buffer.py`, `snapshot.py`, `programs/start_up.py`, `tools/emergency_stop.py` | `/project-review` at the level CLAUDE.md asks for, with `fresh` |
| 2 | `behaviors/`, the other programs, `drone/mock_adapter.py`, `timing/`, `geometry.py`, the other scripts in `tools/` | `/project-review` at high |
| 3 | tests (test fakes included), docs | test fakes: `/project-review` at high; the rest: the path map's questions |

For a `.py` file outside `tests/` in no row, Claude asks me which tier it
goes in.

**Each review is a pull request**, read in PyCharm:

- A `reviewed` branch on GitHub marks the last reviewed commit. The first
  review creates it at `0846826`.
- Before a review, Claude commits and pushes `main`, then pushes a branch
  `review/<date>` at `main`'s last commit, runs `/project-review`, then
  `/review-packet`, on `reviewed..review/<date>`, and opens a pull request from that branch into
  `reviewed`. Its description gives the range and the review packet's path
  in `drafts/`. Claude posts each finding as a comment at its line,
  starting with "Claude:", without asking.
- Nothing is pushed to the review branch once it's open (M-049). Work,
  flights and review fixes stay on `main`, and the fixes are in the next
  review.
- My comments on the pull request are the review's record; Claude's start
  with "Claude:". When I'm done,
  it's merged with a merge commit, not squashed or rebased: those make new
  commits, so the next review's diff would show this one's changes again.
  The merge moves `reviewed` forward; then the review branch is deleted and
  the log below gets a row.

| Dates | Reviewed up to | Pull request | What |
|---|---|---|---|
| 2026-10-22 to 2026-10-27 | `b3bc274` | none | All the source then (geometry, snapshot, clock, the drone interface, telemetry buffer, mock adapter, conversions, touchdown, the Crazyflie adapter) and the tests, as a spec. Led to ADR-0018 to ADR-0021 and 20 new adapter tests |
| 2026-10-28 to 2026-11-02 | `366714a` | none | ADRs 0022 to 0033, the safety layer, the tick loop, behaviors, programs and the drone changes. Led to ADR-0033 and the non-finite-value rule in ADR-0030 |
| 2026-11-04 | `0846826` | none | Everything after `366714a`: `cd6e156` plus the five commits after it on this branch. The drone interface and snapshot, the safety layer, the Crazyflie adapter (ADR-0037, ADR-0038, ADR-0039, ADR-0045), the mock adapter and start-up, the failsafe and rescue landing programs and behaviors, the emergency stop tool, wording changes, and the tests as a spec. Led to ADR-0046, three coding-style rules, the glossary's *Stale value* and backlog #45(c) |
| 2026-11-17 | `93c8f5f`, C1 only | [#24](https://github.com/joecgo/crazyflie-behavior/pull/24), closed unmerged | C1 alone: console output on a background thread, 2 s at exit. Led to `d404629` (`_CONSOLE_LEVEL` dropped, two coding-style rules) and M-182 to M-184 |
| 2026-11-17 | `f973e8a`, ADR-0077 only | [#25](https://github.com/joecgo/crazyflie-behavior/pull/25), closed unmerged | ADR-0077 alone: the initial climb ends at a fixed 0.15 m. Led to the placeholder comment dropped from `bad_flow_zone.py` (ADR-0077 unchanged) and a glossary row for *Flow* |
| 2026-11-18 | `28cc232`, ADR-0076 and ADR-0080 only | [#26](https://github.com/joecgo/crazyflie-behavior/pull/26), closed unmerged | ADR-0076 alone (program tests on the sim clock), with ADR-0080 (their 120 s sim-time limit). No comments from Joe. The project review of ADR-0080's build left seven findings, not fixed: backlog #129. M-191 (a packet's bare "the same") |
| 2026-11-21 | `fab1d5d`, ADR-0081 only | [#27](https://github.com/joecgo/crazyflie-behavior/pull/27), closed unmerged | ADR-0081 alone (one age limit, `STALE_AFTER`). Led to `2bf62ae`: the low-light warning's (time, quality) pair became `Stamped[int]`, and `STALE_AFTER`'s placeholder comment went |
| 2026-11-21 | `edbc4a9`, ADR-0082 only | [#28](https://github.com/joecgo/crazyflie-behavior/pull/28), closed unmerged | ADR-0082 alone (the sim-time limit for every tick-loop test). No comments from Joe, and no project review ran on it |
| 2026-11-22 | `1b673f9` to `e8f7e10`, ADR-0083 and ADR-0084, then ADR-0085 and ADR-0086 | [#29](https://github.com/joecgo/crazyflie-behavior/pull/29), closed unmerged | ADR-0083 and ADR-0084 (flight ends land in the tick loop, a lost link is an error), updated during the review to include ADR-0085 and ADR-0086. Led to `4a97e68` (review fixes: `FlightEndReason`, plain names) and ADR-0086, which moved the lost-link check to `take_snapshot()`. M-207 and M-209 |
| Next | | [#30](https://github.com/joecgo/crazyflie-behavior/pull/30), open | Everything after `e8f7e10`; #30 reads `e8f7e10..fdcd31c` (the recorder and the boundary tests), 12 findings posted as comments. #24 to #29 read C1, ADR-0077, ADR-0076, ADR-0081, ADR-0082, and ADR-0083 to ADR-0086 ahead of it; their `review-base/*` branches stay so their diffs stay viewable |
