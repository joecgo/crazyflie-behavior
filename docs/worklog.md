# Work log

Newest first. One row per day and milestone, readable at a glance; a day that
covers two milestones gets a row for each. A milestone names what the work is
building towards. Time per milestone is summed at the bottom.

Milestones so far:
- **First flight:** everything up to the drone's first hover through the
  project's own code (field-test stage 1): tools and process, the
  architecture, the drone interface, the tick loop and the first programs.
  Reached when that first hover passes.

| Date | Hours | Milestone | Worked on |
|---|---|---|---|
| 2026-10-30 | ~1.5 | First flight | Work log: a milestone for each row, with time per milestone summed at the bottom; the first milestone is First flight. ADR-0029: connecting has time limits, each cflib step waited for on a helper thread so Ctrl+C gets through on Windows too. Found that `open_link()` can wait forever if the link drops while connecting. 13 new tests, each proven by bug planting; a test that failed only sometimes led to a real gap; code review fixes. ADR-0030: a minimal safety layer for First flight (a pre-check, one failsafe: land; velocity and fast mode refused until the speed envelope exists, backlog #30). Built it with the hover test, the tick step for flying and the hover program; the mock adapter now streams every value, and the programs share their start-up code. 69 new tests and two fitness functions, proven by 78 planted bugs; a high-level code review. Checked the firmware source: it stops the motors when its own landing ends, which ADR-0012 assumed it didn't (backlog #31), and on the floor a land command spins an armed drone's motors up. The review found that the first ticks on the real drone have no telemetry yet (backlog #32). A review checklist, `REVIEW.md`, built from the mistakes log's takeaways, which every code review now works through |
| 2026-10-29 | ~3.5 | First flight | Listed what's left before a test flight. Tick loop design: ADR-0025, the safety layer runs a pre-check before behaviors, answers command requests at once, and sends one command per command slot per tick (supersedes ADR-0008's safety queries; closes backlog #21). ADR-0026: the tick loop keeps time and calls one tick step, a watchdog reports hung ticks, and every tick is logged. First tick loop code: 32 tests and a fitness function, each proven by planting bugs; code review fixes. Started a log of Claude's mistakes (11 entries). Moved deprecated glossary terms to their own section, and replaced the status column with ADR links. Backlog #27: logging must never block the tick loop. Ctrl+C is a stop request; later presses are ignored so they can't cut a landing short. ADR-0027, operator controls: Windows hotkeys plus an optional PS5 controller (a lost controller lands), "land now" through the safety pre-check, a kill latch, no dead-man mode (a drop can damage the battery). Checked the firmware: an emergency stop locks the drone until it reboots. ADR-0028: programs live in `programs/`; the bench program logs every snapshot and never commands the drone; the mock adapter by default; plain logging, with QuickEdit off in old console windows. Built the start-up code (logging, Ctrl+C, QuickEdit) and the bench program: 40 new tests, each proven by planting bugs, and three code reviews. Split the mistakes log by who caught each mistake |
| 2026-10-27 | ~2.0 | First flight | Test review: fitness functions. Switched to reading the test names as a spec, which showed gaps in the Crazyflie adapter's tests: 20 new tests for connect(), the telemetry callbacks and the commands, proven with planted bugs. Ordered the hardware (STEM ranging bundle, Buzzer deck, long pins, spare battery, charger) and chose a LiPo bag for storage. Started backlog #2, tick rate: checked sensor update rates in the firmware; the Multi-ranger's 10 Hz is a firmware choice (new backlog #24). ADR-0022: the Multi-ranger keeps the stock firmware's 10 Hz; no follow-up item (removed backlog #24). Checked the Flow deck's rates in the firmware (down range 40 Hz, optical flow just under 100 Hz). ADR-0023: the tick loop runs at 20 Hz, with log periods matched to their sources (state and down range 20 ms, Multi-ranger 100 ms, battery 1000 ms); a test checks the periods. ADR-0024, tick timing: due times on a fixed beat, start at once after an overrun and skip missed ticks, plain sleep (spinning would hold the GIL from cflib's radio thread), garbage collector left on and measured. Six glossary terms for the tick loop. Backlog #25 (revisit the tick rate with measurements) and #26 (a hung tick drops the drone) |
| 2026-10-26 | ~0.5 | First flight | Code review: tests, part 1 (geometry, snapshot, clock, conversions, adapter status); all float comparisons checked. Coding style: compare computed floats with `pytest.approx`. Learned `range` loops, context managers (`with`) and how `pytest.raises` fails a test |
| 2026-10-24 | ~4.25 | First flight | Code review on my phone: clock and geometry. Reviewing touchdown, found that the height-estimate fallback could cut the motors in mid-air. ADR-0019: only a steady down reading confirms touchdown, otherwise a bounded final descent; code review fixes and landing tests against a fake cflib. Reviewed conversions and the Crazyflie adapter section by section: clearer names, explicit landing phases, a full-words naming rule. Found that cflib's status read returns old data on a timeout; ADR-0021 streams drone status with position and velocity in one log block. ADR-0020: failures degrade gracefully and are always logged. Updated Git and set up the GitHub CLI |
| 2026-10-23 | ~1.75 | First flight | Code review: geometry (added `Vector3.ZERO`) and the snapshot. ADR-0018: data records are frozen dataclasses with slots, enforced by a new fitness function. Dropped the fixed-yaw wording from range directions. Learned pip, packages, egg-info and class methods |
| 2026-10-22 | ~2.0 | First flight | Code review on my phone (GitHub app): drone interface, telemetry buffer, mock adapter. Started a review to-do list |
| 2026-10-21 | ~1.25 | First flight | Game design: hide-and-seek returns as the first game, safe by structure (ADR-0016: the drone hides, lands and stops its motors; a mapping run first). Hints every 15 s from a Buzzer deck (ADR-0017), after checking the firmware source (LEDs through a parameter; motor tones would need custom firmware). Hide-and-seek rules, glossary sections per game, README hardware. Learned how continuous integration, YAML and pytest test discovery work |
| 2026-10-20 | ~5.5 | First flight | Design: ADRs 0008–0015 (drone interface, clock, code foundations, setpoint timeout, touchdown confirmation, kill switch, Rerun, first game). First code: snapshot types, clocks, telemetry buffer, drone interface, mock and Crazyflie adapters, 63 tests incl. fitness functions, strict pyright, continuous integration. Code review fixes. Reflected on authorship: ADR origins and an index. Researched player tracking (UWB from firmware source, deck compatibility, prices). Game design: dropped hide-and-seek for safety; chose Catch the bird |
| 2026-10-19 | ~1.0 | First flight | Design: ADR-0007 telemetry buffer, per-tick snapshot, blackboard as behavior memory. Drone interface design in progress (safety layer as sole caller, shared TelemetryBuffer, range readings incl. down, command set, world frame with fixed yaw). Backlogged tick timing, ceiling protection, yaw control, mapping |
| 2026-10-18 | ~3.75 | First flight | Design: ADR-0003 tick loop, ADR-0004 strict typing/ruff/SI units, ADR-0005 control modes (steering + fast mode), ADR-0006 Crazyflie-focused interface. Coding style, decision backlog, tools/ exemption. Published the repo on GitHub |
| 2026-10-17 | ~0.5 | First flight | Project process: CLAUDE.md working rules, shared glossary (UE5 analogies), ADRs 0001–0002, field-testing plan, continuous integration and fitness functions as focus areas |
| 2026-10-16 | ~0.5 | First flight | Setup: Python 3.12, repo, venv, cflib, PyCharm. Weighed C++ options and kept Python. cflib primer checked against installed source |

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

## Time per milestone

| Milestone | Hours |
|---|---|
| First flight | ~28 |
| **Total** | **~28** |
