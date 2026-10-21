# Work log

Newest first. One line per work session, readable at a glance.

| Date | Hours | Worked on |
|---|---|---|
| 2026-10-20 | ~0.5 | Design: ADR-0008 drone interface (safety queries for behavior trees), ADR-0009 clock abstraction. Confirmed sensor-based mapping as a future feature. Prepared decisions for the first code |
| 2026-10-19 | ~1.0 | Design: ADR-0007 telemetry buffer, per-tick snapshot, blackboard as behavior memory. Drone interface design in progress (safety layer as sole caller, shared TelemetryBuffer, range readings incl. down, command set, world frame with fixed yaw). Backlogged tick timing, ceiling protection, yaw control, mapping |
| 2026-10-18 | ~3.75 | Design: ADR-0003 tick loop, ADR-0004 strict typing/ruff/SI units, ADR-0005 control modes (steering + fast mode), ADR-0006 Crazyflie-focused interface. Coding style, decision backlog, tools/ exemption. Published the repo on GitHub |
| 2026-10-17 | ~0.5 | Project process: CLAUDE.md working rules, shared glossary (UE5 analogies), ADRs 0001–0002, field-testing plan, continuous integration and fitness functions as focus areas |
| 2026-10-16 | ~0.5 | Setup: Python 3.12, repo, venv, cflib, PyCharm. Weighed C++ options and kept Python. cflib primer checked against installed source |

## Details

Notable moments worth revisiting for the portfolio: hard problems, surprising
findings, key design turns. Added only with the architect's OK.

<!-- Format:
### YYYY-MM-DD: <short title>
A few sentences: what happened, why it matters, links to ADRs, commits or session logs.
-->
