# 0039: The adapter decides whether the drone may be flying; hover on the floor does nothing

- **Status:** Accepted. Amends [ADR-0030](0030-minimal-safety-layer-for-first-flight.md): the safety layer no longer refuses hover and land on the floor.
- **Date:** 2026-11-02
- **Origin:** AI recommendation accepted (option A, which backlog #8 already suggested). Splitting this piece off from the rest of #8: mine.

## Context

Two definitions of "may be flying" disagreed. The safety layer's `judge()`
and failsafe use only the drone status (ADR-0030). The Crazyflie adapter's
`_may_be_flying()` (ADR-0032) also knows what it sent: for 1 s after a
take-off the status doesn't show flying yet, and for 2 s after our own motor
stop it still does. Three gaps follow:

1. In the take-off grace period, `judge()` refuses a land request and the
   failsafe sends no landing; only the shutdown after a failed pre-check
   lands the drone.
2. In the 2 s after touchdown, `judge()` approves a hover, and the adapter's
   `hover()` sends a `go_to` at floor height: the motors of an armed drone on
   the floor spin up. The operator's "hover" key (ADR-0027) would hit this.
3. The failsafe skips `judge()` and repeats the status test itself.

## Options considered

- **A. The adapter decides.** `judge()` approves hover and land whatever the
  status says; the failsafe always requests land; `hover()` gets a floor
  check like `land()`'s.
- **B. The safety layer decides,** from a "may be flying" value the adapter
  publishes in the snapshot. Puts what was sent into the snapshot and the
  drone interface, and the adapter still needs it for `disconnect()`.
- **C. Only the floor check in `hover()`.** Fixes gap 2, leaves 1 and 3.

## Decision

Option A.

- `judge()` approves `Hover` and `Land` without checking the drone status.
  Arm and take-off keep their status rules.
- The failsafe always puts `Land` in the movement slot, and its log no longer
  says "no landing sent".
- The Crazyflie adapter's `hover()` does nothing on the floor (not "may be
  flying"), logged once per streak. `land()` already just stops the motors
  there.

## Failure modes

- **Inputs:** a missing or stale drone status counts as flying (ADR-0032), so
  hover and land fly when unsure.
- **Backups:** the kill switch (ADR-0027) if a landing holds on the floor.
- **Never:** a hover or land spins up the motors of an armed drone our code
  knows is on the floor; a land request refused during the take-off grace
  period.
- **Always eventually:** a failed pre-check lands a drone that may be flying.

## Consequences

- **Risk I accept knowingly:** an approved hover can mean the adapter did
  nothing. Approved never meant done (ADR-0025); behaviors see it only in
  later snapshots.
- The take-off rule still uses the status, so a take-off within 2 s after
  touchdown is refused. That's the safe direction; it stays in backlog #8.
- To build, with tests: `judge()` approving hover and land on the floor, the
  failsafe landing during the take-off grace period, `hover()` doing nothing
  on the floor. The mock adapter's hover and land are already harmless on the
  floor.
- ADR-0032's note on the two definitions is resolved. The rest of #8 stays
  open.
