# 0094: Connecting raises the interrupt signal that a CPython lock error hides

- **Status:** Accepted
- **Date:** 2026-11-25
- **Origin:** Mixed: fixing it before stage 4's commits was mine, over the
  AI's recommendation to carry on and fix it later; the fix (option A) was an
  AI recommendation accepted.

## Context

`test_the_interrupt_signal_while_the_link_opens_gets_through_and_stops_the_connection_under_way`
failed at random: once in 117 runs on its own on `479f64f`, once in 238 on
#157's stage 4, and once in a full run. Its fake step sends the interrupt
signal from the helper thread as the step starts. In CPython 3.12.10,
`Condition.wait` takes its lock back in a `finally` through
`_acquire_restore`, a Python method. When the KeyboardInterrupt is raised on
entering it, the lock stays released, and `Event.wait`'s `with` block raises
`RuntimeError: release unlocked lock` with the KeyboardInterrupt as its
context (the traceback ran through `Thread.start()`; every 0.1 s wait in
`run_with_time_limit` has the same window). The cleanup is the same either
way: `run_with_time_limit` and `connect()` both catch `BaseException`. But
`run_program` then logs a Ctrl+C while connecting as a critical error and
exits with code 1, not 130 (ADR-0029). Connect's other waits use
`clock.sleep_until`, which holds no lock.

## Options considered

- **A. `run_with_time_limit` raises the hidden KeyboardInterrupt:** fixes
  the tests and the program's ending; code for one CPython behavior in the
  Crazyflie adapter.
- **B. Tests only:** the fake step sends the signal after the thread starts.
  The rare wrong ending stays, and the delay is a timing assumption.
- **C. No asynchronous interrupt while connecting:** the signal handler
  records it, and the time-limit loop raises it between waits. A new path
  from the program into the adapter, for a rare, harmless case.
- **D. The tests accept the lock error:** production unchanged; a test that
  passes on a RuntimeError reads as weaker.

## Decision

Option A, and before stage 4's commits: a test that fails at random makes
a red continuous integration run mean nothing.

- When `run_with_time_limit` catches a `RuntimeError` raised while a
  `KeyboardInterrupt` was being handled, it abandons the step and runs
  `on_abandon` as for any error, then raises that KeyboardInterrupt with no
  context, so `run_program` reports the interrupt signal (exit code 130).
  The hidden RuntimeError goes to the log at debug level.
- A Ctrl+C while connecting then always ends the program the way ADR-0029
  says, and the tests that send the signal as a step starts stay as written:
  they still check why `step.start()` is inside the `try`.
- **Risks accepted:** the race is recognized by its symptom; inside that
  block nothing else raises a RuntimeError while an interrupt is handled. A
  later Python may not have the race (not checked); the code is then dead
  until ADR-0078's pin to 3.12 moves.

## Failure modes

- **Inputs:** the interrupt signal at any moment of connecting, including
  inside CPython's lock handling.
- **Backups:** the cleanup doesn't depend on recognizing the race: it runs
  for every exception, as before.
- **Never:** a Ctrl+C while connecting is lost, leaves the radio claimed, or
  commands the drone (nothing is commanded while connecting: ADR-0038).
- **Always eventually:** the step is abandoned, the link closes as before,
  and the program stops with the interrupt signal's exit code.

## Consequences

- One new test raises the lock error during a KeyboardInterrupt at a step's
  start, with no real signal, so it can't race. The three tests that send
  the signal as a step starts (the link, the parameters, the time limit) stay
  as written and stop failing at random.
- The CPython behavior goes in the facts register, so a Python upgrade
  re-checks it (ADR-0078): re-run the three tests many times, and remove the
  code if the race is gone.
- Amends ADR-0029. No glossary change.
