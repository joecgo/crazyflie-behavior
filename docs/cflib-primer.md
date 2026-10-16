# cflib primer

How a Python program talks to a Crazyflie, checked against the installed
**cflib 0.1.34** (`.venv\Lib\site-packages\cflib\`) and Bitcraze's current
examples. File references below are inside that folder. Ctrl+click any cflib
name in PyCharm to jump to its source.

## The big picture

```
your script  ──radio (Crazyradio)──►  Crazyflie firmware
   │                                     │
   │  send commands (setpoints)          │  runs the fast loops (~1 kHz):
   │  receive telemetry (log blocks)     │  stabilization, state estimation,
   │  read/write parameters              │  motor control
```

Your Python code is the **AI layer**: it decides where to go at a few to tens
of Hz. The firmware is the **locomotion/physics layer**: it keeps the drone in
the air and follows your targets. That split is why Python is fast enough here.

All communication is over **CRTP**, a small packet protocol. Everything below
is a convenience wrapper over sending and receiving CRTP packets.

## 1. Connecting

```python
import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.utils import uri_helper

URI = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E7E7')

cflib.crtp.init_drivers()                       # register radio/USB drivers once
with SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache')) as scf:
    ...                                         # connected in here
# leaving the block closes the link, even if an exception was thrown
```

- **URI** is the drone's address: `radio://<dongle>/<channel>/<datarate>/<address>`.
  `uri_from_env` reads the `CFLIB_URI` environment variable, falling back to the
  factory default.
- **`Crazyflie`** (`crazyflie/__init__.py`) is the real API, and it is
  **asynchronous**. `open_link()` returns immediately and you learn the outcome
  through events: `connected`, `fully_connected`, `connection_failed`,
  `connection_lost`, `disconnected`. These are `Caller` objects. `add_callback(fn)`
  works like `event +=` in C# or a multicast delegate/signal in C++.
- **`SyncCrazyflie`** (`crazyflie/syncCrazyflie.py`) wraps that in blocking
  calls. It waits on those events with `threading.Event` so your script reads
  top to bottom.
- **`with ... as scf:`** is Python's RAII. `__enter__` opens the link and
  `__exit__` closes it, guaranteed, like a C++ destructor at scope end. cflib
  uses this pattern everywhere, including for flying (see below).
- On connect, cflib downloads the drone's **TOCs (tables of contents)**: the
  list of every loggable variable and parameter the firmware exposes, by name.
  `rw_cache='./cache'` saves them to disk so later connects are faster.
- `scf.wait_for_params()` blocks until parameter values have also arrived
  (the `fully_connected` event).

## 2. Telemetry (logging)

The drone doesn't answer "what's your position?" requests. You **subscribe** to
variables and it streams them at a fixed period. This is the perception feed
for your behavior.

```python
from cflib.crazyflie.log import LogConfig

logconf = LogConfig(name='Position', period_in_ms=100)    # 10 Hz
logconf.add_variable('stateEstimate.x', 'float')
logconf.add_variable('stateEstimate.y', 'float')
logconf.add_variable('stateEstimate.z', 'float')
```

Variable names are `group.name` strings from the TOC. A wrong name raises
`KeyError` when the config is added (`crazyflie/log.py`, `Log.add_config`).
Useful ones:

| Variable | Meaning |
|---|---|
| `stateEstimate.x/y/z` | Estimated position in meters (from the Flow deck + IMU) |
| `stateEstimate.yaw` | Heading in degrees |
| `range.front/back/left/right/up` | Multi-ranger distances, mm |
| `range.zrange` | Height above the floor, mm (Flow deck) |
| `pm.vbat` | Battery voltage |

Limits that matter: **one `LogConfig` carries at most 26 bytes** (about six
floats), and the period must be 10–2540 ms. Use several configs if you need more.

There are two ways to receive the data:

**Callback (asynchronous).** This is the one to use for behavior code:

```python
def on_position(timestamp, data, logconf):
    # runs on cflib's receive thread, not your main thread
    latest['x'] = data['stateEstimate.x']

scf.cf.log.add_config(logconf)
logconf.data_received_cb.add_callback(on_position)
logconf.start()
...
logconf.stop()
```

The callback runs on a background thread. The usual pattern is to **just store
the latest value** (a blackboard) and let your main loop read it each tick.

**`SyncLogger` (blocking iterator)** is fine for scripts and tests:

```python
from cflib.crazyflie.syncLogger import SyncLogger

with SyncLogger(scf, logconf) as logger:
    for timestamp, data, logconf_name in logger:   # blocks until next sample
        print(data)
        break
```

**Multi-ranger shortcut:** `cflib.utils.multiranger.Multiranger(scf)` sets up
the range logging for you and exposes `.front`, `.left` and so on, in **meters**,
or `None` when nothing is in range (≥ 8 m).

## 3. Parameters

Parameters are firmware settings you can read and write by name:

```python
scf.cf.param.set_value('kalman.resetEstimation', '1')
scf.cf.param.add_update_callback(group='deck', name='bcFlow2', cb=on_flow_deck)
```

The examples use the `deck.bcFlow2` parameter to **check that the Flow deck is
attached** before flying. Changes persist until the drone reboots.

## 4. Arming

**Current firmware requires the drone to be armed before it flies.** The
current examples do:

```python
scf.cf.supervisor.send_arming_request(True)
time.sleep(1.0)
```

The older `scf.cf.platform.send_arming_request(...)` still exists but is
**marked deprecated** in 0.1.34. `supervisor` (`crazyflie/supervisor.py`) also
gives you state flags (`is_armed`, `can_fly`, `is_flying`, `is_tumbled`,
`is_crashed`) and **`send_emergency_stop()`**, which cuts the motors. These
are useful for a safety layer.

## 5. Moving

cflib gives you three levels of control. In game terms, from "pathfind to a
point" down to "drive velocity every tick":

### a) `PositionHlCommander`: go to a point (blocking)

```python
from cflib.positioning.position_hl_commander import PositionHlCommander

with PositionHlCommander(scf, default_height=0.5, default_velocity=0.3) as pc:
    pc.go_to(1.0, 0.0)        # blocks until it should have arrived
    pc.go_to(1.0, 1.0)
# leaving the block lands
```

Two important details from the source (`positioning/position_hl_commander.py`):

- **`go_to` blocks** by calling `time.sleep(distance / velocity)`. Your code
  can't react to anything mid-move, so this doesn't fit a behavior tick loop.
- **`get_position()` returns where it was told to go, not where it is.** It
  returns the last commanded target. For the real position, log
  `stateEstimate.*`.

### b) `HighLevelCommander`: go to a point (non-blocking)

`scf.cf.high_level_commander` (`crazyflie/high_level_commander.py`) is what (a)
wraps. `takeoff(height, duration_s)`, `go_to(x, y, z, yaw, duration_s)`,
`land(height, duration_s)` and `stop()` all **return immediately**. The
firmware plans a smooth trajectory and flies it. Things to know:

- You give a **duration**, not a speed (`duration = distance / speed`).
- `yaw` is in **radians** here.
- The source warns: **don't send overlapping `go_to` commands**, or the drone
  may take unexpected paths. Wait for one to finish (or call `stop()`) before
  sending the next.
- `supervisor.hl_traj_finished` tells you when the trajectory is done.

This is the best match for "MoveTo(target)" actions in a behavior tree.

### c) `MotionCommander`: velocity control (steering)

```python
from cflib.positioning.motion_commander import MotionCommander

with MotionCommander(scf, default_height=0.5) as mc:     # takes off on enter
    mc.start_linear_motion(0.2, 0.0, 0.0)   # vx, vy, vz (m/s), returns immediately
    time.sleep(1)
    mc.stop()                               # hover in place
# lands on exit
```

- Velocities are **body frame**: +x forward, +y left, +z up, relative to where
  the drone faces.
- The `start_*` methods return immediately. The blocking ones (`forward(0.5)`,
  `turn_left(90)`) sleep until done.
- Internally a background thread resends the current velocity **every 0.2 s**
  (`_SetPointThread`), because the firmware treats silence as "link lost" and
  stops following. When you send low-level setpoints yourself, you must keep
  streaming them too.
- Taking off resets the position estimator, so **(0, 0) is wherever it took
  off**.

This is the natural fit for steering behaviors (seek, avoid, wander).

### d) Raw setpoints (lowest level)

`scf.cf.commander` (`crazyflie/commander.py`) has `send_hover_setpoint`,
`send_velocity_world_setpoint`, `send_position_setpoint` and others. These are
what (c) uses, and you must stream them continuously. `send_stop_setpoint()`
cuts the motors. Avoid this level unless (b) or (c) can't do what you need.

## Coordinate frame

Meters, with +x forward, +y left, +z up (a right-handed frame, **not** Unity's).
With only a Flow deck, the origin is the takeoff point and position slowly
**drifts** over a flight. Treat positions as approximate.

## What this means for our `Drone` interface

- Read state from **telemetry callbacks into a cached blackboard**, never from
  `PositionHlCommander.get_position()`.
- Use **non-blocking** commands (`HighLevelCommander` or `MotionCommander.start_*`)
  so the behavior loop keeps ticking and can react to obstacles mid-move.
- Use `with`-style setup and teardown so the drone **always lands**, even if the
  behavior code throws.
- Before takeoff: check the Flow deck is attached, then arm through `supervisor`.
- Keep `supervisor.send_emergency_stop()` within reach (for example, Ctrl+C →
  e-stop).
