"""The project tour shows the code's numbers as they are at the commit its links are pinned to.

tools/tour_numbers.py writes them into each page; these tests fail while a page differs from what it writes.
Decided 2026-11-26 with the tour's first chapter; its ADR follows pass one.
"""

import difflib
import re

import pytest
from tools.tour_numbers import (
    CONSTANTS,
    TOUR_ROOT,
    CodeConstant,
    ConstantSpec,
    FormulaSpec,
    TourNumbers,
    TourNumbersError,
    load_numbers,
    pinned_commit,
    read_constant,
    render_page,
    shown,
    tour_pages,
    work_out,
    written_page,
)

FAKE_COMMIT = "0" * 40
FAKE_PAGE_LINK = f"https://github.com/joecgo/crazyflie-behavior/blob/{FAKE_COMMIT}/README.md"
SOURCE = '''"""A module."""

# A comment.
SPEED = 0.4
"""Meters per second: up.
Over two lines. VERIFY at the bench."""
PERIOD_MS = 20
RANGE_MS = 1 << 24
"""Counts (ADR-0023)."""
'''


def constant(name: str, unit: str) -> CodeConstant:
    return read_constant(SOURCE, ConstantSpec(name, "src/module.py", unit))


def fake_numbers() -> TourNumbers:
    constants = {c.name: c for c in (constant("SPEED", "m/s"), constant("PERIOD_MS", "ms"), constant("RANGE_MS", "ms"))}
    halved = work_out(FormulaSpec("halved", "SPEED / 2", "m/s", "Half the speed."), constants)
    return TourNumbers(FAKE_COMMIT, constants, {"halved": halved}, {"0023": "0023-tick-rate-20-hz.md"})


def fake_page(body: str) -> str:
    return f'<a href="{FAKE_PAGE_LINK}">x</a>{body}<script type="application/json" id="tour-numbers"></script>'


# --- The committed pages ---------------------------------------------------------------------------------------


def test_every_tour_page_matches_what_tools_tour_numbers_writes() -> None:
    pages = tour_pages()
    assert pages, f"no pages in {TOUR_ROOT}"
    for path in pages:
        page, written = written_page(path)
        stale = list(difflib.unified_diff(page.splitlines(), written.splitlines(), lineterm="", n=0))
        assert stale == [], f"{path.name} is out of date: run .venv\\Scripts\\python tools/tour_numbers.py"


def test_the_tour_shows_numbers_from_the_code() -> None:
    """Guards the page test: a page with no marked numbers would match whatever the script reads."""
    page = (TOUR_ROOT / "adapter.html").read_text(encoding="utf-8")
    assert len(re.findall(r'\bdata-(?:const|formula)="', page)) >= 50
    assert len(re.findall(r'\bdata-const-link="', page)) >= 15


def test_every_number_tour_js_reads_is_one_the_page_holds() -> None:
    script = (TOUR_ROOT / "tour.js").read_text(encoding="utf-8")
    names = set(re.findall(r'"([A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+)"', script))
    assert len(names) >= 15, "the scanner found too few: has tour.js stopped reading numbers by name?"
    assert names - {spec.name for spec in CONSTANTS} == set()


def test_each_unit_agrees_with_the_constants_docstring_or_name() -> None:
    """The units in tools/tour_numbers.py are typed by hand; the code says them in a docstring or a name."""
    page = (TOUR_ROOT / "adapter.html").read_text(encoding="utf-8")
    numbers = load_numbers(pinned_commit(page))
    said = {"Meters per second": "m/s", "Meters": "m", "Seconds": "s", "Ticks per second": "Hz"}
    checked = 0
    for constant in numbers.constants.values():
        unit = "ms" if constant.name.endswith("_MS") else None
        for words, symbol in said.items():
            if constant.description.startswith(words):
                unit = symbol
                break
        if unit is not None:
            assert constant.unit == unit, constant.name
            checked += 1
    assert checked >= 20


def test_no_description_carries_a_placeholder_mark() -> None:
    page = (TOUR_ROOT / "adapter.html").read_text(encoding="utf-8")
    numbers = load_numbers(pinned_commit(page))
    marked = [c.name for c in numbers.constants.values() if re.search(r"PLACEHOLDER|VERIFY", c.description, re.I)]
    assert marked == []


# --- Reading the code ------------------------------------------------------------------------------------------


def test_a_constant_is_read_with_its_value_code_lines_and_docstring() -> None:
    speed = constant("SPEED", "m/s")

    assert (speed.value, speed.code, speed.first_line, speed.last_line) == (0.4, "SPEED = 0.4", 4, 6)
    assert speed.description == "Meters per second: up. Over two lines."


def test_a_constant_without_a_docstring_ends_on_its_own_line() -> None:
    period = constant("PERIOD_MS", "ms")

    assert (period.value, period.first_line, period.last_line, period.description) == (20, 7, 7, "")


def test_a_constant_may_be_arithmetic_on_literals() -> None:
    assert constant("RANGE_MS", "ms").value == 16_777_216


@pytest.mark.parametrize(
    "source",
    ['SPEED = "fast"\n', "SPEED = 0.4\nSPEED = 0.5\n", "OTHER = 1\n", "SPEED = math.pi\n", "if True:\n    SPEED = 1\n"],
    ids=["not a number", "assigned twice", "missing", "a call", "not at the top level"],
)
def test_a_constant_the_tour_cant_read_raises(source: str) -> None:
    with pytest.raises(TourNumbersError):
        read_constant(source, ConstantSpec("SPEED", "src/module.py", "m/s"))


def test_a_formula_is_worked_out_from_the_constants() -> None:
    halved = fake_numbers().formulas["halved"]

    assert (halved.value, halved.worked, halved.uses) == (0.2, "0.4 m/s / 2", ("SPEED",))


def test_a_formula_with_a_constant_the_tour_doesnt_read_raises() -> None:
    with pytest.raises(TourNumbersError, match="OTHER"):
        work_out(FormulaSpec("x", "SPEED + OTHER", "m/s", ""), fake_numbers().constants)


# --- Writing numbers -------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("name", "form", "expected"),
    [
        ("SPEED", None, "0.4 m/s"),
        ("PERIOD_MS", None, "20 ms"),
        ("PERIOD_MS", "hz", "50 Hz"),
        ("PERIOD_MS", "s", "0.02 s"),
        ("RANGE_MS", "number", "16,777,216"),
        ("RANGE_MS", "hours", "4.7 hours"),
    ],
)
def test_a_constant_is_shown_in_its_form(name: str, form: str | None, expected: str) -> None:
    assert shown(fake_numbers().constants[name], form) == expected


def test_a_length_is_shown_in_centimeters() -> None:
    aim = read_constant("AIM = 0.05\n", ConstantSpec("AIM", "src/module.py", "m"))

    assert shown(aim, "cm") == "5 cm"


@pytest.mark.parametrize("form", ["hz", "cm", "furlongs"])
def test_a_form_for_another_unit_or_no_form_raises(form: str) -> None:
    with pytest.raises(TourNumbersError):
        shown(fake_numbers().constants["SPEED"], form)


# --- Pages -----------------------------------------------------------------------------------------------------


def test_the_page_gets_each_number_its_constant_link_and_the_numbers_script() -> None:
    page = fake_page(
        '<span class="from-code" data-const="SPEED">?</span>'
        '<tspan data-const="PERIOD_MS" data-form="hz">?</tspan>'
        '<span data-formula="halved">?</span>'
        '<a class="src" data-const-link="SPEED" href="">?</a>'
        '<a class="src" data-const-link="PERIOD_MS SPEED" href="old">?</a>'
    )

    written = render_page(page, fake_numbers())

    assert '<span class="from-code" data-const="SPEED">0.4&nbsp;m/s</span>' in written
    assert '<tspan data-const="PERIOD_MS" data-form="hz">50&nbsp;Hz</tspan>' in written
    assert '<span data-formula="halved">0.2&nbsp;m/s</span>' in written
    assert f'href="https://github.com/joecgo/crazyflie-behavior/blob/{FAKE_COMMIT}/src/module.py#L4-L6">' in written
    assert f'href="https://github.com/joecgo/crazyflie-behavior/blob/{FAKE_COMMIT}/src/module.py#L4-L7">' in written
    assert ">module.py 4</a>" in written
    assert ">module.py 4-7</a>" in written
    assert '"ADR-0023": "https://github.com/joecgo/crazyflie-behavior/blob/' in written
    assert render_page(written, fake_numbers()) == written


@pytest.mark.parametrize(
    "body",
    [
        '<span data-const="FAST">?</span>',
        '<span data-formula="doubled">?</span>',
        '<span data-formula="halved" data-form="s">?</span>',
        '<a data-const-link="FAST" href="">?</a>',
        '<a data-const-link="SPEED">?</a>',
    ],
    ids=["unknown constant", "unknown formula", "a formula with a form", "unknown link", "a link with no href"],
)
def test_a_page_naming_what_the_script_cant_write_raises(body: str) -> None:
    with pytest.raises(TourNumbersError):
        render_page(fake_page(body), fake_numbers())


def test_a_link_to_constants_in_two_files_raises() -> None:
    numbers = fake_numbers()
    other = read_constant("OTHER = 1\n", ConstantSpec("OTHER", "src/other.py", "s"))
    numbers = TourNumbers(numbers.commit, {**numbers.constants, "OTHER": other}, numbers.formulas, numbers.adr_files)

    with pytest.raises(TourNumbersError, match="two files"):
        render_page(fake_page('<a data-const-link="SPEED OTHER" href="">?</a>'), numbers)


def test_a_page_without_one_numbers_script_raises() -> None:
    with pytest.raises(TourNumbersError):
        render_page(f'<a href="{FAKE_PAGE_LINK}">x</a>', fake_numbers())


def test_the_pin_is_the_one_commit_the_page_links_to() -> None:
    assert pinned_commit(fake_page("")) == FAKE_COMMIT
    with pytest.raises(TourNumbersError, match="2 commits"):
        pinned_commit(fake_page(FAKE_PAGE_LINK.replace(FAKE_COMMIT, "1" * 40)))
