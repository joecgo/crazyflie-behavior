# 0033: Behaviors written for field tests choose their own failure rule

- **Status:** Accepted. Amends [ADR-0020](0020-failures-degrade-gracefully.md) for behaviors written for field tests.
- **Date:** 2026-11-01
- **Origin:** Mixed. Letting each field test choose whether to stop or retry, depending on what it tests, and the hover test stopping at its first refused request: mine. Keeping ADR-0020's other two parts for every field test, and each test's docstring saying which rule it uses: AI recommendations accepted. Claude first chose the hover test's rule without asking; my second code review caught it.

## Context

The hover test ([ADR-0030](0030-minimal-safety-layer-for-first-flight.md))
ends at its first refused command request: it logs an error and reports done.
ADR-0020 says to keep going when it's safe, retrying where it makes sense, and
a refusal is safe to retry: a refused request takes nothing, and the safety
layer judges every retry again ([ADR-0025](0025-safety-pre-check-and-command-slots.md)).
So the hover test's rule went against ADR-0020, without a decision.

## Options considered

- **A. Retry, as ADR-0020 says:** ask again each tick until the step's time
  limit runs out, then fail.
- **B. Stop at the first refusal:** the hover test is a test, so an unexpected
  state is what it's looking for.
- **C. Each field test chooses,** depending on what it tests.

## Decision

Option C. A behavior written for a field test decides whether a refused
request stops it or is retried, and its docstring says which. Some tests want
to stop at the first surprise; others, such as one that counts problems over a
long flight, want to keep going.

- **The hover test stops at its first refused request.** It tests the basic
  sequence (arm, take off, hover, land), so an unexpected state is the finding.
  Its time limits end it too: arming too slowly ends it at once (nothing is
  flying yet), and a take-off that doesn't reach the height lands first.
- **ADR-0020's other two parts still apply to every field test:** stopping
  fails safe (the behavior reports done, and disconnecting lands the drone),
  and the refusal is logged with its reason.
- **Game behaviors keep ADR-0020 in full.**

## Failure modes

- **Inputs:** a refused request in the hover test ends it with an error that
  names the request and the reason.
- **Never:** a field test that stops without landing or without logging why;
  a field test whose failure rule isn't stated.
- **Always eventually:** a stopped field test ends with the drone landed and
  its motors off ([ADR-0026](0026-tick-loop-calls-one-tick-step.md)).

## Consequences

- The hover test's docstring states its rule. Its test
  `test_a_refused_request_ends_the_hover_test` already pins it.
- ADR-0020's status line marks the exception.
- Disconnecting doesn't disarm, so a drone that arms just after the arming
  time limit stays armed: backlog #37.
- Glossary: *Failure rule* and *Field test* added.
