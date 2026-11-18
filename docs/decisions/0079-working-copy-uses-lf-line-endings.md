# 0079: Every text file uses LF line endings, in the repository and the working copy

- **Status:** Accepted
- **Date:** 2026-11-18
- **Origin:** AI recommendation accepted (the option was the AI's; the choice of A over the AI's recommendation C was mine: no fitness function).

## Context

Twice a scripted edit changed a file's line endings ([M-169, M-171](../claude-mistakes.md); backlog #119). The repository stores LF, but `core.autocrlf=true` gives Windows working copies CRLF, and the working copy is already mixed: 119 files CRLF, 121 LF (`git ls-files --eol`, 2026-11-18). A script can't know which a file uses.

## Options considered

- **A. `.gitattributes` with `* text=auto eol=lf` and an `.editorconfig` with `end_of_line = lf`:** one ending everywhere. Fixes the cause. Costs a one-time renormalise of the working copy.
- **B. A fitness function only:** detects mixed endings after the fact; always green on Linux continuous integration.
- **C. A and B together.** The AI's recommendation.
- **D. `eol=crlf`:** keeps the Windows look; scripts must write CRLF, and Linux tools expect LF.

## Decision

A. Every text file is LF in the repository and in the working copy, so a script that writes LF is always right and nothing has to guess. A file that must be CRLF (a Windows-only script) gets its own `eol=crlf` line in `.gitattributes`.

I chose A without a fitness function. The risk I accepted: a script or editor that ignores `.gitattributes` and `.editorconfig` can still write CRLF, and nothing tests for it. The diff stat after a scripted edit (M-171's guard) remains the only check.

## Consequences

- Scripts and tools can read and write text without preserving endings.
- Built 2026-11-18: `.gitattributes`, `.editorconfig`, and the renormalise of the 119 CRLF working files (no committed content changed).
- PyCharm follows `.editorconfig`; GitHub Desktop follows `.gitattributes`.
- No glossary change.
