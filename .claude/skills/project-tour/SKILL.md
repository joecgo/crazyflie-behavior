---
name: project-tour
description: "Builds or revises the project tour in docs/tour/ (the interactive pages that walk a reader through the project): the user's rules for its reader, style, headings and interactive parts, the evidence each claim needs, the checks, and how the private preview is republished. Use it for any new chapter or section, any edit to a tour page, and the user's feedback on the tour. Argument: the chapter or the feedback."
---

# Project tour

Joe judges the tour by reading it. These are Joe's rules from building and
reviewing chapter 1. When Joe gives feedback that would apply to another page
or chapter too, apply it and add it here in the same task.

## Reader and style

- The reader, in Joe's words: "a curious reader who might skim for 5 minutes,
  or could be drawn in for [a] deep [dive] for their own personal project. Or,
  it could be me, trying to review how things work in a low stress way." Assume
  an engineer's coding skill, not Python or the libraries.
- "It shouldn't read like a review packet." It's a comprehensive tour: lots of
  visuals, diagrams, links and drop-downs, simple at first, deeper by clicking.
- Use the glossary's terms exactly.

## Write for the reader

From Joe's feedback on chapter 1 (2026-11-27).

- A "why" gives the reason, with a case of what goes wrong without it.
  Saying what the code does isn't a why.
- A count names its members: "the four parts: the link, the log blocks,
  the commands, and take-off and landing".
- Describe the project as it is. No history the reader wasn't told, such
  as "before the split"; a drop-down about the history itself is fine.
- A cross-reference says what's there, and links it: "Section 5 animates a
  take-off", not "Section 5 flies it".
- A word from the code (a builder, a callback, a forward) gets a plain
  description at its first use, or a drop-down. A detail with no room to
  explain is left to the code's docstrings.
- An edge case the reader can't picture gets an example: a lost link
  "nothing has raised yet" is one that drops during the wait after the
  buzzer's silence.
- An analogy uses a general idea (an interface, a template, a pointer), not
  one language's newest feature. Say what Python does that a C++ reader
  wouldn't expect, such as variables holding references, never copies.
- "Sleep" for a timed pause. "Wait" alone is ambiguous.
- A cause that isn't known is written as possible causes, each with its
  evidence, and the evidence against.
- A diagram that shows a failure also shows what the design does about it.
  A failure with no answer only alarms.

## Glossary dots

- Dot a glossary term at its first use in every lede, card and drop-down:
  each is read on its own. Not inside a button or a heading.
- A dotted term's pop-up shows its definition from `docs/glossary.md` at the
  pinned commit, which `tools/tour_numbers.py` writes into the page. Run it
  after dotting a new term. A term the glossary doesn't define there stops
  the script: add it to the glossary first, then move the pin.
- "Part" is the glossary's word for the four objects the adapter builds. A
  file is a module, and a folder of modules is a package.
- `tests/docs/test_tour_dots.py` fails while a term the page dots anywhere
  has no dot at its first use in a lede, card or drop-down. Text in a link,
  button, heading, drop-down title, code or diagram doesn't count.
- A glossary word in its everyday sense ("play a part", a drone that
  drifts sideways) gets `<span class="plain">`, which the check skips.
  Reword instead where that reads as well. Read the code before calling a
  use plain: "the PC's clock" is the glossary's *Clock*.
- A part's name before "part" ("the link part") is a use of *Part*, not of
  *Link* or *Command*. A part's name alone, as in a list of the four, is
  dotted when the glossary has it (*Link*, *Log block*, *Command*).

## Cut clutter

- No placeholder marks, and no note anywhere of which values are placeholders.
- No focus-area tags.
- No project jargon about how the tour is being built ("pass one", "pass
  two"). An unwritten section says in plain words that it's coming.

## Formulas

- Don't write a formula out in words. Give an approximate result for an example
  input, and put the whole formula in a drop-down.

## Names

- Headings are short and plain: "The Parts", not "Meet the parts". Nothing
  cute.
- A reading time is honest about how much there is to take in.

## Interactive parts

- Every interactive diagram opens with a "How to interact" line above it
  (`<p class="interact">`), so the reader sees it before trying the diagram.
  The caption below keeps only sources and notes.
- No switch that opens every drop-down at once, and no reading-time button:
  the page looks bad fully open, and the buttons weren't clear.
- A number a reader would wonder about, such as a firmware limit, gets a
  drop-down saying where it comes from.
- Replaying an animation starts at time 0. Time spent paused or finished
  doesn't count.

## Evidence

- Every claim links to its evidence: the code or a test at the pinned commit,
  an ADR or a facts register row. A claim with nothing to link is left out.
- No field result without its committed test log or recording, linked.
- A Markdown file opens rendered, never as code: link a heading's anchor
  (`ARCHITECTURE.md#5-timing-and-threads`), not `?plain=1#L…`.
  `tests/docs/test_tour_links.py` checks both.
- A code excerpt's caption is its file and lines, and what else it links.
  No notes on how the excerpt was edited ("docstring left out"); a cut in
  the code shows as `...`.
- A footer says the architecture and decisions are Joe's and the
  implementation is AI-assisted, with the ADRs as the record.

## Patterns that worked

Joe reviewed chapter 1 and left these with no notes, so reuse them:

- A stack of layers in SVG, each opening a side card (section 1).
- A list of buttons with a side card: modules with a length bar (section 2),
  steps with a time-limit bar (section 7), failures with a numbered chain of
  what happens (section 8), planted bugs with every test that failed
  (section 9).
- A timeline of packets and ticks: click a tick for each value's age in a
  table, and a button that drops packets (section 3).
- An animated flight with a time slider, and a state machine and the
  transcript's sends that follow it, with clickable failure branches
  (section 5).
- A calculator with example presets that highlights the rule that decided
  (section 6).

What didn't work: a step-through of sends whose states used words the page
never explained, with no consequence shown (section 4, removed).

## Form

- One HTML page per chapter in `docs/tour/`, sharing `tour.css` and `tour.js`.
  No build step, libraries or web fonts. Inline SVG, dark theme only
  ([ADR-0096](../../../docs/decisions/0096-the-project-tour-is-one-html-page-per-chapter-pinned-to-one-commit.md)).
- The one outside script is the GoatCounter visit count, the last line before
  `</body>`, the same as the portfolio home page's. Keep it on every chapter.
  It skips local files, `localhost` and framed pages (facts register).

## Numbers from the code

- Never type a number from the code by hand. Mark it and let
  `tools/tour_numbers.py` write it, read at the pinned commit:
  `<span class="from-code" tabindex="0" data-const="NAME">`, with `data-form`
  for another form (`number`, `hz`, `s`, `cm`, `hours`); `data-formula` for a
  number worked out from constants; `data-const-link` for a link to a
  constant's lines. Inside a `summary` or SVG text, leave out the class (a
  plain `span`, or a `tspan`), so a tap opens the drop-down, not a pop-up.
- A module's length in lines is marked too: `data-module-lines="PATH"` on a
  `span`, and `data-module-bar="PATH"` on a bar's `i`, whose width the script
  writes beside the longest module with a bar on the page. `PATH` is from the
  repository's root.
- `tour.js` reads a constant with `value("NAME")` or `text("NAME")`, never a
  copy.
- A constant not in the script's `CONSTANTS` list gets a row there, with its
  unit. A new formula goes in `FORMULAS`.
- Stay hand-written: example inputs, the model's own choices, quotes of a
  transcript, and numbers from the facts register (linked).
- Moving the pin: replace the hash on the page, in its full and short forms,
  then run the script. List the files changed since the old pin
  (`git diff --name-only`) and check every line link into one of them: the
  link test passes on a link whose lines have only shifted.
- A number is shown in its shortest form, with a non-breaking space before
  its unit: "1 s", not "1.0 s". The script does this.
- A number's pop-up shows `NAME = value`, its docstring with ADR numbers as
  links (a "VERIFY" sentence dropped), and a link to its line. A worked-out
  number shows its formula, a sentence and the sum.

## Colors

- Bars that measure the same thing share one color: every module's
  line-count bar is yellow. Color never carries a meaning the page doesn't
  state.

## The how-to box

- The word "dots" in "Words and numbers with dots" is itself dotted, as the
  example, and its pop-up is a joke definition of dots: "See dots", where "dots" opens
  the same pop-up (`data-pop-title`, `data-pop-see-itself`, `data-pop-from`
  on the span). Keep it on every chapter.

## Check and publish

1. Run `.venv\Scripts\python tools/tour_numbers.py`, then
   `.venv\Scripts\python -m pytest tests/docs`.
2. Open the page at desktop and phone widths, and try what changed. Headless
   Edge won't make a window narrower than about 500 px: for a phone, load the
   page in a 390 px iframe.
3. Republish the private preview at the same URL (`docs/next-up.md` or the
   tour's work order has it), from a copy without the document-skeleton lines
   (doctype, `html`, `head`, the two `meta` lines for charset and viewport,
   `body` and their closing tags), with `tour.css` and `tour.js`.

## Copy to the portfolio

The live tour, `https://joecgo.com/crazyflie-project-tour`, is a copy in
`joecgo/portfolio`. No test notices a stale copy, so run these steps after
any tour change Joe accepts, once it's committed.

1. Clone `joecgo/portfolio` into the scratchpad.
2. Write the three files into its `crazyflie-project-tour/` from the commit,
   not the working tree, whose line endings differ:
   `git show <commit>:docs/tour/adapter.html` as `index.html`, then
   `tour.css` and `tour.js`.
3. Show Joe what changed, and commit and push only after Joe's OK.
4. Download the three live files and compare each one's SHA-256 with
   `git show`'s. If they differ, the site may not have updated yet: compare
   again later, and don't report it live until they match.
