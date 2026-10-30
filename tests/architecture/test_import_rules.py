"""Fitness functions: structural rules from the ADRs, enforced as tests.

Each test reads the source files' import statements (without running them) and
fails if a rule is broken.
"""

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPO_ROOT / "src"
PACKAGE_ROOT = SOURCE_ROOT / "crazyflie_behavior"
TOOLS_ROOT = REPO_ROOT / "tools"
CRAZYFLIE_ADAPTER_ROOT = PACKAGE_ROOT / "drone" / "crazyflie"
BEHAVIORS_ROOT = PACKAGE_ROOT / "behaviors"
SAFETY_ROOT = PACKAGE_ROOT / "safety"
DRONE_ROOT = PACKAGE_ROOT / "drone"
TICK_LOOP = PACKAGE_ROOT / "loop" / "tick_loop.py"

CLOCK_MODULES = ["time", "datetime", "crazyflie_behavior.timing"]

DRONE_COMMANDS = {"arm", "disarm", "take_off", "land", "hover", "set_velocity", "move_to"}
"""The drone interface's commands that only the safety layer sends (ADR-0008). Not
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
    offenders = [
        path
        for path in python_files(BEHAVIORS_ROOT)
        if imports_any(path, ["crazyflie_behavior.drone"])
    ]

    assert relative_paths(offenders) == []


def test_behaviors_use_only_the_request_types_from_the_safety_package() -> None:
    """ADR-0008: behaviors make command requests. They never hold the safety layer,
    which holds the drone."""
    offenders = [
        path
        for path in python_files(BEHAVIORS_ROOT)
        if any(
            imports_any_of(name, ["crazyflie_behavior.safety"])
            and name != "crazyflie_behavior.safety.requests"
            for name in imported_modules(path)
        )
    ]

    assert relative_paths(offenders) == []


def test_only_the_safety_layer_sends_commands_to_the_drone() -> None:
    """ADR-0008, ADR-0030: everything else asks. The drone package implements the commands."""
    offenders = [
        path
        for path in python_files(PACKAGE_ROOT)
        if drone_commands_called(path)
        and not (path.is_relative_to(SAFETY_ROOT) or path.is_relative_to(DRONE_ROOT))
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
        if imports_any_of(name, ["crazyflie_behavior"])
        and not imports_any_of(name, ["crazyflie_behavior.timing"])
    )

    assert offenders == []


def test_the_import_scanner_sees_real_imports() -> None:
    """Guards the fitness functions themselves: if the scanner silently found
    nothing, every rule above would pass for the wrong reason."""
    assert imports_any(TOOLS_ROOT / "first_flight.py", ["cflib"])
    assert imports_any(CRAZYFLIE_ADAPTER_ROOT / "adapter.py", ["cflib"])
    assert imports_any(PACKAGE_ROOT / "timing" / "clock.py", ["time"])
    assert imports_any(PACKAGE_ROOT / "drone" / "mock_adapter.py", ["crazyflie_behavior.drone"])
    assert imports_any(TICK_LOOP, ["crazyflie_behavior.timing"])
    assert imports_any(BEHAVIORS_ROOT / "hover_test.py", ["crazyflie_behavior.safety"])
    assert drone_commands_called(SAFETY_ROOT / "safety_layer.py") >= {"arm", "take_off", "land"}
