# Coding style

Only what tools can't check. Formatting and lint rules come from **ruff**, and
types are checked by **pyright** in strict mode. Both run in continuous integration
([ADR-0004](decisions/0004-strict-typing-ruff-and-units-in-names.md)).

## Types

- **Every function is fully typed**: parameters and return type, including
  `-> None`.
- **"May be missing" is `X | None`**, never a sentinel value like `-1` or `0`.
  A range sensor with nothing in range returns `None`, not `8.0`.
- **No anonymous shapes.** Don't return `list[list[str]]`,
  `tuple[float, float, float]` or `dict[str, float]` to mean a structured
  thing. Name it:
  - `NamedTuple` for small immutable values (`FoundDrone(uri, description)`)
  - `dataclass` for richer data (state snapshots, configs), always
    `frozen=True, slots=True` ([ADR-0018](decisions/0018-frozen-dataclasses-with-slots.md)).
    State that changes over time lives in ordinary classes.
- **Modern syntax** (Python 3.12): `list[str]`, `int | None`, not `List[str]`
  or `Optional[int]`.

UE5 analogy: think `USTRUCT` rather than `TArray<TArray<FString>>`.

## Units

([ADR-0004](decisions/0004-strict-typing-ruff-and-units-in-names.md))

**Everything is SI internally:** meters, seconds, meters per second, hertz,
volts, radians. The Crazyflie adapter converts cflib's millimeters and degrees
at the boundary.

1. **SI values get no suffix:** `height`, `distance`, `dt`, `timeout`,
   `speed`, `tick_rate`, `battery_voltage`.
2. **Non-SI values always get a suffix:**

   | Suffix | Unit | Example |
   |---|---|---|
   | `_mm` | millimeters | `range_mm` (raw cflib value, adapter only) |
   | `_cm` | centimeters | `margin_cm` |
   | `_ms` | milliseconds | `period_ms` (cflib log periods) |

3. **Angles always get a suffix**, even in SI: `yaw_rad`, `heading_deg`.
   Math uses `_rad`. Logs and debug output may show `_deg`, converted at the
   point of display.

Unitless values (counts, ratios, flags) get no suffix.

## Names

- Use **glossary terms** exactly (`docs/glossary.md`). A concept without a
  glossary term gets one proposed before it's named in code.
- **Name things after what they hold**, not how they were obtained:
  `available_drones`, not `found` or `result`.
- **Full words, not abbreviations:** `crazyflie`, not `cf`; `reading`, not
  `rdg`. Standard abbreviations are fine: unit suffixes (`_ms`, `_mm`,
  `_rad`), and well-known ones such as `dt`, `uri` and `id`. Names that
  come from cflib's API (`SyncCrazyflie.cf`) stay as cflib spells them.
- Python naming: `snake_case` for functions, variables and modules,
  `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants. A leading `_`
  marks something private to its module or class.

## The cflib boundary

- Only the Crazyflie adapter imports `cflib`
  ([ADR-0002](decisions/0002-behavior-depends-only-on-drone-interface.md)),
  plus diagnostic scripts in `tools/`. Those run in basic mode, type their own
  functions, and annotate raw cflib values where they enter
  (`available_drones: list[list[str]] = cflib.crtp.scan_interfaces()`).
- It runs pyright in **basic** mode and converts every untyped cflib value
  into a typed project type before handing it on.
- Type-check suppressions are allowed **only** in the Crazyflie adapter,
  always scoped to one rule and with a reason:
  `# pyright: ignore[reportUnknownMemberType]  # cflib is untyped`.

## Docstrings and comments

- **Public classes and functions** get a docstring: one line saying what it
  does, plus units, frames or threading notes when relevant.
- **Comments explain *why***, not what the next line does. A good comment
  records a non-obvious constraint ("cflib callbacks run on its receive
  thread, so only copy data here").
- Reference ADRs where code exists *because of* a decision (`# See ADR-0003.`).
