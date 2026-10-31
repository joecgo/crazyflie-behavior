# Review checklist

Questions every code review asks, on top of looking for ordinary bugs: in
Claude's `/code-review` (CLAUDE.md points it here) and in my own reviews.
Each one comes from a takeaway in the [mistakes log](docs/claude-mistakes.md),
so reviews look for the kinds of mistakes Claude has made before. When a new
takeaway applies to reviews, it's added here as a question.

## Facts about the hardware and libraries

- Does every claim about how the firmware, cflib, Python or Windows behaves
  name the file or document it was checked in? A claim without one is a guess.
- For each library call the code relies on: what does it do on a timeout or
  an error? Is that checked in the source?
- Windows-only code: is it checked against Windows' documented behavior?
  Continuous integration runs on Linux.

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
  failed?
- A decision made from telemetry: what does it do when the value is missing
  or old? Is that the safe choice for that decision?
- For a check like "has it arrived?" or "is it ready?": could state left by
  an earlier run or connection satisfy it?
- For each cleanup path: what if an interruption lands between two lines, or
  comes twice? Is everything that needs cleaning up started inside the `try`
  that cleans it up?

## Time

- A wait with a deadline: what happens just before and just after it, and
  what does a failing cleanup do to the error meant to be shown?
- A loop: check the first tick, the last tick and the time between ticks, not
  just the middle.
- A mechanism such as Ctrl+C or a timeout: what does it do by default, and
  what does a second one do?

## How I run things

- Controls and failure paths: do they work the way I run the program
  (PyCharm's Run window, a terminal window, the phone)?
- Logging: is it checked with a real library attached, and with the program
  started the way I start it?

## Rules and records

- "Only", "never", "always": what exactly does it apply to? If it's a rule
  about the code, is there a fitness function, and does it read at least one
  real file?
- A decision that makes an exception to an older ADR: is the older ADR's
  status line marked?
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
| Next | | Everything after `b3bc274`: ADRs 0022 to 0032, the safety layer, the tick loop, behaviors, programs and the drone changes |
