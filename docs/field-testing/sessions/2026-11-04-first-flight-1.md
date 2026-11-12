# 2026-11-04-first-flight-1

> Flown 2026-11-04: the Bench; Failsafe low twice and Failsafe high once,
> each cut short by the real battery; after charging, Failsafe high with the
> forged fault, and Hover twice (60 s, then 19 s on a low battery). The
> results below are Joe's to write.

A session is one trip with one or more field tests, flown in order. Each
field test has its own log in [`../field-tests/`](../field-tests/).

- **Milestone:** First flight, session 1
- **Environment:** [Living room](../environments/living-room.md), hide-and-seek launch point; the Hover in the [kitchen](../environments/kitchen.md), center

## Plan

Each test needs the ones before it to pass. If one fails, stop and write it
up before flying the next (README, "Sessions and test logs").

1. [Bench](../field-tests/2026-11-04-first-flight-1-bench.md)
2. [Failsafe low](../field-tests/2026-11-04-first-flight-1-failsafe-low.md)
3. [Failsafe high](../field-tests/2026-11-04-first-flight-1-failsafe-high.md)
4. [Hover](../field-tests/2026-11-04-first-flight-1-hover.md)

## Results
*From the operator or the recordings, never from an AI. One line per test: passed, failed or not flown.*

Joe's verdicts, said on 2026-11-05: all four passed, because even though the
Flow deck and battery issues threw the drone around a little, the failsafe
worked, the hover worked and the bench worked.

- Bench: passed. Findings: backlog #47 to #53.
- Failsafe low: passed. The real low battery's failsafe landed it both times;
  the forged fault never ran (#52 reworks the test). Findings: #50, #51, #52.
- Failsafe high: passed. Findings: #50, #51.
- Hover: passed. Findings: #48, #50, #51, #54.

## Next session
*What the results decide: session 2 of First flight, or the milestone is done.*

Joe, 2026-11-05: First flight needs a session 2. All four tests are flown
again after the code changes, testing the new take-off and landing
([ADR-0048](../../decisions/0048-level-through-the-bad-flow-zone.md)).
The Hover passes only if the landing is within 3 cm of the take-off point
(session 1: about 4 cm). The Bench passes only once all the data its
criteria ask for has been collected.

