# Claude's mistakes

The implementation and many of the options in this project are AI-assisted
(Claude Code). This log records Claude's mistakes so I can see what kind of
work it finds hard: where to focus my own learning, where to double-check
Claude, and where a new skill for Claude might help.

A mistake is something wrong by what was known or written down at the time.
A recommendation I decide against, or a rule I change later, isn't one.

Two sections, newest first in each:
- **Mistakes I had to point out.** Each says whether a later Claude review
  would probably have caught it anyway.
- **Mistakes Claude caught itself**, at a later step (a code review, planting
  bugs to prove the tests, or while writing the code).

Takeaways that apply to code reviews also become questions in the
[review checklist](../REVIEW.md).

**Kinds of work:** *design* (how parts fit together), *safety design*,
*recommendation* (an option Claude pushed on a false fact, a missed
constraint, or no real reason), *environment*
(assumptions about my machine, time zone or tools), *testing*, *process* (how
decisions are recorded), *communication* (how Claude explains things).

## At a glance

| Kind | I pointed it out | Claude caught it later |
|---|---|---|
| design | 3 | 12 |
| safety design | 3 | 12 |
| recommendation | 7 | 3 |
| environment | 3 | 5 |
| communication | 5 | 6 |
| testing | 0 | 6 |
| process | 1 | 8 |
| **Total** | **22** | **52** |

Of the 22 I pointed out, a later Claude review would probably have caught
none, maybe 6, and probably not 16. So far, 7 of the 10 recommendation
mistakes needed me, and 5 of the 9 communication mistakes. Claude's own reviews, planted bugs and
source checks find mistakes in code, tests and records, including Windows
details and a firmware claim that two ADRs rested on. A repeating
pattern: an interruption landing between two lines of cleanup code (five
times so far).

---

## Mistakes I had to point out

### 2026-11-02: Follow-up commits pushed to a pull request already merged

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
- **Takeaway:** before pushing to a pull request's branch or editing its
  description, check that it's still open.

### 2026-11-02: "Nothing is scheduled" said without checking

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
- **Takeaway:** before saying something does or doesn't exist (a schedule,
  a session, a file), look it up, and read the file the question is about.

### 2026-11-02: Options offered that didn't fix the problem

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
- **Takeaway:** check each option against the problem before listing it. If
  only one option fixes it, say so instead of inventing alternatives.

### 2026-11-01: A gap described without reading the code that closes it

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
- **Takeaway:** before describing what happens after a failure, read the
  code path to its end, including the program's shutdown.

### 2026-11-01: A backlog item written and dropped without checking or measuring

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
- **Takeaway:** before writing or dropping a backlog item, check the ADRs on
  the same question, and measure a performance risk before calling it small.

### 2026-11-01: A key named where the code handles a signal

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
- **Takeaway:** name what the code receives (a signal, a command), not the
  raw input that usually sends it; only instructions for the operator name
  the key. The glossary now has *Interrupt signal*, and the coding style has
  the rule.

### 2026-11-01: A local named for when it was fetched, not what it holds

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
- **Takeaway:** the naming rule applies to local variables too. The coding
  style now says so, with `latest` as the example.

### 2026-11-01: A behavior's failure rule chosen without asking

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
- **Takeaway:** a rule for what code does on a failure (stop, retry or carry
  on) is a decision: check it against ADR-0020 and ask.

### 2026-10-31: A quiz instead of an answer

- **What happened:** I asked Claude where a backlog #8 decision from my other
  session overlapped the review. Claude saw that one of its claims (a failed
  pre-check right after take-off lets the take-off continue to 0.5 m) doesn't
  match the code. Instead of saying why, it treated the claim as if it were
  my explain-back answer, gave me a hint, and asked a second question in the
  same reply. I couldn't tell what it was asking.
- **Why it was wrong:** I had asked for the overlaps, to pass them on, and an
  ADR was about to record the wrong reason. Explain-back questions check my
  understanding after an explanation; they aren't a reason to hold back an
  answer I asked for. Two questions in one reply also left it unclear which
  to answer.
- **How I caught it:** I said I didn't understand what Claude was asking.
- **Would a Claude review have caught it?** Probably not: reviews check code
  and records, not conversations.
- **Kind:** communication.
- **Takeaway:** when I ask for information, give it directly. Ask
  explain-back questions only about what Claude explained, and one question
  at a time.

### 2026-10-31: Unclear docstrings that lean on terms not in the glossary

- **What happened:** two docstrings in the safety package confused me in one
  review. `safety/requests.py` said "First flight approves arm, take off,
  hover and land", as if the milestone approved requests, when the safety
  layer does. `safety/safety_layer.py` said the operator's "land now" and
  "hover" "join the pre-check with the operator controls, not built yet",
  which doesn't say what joins what, or when. None of the terms had a
  glossary entry: *First flight* was defined only in the work log, *operator
  controls* only in ADR-0027, and *operator* is used in the glossary but
  never defined.
- **Why it was wrong:** a code comment should make sense to someone who
  knows only the code and the glossary, and CLAUDE.md says names and
  comments use glossary terms.
- **How I caught it:** in my second code review, I asked what each sentence
  meant.
- **Would a Claude review have caught it?** Probably not: Claude's own
  high-level `/code-review` had already passed both files, and the review
  checklist had no question about terms outside the glossary.
- **Kind:** communication.
- **Takeaway:** a term used in code needs a glossary entry, even one the docs
  already use, and a note about unbuilt work says plainly what will change.
  The glossary now has *First flight* (in a new Milestones section),
  *operator* and *operator controls*, and the review checklist asks about
  glossary terms.

### 2026-10-31: Recommending against accepted ADRs for vague reasons

- **What happened:** for backlog #31 (landing), Claude recommended trusting
  the firmware's landing (option A), which gives up ADR-0012's guarantee and
  retires ADR-0019's final descent, over landing with a `go_to` so the
  touchdown check stops the motors (option B), which is what those ADRs
  intended. Its reasons were vague or wrong: "B relies on behavior nobody has
  tested", when nothing in the project has run on hardware yet and B's only
  new physical moment is about 0.3 s more at the floor with the motors
  running; and "more code", when B's landing code already exists. The cloud
  session leaned towards A first, and Claude repeated it without checking.
- **Would a later Claude review have caught it?** Probably not: reviews look
  at code and records, not at the reasons behind a recommendation.
- **Kind:** recommendation.
- **Takeaway:** when accepted ADRs already answer a question, keeping them is
  the default. Recommending a change needs a concrete reason, and "untested"
  must say exactly what is untested and why it matters.

### 2026-10-31: An option with no reason to choose it

- **What happened:** for backlog #31, Claude listed option C (descend to
  10 cm, confirm, then stop the motors), copied from the backlog's options to
  explore, without saying why anyone would pick it. Its only conceivable
  advantage, less time on the floor with the motors running, is none: the
  firmware's own landing reaches the floor with the motors running too, and
  B's extra time there is the 0.3 s touchdown hold. C also cuts the motors in
  mid-air on purpose, which ADR-0019 exists to prevent.
- **Would a later Claude review have caught it?** Probably not, for the same
  reason.
- **Kind:** recommendation.
- **Takeaway:** give every option the reason someone would choose it. An
  option with none is dropped, not listed.

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

### 2026-11-03: Docstrings that a change left behind

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
- **Takeaway:** when a decision changes what a function does, search for
  every docstring that describes it, the interface's included, and fix a
  claim everywhere it was copied, not only where it was found.

### 2026-11-03: An emergency stop that said "not delivered" when it may have been

- **What happened:** `tools/emergency_stop.py` printed "the radio did not
  deliver the emergency stop" whenever the stop wasn't confirmed, also when
  the radio took every packet and only reported a link error on the way.
- **Caught at:** the second end-of-run review of pull request #8.
- **Kind:** communication.
- **Takeaway:** a failure message names every way to reach it (REVIEW.md:
  the stated cause holds on every path).

### 2026-11-03: A once-per-streak log line whose streak never ended

- **What happened:** the adapter's "Hover ignored" line (ADR-0039) was
  limited to once per streak, but the flag was cleared only by `connect()`
  and `take_off()`, not by a hover that went through. After the first
  ignored hover, a taken-over flight, which never sends a take-off, would
  never log another.
- **Caught at:** the second end-of-run review of pull request #8, reproduced
  with a script.
- **Kind:** design.
- **Takeaway:** a once-per-streak flag is cleared on every path that ends
  the streak (now a REVIEW.md question).

### 2026-11-03: A new connection that kept the last one's landing

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
- **Takeaway:** state reset for a new connection is checked against the
  constructor's field list (now a REVIEW.md question).

### 2026-11-03: Fitness functions with blind spots

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
- **Takeaway:** a fitness function's scanner gets a test for each form it
  handles, on a made-up file; every structural "only" in a new ADR gets its
  fitness function in the same change.

### 2026-11-03: Two constants that must agree, with no test between them

- **What happened:** the failsafe test's `FAULT_TIME_LIMIT` (10 s) must
  exceed the wrapper's `HOVER_DURATION_BEFORE_FAULT` (3 s), or the test
  lands before the fault is injected. Nothing related them, and two
  docstrings copied "3 s".
- **Caught at:** the first end-of-run review of pull request #8, fixed after
  the second.
- **Kind:** testing.
- **Takeaway:** when one placeholder only works relative to another, a test
  says so, and the docstrings point to the constant instead of copying it.

### 2026-11-03: A taken-over flight given the take-off grace period

- **What happened:** taking over a flight (ADR-0038) started the 1 s take-off
  grace period without reading the status, so a rescue run on an armed
  drone already on the floor would send a floor-height `go_to` (ADR-0039's
  "Never").
- **Caught at:** the first end-of-run review of pull request #8.
- **Kind:** safety design.
- **Takeaway:** a new way into a state ("as if we had sent the take-off")
  is checked against every rule that state's usual entry carries.

### 2026-11-03: An emergency stop that said "Sent." when nothing was

- **What happened:** `tools/emergency_stop.py` ignored `send_packet()`'s
  result and printed "Sent." after about 38 s of silence when nothing
  reached the drone (reproduced against cflib's real `RadioDriver`).
- **Caught at:** the first end-of-run review of pull request #8.
- **Kind:** safety design.
- **Takeaway:** a tool whose job is one outcome reports success only when
  that outcome happened (now a REVIEW.md question).

### 2026-11-03: A rescue landing that exited 0 when the rescue failed

- **What happened:** the rescue landing program returned exit code 0 after
  a refused landing or its time limit.
- **Caught at:** the first end-of-run review of pull request #8.
- **Kind:** design.
- **Takeaway:** the same as the emergency stop's: the exit code is part of
  the report.

### 2026-11-03: A mitigation in ADR-0044 that the code didn't provide

- **What happened:** ADR-0044 said "nothing in our code sends it a
  setpoint" during the Bench, but `disconnect()` on a drone on the floor
  makes cflib send a zero-thrust setpoint, and `connect()` resets the
  estimate.
- **Caught at:** the first end-of-run review of pull request #8.
- **Kind:** safety design.
- **Takeaway:** a safety claim in an ADR is checked against the code path
  it describes, end to end, before it's recorded.

### 2026-11-03: ADR-0043 described the old field-testing README wrongly

- **What happened:** ADR-0043 said the old README's gate and simulator rule
  were different from what it said (the gate belonged to each stage; the
  simulator was required except for Bench and Hover).
- **Caught at:** the first end-of-run review of pull request #8.
- **Kind:** process.
- **Takeaway:** when an ADR describes what it replaces, quote or re-read
  the old text rather than summarizing it from memory.

### 2026-11-03: A test fake that streamed only once

- **What happened:** the first `FakeCflib` sent each log block's sample once,
  but `connect()` swaps the telemetry buffer after the estimate reset and
  relies on the drone streaming on, so the fake couldn't model it.
- **Caught at:** while building it.
- **Kind:** testing.
- **Takeaway:** REVIEW.md's "how does the real adapter differ from the
  fake?" applies to timing too: a real drone keeps streaming.

### 2026-11-03: New vocabulary in code names before proposing it

- **What happened:** the unattended run named code with terms the glossary
  lacks (Failsafe test, Forged low battery drone, Take over, Streak, and
  others), then proposed them in the pull request afterwards.
- **Why it was wrong:** CLAUDE.md says to propose a term before introducing
  it in code.
- **Caught at:** the first end-of-run review of pull request #8.
- **Kind:** process.
- **Takeaway:** in an unattended run, propose the term in the pull request
  and use a plain description in code until it's accepted, or record the
  name as a choice for Joe to confirm before using it.


### 2026-11-02: A work-log row raised without its total

- **What happened:** the work-log commit for ADR-0040 and ADR-0042 raised the
  2026-11-02 row from ~2.5 to ~3 hours but left the milestone total at
  ~36.75; the rows summed to ~37.25.
- **Caught at:** adding the next row to the same day, by summing the rows
  with a script.
- **Kind:** process.
- **Takeaway:** when a work-log row's hours change, recompute the milestone
  total from the rows, not by adding the change to the old total.

### 2026-11-02: A tick period quoted from memory

- **What happened:** explaining the negative-ages options, Claude gave one
  tick period as 20 ms at 50 Hz.
- **Why it was wrong:** the tick loop runs at 20 Hz (`TICK_RATE`), so a tick
  is 50 ms.
- **Caught at:** looking up `TICK_RATE` while writing ADR-0042, before it was
  recorded.
- **Kind:** communication.
- **Takeaway:** look up project constants before quoting them, even in
  conversation.

### 2026-11-02: A watchdog recommended that the backlog already ruled out

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
- **Takeaway:** before proposing options, search the backlog and ADRs for the
  same problem; an earlier finding may already rule an option out.

### 2026-11-02: A refusal that drops the drone it protects

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
- **Takeaway:** for a new failure path, follow it through its cleanup, and
  check what that cleanup sends to a drone that may be flying.

### 2026-11-02: Manual arming called a barrier that doesn't rely on our code

- **What happened:** for backlog #37, Claude said manual arming (our own
  firmware build) gives hide-and-seek "a second barrier that doesn't rely on
  our code staying correct".
- **Why it was wrong:** the arm request comes from our code too. A bug that
  sends an arm request and then a flight command still spins the motors. It
  is a second step a bug must hit, not a barrier independent of our code.
- **Caught at:** explaining the claim when I asked what it meant.
- **Kind:** safety design.
- **Takeaway:** before calling a backup independent, name what triggers it
  and check that the primary's failure can't trigger it too.

### 2026-11-02: A pushed commit that doesn't pass its own tests

- **What happened:** the review's work was committed by topic, but
  `878c16f` uses `Vector3.is_finite()` and a renamed safety-layer property
  that only arrive in the next commit, so it fails 25 tests on its own. The
  tests ran only before the first commit, and Claude's brief for the commit
  session asked for nothing more.
- **Caught at:** running the tests at each commit after they were made, but
  the commits had been pushed by then. I left the history as it is: the
  commits before and after it pass.
- **Kind:** process.
- **Takeaway:** commit in dependency order and run the tests at every commit
  before pushing, so any commit can be rolled back to.

### 2026-11-02: A failsafe whose landing used the value that failed it

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
- **Takeaway:** when a check sends a bad value into a failsafe, follow that
  value through the failsafe in the same change. The review checklist
  already asked; the check was skipped while recommending.

### 2026-11-02: Wording in the NaN change that missed the project's rules

- **What happened:** in the same change, `Verdict`'s new check packed two
  rules into one comparison, although `judge()` had just moved to plain `if`
  statements; `Behavior.tick`'s docstring still promised only "present and
  fresh"; and a comment restated ADR-0030's rule without pointing to it, as
  the coding style asks.
- **Caught at:** the same review.
- **Kind:** communication.
- **Takeaway:** a new rule also changes the docstrings that promise what
  callers can rely on; check them in the same change.

### 2026-11-02: The gap between two lines, a fifth time

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
- **Takeaway:** log lines are lines too: keep a signal handler in place until
  the last line it protects, and log inside the `try`.

### 2026-11-02: A Windows call whose failure went unnoticed

- **What happened:** `quick_edit_off` ignored what `SetConsoleMode` returned.
  If turning QuickEdit off failed, the log still said it was off, and
  selecting text could pause a tick with no warning. A failed restore went
  unnoticed too.
- **Caught at:** the same review. Both calls are checked now, and a failure is
  a warning with the Windows error; two new tests (Windows only), proven by
  bug planting.
- **Kind:** environment.
- **Takeaway:** check every Windows call's result: called through ctypes, a
  failure is only a return value, never an exception.

### 2026-11-02: A log message and a docstring narrower than the code

- **What happened:** an abandoned connect step's late error was logged as
  coming "after its time limit", but a step is also abandoned when the
  interrupt signal stops connecting. And `_HelperStep`'s docstring said a
  thread ends only when its code returns, leaving out raising.
- **Caught at:** the same review. Now "after it was abandoned" and "returns
  or raises".
- **Kind:** communication.
- **Takeaway:** check that a log message's cause holds on every path that
  reaches it.

### 2026-11-02: A review skill whose steps clashed with the skill it runs

- **What happened:** `/project-review` runs `/code-review` and keeps its
  findings for one merged report, but `/code-review`'s own instructions say
  to report them itself. A run that followed `/code-review` would have
  reported twice, with the merged list shown as a re-report.
- **Caught at:** running `/project-review` in the same review. Its step 2 now
  says not to report `/code-review`'s findings separately.
- **Kind:** process.
- **Takeaway:** when a skill runs another skill, read the inner skill's
  instructions for steps that clash with the outer one's.

### 2026-11-01: A safety gap deferred without checking the planned control that opens it

- **What happened:** after the gap (a) correction, Claude proposed deferring
  the fix for a hover command that can start the motors of a drone on the
  floor (backlog #8), without checking ADR-0027, whose operator controls
  include a "hover" key that would send exactly that command.
- **Why it was wrong:** the deferral assumed nothing sends a hover command
  on the floor before the safety-layer work; the accepted operator controls
  do.
- **Caught at:** the review session, checking the deferral against the ADRs.
- **Kind:** safety design.
- **Takeaway:** before deferring a safety gap, check the accepted ADRs for
  planned features that would open it, and tie the fix to the first of them.

### 2026-11-01: A rename recommended without checking how the project already says it

- **What happened:** in my second code review, Claude recommended renaming
  `missing_values`' "front range" to "front range reading", the glossary
  term. But "down range" is the project's shorthand everywhere: the safety
  layer's stale-data messages, the touchdown code and ADR-0019's title. The
  rename would have made the operator's messages disagree. I accepted it.
- **Caught at:** searching for the old names before making the change.
- **Kind:** recommendation.
- **Takeaway:** before recommending a rename, search how the rest of the
  project already says it.

### 2026-11-01: Code called dead without following every path to it

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
- **Takeaway:** before calling code dead, follow every path to where its
  result is read, including early returns.

### 2026-11-01: A parameter named with a glossary term that means something else

- **What happened:** `run_with_time_limit` called the "what to check" part of
  its timeout message `hint`, but the glossary's *Hint* is the drone's LED
  flash and chirp while it's hidden (ADR-0017). The docstring called the same
  text "what to check" and a comment called it "the fix": three names for
  one thing.
- **Caught at:** walking me through `time_limit.py` in my second code review.
  It's now `what_to_check`, keyword-only, so every call shows the name.
- **Kind:** communication.
- **Takeaway:** before naming something, look the word itself up in the
  glossary, not only the concept.

### 2026-11-01: Cloud setup advice from memory

- **What happened:** to get `CLAUDE.local.md` into cloud sessions, Claude
  described the cloud setup script from memory: where to find it, and a line
  that downloads the file into the repo folder. The docs say the script runs
  before Claude Code starts, is cached for about seven days, and should write
  `~/.claude/CLAUDE.md` instead.
- **Caught at:** looking up the docs after I couldn't find the setup script.
- **Kind:** environment.
- **Takeaway:** check how a tool works in its docs before giving
  step-by-step instructions, the same as checking cflib against its source.

### 2026-11-01: Code reviews that skipped the review checklist

- **What happened:** CLAUDE.md says every `/code-review` also works through
  `REVIEW.md`. The skill's own steps don't include it, and Claude's two
  high-level reviews on 2026-11-01 followed the skill's steps only.
- **Caught at:** answering my question about why some findings come up only
  in my reviews.
- **Kind:** process.
- **Takeaway:** the skill doesn't know this project's checklist, ADRs or
  glossary; a review here must bring them in itself. The project skill
  `/project-review` now does.

### 2026-11-01: The gap between two lines, a fourth time

- **What happened:** the tick loop added its garbage-collector hook before
  the `try` whose `finally` removes it, with a log call in between. Safe in
  practice (Ctrl+C can't raise by then), but it's the same shape as the
  earlier cleanup gaps.
- **Caught at:** walking me through `tick_loop.py` in my second code review.
  The hook is now added inside the `try`, and removed only if present.
- **Kind:** design. Windows of time between two steps.
- **Takeaway:** start anything that needs cleaning up inside the `try` that
  cleans it up.

### 2026-11-01: A tick that raised left no timing behind

- **What happened:** when the tick step raised, the tick loop skipped
  recording that tick, so the log and the summary left out its work time and
  any overrun warning, against ADR-0026's "every tick is logged". A test
  pinned the old count.
- **Caught at:** walking me through `tick_loop.py` in my second code review.
  The tick is now recorded in a `finally`; a new test is proven by bug
  planting.
- **Kind:** design. Edge cases at the start, end and between ticks.
- **Takeaway:** on an error path, check that what the normal path records is
  still recorded.

### 2026-11-01: A cost from Linux in a comment, with no source

- **What happened:** a comment said arming the hang watchdog costs "about
  0.1 ms on Linux", with no source, and the program runs on Windows.
- **Caught at:** walking me through `tick_loop.py` in my second code review.
  Measured on my laptop (0.09 ms median, 0.8 ms worst), and the comment now
  says so.
- **Kind:** environment. Code that was only run on Linux.
- **Takeaway:** a performance figure says where it was measured, on the
  machine the program runs on.

### 2026-10-31: A battery check that a NaN voltage would pass

- **What happened:** the safety pre-check landed the drone when
  `battery.value < LOW_BATTERY_VOLTAGE`. Every comparison with NaN is false,
  so a NaN voltage would have passed the check. `requests.py`, written at the
  same time, already wrote its check so NaN fails.
- **Caught at:** walking me through `safety_layer.py` in my second code
  review. The check is now `not (battery.value >= LOW_BATTERY_VOLTAGE)`, with
  a test proven by bug planting. The firmware is very unlikely to send a NaN
  voltage.
- **Kind:** safety design.
- **Takeaway:** write a threshold check so a value that isn't a number fails
  it: test for the safe side and negate, as `requests.py` does.

### 2026-10-31: A glossary definition the code outgrew

- **What happened:** the minimal safety layer (ADR-0030) puts an approved
  arm request into the movement slot, its only slot, but the glossary's
  *Command slot* still listed the movement slot's commands without arm.
- **Caught at:** walking me through `safety_layer.py` in my second code
  review. The glossary now lists arm.
- **Kind:** process.
- **Takeaway:** when code adds to something the glossary lists, update the
  list in the same commit.

### 2026-10-31: A landing guard that trusted an old drone status

- **What happened:** ADR-0032's `land()` stops the motors instead of landing
  when the drone isn't flying, judged from the drone status. The first
  version didn't check the status's age: if the status stream stalled before
  a take-off showed in it, an old "not flying" would have made `land()` cut
  the motors with the drone in the air.
- **Caught at:** Claude's code review, at a high level. A missing or old
  status now counts as unknown, so the drone lands; a test covers it.
- **Kind:** safety design.
- **Takeaway:** a guard that decides from telemetry must say what it does
  when the value is missing or old, and the safe choice for a missing value
  isn't always the same as for a "no".

### 2026-10-30: A wait that a previous connection could satisfy

- **What happened:** the wait for the first telemetry (ADR-0031) checks that
  every value is in the telemetry buffer. But the adapter kept one buffer for
  its whole life, so connecting a second time found the previous session's
  values already there: the wait passed at once, and the pre-check would have
  ended the flight at its first tick on stale values, the very failure the
  wait exists to prevent.
- **Caught at:** Claude's code review, at a high level. Each connect now
  starts a fresh buffer, and a test connects twice.
- **Kind:** design. State that outlives the session it describes.
- **Takeaway:** for a check like "has it arrived?" or "is it ready?", ask what
  state an earlier run or connection could have left behind.

### 2026-10-30: A reason copied from cflib's waits to a plain sleep

- **What happened:** the new wait in `connect()` (ADR-0031) sleeps in 0.1 s
  slices, and its comment and ADR said that was so Ctrl+C gets through, as
  with the other connect steps. That reason belongs to cflib's waits
  (ADR-0029), which Ctrl+C can't interrupt on Windows. A plain `time.sleep`
  is interrupted by Ctrl+C at once. The Ctrl+C test also only checked that
  Ctrl+C got through eventually, not promptly.
- **Caught at:** planting bugs to prove the tests: one long sleep instead of
  short ones still passed every test. The slices are really for noticing late
  telemetry promptly; the comment and ADR now say so, and a test checks that
  late values are noticed within a second.
- **Kind:** environment. A reason reused without checking that it applies.
- **Takeaway:** when reusing a reason from another part of the code, check
  that the mechanism behind it is the same here; and a test of "it gets
  through" should also check how quickly.

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
