# 0077: The initial climb ends at a fixed 0.15 m and hands over only with flow; no settle detector, no climb-speed flag

- **Status:** Accepted. Supersedes [ADR-0059](0059-initial-climb-speed-set-per-hover-run.md) (the hover program's climb speed and the scaled time limit). Amends [ADR-0048](0048-level-through-the-bad-flow-zone.md) (the settle height, the final descent height's formula and the cap), [ADR-0054](0054-a-fresh-estimate-for-every-take-off.md) (the flow check at the top of the initial climb), [ADR-0056](0056-adr-0048-as-built.md) (the settle hold, the final descent height without a take-off, the lowest take-off target and the time limit) and [ADR-0070](0070-initial-climb-default-0-4-m-per-s.md) (0.4 m/s becomes the only climb speed). Closes backlog #104, #89 and #98.
- **Date:** 2026-11-17
- **Origin:** Mixed. Removing the settle detector; option A over the AI's B (a speed check as well); 0.15 m as the lowest take-off target, over the AI's 0.25 m; a fixed 1.5 s time limit, over the AI's 1.375 s scaled with the speed; and removing `--climb-speed`, over the AI's narrowing it to 0.2-0.4 m/s: mine. The fixed 0.15 m, and taken-over flights landing from it: AI recommendations accepted.

## Context

ADR-0048 measures the settle height on every take-off: the down range where
the horizontal speed estimate stays under 0.15 m/s for 0.2 s with a low
velocity uncertainty. The final descent height is that plus 5 cm (0.15-0.30
m), and no settle by 0.25 m lands the drone (the cap). Across every flight log
(2026-11-07 to 11-14), the 39 climbs that settled did so at 0.101-0.144 m
(final descent heights 0.151-0.194 m). The cap fired 4 times, each time on
real sideways drift, not bad flow (backlog #68). At the first down range
reading at or above 0.15 m, in all 41 climbs that reached it: the velocity
uncertainty was 0.011-0.014 m/s (in the 35 that logged it), and the speed
estimate was 0.022-0.178 m/s, with the four over 0.15 m/s being the cap
landings. Computed by `drafts/104/handover.py` and `reach_time.py`.

## Options considered

- **A. A fixed final descent height, with only the velocity uncertainty checked there (chosen).**
- **B. A, plus a speed check:** a speed estimate over 0.3 m/s also lands. A
  rough catch for wrong flow that reads as speed. It would have fired 0 times
  in 41 climbs.
- **C. Climb until flow arrives, up to a cap:** take-offs in light where flow
  arrives above 0.15 m. Never seen, and more climbing that nothing brakes.
- **Keep the settle detector with a looser speed:** its height mostly
  measured its own 0.10 m start, the hold and drift, not the light.

## Decision

The settle detector hasn't earned its complexity, so it goes.

- **Initial climb:** level, always at 0.4 m/s. I don't plan to change the
  take-off speed, so the hover program's `--climb-speed` and the adapters'
  climb-speed setting go. The climb ends at the first fresh down range
  reading at or above the final descent height. There, a fresh velocity
  uncertainty under 0.03 m/s (flow, ADR-0060) hands over to the high-level
  climb in ADR-0048's order. A missing, stale, negative or non-finite one, or
  one at 0.03 m/s or more, lands the drone as ADR-0049 lands it during the
  climb, with no landing approach. The safety pre-check still skips the
  velocity uncertainty during the climb.
- **Final descent height:** a fixed 0.15 m for every landing, taken-over
  flights too (was the cap, 0.30 m). The landing approach aims at 0.10 m
  (ADR-0068).
- **Lowest take-off target:** a target at or below the final descent height
  is a bug (`ValueError`, ADR-0056), so one constant sets both.
- **Time limit:** the drone lands if the initial climb hasn't ended 1.5 s
  after the take-off was sent (was 1.75 s). Since the thrust base (ADR-0061),
  the 23 climbs at 0.4 m/s reached 0.15 m 0.57-0.68 s after the send.
- Placeholders: 0.15 m and 1.5 s.

## Failure modes

- **Inputs:**
  - A missing or stale down range: no hand-over, and the time limit lands the
    drone (ADR-0019's slow descent if the range is still unusable).
  - A NaN or infinite down range: no hand-over, as if missing (added in the
    project review). The landing after it doesn't check for one yet (backlog
    #123).
  - A down range that reads high: the climb hands over below 0.15 m, as
    before.
  - A missing, stale, negative or non-finite velocity uncertainty: counts as
    no flow, so the drone lands (negative values and −inf added in the
    second project review). An old one gets its own log line: it may be a telemetry
    stall, not darkness.
  - A low uncertainty without flow, just after an estimate reset (#74): the
    climb hands over without flow, and the in-flight pre-check lands the
    drone once the uncertainty passes ADR-0064's limit.
- **Backups:** that in-flight check reads the same estimator, so it isn't
  independent; the settle detector had the same gap (ADR-0054). The
  firmware's 2 s cut if the ticks stop (ADR-0048).
- **Never:** a hand-over below 0.15 m by the down range, or without a fresh
  velocity uncertainty under 0.03 m/s; an initial climb past 1.5 s.
- **Always eventually:** a hand-over or a landing within 1.5 s of the
  take-off, and the motors stop (ADR-0048).

## Consequences

- **Risks I accept knowingly:**
  - Wrong flow that the firmware trusts and that reads as speed isn't caught
    at take-off, and no check catches it in flight. The settle detector's cap
    caught it above 0.15 m/s. To verify in the darkest light hide-and-seek
    is played in (backlog #116).
  - A take-off target just above 0.15 m hovers where the hand-over sag
    happens (#69). In First flight 3, before the thrust base, the drone fell
    7.8 cm, which from 0.15 m reaches the bad-flow zone with position hold
    on. Since then the sag has been at most 1 cm.
  - Light where flow arrives above 0.15 m lands the drone, where option C
    would climb on to find the flow.
  - A lost down range climbs level to about 0.4-0.45 m before the time limit
    (from ADR-0070's lift-off at 0.37-0.53 s).
- Easier: the level part ends lower than the settle detector's up to 0.19 m,
  so less drift that nothing brakes (#68); the cap's needless landings go;
  the mock adapter needs no settle model, and its dark floor still lands a
  drone with no flow at 0.15 m.
- Code: `bad_flow_zone.py`, both adapters, `make_drone`, the
  hover program, the take-off rule's docstring and the pre-check's comment in
  `safety_layer.py`, and their tests.
- Glossary: *Settle height* deprecated; *Initial climb* and *Final descent
  height* reworded (approved 2026-11-17).
