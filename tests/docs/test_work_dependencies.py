"""Every work dependency names a backlog row that still exists (ADR-0091)."""

import ast
import io
import re
import tokenize
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKLOG = "docs/decision-backlog.md"
NEXT_UP = "docs/next-up.md"
ADR_INDEX = "docs/decisions/README.md"
WHOLE_DOCS = ("docs/glossary.md", "ARCHITECTURE.md")
CODE_FOLDERS = ("src", "tests", "tools")
SKIPPED_NEXT_UP_SECTION = "## Done last"
ROW_NUMBER = re.compile(r"(?<![\w/])#(?P<number>[0-9]+)\b")
PULL_REQUEST = re.compile(
    r"\[[^\]]*\]\(https://github\.com/[^)\s]*/pull/[^)]*\)|[Pp]ull\s+requests?\s+#[0-9]+"
)
"""A GitHub link to a pull request, or the words "pull request" before its number, even across two lines."""
CELL_BORDER = re.compile(r"(?<!\\)\|")
TODO_MARK = "TODO:"


@dataclass(frozen=True, slots=True)
class Text:
    """Part of a file, with the line it starts on."""

    source: str
    first_line: int
    text: str


@dataclass(frozen=True, slots=True)
class WorkDependency:
    source: str
    line: int
    row: int


def work_dependencies(texts: Sequence[Text]) -> list[WorkDependency]:
    found: list[WorkDependency] = []
    for part in texts:
        # A pull request keeps its line breaks, so the line numbers after it stay right.
        text = PULL_REQUEST.sub(lambda match: "\n" * match.group(0).count("\n"), part.text)
        for match in ROW_NUMBER.finditer(text):
            line = part.first_line + text.count("\n", 0, match.start())
            found.append(WorkDependency(part.source, line, int(match["number"])))
    return found


def table_cells(line: str) -> list[str]:
    return [cell.strip() for cell in CELL_BORDER.split(line)[1:-1]]


def column(source: str, markdown: str, heading: str) -> list[Text]:
    """The cells under `heading`, from every table that has that column."""
    cells: list[Text] = []
    position: int | None = None
    for number, line in enumerate(markdown.split("\n"), start=1):
        if not line.startswith("|"):
            position = None
        elif position is None:
            headings = table_cells(line)
            position = headings.index(heading) if heading in headings else None
        else:
            cells.append(Text(source, number, table_cells(line)[position]))
    assert cells, f"{source}: no table with a {heading!r} column"
    return cells


def backlog_rows(markdown: str) -> set[int]:
    return {int(cell.text) for cell in column(BACKLOG, markdown, "#") if cell.text.isdigit()}


def without_section(source: str, markdown: str, heading: str) -> list[Text]:
    """The text before and after one `##` section."""
    lines = markdown.split("\n")
    assert heading in lines, f"{source}: no {heading!r} section"
    start = lines.index(heading)
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return [Text(source, 1, "\n".join(lines[:start])), Text(source, end + 1, "\n".join(lines[end:]))]


def comment_blocks(code: str) -> list[tuple[int, list[str]]]:
    """Each run of comments on consecutive lines, as its first line number and its lines."""
    blocks: list[tuple[int, list[str]]] = []
    for token in tokenize.generate_tokens(io.StringIO(code).readline):
        if token.type != tokenize.COMMENT:
            continue
        line = token.start[0]
        if not blocks or blocks[-1][0] + len(blocks[-1][1]) != line:
            blocks.append((line, []))
        blocks[-1][1].append(token.string.removeprefix("#"))
    return blocks


def docstring_paragraphs(code: str) -> list[tuple[int, list[str]]]:
    """Each paragraph of each docstring, an attribute's included."""
    paragraphs: list[tuple[int, list[str]]] = []
    for node in ast.walk(ast.parse(code)):
        if not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)):
            continue
        if not isinstance(node.value.value, str):
            continue
        in_paragraph = False
        for number, line in enumerate(node.value.value.split("\n"), start=node.lineno):
            if line.strip():
                if not in_paragraph:
                    paragraphs.append((number, []))
                paragraphs[-1][1].append(line)
            in_paragraph = bool(line.strip())
    return paragraphs


def todo_texts(source: str, code: str) -> list[Text]:
    """From each `TODO:` to the end of its comment block or docstring paragraph."""
    texts: list[Text] = []
    for first_line, lines in comment_blocks(code) + docstring_paragraphs(code):
        for index, line in enumerate(lines):
            if TODO_MARK in line:
                rest = [line[line.index(TODO_MARK) :], *lines[index + 1 :]]
                texts.append(Text(source, first_line + index, "\n".join(rest)))
                break
    return texts


def stale_dependencies(texts: Sequence[Text], rows: set[int]) -> list[WorkDependency]:
    return [found for found in work_dependencies(texts) if found.row not in rows]


def code_files() -> list[Path]:
    return [path for folder in CODE_FOLDERS for path in sorted((REPO_ROOT / folder).rglob("*.py"))]


def read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def forward_looking_texts() -> list[Text]:
    """Everything in the repository that can hold a work dependency."""
    texts = column(BACKLOG, read(BACKLOG), "Needed by")
    texts += column(ADR_INDEX, read(ADR_INDEX), "Built")
    texts += without_section(NEXT_UP, read(NEXT_UP), SKIPPED_NEXT_UP_SECTION)
    texts += [Text(path, 1, read(path)) for path in WHOLE_DOCS]
    for path in code_files():
        source = path.relative_to(REPO_ROOT).as_posix()
        texts += todo_texts(source, path.read_text(encoding="utf-8"))
    return texts


def test_every_work_dependency_names_a_backlog_row() -> None:
    rows = backlog_rows(read(BACKLOG))
    stale = stale_dependencies(forward_looking_texts(), rows)
    assert not stale, "\n".join(
        f"{found.source}:{found.line}: #{found.row} isn't a backlog row. "
        f'Update this place, or write "pull request #{found.row}" if that\'s what it is.'
        for found in stale
    )


@pytest.mark.parametrize(
    "source",
    [BACKLOG, ADR_INDEX, NEXT_UP, "docs/glossary.md", "ARCHITECTURE.md", "src/", "tools/"],
)
def test_the_scan_reads_each_place(source: str) -> None:
    assert any(text.source.startswith(source) and text.text for text in forward_looking_texts())


def test_the_scan_reads_every_code_folder() -> None:
    assert {path.relative_to(REPO_ROOT).parts[0] for path in code_files()} == {"src", "tests", "tools"}


def test_only_a_missing_row_is_stale() -> None:
    texts = [Text("a.md", 1, "#7 and #8")]
    assert stale_dependencies(texts, {7}) == [WorkDependency("a.md", 1, 8)]


@pytest.mark.parametrize(
    ("text", "rows"),
    [
        ("After #7.", [7]),
        ("(#7, #8)", [7, 8]),
        ("#7 to #9", [7, 9]),
        ("pull request #7", []),
        ("Pull requests #7", []),
        ("pull\nrequest\n#7", []),
        ("[#7](https://github.com/owner/name/pull/7)", []),
        ("[#7](https://github.com/owner/name/issues/7)", [7]),
        ("pull request #7, then #8", [8]),
        ("[the notes](notes.md#7)", []),
        ("M-007 and ADR-0007", []),
    ],
)
def test_a_row_number_is_a_work_dependency_unless_it_is_a_pull_request(text: str, rows: list[int]) -> None:
    assert [found.row for found in work_dependencies([Text("a.md", 1, text)])] == rows


def test_a_dependency_after_a_wrapped_pull_request_keeps_its_line() -> None:
    found = work_dependencies([Text("a.md", 10, "pull request\n#7\nthen #8")])
    assert found == [WorkDependency("a.md", 12, 8)]


def test_only_the_named_column_is_read() -> None:
    markdown = "| # | Question | Needed by |\n|---|---|---|\n| 1 | a \\| #2 | After #3 |\n\ntext #4"
    assert work_dependencies(column("a.md", markdown, "Needed by")) == [WorkDependency("a.md", 3, 3)]
    assert backlog_rows(markdown) == {1}


def test_a_table_without_the_column_is_not_read() -> None:
    markdown = "| Needed by |\n|---|\n| #1 |\n\n| Other |\n|---|\n| #2 |"
    assert work_dependencies(column("a.md", markdown, "Needed by")) == [WorkDependency("a.md", 3, 1)]


def test_a_missing_column_fails() -> None:
    with pytest.raises(AssertionError, match="no table"):
        column("a.md", "| # |\n|---|\n| 1 |", "Needed by")


def test_only_the_skipped_section_is_left_out() -> None:
    markdown = "#1\n## Done last\n#2\n### Detail\n#3\n## Next\n#4"
    assert work_dependencies(without_section("a.md", markdown, "## Done last")) == [
        WorkDependency("a.md", 1, 1),
        WorkDependency("a.md", 7, 4),
    ]


def test_a_missing_section_fails() -> None:
    with pytest.raises(AssertionError, match="section"):
        without_section("a.md", "## Next", "## Done last")


@pytest.mark.parametrize(
    ("code", "found"),
    [
        ("x = 1  # TODO: see #7", [(1, 7)]),
        ("# TODO: later\n# see #7", [(2, 7)]),
        ("# see #7\n# TODO: later", []),
        ("# TODO: later\n\n# see #7", []),
        ("# see #7", []),
        ('"""Title.\n\nTODO: later,\nsee #7.\n"""', [(4, 7)]),
        ('"""TODO: later.\n\nSee #7."""', []),
        ('x = 1\n"""TODO: see #7."""', [(2, 7)]),
        ('x = "TODO: see #7"', []),
    ],
)
def test_a_todo_runs_to_the_end_of_its_comment_or_paragraph(code: str, found: list[tuple[int, int]]) -> None:
    dependencies = work_dependencies(todo_texts("a.py", code))
    assert [(each.line, each.row) for each in dependencies] == found
