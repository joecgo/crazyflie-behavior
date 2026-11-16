"""Keep the mistakes log's IDs, counts and index in step with its entries.

Usage:
    python tools/mistakes_log.py check      # exit 1 if the tables are out of date
    python tools/mistakes_log.py write      # assign new IDs, rewrite the tables
    python tools/mistakes_log.py archive 2026-11   # move a month to its own file
"""

import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "docs" / "claude-mistakes.md"
ARCHIVE_DIR = ROOT / "docs" / "claude-mistakes"

POINTED_OUT = "## Mistakes I had to point out"
CAUGHT_LATER = "## Mistakes Claude caught itself"
SECTIONS = (POINTED_OUT, CAUGHT_LATER)

KINDS = (
    "design",
    "safety design",
    "recommendation",
    "environment",
    "communication",
    "testing",
    "process",
)

HEADING = re.compile(r"^### (?:(M-\d{3}), )?(\d{4}-\d{2}-\d{2}): (.*)$")
FIELD = re.compile(r"^- \*\*(Kind|Pattern|Guard):\*\* *(.*?)(?:\.\s.*)?\.?\s*$")


@dataclass
class Entry:
    path: Path
    section: str
    position: int
    mistake_id: str | None
    date: str
    title: str
    kind: str
    pattern: str
    guard: str


def log_files() -> list[Path]:
    return [MAIN, *sorted(ARCHIVE_DIR.glob("*.md"))]


def parse(path: Path) -> list[Entry]:
    entries: list[Entry] = []
    section = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line in SECTIONS:
            section = line
            continue
        heading = HEADING.match(line)
        if heading:
            entries.append(Entry(path, section, len(entries), heading[1], heading[2], heading[3], "", "", ""))
            continue
        field = FIELD.match(line)
        if field and entries:
            setattr(entries[-1], field[1].lower(), field[2])
    return entries


def all_entries() -> list[Entry]:
    return [entry for path in log_files() for entry in parse(path)]


def assign_ids(entries: list[Entry]) -> dict[tuple[Path, int], str]:
    """New IDs for entries without one: oldest first; in a day, the lower in its file first."""
    used = [int(e.mistake_id[2:]) for e in entries if e.mistake_id]
    next_number = max(used, default=0) + 1
    new = sorted(
        (e for e in entries if e.mistake_id is None),
        key=lambda e: (e.date, SECTIONS.index(e.section), -e.position),
    )
    assigned: dict[tuple[Path, int], str] = {}
    for entry in new:
        entry.mistake_id = f"M-{next_number:03d}"
        assigned[(entry.path, entry.position)] = entry.mistake_id
        next_number += 1
    return assigned


def write_ids(assigned: dict[tuple[Path, int], str]) -> None:
    for path in {p for p, _ in assigned}:
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        position = -1
        for index, line in enumerate(lines):
            if HEADING.match(line.rstrip("\n")):
                position += 1
                mistake_id = assigned.get((path, position))
                if mistake_id:
                    lines[index] = line.replace("### ", f"### {mistake_id}, ", 1)
        path.write_text("".join(lines), encoding="utf-8")


def kind_table(entries: list[Entry]) -> str:
    counts = Counter((e.kind, e.section) for e in entries)
    rows = ["| Kind | I pointed it out | Claude caught it later |", "|---|---|---|"]
    for kind in KINDS:
        rows.append(f"| {kind} | {counts[kind, POINTED_OUT]} | {counts[kind, CAUGHT_LATER]} |")
    pointed = sum(1 for e in entries if e.section == POINTED_OUT)
    rows.append(f"| **Total** | **{pointed}** | **{len(entries) - pointed}** |")
    return "\n".join(rows)


def pattern_table(entries: list[Entry]) -> str:
    counts = Counter(e.pattern for e in entries)
    rows = ["| Pattern | Entries |", "|---|---|"]
    rows += [f"| {pattern} | {count} |" for pattern, count in counts.most_common()]
    return "\n".join(rows)


def index_table(entries: list[Entry]) -> str:
    rows = ["| ID | Date | Title | Kind | Pattern | Guard |", "|---|---|---|---|---|---|"]
    for e in sorted(entries, key=lambda e: e.mistake_id or "", reverse=True):
        where = e.mistake_id if e.path == MAIN else (f"[{e.mistake_id}](claude-mistakes/{e.path.name})")
        title = e.title.replace("|", "\\|")
        rows.append(f"| {where} | {e.date} | {title} | {e.kind} | {e.pattern} | {e.guard} |")
    return "\n".join(rows)


def generated(text: str) -> dict[str, str]:
    pairs: list[tuple[str, str]] = re.findall(r"<!-- generated: (\S+) -->\n(.*?)\n<!-- end generated -->", text, re.S)
    return dict(pairs)


def expected_tables(entries: list[Entry]) -> dict[str, str]:
    return {
        "kinds": kind_table(entries),
        "patterns": pattern_table(entries),
        "index": index_table(entries),
    }


def problems(entries: list[Entry]) -> list[str]:
    found: list[str] = []
    for e in entries:
        label = e.mistake_id or f"{e.date}: {e.title}"
        if e.kind not in KINDS:
            found.append(f"{label}: unknown kind {e.kind!r}")
        if not e.pattern:
            found.append(f"{label}: no Pattern line")
        if not e.guard:
            found.append(f"{label}: no Guard line")
        if e.mistake_id is None:
            found.append(f"{label}: no ID; run `write`")
    actual = generated(MAIN.read_text(encoding="utf-8"))
    for name, table in expected_tables(entries).items():
        if actual.get(name) != table:
            found.append(f"the {name} table is out of date; run `write`")
    return found


def write_tables(entries: list[Entry]) -> None:
    text = MAIN.read_text(encoding="utf-8")
    for name, table in expected_tables(entries).items():
        text = re.sub(
            rf"(<!-- generated: {name} -->\n)(?:.*?\n)??(<!-- end generated -->)",
            lambda m, t=table: m[1] + t + "\n" + m[2],
            text,
            flags=re.S,
        )
    MAIN.write_text(text, encoding="utf-8")


def archive(month: str) -> None:
    """Move a month's entries from the main file to docs/claude-mistakes/<month>.md."""
    lines = MAIN.read_text(encoding="utf-8").splitlines(keepends=True)
    kept: list[str] = []
    moved: dict[str, list[str]] = {section: [] for section in SECTIONS}
    section = ""
    moving = False
    for line in lines:
        bare = line.rstrip("\n")
        if bare in SECTIONS:
            section = bare
        heading = HEADING.match(bare)
        if heading:
            moving = heading[2].startswith(month)
        elif bare.startswith("## ") or bare == "---":
            moving = False
        (moved[section] if moving else kept).append(line)
    target = ARCHIVE_DIR / f"{month}.md"
    if target.exists():
        sys.exit(f"{target} already exists; merge by hand")
    ARCHIVE_DIR.mkdir(exist_ok=True)
    note = "Moved from the [mistakes log](../claude-mistakes.md), which keeps the index."
    parts = [f"# Claude's mistakes, {month}\n\n{note}\n\n"]
    for heading_line in SECTIONS:
        parts.append(heading_line + "\n\n" + "".join(moved[heading_line]).rstrip("\n") + "\n\n")
    target.write_text("".join(parts).rstrip("\n") + "\n", encoding="utf-8")
    MAIN.write_text("".join(kept), encoding="utf-8")


def main(arguments: list[str]) -> int:
    command = arguments[0] if arguments else "check"
    if command == "archive":
        archive(arguments[1])
        command = "write"
    entries = all_entries()
    if command == "write":
        assigned = assign_ids(entries)
        write_ids(assigned)
        write_tables(all_entries())
        return 0
    found = problems(entries)
    for problem in found:
        print(problem)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
