# 0041: The Failsafe low and Failsafe high tests inject a fault into the safety pre-check

- **Status:** Accepted. Amended 2026-11-02: Failsafe high flies at 0.5 m, the Hover test's height, instead of 0.3 m, so the failsafe is proven at the height Hover then flies. Edited in place rather than superseded, since the program isn't built yet. Accepted risk: a bigger step from 0.1 m, with no middle height. Amended 2026-11-03: the mechanism of the fault, and how the program judges the test, are recorded below as built.
- **Date:** 2026-11-02
- **Origin:** Mixed. A failsafe test before the Hover test, from 0.1 m and then 0.3 m, run by one program, and the names Failsafe low and Failsafe high: mine. Raising Failsafe high to the Hover test's 0.5 m, and amending this record in place: mine. Injecting a fault into the pre-check (option A), so the drone lands itself: my choice, after the AI first described the alternative (the program exits and the rescue landing takes over) wrongly as an automatic failsafe. How: the AI recommended a wrapper around the drone that forges a low battery; I chose it.

## Context

The field-testing README gets two tests before Hover: the drone takes off to
0.1 m (Failsafe low) or 0.5 m (Failsafe high) and the failsafe landing
([ADR-0030](0030-minimal-safety-layer-for-first-flight.md)) brings it down.
Something has to trigger it. The operator's "land now" hotkey
([ADR-0027](0027-operator-controls.md)) isn't built, and a program that exits
leaves the drone hovering for a manual rescue landing
([ADR-0038](0038-connecting-to-a-flying-drone.md)), which isn't the failsafe.

## Options considered

- **A. Inject a fault into the safety pre-check:** the test program makes the
  pre-check fail, for example by reporting stale data. The real failsafe path
  runs (pre-check fails, land). Needs a test hook somewhere.
- **B. The program exits mid-hover** and the rescue landing is run by hand:
  no safety-layer change, but it tests manual recovery, not the failsafe.
- **C. A for one test, B for the other:** more work.

## Decision

Option A. The drone landing itself on a failed pre-check is the behavior being
proven, so the test uses that path.

- One program flies both tests, taking the height (0.1 m or 0.5 m) as an
  argument.
- **The fault is a forged low battery, injected by a wrapper around the
  drone,** not by a change to the safety layer. The wrapper hands the safety
  layer a snapshot with the battery voltage below the low-battery limit after
  about 3 s of hover; every other field stays real, down range included, since
  the landing uses it ([ADR-0032](0032-landing-with-a-go-to.md)). The real
  pre-check and failsafe run unmodified, and the wrapper logs that a fault was
  injected. Options considered for this: a flag on `SafetyLayer`, or passing
  the pre-check function in. Both put a test hook inside the code that must
  never be wrong.
- **As built** (`programs/failsafe_fault.py`, `behaviors/failsafe_test.py`,
  `programs/failsafe.py`): the wrapper's `take_snapshot()` returns the real
  snapshot until the drone has hovered at the take-off height for 3 s, then a
  copy (`dataclasses.replace`; snapshots are frozen with slots, ADR-0018) with
  only `battery_voltage` replaced by 3.2 V. It logs one warning, "FAULT
  INJECTED: battery voltage forged", and passes every command on unchanged. The
  failsafe test behavior arms, takes off, hovers and waits; past a 10 s time
  limit it lands normally and the test has failed (ADR-0033's failure rule).
- **The pass is judged by the program.** A failed pre-check ends the run at once
  (ADR-0026) and the landing finishes inside `disconnect()`, so no behavior
  sees the drone land. The exit code is 0 only if the fault was injected, the
  pre-check then failed, and the test didn't fail by its own rules. That the
  pre-check failed *because of the battery* is checked by a pytest test on the
  log line, not by the program.

## Failure modes

- **Inputs:** if the injected fault never takes effect, the drone keeps
  hovering. The program has a time limit and then lands normally.
- **Backups:** the program's own landing shares its code with the test, so a
  bug in the program could hide a failed failsafe. Early flights are low over a
  soft mat, and the kill switch and rescue landing
  ([ADR-0038](0038-connecting-to-a-flying-drone.md)) are the manual backups.
  Accepted risk.
- **Never:** the fault hook reachable from a game program or behavior; a hook
  that is on by default.
- **Always eventually:** the drone lands and its motors stop.

## Consequences

- The safety layer doesn't change. An architecture test checks that only the
  failsafe program imports the wrapper. The wrapper passes commands on, so the
  test "only the safety layer sends commands" has an exemption for that one
  file, marked in ADR-0008 and ADR-0030 (amended 2026-11-03, my call on the
  AI's recommendation; closes backlog #39). Exempting all of `programs/` was
  rejected: game programs live there, and the rule must catch them. When a
  second fault is planned, fault wrappers move to a `faults/` folder with
  the exemption (backlog #44).
- The failsafe test reaches its pass through the exit code, not through the
  behavior reporting done (see "Who judges the pass" below).
- Glossary: *Failsafe low / Failsafe high*.
- **Who judges the pass (amended 2026-11-03, my call on the AI's
  recommendation; closes backlog #40 and #42):** the failsafe program, not
  the behavior. A failed pre-check ends the run at once and the failsafe
  landing finishes inside `disconnect()`, so `FailsafeTest` is never ticked
  again. Exit code 0 means the fault was injected, the pre-check then failed,
  the test didn't fail by its own rules, and the landing in `disconnect()`
  finished with the motors stopped (a landing that raises makes it 1). It
  doesn't say whether touchdown was confirmed or the final descent ran out
  its time limit ([ADR-0019](0019-final-descent-when-touchdown-unconfirmed.md)):
  the test log records that from the operator and the recording. ADR-0036's
  exit-code rule is amended to allow this.
