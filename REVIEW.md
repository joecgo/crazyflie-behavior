# Review checklist

Questions every code review asks, on top of looking for ordinary bugs: in
Claude's `/project-review` (step 6) and in my own reviews.
Each one comes from a takeaway in the [mistakes log](docs/claude-mistakes.md),
so reviews look for the kinds of mistakes Claude has made before. When a new
takeaway applies to reviews, it's added here as a question.

## Facts about the hardware and libraries

- Was each claim about how the firmware, cflib, Python or Windows behaves
  checked, not recalled? If a decision or safety code rests on it, its ADR
  names the file it was checked in. Docstrings and comments don't cite
  sources.
- Does a checked claim say only what its source showed? "This path fails" is
  not "every path fails" unless the other paths were checked too.
- For each library call the code relies on: what does it do on a timeout or
  an error? Is that checked in the source, including the `if` that guards the
  call (not only what the function does when it runs)?
- Windows-only code: is it checked against Windows' documented behavior, and
  is every Windows call's result checked? Continuous integration runs on
  Linux.

## Fakes and the real drone

- For each fake (the mock adapter, a test's fake): how does the real adapter
  differ at start-up, and in the moments after each command? Are those
  moments tested?
- Can a fake loop forever? It needs a limit, so a broken test fails instead of
  hanging.

## Failures

- For each failure mode: how is it detected, how is it logged, and what
  handles it?
- For each backup: what is it computed from, and is that the thing that just
  failed? For a failsafe a check triggers, follow the failed value through
  the failsafe's own action.
- For each failure or refusal the code handles: does it stop, retry or carry
  on, and does that follow ADR-0020 (or ADR-0033, for a field test)?
- A decision made from telemetry: what does it do when the value is missing,
  old or not a number? Is that the safe choice for that decision?
- For a check like "has it arrived?" or "is it ready?": could state left by
  an earlier run or connection satisfy it?
- Code that resets state for a new connection or run: is every field the
  constructor sets either reset or kept on purpose? Check against the field
  list, not memory.
- A flag that limits a log line to once per streak: is it cleared on every
  path that ends the streak, not only the usual one?
- For each cleanup path: what if an interruption lands between two lines (log
  lines included), or comes twice? Is everything that needs cleaning up started inside the `try`
  that cleans it up?
- A claim about what happens after a failure: is the code path read to its
  end, through the program's shutdown?
- For each error or cleanup path that closes the link: could the drone be
  flying then? cflib's `close_link()` sends a zero-thrust setpoint first,
  while its link is still open (ADR-0038; the condition was checked in the
  source on 2026-11-04).
- A safety gap that's deferred: does an accepted ADR plan a feature that
  would open it first?

## Time

- A wait with a deadline: what happens just before and just after it, and
  what does a failing cleanup do to the error meant to be shown?
- A wait whose error message reads live state: does the message use the
  result of the check that timed out, not a fresh read?
- A loop: check the first tick, the last tick and the time between ticks, not
  just the middle.
- A mechanism such as the interrupt signal or a timeout: what does it do by
  default, and what does a second one do?

## How I run things

- Controls and failure paths: do they work the way I run the program
  (PyCharm's Run window, a terminal window, the phone)?
- Logging: is it checked with a real library attached, and with the program
  started the way I start it?

## Rules and records

- "Only", "never", "always": what exactly does it apply to? If it's a rule
  about the code, is there a fitness function, and does it read at least one
  real file? Is each form its scanner handles exercised by a test?
- A decision that makes an exception to an older ADR: is the older ADR's
  status line marked?
- A change to what a value or term means: was the old wording searched for
  across the code, the glossary and the ADRs?
- An ADR amendment that changes how a test passes: do the test log drafts'
  pass criteria and checklists match it, and is there a test for the new rule?
- Does every term in a new name or comment appear in the glossary, even one
  that other docs already use? Does its definition still match the code?
- Does a new name use a glossary term's word for something else?
- Does a name, comment or log message name a raw input (a key) where the
  code receives a signal or command?
- Does each log message's stated cause hold on every path that reaches it?
- Is every new log or console message one short sentence an operator could
  read mid-flight, with the reasons left in a comment or the ADR? Does a
  shortened message still say the outcome (failed, not confirmed, refused)?
- Does new wording name a milestone, quote a constant's value, or describe
  something temporary without `TODO:`?
- Is any new constant a copy of a value that follows from another one?
- A docstring, comment or message that describes a safety judgment: which
  way does the judgment fail when unsure, and does the wording say the same?
- Review fixes are new code: did anything review the lines a fix commit
  added, wording included?
- A tool or program whose job is one outcome (a stop, a rescue, a pass): does
  it report success only when that outcome happened, through its exit code
  as well as its message? When a record says an action "stopped" or "landed",
  does it say what observed that? A command the adapter sent is not a command
  that arrived: cflib drops packets without an error once the link is lost.
- New tests: are they proven by bug planting
  ([coding style](docs/coding-style.md))?

Takeaways about recommendations and explanations stay in the mistakes log
only: they're for me, when I weigh Claude's options.

## My reviews

Each review covers only what's new since the one before: new files line by
line, changed files as diffs from the last reviewed commit, and tests as a
spec, by their names.

| Dates | Reviewed up to | What |
|---|---|---|
| 2026-10-22 to 2026-10-27 | `b3bc274` | All the source then (geometry, snapshot, clock, the drone interface, telemetry buffer, mock adapter, conversions, touchdown, the Crazyflie adapter) and the tests, as a spec. Led to ADR-0018 to ADR-0021 and 20 new adapter tests |
| 2026-10-28 to 2026-11-02 | `366714a` | ADRs 0022 to 0033, the safety layer, the tick loop, behaviors, programs and the drone changes. Led to ADR-0033 and the non-finite-value rule in ADR-0030 |
| 2026-11-04 | `0846826` | Everything after `366714a`: `cd6e156` plus the five commits after it on this branch. The drone interface and snapshot, the safety layer, the Crazyflie adapter (ADR-0037, ADR-0038, ADR-0039, ADR-0045), the mock adapter and start-up, the failsafe and rescue landing programs and behaviors, the emergency stop tool, wording changes, and the tests as a spec. Led to ADR-0046, three coding-style rules, the glossary's *Stale value* and backlog #45(c) |
| Next | | Everything after `0846826`, starting with this review's fix commits |
