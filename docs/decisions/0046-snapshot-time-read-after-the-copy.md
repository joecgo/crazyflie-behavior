# 0046: The snapshot's time is read after its values are copied

- **Status:** Accepted
- **Date:** 2026-11-04
- **Origin:** My idea, during my third code review. It was option D in
  ADR-0042, which the AI had recommended against; the AI now recommends it.
  Removing the negative-age warning entirely was mine. Supersedes
  [ADR-0042](0042-negative-ages-count-as-fresh.md).

## Context

The tick read its time first, then `take_snapshot` copied the telemetry
buffer. cflib's receive thread could store a value in between, so its age came
out negative. ADR-0042 let slightly negative ages count as fresh and warned
about large ones, with `MAX_NEGATIVE_AGE`, a copy of the tick period. That
copy had to change with the tick rate. ADR-0042 also said a large negative age
could only be a clock bug; a stall between reading the time and copying could
cause one too.

## Options considered

- **C (ADR-0042, kept as is):** a warning below one tick period, with the
  period copied into the safety layer.
- **C with the tick period passed into the safety layer:** no copied value,
  the same warning.
- **D. Read the snapshot's time after the copy:** the telemetry buffer reads
  its clock inside the lock, after copying. Every stored value was stamped
  before it was stored, so no age in a snapshot is negative.

## Decision

Option D, and no negative-age check at all.

- `take_snapshot(time, dt)` becomes `take_snapshot(dt)` in the drone
  interface. The telemetry buffer sets `Snapshot.time` from its clock, under
  the lock, after copying.
- The tick loop's own start time still drives `dt` and lateness (ADR-0024).
- `MAX_NEGATIVE_AGE`, the warning, its tests and the *Negative age* term go.

## Failure modes

- **Inputs:** a value stamped on another clock would look fresher than it is,
  and nothing reports it. Only the telemetry buffer stamps arrival times, with
  its own clock, so this needs a new bug in the buffer.
- **Backups:** none.
- **Never:** a value in a snapshot newer than the snapshot's time.
- **Always eventually:** none new.

## Consequences

- **Risk I accept knowingly:** a clock bug is no longer reported at run time.
  A test guards the order instead: the snapshot's time is read after the copy.
- `Snapshot.time` is slightly later than the tick's start: microseconds
  normally, longer after a stall. `dt` still comes from tick starts, so after
  a stall the two disagree slightly; harmless for durations of seconds.
- Changes the drone interface, both adapters, the fault wrapper, the bench
  program and the tick step. Glossary: *Snapshot* reworded, *Negative age*
  removed.
