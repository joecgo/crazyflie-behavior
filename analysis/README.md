# Analysis scripts

Scripts whose numbers or charts a committed doc cites, such as a test log or
an ADR ([ADR-0092](../docs/decisions/0092-cited-analysis-scripts-are-committed-to-analysis-and-the-snapshot-line-goes-after-the-first-recorded-session.md)).
Exploring happens in `drafts/<session>/`; a script comes here in the same
change as the doc that cites it.

- A script reads only committed recordings (`recordings/*.jsonl.gz`), through
  `read_recording`. It never reads a text log or touches the drone.
- Fitness functions: `src/` never imports this folder, and nothing here
  imports cflib.
- Scripts pass ruff and pyright strict. A helper that scripts share has tests
  in `tests/analysis/`.
- Run one from the repository root: `.venv\Scripts\python analysis\<script>.py`.
