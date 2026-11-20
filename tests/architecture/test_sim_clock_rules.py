"""Fitness function: tests that run the tick loop on a sim clock get the sim time limit (ADR-0082).

Reads the test files (without running them) and fails on a plain `SimClock()`
or a new subclass of `SimClock` in the folders that run the tick loop.
"""

import ast
from pathlib import Path

TESTS_ROOT = Path(__file__).resolve().parents[1]
COVERED_FOLDERS = [TESTS_ROOT / "programs", TESTS_ROOT / "loop"]

ALLOWED_SUBCLASSES = {
    # Wakes every wait late for one test, whose tick step ends after 4 ticks (ADR-0082).
    ("loop/test_tick_loop.py", "LateWakingClock"),
}


def _is_sim_clock(node: ast.expr) -> bool:
    return isinstance(node, ast.Name) and node.id == "SimClock"


def _breaks() -> list[str]:
    found: list[str] = []
    for folder in COVERED_FOLDERS:
        for path in sorted(folder.rglob("*.py")):
            relative = path.relative_to(TESTS_ROOT).as_posix()
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, ast.Call) and _is_sim_clock(node.func):
                    found.append(f"{relative}:{node.lineno}: SimClock() has no time limit; use the sim_clock fixture")
                if (
                    isinstance(node, ast.ClassDef)
                    and any(_is_sim_clock(base) for base in node.bases)
                    and (relative, node.name) not in ALLOWED_SUBCLASSES
                ):
                    found.append(f"{relative}:{node.lineno}: {node.name} subclasses SimClock, which has no time limit")
    return found


def test_tests_of_the_tick_loop_use_the_time_limited_sim_clock() -> None:
    assert _breaks() == []
