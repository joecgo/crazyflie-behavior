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
| design | 4 | 20 |
| safety design | 5 | 18 |
| recommendation | 7 | 6 |
| environment | 4 | 9 |
| communication | 8 | 39 |
| testing | 0 | 12 |
| process | 5 | 20 |
| **Total** | **33** | **124** |
<!-- end generated -->

<!-- generated: patterns -->
| Pattern | Entries |
|---|---|
| said-without-checking | 30 |
| how-I-work | 20 |
| safety-judgment | 16 |
| reading-field-data | 14 |
| records-ahead-of-code | 14 |
| recommendation | 12 |
| message-misstates-outcome | 12 |
| vocabulary | 10 |
| window-between-steps | 10 |
| weak-test | 10 |
| environment | 6 |
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
| M-157 | 2026-11-14 | One flight's battery line filed under other flights | communication | reading-field-data | none yet |
| M-156 | 2026-11-14 | Motor outputs read as the thrust command | communication | reading-field-data | none yet |
| M-155 | 2026-11-14 | The forged drone changed, but not its ADR or glossary row | process | records-ahead-of-code | Q-35 |
| M-154 | 2026-11-14 | A helper and a test whose names said something else | communication | vocabulary | none yet |
| M-153 | 2026-11-14 | A flight command without `--crazyflie` | communication | how-I-work | none yet |
| M-152 | 2026-11-13 | Two backlog rows said ADR-0035's console thread was built | process | records-ahead-of-code | Q-39 |
| M-151 | 2026-11-13 | A flight started without reading how the last one ended | process | reading-field-data | none yet |
| M-150 | 2026-11-13 | A chance worked out for a battery reading that arrives at a fixed time | communication | reading-field-data | none yet |
| M-149 | 2026-11-13 | An option offered for the landing approach that the code already has | recommendation | recommendation | none yet |
| M-148 | 2026-11-13 | Hover heights taken from the moment the hover started | communication | reading-field-data | none yet |
| M-147 | 2026-11-12 | A time limit quoted from memory | communication | said-without-checking | none yet |
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
| M-126 | 2026-11-12 | A recording started before Joe was ready | process | how-I-work | none yet |
| M-125 | 2026-11-10 | One no-flow limit for an uncertainty that grows with height | safety design | safety-judgment | Q-08 |
| M-124 | 2026-11-10 | The altHold climb chosen without reading what its controller does at a switch | design | said-without-checking | Q-07 |
| M-123 | 2026-11-10 | One limit read two ways, and messages that seemed to contradict it | design | message-misstates-outcome | Q-48 |
| M-122 | 2026-11-10 | A comment and an ADR line that promised more than the code | process | records-ahead-of-code | Q-49 |
| M-121 | 2026-11-10 | Choices made while building, not recorded, and new terms not proposed | process | how-I-work | none yet |
| M-120 | 2026-11-10 | The mock found the settle height again every tick | testing | weak-test | Q-09 |
| M-119 | 2026-11-10 | An old status logged as current, and a reset logged before it was sent | communication | message-misstates-outcome | none yet |
| M-118 | 2026-11-10 | A cut-off extraction read as the touchdown | communication | reading-field-data | none yet |
| M-117 | 2026-11-10 | Session 2's light blamed on a check that didn't exist yet | communication | reading-field-data | none yet |
| M-116 | 2026-11-09 | A 0.05 s margin on the climb time limit, not flagged | safety design | reading-field-data | none yet |
| M-115 | 2026-11-09 | ADR-0054 described from its number, not its text | communication | said-without-checking | none yet |
| M-114 | 2026-11-08 | "In this light it never did", for a run with no flow data | communication | reading-field-data | none yet |
| M-113 | 2026-11-08 | "First flight 1 didn't hit it", with cflib's close unchecked | communication | said-without-checking | none yet |
| M-112 | 2026-11-08 | The level final descent's motor stop locks the drone | safety design | said-without-checking | Q-06 |
| M-111 | 2026-11-07 | "About 4.5 s" for the no-flow uncertainty, read from an upper bound | communication | reading-field-data | none yet |
| M-110 | 2026-11-07 | Extra usage spent without a cost estimate or a usage check | process | how-I-work | none yet |
| M-109 | 2026-11-07 | Landing work hidden in take_snapshot, never decided | design | how-I-work | Q-34 |
| M-108 | 2026-11-06 | "About 8" parameter writes for "Charge", counted one per note | communication | said-without-checking | none yet |
| M-107 | 2026-11-06 | A pre-check rule that would end the game at a dark hiding spot | safety design | safety-judgment | Q-24 |
| M-106 | 2026-11-06 | A sound effect's number read from an out-of-date comment | communication | said-without-checking | none yet |
| M-105 | 2026-11-06 | A hand-over order justified by a cflib call it doesn't match | safety design | said-without-checking | Q-02 |
| M-104 | 2026-11-06 | ADR-0041 amended twice without its status line saying so | process | records-ahead-of-code | Q-33 |
| M-103 | 2026-11-05 | The Crazyflie's weight in the glossary, with no source | environment | said-without-checking | Q-01 |
| M-102 | 2026-11-05 | A firmware shutdown at 3.0 V that the default build leaves out | safety design | said-without-checking | Q-03 |
| M-101 | 2026-11-05 | `kalman.varPX` called the position variance | communication | said-without-checking | Q-01 |
| M-100 | 2026-11-05 | "Touchdown never confirmed", read from a log line that wasn't there | testing | reading-field-data | none yet |
| M-099 | 2026-11-05 | Explaining a finding with words the glossary doesn't have | communication | vocabulary | none yet |
| M-098 | 2026-11-04 | A go/no-go rule of "the motion flag set in most samples" | communication | reading-field-data | none yet |
| M-097 | 2026-11-04 | A Bench criterion of 0.5 s for a value that streams at 1 Hz | testing | reading-field-data | none yet |
| M-096 | 2026-11-04 | The Flow deck's maximum shutter read as "too dark" | communication | reading-field-data | none yet |
| M-095 | 2026-11-04 | "A red LED that keeps blinking means a failed self-test" | environment | said-without-checking | Q-01 |
| M-094 | 2026-11-04 | WinUSB for the Crazyradio, and "the README says WinUSB" | environment | said-without-checking | Q-01 |
| M-093 | 2026-11-04 | A battery connector named from memory | environment | said-without-checking | none yet |
| M-092 | 2026-11-04 | ADR-0046 applied without searching for the old wording | process | records-ahead-of-code | Q-35 |
| M-091 | 2026-11-04 | A shortened log line that dropped the outcome | communication | message-misstates-outcome | Q-44 |
| M-090 | 2026-11-04 | Restoring a planted bug with `git checkout` discarded edits | testing | how-I-work | none yet |
| M-089 | 2026-11-04 | "No test enforces it" said without looking at the tests | communication | said-without-checking | none yet |
| M-088 | 2026-11-04 | "Can only be a clock bug", and a cost overstated | design | said-without-checking | none yet |
| M-087 | 2026-11-04 | "Isn't known to be flying", the opposite of the rule | communication | safety-judgment | Q-50, Q-51 |
| M-086 | 2026-11-04 | Comments that said more than their code | communication | records-ahead-of-code | none yet |
| M-085 | 2026-11-04 | A time-limit message that read the telemetry again after the check | design | message-misstates-outcome | Q-26 |
| M-084 | 2026-11-04 | A take-over message that assumed the drone was flying | communication | message-misstates-outcome | Q-43 |
| M-083 | 2026-11-04 | A "known risk" that cflib's own guard rules out | recommendation | said-without-checking | Q-03 |
| M-082 | 2026-11-04 | Records that claimed more than the code or the source showed | communication | message-misstates-outcome | Q-52 |
| M-081 | 2026-11-04 | An ADR amendment without the documents and the test that follow from it | process | records-ahead-of-code | Q-36 |
| M-080 | 2026-11-04 | The battery placed under the board, from memory | environment | said-without-checking | none yet |
| M-079 | 2026-11-04 | A right understanding "corrected" | communication | how-I-work | none yet |
| M-078 | 2026-11-04 | A commit rule that says "before" a review, read as "during" | process | how-I-work | none yet |
| M-077 | 2026-11-03 | Crazyflie adapter code committed without `/project-review` | process | how-I-work | none yet |
| M-076 | 2026-11-03 | Docstrings that a change left behind | communication | records-ahead-of-code | none yet |
| M-075 | 2026-11-03 | An emergency stop that said "not delivered" when it may have been | communication | message-misstates-outcome | Q-43 |
| M-074 | 2026-11-03 | A once-per-streak log line whose streak never ended | design | leftover-state | Q-18 |
| M-073 | 2026-11-03 | A new connection that kept the last one's landing | safety design | leftover-state | Q-17 |
| M-072 | 2026-11-03 | Fitness functions with blind spots | testing | weak-test | Q-32 |
| M-071 | 2026-11-03 | Two constants that must agree, with no test between them | testing | weak-test | Q-47 |
| M-070 | 2026-11-03 | A taken-over flight given the take-off grace period | safety design | safety-judgment | none yet |
| M-069 | 2026-11-03 | An emergency stop that said "Sent." when nothing was | safety design | message-misstates-outcome | Q-52 |
| M-068 | 2026-11-03 | A rescue landing that exited 0 when the rescue failed | design | message-misstates-outcome | Q-52 |
| M-067 | 2026-11-03 | A mitigation in ADR-0044 that the code didn't provide | safety design | records-ahead-of-code | none yet |
| M-066 | 2026-11-03 | ADR-0043 described the old field-testing README wrongly | process | said-without-checking | none yet |
| M-065 | 2026-11-03 | A test fake that streamed only once | testing | weak-test | Q-09 |
| M-064 | 2026-11-03 | New vocabulary in code names before proposing it | process | vocabulary | none yet |
| M-063 | 2026-11-03 | "No landing command can work" on a NaN estimate | safety design | said-without-checking | Q-02 |
| M-062 | 2026-11-03 | An idea of mine credited to the AI | process | how-I-work | none yet |
| M-061 | 2026-11-02 | A work-log row raised without its total | process | how-I-work | none yet |
| M-060 | 2026-11-02 | A tick period quoted from memory | communication | said-without-checking | none yet |
| M-059 | 2026-11-02 | A watchdog recommended that the backlog already ruled out | recommendation | recommendation | none yet |
| M-058 | 2026-11-02 | A refusal that drops the drone it protects | safety design | safety-judgment | Q-21 |
| M-057 | 2026-11-02 | Manual arming called a barrier that doesn't rely on our code | safety design | safety-judgment | Q-12 |
| M-056 | 2026-11-02 | A pushed commit that doesn't pass its own tests | process | how-I-work | none yet |
| M-055 | 2026-11-02 | A failsafe whose landing used the value that failed it | safety design | safety-judgment | Q-12 |
| M-054 | 2026-11-02 | Wording in the NaN change that missed the project's rules | communication | records-ahead-of-code | none yet |
| M-053 | 2026-11-02 | The gap between two lines, a fifth time | design | window-between-steps | Q-19 |
| M-052 | 2026-11-02 | A Windows call whose failure went unnoticed | environment | environment | Q-05 |
| M-051 | 2026-11-02 | A log message and a docstring narrower than the code | communication | message-misstates-outcome | Q-43 |
| M-050 | 2026-11-02 | A review skill whose steps clashed with the skill it runs | process | how-I-work | none yet |
| M-049 | 2026-11-02 | Follow-up commits pushed to a pull request already merged | process | how-I-work | none yet |
| M-048 | 2026-11-02 | "Nothing is scheduled" said without checking | environment | said-without-checking | none yet |
| M-047 | 2026-11-02 | Options offered that didn't fix the problem | recommendation | recommendation | none yet |
| M-046 | 2026-11-01 | A safety gap deferred without checking the planned control that opens it | safety design | safety-judgment | Q-23 |
| M-045 | 2026-11-01 | A rename recommended without checking how the project already says it | recommendation | recommendation | none yet |
| M-044 | 2026-11-01 | Code called dead without following every path to it | recommendation | recommendation | none yet |
| M-043 | 2026-11-01 | A parameter named with a glossary term that means something else | communication | vocabulary | Q-41 |
| M-042 | 2026-11-01 | Cloud setup advice from memory | environment | said-without-checking | none yet |
| M-041 | 2026-11-01 | Code reviews that skipped the review checklist | process | how-I-work | none yet |
| M-040 | 2026-11-01 | The gap between two lines, a fourth time | design | window-between-steps | Q-19 |
| M-039 | 2026-11-01 | A tick that raised left no timing behind | design | window-between-steps | none yet |
| M-038 | 2026-11-01 | A cost from Linux in a comment, with no source | environment | environment | none yet |
| M-037 | 2026-11-01 | A gap described without reading the code that closes it | safety design | safety-judgment | Q-20 |
| M-036 | 2026-11-01 | A backlog item written and dropped without checking or measuring | recommendation | recommendation | none yet |
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

### M-153, 2026-11-14: A flight command without `--crazyflie`

- **What happened:** for session 6's test 3 I gave Joe the hover command copied from the mock-run checklist, with no `--crazyflie`, so it would have run the mock adapter, not the drone. Joe reported "it didn't do anything". His terminal tab was also still busy with a fourth propeller test waiting to connect.
- **Would a Claude review have caught it?** No: it's a command given in chat, not code.
- **Kind:** communication.
- **Pattern:** how-I-work.
- **Guard:** none yet.
- **Takeaway:** a command for a real flight is checked against the program's own usage lines (the `--crazyflie` flag) before it's given, never copied from the mock-run list.

### M-126, 2026-11-12: A recording started before Joe was ready

- **What happened:** after Joe said the next bench would use `--take-off-log`, I started the bench at once. Joe was not at the window yet and only held the drone there at the end, so most of that run was unusable ("I didn't realize you started"). Earlier I had told Joe to say "start" first.
- **Would a Claude review have caught it?** No: it's a conversation step, not code.
- **Kind:** process.
- **Pattern:** how-I-work.
- **Guard:** none yet.
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
- **Guard:** none yet.
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
- **Guard:** none yet.
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
- **Guard:** none yet.
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
- **Guard:** none yet.
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
- **Guard:** none yet.
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

### M-157, 2026-11-14: One flight's battery line filed under other flights

- **What happened:** recording session 6's night flights, I left a line about the 14:51 turned-around flight ("Battery 3.94 V before; 3.39 V at spin-up; 3.50-3.56 V in the hover. Image quality 23 at take-off.") after "Logs not yet analyzed." under the night flights, where it read as their battery. Its spin-up value was also the dip's second reading, not its lowest (3.27 V). Caught while analyzing the night flights, whose logs read 4.01-4.10 V before each flight.
- **Kind:** communication.
- **Pattern:** reading-field-data.
- **Guard:** none yet.
- **Takeaway:** after editing a session log, read each analysis line back against its heading and its log.

### M-156, 2026-11-14: Motor outputs read as the thrust command

- **What happened:** in session 6 I told Joe the hover's "thrust command" averaged about 46,300-47,000, above the plan's 44,500 check and well above session 4's 43,000-43,500. I'd averaged the diagnostic block's `motors` values, which are motor outputs, not the thrust command the plan and session 4 measured. Session 4's motor outputs were 47,900-50,300, so today's are not higher. Caught while comparing the logs across sessions.
- **Kind:** communication.
- **Pattern:** reading-field-data.
- **Guard:** none yet.
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
- **Guard:** none yet.
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
- **Guard:** none yet.
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
- **Guard:** none yet.
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
- **Guard:** none yet.
- **Takeaway:** a number in "Computed from the logs" comes from the data over
  the part it describes, not from a log line written at one moment of it.

### M-147, 2026-11-12: A time limit quoted from memory

- **What happened:** I said a 0.6 m/s initial climb would have a time limit of about 1.2 s. The code's formula (`MAX_FINAL_DESCENT_HEIGHT / climb_speed + 1.0`) gives 1.5 s. I corrected it in the next message.
- **How it was caught:** reading `initial_climb_time_limit` while checking the climb speed limit.
- **Kind:** communication.
- **Pattern:** said-without-checking.
- **Guard:** none yet.
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
- **Guard:** none yet.
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
- **Guard:** none yet.
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
- **Guard:** none yet.
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
- **Guard:** none yet.
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
- **Guard:** none yet.
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
- **Guard:** none yet.
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
- **Guard:** none yet.
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
- **Guard:** none yet.
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
- **Guard:** none yet.
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
- **Guard:** none yet.
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
- **Guard:** none yet.
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
- **Guard:** none yet.
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
- **Guard:** none yet.
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
- **Guard:** none yet.
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
- **Guard:** none yet.
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
- **Guard:** none yet.
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
- **Guard:** none yet.
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
- **Guard:** none yet.
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
- **Guard:** none yet.
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
- **Guard:** none yet.
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
- **Guard:** none yet.
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
- **Guard:** none yet.
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
- **Guard:** none yet.
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
- **Guard:** none yet.
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

