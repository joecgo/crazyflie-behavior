# Claude's mistakes

The implementation and many of the options in this project are AI-assisted
(Claude Code). This log records the mistakes Claude made that I caught, or
that Claude caught itself, so I can see what kind of work it finds hard. It
tells me where to focus my own learning, where to double-check Claude, and
where a new skill for Claude might help.

Newest first. Each entry: what happened, why it was wrong, who caught it, the
kind of work, and the takeaway.

**Kinds of work** (to spot patterns later): *design* (how parts fit
together), *safety design*, *recommendation* (which option Claude pushed and
why), *environment* (assumptions about my machine, time zone or tools),
*testing*, *process* (how decisions are recorded).

---

## 2026-10-29: A stop control designed for a terminal, not for PyCharm

- **What happened:** Claude designed stopping around Ctrl+C, the terminal
  convention, without checking how I run programs. CLAUDE.md says PyCharm:
  in its Run window, Ctrl+C copies text, and the Stop button may end the
  program outright, skipping the landing.
- **Caught by:** my question about Ctrl+C and copy-paste. Claude found the
  PyCharm gap while answering it. Open in backlog #9.
- **Kind:** environment.
- **Takeaway:** for any control or failure path, ask how I actually run the
  program: PyCharm, a terminal window, or the phone.

## 2026-10-29: Ctrl+C described two ways in one ADR

- **What happened:** ADR-0026's decision calls Ctrl+C a stop request (finish
  the tick, then land). Its failure modes say Ctrl+C anywhere in a tick rises
  like an error. Python's default is the second; the first needs a handler.
  Neither said what a second press during the landing does: with Python's
  default, it cuts the landing short, and the Crazyflie adapter's link
  shutdown then sends zero thrust, which drops the drone.
- **Caught by:** Claude, while writing the tick loop. Fixed: Ctrl+C is a
  stop request, and later presses are ignored (ADR-0026).
- **Kind:** safety design. An ADR's words didn't match what the language
  does by default.
- **Takeaway:** when an ADR names a mechanism (Ctrl+C, a timeout), ask what
  happens by default, and what a second one does.

## 2026-10-29: Gaps at the edges of the tick loop

- **What happened:** in the tick loop's first draft, the last tick's overrun
  went unlogged ("done" returned before the check); the hang watchdog stopped
  before the tick's logging, so a blocked console wouldn't be reported; the
  watchdog fell back to standard error, though ADR-0026 says the log file;
  and a stop request waited up to one tick period.
- **Caught by:** Claude's code review, at a high level.
- **Kind:** design. Edge cases at the start, end and between ticks.
- **Takeaway:** when reviewing a loop, check the first tick, the last tick
  and the time between ticks, not just the middle.

## 2026-10-29: Test fakes that hang instead of failing

- **What happened:** two fake tick steps never reported done. When a planted
  bug broke the stop request, their tests hung forever instead of failing.
- **Caught by:** Claude, planting bugs to prove the tests.
- **Kind:** testing.
- **Takeaway:** a fake that can loop needs a limit. Plant a bug in each path
  and check the test fails, not hangs.

## 2026-10-29: An exception to an older ADR without marking it

- **What happened:** Claude added "every overrun gets its own warning" to
  ADR-0026, an exception to ADR-0020's once-per-streak rule, without marking
  ADR-0020 as amended or updating ADR-0026's origin line.
- **Caught by:** Claude's code review.
- **Kind:** process.
- **Takeaway:** when a decision makes an exception to an older one, mark the
  older ADR's status line.

## 2026-10-29: Only one command request per tick

- **What happened:** in the new safety-layer request design, Claude said only
  one command request could be sent per tick.
- **Why it was wrong:** that's true for movement (one velocity at a time), but
  Claude applied it to every command. A buzzer chirp or an LED change can go
  out in the same tick as a movement. The fix: command slots, one request per
  slot per tick.
- **Caught by:** me, asking why a buzzer command couldn't go with a move.
- **Kind:** design. A constraint generalized beyond where it applies.
- **Takeaway:** when Claude states a limit ("only one", "never", "always"),
  ask what it applies to.

## 2026-10-29: Holding back measurements because of an undecided item

- **What happened:** Claude recommended keeping each tick's timing
  measurements in memory and logging only a summary, because where flight
  data is saved (backlog #11) wasn't decided.
- **Why it was wrong:** a pending decision shouldn't shape the code. Logging
  each tick immediately gives context around any error, and where the log
  goes is set separately at startup.
- **Caught by:** me.
- **Kind:** recommendation.
- **Takeaway:** when a recommendation's reason is "that's not decided yet",
  ask whether the decision can be made now instead.

## 2026-10-29: A hang can't be detected

- **What happened:** Claude wrote that the tick loop can't interrupt a hung
  tick, and only discussed acting on a hang. It missed that detecting one is
  cheap and standard (a watchdog, like UE's hang detector; Python has
  `faulthandler.dump_traceback_later`). Its overrun warning only fires when a
  tick ends, and a hung tick never ends.
- **Caught by:** me, asking how UE detects a hang.
- **Kind:** safety design. A missed option.
- **Takeaway:** for every failure mode, ask separately how it's detected,
  logged and handled.

## 2026-10-27: Dates in the wrong time zone

- **What happened:** the cloud session's clock runs on UTC, so the work log,
  ADR-0022 to 0024 and backlog #26 were dated the next day.
- **Caught by:** me.
- **Kind:** environment. Claude assumed the machine's clock matched my time
  zone.
- **Takeaway:** CLAUDE.md now says dates use Pacific time.

## 2026-10-27: Waiting for the next slot after an overrun

- **What happened:** for tick timing, Claude first recommended that after an
  overrun the loop wait for the next 50 ms slot.
- **Why it was wrong:** after a long tick, waiting up to another 50 ms makes
  the drone slower to respond, for no benefit. My version: start the next
  tick at once ([ADR-0024](decisions/0024-tick-timing-strategy.md)).
- **Caught by:** me, comparing it with a game loop.
- **Kind:** recommendation.
- **Takeaway:** check Claude's timing recommendations against how game loops
  already solve the problem.

## 2026-10-24: Trusting a cflib read that returns old data on a timeout

- **What happened:** the Crazyflie adapter Claude wrote polled drone status
  with cflib's `read_bitfield()` and stamped every result as fresh. On a
  timeout, that call doesn't raise: it returns the last value, or 0 if it
  never had one. A stale status looked current, and a missing one read as
  "all flags false".
- **Caught by:** me, in code review. Fixed by streaming status instead
  ([ADR-0021](decisions/0021-drone-status-streams-with-the-state.md)).
- **Kind:** design. Assumed a library call fails loudly without checking its
  source.
- **Takeaway:** for every library call Claude relies on, ask what it does on a
  timeout or error, and check the answer in the source.

## 2026-10-24: A backup that fails together with what it backs up

- **What happened:** Claude recommended letting the position estimate's
  height confirm touchdown when the down range had nothing usable
  ([ADR-0012](decisions/0012-landing-confirms-touchdown.md)). On a Crazyflie
  that height comes mostly from the same down sensor, so when the sensor
  fails, the backup fails too, and the motors could be cut in mid-air.
- **Caught by:** me, in code review. Fixed by
  [ADR-0019](decisions/0019-final-descent-when-touchdown-unconfirmed.md).
- **Kind:** safety design. A backup sharing the primary's failure.
- **Takeaway:** for every backup, ask what it's computed from, and whether
  that's the same thing that just failed.
