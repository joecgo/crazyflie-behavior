# 0024: Tick timing: due times on a fixed beat, plain sleep, measured jitter

- **Status:** Accepted
- **Date:** 2026-10-28
- **Origin:** Mixed. Starting at once after an overrun, never catching up: my idea. Counting each due time from the previous due time: the AI's tweak, accepted after discussion. Plain sleep, the garbage collector left on, and the measurements: AI recommendations accepted.

## Context

The tick loop runs at 20 Hz ([ADR-0023](0023-tick-rate-20-hz.md)) on Windows
and Python. It needs a rule for when each tick starts, what happens when one
runs long, how it waits, and how we know it's keeping time. Checked in the
CPython 3.12 docs (2026-10-28): on Windows 8.1 and newer, `time.sleep` uses a
high-resolution timer (100 ns), so the old ~15.6 ms sleep granularity is gone.

## Options considered

- **When ticks start:** each due time counted from this tick's actual start
  (like UE's `t.MaxFPS`; small wake-up lateness adds up, about 19.8 Hz); from
  the previous due time; or a fixed grid that, after an overrun, waits for the
  next slot (slower to respond) or catches up (a burst of commands decided on
  one snapshot, like physics substep catch-up).
- **Waiting:** plain sleep; or sleep, then spin for the last millisecond. Spinning
  holds Python's GIL, so cflib's radio thread waits for it (up to the 5 ms
  switch interval) and telemetry arrives later.
- **Garbage collector:** leave it on and measure; or turn off its cycle
  collector during flight and collect in spare time (a rule to follow, and
  memory can grow, for a problem not yet measured).

## Decision

- **Due times:** the next tick is due one tick period after the previous
  tick's due time, so a late start counts as part of the frame time and the
  rate stays at 20 Hz. **After an overrun** (a tick still working at the next
  due time), the next tick starts at once and the beat restarts from there.
  Missed ticks are skipped, never caught up.
- **Waiting:** plain sleep until the due time (`RealClock.sleep_until`), for
  the most accurate telemetry. No spin-wait.
- **Garbage collector:** left on. Every collection's pause is measured with
  `gc.callbacks`.
- **Measuring:** every tick records its lateness (actual start minus due time)
  and its work time. Every overrun is logged as a warning
  ([ADR-0020](0020-failures-degrade-gracefully.md)). Each flight ends with a
  summary: worst case and 99th percentile of lateness and work time, the
  overrun count, and garbage-collector pauses.
- The due-time logic lives in the tick loop and uses the injected clock
  ([ADR-0009](0009-clock-abstraction.md)), so tests drive it with `SimClock`.

## Failure modes

- **Inputs:** the clock is `perf_counter`, which never jumps backward. A late
  wake-up only delays one tick. A tick that hangs can't be interrupted by the
  loop: no tick, no setpoints.
- **Backups:** for a hang, only the firmware's setpoint timeout (on the drone,
  so it doesn't share the PC's failure). In steering mode it stops following
  after about 0.5 s and cuts the motors after about 2 s (placeholders,
  [ADR-0011](0011-mock-models-setpoint-timeout.md)), so a hang over 2 s
  drops the drone.
- **Never:** a burst of catch-up ticks; an overrun that isn't logged.
- **Always eventually:** the next tick starts, unless a tick hangs.

## Consequences

- Escalation paths, only if measurements show jitter hurts: spin-waiting,
  garbage-collector control, Linux with PREEMPT_RT, or the onboard reflex
  layer (backlog #12). The measurements feed backlog #25.
- Tests use `SimClock` to check due times, skipped ticks after an overrun,
  and that lateness and work time are recorded.
