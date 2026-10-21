# 0010: Code foundations: layout, interfaces, tests, and the first adapters

- **Status:** Accepted
- **Date:** 2026-10-20

## Context

With the drone interface (ADR-0008) and clock (ADR-0009) designed, the first
code needs a few structural choices: how the package is laid out, how
interfaces are declared in Python, which test framework to use, whether the
snapshot is immutable, and which adapters get written first.

## Options considered and decisions

### 1. Package layout
- **Src layout with subpackages:** `src/crazyflie_behavior/` with `drone/`,
  `timing/`, and later `safety/`, `behaviors/`, `loop/`. Tests in `tests/`,
  fitness functions in `tests/architecture/`.
- Flat: all modules side by side in `src/`.

**Chosen: src layout with subpackages.** It mirrors how UE5 organizes code into
modules and subsystem folders, and the extra package level makes tests import
the code the way real users would.

### 2. Declaring interfaces
- **`abc.ABC` (abstract base class):** implementations inherit explicitly;
  missing methods fail when an object is created.
- `typing.Protocol`: structural matching, checked only by the type checker
  (like C++20 concepts).

**Chosen: `abc.ABC`.** Explicit, like a C++ pure virtual base or a UInterface,
and it fails loudly even without pyright.

### 3. Test framework
- **pytest:** plain functions and `assert`, clear failure output, the
  industry norm.
- unittest: built in, but class-based with `self.assert…` boilerplate.

**Chosen: pytest.**

### 4. Snapshot immutability
**Provisional: the snapshot is a frozen dataclass**, enforcing ADR-0007's
read-only rule. Whether frozen becomes the default for other dataclasses is
decided after seeing how it reads in real code (backlog).

### 5. Which adapters first
- Mock adapter only, Crazyflie adapter when hardware arrives (consistent with
  ADR-0006's "don't build what can't be tested").
- **Mock adapter and Crazyflie adapter together.**

**Chosen: both, as a deliberate exception for learning.** Comparing a real
adapter with a fake one side by side shows exactly what the interface hides.

## Consequences

- The Crazyflie adapter can't be run until hardware arrives. Its bugs will
  surface at the first bench test (field-test stage 0). Risk reduction: its
  conversions (mm → m, degrees → radians, cflib's missing readings → unknown)
  are separate functions with unit tests, and its cflib calls are checked
  against the installed source and type-checked.
- All dependencies (cflib, plus pytest, ruff and pyright for development), with
  exact versions, and the tool configuration live in `pyproject.toml`. It
  replaces `requirements.txt`.
- Shared data types (`geometry.py`, `snapshot.py`) live at the package root,
  outside `drone/`, so behaviors can use the snapshot without importing the
  drone package (ADR-0008's fitness function).
- Fitness functions live in `tests/architecture/` and run with the other tests.
- Glossary: *Mock* is renamed *Mock adapter*, to match *Crazyflie adapter*.
