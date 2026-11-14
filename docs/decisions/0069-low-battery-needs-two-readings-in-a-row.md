# 0069: The low-battery limit needs two readings in a row; the sag value stays 0.42 V

- **Status:** Accepted. Amends [ADR-0051](0051-battery-flight-limit-and-take-off-limit.md) , [ADR-0030](0030-minimal-safety-layer-for-first-flight.md) and [ADR-0041](0041-failsafe-tests-inject-a-fault-into-the-pre-check.md): the safety pre-check's low-battery rule, the snapshot carries the previous battery reading, and the forged low battery drone forges both readings.
- **Date:** 2026-11-13
- **Origin:** Mixed. Two readings in a row, with the snapshot carrying both: AI recommendation accepted. Keeping the 0.42 V sag value: mine, over the AI's 0.5 V.

## Context

One battery reading under 3.2 V fails the safety pre-check. At spin-up the
battery dips 0.55-0.73 V for about 0.1-0.2 s: under 3.2 V in all six
take-offs of First flight 4 and three of eight in First flight 5 (by the
10 Hz diagnostic samples, from 3.84 V at rest and below). The battery
reading the pre-check uses comes once a second. Today's programs take off
just after one (connect ends on it), so the next arrives past the dip. A
take-off at any other moment, such as a relaunch in hide-and-seek, would
read the dip about 1 time in 5 to 10. One reading at the limit while braking
into the final descent ended First flight 4's Hover tick loop.

## Options considered

- **A. Two readings in a row, the snapshot carrying the last two (chosen):**
  the pre-check stays a function of the snapshot alone.
- **B. Skip the check for a short time after a take-off.**
- **C. A faster battery block:** sees the dip more often, not less.
- **D. A higher take-off limit.**
- **E. Leave it:** the programs' timing misses the dip, by luck.

## Decision

Option A.

- The safety pre-check fails on low battery only when the latest two
  battery readings are both under 3.2 V. The snapshot carries the previous
  reading next to the latest. With one reading only (just after connect), it
  decides alone. A reading that isn't finite fails at once, as before.
- A previous reading that isn't finite counts as low, so with a low latest
  reading the check fails at once (decided 2026-11-13, while building).
- The forged low battery drone forges both readings, so the failsafe tests
  fire as soon as their trigger does.
- The take-off limit stays 3.62 V: the sag value stays 0.42 V, judged on one
  reading before the motors spin.

## Failure modes

- **Inputs:** a real low battery lands about 1 s later, on readings up to
  2 s old. A lost reading: the two latest received count. A missing previous
  reading: the latest decides alone. A previous reading that isn't finite:
  counts as low.
- **Backups:** none independent (ADR-0051).
- **Never:** a failsafe test's forged battery waits for a second reading.
- **Always eventually:** two readings in a row under 3.2 V in flight end with
  the drone landed and its motors off.

## Consequences

- **Risks I accept knowingly:**
  - The sag value stays 0.42 V, as I chose in ADR-0051 over the AI's 0.51 V.
    The hovers have since sagged 0.42-0.49 V, so a take-off at the 3.62 V
    take-off limit can hover at 3.13-3.20 V and be landed by the failsafe
    about 2 s into the flight: the safe direction, but a short flight.
  - A real low battery lands about 1 s later than before, on a margin
    ADR-0051 already called none.
  - A braking dip that lasts over a second still lands the drone.
- Code: the snapshot's previous battery reading, both adapters, the safety
  pre-check, the forged low battery drone, and tests (two in a row, one
  alone, one low then one high, the forged drone forging both). Safety layer:
  an Extra-level review.
- Backlog #91 keeps its open part: whether the take-off limit should scale
  with the planned flight's length.
- Glossary: *Low-battery limit* reworded (my OK, 2026-11-13).
