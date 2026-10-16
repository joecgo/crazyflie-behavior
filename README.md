# crazyflie-behavior

Autonomous behavior experiments for the [Bitcraze Crazyflie 2.1+](https://www.bitcraze.io/products/crazyflie-2-1-plus/) nano drone, written in Python with [cflib](https://github.com/bitcraze/crazyflie-lib-python).

The goal is NPC-style behavior (patrol, react to obstacles, and so on) with the
behavior logic kept separate from the drone connection, so the same logic can run
against a mock drone, a simulator, or real hardware.

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
.venv\Scripts\python src\first_flight.py
```

Without hardware it reports that no Crazyflie was found, which confirms the setup works.

## Hardware (planned)

- Crazyflie 2.1+ and Crazyradio USB dongle
- Flow deck (needed for stable autonomous hover)
- Multi-ranger deck (obstacle sensing, optional)
- Spare batteries and propellers (about 7 minutes of flight per battery)

On Windows the Crazyradio needs a USB driver installed with Zadig. Follow the
Bitcraze docs for the current steps.

## Layout

```
src/
  first_flight.py   # cflib smoke test: scan for a Crazyflie
```
