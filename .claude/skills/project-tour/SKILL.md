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
- A footer says the architecture and decisions are Joe's and the
  implementation is AI-assisted, with the ADRs as the record.

## Form

- One HTML page per chapter in `docs/tour/`, sharing `tour.css` and `tour.js`.
  No build step, libraries or web fonts. Inline SVG, dark theme only.

## Numbers from the code

- Never type a number from the code by hand. Mark it and let
  `tools/tour_numbers.py` write it, read at the pinned commit:
  `<span class="from-code" tabindex="0" data-const="NAME">`, with `data-form`
  for another form (`number`, `hz`, `s`, `cm`, `hours`); `data-formula` for a
  number worked out from constants; `data-const-link` for a link to a
  constant's lines. Inside a `summary` or SVG text, leave out the class (a
  plain `span`, or a `tspan`), so a tap opens the drop-down, not a pop-up.
- `tour.js` reads a constant with `value("NAME")` or `text("NAME")`, never a
  copy.
- A constant not in the script's `CONSTANTS` list gets a row there, with its
  unit. A new formula goes in `FORMULAS`.
- Stay hand-written: example inputs, the model's own choices, quotes of a
  transcript, and numbers from the facts register (linked).
- Moving the pin: replace the hash on the page, then run the script.
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
