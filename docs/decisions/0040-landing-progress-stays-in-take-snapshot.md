# 0040: Landing progress stays in take_snapshot for First flight

- **Status:** Superseded by [0055](0055-take-off-and-landing-update-each-tick.md) (2026-11-07): landing progress moves to a per-tick drone call; the hang risk below stays.
- **Date:** 2026-11-02
- **Origin:** Mixed. Option A for First flight and keeping D as the alternative to try: mine, against the AI's recommendation of D. Splitting this off from backlog #8: AI suggestion accepted.

## Context

The Crazyflie adapter lands with a `go_to` to the floor that keeps holding
its end point, and stops the motors only once touchdown is confirmed
(ADR-0032). That check runs inside `take_snapshot`, so it advances only while
ticks run. A crash or a normal exit is covered: `disconnect()` lands and
blocks until the motors stop. A hung tick is not: the hang watchdog (ADR-0026)
only reports it, and the `go_to` keeps the motors running at the estimated
floor height, where drift can hold the drone just above the floor or press it
into it.

## Options considered

- **A. Leave it in `take_snapshot`.** The kill switch, on its own thread
  (ADR-0027), is the backup.
- **B. A separate per-tick call.** Cleaner (no side effect in a snapshot), but
  it still stops when ticks stop.
- **C. A landing thread in the adapter.** Covers landings only, and races with
  commands from the tick (a `take_off` while it stops the motors).
- **D. The hang watchdog lands.** On a hang, a watchdog thread latches and
  calls `_land_and_wait_for_touchdown`. Covers hangs in flight too, but not a
  hang inside a cflib send, since its own commands wait behind it (backlog
  #26).

## Decision

Option A for First flight. D goes to backlog #26 as the alternative to try.

## Failure modes

- **Inputs:** none new.
- **Backups:** the kill switch, on its own thread, which needs the operator
  to notice.
- **Never:** none new.
- **Always eventually:** a landing the program leaves, by error or exit,
  stops the motors (unchanged, ADR-0026).

## Consequences

- **Risk I accept knowingly:** a tick that hangs mid-landing leaves the motors
  running at the floor until ticks resume or I use the kill switch. At First
  flight I'm watching the whole time; in hide-and-seek the drone lands every
  round, maybe while I'm not looking, so this needs revisiting before the
  game.
- No code change. The take-off-height, ceiling, stale-data and severity parts
  of backlog #8 stay open.
