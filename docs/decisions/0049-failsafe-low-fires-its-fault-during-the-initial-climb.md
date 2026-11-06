# 0049: Failsafe low forges its battery fault during the initial climb; a landing during the climb is a final descent

- **Status:** Accepted. Amends [ADR-0041](0041-failsafe-tests-inject-a-fault-into-the-pre-check.md): Failsafe low no longer hovers at 0.1 m. Amends [ADR-0048](0048-level-through-the-bad-flow-zone.md): it covers a landing requested during the initial climb. Closes backlog #52.
- **Date:** 2026-11-05
- **Origin:** AI recommendation accepted: firing the fault during the climb, and the gap in ADR-0048 it exposed. Keeping the name Failsafe low, a new ADR instead of an edit, and the rule for a landing during the climb (stop the climb, final descent): mine.

## Context

Failsafe low took off to 0.1 m so a failsafe landing could be tried low first,
where a fall is harmless (ADR-0041). ADR-0048 refuses take-off targets at or
below 0.30 m, and a level hover below the final descent height would hold
position by flow inside the bad-flow zone, which ADR-0048 rules out. So no
hover below about 0.40 m can fly (0.30 m cap plus the failsafe test's 5 cm
tolerance). On 2026-11-04 the real battery also tripped the failsafe 0.9-2.0 s
after take-off, before the forged fault (backlog #50).

ADR-0048 has a gap: its landing approach is a `go_to` to the final descent
height, but a landing requested during the initial climb has no such height
yet (the settle height isn't found), and a `go_to` there would hold position
by flow in the zone.

## Options considered

- **A. Failsafe low hovers at 0.40 m:** a one-constant change, but it nearly
  duplicates Failsafe high, 10 cm lower.
- **B. Retire Failsafe low:** simplest, but landing during take-off would only
  ever be tested by accident.
- **C. Fire the fault during the initial climb:** the tests differ by what the
  failsafe interrupts, not by height.
- **Rejected: a level hover at 0.1 m.** A 1° tilt error moves the drone about
  0.8 m in 3 s with no position hold.

## Decision

Option C, and Failsafe low keeps its name.

- **Both tests take off to 0.5 m.** Failsafe high forges the fault after a 3 s
  hover (unchanged). Failsafe low forges it during the initial climb: when the
  down range has been at least 0.10 m for two readings in a row (the reading
  dips to 0.000-0.003 m at spin-up). Counted by reading, not by snapshot, since
  a late reading can show up in two snapshots. Placeholders: 0.10 m, two
  readings.
- **A landing requested during the initial climb** (a failsafe, or the cap's
  "land at once") **stops the climb and starts the final descent** from where
  the drone is: still level, on the same setpoint stream, only the vertical
  speed changes. No landing approach, since there is no final descent height.
  The final descent's time limit (ADR-0019) is worked out from the down range.
- If the down range isn't usable, ADR-0048's fallback applies (ADR-0019's slow
  high-level descent).
- Failsafe high still covers landing from a hover. Pass criteria are ADR-0041's,
  plus: the log shows the climb stopped and the final descent started.

## Failure modes

- **Inputs:** a down range that never reaches 0.10 m means the fault never
  fires; the failsafe test's take-off time limit lands the drone normally and
  the test has failed. A noisy reading near the floor could fire the fault a
  moment early; two readings in a row guard against one bad sample.
- **Backups:** the real low battery can still trip first (#50); the log tells
  which fired. A stopped stream: ADR-0048's 0.5 s level-out and 2 s lock.
- **Never:** a landing during the climb holds position by flow in the zone, or
  hands over to the high-level planner before the final descent.
- **Always eventually:** the motors stop (ADR-0048).

## Consequences

- **Risks I accept knowingly:**
  - The trigger depends on the down range near the floor, its noisiest reading.
  - Failsafe low no longer proves a landing from a low hover; Failsafe high
    proves the hover landing, and Failsafe low the climb landing.
  - The fault fires about 0.5 s after take-off, ahead of the real battery's
    best observed 0.9 s, but a weak battery can still beat it.
  - A landing in the climb starts level, with up to the cap's tilt-drift risk
    (ADR-0048); the fall height is low (up to about 0.3 m).
- Neither test can fly until ADR-0048 is built.
- Glossary: *Failsafe low / Failsafe high* reworded, and *Landing approach*
  gains the climb exception (proposed for my OK).
- Code: the failsafe program takes `--fault-at climb|hover` instead of
  `--height-meters`, and the wrapper has the climb trigger. Still to build with
  ADR-0048: the adapter's landing during the initial climb, and the mock's
  climb (ADR-0011). Until the mock reports a down range (backlog #34), a mock
  rehearsal of Failsafe low can't fire its fault; the tests set a reading.
