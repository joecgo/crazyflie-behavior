# 0056: ADR-0048 as built: low take-off targets are a bug, the initial climb has a time limit, commands wait out the level parts

- **Status:** Accepted. Amends [ADR-0048](0048-level-through-the-bad-flow-zone.md): the rules below, and its field-test plan. Closes backlog #56. Amended by [ADR-0068](0068-landing-approach-aims-below-the-final-descent-height.md), 2026-11-13: the landing approach's aim, and its time limit, now a backup.
- **Date:** 2026-11-07
- **Origin:** Mixed. Raising for low targets, the cap as the minimum, the climb time limit, ignoring commands while level, the cap as the final descent height without a take-off, and the settle hold's 0.10 m start: AI recommendations accepted. No separate initial-climb test, and no flashlight in session 2: mine.

## Context

Building ADR-0048 left gaps. It says a take-off target at or below the 0.30 m
cap is refused, but not how. A lost down range during the initial climb never
finds a settle height or trips the cap, so the drone climbs level until the
firmware's 2 s cut, up to about 0.7 m. A command during a level part could
hand over to the high-level commander inside the bad-flow zone. A taken-over
flight (ADR-0038) lands with no settle height. And the settle rule could fire
on the floor: before lift-off the drone sits still, so its speed estimate is
low.

## Options considered

- **Low targets:** the adapter raises `ValueError`; or the safety layer refuses
  them (needs a minimum on the drone interface, with backlog #8).
- **Commands while level:** ignored, logged once per streak (ADR-0039's way);
  or the latest kept and run when the level part ends (stale by then).
- **No settle height:** the cap; the 0.15 m minimum (dim light can put the zone
  above it); or ADR-0019's slow high-level descent all the way (holds position
  by flow in the zone).

## Decision

- **Low targets are a bug:** the adapter raises `ValueError` for a target at or
  below the cap constant itself, so lowering the cap lowers the minimum. The
  mock does the same.
- **Climb time limit:** if the initial climb hasn't ended by the cap divided by
  0.2 m/s plus 1 s (2.5 s) after the take-off was sent, the drone lands with
  ADR-0049's climb landing. A placeholder.
- **Commands while level:** hover, move-to, set-velocity and take-off are
  ignored during the initial climb and the final descent, logged once per
  streak. Land and the motor stops go through. A land during the initial climb
  starts the final descent from there (ADR-0049).
- **No settle height:** the final descent height is the cap.
- **The settle hold starts above 0.10 m** by the down range: below that the
  firmware's flow model is wrong in any light (ADR-0048). The final descent
  height is at least 0.15 m anyway, so only the logged settle height changes in
  good light. A placeholder.
- **Backlog #56:** every hand-over to the high-level commander uses ADR-0048's
  order: the last setpoint, the high-level command, then the release.
- **Field test:** no separate initial-climb test. First flight 2's tests check
  the take-off; Failsafe high's take-off is the first full initial climb. No
  flashlight in session 2.

## Failure modes

- **Inputs:** a lost down range in the climb: the time limit lands the drone,
  with ADR-0019's slow descent if the range is still unusable. A target too low
  fails the program's first take-off, on the mock too.
- **Backups:** the firmware's 2 s cut if ticks stop (ADR-0048).
- **Never:** the initial climb runs past its time limit; a command hands over
  inside the bad-flow zone.
- **Always eventually:** the motors stop (ADR-0048).

## Consequences

- **Risks I accept knowingly:**
  - The time limit counts from the take-off, so a slow spin-up or a slow climb
    (battery sag) lands the drone too.
  - An ignored command shows only in later snapshots (as ADR-0039).
  - A taken-over flight's level descent starts at 0.30 m: the cap's tilt-drift
    risk (ADR-0048).
  - Without the flashlight, the settle height may be higher or the cap may
    trip: that's what session 2 measures.
- As built: the level final descent's time limit uses its own 0.2 m/s; the
  climb to the target is a `go_to` at the estimated x and y; a land during a
  landing doesn't restart it (a landing approach would climb back up).
- Glossary: *Final descent height* and *Initial climb* reworded (proposed for
  my OK).

## Firmware sources (firmware 2026.08)

- A setpoint stops the high-level planner, and a stopped planner commands the motors off once the stream is released: `commander.c` 88, `crtp_commander_high_level.c` 359-368.
- The planner plans a command from the current estimate: `crtp_commander_high_level.c` 689-693.
- The altHold setpoint (type 4) and its packet layout: `crtp_commander_generic.c` 70, 364-392.
