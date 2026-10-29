# 0027: Operator controls: Windows hotkeys, an optional PS5 controller, no dead-man mode

- **Status:** Accepted
- **Date:** 2026-10-29
- **Origin:** Mixed. Keys that work in any window plus an optional PS5 controller, landing when a controller in use disconnects, and no dead-man mode (a drop can damage the battery, a fire hazard): mine, the last one overriding the AI's recommendation. Windows hotkeys rather than a keyboard hook, "land now" through the safety pre-check, the kill latch and the `tools/` script: AI recommendations accepted.

## Context

ADR-0013 made the kill switch cut the motors directly, on its own thread. It
left open how I give commands during a flight, what a kill leaves behind, and
whether the first flights need a dead-man switch. Ctrl+C is only a fallback
(ADR-0026): in PyCharm's Run window it copies text.

## Options considered

- **Input:** keys read in the console window (lost when another window has
  focus); a keyboard hook such as pynput (any window, but Windows silently
  removes a hook that answers too slowly, for example at a breakpoint);
  Windows global hotkeys (any window and can't be lost that way, but each
  registered combination is taken from other apps while the program runs);
  a gamepad.
- **"Land now" and "hover":** inputs to the safety layer, or command requests
  that a behavior's later request could replace (ADR-0025).
- **Dead-man mode for the first flights:** the motors run only while a
  trigger is held, backed by the firmware's 1 s emergency-stop watchdog.

## Decision

- **Windows global hotkeys** (`RegisterHotKey`, no new library) are always
  available. They use key combinations, so a stray key press can't set them off.
- **An optional PS5 controller, through pygame** (its SDL library reads it
  over USB or Bluetooth). If a controller in use disconnects, the drone lands
  now.
- **"Land now" and "hover" are inputs to the safety layer.** They fail the
  safety pre-check, so behaviors are skipped and the failsafe lands or hovers.
  No behavior can override them.
- **The kill switch** (ADR-0013) uses a deliberate combination. After a kill,
  the **kill latch** refuses to arm or take off until the program restarts,
  backing up the **drone lock** (the firmware's "Locked, reboot required").
- **No dead-man mode.** An accidental release would drop the drone, and a
  drop can damage the LiPo battery, which is a fire hazard.
- **A `tools/` emergency-stop script**, for when the main program has exited.

## Failure modes

- **Inputs:** hotkeys work whatever window has focus. A combination another
  app already holds can't be registered, so the program refuses to start. A
  controller can disconnect: over a cable that's noticed at once, over
  Bluetooth after a delay still to be measured.
- **Backups:** the hotkeys and the controller share no hardware. Every command
  shares the radio, though: during radio trouble any send, the kill included,
  can wait up to 2 s (cflib), and with the link gone no PC control reaches the
  drone (backlog #26). The `tools/` script needs the radio free, so it only
  helps once the main program has exited.
- **Never:** a stray press drops the drone; a lost controller goes unnoticed;
  a flight after a kill without a restart.
- **Always eventually:** "land now" ends landed with the motors off; a kill
  ends with the motors off and the drone locked.

## Consequences

- The kill switch drops the drone too, so it's a deliberate combination, and
  "land now" is the normal way to stop.
- pygame is a new dependency, used only for the controller; a fitness
  function keeps it in one module, as for cflib. The hotkey code is Windows
  only. Tests and continuous integration use fakes for both.
- Key combinations and controller buttons: proposed with the implementation.
- Before the first flight: check what PyCharm's Stop button does, with the
  mock adapter (it may skip the landing), and measure how long Windows takes
  to notice a Bluetooth controller dropping out.
- Backlog #9 is closed.
- Glossary: *Drone lock* and *Kill latch*.
