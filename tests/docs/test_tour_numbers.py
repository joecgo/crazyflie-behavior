"""The project tour shows the code's numbers, its modules' lengths and the glossary's definitions as they are at
the commit its links are pinned to.

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
    count_lines,
    load_numbers,
    pinned_commit,
    read_constant,
    read_glossary,
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
MODULE = "src/module.py"
OTHER_MODULE = "src/other.py"
GLOSSARY = """# Glossary

## Architecture

| Term | Definition | ADR |
|---|---|---|
| **Tick** | One iteration of the loop, at `TICK_RATE` ([ADR-0023](decisions/0023-tick-rate-20-hz.md)). | [0023](x.md) |
| **Emergency stop** (e-stop) | Cut **all** motors: *the drone falls*. | — |

## Space and motion

| Term | Definition |
|---|---|
| **Setpoint** | A target the controller tries to reach. |

## Deprecated terms

| Term | Replaced by | Why |
|---|---|---|
| **Planned landing** | Landing approach | Renamed. |
"""


def constant(name: str, unit: str) -> CodeConstant:
    return read_constant(SOURCE, ConstantSpec(name, "src/module.py", unit))


def fake_numbers() -> TourNumbers:
    constants = {c.name: c for c in (constant("SPEED", "m/s"), constant("PERIOD_MS", "ms"), constant("RANGE_MS", "ms"))}
    halved = work_out(FormulaSpec("halved", "SPEED / 2", "m/s", "Half the speed."), constants)
    return TourNumbers(
        FAKE_COMMIT,
        constants,
        {"halved": halved},
        {"0023": "0023-tick-rate-20-hz.md"},
        {MODULE: 1200, OTHER_MODULE: 300},
        read_glossary(GLOSSARY),
    )


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


def test_the_tour_shows_numbers_lengths_and_terms_from_the_pinned_commit() -> None:
    """Guards the page test: a page with nothing marked would match whatever the script reads."""
    page = (TOUR_ROOT / "adapter.html").read_text(encoding="utf-8")
    assert len(re.findall(r'\bdata-(?:const|formula)="', page)) >= 50
    assert len(re.findall(r'\bdata-const-link="', page)) >= 15
    assert len(re.findall(r'\bdata-module-lines="', page)) >= 18
    assert len(re.findall(r'\bdata-module-bar="', page)) >= 9
    assert len(set(re.findall(r'\bdata-term="([^"]*)"', page))) >= 50


def test_tour_js_keeps_no_copy_of_a_definition() -> None:
    """A copy would go stale when the glossary changes; the page's tour-numbers script holds them instead."""
    page = (TOUR_ROOT / "adapter.html").read_text(encoding="utf-8")
    script = (TOUR_ROOT / "tour.js").read_text(encoding="utf-8")
    terms = load_numbers(pinned_commit(page)).terms

    dotted = set(re.findall(r'\bdata-term="([^"]*)"', page))
    copied = [term for term in dotted if term in terms and terms[term] in script]

    assert copied == []


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


def test_a_formula_with_digits_shows_its_value_rounded_and_keeps_it_exact() -> None:
    constants = fake_numbers().constants
    thirds = work_out(FormulaSpec("thirds", "SPEED / 3", "m/s", "A third of the speed.", digits=2), constants)
    numbers = TourNumbers(FAKE_COMMIT, constants, {"thirds": thirds}, fake_numbers().adr_files, {}, {})

    written = render_page(fake_page('<span data-formula="thirds">?</span>'), numbers)

    assert '<span data-formula="thirds">0.13&nbsp;m/s</span>' in written
    assert thirds.value == pytest.approx(0.4 / 3)


def test_a_formula_with_a_constant_the_tour_doesnt_read_raises() -> None:
    with pytest.raises(TourNumbersError, match="OTHER"):
        work_out(FormulaSpec("x", "SPEED + OTHER", "m/s", ""), fake_numbers().constants)


@pytest.mark.parametrize(
    ("source", "lines"),
    [("", 0), ("one\n", 1), ("one\ntwo\n", 2), ("one\ntwo", 2), ("one\n\n", 2)],
    ids=["empty", "one line", "two lines", "no newline at the end", "a blank last line"],
)
def test_a_module_has_as_many_lines_as_github_numbers(source: str, lines: int) -> None:
    assert count_lines(source) == lines


def test_each_glossary_term_is_read_with_its_definition_as_plain_text() -> None:
    assert read_glossary(GLOSSARY) == {
        "Tick": "One iteration of the loop, at TICK_RATE (ADR-0023).",
        "Emergency stop": "Cut all motors: the drone falls.",
        "Setpoint": "A target the controller tries to reach.",
    }


def test_a_term_defined_twice_raises() -> None:
    with pytest.raises(TourNumbersError, match="Setpoint twice"):
        read_glossary(GLOSSARY + "\n## More\n\n| **Setpoint** | Again. |\n")


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


def test_the_page_gets_each_modules_length_and_a_bar_beside_the_longest() -> None:
    page = fake_page(
        f'<span class="lines" data-module-lines="{MODULE}">?</span><i data-module-bar="{MODULE}"></i>'
        f'<span data-module-lines="{OTHER_MODULE}">?</span><i data-module-bar="{OTHER_MODULE}" style="width:3%"></i>'
    )

    written = render_page(page, fake_numbers())

    assert f'<span class="lines" data-module-lines="{MODULE}">1,200</span>' in written
    assert f'<span data-module-lines="{OTHER_MODULE}">300</span>' in written
    assert f'<i data-module-bar="{MODULE}" style="width:100%"></i>' in written
    assert f'<i data-module-bar="{OTHER_MODULE}" style="width:25%"></i>' in written
    assert render_page(written, fake_numbers()) == written


def test_the_page_gets_the_definition_of_each_term_it_dots_and_no_other() -> None:
    page = fake_page('<span class="term" data-term="Tick">ticks</span> and <span data-term="Tick">a tick</span>')

    written = render_page(page, fake_numbers())

    assert '"terms": {\n  "Tick": "One iteration of the loop, at TICK_RATE (ADR-0023)."\n }' in written


@pytest.mark.parametrize("term", ["Planned landing", "Drift"], ids=["deprecated", "not in the glossary"])
def test_a_page_dotting_a_term_the_glossary_doesnt_define_raises(term: str) -> None:
    with pytest.raises(TourNumbersError, match=term):
        render_page(fake_page(f'<span class="term" data-term="{term}">x</span>'), fake_numbers())


@pytest.mark.parametrize(
    "body",
    [
        '<span data-const="FAST">?</span>',
        '<span data-formula="doubled">?</span>',
        '<span data-formula="halved" data-form="s">?</span>',
        '<a data-const-link="FAST" href="">?</a>',
        '<a data-const-link="SPEED">?</a>',
        '<span data-module-lines="src/uncounted.py">?</span>',
        '<i data-module-bar="src/uncounted.py"></i>',
    ],
    ids=[
        "unknown constant",
        "unknown formula",
        "a formula with a form",
        "unknown link",
        "a link with no href",
        "uncounted length",
        "uncounted bar",
    ],
)
def test_a_page_naming_what_the_script_cant_write_raises(body: str) -> None:
    with pytest.raises(TourNumbersError):
        render_page(fake_page(body), fake_numbers())


def test_a_link_to_constants_in_two_files_raises() -> None:
    numbers = fake_numbers()
    other = read_constant("OTHER = 1\n", ConstantSpec("OTHER", "src/other.py", "s"))
    numbers = TourNumbers(
        numbers.commit,
        {**numbers.constants, "OTHER": other},
        numbers.formulas,
        numbers.adr_files,
        numbers.module_lines,
        numbers.terms,
    )

    with pytest.raises(TourNumbersError, match="two files"):
        render_page(fake_page('<a data-const-link="SPEED OTHER" href="">?</a>'), numbers)


def test_a_page_without_one_numbers_script_raises() -> None:
    with pytest.raises(TourNumbersError):
        render_page(f'<a href="{FAKE_PAGE_LINK}">x</a>', fake_numbers())


def test_the_pin_is_the_one_commit_the_page_links_to() -> None:
    assert pinned_commit(fake_page("")) == FAKE_COMMIT
    with pytest.raises(TourNumbersError, match="2 commits"):
        pinned_commit(fake_page(FAKE_PAGE_LINK.replace(FAKE_COMMIT, "1" * 40)))
