# 0084: A lost link ends the run with an error; when our landing raises, the firmware's land is the last resort

- **Status:** Accepted. Amends [ADR-0032](0032-landing-with-a-go-to.md): the firmware's land is sent as a last resort, never as a normal landing. Answers backlog #46.
- **Date:** 2026-11-21
- **Origin:** AI recommendations accepted. For how the tick loop hears of a lost link, I first leaned to the snapshot carrying it (it fits the architecture: the safety layer decides) and chose the adapter raising on the AI's recommendation.

## Context

Nothing subscribes to cflib's `connection_lost`. The adapter infers a lost
link from `link is None`, and stale telemetry fails the pre-check 0.25 s
later. The landing then runs blind: cflib drops every send without an error,
the final descent waits out its time limit, and the program exits 0 with the
drone perhaps still hovering (backlog #46). Separately, if our landing code
raises, `disconnect()` closes the radio link only and the drone keeps
flying; the rescue landing runs the same code, so a repeatable bug defeats
both. From the 2026-11-13 codebase review (C4, D7 and D8, in `drafts/`).
Firmware 2026.08, checked 2026-11-21 (facts register): nothing reacts to the
radio going quiet; a high-level hover holds with no time limit; the
low-battery shutdown is compiled out.

## Options considered

- **A lost link:** A. notice it, log it, skip the blind wait, exit nonzero;
  B. A plus automatic rescue attempts; C. leave it to the test log; D. the
  firmware's emergency-stop watchdog. How the tick hears of it: A. the
  adapter raises; B. the snapshot carries it and the safety layer decides.
- **Our landing raises:** A. the firmware's land as a last resort, then close
  the radio link only; B. a script in `tools/` only; C. as today.

## Decision

- **A lost link.** In `connect()` the adapter subscribes to
  `connection_lost`; the callback can run on any thread, so it only stores
  cflib's message and logs one error. The adapter raises on the tick's next
  call to it; the error leaves the tick loop, and `disconnect()` stops
  waiting and closes without landing. The log says whether the drone may
  still be flying and points to the rescue landing and the emergency stop.
  Exit 1. A link lost on the floor is an error too, and the log says the
  drone wasn't flying. The mock adapter can lose its link on cue.
- **Raising, not the snapshot:** `ARCHITECTURE.md` section 3 already says
  exceptions are for broken connections. The snapshot needs a tick-step
  exception (done while the drone may be flying) and every program checking
  the exit code (the failsafe program would exit 0), and still needs the
  adapter part. It waits for the recorder's events (D11, backlog #137).
- **The last resort.** When `disconnect()`'s own landing raises an
  `Exception` with the link up:
  1. send the firmware's land to height 0 over a fixed 6.7 s
     (`HEIGHT_IF_UNKNOWN` 2 m at `VERTICAL_SPEED` 0.3 m/s; arithmetic, not
     flown);
  2. then release the setpoint priority: released first, the idle planner's
     motors-off setpoint gets through until the land arrives;
  3. sleep that long with the link open;
  4. close the radio link only, and re-raise the first error.

  It reads no telemetry and no project state. An error inside it is logged,
  not raised. Not after a lost link.

## Failure modes

- **Inputs:** after a `go_to` the firmware lands from the `go_to`'s last
  setpoint, finite whatever the estimate. After a setpoint stream it lands
  from the estimate; a NaN or infinite one plans a NaN trajectory, the
  planner switches off, nothing is sent, and the drone drops within 2 s, as
  with no last resort. A height estimate reading low stops the motors above
  the floor: a drop by the error, ADR-0032's reason. A link lost mid-flight
  leaves a high-level hover holding with no time limit, and a setpoint
  stream dropping within 2 s.
- **Backups:** the last resort shares the link and the drone's estimate with
  our landing, and none of our Python landing code. For a lost link nothing
  on the PC helps (backlog #12).
- **Never:** the last resort runs while our landing still works, or reads
  what failed it; a lost link logged as a landing; exit 0 after a lost link.
- **Always eventually:** a drone whose link is up gets some landing command
  after any error.

## Consequences

- **Risk I accept knowingly:** a link lost in high-level flight leaves the
  drone hovering until the rescue landing, the emergency stop or a flat
  battery. The emergency-stop watchdog would drop it instead, and defeats the
  rescue landing (backlog #12).
- ADR-0032's "never" line (the motors stop in mid-air because a trajectory
  ended) now has one exception: the last resort, with a height estimate
  reading low. Without the last resort, the drone drops within 2 s after a
  setpoint stream, or hovers after a `go_to` until the rescue landing, the
  emergency stop or a flat battery.
- Not checked: whether cflib drops packets still queued when the link closes;
  the sleep avoids relying on it (backlog #138).
- Tests: a landing that raises sends the land, then the release, then closes
  the radio link only, in that order; the first error reaches the program;
  no last resort after a lost link; a lost link in flight and on the floor
  ends the run at once with exit 1 and the right log line.
- Backlog #135 builds it, with ADR-0083: Crazyflie adapter code, so Max and
  `/project-review max`. Backlog #61's race now ends the run as a lost link
  does, with a `KeyError`.
- Glossary: *Last-resort landing* added.
