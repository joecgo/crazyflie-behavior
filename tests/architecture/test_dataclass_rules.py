"""Fitness function for ADR-0018: data records are frozen dataclasses with slots.

Reads the source files' decorators (without running them) and fails if a
dataclass is missing either option.
"""

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = REPO_ROOT / "src" / "crazyflie_behavior"

REQUIRED_OPTIONS = {"frozen", "slots"}

EXCEPTIONS: dict[str, str] = {}
"""Dataclasses allowed to skip the rule, as "path::ClassName": reason."""


def dataclass_options(decorator: ast.expr) -> set[str] | None:
    """The options set to True on a @dataclass decorator, or None if it isn't one."""
    call = decorator if isinstance(decorator, ast.Call) else None
    target = call.func if call else decorator
    name = target.attr if isinstance(target, ast.Attribute) else getattr(target, "id", None)
    if name != "dataclass":
        return None
    if call is None:
        return set()
    return {
        keyword.arg
        for keyword in call.keywords
        if keyword.arg is not None
        and isinstance(keyword.value, ast.Constant)
        and keyword.value.value is True
    }


def dataclasses_in(path: Path) -> dict[str, set[str]]:
    """Each dataclass in a file, as "path::ClassName", with its options."""
    found: dict[str, set[str]] = {}
    relative = path.relative_to(REPO_ROOT).as_posix()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.ClassDef):
            for decorator in node.decorator_list:
                options = dataclass_options(decorator)
                if options is not None:
                    found[f"{relative}::{node.name}"] = options
    return found


def all_dataclasses() -> dict[str, set[str]]:
    found: dict[str, set[str]] = {}
    for path in sorted(PACKAGE_ROOT.rglob("*.py")):
        found.update(dataclasses_in(path))
    return found


def test_dataclasses_are_frozen_with_slots() -> None:
    """ADR-0018: every dataclass in src/ uses frozen=True, slots=True."""
    offenders = [
        name
        for name, options in all_dataclasses().items()
        if not options >= REQUIRED_OPTIONS and name not in EXCEPTIONS
    ]

    assert offenders == []


def test_the_dataclass_scanner_sees_real_dataclasses() -> None:
    """Guards the rule above: if the scanner found nothing, it would pass for the wrong reason."""
    found = all_dataclasses()

    assert found["src/crazyflie_behavior/geometry.py::Vector3"] == REQUIRED_OPTIONS
    assert "src/crazyflie_behavior/snapshot.py::Snapshot" in found
