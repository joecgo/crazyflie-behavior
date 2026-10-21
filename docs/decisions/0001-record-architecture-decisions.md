# 0001: Record architecture decisions as ADRs

- **Status:** Accepted
- **Date:** 2026-10-17
- **Origin:** AI recommendation accepted.

## Context

This project is a portfolio piece meant to show architectural judgment in
robotics. The code is implemented with an AI assistant, so the design reasoning
must be visible and clearly the architect's own. Without a record, decisions end
up buried in chat history and the "why" is lost.

## Options considered

### A. No formal record
Decisions live in commit messages and memory.
- **Pros:** zero overhead.
- **Cons:** reasoning is invisible to reviewers and easy to forget or contradict.

### B. One big design document
- **Pros:** single place to read.
- **Cons:** rewritten over time, so the history of *how* the design evolved is lost.

### C. Architecture Decision Records
One short, numbered, immutable file per decision. A changed decision gets a new
ADR that supersedes the old one.
- **Pros:** shows the reasoning and its evolution, cheap to write, an
  industry-standard practice reviewers recognize.
- **Cons:** small ongoing discipline cost.

## Decision

Option C. Every architectural decision gets an ADR in `docs/decisions/`, using
`0000-template.md`. The architect makes the call. The assistant drafts the
options and writes the record.

## Consequences

- Design question rounds end with one ADR per decision.
- `docs/glossary.md` is updated alongside any ADR that introduces or changes terms.
- `CLAUDE.md` tells the assistant to check accepted ADRs before changing designs.
