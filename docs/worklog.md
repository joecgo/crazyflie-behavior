# Work log

Newest first. One line per work session, readable at a glance.

| Date | Hours | Worked on |
|---|---|---|
| 2026-10-27 | ~2.0 | Test review: fitness functions. Switched to reading the test names as a spec, which showed gaps in the Crazyflie adapter's tests: 20 new tests for connect(), the telemetry callbacks and the commands, proven with planted bugs. Ordered the hardware (STEM ranging bundle, Buzzer deck, long pins, spare battery, charger) and chose a LiPo bag for storage. Started backlog #2, tick rate: checked sensor update rates in the firmware; the Multi-ranger's 10 Hz is a firmware choice (new backlog #24). ADR-0022: the Multi-ranger keeps the stock firmware's 10 Hz; no follow-up item (removed backlog #24). Checked the Flow deck's rates in the firmware (down range 40 Hz, optical flow just under 100 Hz). ADR-0023: the tick loop runs at 20 Hz, with log periods matched to their sources (state and down range 20 ms, Multi-ranger 100 ms, battery 1000 ms); a test checks the periods. ADR-0024, tick timing: due times on a fixed beat, start at once after an overrun and skip missed ticks, plain sleep (spinning would hold the GIL from cflib's radio thread), garbage collector left on and measured. Six glossary terms for the tick loop. Backlog #25 (revisit the tick rate with measurements) and #26 (a hung tick drops the drone) |
| 2026-10-26 | ~0.5 | Code review: tests, part 1 (geometry, snapshot, clock, conversions, adapter status); all float comparisons checked. Coding style: compare computed floats with `pytest.approx`. Learned `range` loops, context managers (`with`) and how `pytest.raises` fails a test |
| 2026-10-24 | ~4.25 | Code review on my phone: clock and geometry. Reviewing touchdown, found that the height-estimate fallback could cut the motors in mid-air. ADR-0019: only a steady down reading confirms touchdown, otherwise a bounded final descent; code review fixes and landing tests against a fake cflib. Reviewed conversions and the Crazyflie adapter section by section: clearer names, explicit landing phases, a full-words naming rule. Found that cflib's status read returns old data on a timeout; ADR-0021 streams drone status with position and velocity in one log block. ADR-0020: failures degrade gracefully and are always logged. Updated Git and set up the GitHub CLI |
| 2026-10-23 | ~1.75 | Code review: geometry (added `Vector3.ZERO`) and the snapshot. ADR-0018: data records are frozen dataclasses with slots, enforced by a new fitness function. Dropped the fixed-yaw wording from range directions. Learned pip, packages, egg-info and class methods |
| 2026-10-22 | ~2.0 | Code review on my phone (GitHub app): drone interface, telemetry buffer, mock adapter. Started a review to-do list |
| 2026-10-21 | ~1.25 | Game design: hide-and-seek returns as the first game, safe by structure (ADR-0016: the drone hides, lands and stops its motors; a mapping run first). Hints every 15 s from a Buzzer deck (ADR-0017), after checking the firmware source (LEDs through a parameter; motor tones would need custom firmware). Hide-and-seek rules, glossary sections per game, README hardware. Learned how continuous integration, YAML and pytest test discovery work |
| 2026-10-20 | ~5.5 | Design: ADRs 0008–0015 (drone interface, clock, code foundations, setpoint timeout, touchdown confirmation, kill switch, Rerun, first game). First code: snapshot types, clocks, telemetry buffer, drone interface, mock and Crazyflie adapters, 63 tests incl. fitness functions, strict pyright, continuous integration. Code review fixes. Reflected on authorship: ADR origins and an index. Researched player tracking (UWB from firmware source, deck compatibility, prices). Game design: dropped hide-and-seek for safety; chose Catch the bird |
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

### 2026-10-24: A touchdown backup that failed with the sensor it backed up

Reviewing `touchdown.py` line by line, I noticed that when the down range had
nothing usable, the position estimate's height confirmed touchdown instead.
On a Crazyflie that height comes mostly from the same down sensor, so the
failure that triggers the backup also corrupts it, and the motors could be cut
in mid-air. Removing the backup would have left the drone hovering until its
battery died, so I pushed back on that fix: the drone must always land. The
result separates "getting down" from "stopping the motors": only a steady down
reading confirms touchdown; otherwise a slow final descent continues until a
time limit says the drone must be on the floor. A second code review then
hardened it against noisy readings and stalled ticks
([ADR-0019](decisions/0019-final-descent-when-touchdown-unconfirmed.md), commit `1187f8d`).

### 2026-10-21: Hide-and-seek made safe by the game's structure

Hide-and-seek was dropped the day before
([ADR-0015](decisions/0015-first-game-catch-the-bird.md)) because a hiding drone
can't see the player coming, so any escape could fly into a child. I redesigned
the game so that danger can't arise: the drone flies only while the play area is
empty (an adult starts each round, and a gate keeps the player out), and it
lands and stops its motors before the search begins. A child only ever meets a
drone with its motors off. The same rule later ruled out motor tones for hints,
in favor of a Buzzer deck. Safety comes from when things happen in the game, not
from sensing ([ADR-0016](decisions/0016-first-game-hide-and-seek-drone-lands.md),
[ADR-0017](decisions/0017-hint-chirps-from-buzzer-deck.md), commit `f19f878`).
