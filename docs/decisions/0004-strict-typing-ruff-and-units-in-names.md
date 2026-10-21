# 0004: Strict typing, ruff, and units in names

- **Status:** Accepted
- **Date:** 2026-10-18
- **Origin:** Mixed. Strict typing and ruff: AI recommendations accepted. No unit suffix for SI values: my idea. Deferring frozen dataclasses: overrode the AI's recommendation.

## Context

Python doesn't declare types, so it's often unclear what a function takes or
returns (cflib's `scan_interfaces()` returns an undocumented `list[list[str]]`).
Coming from C++, I want type mistakes caught before code runs, not in flight.
Robotics code also mixes units constantly (cflib uses meters, millimeters,
degrees and radians in different places), which is a classic source of bugs.
Style should be enforced by tools in continuous integration, not by memory.

## Options considered

### Type checking
- **A. No checking:** hints optional, nothing enforced. Fast to write, but
  errors only surface at run time.
- **B. Basic pyright:** hints checked where present. Gaps let untyped values
  slip through silently.
- **C. Strict pyright everywhere:** every function fully typed. Untyped cflib
  values cause many errors wherever they're used.
- **D. Strict pyright, basic in the Crazyflie adapter only.** Since ADR-0002
  confines cflib to the Crazyflie adapter, that one file is the only place
  untyped values enter.

### Formatting and linting
- **ruff:** formatter and linter in one tool, very fast, the current standard.
- **black + flake8 + isort:** the older combination of three tools doing the same jobs.

### Units
- **A. SI internally, suffix only non-SI values.** Matches ROS (REP 103).
  Clean names, but an unconverted raw value looks the same as a converted one,
  and an unsuffixed `yaw` meaning radians is easy to misread as degrees.
- **B. As A, but angles always carry a suffix** (`_rad` or `_deg`).
- **C. Every quantity with a unit carries a suffix** (`distance_m`, `yaw_rad`).
  Mix-ups are most visible, but names get noisy.
- **D. Units only in docs/comments.**

## Decision

- **Type checking: D.** Strict pyright for all project code. The Crazyflie
  adapter runs in basic mode and converts cflib's untyped data into typed
  project types, so nothing untyped leaks past it. The looseness is contained
  in one file because of ADR-0002. The diagnostic scripts in `tools/` (also
  exempt under ADR-0002) run in basic mode too, but still type their own
  functions and annotate raw cflib values.
- **Formatting and linting: ruff.** One fast tool, current standard.
- **SI units internally.** Project code uses meters, seconds and radians. The
  Crazyflie adapter converts cflib's millimeters and degrees at the boundary,
  so conversions happen in one place.
- **Units: B.** Since everything is SI, SI values need no suffix (`height`,
  `speed`, `timeout`). Non-SI values always carry one (`range_mm`, `period_ms`).
  **Angles always carry a suffix**, `_rad` or `_deg`, because my UE5 habits
  read angles as degrees, and I'll often show degrees in logs and debug output.

Typing and ruff are enforced in continuous integration (focus area 6). The units convention is
checked in code review.

## Consequences

- Every function signature is fully typed. Anonymous shapes like
  `list[list[str]]` are replaced with `NamedTuple` or `dataclass` types.
- Type-check suppressions (`# pyright: ignore[...]`) are allowed only in the
  Crazyflie adapter, each scoped to one rule with a one-line reason.
- The Crazyflie adapter carries a small amount of conversion code.
- Tool configuration (`pyproject.toml`) and dev dependencies get added with the
  first real code.
- Conventions are written down in `docs/coding-style.md`.
- **Deferred:** whether dataclasses default to immutable (`frozen=True`).
  Decide once real code shows how it affects readability, likely together
  with the blackboard design (ADR-0003 follow-up).
