"""The project tour dots a glossary term at its first use in every lede, card and drop-down, as each is read on
its own.

Text in a link, a button, a heading, a drop-down's title, code or a diagram doesn't count: a pop-up can't sit
there. A glossary word in its everyday sense, such as "the PC's clock", is marked `<span class="plain">`. Only
the terms a page dots somewhere are checked, against the glossary at the pinned commit. Joe's choices,
2026-11-27 (backlog #167); its ADR follows with the tour's.
"""

import bisect
import html
import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from html.parser import HTMLParser

import pytest
from tools.tour_numbers import TOUR_ROOT, load_numbers, pinned_commit, tour_pages

SKIPPED_TAGS = frozenset(
    {"a", "button", "summary", "h1", "h2", "h3", "h4", "h5", "h6", "th", "code", "pre", "script", "style", "svg"}
)
"""Where a pop-up can't sit (a link, a button, a drop-down's title, a diagram), headings, and code."""
SKIPPED_CLASS = "label"
"""A card's small heading, such as "Layer"."""
TERM_CLASS = "term"
PLAIN_CLASS = "plain"
"""A glossary word in its everyday sense, which the check skips."""
PART_NAME = re.compile(
    r"(?<![\w-])(?:take-off\s+and\s+landing|log\s+blocks|commands|link)\s+(?=parts?(?![\w-]))", re.IGNORECASE
)
"""A part's name before "part", as in "the link part": a use of Part, not of Link or Command. The glossary's
Part names the four."""
INLINE_TAGS = frozenset(
    {"abbr", "b", "cite", "data", "dfn", "em", "i", "kbd", "mark", "q", "s", "small", "span", "strong", "sub", "sup"}
    | {"time", "tspan", "u", "var"}
)
"""Elements inside a line of text. Any other element's text is read apart from the text around it."""
VOID_TAGS = frozenset({"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "wbr"})
DOTTED_TERM = re.compile(r'\bdata-term="([^"]*)"')
MASK = "\x00"
"""Stands in for text no term is matched in: a dotted term, a plain use, a part's name."""


@dataclass(frozen=True, slots=True)
class _Text:
    text: str
    offset: int
    """Where it starts in the page's source."""


def _no_children() -> "list[_Element | _Text]":
    return []


@dataclass(eq=False, slots=True)
class _Element:
    tag: str
    classes: frozenset[str]
    term: str | None
    """The glossary term a dot names (`data-term`)."""
    parent: "_Element | None"
    children: "list[_Element | _Text]" = field(default_factory=_no_children)


class _PageParser(HTMLParser):
    """The page as a tree of elements and text, each text with its place in the source."""

    def __init__(self, page: str) -> None:
        super().__init__(convert_charrefs=False)
        self.root = _Element("root", frozenset(), None, None)
        self._current = self.root
        self._line_starts = [0, *(match.end() for match in re.finditer("\n", page))]
        self.feed(page)
        self.close()

    def _offset(self) -> int:
        line, column = self.getpos()
        return self._line_starts[line - 1] + column

    def _element(self, tag: str, attrs: list[tuple[str, str | None]]) -> _Element:
        values = dict(attrs)
        element = _Element(tag, frozenset((values.get("class") or "").split()), values.get("data-term"), self._current)
        self._current.children.append(element)
        return element

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        element = self._element(tag, attrs)
        if tag not in VOID_TAGS:
            self._current = element

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._element(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        # An end tag closes any element left open inside it, such as an SVG shape without its own end tag.
        element = self._current
        while element.parent is not None and element.tag != tag:
            element = element.parent
        if element.parent is not None:
            self._current = element.parent

    def handle_data(self, data: str) -> None:
        self._current.children.append(_Text(data, self._offset()))

    def handle_entityref(self, name: str) -> None:
        self._current.children.append(_Text(html.unescape(f"&{name};"), self._offset()))

    def handle_charref(self, name: str) -> None:
        self._current.children.append(_Text(html.unescape(f"&#{name};"), self._offset()))


def _is_unit(element: _Element) -> bool:
    """A lede, a card or a drop-down."""
    return (
        element.tag == "details"
        or (element.tag == "p" and "lede" in element.classes)
        or any(name.endswith("-card") for name in element.classes)
    )


def _units(element: _Element) -> Iterator[_Element]:
    for child in element.children:
        if isinstance(child, _Element):
            if _is_unit(child):
                yield child
            yield from _units(child)


@dataclass(frozen=True, slots=True)
class _Piece:
    text: str
    offset: int
    masked: bool
    """A dot, a plain use or a break: no term is matched inside it."""
    dotted: str | None = None


_BREAK = _Piece("\n", -1, masked=True)
"""Where text stops running on, such as between two table cells: "height" then "0.15" isn't "height0.15"."""


def _pieces(element: _Element) -> list[_Piece]:
    """The unit's text in order, leaving out the skipped places and the units inside it."""
    pieces: list[_Piece] = []
    for child in element.children:
        if isinstance(child, _Text):
            pieces.append(_Piece(child.text, child.offset, masked=False))
        elif child.tag in SKIPPED_TAGS or SKIPPED_CLASS in child.classes or _is_unit(child):
            pieces.append(_BREAK)
        elif TERM_CLASS in child.classes or PLAIN_CLASS in child.classes:
            inner = _pieces(child)
            text = "".join(piece.text for piece in inner)
            dotted = child.term if TERM_CLASS in child.classes else None
            pieces.append(_Piece(text, inner[0].offset if inner else -1, masked=True, dotted=dotted))
        elif child.tag in INLINE_TAGS:
            pieces.extend(_pieces(child))
        else:
            pieces.extend((_BREAK, *_pieces(child), _BREAK))
    return pieces


def _words(term: str) -> str:
    """How the page writes a term: without a qualifier such as "(a flight)", and in lower case."""
    return " ".join(re.sub(r"\s*\([^)]*\)$", "", term).split()).lower()


def _term_pattern(terms: Iterable[str]) -> re.Pattern[str]:
    """Any of `terms` as a whole word, in any case, with a plural ending. The longest is tried first, so "final
    descent height" isn't read as "final descent"."""
    words = sorted({_words(term) for term in terms}, key=len, reverse=True)
    alternatives = "|".join(re.escape(word).replace(r"\ ", r"\s+") for word in words)
    return re.compile(rf"(?<![\w-])(?P<words>{alternatives})(?:s|es)?(?![\w-])", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class UndottedUse:
    """A term's first use in a lede, card or drop-down, with no dot."""

    term: str
    words: str
    """As the page writes them, such as "Setpoints"."""
    offset: int
    """Where they start in the page's source."""
    line: int
    context: str


def page_units(page: str) -> int:
    return sum(1 for _ in _units(_PageParser(page).root))


def undotted_first_uses(page: str, terms: Iterable[str]) -> list[UndottedUse]:
    """Each lede's, card's and drop-down's first use of a term the page dots somewhere, where it has no dot.
    `terms` are the glossary's."""
    known = set(terms)
    checked = set(DOTTED_TERM.findall(page)) & known
    by_words = {_words(term): term for term in known}
    pattern = _term_pattern(known)
    found: list[UndottedUse] = []
    for unit in _units(_PageParser(page).root):
        pieces = _pieces(unit)
        starts: list[int] = []
        position = 0
        for piece in pieces:
            starts.append(position)
            position += len(piece.text)
        text = "".join(piece.text for piece in pieces)
        masked = list("".join(MASK * len(piece.text) if piece.masked else piece.text for piece in pieces))
        for name in PART_NAME.finditer(text):
            masked[name.start() : name.end()] = MASK * len(name.group(0))

        uses: list[tuple[int, int, str, bool]] = [
            (start, start, piece.dotted, True)
            for start, piece in zip(starts, pieces, strict=True)
            if piece.dotted is not None
        ]
        uses += [
            (match.start(), match.end(), by_words[" ".join(match.group("words").split()).lower()], False)
            for match in pattern.finditer("".join(masked))
        ]
        seen: set[str] = set()
        for start, end, term, dotted in sorted(uses):
            if term in seen or term not in checked:
                continue
            seen.add(term)
            if dotted:
                continue
            index = bisect.bisect_right(starts, start) - 1
            offset = pieces[index].offset + start - starts[index]
            context = " ".join(text[max(0, start - 40) : end + 40].split())
            found.append(UndottedUse(term, text[start:end], offset, page.count("\n", 0, offset) + 1, context))
    return sorted(found, key=lambda use: use.offset)


# --- The committed pages ---------------------------------------------------------------------------------------


def test_every_term_a_tour_page_dots_is_dotted_at_its_first_use_in_each_lede_card_and_drop_down() -> None:
    pages = tour_pages()
    assert pages, f"no pages in {TOUR_ROOT}"
    for path in pages:
        page = path.read_text(encoding="utf-8")
        found = undotted_first_uses(page, load_numbers(pinned_commit(page)).terms)
        listed = "\n".join(f"  line {use.line}: {use.term}: ...{use.context}..." for use in found)
        assert found == [], (
            f"{path.name}: {len(found)} first uses without a dot. Dot each, or mark an everyday use "
            f'<span class="plain">:\n{listed}'
        )


def test_the_dot_check_reads_the_pages_ledes_cards_and_drop_downs() -> None:
    """Guards the page test: a page whose units it can't find, or with no dotted terms, would pass."""
    page = (TOUR_ROOT / "adapter.html").read_text(encoding="utf-8")
    terms = load_numbers(pinned_commit(page)).terms

    assert page_units(page) >= 90
    assert len(set(DOTTED_TERM.findall(page)) & set(terms)) >= 50


# --- The check -------------------------------------------------------------------------------------------------

TERMS = (
    "Tick",
    "Setpoint",
    "Part",
    "Link",
    "Command",
    "Clock",
    "Final descent",
    "Final descent height",
    "Take over (a flight)",
)


def dot(term: str, words: str | None = None) -> str:
    return f'<span class="term" tabindex="0" data-term="{term}">{words or _words(term)}</span>'


def found_in(body: str) -> list[tuple[str, str]]:
    """The undotted first uses in `body`, with every term but Clock dotted in a lede first."""
    dotted = "".join(dot(term) for term in TERMS if term != "Clock")
    return [(use.term, use.words) for use in undotted_first_uses(f'<p class="lede">{dotted}</p>{body}', TERMS)]


def test_an_undotted_first_use_in_a_card_is_found() -> None:
    assert found_in('<div class="mod-card"><p>Each tick sends.</p></div>') == [("Tick", "tick")]


def test_a_dotted_first_use_covers_the_rest_of_its_unit() -> None:
    assert found_in(f'<div class="mod-card"><p>Each {dot("Tick")} sends.</p><p>The next tick too.</p></div>') == []


def test_a_use_before_the_dot_is_found() -> None:
    assert found_in(f'<div class="step-card">A tick, then {dot("Tick")}.</div>') == [("Tick", "tick")]


@pytest.mark.parametrize(
    "body",
    [
        "<details><summary>More</summary><p>A tick.</p></details>",
        f'<div class="wi-card">{dot("Tick")}<details><summary>More</summary>A tick.</details></div>',
        f'<div class="wi-card"><details><summary>More</summary>{dot("Tick")}</details>A tick.</div>',
    ],
    ids=["a drop-down", "a drop-down in a dotted card", "a card around a dotted drop-down"],
)
def test_each_lede_card_and_drop_down_is_read_on_its_own(body: str) -> None:
    assert found_in(body) == [("Tick", "tick")]


def test_text_outside_a_lede_card_or_drop_down_isnt_checked() -> None:
    assert found_in("<p>A tick.</p>") == []


@pytest.mark.parametrize(
    "skipped",
    [
        '<a href="x">tick</a>',
        "<button>tick</button>",
        "<h3>tick</h3>",
        "<details><summary>tick</summary></details>",
        "<code>tick</code>",
        "<th>tick</th>",
        "<svg><text>tick</text><circle r='1'></svg>",
        '<span class="label">tick</span>',
        '<span class="plain">tick</span>',
    ],
    ids=["link", "button", "heading", "a drop-down's title", "code", "table heading", "diagram", "label", "plain"],
)
def test_a_use_where_a_pop_up_cant_sit_or_marked_plain_isnt_the_first(skipped: str) -> None:
    assert found_in(f'<div class="layer-card">{skipped} then {dot("Tick")}</div>') == []


def test_a_plain_use_doesnt_stand_for_the_terms_first_use() -> None:
    assert found_in('<div class="layer-card"><span class="plain">a clock</span> and a tick</div>') == [("Tick", "tick")]


def test_a_parts_name_is_a_use_of_part_not_of_link_or_command() -> None:
    assert found_in(f'<div class="mod-card">The commands {dot("Part", "part")} and the link part.</div>') == []
    assert found_in('<div class="mod-card">The link part closes.</div>') == [("Part", "part")]


def test_a_term_is_found_in_plural_and_in_any_case() -> None:
    assert found_in('<div class="mod-card">Setpoints and Ticks.</div>') == [
        ("Setpoint", "Setpoints"),
        ("Tick", "Ticks"),
    ]


def test_the_longest_term_is_found() -> None:
    assert found_in('<div class="mod-card">At the final descent height.</div>') == [
        ("Final descent height", "final descent height")
    ]


def test_a_term_split_by_inline_tags_is_found() -> None:
    assert found_in('<div class="mod-card">The final <em>descent</em>.</div>') == [("Final descent", "final descent")]


def test_text_in_two_table_cells_is_read_apart() -> None:
    table = "<table><tr><td>Final descent height</td><td>0.15 m</td></tr></table>"

    assert found_in(f'<div class="mod-card">{table}</div>') == [("Final descent height", "Final descent height")]


def test_a_qualifier_in_a_terms_name_is_left_out() -> None:
    assert found_in('<div class="mod-card">The operator can take over.</div>') == [
        ("Take over (a flight)", "take over")
    ]


def test_a_word_inside_another_word_isnt_a_use() -> None:
    assert found_in('<div class="mod-card">A ticket, a link-loss and a clocked part-time job.</div>') == []


def test_only_terms_the_page_dots_somewhere_are_checked() -> None:
    assert found_in('<div class="mod-card">The clock.</div>') == []


def test_a_use_is_found_at_its_line_in_the_source() -> None:
    page = f'<p class="lede">{dot("Tick")}</p>\n<div class="mod-card">\n  <p>Each&nbsp;<em>new</em> tick.</p>\n</div>'

    [use] = undotted_first_uses(page, TERMS)

    assert (use.line, page[use.offset : use.offset + len(use.words)]) == (3, "tick")
