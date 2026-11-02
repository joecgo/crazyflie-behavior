# 0037: Disconnecting doesn't disarm; the Crazyflie adapter logs whether the drone arms itself

- **Status:** Accepted
- **Date:** 2026-11-02
- **Origin:** AI recommendation accepted (no disarm, and the log line at connect). Turning off auto-arming in our own firmware build: my idea, deferred to hide-and-seek.

## Context

Backlog #37: the hover test ends if the drone doesn't report armed within
2 s ([ADR-0033](0033-field-tests-choose-their-failure-rule.md)), and
`disconnect()` never disarms, so a drone that arms just after would stay armed
when the link closes. Checked in the firmware source (`master`, 2026-11-02:
`supervisor.c`, `supervisor_state_machine.c`, `platform_defaults.h`, Bitcraze's
arming doc):

- **Stock Crazyflie 2.1+ firmware arms itself** once its pre-flight checks
  pass (auto-arming, a build setting). cflib reports it as `is_auto_armed`.
- **Armed alone doesn't spin the motors:** the 2.1+'s idle thrust is 0, and
  with the link closed nothing sends setpoints.
- **A disarm doesn't last:** the supervisor drops back to "pre-flight checks
  not passed", the checks pass again, and auto-arming re-arms it. The 30 s
  pre-flight timeout (an armed drone that doesn't take off) ends the same way.

## Options considered

- **A. No change:** `disconnect()` doesn't disarm.
- **B. `disconnect()` disarms:** right if the firmware ever requires
  arming, but on stock firmware a safety-looking command with no effect.
- **C. With A: log at connect whether the drone arms itself,** decoded from
  the drone status the adapter already streams (ADR-0021).
- **D. Turn auto-arming off in our own firmware build:** a disarm then
  holds, and the drone ignores flight commands until an arm request. But it's
  our first custom firmware (ADR-0022 kept stock), with no check in
  continuous integration, and the arm request comes from our code too, so it
  isn't a barrier independent of our code.

## Decision

A and C. On stock firmware a disarm is undone at once, and an armed drone
with no commands stays still, so B adds nothing. C turns this source check
into evidence: the bench program's log shows which firmware behavior the
drone really has. D waits for hide-and-seek, where a child handles a landed
drone: backlog #5(h), weighed there alongside physical barriers.

## Failure modes

- **Inputs:** the drone status is always there to log: `connect()` returns
  only once every telemetry value has arrived (ADR-0031).
- **Backups:** the firmware's pre-flight timeout is no backup on stock
  firmware: auto-arming re-arms the drone.

## Consequences

- To build: the Crazyflie adapter logs the auto-arming bit once at connect,
  with tests. Auto-arming stays inside the adapter; behaviors never see it.
- The hover test's arm request is redundant on stock firmware and stays, for
  firmware that requires arming.
- Revisit if the firmware is built with `CONFIG_MOTORS_REQUIRE_ARMING` (for
  example for a Crazyflie Brushless), or if the bench log contradicts the
  source.
- The cflib primer notes auto-arming. Backlog #37 is closed; option D goes
  into #5(h).
