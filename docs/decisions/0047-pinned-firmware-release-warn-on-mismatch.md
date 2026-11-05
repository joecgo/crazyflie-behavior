# 0047: The project pins a Crazyflie firmware release; the adapter warns on a mismatch

- **Status:** Accepted
- **Date:** 2026-11-04
- **Origin:** Mixed. Updating before the bench test, and warning only (over the AI's recommendation to refuse to connect): mine. Pinning a release: AI recommendation accepted.

## Context

The drone arrived with firmware 2024.10. The ADRs that rely on firmware
behavior (0011, 0017, 0023, 0032, 0037) were checked against the firmware's
`master` branch in October and November 2026, two years newer. A bench test on
2024.10 would test assumptions the code doesn't make.

On 2026-11-04 the drone was flashed with release 2026.10 using `cfclient`
2026.8.1. It now reports firmware 2026.08 (release 2026.10 changed only the
AI-deck), unmodified, protocol version 12. cflib is 0.1.34.

## Options considered

- **A. Pin in the docs only.** No code check: an accidental update goes
  unnoticed.
- **B. Pin; the Crazyflie adapter refuses to connect on a mismatch.** Safety
  assumptions can't silently drift, but a change in how the version is
  reported blocks every program until fixed.
- **C. Pin; the Crazyflie adapter warns on a mismatch.** Never blocks a
  session; the warning can be missed.

## Decision

Option C.

- The pinned release is **2026.10** (Crazyflie firmware **2026.08**).
  Firmware claims in ADRs are checked against the `2026.08` tag, not `master`.
- On connect, the Crazyflie adapter reads the firmware version and logs it.
  It logs a warning if the version isn't the pinned one, if the firmware
  reports itself modified, or if no version arrives. Connecting carries on.
- Changing the pin takes a new ADR, a re-check of the firmware-dependent ADRs
  and a new bench test.
- Flashing uses `cfclient` in its own virtual environment outside the repo,
  at the version matching the release. It isn't a project dependency.

## Failure modes

- **Inputs:** another version, a modified build or no reply: a warning, and
  connecting carries on.
- **Backups:** none.
- **Never:** connecting to unpinned firmware without a warning in the log.
- **Always eventually:** none new.

## Consequences

- **Risk I accept knowingly:** the warning can be missed right before a
  flight, so the drone could fly on firmware whose setpoint timeout or
  auto-arming differ from what the safety layer assumes.
- Re-checked 2026-11-04 by comparing the `2026.08` tag with `master`: none of
  the files ADR-0011, 0017, 0023, 0032 and 0037 rely on changed (supervisor,
  commander, high-level commander and planner, the Flow deck and Multi-ranger
  drivers, the sound driver; `uart2.c` was only refactored). One difference
  that matters on 2026.08: a full radio receive queue asserts (backlog #47).
- Code to build, with tests: reading the version within ADR-0029's time
  limits; the matching version logged; a warning for another version, a
  modified build, or no reply.
