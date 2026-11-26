# 0093: The Crazyflie adapter splits into parts, with take-off and landing free of cflib

- **Status:** Accepted. Narrows two older rules inside `drone/crazyflie/`: [ADR-0002](0002-behavior-depends-only-on-drone-interface.md)'s on importing cflib, and [ADR-0004](0004-strict-typing-ruff-and-units-in-names.md)'s that no cflib object crosses a boundary. Judges `commands.py` as [ADR-0074](0074-split-a-module-by-five-tests-never-by-size.md) asked.
- **Date:** 2026-11-24
- **Origin:** AI recommendation accepted: the split (from the 2026-11-13 codebase review), how it's moved (D13 to D15), the names, where the newer members go and the stage order. Taking it up first was Joe's priority. The cflib objects' scope and the blocking-call fitness function came from the project review of stage 3 (2026-11-24), also AI recommendations accepted.

## Context

`drone/crazyflie/adapter.py` is 1,421 lines and one class: the cflib link,
the log blocks and their callbacks on cflib's receive thread, every send,
and the take-off and landing. Because the file imports cflib, the take-off
and landing code runs under `# pyright: basic`. `connect()` resets 18 fields
by hand (`REVIEW.md`, Q-17), and the mock adapter copies the take-off and
landing by hand. `ARCHITECTURE.md` section 7 proposed the split; the plan is
in the review's working notes (`drafts/2026-11-13-code-recommendations.md`,
C6, not in the repository).

## Options considered

- **A. The full split (chosen).**
- **B. Only take-off and landing and the sends come out:** about half the work, but the
  fields cflib's thread writes stay mixed with the tick's.
- **C. Only take-off and landing comes out,** and the adapter satisfies its interface:
  the smallest, with a two-way link between the two.
- **D. Leave it:** ADR-0074 says size alone is no reason. Fixes nothing.

## Decision

Option A. `DroneInterface` doesn't change. Each part looks up the link and the telemetry buffer on every call and keeps neither; the commands part is `CrazyflieCommands` (Joe's choices while building, 2026-11-24).

Only the four modules that import cflib pass cflib objects (the link, a log block) to each other. `take_off_and_landing.py` never receives one, and ADR-0004's rule holds at every boundary `ARCHITECTURE.md` section 3 lists.

| Module | Holds | Imports cflib |
|---|---|---|
| `adapter.py` | Builds the parts; the order of steps in `connect()` and `disconnect()`; the waits; one short forward per interface method | Yes |
| `link.py` | Opening and closing the link with their time limits; the parameters and deck checks; the radio-only close; the lost link; the thrust base write and its confirmation | Yes |
| `log_blocks.py` | The log blocks and their callbacks; owns the telemetry buffer | Yes |
| `commands.py` | Every send: setpoints, the hand-over (inside `go_to`, so no high-level move can skip it), the motor stop's sends, arm, emergency stop, the buzzer, the estimate reset; the last-resort landing as a function that reads no state | Yes |
| `take_off_and_landing.py` | The initial climb, the landing approach, the final descent and "may be flying", sending through `FlightCommands`, a `Protocol` that `commands.py` satisfies | No; strict typing |

By ADR-0074's tests: take-off and landing passes 1, 2 (once the mock runs
it), 4 and 5; the log blocks 3 and 5; the link 3 and 5; the commands 4 (the
setpoint priority's state and packet orders) and 5 (firmware rules). The
commands pass only because the thrust base's confirmation, written on cflib's
thread, goes to `link.py`.

How it's moved:

- **D13:** `connect()` builds fresh parts (as `__init__` does, for tests that
  never connect), so the hand-written reset goes and reconnecting still works.
- **D14:** test bodies don't change during the moves. Fixtures retarget, and
  one-line test-only forwarding properties, marked `TODO:`, reach the parts.
  A prep commit first moves the 49 test lines that set the log level on the
  adapter's logger (four through a constant) to the package's logger; each
  module logs under its own name.
- **D15:** transcript tests for five scripted flights come before the first move:
  take-off to touchdown, a landing during the initial climb, a landing with no
  usable down range, a take-over then a landing, and `disconnect()` while
  flying. Two or three stay afterwards: those guarding an order an ADR requires.
- **Stages, value first,** each move-only with every test green: transcripts,
  logger prep, commands, the blocking-call fitness function, take-off and
  landing (its strict-typing fixes in their own commit), log blocks, link,
  rebuilding the parts, the other two fitness functions. Stopping early leaves
  option B done.

## Failure modes

No flight behavior changes, but every stage moves flight-critical code.

- **Packet order:** a reordered send breaks the setpoint priority (setpoints
  refused, or the motors cut in the air). Three orders matter: the hand-over
  (ADR-0048, ADR-0056), the motor stop then the release (ADR-0058), the land
  then the release (ADR-0084). The transcripts catch a reorder of the first
  two. No transcript reaches the last-resort landing, so its unit test in
  `test_adapter_landing.py`, unchanged by the moves, guards the third.
- **A stale telemetry buffer:** `connect()` replaces it twice, the second time
  after the estimate reset. A part that keeps its own reference reads a dead
  buffer, and a high-level move aims at an old position. Every part reads it
  from `log_blocks.py` each time.
- **The motor stop split in two:** a path that sends the stop without clearing
  the flight state leaves "may be flying" true. Both stay in one method of
  `take_off_and_landing.py`.
- **The last-resort landing** must not share the state of the landing that
  failed: it reads none, so it bypasses the hand-over on purpose.
- **A blocking call in a tick:** the last-resort landing waits its whole
  duration, and stage 4 puts it beside the tick's take-off and landing code.
  A fitness function, built before stage 4, lists every function in
  `drone/crazyflie/` that sleeps, waits or joins, and checks each is called
  only from `connect()`, `disconnect()` or another listed one. A call through
  a stored callable escapes a check by name, so those go on an allow-list.
- **Never:** a move-only commit that changes a send, an order or a test body.
  **Always:** every test, transcripts included, green after each commit.

## Consequences

- Easier: strict typing on take-off and landing, testing it without cflib, one
  file to re-check after a cflib upgrade, and the mock running the real code.
- Harder: a diff from Joe's last reviewed commit can't show the adapter; the
  parts are reviewed as new files after the split.
- Once built, `ARCHITECTURE.md` section 2 and rule 1 name the modules, and three
  fitness functions check them: the blocking calls (built first), the cflib
  importers by name, and take-off and landing free of cflib and `# pyright: basic`.
- Follow-ups: build the split (backlog #157); one shared cflib fake for the
  adapter tests, then the forwarding properties go (#158); the mock runs the
  take-off and landing code, its own ADR (#159); one state object per phase (#160).
- Glossary: *Crazyflie adapter* reworded; *Transcript test* added.
