# 0083: Every flight end lands inside the tick loop; the tick loop runs until the drone is down

- **Status:** Accepted. Amends [ADR-0026](0026-tick-loop-calls-one-tick-step.md) ("Stopping": the loop no longer returns on a stop request, and leaving it no longer lands) and [ADR-0027](0027-operator-controls.md) ("land now" sets the flight end, not a failed safety pre-check). Answers backlog #59.
- **Date:** 2026-11-21
- **Origin:** Mixed. Later interrupt signals ignored during the landing: mine, over the AI's recommendation that a second one leaves the loop at once and `disconnect()` lands. The point that the time limit shares the tick step's state, so it only catches bugs after the flight end: mine. The flight end and its three causes, the time limit (60 s, then an error), `disconnect()` silencing a tone, an abstract `request_stop()`, a land on the floor too, and keeping `BenchTickStep`: AI recommendations accepted. The "As built" answers (2026-11-21, while coding): AI recommendations accepted; I first chose to remove `SILENCE_HOLD`, then kept it, since ADR-0053 records its wait.

## Context

Today `BehaviorTickStep.run` reports done on the tick the safety pre-check
fails, and the loop returns on a stop request. `disconnect()` then lands in a
private loop (`_land_and_wait_for_touchdown`) with no snapshot lines, no hang
watchdog, no overrun warnings and no way to silence a tone (backlog #59). It
flies every landing after a failsafe, a stop request or an error, and none of
the field tests' normal landings. Hide-and-seek lands every round and takes
off again on the same link, so the landing can't live in shutdown. From the
2026-11-13 codebase review (C3, D3 to D6, in `drafts/`, git-ignored).

## Options considered

- **A stop request in flight:** A. land in the loop, and a second interrupt
  signal leaves it at once so `disconnect()` lands; B. land in the loop, later
  signals ignored; C. as today.
- **A behavior done in flight:** A. the tick step lands it; B. as today; C. an
  error.
- **A time limit on that landing:** A. a tick-step backstop; B. only the
  adapter's own deadlines.
- **A tone left on:** A. the tick step requests a silence at the flight end;
  B. `disconnect()` silences; C. later.
- **The bench program:** keep `BenchTickStep`, or run the bench as a behavior
  on `BehaviorTickStep`.

## Decision

- **The flight end.** The safety layer records it, with its reason. A failed
  pre-check, a stop request, or a behavior that reports done while the drone
  may be flying sets it. It fills the movement slot with `Land()` and refuses
  every later request. It never clears within a run: a landing a behavior
  requests between rounds doesn't set it (ADR-0030's "never resumes").
  `pre_check_has_failed` keeps its meaning, so a Ctrl+C can't count as the
  failsafe program's pass (`failsafe.py:99`).
- **The tick step keeps ticking until the drone is down.** After the flight
  end it skips behaviors and still runs the snapshot, the pre-check, the
  take-off and landing update and the send. `run()` reports done on the first
  tick whose snapshot says the drone isn't flying; on the floor, that tick.
- **Stop requests (B).** `TickStep.request_stop()` is abstract. The loop calls
  it once, on the tick's thread, when it first sees the stop request, then
  ticks until `run()` reports done. `BehaviorTickStep`'s sets the flight end;
  `BenchTickStep`'s makes its next `run()` report done. Later signals are
  ignored, as ADR-0026 says. Abstract, because a tick step that forgot it
  would ignore stop requests and only the emergency stop would end the
  program. On the floor a stop request sends `Land()`, which the adapter turns
  into a motor stop.
- **A behavior done in flight (A)** sets the flight end. Fewer changes than an
  error: today's behaviors report done in flight when they fail
  (`hover_test.py:211`, `:292`; `failsafe_test.py:100`, `:108`;
  `rescue_landing.py:63`).
- **A time limit (A): 60 s from the flight end, a placeholder.** If the drone
  may still be flying then, the tick step raises an error; `disconnect()`
  lands; exit 1. The adapter's worst landing from 2 m is about 30 s (from its
  constants, not flown).
- **A tone (B, backlog #59).** After its landing, `disconnect()` silences and
  waits up to 1 s for the drone to confirm the write (cflib's parameter update
  callback), then closes the link; with no confirmation, a warning. Not A:
  "Charge" plays on the floor, where the tick ends at once, and an error skips
  the tick step.
- **The bench keeps `BenchTickStep`.** On `BehaviorTickStep` the safety layer
  would send `Land()`, a motor stop on the floor, at every stop request and
  failed pre-check, and a telemetry stall would end the run. Without a safety
  layer, ADR-0028's "never commands the drone" holds by construction.
- **As built (2026-11-21):**
  - A drone with no `sound.effect` parameter gets a warning, and
    `disconnect()` closes anyway (backlog #136).
  - The first report of `sound.effect` 0 confirms the silence, even the
    answer to an earlier silence (backlog #141).
  - `SILENCE_HOLD` stays: ADR-0053 records its 1 s wait.

## Failure modes

- **Inputs:** a missing or old drone status counts as flying (ADR-0032), so
  the loop keeps ticking, up to the time limit. An error in any tick after the
  flight end reaches `disconnect()`, which lands (ADR-0026).
- **Backups:** the time limit shares the tick step's state and thread: it
  can't catch a flight end that's never set, or a hung tick (backlog #26).
  `disconnect()`'s landing shares the adapter's landing code with the loop's,
  and none of the new tick-step code; ADR-0084 covers that code raising.
- **Never:** a behavior ticked after the flight end; `run()` done while the
  drone may be flying; a stop request counted as a failed pre-check; the
  flight end clearing within a run.
- **Always eventually:** after a flight end, the drone lands and its motors
  stop, inside the loop, or through `disconnect()` at the time limit.

## Consequences

- **Risk I accept knowingly:** a bug in the flight end or the tick step that
  leaves the drone hovering can't be ended with Ctrl+C. Only the 60 s limit
  or the emergency stop (a drop) ends it.
- Easier: every landing after a flight end gets snapshot lines (backlog #72's
  case), the hang watchdog and overrun warnings.
- Must not change: the hover program's exit codes (ADR-0062, ADR-0066), the
  failsafe program's pass (ADR-0041), the bench's exit code 0 on a stop
  request, ADR-0065's take-off block stop in `disconnect()`.
- Tests: the time limit exactly at 60 s and one tick before; the mock adapter
  drops parameter writes still waiting when the link closes; each program
  ends on the floor before `disconnect()`. The eight test fakes get
  `request_stop()`. `SILENCE_HOLD` stays until built.
- Not checked: that the firmware answers each parameter write (cflib's
  comment, `param.py:666-667`); whether `sound.effect` exists without the
  Buzzer deck (backlog #136).
- ADR-0027's "land now" sets the flight end, with the reason "land now", so
  it can't count as the failsafe program's pass (built with backlog #111).
- Backlog #134 builds it, with ADR-0084 (#135): the tick loop, tick step,
  safety layer and Crazyflie adapter, so Max and `/project-review max`. Test
  log drafts and the failsafe test's docstring say where the landing runs.
- Glossary: *Flight end* added; *Stop request* reworded.
