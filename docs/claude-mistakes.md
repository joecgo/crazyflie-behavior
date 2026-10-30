# Claude's mistakes

The implementation and many of the options in this project are AI-assisted
(Claude Code). This log records Claude's mistakes so I can see what kind of
work it finds hard: where to focus my own learning, where to double-check
Claude, and where a new skill for Claude might help.

Two sections, newest first in each:
- **Mistakes I had to point out.** Each says whether a later Claude review
  would probably have caught it anyway.
- **Mistakes Claude caught itself**, at a later step (a code review, planting
  bugs to prove the tests, or while writing the code).

Takeaways that apply to code reviews also become questions in the
[review checklist](../REVIEW.md).

**Kinds of work:** *design* (how parts fit together), *safety design*,
*recommendation* (which option Claude pushed and why), *environment*
(assumptions about my machine, time zone or tools), *testing*, *process* (how
decisions are recorded), *communication* (how Claude explains things).

## At a glance

| Kind | I pointed it out | Claude caught it later |
|---|---|---|
| design | 2 | 6 |
| safety design | 2 | 2 |
| recommendation | 3 | 0 |
| environment | 2 | 1 |
| communication | 1 | 0 |
| testing | 0 | 3 |
| process | 0 | 1 |
| **Total** | **10** | **13** |

Of the 10 I pointed out, a later Claude review would probably have caught
none, maybe 4, and probably not 6. So far, every recommendation and
communication mistake needed me. Claude's own reviews, planted bugs and
source checks find mistakes in code, tests and records, including Windows
details and a firmware claim that two ADRs rested on. A repeating
pattern: an interruption landing between two lines of cleanup code (three
times so far).

---

## Mistakes I had to point out

### 2026-10-29: A logging recommendation that ignored what was already known

- **What happened:** for backlog #27, Claude recommended writing log messages
  on background threads. Both options were on the table, but the
  recommendation didn't weigh two things Claude already knew: I run programs
  in PyCharm, where the console freeze doesn't happen (Claude had written
  that into backlog #27 itself), and the project measures first before adding
  complexity, as with the garbage collector and spin-waiting (ADR-0024).
- **Why it was wrong:** it recommended more code and moving parts against an
  unmeasured risk, and an option that loses the last log lines when the
  program is killed. My SSD was new information; the rest wasn't.
- **How I caught it:** I asked why the simpler option wasn't recommended.
- **Would a Claude review have caught it?** Probably not: it was a
  recommendation.
- **Kind:** recommendation.
- **Takeaway:** when Claude recommends the more complex option, ask whether
  the risk has been measured, and how the project handled similar risks.

### 2026-10-29: Stretched UE analogies

- **What happened:** Claude kept offering UE analogies even where none really
  fit, such as a frozen console for the drone lock, or a "player is dead"
  flag for the kill latch.
- **Why it was wrong:** a stretched analogy can mislead more than it helps.
- **How I caught it:** the analogies read as forced.
- **Would a Claude review have caught it?** Probably not: reviews check code,
  not explanations.
- **Kind:** communication.
- **Takeaway:** when no UE analogy fits, say so. The glossary now says "No UE
  analogy" for those terms.

### 2026-10-29: A stop control designed for a terminal, not for PyCharm

- **What happened:** Claude designed stopping around Ctrl+C, the terminal
  convention, without checking how I run programs. CLAUDE.md says PyCharm:
  in its Run window, Ctrl+C copies text, and the Stop button may end the
  program outright, skipping the landing.
- **How I caught it:** I asked whether Ctrl+C could be pressed by accident
  while copying, and Claude found the PyCharm gap while answering.
- **Would a Claude review have caught it?** Maybe: a review of the start-up
  code against CLAUDE.md's Environment section could have, but no code existed
  yet.
- **Kind:** environment.
- **Takeaway:** for any control or failure path, ask how I actually run the
  program: PyCharm, a terminal window, or the phone.

### 2026-10-29: Only one command request per tick

- **What happened:** in the new safety-layer request design, Claude said only
  one command request could be sent per tick.
- **Why it was wrong:** that's true for movement (one velocity at a time), but
  Claude applied it to every command. A buzzer chirp or an LED change can go
  out in the same tick as a movement. The fix: command slots, one request per
  slot per tick.
- **How I caught it:** I asked why a buzzer command couldn't go with a move.
- **Would a Claude review have caught it?** Probably not: the limit would have
  been built into the design, and reviews check code against the design.
- **Kind:** design. A constraint generalized beyond where it applies.
- **Takeaway:** when Claude states a limit ("only one", "never", "always"),
  ask what it applies to.

### 2026-10-29: Holding back measurements because of an undecided item

- **What happened:** Claude recommended keeping each tick's timing
  measurements in memory and logging only a summary, because where flight
  data is saved (backlog #11) wasn't decided.
- **Why it was wrong:** a pending decision shouldn't shape the code. Logging
  each tick immediately gives context around any error, and where the log
  goes is set separately at startup.
- **How I caught it:** the reason didn't hold up when I asked about it.
- **Would a Claude review have caught it?** Probably not: it was a
  recommendation, and the code would have followed it.
- **Kind:** recommendation.
- **Takeaway:** when a recommendation's reason is "that's not decided yet",
  ask whether the decision can be made now instead.

### 2026-10-29: A hang can't be detected

- **What happened:** Claude wrote that the tick loop can't interrupt a hung
  tick, and only discussed acting on a hang. It missed that detecting one is
  cheap and standard (a watchdog, like UE's hang detector; Python has
  `faulthandler.dump_traceback_later`). Its overrun warning only fires when a
  tick ends, and a hung tick never ends.
- **How I caught it:** I asked how UE detects a hang.
- **Would a Claude review have caught it?** Maybe: the tick loop's review
  checked what the hang watchdog covers, but only once there was one.
- **Kind:** safety design. A missed option.
- **Takeaway:** for every failure mode, ask separately how it's detected,
  logged and handled.

### 2026-10-27: Dates in the wrong time zone

- **What happened:** the cloud session's clock runs on UTC, so the work log,
  ADR-0022 to 0024 and backlog #26 were dated the next day.
- **How I caught it:** the work log showed tomorrow's date.
- **Would a Claude review have caught it?** Probably not: nothing in a diff
  shows which time zone a date is in.
- **Kind:** environment. Claude assumed the machine's clock matched my time
  zone.
- **Takeaway:** CLAUDE.md now says dates use Pacific time.

### 2026-10-27: Waiting for the next slot after an overrun

- **What happened:** for tick timing, Claude first recommended that after an
  overrun the loop wait for the next 50 ms slot.
- **Why it was wrong:** after a long tick, waiting up to another 50 ms makes
  the drone slower to respond, for no benefit. My version: start the next
  tick at once ([ADR-0024](decisions/0024-tick-timing-strategy.md)).
- **How I caught it:** comparing it with a game loop.
- **Would a Claude review have caught it?** Probably not: it was a
  recommendation, judged against game-loop experience.
- **Kind:** recommendation.
- **Takeaway:** check Claude's timing recommendations against how game loops
  already solve the problem.

### 2026-10-24: Trusting a cflib read that returns old data on a timeout

- **What happened:** the Crazyflie adapter Claude wrote polled drone status
  with cflib's `read_bitfield()` and stamped every result as fresh. On a
  timeout, that call doesn't raise: it returns the last value, or 0 if it
  never had one. A stale status looked current, and a missing one read as
  "all flags false".
- **How I caught it:** in my code review. Fixed by streaming status instead
  ([ADR-0021](decisions/0021-drone-status-streams-with-the-state.md)).
- **Would a Claude review have caught it?** Maybe: a review that reads the
  library's source for each call the code relies on could have.
- **Kind:** design. Assumed a library call fails loudly without checking its
  source.
- **Takeaway:** for every library call Claude relies on, ask what it does on a
  timeout or error, and check the answer in the source.

### 2026-10-24: A backup that fails together with what it backs up

- **What happened:** Claude recommended letting the position estimate's
  height confirm touchdown when the down range had nothing usable
  ([ADR-0012](decisions/0012-landing-confirms-touchdown.md)). On a Crazyflie
  that height comes mostly from the same down sensor, so when the sensor
  fails, the backup fails too, and the motors could be cut in mid-air.
- **How I caught it:** in my code review. Fixed by
  [ADR-0019](decisions/0019-final-descent-when-touchdown-unconfirmed.md).
- **Would a Claude review have caught it?** Maybe: the failure-mode checks
  every safety ADR now has ask exactly this, but they came afterwards.
- **Kind:** safety design. A backup sharing the primary's failure.
- **Takeaway:** for every backup, ask what it's computed from, and whether
  that's the same thing that just failed.

---

## Mistakes Claude caught itself

### 2026-10-30: A safety pre-check that only passed with the mock adapter

- **What happened:** the safety pre-check counts a missing value as a
  failure, and a failure ends the flight. The mock adapter writes every value
  the moment it connects, so every test passed. The Crazyflie adapter returns
  from `connect()` before any value has arrived, so on the real drone the
  hover program would have ended at its first tick without flying. And in the
  few ticks after a take-off is sent, before the drone status says flying,
  the failsafe's log line claimed the drone "stays down".
- **Caught at:** Claude's code review, at a high level. Not fixed yet:
  backlog #32 and #31.
- **Kind:** design. Tested against a fake that's kinder than the real thing.
- **Takeaway:** for every fake, ask how the real adapter differs at start-up
  and in the moments after each command, and test those moments too.

### 2026-10-30: Rules stated in code that no fitness function checked

- **What happened:** the command request module said "behaviors import this
  module, never the safety layer itself", and ADR-0008 says only the safety
  layer sends commands, but no fitness function checked either. The behavior
  import rules had also been checking an empty folder: `behaviors/` didn't
  exist until now, so they couldn't fail.
- **Caught at:** Claude's code review (the first), then while writing the
  hover test (the second). Both are fitness functions now, with a check that
  they see real files.
- **Kind:** testing.
- **Takeaway:** when code says "never" or "only", write the fitness function
  in the same commit, and make sure it reads at least one real file.

### 2026-10-30: Two ADRs built on an unchecked firmware claim

- **What happened:** ADR-0012 starts from "after the high-level commander
  lands, the motors keep running until the adapter stops them". Claude wrote
  that without checking the firmware, which does the opposite: when a landing
  trajectory ends, the high-level commander goes idle and asks for the motors
  off (the same in releases 2022.01, 2023.02 and 2025.02, and today's
  source). So the motors stop when the planned landing time is up, whether
  touchdown is confirmed or not. And the final descent (ADR-0019), sent
  after an unconfirmed touchdown, would start the motors again, even with the
  drone already on the floor. The Crazyflie adapter's landing code rests on
  both ADRs. The same day, Claude's first guess at another firmware rule
  (that a land command on the floor is ignored) was wrong too, but checking
  the source first caught it before any code was written.
- **Caught at:** checking the firmware source while building the safety
  layer's failsafe (ADR-0030), 10 days after ADR-0012. Not fixed yet:
  backlog #31.
- **Kind:** safety design. A claim about the hardware from memory, not from
  the source.
- **Takeaway:** when an ADR says how the firmware or a library behaves, ask
  which file it was checked in. The firmware source is public; a claim
  without a file name is a guess.

### 2026-10-30: The same gap between two lines, again

- **What happened:** the time-limit helper started its thread one line
  before the `try` that cleans up. A Ctrl+C at that moment skipped the
  cleanup, so a connection under way wasn't stopped. It's the same pattern
  as "Cleanup gaps around connecting", the day before.
- **Caught at:** bug planting: the Ctrl+C tests failed in about one run in
  two, and the failures led to the gap. A test now injects the Ctrl+C at
  exactly that moment.
- **Kind:** design. Windows of time between two steps.
- **Takeaway:** start anything that needs cleaning up inside the `try` that
  cleans it up. A test that fails only sometimes is a clue, not noise.

### 2026-10-30: Edge cases in the connect time limits

- **What happened:** in the first version, a step that finished in the last
  wait slice still counted as a timeout; an error in the cleanup could hide
  the time-limit message naming the step; a late error was logged without
  its traceback; and ADR-0029 claimed Ctrl+C gets through within 0.1 s,
  although closing the link takes a second or two more.
- **Caught at:** Claude's code review.
- **Kind:** design.
- **Takeaway:** for a wait with a deadline, check both edges: just before
  and just after the deadline, and what a failing cleanup does to the error
  you meant to show.

### 2026-10-29: Cleanup gaps around connecting

- **What happened:** in the start-up code's first draft, a Ctrl+C in the
  instant between connecting and installing the Ctrl+C handler would have
  skipped the disconnect. Then a Ctrl+C during cflib's `open_link` left a
  half-open link the adapter didn't track, and a second press could cut the
  cleanup short.
- **Caught at:** writing the code (the first), then Claude's code review.
- **Kind:** design. Windows of time between two steps.
- **Takeaway:** for every cleanup path, check what happens if the
  interruption lands between two lines, and if it comes twice.

### 2026-10-29: Windows details in the start-up code

- **What happened:** the docs promised that Ctrl+C stops the program at once
  while connecting, but on Windows, Python 3.12 can't interrupt cflib's waits,
  which have no time limit (backlog #29, solved by ADR-0029). The QuickEdit code also restored the
  console mode in a form Windows can ignore, and let ctypes cut a 64-bit
  handle to 32 bits.
- **Caught at:** Claude's code review.
- **Kind:** environment. Code that was only run on Linux.
- **Takeaway:** for Windows-only code, ask the review to check it against
  Windows' documented behavior, since continuous integration runs on Linux.

### 2026-10-29: Debug logging for every library, and a logger named `__main__`

- **What happened:** the logging setup turned on debug level for every
  logger, so cflib would log every radio packet. And run as a program, the
  bench program's logger is called `__main__`, outside the project's loggers,
  so its debug lines would have been dropped once that was fixed.
- **Caught at:** Claude's code review (the first), then while fixing it.
- **Kind:** design.
- **Takeaway:** check logging setups with a real library attached and the
  program started the way I start it.

### 2026-10-29: Tests that couldn't fail cleanly

- **What happened:** when a planted bug made Ctrl+C raise an error, it
  escaped the test and stopped the whole pytest run instead of failing one
  test. The QuickEdit test's example console mode already had the bit the
  planted bug removed, so it couldn't fail at all. An end-to-end test relied
  on a 0.5 s timer.
- **Caught at:** planting bugs (the first two), then Claude's code review.
- **Kind:** testing.
- **Takeaway:** for each test, plant the bug it's meant to catch, and check
  that it fails, fails alone, and doesn't depend on timing.

### 2026-10-29: Ctrl+C described two ways in one ADR

- **What happened:** ADR-0026's decision calls Ctrl+C a stop request (finish
  the tick, then land). Its failure modes say Ctrl+C anywhere in a tick rises
  like an error. Python's default is the second; the first needs a handler.
  Neither said what a second press during the landing does: with Python's
  default, it cuts the landing short, and the Crazyflie adapter's link
  shutdown then sends zero thrust, which drops the drone.
- **Caught at:** writing the tick loop. Fixed: Ctrl+C is a stop request, and
  later presses are ignored (ADR-0026).
- **Kind:** safety design. An ADR's words didn't match what the language
  does by default.
- **Takeaway:** when an ADR names a mechanism (Ctrl+C, a timeout), ask what
  happens by default, and what a second one does.

### 2026-10-29: Gaps at the edges of the tick loop

- **What happened:** in the tick loop's first draft, the last tick's overrun
  went unlogged ("done" returned before the check); the hang watchdog stopped
  before the tick's logging, so a blocked console wouldn't be reported; the
  watchdog fell back to standard error, though ADR-0026 says the log file;
  and a stop request waited up to one tick period.
- **Caught at:** Claude's code review, at a high level.
- **Kind:** design. Edge cases at the start, end and between ticks.
- **Takeaway:** when reviewing a loop, check the first tick, the last tick
  and the time between ticks, not just the middle.

### 2026-10-29: Test fakes that hang instead of failing

- **What happened:** two fake tick steps never reported done. When a planted
  bug broke the stop request, their tests hung forever instead of failing.
- **Caught at:** planting bugs to prove the tests.
- **Kind:** testing.
- **Takeaway:** a fake that can loop needs a limit. Plant a bug in each path
  and check the test fails, not hangs.

### 2026-10-29: An exception to an older ADR without marking it

- **What happened:** Claude added "every overrun gets its own warning" to
  ADR-0026, an exception to ADR-0020's once-per-streak rule, without marking
  ADR-0020 as amended or updating ADR-0026's origin line.
- **Caught at:** Claude's code review.
- **Kind:** process.
- **Takeaway:** when a decision makes an exception to an older one, mark the
  older ADR's status line.
