# 0032: Landing is a go_to down to the floor; our touchdown check stops the motors

- **Status:** Accepted. Amends [ADR-0012](0012-landing-confirms-touchdown.md): its landing assumed the firmware keeps the motors running after it lands.
- **Date:** 2026-10-31
- **Origin:** My call: keep in line with ADR-0012 and ADR-0019, which already said the touchdown check decides when the motors stop. Claude had recommended trusting the firmware's landing instead.

## Context

ADR-0012 and ADR-0019 assumed that after the firmware's landing, the motors
keep running until the touchdown check stops them. In the firmware source,
when a landing trajectory finishes, the high-level commander goes idle and
switches the motors off itself (`planner.c` lines 114-120,
`crtp_commander_high_level.c` lines 359-369, in today's source, checked
2026-10-31; backlog #31 found the same in releases 2022.01 to 2025.02). So the
firmware could stop the motors above the floor after a landing planned from a
wrong height, and ADR-0019's final descent would spin them up again
afterwards. And `disconnect()` landed
whenever a take-off had been sent, even if the drone never left the floor,
where a move down spins an armed drone's motors up.

## Options considered

- **A. Trust the firmware's landing,** and keep the touchdown check only as a
  logged cross-check. Gives up ADR-0012's guarantee and retires ADR-0019's
  final descent.
- **B. Land with a `go_to` down to the floor.** A `go_to` keeps holding its
  end point (`planner.c` lines 119-120), so the motors stay on until the
  touchdown check stops them, as ADR-0012 and ADR-0019 intended.

## Decision

Option B. A landing is a smooth `go_to` to height 0 at the drone's estimated
position, ending at rest (`planner.c` lines 206-208); the touchdown check and
the final descent stay as ADR-0019 designed them. A landing is only sent when
the drone may be flying: its status says flying, or a take-off was sent too
recently for the status to show it. A missing or old status counts as
unknown, so the drone lands: stopping the motors on a guess could cut them in
mid-air. Otherwise the motors are just stopped.

## Failure modes

- **Inputs:** a wrong height estimate ends the `go_to` above the floor, still
  holding with the motors on; the final descent continues down. A failed
  down sensor ends at the final descent's time limit (ADR-0019).
- **Backups:** the supervisor won't step in: it counts the drone as flying
  while any motor runs above idle (`supervisor.c` lines 276-300).
- **Never:** the motors stop in mid-air because a trajectory ended; a landing
  spins up an armed drone that's on the floor.
- **Always eventually:** the motors stop, on confirmed touchdown or at the
  final descent's time limit.

## Consequences

- **Risk I accept knowingly:** only our program stops the motors. If it hangs
  at touchdown, they keep spinning against the floor until the kill switch
  (ADR-0027) or a flat battery stops them. The firmware's landing would have
  stopped them anyway.
- After our own stop, the drone status keeps saying flying for 2 s
  (`supervisor.c`, `IS_FLYING_HYSTERESIS_THRESHOLD`), so "may be flying" also
  requires that we haven't stopped the motors since the take-off.
- The take-off grace period (1 s) is a placeholder to measure at the bench.
  VERIFY at the bench how the drone settles at the floor while the `go_to`
  holds it there.
- The safety layer's `judge()` still refuses a land request until the status
  says flying (ADR-0030), so it and the adapter define "may be flying"
  differently during the take-off grace period (backlog #8).
- Backlog #31 is closed.
