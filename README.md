# crazyflie-behavior

[![checks](https://github.com/joecgo/crazyflie-behavior/actions/workflows/checks.yml/badge.svg)](https://github.com/joecgo/crazyflie-behavior/actions/workflows/checks.yml)

Autonomous behavior experiments for the [Bitcraze Crazyflie 2.1+](https://www.bitcraze.io/products/crazyflie-2-1-plus/) nano drone, written in Python with [cflib](https://github.com/bitcraze/crazyflie-lib-python).

**The goal: a drone that plays hide-and-seek with a small child.** While the
child waits behind a gate, the drone flies off, hides behind a wall, lands and
turns its motors off. The child hunts for it, and when they pick it up, it
lights up and the computer plays a fanfare. Game-AI techniques (a map of the
room, choosing hiding spots, line-of-sight checks) on a real robot, where
sensors are noisy and positions drift. The game is safe by design: the drone
flies only when the play area is empty. See [the rules](docs/hide-and-seek.md).
The second game is [Catch the bird](docs/catch-the-bird.md).

The behavior logic is kept separate from the drone connection, so the same
logic runs against a mock drone, a simulator, or real hardware.

## How this project is built

I set the goals, priorities and constraints, and I make every design decision,
recorded as Architecture Decision Records with the options considered (see the
[index](docs/decisions/README.md)). Most options, and all implementation and
verification, are AI-assisted (Claude Code). Each record notes whether a
decision was my own idea, an AI recommendation I accepted, or one I overrode.
The code follows the shared vocabulary in [`docs/glossary.md`](docs/glossary.md).
Real-world testing is documented session by session in
[`docs/field-testing/`](docs/field-testing/README.md).

## Setup (Windows)

Requires Python 3.12 (`py -3.12 --version` to check).

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
```

`.venv` is this project's private copy of Python and its packages (similar to a
per-solution NuGet packages folder). It is git-ignored; `pyproject.toml` lists
the dependencies, with exact versions, so the environment can be rebuilt.
`-e` installs the project in editable mode: code changes take effect without
reinstalling.

**PyCharm:** Settings → Project → Python Interpreter → Add Interpreter →
Existing → `.venv\Scripts\python.exe`.

## Checks

The same four checks run locally and in continuous integration on every push:

```powershell
.venv\Scripts\ruff format --check .   # formatting
.venv\Scripts\ruff check .            # lint
.venv\Scripts\pyright                 # strict type checking
.venv\Scripts\python -m pytest        # tests and architecture fitness functions
```

In PyCharm, the **tests** run configuration runs the test suite.

## Hardware smoke test

```powershell
.venv\Scripts\python tools\first_flight.py
```

Without hardware it reports that no Crazyflie was found, which confirms the
setup works. In PyCharm, use the **first_flight** run configuration.

## Hardware (planned)

- Crazyflie 2.1+ and Crazyradio USB dongle
- Flow deck (needed for stable autonomous hover)
- Multi-ranger deck (obstacle sensing and mapping)
- Buzzer deck (hint chirps)
- Long pins (19+2+4 mm) to stack three decks: two on top, the Flow deck underneath
- Spare batteries and propellers (about 7 minutes of flight per battery)
- PS5 controller (DualSense), optional, for the operator controls
  ([ADR-0027](docs/decisions/0027-operator-controls.md)). A USB cable is safer
  than Bluetooth for flights: an unplugged cable is noticed at once.

On Windows the Crazyradio needs a USB driver installed with Zadig. Follow the
Bitcraze docs for the current steps.

## Layout

```
src/crazyflie_behavior/
  geometry.py       # Vector3
  snapshot.py       # the per-tick snapshot and the types inside it
  timing/           # clocks: real and simulated
  loop/             # the tick loop: keeps time and calls the tick step
  drone/            # drone interface, telemetry buffer, mock adapter
    crazyflie/      # Crazyflie adapter: the only code that imports cflib
tests/
  architecture/     # fitness functions: ADR rules enforced as tests
tools/
  first_flight.py   # hardware smoke test: scan for a Crazyflie
docs/
  hide-and-seek.md  # the rules of the first game
  catch-the-bird.md # the rules of the second game
  glossary.md       # the project's shared vocabulary
  coding-style.md   # conventions the tools can't check
  decisions/        # Architecture Decision Records (ADRs)
  decision-backlog.md  # open design questions, in order of need
  field-testing/    # real-world test process and session logs
  cflib-primer.md   # how cflib works, checked against the installed version
  claude-mistakes.md  # mistakes Claude made, and what they say about its weak spots
```
