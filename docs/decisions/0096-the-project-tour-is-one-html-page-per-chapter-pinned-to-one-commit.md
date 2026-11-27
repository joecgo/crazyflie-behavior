# 0096: The project tour is one HTML page per chapter, pinned to one commit and copied to the portfolio by a skill step

- **Status:** Accepted
- **Date:** 2026-11-27
- **Origin:** Mixed: the tour, its reader and its style are mine; the form, the
  checks and the publishing steps were my choices among options Claude gave,
  with its recommendation accepted

## Context

The [glossary's](../glossary.md) *Project tour* needed a form. The first
chapter, on the Crazyflie adapter, tested the idea; I accepted it on
2026-11-27. Its live copy is outside this repository, so later edits don't
reach it.

## Options considered

For keeping the live copy in step:

- **A. A step in the project-tour skill:** no new code; skipped if an edit
  skips the skill.
- **B. A script in `tools/`:** repeatable, but new code, tests and a local
  clone of the portfolio.
- **C. A workflow that copies on push:** never stale, but needs a token for
  the other repository and publishes edits before I've judged them.

For counting visits: the line committed in `docs/tour/`, added at each copy,
or none. For a second chapter's place: decide then, beside the first, or
behind a contents page.

## Decision

- **Scope:** one chapter at a time, as a vertical slice. A static site
  generator comes later, with more chapters.
- **Form:** one HTML page per chapter in `docs/tour/`, sharing `tour.css` and
  `tour.js`. No build step, libraries or web fonts. Inline SVG, dark theme.
  Each page holds its own term definitions.
- **Evidence:** links into this repository are pinned to one commit, and a
  test reads that commit with git and fails on a link to a missing file, line
  or heading, so continuous integration checks out the full history.
- **Numbers and definitions:** `tools/tour_numbers.py` (it keeps its name)
  reads them at the pinned commit and writes them into the pages: text,
  tables, the animations' numbers, other forms and constant links. A test
  fails while a committed page differs from what it writes.
- **Dots:** a test, with its code in the test file, fails while a term the
  page dots has no dot at its first use in a lede, card or drop-down. A
  glossary word in its everyday sense is marked `<span class="plain">`. A
  part's name before "part" is a use of *Part*; a part's name alone is dotted
  when the glossary has the term. Table label cells keep their dots.
- **Publishing:** a private preview first, then
  `joecgo.com/crazyflie-project-tour`. **A:** the project-tour skill copies
  the three files to `joecgo/portfolio` (`adapter.html` as `index.html`),
  pushes after my OK and checks that the live files match.
- **Visits:** the portfolio home page's GoatCounter line is committed in the
  tour's page, so the copy stays exact. It's the one outside script the page
  loads, an exception to "no libraries".
- **Chapter 2's place** is decided when chapter 2 exists.

## Consequences

- No test notices a stale live copy; only the skill step does.
- Moving the pin means rereading each line link into a changed file: the link
  test passes on lines that only shifted.
- The dot check misses a glossary term the page never dots.
- The shared address keeps showing chapter 1; a later layout might change it.
- Follow-ups: backlog #169 (the visit-count line and the skill step) and #170
  (chapter 2's place and the generator).
