"""Fitness functions: structural rules from the ADRs, enforced as tests.

Each test reads the source files' import statements (without running them) and
fails if a rule is broken.
"""

import ast
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPO_ROOT / "src"
PACKAGE_ROOT = SOURCE_ROOT / "crazyflie_behavior"
TOOLS_ROOT = REPO_ROOT / "tools"
CRAZYFLIE_ADAPTER_ROOT = PACKAGE_ROOT / "drone" / "crazyflie"
BEHAVIORS_ROOT = PACKAGE_ROOT / "behaviors"
SAFETY_ROOT = PACKAGE_ROOT / "safety"
DRONE_ROOT = PACKAGE_ROOT / "drone"
TICK_LOOP = PACKAGE_ROOT / "loop" / "tick_loop.py"
PROGRAMS_ROOT = PACKAGE_ROOT / "programs"
FAILSAFE_PROGRAM = PROGRAMS_ROOT / "failsafe.py"
FORGED_BATTERY_WRAPPER = "crazyflie_behavior.programs.failsafe_fault"
FORGED_BATTERY_FILE = PROGRAMS_ROOT / "failsafe_fault.py"
RESCUE_LANDING_PROGRAM = PROGRAMS_ROOT / "rescue_landing.py"
START_UP = PROGRAMS_ROOT / "start_up.py"
TAKE_OVER_SETTING = "take_over_flight"

CLOCK_MODULES = ["time", "datetime", "crazyflie_behavior.timing"]

DRONE_COMMANDS = {
    "arm",
    "disarm",
    "take_off",
    "land",
    "hover",
    "set_velocity",
    "move_to",
    "chirp",
    "play_tone",
    "silence",
}
"""The drone interface's commands that only the safety layer sends (ADR-0008, ADR-0053). Not
`emergency_stop`: the kill switch bypasses the safety layer (ADR-0013)."""


def python_files(root: Path) -> list[Path]:
    return sorted(root.rglob("*.py")) if root.exists() else []


def containing_package(path: Path) -> list[str]:
    """The dotted package a source file belongs to, as parts."""
    parts = list(path.relative_to(SOURCE_ROOT).with_suffix("").parts)
    parts.pop()  # a module's own name, or "__init__" for a package
    return parts


def resolve_relative_import(path: Path, level: int, module: str | None) -> str:
    package = containing_package(path)
    base = package[: len(package) - (level - 1)]
    return ".".join([*base, module] if module else base)


def imported_modules(path: Path) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module is not None:
                modules.add(node.module)
            elif node.level > 0:
                modules.add(resolve_relative_import(path, node.level, node.module))
    return modules


def imports_any_of(imported: str, module_names: list[str]) -> bool:
    """Whether one imported module is any of `module_names` or inside one of them."""
    return any(imported == name or imported.startswith(name + ".") for name in module_names)


def imports_any(path: Path, module_names: list[str]) -> bool:
    return any(imports_any_of(imported, module_names) for imported in imported_modules(path))


def is_the_drone(receiver: ast.expr) -> bool:
    """Whether an expression names the drone: the code always holds the drone
    interface as `drone` or `self._drone`."""
    return (isinstance(receiver, ast.Name) and receiver.id == "drone") or (
        isinstance(receiver, ast.Attribute) and receiver.attr == "_drone"
    )


def drone_commands_called(path: Path) -> set[str]:
    """The drone commands a source file sends, as in `drone.land()` or `self._drone.land()`."""
    return {
        node.func.attr
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in DRONE_COMMANDS
        and is_the_drone(node.func.value)
    }


def imports_module_in_any_form(path: Path, module_name: str) -> bool:
    """Whether a source file imports exactly this module: `import a.b`, `from a import b` or `from a.b import x`.

    `imported_modules` records only the module a `from` import names, so
    `from crazyflie_behavior.programs import failsafe_fault` would slip past it.
    """
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import) and any(alias.name == module_name for alias in node.names):
            return True
        if isinstance(node, ast.ImportFrom):
            source = resolve_relative_import(path, node.level, node.module) if node.level > 0 else (node.module or "")
            if source == module_name or any(f"{source}.{alias.name}" == module_name for alias in node.names):
                return True
    return False


def passes_keyword(path: Path, keyword: str) -> bool:
    """Whether a source file passes `keyword=...` in any call."""
    return any(
        isinstance(node, ast.Call) and any(argument.arg == keyword for argument in node.keywords)
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
    )


def relative_paths(paths: list[Path]) -> list[str]:
    return [path.relative_to(REPO_ROOT).as_posix() for path in paths]


def test_only_the_crazyflie_adapter_imports_cflib() -> None:
    """ADR-0002: cflib stays inside the Crazyflie adapter (tools/ is exempt)."""
    offenders = [
        path
        for path in python_files(PACKAGE_ROOT)
        if imports_any(path, ["cflib"]) and not path.is_relative_to(CRAZYFLIE_ADAPTER_ROOT)
    ]

    assert relative_paths(offenders) == []


def test_project_code_never_imports_tools() -> None:
    """ADR-0002: diagnostic tools may use cflib, so project code never imports them."""
    offenders = [path for path in python_files(PACKAGE_ROOT) if imports_any(path, ["tools"])]

    assert relative_paths(offenders) == []


def test_behaviors_never_import_the_drone_package() -> None:
    """ADR-0008: behaviors send command requests to the safety layer instead."""
    offenders = [path for path in python_files(BEHAVIORS_ROOT) if imports_any(path, ["crazyflie_behavior.drone"])]

    assert relative_paths(offenders) == []


def test_behaviors_use_only_the_request_types_from_the_safety_package() -> None:
    """ADR-0008: behaviors make command requests. They never hold the safety layer,
    which holds the drone."""
    offenders = [
        path
        for path in python_files(BEHAVIORS_ROOT)
        if any(
            imports_any_of(name, ["crazyflie_behavior.safety"]) and name != "crazyflie_behavior.safety.requests"
            for name in imported_modules(path)
        )
    ]

    assert relative_paths(offenders) == []


def test_only_the_safety_layer_sends_commands_to_the_drone() -> None:
    """ADR-0008, ADR-0030: everything else asks. The drone package implements the commands.

    One exemption: the forged low battery drone is itself a drone that passes
    every command on unchanged (ADR-0041), so it calls them without ever
    deciding one. Its own fitness function keeps everyone else from importing
    it. ADR-0041 records the exemption; backlog #44 would move it to a faults
    folder with a second fault.
    """
    offenders = [
        path
        for path in python_files(PACKAGE_ROOT)
        if drone_commands_called(path)
        and not (path.is_relative_to(SAFETY_ROOT) or path.is_relative_to(DRONE_ROOT) or path == FORGED_BATTERY_FILE)
    ]

    assert relative_paths(offenders) == []


def test_behaviors_never_read_a_clock() -> None:
    """ADR-0009: behaviors receive the tick's time in the snapshot."""
    offenders = [path for path in python_files(BEHAVIORS_ROOT) if imports_any(path, CLOCK_MODULES)]

    assert relative_paths(offenders) == []


def test_the_tick_loop_imports_only_the_clock_from_the_project() -> None:
    """ADR-0026: the tick loop is only a timer; the tick step holds what a tick does."""
    offenders = sorted(
        name
        for name in imported_modules(TICK_LOOP)
        if imports_any_of(name, ["crazyflie_behavior"]) and not imports_any_of(name, ["crazyflie_behavior.timing"])
    )

    assert offenders == []


def test_only_the_failsafe_program_imports_the_forged_battery_wrapper() -> None:
    """ADR-0041: the fault must be unreachable from a game program, a behavior or the safety layer.

    Not behaviors/, safety/, loop/ or drone/, and no other program either. (The
    wrapper itself and tests don't count: the tests are outside the package.)
    """
    importers = [
        path
        for path in python_files(PACKAGE_ROOT)
        if path != FORGED_BATTERY_FILE and imports_module_in_any_form(path, FORGED_BATTERY_WRAPPER)
    ]

    assert relative_paths(importers) == relative_paths([FAILSAFE_PROGRAM])


def test_only_the_rescue_landing_program_asks_to_take_over_a_flight() -> None:
    """ADR-0038: behaviors and game programs have no way to ask for take-over.

    `start_up.make_drone` only passes the setting on to the adapter it builds,
    and the adapters themselves are in the drone package, which only defines it.
    """
    askers = [path for path in python_files(PACKAGE_ROOT) if passes_keyword(path, TAKE_OVER_SETTING)]

    assert relative_paths(askers) == relative_paths([RESCUE_LANDING_PROGRAM, START_UP])


def test_the_import_scanner_sees_real_imports() -> None:
    """Guards the fitness functions themselves: if the scanner silently found
    nothing, every rule above would pass for the wrong reason."""
    assert imports_any(TOOLS_ROOT / "first_flight.py", ["cflib"])
    assert imports_any(CRAZYFLIE_ADAPTER_ROOT / "adapter.py", ["cflib"])
    assert imports_any(PACKAGE_ROOT / "timing" / "clock.py", ["time"])
    assert imports_any(PACKAGE_ROOT / "drone" / "mock_adapter.py", ["crazyflie_behavior.drone"])
    assert imports_any(TICK_LOOP, ["crazyflie_behavior.timing"])
    assert imports_any(BEHAVIORS_ROOT / "hover_test.py", ["crazyflie_behavior.safety"])
    assert drone_commands_called(SAFETY_ROOT / "safety_layer.py") >= {"arm", "take_off", "land", "chirp", "silence"}
    assert drone_commands_called(FORGED_BATTERY_FILE) >= {"arm", "take_off", "land"}  # why it needs its exemption
    assert imports_module_in_any_form(FAILSAFE_PROGRAM, FORGED_BATTERY_WRAPPER)
    assert not imports_module_in_any_form(PROGRAMS_ROOT / "hover.py", FORGED_BATTERY_WRAPPER)
    assert passes_keyword(RESCUE_LANDING_PROGRAM, TAKE_OVER_SETTING)
    assert not passes_keyword(PROGRAMS_ROOT / "hover.py", TAKE_OVER_SETTING)


@pytest.mark.parametrize(
    "import_line",
    [
        "import crazyflie_behavior.programs.failsafe_fault",
        "import crazyflie_behavior.programs.failsafe_fault as fault",
        "from crazyflie_behavior.programs import failsafe_fault",
        "from crazyflie_behavior.programs.failsafe_fault import ForgedLowBatteryDrone",
        "from . import failsafe_fault",
        "from .failsafe_fault import ForgedLowBatteryDrone",
        "from ..programs import failsafe_fault",
    ],
)
def test_the_import_scanner_sees_every_form_of_an_import(
    import_line: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Each form `imports_module_in_any_form` handles, on a made-up program file.

    Relative imports resolve from the file's package, so the file sits in a
    made-up source tree at the same place as the real programs.
    """
    monkeypatch.setattr(sys.modules[__name__], "SOURCE_ROOT", tmp_path)
    program = tmp_path / "crazyflie_behavior" / "programs" / "made_up_program.py"
    program.parent.mkdir(parents=True)
    program.write_text(import_line + "\n", encoding="utf-8")

    assert imports_module_in_any_form(program, FORGED_BATTERY_WRAPPER)


@pytest.mark.parametrize(
    "import_line",
    [
        "import crazyflie_behavior.programs",
        "from crazyflie_behavior.programs import failsafe",
        "from crazyflie_behavior.programs.failsafe_faults import x",
        "from . import failsafe",
    ],
)
def test_the_import_scanner_does_not_see_a_near_miss(
    import_line: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys.modules[__name__], "SOURCE_ROOT", tmp_path)
    program = tmp_path / "crazyflie_behavior" / "programs" / "made_up_program.py"
    program.parent.mkdir(parents=True)
    program.write_text(import_line + "\n", encoding="utf-8")

    assert not imports_module_in_any_form(program, FORGED_BATTERY_WRAPPER)
