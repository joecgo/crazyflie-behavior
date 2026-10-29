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
why), *environment* (assumptions about my machine, time zone or tools).

---

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
