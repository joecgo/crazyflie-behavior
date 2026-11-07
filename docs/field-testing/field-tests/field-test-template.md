# YYYY-MM-DD-{milestone}-{session#}-{test-name}

- **Session:** [{milestone} {session#}](../sessions/YYYY-MM-DD-{milestone}-{session#}.md)
- **Test:** calibration: Bench | Sensor characterization · safety: Failsafe low | Failsafe high | Safety validation · flight: Hover | Mapping run | Hide-and-seek
- **Environment:** [{environment}](../environments/{environment}.md), {location}, {lighting setup}. Time of day / sunlight: ___
- **Git commit:** `<hash>` (must be committed before flying)
- **Hardware:** Crazyflie 2.1+, decks: Flow / Multi-ranger, battery #
- **Firmware / cflib:** {firmware version} / {cflib version}

## Goal and pass criteria
*Written before flying.*

- Goal:
- Pass if:
- Simulator prediction, if simulated:

## Pre-flight checklist

- [ ] Code committed, hash recorded above, the same commit as the session doc's mock runs
- [ ] Propellers undamaged, battery charged (voltage: ___; below 3.62 V the take-off is refused, [ADR-0051](../../decisions/0051-battery-flight-limit-and-take-off-limit.md))
- [ ] Flight area clear of people and pets
- [ ] E-stop tested on the ground this session
- [ ] Geofence configured for this space
- [ ] Recording on (telemetry + video)

## During the test
*The operator's steps, in order.*

- [ ]

## Flights

| # | What was run | Result | Data file | Notes |
|---|---|---|---|---|
| 1 | | | | |

## Observations
What happened, especially anything surprising. Include numbers.

## Sim vs real
Where the prediction matched reality and where it didn't. Optional: remove this section if there was no simulator run.

## Next
- Code changes:
- Simulator model changes:
- ADRs to write or revisit:
- Next session's goal:
