# 0074: A module is split by five tests, never by its size

- **Status:** Accepted
- **Date:** 2026-11-16
- **Origin:** Mixed. Asking for an architectural rule for when to split a file, and the view that one file doing many related things is fine: mine. The five tests, and dropping the line-count limit: AI recommendations accepted.

## Context

`drone/crazyflie/adapter.py` is 1,332 lines, 2.7 times the next largest file,
and nothing in the rules says when a file should be split. The refactor's
target ([ARCHITECTURE.md](../../ARCHITECTURE.md) section 7) splits it, but as
a one-off. Ruff's complexity rules (`C901`, `PLR09xx`) measure one function or
class, so they barely touch the adapter: about 70 small functions in one
class. A line limit measures size, which is only a stand-in for the real
problem.

## Options considered

- **A. A line-count limit with a ratchet** (a cap, with the adapter on a
  list of exceptions): catches growth, but a big file whose parts share state
  and change together is fine, and a small file can mix unrelated things.
- **B. Ruff complexity rules:** catch big functions, not big modules.
- **C. Tests about the parts, not the size (chosen).**

## Decision

Option C. One file doing many related things is not a fault: parts that share
state, dependencies and reasons to change belong together, and splitting them
only adds interfaces to pass that state through.

**Split a part out of a module when any of these is true of it:**

1. **It needs fewer dependencies than the module** (for example, no cflib).
   The take-off and landing logic needs no cflib, but sits in a file that
   imports it, so it can only run with cflib present. The import fitness
   functions could check this one.
2. **Another module needs it.** The mock adapter is meant to run the Crazyflie
   adapter's take-off and landing code (section 7), which it can't while that
   code is inside `CrazyflieAdapter`.
3. **It runs on a different thread than the rest.** Code called from cflib's
   callbacks and code called from the tick shouldn't share a file's worth of
   private state. One small module for the part that crosses threads makes
   what crosses visible.
4. **It has its own state and invariants,** which the rest touches through few
   calls. `_LandingPhase`, the landing's state machine, looks like this.
5. **It changes for a different reason.** A cflib or firmware update changes
   the link and log-block code; a field test changes the landing's tuning.

**Don't split when** the parts share most of their state and the split would
mostly create wide interfaces.

The reasoning: many related things in one file are fine, and splitting them
only adds interfaces to pass state through. A line count is a stand-in for
the five properties above, and is weaker than the import rules because a big
cohesive file would fail a size check it should pass, and a small file can
still mix unrelated things and pass it. The line limit and the Ruff complexity rules are
not adopted. Test 1 could become a fitness function later; for now the rule
is kept by review.

## Consequences

- The section 7 adapter split is judged by these tests: `flight_phases.py`
  meets tests 1, 2 and 4 (the strongest case); `link.py` and `log_blocks.py`
  rest on tests 3 and 5; `commands.py` is the weakest and unchecked, to be
  verified in its own ADR.
- A review question for `REVIEW.md` is a possible follow-up.
- No new glossary terms.
