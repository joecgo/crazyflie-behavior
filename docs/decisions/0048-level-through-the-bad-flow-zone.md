# 0048: Take-off and landing cross the bad-flow zone level, above a height found during take-off

- **Status:** Accepted. Amends [ADR-0019](0019-final-descent-when-touchdown-unconfirmed.md): the final descent runs on every landing, held level by a setpoint stream; its slow high-level descent stays only as a fallback. Amends [ADR-0032](0032-landing-with-a-go-to.md): the landing's `go_to` ends above the bad-flow zone, not at the floor. Amends [ADR-0011](0011-mock-models-setpoint-timeout.md): take-off and landing stream setpoints in their level parts. Amended by [ADR-0049](0049-failsafe-low-fires-its-fault-during-the-initial-climb.md) (no landing approach during the initial climb), [ADR-0055](0055-take-off-and-landing-update-each-tick.md) (where the level parts run) and [ADR-0056](0056-adr-0048-as-built.md) (low targets, the climb time limit, commands while level, the field-test plan), 2026-11-07. Amended by [ADR-0054](0054-a-fresh-estimate-for-every-take-off.md), 2026-11-08: the settle height also needs a low velocity uncertainty, so the drone can take off without flow.
- **Date:** 2026-11-05
- **Origin:** Mixed. Moving only vertically through the zone, a speed instead of height targets, measuring the zone during take-off, the 5 cm margin, and trusting the setpoint stream: mine. Holding roll and pitch level, the horizontal speed estimate as the measure, its threshold, the 15 cm minimum, the cap, the fallback and refusing low take-off targets: AI recommendations accepted.

## Context

Near the floor the Flow deck's flow is wrong, so the estimated horizontal
speed is too (backlog #54). The landing's `go_to` and the high-level take-off
hold position by that estimate, so the controller chases a speed that isn't
there. In the Hover test I saw a 4-8 cm slide before the propellers stopped,
and the drone seemed to shift sideways at take-off and hover off-centre.
Computed from the three take-offs: the speed estimate reached 0.44-0.77 m/s
near the floor, even with a flashlight, and the estimated position moved
8-12 cm. One likely cause, whatever the light: the firmware's flow model
treats any height under 0.1 m as 0.1 m (`mm_flow.c` 64-65, firmware 2026.08),
overstating the speed up to 4 times at the floor.

## Options considered

- **A. High-level moves all the way (today):** they keep going if ticks stop,
  but hold position by the false speed.
- **B. Steering's velocity command with zero horizontal speed:** holds the
  *estimated* speed at zero, so it chases the same false speed.
- **C. Level, with a height target lowered each tick** (cflib's zDistance
  setpoint): ignores the horizontal estimate, but its speed depends on the
  height estimate.
- **D. Level, with a vertical speed** (the firmware's altHold setpoint):
  ignores the horizontal estimate (`controller_pid.c` 124-127); the height
  controller tracks the vertical speed estimate.

## Decision

Option D through the zone, both ways, with the zone's top measured on every
take-off. Moving only vertically, the drone doesn't need the flow there.
Steering will rely on the same setpoint stream, so I trust it until a test
shows otherwise.

- **Initial climb:** take-off starts level, climbing at 0.2 m/s. The
  **settle height** is the down range where the horizontal speed estimate
  first goes under 0.15 m/s and then stays under it for 0.2 s. Held level, the
  drone barely moves sideways, so a large estimated speed is estimate error.
- **Final descent height:** the larger of 0.15 m and the settle height plus
  0.05 m, by the down range. The 5 cm covers estimate error and small light
  differences; the landing spot is assumed lit like the take-off spot.
- The initial climb ends at the final descent height. A high-level move then
  climbs to the target, holding the current x and y, not the take-off point
  (going back there would repeat the shift).
- **Cap:** the final descent height is at most 0.30 m. If the speed hasn't
  settled by 0.25 m, the flow is bad there, so the drone lands at once.
  A take-off target at or below 0.30 m is refused.
- **Landing approach** (was the planned landing): a `go_to` down to the final
  descent height at the estimated position. When it ends, or sooner if the
  down range reaches that height, the **final descent** starts: level,
  descending at 0.2 m/s, until touchdown is confirmed or its time limit
  (ADR-0019).
- If the down range isn't usable when the final descent should start, it
  falls back to ADR-0019's slow high-level descent: a level descent from an
  unknown height could drift for seconds.
- Hand-over to the high-level commander: the last level setpoint, then the
  high-level command, then the release (`notify_setpoint_stop`). A setpoint
  stops the high-level planner, and a stopped planner commands the motors off
  once the stream is released (`commander.c` 88,
  `crtp_commander_high_level.c` 359-368).
- Placeholders to verify in flight: 0.2 m/s, 0.15 m/s for 0.2 s, 0.15 m,
  0.05 m and 0.30 m.

## Failure modes

- **Inputs:** a wrong height estimate ends the landing approach high or low;
  the down range starts the final descent instead. Bad flow during the
  initial climb raises the settle height until the cap lands the drone. An
  unusable down range: ADR-0019's descent. A darker landing spot: the margin
  may not cover it.
- **Backups:** if the stream stops, the firmware levels the drone after
  0.5 s, keeping its last vertical speed, and cuts the motors and locks after
  2 s (`supervisor.c`). That doesn't depend on our program.
- **Never:** the drone holds position by flow inside the bad-flow zone; the
  release cuts the motors at the top of the initial climb.
- **Always eventually:** the motors stop: at confirmed touchdown, at the final
  descent's time limit, or 2 s after the stream stops.

## Consequences

- **Risks I accept knowingly:**
  - No position hold while level: a 1° tilt error pushes the drone sideways
    at about 0.17 m/s², about 4 cm from 0.15 m and up to about 17 cm from the
    cap.
  - The estimate keeps the offset it builds in the zone; the drone stays put.
  - Trusting the stream: a hang or a lost link in a level part drops the drone
    within 2 s, from up to about 0.7 m during the initial climb (it keeps
    climbing until the cut).
  - A hang during the landing approach leaves the drone holding at the final
    descent height until ticks resume, the kill switch or a flat battery
    (backlog #26). In the final descent, ADR-0032's risk (motors spinning on
    the floor after a hang) no longer applies: the firmware stops them.
- The old take-off logs can't predict the settle height: the speed dipped
  under 0.1 m/s for only 1-2 ticks at 0.08-0.14 m, then rose as the take-off
  pulled the drone back. The next flight test tries the initial climb alone
  first.
- cflib has no altHold method, so the adapter builds the packet (type 4,
  `<Bffff`: roll, pitch, yaw rate, vertical speed; `crtp_commander_generic.c`
  70, 370), guarded by the firmware pin (ADR-0047) and a test of its bytes.
- The adapter logs the settle height, the final descent height and confirmed
  touchdown. Backlog #51 and #54 are closed; #52 changes (Failsafe low's
  0.1 m can't fly); #56 records the adapter's existing release-first order.
  The mock adapter needs the level parts too (ADR-0011, backlog #34).
- Glossary changes, proposed for my OK: *Landing approach* replaces *Planned
  landing*; *Initial climb*, *Settle height* and *Final descent height* are
  new; *Final descent*, *Landing phase* and *Bad-flow zone* are reworded.
