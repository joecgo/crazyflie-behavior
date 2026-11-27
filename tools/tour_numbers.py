"""Writes the code's numbers into the project tour's pages, read at the commit the page's links are pinned to.

Run it after moving a page's pin. tests/docs/test_tour_numbers.py fails while a page differs from what it writes.

    .venv\\Scripts\\python tools/tour_numbers.py
"""

import ast
import json
import re
import subprocess
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TOUR_ROOT = REPO_ROOT / "docs" / "tour"
REPOSITORY_URL = "https://github.com/joecgo/crazyflie-behavior"
PINNED_COMMIT = re.compile(re.escape(REPOSITORY_URL) + r"/(?:blob|tree)/(?P<commit>[0-9a-f]{40})/")
"""A link pinned to a full commit hash, as the link test reads it."""

ADAPTER = "src/crazyflie_behavior/drone/crazyflie/"


class TourNumbersError(Exception):
    """A page or the code can't give the tour a number it names."""


@dataclass(frozen=True, slots=True)
class ConstantSpec:
    """A constant the tour shows: its module and its unit's symbol."""

    name: str
    path: str
    unit: str


CONSTANTS = (
    ConstantSpec("TOUCHDOWN_DOWN_RANGE", "src/crazyflie_behavior/drone/interface.py", "m"),
    ConstantSpec("FLOW_VELOCITY_UNCERTAINTY", "src/crazyflie_behavior/drone/interface.py", "m/s"),
    ConstantSpec("STALE_AFTER", "src/crazyflie_behavior/drone/interface.py", "s"),
    ConstantSpec("INITIAL_CLIMB_SPEED", ADAPTER + "bad_flow_zone.py", "m/s"),
    ConstantSpec("FINAL_DESCENT_SPEED", ADAPTER + "bad_flow_zone.py", "m/s"),
    ConstantSpec("FINAL_DESCENT_HEIGHT", ADAPTER + "bad_flow_zone.py", "m"),
    ConstantSpec("INITIAL_CLIMB_TIME_LIMIT", ADAPTER + "bad_flow_zone.py", "s"),
    ConstantSpec("LANDING_APPROACH_AIM_BELOW", ADAPTER + "take_off_and_landing.py", "m"),
    ConstantSpec("LANDING_APPROACH_BACKUP", ADAPTER + "take_off_and_landing.py", "s"),
    ConstantSpec("VERTICAL_SPEED", ADAPTER + "take_off_and_landing.py", "m/s"),
    ConstantSpec("HOVER_SETTLE_DURATION", ADAPTER + "take_off_and_landing.py", "s"),
    ConstantSpec("MIN_MOVE_DURATION", ADAPTER + "take_off_and_landing.py", "s"),
    ConstantSpec("TOUCHDOWN_HOLD", ADAPTER + "touchdown.py", "s"),
    ConstantSpec("RECENT_WINDOW", ADAPTER + "touchdown.py", "s"),
    ConstantSpec("SLOW_DESCENT_SPEED", ADAPTER + "touchdown.py", "m/s"),
    ConstantSpec("FINAL_DESCENT_MARGIN", ADAPTER + "touchdown.py", "s"),
    ConstantSpec("HEIGHT_IF_UNKNOWN", ADAPTER + "touchdown.py", "m"),
    ConstantSpec("STATE_PERIOD_MS", ADAPTER + "log_blocks.py", "ms"),
    ConstantSpec("DOWN_RANGE_PERIOD_MS", ADAPTER + "log_blocks.py", "ms"),
    ConstantSpec("MULTIRANGER_PERIOD_MS", ADAPTER + "log_blocks.py", "ms"),
    ConstantSpec("BATTERY_PERIOD_MS", ADAPTER + "log_blocks.py", "ms"),
    ConstantSpec("LOG_TIMESTAMP_RANGE_MS", ADAPTER + "conversions.py", "ms"),
    ConstantSpec("TICK_RATE", "src/crazyflie_behavior/loop/tick_loop.py", "Hz"),
    ConstantSpec("BATTERY_STALE_AFTER", "src/crazyflie_behavior/safety/safety_layer.py", "s"),
)


@dataclass(frozen=True, slots=True)
class FormulaSpec:
    """A number the tour works out from constants, written as a formula in their names."""

    key: str
    formula: str
    unit: str
    description: str


FORMULAS = (
    FormulaSpec(
        "deadline-at-final-descent-height",
        "FINAL_DESCENT_HEIGHT / FINAL_DESCENT_SPEED + FINAL_DESCENT_MARGIN",
        "s",
        "How long after the final descent starts its deadline comes, when the highest recent down range is the "
        "final descent height.",
    ),
    FormulaSpec(
        "deadline-without-down-range",
        "HEIGHT_IF_UNKNOWN / SLOW_DESCENT_SPEED + FINAL_DESCENT_MARGIN",
        "s",
        "How long after the final descent starts its deadline comes, with no recent down range: a slow descent "
        "from the most the drone could be above the floor.",
    ),
    FormulaSpec(
        "landing-approach-aim",
        "FINAL_DESCENT_HEIGHT - LANDING_APPROACH_AIM_BELOW",
        "m",
        "The height the landing approach aims at.",
    ),
)


@dataclass(frozen=True, slots=True)
class CodeConstant:
    """A constant as it is at one commit."""

    name: str
    path: str
    unit: str
    value: float
    code: str
    """The assignment as written, such as `STALE_AFTER = 0.25`."""
    first_line: int
    last_line: int
    """The end of its docstring, or of the assignment when it has none."""
    description: str
    """Its docstring on one line, without placeholder marks, or empty."""


@dataclass(frozen=True, slots=True)
class FormulaValue:
    key: str
    formula: str
    unit: str
    value: float
    worked: str
    """The formula with each constant's value in place of its name."""
    uses: tuple[str, ...]
    description: str


@dataclass(frozen=True, slots=True)
class TourNumbers:
    commit: str
    constants: Mapping[str, CodeConstant]
    formulas: Mapping[str, FormulaValue]
    adr_files: Mapping[str, str]
    """Each ADR number, such as `0081`, to its file in docs/decisions/."""


# --- Reading the code -----------------------------------------------------------------------------------------

_PLACEHOLDER_SENTENCE = re.compile(r"\s*VERIFY\b[^.]*\.")
"""A sentence that marks a value to verify. The tour shows no placeholder marks."""


def evaluate(node: ast.expr, names: Mapping[str, float]) -> float:
    """A number from a literal, a name in `names`, or arithmetic on those. Anything else raises."""
    if isinstance(node, ast.Constant) and isinstance(node.value, int | float) and not isinstance(node.value, bool):
        return node.value
    if isinstance(node, ast.Name) and node.id in names:
        return names[node.id]
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -evaluate(node.operand, names)
    if isinstance(node, ast.BinOp):
        left = evaluate(node.left, names)
        right = evaluate(node.right, names)
        match node.op:
            case ast.Add():
                return left + right
            case ast.Sub():
                return left - right
            case ast.Mult():
                return left * right
            case ast.Div():
                return left / right
            case ast.LShift() if isinstance(left, int) and isinstance(right, int):
                return left << right
            case _:
                pass
    raise TourNumbersError(f"not a number the tour can work out: {ast.unparse(node)}")


def _assignment(statement: ast.stmt) -> tuple[str, ast.expr] | None:
    """The name and value of a top-level `NAME = value` or `NAME: type = value`."""
    if isinstance(statement, ast.Assign) and len(statement.targets) == 1 and isinstance(statement.targets[0], ast.Name):
        return statement.targets[0].id, statement.value
    if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name) and statement.value is not None:
        return statement.target.id, statement.value
    return None


def _docstring(statement: ast.stmt | None) -> str | None:
    """The text of a bare string statement: an attribute docstring when it follows an assignment."""
    if (
        isinstance(statement, ast.Expr)
        and isinstance(statement.value, ast.Constant)
        and isinstance(statement.value.value, str)
    ):
        return statement.value.value
    return None


def read_constant(source: str, spec: ConstantSpec) -> CodeConstant:
    """`spec`'s value, lines and docstring from a module's source, without running it."""
    body = ast.parse(source).body
    found = [
        (index, assignment[1])
        for index, statement in enumerate(body)
        if (assignment := _assignment(statement)) is not None and assignment[0] == spec.name
    ]
    if len(found) != 1:
        raise TourNumbersError(f"{spec.path}: {spec.name} is assigned {len(found)} times at the top level, not once")
    index, value_node = found[0]
    statement = body[index]
    following = body[index + 1] if index + 1 < len(body) else None
    docstring = _docstring(following)
    end = following.end_lineno if following is not None and docstring is not None else statement.end_lineno
    description = " ".join((docstring or "").split())
    return CodeConstant(
        name=spec.name,
        path=spec.path,
        unit=spec.unit,
        value=evaluate(value_node, {}),
        code=f"{spec.name} = {ast.get_source_segment(source, value_node)}",
        first_line=statement.lineno,
        last_line=end or statement.lineno,
        description=_PLACEHOLDER_SENTENCE.sub("", description).strip(),
    )


def work_out(spec: FormulaSpec, constants: Mapping[str, CodeConstant]) -> FormulaValue:
    tree = ast.parse(spec.formula, mode="eval")
    uses = tuple(dict.fromkeys(node.id for node in ast.walk(tree) if isinstance(node, ast.Name)))
    missing = [name for name in uses if name not in constants]
    if missing:
        raise TourNumbersError(f"the formula {spec.key} uses constants the tour doesn't read: {', '.join(missing)}")
    value = evaluate(tree.body, {name: constants[name].value for name in uses})
    worked = re.sub(r"\b[A-Z][A-Z0-9_]*\b", lambda match: constant_text(constants[match.group(0)]), spec.formula)
    return FormulaValue(spec.key, spec.formula, spec.unit, value, worked, uses, " ".join(spec.description.split()))


# --- Writing numbers ------------------------------------------------------------------------------------------


def number_text(value: float) -> str:
    """The shortest plain form: 1 not 1.0, 0.1 not 0.09999999999999999, and thousands with commas."""
    rounded = round(value, 6)
    if rounded == int(rounded):
        return f"{int(rounded):,}"
    return f"{rounded:g}"


def constant_text(constant: CodeConstant) -> str:
    return f"{number_text(constant.value)} {constant.unit}"


FORMS: Mapping[str, tuple[str | None, Callable[[float], str]]] = {
    "number": (None, number_text),
    "hz": ("ms", lambda ms: f"{number_text(1000 / ms)} Hz"),
    "s": ("ms", lambda ms: f"{number_text(ms / 1000)} s"),
    "cm": ("m", lambda m: f"{number_text(m * 100)} cm"),
    "hours": ("ms", lambda ms: f"{ms / 3_600_000:.1f} hours"),
}
"""Other ways a page may show a constant (`data-form`): each needs the constant's unit, or any unit for None."""


def shown(constant: CodeConstant, form: str | None) -> str:
    if form is None:
        return constant_text(constant)
    if form not in FORMS:
        raise TourNumbersError(f'{constant.name}: no form "{form}"; the forms are {", ".join(FORMS)}')
    unit, write = FORMS[form]
    if unit is not None and constant.unit != unit:
        raise TourNumbersError(f'{constant.name}: the form "{form}" needs {unit}, not {constant.unit}')
    return write(constant.value)


def code_url(commit: str, constants: list[CodeConstant]) -> str:
    """A link to the constants' lines, from the first assignment to the end of the last docstring."""
    first = min(constant.first_line for constant in constants)
    last = max(constant.last_line for constant in constants)
    lines = f"L{first}" if first == last else f"L{first}-L{last}"
    return f"{REPOSITORY_URL}/blob/{commit}/{constants[0].path}#{lines}"


def code_label(constants: list[CodeConstant]) -> str:
    """The file's name and the lines the constants are assigned on, such as `log_blocks.py 39-45`."""
    first = min(constant.first_line for constant in constants)
    last = max(constant.first_line for constant in constants)
    name = constants[0].path.rsplit("/", 1)[-1]
    return f"{name} {first}" if first == last else f"{name} {first}-{last}"


def adr_url(numbers: TourNumbers, adr: str) -> str:
    if adr not in numbers.adr_files:
        raise TourNumbersError(f"ADR-{adr} has no file in docs/decisions/ at {numbers.commit[:7]}")
    return f"{REPOSITORY_URL}/blob/{numbers.commit}/docs/decisions/{numbers.adr_files[adr]}"


def numbers_json(numbers: TourNumbers) -> str:
    """What tour.js reads: every constant and formula, with its text, code, link and description."""
    cited = {adr for constant in numbers.constants.values() for adr in re.findall(r"ADR-(\d{4})", constant.description)}
    data = {
        "commit": numbers.commit,
        "constants": {
            constant.name: {
                "value": constant.value,
                "text": constant_text(constant),
                "code": constant.code,
                "description": constant.description,
                "url": code_url(numbers.commit, [constant]),
                "label": code_label([constant]),
            }
            for constant in numbers.constants.values()
        },
        "formulas": {
            formula.key: {
                "value": formula.value,
                "text": f"{number_text(formula.value)} {formula.unit}",
                "formula": formula.formula,
                "worked": formula.worked,
                "uses": list(formula.uses),
                "description": formula.description,
            }
            for formula in numbers.formulas.values()
        },
        "adrs": {f"ADR-{adr}": adr_url(numbers, adr) for adr in sorted(cited)},
    }
    return json.dumps(data, indent=1, ensure_ascii=False).replace("</", "<\\/")


# --- Pages ----------------------------------------------------------------------------------------------------

_ATTRIBUTE = re.compile(r'([\w-]+)="([^"]*)"')
_NUMBER_ELEMENT = re.compile(
    r'<(?P<tag>span|tspan)(?P<attrs>\s[^>]*?\bdata-(?:const|formula)="[^"]*"[^>]*)>(?P<text>[^<]*)</(?P=tag)>'
)
"""An element showing one number: a constant (`data-const`, with an optional `data-form`) or a formula's."""
_CONSTANT_LINK = re.compile(r'<a(?P<attrs>\s[^>]*?\bdata-const-link="[^"]*"[^>]*)>(?P<text>[^<]*)</a>')
"""A link to one or more constants' lines, in one file."""
_NUMBERS_SCRIPT = re.compile(r'(<script type="application/json" id="tour-numbers">)(.*?)(</script>)', re.DOTALL)


def pinned_commit(page: str) -> str:
    """The one commit every pinned link on the page names."""
    commits = sorted(set(PINNED_COMMIT.findall(page)))
    if len(commits) != 1:
        raise TourNumbersError(f"the page's links name {len(commits)} commits, not one: {', '.join(commits)}")
    return commits[0]


def _number_element(match: re.Match[str], numbers: TourNumbers) -> str:
    attributes = dict(_ATTRIBUTE.findall(match.group("attrs")))
    if "data-formula" in attributes:
        key = attributes["data-formula"]
        if key not in numbers.formulas or "data-form" in attributes:
            raise TourNumbersError(f'no formula "{key}" in tools/tour_numbers.py, or it has a data-form it can\'t take')
        formula = numbers.formulas[key]
        text = f"{number_text(formula.value)} {formula.unit}"
    else:
        name = attributes["data-const"]
        if name not in numbers.constants:
            raise TourNumbersError(f"the page shows {name}, which tools/tour_numbers.py doesn't read")
        text = shown(numbers.constants[name], attributes.get("data-form"))
    # A number never wraps away from its unit.
    return f"<{match.group('tag')}{match.group('attrs')}>{text.replace(' ', '&nbsp;')}</{match.group('tag')}>"


def _constant_link(match: re.Match[str], numbers: TourNumbers) -> str:
    attrs = match.group("attrs")
    names = dict(_ATTRIBUTE.findall(attrs))["data-const-link"].split()
    unknown = [name for name in names if name not in numbers.constants]
    if unknown:
        raise TourNumbersError(f"the page links {', '.join(unknown)}, which tools/tour_numbers.py doesn't read")
    constants = [numbers.constants[name] for name in names]
    if len({constant.path for constant in constants}) != 1:
        raise TourNumbersError(f"one link can't span two files: {' '.join(names)}")
    if 'href="' not in attrs:
        raise TourNumbersError(f"the link to {' '.join(names)} has no href")
    attrs = re.sub(r'href="[^"]*"', f'href="{code_url(numbers.commit, constants)}"', attrs)
    return f"<a{attrs}>{code_label(constants)}</a>"


def render_page(page: str, numbers: TourNumbers) -> str:
    """The page with every number, every constant link and the tour-numbers script written from `numbers`."""
    if len(_NUMBERS_SCRIPT.findall(page)) != 1:
        raise TourNumbersError('a page needs one <script type="application/json" id="tour-numbers">')
    page = _NUMBER_ELEMENT.sub(lambda match: _number_element(match, numbers), page)
    page = _CONSTANT_LINK.sub(lambda match: _constant_link(match, numbers), page)
    written = numbers_json(numbers)
    return _NUMBERS_SCRIPT.sub(lambda match: f"{match.group(1)}\n{written}\n{match.group(3)}", page)


# --- Git ------------------------------------------------------------------------------------------------------


def _git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, check=False, timeout=60)
    if result.returncode != 0:
        raise TourNumbersError(f"git {' '.join(args)}: {result.stderr.decode('utf-8', 'replace').strip()}")
    return result.stdout.decode("utf-8")


def load_numbers(commit: str) -> TourNumbers:
    """Every constant and formula the tour shows, read at `commit`."""
    sources = {path: _git("show", f"{commit}:{path}") for path in sorted({spec.path for spec in CONSTANTS})}
    constants = {spec.name: read_constant(sources[spec.path], spec) for spec in CONSTANTS}
    formulas = {spec.key: work_out(spec, constants) for spec in FORMULAS}
    adr_files: dict[str, str] = {}
    for line in _git("ls-tree", "--name-only", commit, "docs/decisions/").splitlines():
        name = line.rsplit("/", 1)[-1]
        if re.fullmatch(r"\d{4}-.*\.md", name):
            adr_files[name[:4]] = name
    return TourNumbers(commit, constants, formulas, adr_files)


def tour_pages() -> list[Path]:
    return sorted(TOUR_ROOT.glob("*.html"))


def written_page(path: Path) -> tuple[str, str]:
    """The page as it is, and as this script writes it."""
    page = path.read_text(encoding="utf-8")
    return page, render_page(page, load_numbers(pinned_commit(page)))


def main() -> int:
    for path in tour_pages():
        page, written = written_page(path)
        name = path.relative_to(REPO_ROOT).as_posix()
        if written == page:
            print(f"{name} is up to date")
        else:
            path.write_text(written, encoding="utf-8", newline="\n")
            print(f"wrote {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
