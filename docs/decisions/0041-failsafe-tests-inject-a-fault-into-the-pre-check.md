# 0041: The Failsafe low and Failsafe high tests inject a fault into the safety pre-check

- **Status:** Accepted
- **Date:** 2026-11-02
- **Origin:** Mixed. A failsafe test before the Hover test, from 0.1 m and then 0.3 m, run by one program, and the names Failsafe low and Failsafe high: mine. Injecting a fault into the pre-check, so the drone lands itself: my choice, after the AI first described the alternative (the program exits and the rescue landing takes over) wrongly as an automatic failsafe.

## Context

The field-testing README gets two tests before Hover: the drone takes off to
0.1 m (Failsafe low) or 0.3 m (Failsafe high) and the failsafe landing
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

- One program flies both tests, taking the height (0.1 m or 0.3 m) as an
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
  failsafe program imports the wrapper.
- Glossary: *Failsafe low* and *Failsafe high* may need terms (proposed at the
  end of the field-testing README review).
