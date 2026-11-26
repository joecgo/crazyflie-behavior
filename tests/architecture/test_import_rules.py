"""Fitness functions: structural rules from the ADRs, enforced as tests.

Each test reads the source files without running them (their imports, and for
some rules their calls or comments), or the project's pyright settings, and
fails if a rule is broken.
"""

import ast
import re
import sys
import tokenize
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPO_ROOT / "src"
PACKAGE_ROOT = SOURCE_ROOT / "crazyflie_behavior"
TOOLS_ROOT = REPO_ROOT / "tools"
ANALYSIS_ROOT = REPO_ROOT / "analysis"
CRAZYFLIE_ADAPTER_ROOT = PACKAGE_ROOT / "drone" / "crazyflie"
CFLIB_IMPORTERS = [CRAZYFLIE_ADAPTER_ROOT / name for name in ["adapter.py", "commands.py", "link.py", "log_blocks.py"]]
"""The Crazyflie adapter's modules that import cflib, the only ones that pass cflib objects to each other (ADR-0093)."""
TAKE_OFF_AND_LANDING = CRAZYFLIE_ADAPTER_ROOT / "take_off_and_landing.py"
TYPE_CHECK_COMMENT = re.compile(r"#\s*(pyright\s*:|type\s*:\s*ignore)")
"""A comment that changes what pyright checks: a `# pyright:` setting or ignore, or a `# type: ignore`."""
PYPROJECT = REPO_ROOT / "pyproject.toml"
PYRIGHT_SETTINGS = {
    "include": ["src", "tests", "tools", "analysis"],
    "typeCheckingMode": "strict",
    "pythonVersion": "3.12",
    "venvPath": ".",
    "venv": ".venv",
}
"""`pyproject.toml`'s whole `[tool.pyright]` table: strict everywhere, nothing ignored or excluded, no rule
turned down. A setting there could relax take-off and landing with no comment in the file, so any change shows in
review."""
BEHAVIORS_ROOT = PACKAGE_ROOT / "behaviors"
SAFETY_ROOT = PACKAGE_ROOT / "safety"
DRONE_ROOT = PACKAGE_ROOT / "drone"
TICK_LOOP = PACKAGE_ROOT / "loop" / "tick_loop.py"
TICK_STEP = PACKAGE_ROOT / "loop" / "tick_step.py"
RECORDING_ROOT = PACKAGE_ROOT / "recording"
RECORDING_PACKAGE = "crazyflie_behavior.recording"
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


def project_file(module: str) -> Path | None:
    """A module's file in `src/`: `x.py`, or `x/__init__.py` for a package. None for a module from outside `src/`."""
    base = SOURCE_ROOT.joinpath(*module.split("."))
    return next((file for file in [base.with_suffix(".py"), base / "__init__.py"] if file.is_file()), None)


def files_run_by_import(module: str) -> list[Path]:
    """The files in `src/` that importing a module runs: each package on its dotted path, then the module itself."""
    parts = module.split(".")
    files = [project_file(".".join(parts[:end])) for end in range(1, len(parts) + 1)]
    return [file for file in files if file is not None]


def modules_named_by_imports(path: Path) -> set[str]:
    """Every module a source file's imports may load. `from a import b` loads `a`, and `a.b` too when `b` is a
    module."""
    names: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            source = resolve_relative_import(path, node.level, node.module) if node.level > 0 else (node.module or "")
            names.add(source)
            names.update(f"{source}.{alias.name}" for alias in node.names if alias.name != "*")
    return names


def files_loaded_with(path: Path) -> set[Path]:
    """Every file in `src/` that importing a source file may run: itself, its packages, and what each of those
    imports, in turn."""
    loaded: set[Path] = set()
    unvisited = [*files_run_by_import(".".join(containing_package(path))), path]
    while unvisited:
        file = unvisited.pop()
        if file not in loaded:
            loaded.add(file)
            unvisited.extend(found for name in modules_named_by_imports(file) for found in files_run_by_import(name))
    return loaded


def type_check_comments(path: Path) -> list[str]:
    """Each comment in a source file that changes what pyright checks, with its line."""
    with path.open(encoding="utf-8") as source:
        return [
            f"line {token.start[0]}: {token.string}"
            for token in tokenize.generate_tokens(source.readline)
            if token.type == tokenize.COMMENT and TYPE_CHECK_COMMENT.search(token.string)
        ]


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


def test_inside_the_crazyflie_adapter_only_the_named_modules_import_cflib() -> None:
    """ADR-0093: only these modules import cflib, so only they pass cflib objects to each other. One that starts or
    stops importing cflib changes the list, so the change shows in review."""
    importers = [path for path in python_files(CRAZYFLIE_ADAPTER_ROOT) if imports_any(path, ["cflib"])]

    assert sorted(relative_paths(importers)) == sorted(relative_paths(CFLIB_IMPORTERS))


def test_take_off_and_landing_reaches_no_cflib() -> None:
    """ADR-0093: not even through another module in `src/`, so take-off and landing can run and be tested without
    cflib."""
    offenders = [path for path in sorted(files_loaded_with(TAKE_OFF_AND_LANDING)) if imports_any(path, ["cflib"])]

    assert relative_paths(offenders) == []


def test_take_off_and_landing_keeps_pyright_strict() -> None:
    """ADR-0093: with no cflib values to type, nothing turns pyright's strict mode down for take-off and landing: no
    `# pyright:` setting, rule turned off or line ignored in the file, and `pyproject.toml`'s settings as pinned."""
    pyright_settings = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["tool"]["pyright"]

    assert type_check_comments(TAKE_OFF_AND_LANDING) == []
    assert pyright_settings == PYRIGHT_SETTINGS


def test_project_code_never_imports_tools() -> None:
    """ADR-0002: diagnostic tools may use cflib, so project code never imports them."""
    offenders = [path for path in python_files(PACKAGE_ROOT) if imports_any(path, ["tools"])]

    assert relative_paths(offenders) == []


def test_project_code_never_imports_analysis_scripts() -> None:
    """ADR-0092: analysis scripts read recordings after a run; the flying code never depends on them."""
    offenders = [path for path in python_files(PACKAGE_ROOT) if imports_any(path, ["analysis"])]

    assert relative_paths(offenders) == []


def test_analysis_scripts_never_import_cflib() -> None:
    """ADR-0092: an analysis script reads committed recordings and never touches the drone."""
    offenders = [path for path in python_files(ANALYSIS_ROOT) if imports_any(path, ["cflib"])]

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

    `start_up.make_drone` only passes the setting on to the adapter it builds, and
    the Crazyflie adapter only passes it on to its log-block part (ADR-0093).
    """
    askers = [path for path in python_files(PACKAGE_ROOT) if passes_keyword(path, TAKE_OVER_SETTING)]

    assert relative_paths(askers) == relative_paths(
        [CRAZYFLIE_ADAPTER_ROOT / "adapter.py", RESCUE_LANDING_PROGRAM, START_UP]
    )


def test_only_the_tick_steps_and_the_programs_import_the_recording_package() -> None:
    """ADR-0088: the programs make the recorder and the tick steps hand it each tick. The safety layer, the
    behaviors, the drone package and the tick loop never hold it."""
    importers = [
        path
        for path in python_files(PACKAGE_ROOT)
        if not path.is_relative_to(RECORDING_ROOT)
        and (imports_any(path, [RECORDING_PACKAGE]) or imports_module_in_any_form(path, RECORDING_PACKAGE))
    ]

    offenders = [path for path in importers if path != TICK_STEP and not path.is_relative_to(PROGRAMS_ROOT)]

    assert relative_paths(offenders) == []


def test_the_recording_package_imports_only_the_snapshot_the_geometry_and_the_safety_package() -> None:
    """ADR-0088: a recording holds the snapshots, the command requests and the events, so the recorder needs
    nothing else from the project: not the drone package, the tick loop or a behavior."""
    allowed = [
        RECORDING_PACKAGE,
        "crazyflie_behavior.snapshot",
        "crazyflie_behavior.geometry",
        "crazyflie_behavior.safety",
    ]
    offenders = sorted(
        f"{path.name}: {name}"
        for path in python_files(RECORDING_ROOT)
        for name in imported_modules(path)
        if imports_any_of(name, ["crazyflie_behavior"]) and not imports_any_of(name, allowed)
    )

    assert offenders == []


def test_the_import_scanner_sees_real_imports() -> None:
    """Guards the fitness functions themselves: if the scanner silently found
    nothing, every rule above would pass for the wrong reason."""
    assert imports_any(TOOLS_ROOT / "first_flight.py", ["cflib"])
    assert ANALYSIS_ROOT.is_dir()  # python_files finds nothing in a folder that isn't there
    assert imports_any(CRAZYFLIE_ADAPTER_ROOT / "adapter.py", ["cflib"])
    assert imports_any(PACKAGE_ROOT / "timing" / "clock.py", ["time"])
    assert imports_any(PACKAGE_ROOT / "drone" / "mock_adapter.py", ["crazyflie_behavior.drone"])
    assert imports_any(TICK_LOOP, ["crazyflie_behavior.timing"])
    assert imports_any(TICK_STEP, [RECORDING_PACKAGE])
    assert imports_any(RECORDING_ROOT / "recorder.py", ["crazyflie_behavior.snapshot"])
    assert imports_any(BEHAVIORS_ROOT / "hover_test.py", ["crazyflie_behavior.safety"])
    assert drone_commands_called(SAFETY_ROOT / "safety_layer.py") >= {"arm", "take_off", "land", "chirp", "silence"}
    assert drone_commands_called(FORGED_BATTERY_FILE) >= {"arm", "take_off", "land"}  # why it needs its exemption
    assert imports_module_in_any_form(FAILSAFE_PROGRAM, FORGED_BATTERY_WRAPPER)
    assert not imports_module_in_any_form(PROGRAMS_ROOT / "hover.py", FORGED_BATTERY_WRAPPER)
    assert passes_keyword(RESCUE_LANDING_PROGRAM, TAKE_OVER_SETTING)
    assert not passes_keyword(PROGRAMS_ROOT / "hover.py", TAKE_OVER_SETTING)
    assert files_loaded_with(TAKE_OFF_AND_LANDING) >= {
        PACKAGE_ROOT / "__init__.py",
        CRAZYFLIE_ADAPTER_ROOT / "touchdown.py",
        DRONE_ROOT / "telemetry_buffer.py",
        PACKAGE_ROOT / "geometry.py",
    }
    assert CRAZYFLIE_ADAPTER_ROOT / "link.py" in files_loaded_with(CRAZYFLIE_ADAPTER_ROOT / "adapter.py")
    assert "line 1: # pyright: basic" in type_check_comments(CRAZYFLIE_ADAPTER_ROOT / "adapter.py")


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


def made_up_take_off_and_landing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, files: dict[str, str]) -> Path:
    """A made-up source tree holding `files`, by path inside a made-up Crazyflie adapter, beside a `radio.py` that
    imports cflib. The adapter package and its two parents get an empty `__init__.py` unless `files` gives one. Points
    `SOURCE_ROOT` at the tree for the rest of the test, and returns its take-off and landing file."""
    monkeypatch.setattr(sys.modules[__name__], "SOURCE_ROOT", tmp_path)
    adapter_root = tmp_path / "crazyflie_behavior" / "drone" / "crazyflie"
    adapter_root.mkdir(parents=True)
    for package in [adapter_root.parent.parent, adapter_root.parent, adapter_root]:
        (package / "__init__.py").write_text("", encoding="utf-8")
    for name, source in {"radio.py": "import cflib.crtp", **files}.items():
        (adapter_root / name).parent.mkdir(parents=True, exist_ok=True)
        (adapter_root / name).write_text(source + "\n", encoding="utf-8")
    return adapter_root / "take_off_and_landing.py"


@pytest.mark.parametrize(
    "files",
    [
        {"take_off_and_landing.py": "import cflib"},
        {"take_off_and_landing.py": "import crazyflie_behavior.drone.crazyflie.radio"},
        {"take_off_and_landing.py": "from crazyflie_behavior.drone.crazyflie import radio"},
        {"take_off_and_landing.py": "from crazyflie_behavior.drone.crazyflie.radio import send"},
        {"take_off_and_landing.py": "from . import radio"},
        {"take_off_and_landing.py": "from .radio import send"},
        {"take_off_and_landing.py": "def land():\n    from .radio import send"},
        {"take_off_and_landing.py": "if TYPE_CHECKING:\n    from .radio import Radio"},
        {"take_off_and_landing.py": "from .middle import x", "middle.py": "from .radio import send"},
        {"take_off_and_landing.py": "", "__init__.py": "from .radio import send"},
        {
            "take_off_and_landing.py": "from .parts.maths import y",
            "parts/__init__.py": "import cflib",
            "parts/maths.py": "",
        },
    ],
)
def test_the_import_follower_sees_every_import_statement_that_reaches_cflib(
    files: dict[str, str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Directly, through a module or a package in `src/`, inside a function, or for type checking only: a type-only
    import would still hand take-off and landing a cflib type."""
    take_off_and_landing = made_up_take_off_and_landing(tmp_path, monkeypatch, files)

    assert any(imports_any(path, ["cflib"]) for path in files_loaded_with(take_off_and_landing))


@pytest.mark.parametrize(
    "files",
    [
        {"take_off_and_landing.py": "import logging"},
        {"take_off_and_landing.py": "from . import touchdown", "touchdown.py": ""},
        {"take_off_and_landing.py": "from .touchdown import radio", "touchdown.py": "radio = 1"},
        {"take_off_and_landing.py": "from .radios import send"},
        {"take_off_and_landing.py": "# from .radio import send"},
        {"take_off_and_landing.py": 'TEXT = "from .radio import send"'},
    ],
)
def test_the_import_follower_does_not_see_a_near_miss(
    files: dict[str, str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    take_off_and_landing = made_up_take_off_and_landing(tmp_path, monkeypatch, files)

    assert not any(imports_any(path, ["cflib"]) for path in files_loaded_with(take_off_and_landing))


@pytest.mark.parametrize(
    "source",
    [
        "# pyright: basic",
        "#pyright: standard",
        "# pyright: strict",
        "# pyright: reportUnknownMemberType=false",
        "x = f()  # pyright: ignore[reportUnknownMemberType]",
        "x = f()  # cflib is untyped # pyright: ignore",
        "# type: ignore",
        "x = f()  # type: ignore[attr-defined]",
        "import math\nx = f()  # pyright: ignore[reportUnknownMemberType]",
    ],
)
def test_the_comment_scanner_sees_every_type_check_comment(source: str, tmp_path: Path) -> None:
    path = tmp_path / "made_up.py"
    path.write_text(source + "\n", encoding="utf-8")

    assert type_check_comments(path) != []


@pytest.mark.parametrize(
    "source",
    [
        'TEXT = "# pyright: basic"',
        '"""Unlike adapter.py, no # pyright: basic here."""',
        "# Strict typing: there are no cflib values to convert.",
        "x: list[int] = []  # type: list[int]",
    ],
)
def test_the_comment_scanner_does_not_see_a_near_miss(source: str, tmp_path: Path) -> None:
    path = tmp_path / "made_up.py"
    path.write_text(source + "\n", encoding="utf-8")

    assert type_check_comments(path) == []
