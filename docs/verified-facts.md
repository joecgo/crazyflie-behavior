# Facts register

Each fact about cflib, the firmware, Python or Windows that the project
relies on, checked in source. A fact not in this table is checked before it's
said or written, then added. ADRs keep naming their own sources; this table
is the index across them.

- **Adding a row.** Source is the installed file and its lines
  (`.venv/Lib/site-packages/...`), the version is the one installed, and the
  date is when it was read. Say only what the source showed (REVIEW.md Q-02).
- **Upgrading a library or the firmware.** Re-check every row for it, and
  update the version and date, or the row and what relies on it.

| Fact | Source | Version | Checked | Relied on by |
|---|---|---|---|---|
| `Crazyflie.close_link()` sends a zero-thrust setpoint first when the link is open, then closes it, stops and replaces the incoming handler, and calls `disconnected`. | `cflib/crazyflie/__init__.py` 281-299 | cflib 0.1.34 | 2026-11-13 | ADR-0038; `drone/crazyflie/adapter.py` |
| `Crazyflie.send_packet()` sends nothing and raises nothing when `link is None`. | `cflib/crazyflie/__init__.py` 349-392 | cflib 0.1.34 | 2026-11-13 | `drone/crazyflie/adapter.py` |
| The incoming handler catches `Exception` from each callback, logs it at error level through cflib's logger, and keeps running. A callback that always raises logs one error per packet. | `cflib/crazyflie/__init__.py` 449-481 | cflib 0.1.34 | 2026-11-13 | `drone/crazyflie/adapter.py` |
| `LogConfig.start()`, `stop()` and `delete()` do nothing when `cf.link is None`. `start()` on a block not yet added calls `create()`. | `cflib/crazyflie/log.py` 292-330 | cflib 0.1.34 | 2026-11-13 | `drone/crazyflie/adapter.py` |
| `SyncCrazyflie.close_link()` waits for an event with no time limit. | `cflib/crazyflie/syncCrazyflie.py` 123-129 | cflib 0.1.34 | 2026-11-13 | `drone/crazyflie/adapter.py` |
| `Param.set_value()` raises `KeyError` for a name that isn't in the TOC and `AttributeError` for a read-only one. | `cflib/crazyflie/param.py` 339-358 | cflib 0.1.34 | 2026-11-13 | `drone/crazyflie/adapter.py` |
| On a link error, `Crazyflie._link_error_cb` sets `link = None`, then calls `disconnected` and `connection_lost`. The radio driver calls it from its own thread and also from `send_packet`, so it can run on the caller's thread. | `cflib/crazyflie/__init__.py` 213-227; `cflib/crtp/radiodriver.py` 371, 604, 619 | cflib 0.1.34 | 2026-11-13 | `drone/crazyflie/adapter.py` |
| `HighLevelCommander` has `stop()`, `go_to(x, y, z, yaw, duration_s, relative=False, linear=False)` and `land(absolute_height_m, duration_s, group_mask, yaw=0.0)`. | `cflib/crazyflie/high_level_commander.py` 108-145 | cflib 0.1.34 | 2026-11-13 | `drone/crazyflie/adapter.py` |
| `Commander` has `send_notify_setpoint_stop(remain_valid_milliseconds=0)` and `send_stop_setpoint()`. | `cflib/crazyflie/commander.py` 99-118 | cflib 0.1.34 | 2026-11-13 | `drone/crazyflie/adapter.py` |
| `QueueHandler.prepare()` formats the message on the calling thread and queues a copy. `QueueListener`'s thread is a daemon. `QueueListener.stop()` joins it with no time limit. `respect_handler_level` exists. | `logging/handlers.py`, read with `inspect.getsource` | Python 3.12.10 | 2026-11-13 | nothing yet |
