"""Fitness function: in the Crazyflie adapter, only `connect()` and `disconnect()` may block (ADR-0093).

Reads `drone/crazyflie/` without running it. A function blocks when it sleeps, waits or joins, or calls a function
that does. Calls match by name alone, so `x.emergency_stop()` counts as a call to every `emergency_stop`, and a name
imported under another name counts as the original (`pause` for `from time import sleep as pause`). A function
passed or stored as a value is run later through another name, which a check by name can't follow, so each such use
of a blocking function goes on an allow-list.
"""

import ast
from collections.abc import Collection
from pathlib import Path
from typing import NamedTuple

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = REPO_ROOT / "src" / "crazyflie_behavior"
CRAZYFLIE_ADAPTER_ROOT = PACKAGE_ROOT / "drone" / "crazyflie"
DRONE_INTERFACE = PACKAGE_ROOT / "drone" / "interface.py"

BLOCKING_CALLS = {
    "sleep",  # time.sleep
    "sleep_until",  # Clock.sleep_until
    "wait",  # threading.Event.wait
    "join",  # threading.Thread.join; a text literal's join is skipped
    "open_link",  # SyncCrazyflie.open_link: until the link is open
    "wait_for_params",  # SyncCrazyflie.wait_for_params: until every parameter has a value
    "close_link",  # SyncCrazyflie.close_link: until the link is closed
}
"""The calls that sleep, wait or join. Not counted: cflib's sends, which can wait during radio trouble (ADR-0027); its
parameter reads and writes, which wait only until every parameter has a value: `connect()` waits for that first; and
locks, held only for a quick read or write (the telemetry buffer's, `time_limit.py`'s)."""

MAY_BLOCK = {"connect", "disconnect"}
"""The drone interface's methods that may block: programs call them, never a tick (ARCHITECTURE.md section 3)."""

BLOCKING_FUNCTIONS = {
    "adapter.py::CrazyflieAdapter.connect",
    "adapter.py::CrazyflieAdapter.disconnect",
    "adapter.py::CrazyflieAdapter._close_link",
    "adapter.py::CrazyflieAdapter._land_silence_and_wait",
    "adapter.py::CrazyflieAdapter._shut_down_link",
    "adapter.py::CrazyflieAdapter._silence_and_keep_the_link_open",
    "adapter.py::CrazyflieAdapter._wait_for_drone_status",
    "adapter.py::CrazyflieAdapter._wait_for_first_telemetry",
    "adapter.py::CrazyflieAdapter._wait_for_not_flying",
    "adapter.py::CrazyflieAdapter._wait_until",
    "commands.py::land_as_a_last_resort",
    "link.py::CrazyflieLink.close",
    "link.py::CrazyflieLink.close_radio_link_only",
    "link.py::CrazyflieLink.open",
    "take_off_and_landing.py::TakeOffAndLanding.land_and_wait_for_touchdown",
    "time_limit.py::run_with_time_limit",
}
"""Every function in `drone/crazyflie/` that blocks, as "file::Class.method" or "file::function". One that starts
blocking goes on this list, so the change shows in review."""

ALLOWED_STORED_CALLABLES: dict[tuple[str, str], str] = {
    ("adapter.py::CrazyflieAdapter._land_silence_and_wait", "close_radio_link_only"): "land_as_a_last_resort runs it",
    ("link.py::CrazyflieLink.open", "open_link"): "run_with_time_limit's helper thread runs it",
    ("link.py::CrazyflieLink.open", "wait_for_params"): "run_with_time_limit's helper thread runs it",
    ("link.py::CrazyflieLink.open", "close_radio_link_only"): "run_with_time_limit runs it as on_abandon",
}
"""Blocking functions and calls used as a value: (the function that uses it, its name) to what runs it. Allowed only
when what it's passed to runs it, or waits for it, before returning: the function that passes it then blocks too."""


class Use(NamedTuple):
    """A name a function's code calls or uses as a value, and its line."""

    name: str
    line: int


class ScannedFunction:
    """The names one function's code calls and uses as values."""

    def __init__(self) -> None:
        self.calls: list[Use] = []
        """The calls in its own body."""
        self.values: list[Use] = []
        """Names it uses without calling them, and the calls inside its lambdas and nested functions: those run
        whenever the lambda or nested function is called, not where it's defined."""


class _Scanner:
    """Records what each function in one file names. Code outside any function counts as the file's `<module>`."""

    def __init__(self, file_name: str, aliases: dict[str, str]) -> None:
        self._file_name = file_name
        self._aliases = aliases
        """Each name the file imports under another name, to the original: `pause` to `sleep`."""
        self._class_names: list[str] = []
        self._function: str | None = None
        """The function or method being scanned, as "file::Class.method"."""
        self._is_deferred = False
        """Inside a lambda or a nested function."""
        self.functions: dict[str, ScannedFunction] = {}

    def scan(self, node: ast.AST) -> None:
        match node:
            case ast.ClassDef() if self._function is None:
                self._class_names.append(node.name)
                self._scan_children(node)
                self._class_names.pop()
            case ast.FunctionDef() | ast.AsyncFunctionDef() if self._function is None:
                self._function = f"{self._file_name}::{'.'.join([*self._class_names, node.name])}"
                self._current()
                self._scan_children(node)
                self._function = None
            case ast.FunctionDef() | ast.AsyncFunctionDef() | ast.Lambda():
                was_deferred, self._is_deferred = self._is_deferred, True
                self._scan_children(node)
                self._is_deferred = was_deferred
            case ast.Call():
                self._scan_call(node)
            case ast.Name(ctx=ast.Load()):
                self._current().values.append(Use(self._aliases.get(node.id, node.id), node.lineno))
            case ast.Attribute():
                if isinstance(node.ctx, ast.Load):
                    self._current().values.append(Use(node.attr, node.lineno))
                self.scan(node.value)
            case _:
                self._scan_children(node)

    def _scan_call(self, call: ast.Call) -> None:
        callee = call.func
        match callee:
            case ast.Name():
                self._record_call(Use(self._aliases.get(callee.id, callee.id), call.lineno))
            case ast.Attribute():
                if not _is_text_join(callee):
                    self._record_call(Use(callee.attr, call.lineno))
                self.scan(callee.value)
            case _:
                self.scan(callee)
        for argument in [*call.args, *(keyword.value for keyword in call.keywords)]:
            self.scan(argument)

    def _record_call(self, use: Use) -> None:
        function = self._current()
        (function.values if self._is_deferred else function.calls).append(use)

    def _scan_children(self, node: ast.AST) -> None:
        for child in ast.iter_child_nodes(node):
            self.scan(child)

    def _current(self) -> ScannedFunction:
        name = self._function or f"{self._file_name}::<module>"
        if name not in self.functions:
            self.functions[name] = ScannedFunction()
        return self.functions[name]


def _is_text_join(callee: ast.Attribute) -> bool:
    """`", ".join(parts)`, which joins text, not a thread."""
    return callee.attr == "join" and isinstance(callee.value, ast.Constant) and isinstance(callee.value.value, str)


def _import_aliases(tree: ast.AST) -> dict[str, str]:
    """Each name a file imports under another name, to the original's last part: `pause` to `sleep`."""
    return {
        alias.asname: alias.name.split(".")[-1]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import | ast.ImportFrom)
        for alias in node.names
        if alias.asname is not None and alias.asname != alias.name
    }


def scan_functions(root: Path) -> dict[str, ScannedFunction]:
    """Every function in the files under `root`, by "file::Class.method" or "file::function"."""
    functions: dict[str, ScannedFunction] = {}
    for path in sorted(root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        scanner = _Scanner(path.relative_to(root).as_posix(), _import_aliases(tree))
        scanner.scan(tree)
        functions.update(scanner.functions)
    return functions


def bare_name(function: str) -> str:
    """A function's own name, without its file and class."""
    return function.split("::")[-1].split(".")[-1]


def blocking_functions(functions: dict[str, ScannedFunction], allowed: Collection[tuple[str, str]]) -> dict[str, Use]:
    """Each function that blocks, with the first use that makes it block: a blocking call, a call to a function that
    blocks, or an allow-listed use of either as a value."""
    blocking: dict[str, Use] = {}
    names = set(BLOCKING_CALLS)
    while True:
        found: dict[str, Use] = {}
        for function, scanned in functions.items():
            allowed_values = [use for use in scanned.values if (function, use.name) in allowed]
            uses = [use for use in [*scanned.calls, *allowed_values] if use.name in names]
            if function not in blocking and uses:
                found[function] = min(uses, key=lambda use: use.line)
        if not found:
            return blocking
        blocking.update(found)
        names.update(bare_name(function) for function in found)


def blocking_values(functions: dict[str, ScannedFunction], blocking: Collection[str]) -> dict[tuple[str, str], Use]:
    """Each use of a blocking call or a blocking function as a value, by (the function that uses it, its name)."""
    names = BLOCKING_CALLS | {bare_name(function) for function in blocking}
    values: dict[tuple[str, str], Use] = {}
    for function, scanned in functions.items():
        for use in scanned.values:
            if use.name in names:
                values.setdefault((function, use.name), use)
    return values


def reached_from_connect_and_disconnect(
    functions: dict[str, ScannedFunction], blocking: Collection[str], allowed: Collection[tuple[str, str]]
) -> set[str]:
    """The blocking functions `connect()` and `disconnect()` run: themselves, and each one a reached function calls
    by name or runs through an allow-listed value."""
    by_name: dict[str, set[str]] = {}
    for function in blocking:
        by_name.setdefault(bare_name(function), set()).add(function)
    reached = {function for function in blocking if bare_name(function) in MAY_BLOCK}
    unvisited = list(reached)
    while unvisited:
        function = unvisited.pop()
        scanned = functions[function]
        names = {use.name for use in scanned.calls}
        names |= {use.name for use in scanned.values if (function, use.name) in allowed}
        for name in names:
            for callee in by_name.get(name, set()) - reached:
                reached.add(callee)
                unvisited.append(callee)
    return reached


def drone_interface_methods(path: Path = DRONE_INTERFACE) -> set[str]:
    """Every method `DroneInterface` declares, whatever decorates it, read from its class. Not those named with double
    underscores, such as `__enter__`: programs use them, as they do `connect()`."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    interface = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "DroneInterface")
    return {
        node.name
        for node in interface.body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and not node.name.startswith("__")
    }


# --- The rules, on the Crazyflie adapter -------------------------------------


def test_no_drone_interface_method_blocks_but_connect_and_disconnect() -> None:
    """A tick calls the drone interface's other methods, and nothing in a tick may wait (ARCHITECTURE.md section 5)."""
    functions = scan_functions(CRAZYFLIE_ADAPTER_ROOT)
    blocking = blocking_functions(functions, ALLOWED_STORED_CALLABLES)
    tick_methods = drone_interface_methods() - MAY_BLOCK

    offenders = [
        f"{function} blocks: {use.name} at line {use.line}"
        for function, use in sorted(blocking.items())
        if bare_name(function) in tick_methods
    ]

    assert offenders == []


def test_every_blocking_function_is_reached_from_connect_or_disconnect() -> None:
    """Anything that calls a blocking function blocks too, so it must be reached from them as well. With the first
    rule, no tick reaches one, and with the allow-list rule, none runs as a stored callable. Also catches a blocking
    function that nothing in the package calls by name: a constructor, a cflib callback, or one only code outside the
    package calls."""
    functions = scan_functions(CRAZYFLIE_ADAPTER_ROOT)
    blocking = blocking_functions(functions, ALLOWED_STORED_CALLABLES)

    unreached = blocking.keys() - reached_from_connect_and_disconnect(functions, blocking, ALLOWED_STORED_CALLABLES)

    assert sorted(unreached) == []


def test_every_blocking_function_used_as_a_value_is_allow_listed() -> None:
    functions = scan_functions(CRAZYFLIE_ADAPTER_ROOT)
    blocking = blocking_functions(functions, ALLOWED_STORED_CALLABLES)

    offenders = [
        f"{function} uses {name} as a value at line {use.line}"
        for (function, name), use in sorted(blocking_values(functions, blocking).items())
        if (function, name) not in ALLOWED_STORED_CALLABLES
    ]

    assert offenders == []


def test_the_list_of_blocking_functions_is_current() -> None:
    functions = scan_functions(CRAZYFLIE_ADAPTER_ROOT)
    blocking = blocking_functions(functions, ALLOWED_STORED_CALLABLES)

    unlisted = [
        f"{function} blocks but isn't listed: {use.name} at line {use.line}"
        for function, use in sorted(blocking.items())
        if function not in BLOCKING_FUNCTIONS
    ]
    no_longer_blocking = [
        f"{function} is listed but doesn't block" for function in sorted(BLOCKING_FUNCTIONS - blocking.keys())
    ]

    assert [*unlisted, *no_longer_blocking] == []


def test_every_allow_listed_value_is_still_used() -> None:
    functions = scan_functions(CRAZYFLIE_ADAPTER_ROOT)
    blocking = blocking_functions(functions, ALLOWED_STORED_CALLABLES)

    unused = ALLOWED_STORED_CALLABLES.keys() - blocking_values(functions, blocking).keys()

    assert sorted(unused) == []


def test_the_scanner_reads_the_drone_interface_methods() -> None:
    """Guards the first rule: with no methods read, it would pass for the wrong reason."""
    assert drone_interface_methods() >= {
        "connect",
        "disconnect",
        "take_snapshot",
        "update_take_off_and_landing",
        "land",
    }


def test_the_scanner_reads_every_drone_interface_method_whatever_decorates_it(tmp_path: Path) -> None:
    path = tmp_path / "interface.py"
    path.write_text(
        """\
import abc
from abc import abstractmethod


class DroneInterface(abc.ABC):
    def __enter__(self):
        self.connect()

    @abstractmethod
    def land(self): ...

    @abc.abstractmethod
    def go_to(self): ...

    @property
    @abstractmethod
    def is_flying(self): ...

    def hover(self): ...
""",
        encoding="utf-8",
    )

    assert drone_interface_methods(path) == {"land", "go_to", "is_flying", "hover"}


# --- Each form the scanner handles, on made-up code --------------------------

MADE_UP_ADAPTER = """\
import time
from time import sleep
from time import sleep as pause


def wait_for_it(clock):
    clock.sleep_until(1.0)


class Adapter:
    def _wait(self):
        self._clock.sleep_until(1.0)

    def update(self, parts, run):
        BODY
"""
UPDATE = "made_up.py::Adapter.update"


def scan_made_up_adapter(tmp_path: Path, body: str) -> dict[str, ScannedFunction]:
    """Scans `MADE_UP_ADAPTER` with `body` as `update`'s body. A body's own lines are indented by four spaces."""
    source = MADE_UP_ADAPTER.replace("BODY", body.replace("\n", "\n        "))
    (tmp_path / "made_up.py").write_text(source, encoding="utf-8")
    return scan_functions(tmp_path)


@pytest.mark.parametrize(
    "body",
    [
        "self._clock.sleep_until(1.0)",
        "time.sleep(0.1)",
        "sleep(0.1)",
        "pause(0.1)",
        "self._finished.wait(0.1)",
        "self._thread.join(timeout=1)",
        "self._sync_crazyflie.open_link()",
        "self._sync_crazyflie.wait_for_params()",
        "self._sync_crazyflie.close_link()",
        "self._wait()",
        "wait_for_it(self._clock)",
        "with self._lock:\n    self._wait()",
        "run(self._wait())",
        "self._wait().stop()",
        "factory(self._wait())()",
    ],
)
def test_the_scanner_sees_every_form_of_a_blocking_call(body: str, tmp_path: Path) -> None:
    functions = scan_made_up_adapter(tmp_path, body)

    assert UPDATE in blocking_functions(functions, allowed=())


@pytest.mark.parametrize(
    ("import_line", "call"),
    [
        ("from time_limit import run_with_time_limit", "run_with_time_limit(self._event)"),
        ("from time_limit import run_with_time_limit as run_limited", "run_limited(self._event)"),
    ],
)
def test_the_scanner_sees_a_call_to_a_blocking_function_in_another_file(
    import_line: str, call: str, tmp_path: Path
) -> None:
    (tmp_path / "time_limit.py").write_text("def run_with_time_limit(event):\n    event.wait(0.1)\n", encoding="utf-8")
    (tmp_path / "adapter.py").write_text(
        f"{import_line}\n\n\nclass Adapter:\n    def connect(self):\n        {call}\n",
        encoding="utf-8",
    )

    assert "adapter.py::Adapter.connect" in blocking_functions(scan_functions(tmp_path), allowed=())


@pytest.mark.parametrize(
    "source",
    [
        "import time\n\ntime.sleep(1)\n",
        "import time\n\n\nclass Adapter:\n    PAUSE = time.sleep(1)\n",
    ],
)
def test_the_scanner_counts_code_outside_any_function_as_the_module(source: str, tmp_path: Path) -> None:
    """Code run at import or in a class body; no `connect()` reaches it, so the reach rule fails on it."""
    (tmp_path / "made_up.py").write_text(source, encoding="utf-8")

    assert "made_up.py::<module>" in blocking_functions(scan_functions(tmp_path), allowed=())


@pytest.mark.parametrize(
    "body",
    [
        "', '.join(parts)",
        "print(f\"Missing: {', '.join(parts)}.\")",
        "self._log_config.stop()",
        "self.waiting()",
        "print('self._wait()')",
        "pass  # self._wait()",
        "run(self._wait)",
        "run(lambda: self._wait())",
    ],
)
def test_the_scanner_does_not_see_a_near_miss(body: str, tmp_path: Path) -> None:
    """The last two use a blocking function as a value: the allow-list rule judges those, not this one."""
    functions = scan_made_up_adapter(tmp_path, body)

    assert UPDATE not in blocking_functions(functions, allowed=())


@pytest.mark.parametrize(
    ("body", "name"),
    [
        ("run(on_abandon=self._wait)", "_wait"),
        ("run(self._wait)", "_wait"),
        ("self._stored = self._wait", "_wait"),
        ("return self._wait", "_wait"),
        ("run([wait_for_it])", "wait_for_it"),
        ("run(self._sync_crazyflie.open_link)", "open_link"),
        ("run(lambda: self._wait())", "_wait"),
        ("def inner():\n    self._wait()\nrun(inner)", "_wait"),
        ("class Inner:\n    def go(self):\n        self._wait()\nrun(Inner)", "_wait"),
        ("run(pause)", "sleep"),
    ],
)
def test_the_scanner_sees_every_form_of_a_blocking_function_used_as_a_value(
    body: str, name: str, tmp_path: Path
) -> None:
    functions = scan_made_up_adapter(tmp_path, body)
    blocking = blocking_functions(functions, allowed=())

    assert (UPDATE, name) in blocking_values(functions, blocking)


def test_an_allow_listed_value_blocks_the_function_that_uses_it(tmp_path: Path) -> None:
    functions = scan_made_up_adapter(tmp_path, "run(on_abandon=self._wait)")

    assert UPDATE in blocking_functions(functions, allowed={(UPDATE, "_wait")})


def test_the_scanner_sees_what_connect_and_disconnect_reach(tmp_path: Path) -> None:
    """Calls by name and allow-listed values reach; a blocking constructor and a blocking callback don't."""
    (tmp_path / "made_up.py").write_text(
        """\
class Adapter:
    def __init__(self, clock):
        clock.sleep_until(1.0)

    def connect(self):
        self._wait()
        self._log.add_callback(self._on_state)

    def disconnect(self):
        run(on_abandon=self._close)

    def _wait(self):
        self._clock.sleep_until(1.0)

    def _close(self):
        self._thread.join(timeout=1)

    def _on_state(self, data):
        self._wait()
""",
        encoding="utf-8",
    )
    functions = scan_functions(tmp_path)
    allowed = {("made_up.py::Adapter.disconnect", "_close")}
    blocking = blocking_functions(functions, allowed)

    unreached = blocking.keys() - reached_from_connect_and_disconnect(functions, blocking, allowed)

    assert unreached == {"made_up.py::Adapter.__init__", "made_up.py::Adapter._on_state"}
