# crazyflie-behavior

Autonomous behavior experiments for the [Bitcraze Crazyflie 2.1+](https://www.bitcraze.io/products/crazyflie-2-1-plus/) nano drone, written in Python with [cflib](https://github.com/bitcraze/crazyflie-lib-python).

The goal is NPC-style behavior (patrol, react to obstacles, and so on) with the
behavior logic kept separate from the drone connection, so the same logic can run
against a mock drone, a simulator, or real hardware.

## How this project is built

The architecture and every design decision are mine. Each one is recorded,
with the options I considered and my reasoning, as an Architecture Decision
Record in [`docs/decisions/`](docs/decisions/). The implementation is
AI-assisted (Claude Code), working to those decisions and to the shared
vocabulary in [`docs/glossary.md`](docs/glossary.md). Real-world testing is
documented session by session in [`docs/field-testing/`](docs/field-testing/README.md).

## Setup (Windows)

Requires Python 3.12 (`py -3.12 --version` to check).

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

`.venv` is this project's private copy of Python and its packages (similar to a
per-solution NuGet packages folder). It is git-ignored; `requirements.txt` is what
gets committed so the environment can be rebuilt.

**PyCharm:** Settings → Project → Python Interpreter → Add Interpreter →
Existing → `.venv\Scripts\python.exe`.

## Running

```powershell
.venv\Scripts\python tools\first_flight.py
```

A hardware smoke test. Without hardware it reports that no Crazyflie was
found, which confirms the setup works. In PyCharm, use the **first_flight**
run configuration.

## Hardware (planned)

- Crazyflie 2.1+ and Crazyradio USB dongle
- Flow deck (needed for stable autonomous hover)
- Multi-ranger deck (obstacle sensing, optional)
- Spare batteries and propellers (about 7 minutes of flight per battery)

On Windows the Crazyradio needs a USB driver installed with Zadig. Follow the
Bitcraze docs for the current steps.

## Layout

```
tools/
  first_flight.py   # hardware smoke test: scan for a Crazyflie
docs/
  glossary.md       # the project's shared vocabulary
  coding-style.md   # conventions the tools can't check
  decisions/        # Architecture Decision Records (ADRs)
  field-testing/    # real-world test process and session logs
  cflib-primer.md   # how cflib works, checked against the installed version
```
