# 0051: Land below 3.2 V in flight; take off only above 3.2 V plus the sag

- **Status:** Accepted. Amends [ADR-0030](0030-minimal-safety-layer-for-first-flight.md): the low-battery limit is set, and its firmware backup is corrected. Closes backlog #50. Amended by [ADR-0069](0069-low-battery-needs-two-readings-in-a-row.md), 2026-11-13: the in-flight limit needs two low readings in a row.
- **Date:** 2026-11-05
- **Origin:** Mixed. Landing at 3.2 V and a separate take-off limit set by a sag value: mine, over the AI's recommendation to keep 3.40 V until measured. A sag value of 0.42 V: mine, over the AI's 0.51 V. Judging the limit on the take-off request, checking the hardware docs first and a planned test below 3.37 V: AI recommendations accepted.

## Context

On 2026-11-04 the pre-check's placeholder limit of 3.40 V landed four of six
flights, three within 2 s of take-off. Computed from the logs: the reading
drops 0.32-0.42 V one second after take-off and 0.48-0.51 V by 20 s (sag).
The first three flights started at 3.77-3.79 V at rest, 10-20% in the
firmware's charge table. On a full charge, flight lasted about 1.5 min before
3.40 V, and Hover 1 landed at 3.45 V and read 3.88 V at rest 4 min later.

Checked in firmware 2026.08 (`pm_stm32f4.c`, `platform_defaults_cf2.h`): the
firmware's low state is 3.2 V for 5 s in a row on the same reading, with no
allowance for sag. It lights the red M1 LED and beeps, and Bitcraze's
getting-started guide says that LED means it's time to land. The 3.0 V
shutdown is compiled out by default (`CONFIG_PM_AUTO_SHUTDOWN`), and the radio
chip sends single raw samples with no cutoff (`crazyflie2-nrf-firmware`
2026.08, `src/pm.c`). Bitcraze's datasheet states no minimum battery voltage.

## Options considered

- **A. Keep 3.40 V, always charge fully:** no code. About 1.5 min per charge,
  and a half-charged battery still trips at take-off.
- **B. A take-off limit on the resting voltage, judged on the take-off
  request, plus the flight limit in the pre-check:** staged (3.40 V in flight
  until measured) or both now.
- **C. Filter the reading:** the drop isn't noise, so a filter doesn't stop the
  trip at take-off, and it delays a real failsafe.
- **D. Use the firmware's low state:** 3.2 V plus 5 s, later than ours.

## Decision

Option B, both now.

- **Flight limit 3.2 V** (`LOW_BATTERY_VOLTAGE`), in the safety pre-check as
  today: Bitcraze's own time-to-land voltage. At 3.40 V, charge went unused.
- **Take-off limit: the flight limit plus a sag value of 0.42 V, so 3.62 V,**
  the largest drop measured one second after take-off. The safety layer
  refuses a take-off request below it. That's judged once, on a reading taken
  before the motors spin. Not in the pre-check by drone status: its "flying"
  lags after take-off, so the pre-check would apply 3.62 V to the loaded
  voltage and land every flight. A refused take-off ends the Hover and Failsafe
  tests with the reason logged (ADR-0033).
- The first flights below 3.37 V, the lowest reading so far, are a planned
  field test over the mat that records the voltage down to the limit.

## Failure modes

- **Inputs:** a missing or stale battery reading fails the pre-check first
  (ADR-0030); a take-off judged without one is refused. A brief dip below
  3.2 V lands the drone at once (the safe direction). The resting voltage
  rises for minutes after a flight, so a weak battery can pass 3.62 V after a
  rest; the flight limit stays the guard.
- **Backups:** none independent. The firmware's low state is at the same
  voltage, 5 s later, and only signals. Manual: the kill switch and rescue landing.
- **Never:** a take-off approved below 3.62 V.
- **Always eventually:** a reading below 3.2 V in flight ends with the drone
  landed and its motors off (ADR-0030).

## Consequences

- **Risks I accept knowingly:**
  - No margin: the landing starts at Bitcraze's time-to-land voltage, on a
    reading up to 1 s old, and Hover 1's landing took 2.0 s.
  - From 3.37 V to 3.2 V nothing is measured: how fast the voltage falls, or
    whether the drone can still climb. Bitcraze doesn't document where the
    electronics lose power, and the schematic wasn't checked.
  - The drop keeps growing after the first second, so a battery just above
    3.62 V may reach 3.2 V within seconds of take-off.
- ADR-0030's backup line was wrong: the firmware doesn't shut down at 3.0 V on
  a default build (mistakes log, 2026-11-05).
- ADR-0041 and ADR-0049: the forged fault becomes 3.0 V (the limit minus
  0.2 V). A battery below 3.62 V is refused on the floor instead of beating
  the fault in the air.
- Backlog: the limits after the planned test, and the firmware's low state as
  a backup (#57).
- Glossary: *Sag*, *Resting voltage*, *Low-battery limit*, *Take-off limit*
  are new, and *Crazyflie* is reworded (proposed for my OK).
