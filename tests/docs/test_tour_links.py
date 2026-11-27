"""The project tour's links into this repository open what they name.

Each link is pinned to one commit, and git reads that commit, so continuous integration checks out the full
history. Decided 2026-11-26 with the tour's first chapter; its ADR follows pass one.
"""

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TOUR_ROOT = REPO_ROOT / "docs" / "tour"
TOUR_SUFFIXES = {".html", ".css", ".js"}
REPOSITORY_LINK = re.compile(r"https://github\.com/joecgo/crazyflie-behavior/[^\s\"'<>)]*")
"""Any link into this repository on GitHub."""
PINNED_LINK = re.compile(
    r"https://github\.com/joecgo/crazyflie-behavior/(?P<kind>blob|tree)/(?P<commit>[0-9a-f]{40})/"
    r"(?P<path>[^?#\s\"'<>]+)(?P<plain>\?plain=1)?"
    r"(?:#L(?P<first>[0-9]+)(?:-L(?P<last>[0-9]+))?|#(?P<heading>[a-z0-9_-]+))?"
)
"""A link pinned to a full commit hash: a file (`blob`, with an optional line range or heading) or a folder
(`tree`)."""
GIT_OBJECT_KIND = {"blob": "blob", "tree": "tree"}
MARKDOWN_HEADING = re.compile(r"^#{1,6} +(?P<text>.+?) *#* *$", re.MULTILINE)


@dataclass(frozen=True, slots=True)
class TourLink:
    source: str
    """The tour file the link is in, relative to the repository."""
    url: str


@dataclass(frozen=True, slots=True)
class GitObject:
    kind: str
    contents: bytes


def tour_links() -> list[TourLink]:
    files = sorted(path for path in TOUR_ROOT.rglob("*") if path.suffix in TOUR_SUFFIXES)
    return [
        TourLink(path.relative_to(REPO_ROOT).as_posix(), match.group(0))
        for path in files
        for match in REPOSITORY_LINK.finditer(path.read_text(encoding="utf-8"))
    ]


def pinned(link: TourLink) -> re.Match[str]:
    match = PINNED_LINK.fullmatch(link.url)
    assert match is not None, f"{link.source}: not pinned to a commit: {link.url}"
    return match


def read_git_objects(names: list[str]) -> dict[str, GitObject | None]:
    """Each `<commit>:<path>` from git, or None when that commit has no such path."""
    result = subprocess.run(
        ["git", "cat-file", "--batch"],
        input="".join(f"{name}\n" for name in names).encode("utf-8"),
        cwd=REPO_ROOT,
        capture_output=True,
        check=True,
        timeout=60,
    )
    output = result.stdout
    objects: dict[str, GitObject | None] = {}
    position = 0
    for name in names:
        header_end = output.index(b"\n", position)
        header = output[position:header_end].decode("utf-8")
        position = header_end + 1
        if header.endswith((" missing", " ambiguous")):
            objects[name] = None
            continue
        _, kind, size = header.rsplit(" ", 2)
        objects[name] = GitObject(kind, output[position : position + int(size)])
        position += int(size) + 1  # git ends each object's contents with a newline
    return objects


def git_has_commit(commit: str) -> bool:
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{commit}^{{commit}}"], cwd=REPO_ROOT, capture_output=True, timeout=60
    )
    return result.returncode == 0


def line_count(contents: bytes) -> int:
    return contents.count(b"\n") + (0 if contents.endswith(b"\n") or not contents else 1)


def linked_objects() -> list[tuple[TourLink, re.Match[str], GitObject | None]]:
    links = [(link, pinned(link)) for link in tour_links()]
    for commit in sorted({match.group("commit") for _, match in links}):
        assert git_has_commit(commit), (
            f"commit {commit} isn't in this clone: continuous integration must check out the full history"
        )
    objects = read_git_objects(sorted({f"{match.group('commit')}:{match.group('path')}" for _, match in links}))
    return [(link, match, objects[f"{match.group('commit')}:{match.group('path')}"]) for link, match in links]


def heading_anchor(text: str) -> str:
    """GitHub's anchor for a heading: lower case, punctuation dropped, spaces to hyphens."""
    return re.sub(r"[^\w\- ]", "", text.lower()).replace(" ", "-")


def test_the_tour_has_repository_links_to_check() -> None:
    """Guards the scanner: a pattern that matched nothing would pass every other test."""
    assert len(tour_links()) >= 50


def test_every_repository_link_in_the_tour_is_pinned_to_a_commit() -> None:
    for link in tour_links():
        pinned(link)


def test_every_repository_link_in_the_tour_names_a_file_or_folder_at_its_commit() -> None:
    broken = [
        f"{link.source}: {link.url}"
        for link, match, found in linked_objects()
        if found is None or found.kind != GIT_OBJECT_KIND[match.group("kind")]
    ]

    assert broken == []


def test_every_line_range_in_the_tour_is_inside_its_file() -> None:
    broken: list[str] = []
    for link, match, found in linked_objects():
        if match.group("first") is None or found is None:
            continue
        first = int(match.group("first"))
        last = int(match.group("last") or first)
        lines = line_count(found.contents) if found.kind == "blob" else 0
        if not 1 <= first <= last <= lines:
            broken.append(f"{link.source}: lines {first}-{last} of {lines}: {link.url}")

    assert broken == []


def test_every_markdown_link_in_the_tour_opens_the_rendered_page() -> None:
    """Markdown read as code is hard to read, so a link to a heading replaces a line range."""
    as_code = [
        f"{link.source}: {link.url}"
        for link in tour_links()
        if (match := pinned(link)).group("path").endswith(".md")
        and (match.group("plain") is not None or match.group("first") is not None)
    ]

    assert as_code == []


def test_every_heading_link_in_the_tour_names_a_heading_in_its_file() -> None:
    broken: list[str] = []
    for link, match, found in linked_objects():
        if match.group("heading") is None or found is None:
            continue
        text = found.contents.decode("utf-8")
        anchors = {heading_anchor(heading.group("text")) for heading in MARKDOWN_HEADING.finditer(text)}
        if match.group("heading") not in anchors:
            broken.append(f"{link.source}: no heading #{match.group('heading')}: {link.url}")

    assert broken == []
