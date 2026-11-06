# 0053: Buzzer commands go through the safety layer; the Hover test can chirp

- **Status:** Accepted. Amends [ADR-0050](0050-diagnostic-log-block-to-the-debug-log.md): the diagnostic block also carries the battery voltage.
- **Date:** 2026-11-06
- **Origin:** Mixed. Testing the buzzer in the hover (over the AI's recommendation of a floor test), the chirp schedule and the "Charge" fanfare at the end: mine. A chirp command in a buzzer command slot, the firmware's one-shot tune, 10 Hz voltage in the diagnostic block, an option that's off by default, and notes timed by the behavior's ticks: AI recommendations accepted. The "As built" choices (2026-11-06, while coding): AI recommendations accepted.

## Context

I want to see how the Buzzer deck sags and drains the battery
([ADR-0051](0051-battery-flight-limit-and-take-off-limit.md)), and the game
needs hint chirps anyway ([ADR-0017](0017-hint-chirps-from-buzzer-deck.md)).
The drone interface has no buzzer command, and only the safety layer sends
commands ([ADR-0008](0008-drone-interface.md)). The battery voltage arrives once a second in 5 mV steps,
so a 1 s chirp overlaps about one reading.

Checked in firmware 2026.08: the sound module plays through the Buzzer deck
only (`buzzdeck.c` sets the buzzer control in `buzzer.c`). `sound.effect`
indexes the effects table in `sound_cf2.c`: 4 is "charging done" (two
0.5 s notes, then it switches itself off), 12 a steady tone at `sound.freq`.
The parameter's doc comment numbers them wrongly (mistakes log, 2026-11-06).

## Options considered

- **Command:** a chirp command judged in a buzzer command slot, or the program
  writing the parameter through a wrapper (bypasses the safety layer).
- **Chirp:** the firmware's one-shot tune, or a steady tone the PC switches off.
- **Voltage:** add `pm.vbatMV` to the diagnostic block, or stay at 1 Hz.
- **Hover test:** an option, or change every Hover test.
- **End tune:** the firmware's Calibrated tune, or "Charge" played note by note.

## Decision

- **Three buzzer commands in the drone interface: chirp, tone (a pitch in
  Hz) and silence,** judged by the safety layer in the buzzer command slot
  ([ADR-0025](0025-safety-pre-check-and-command-slots.md)). A chirp is the
  one-shot tune (effect 4, about 1 s). A tone is the steady tone at a pitch
  until silence. Effect numbers and parameter names stay in the Crazyflie adapter.
- **The battery voltage at 10 Hz in the diagnostic block** (`pm.vbatMV`,
  2 bytes, 25 of 26), debug log only. The snapshot keeps the 1 Hz reading.
- **The hover program's `--chirp` option, off by default:** chirp on the
  floor, wait 5 s, take off; chirp every 5 s until the drone status says
  landed; 1 s later chirp; wait 5 s; play "Charge"; done.
- **"Charge"** (the bugle call): G4 C5 E5 G5 E5 G5, 150/150/150/300/150/600 ms,
  with the octave a constant. The Hover test behavior requests each note on
  its tick, then silence, so the adapter needs no timer. Placeholders: the
  lengths and the octave, tuned by ear.
- **As built (2026-11-06):**
  - The safety layer approves every chirp, tone and silence while the
    pre-check passes; after a failed one they're refused like every request. A
    tone's pitch must be 20 Hz-20 kHz, checked when the request is made (a
    bug otherwise, like a take-off height of 0).
  - The first chirp in flight comes 5 s after the take-off request, so it
    doesn't overlap the take-off's own sag.
  - After its silence, the Hover test waits 1 s before it's done: closing the
    link empties cflib's queue of parameter writes (`param.py`, cflib 0.1.34),
    so a silence sent on the last tick could be lost.
  - With the link closed, the Crazyflie adapter skips a buzzer write with a
    warning once per streak: cflib's parameter write then raises, because it
    forgets the parameter list, while a movement command is only dropped.
  - Connecting logs whether a Buzzer deck is attached (`deck.bcBuzzer`); it
    never fails the connect.

## Failure modes

- **Inputs:** a lost chirp is a missed chirp. A lost silence leaves the tone
  on until the next buzzer write or a power-off. The firmware's low-battery
  tune overrides ours while it plays.
- **Backups:** none needed: nothing in the buzzer path moves the drone.
- **Never:** a buzzer command reaching the drone without the safety layer.
- **Always eventually:** the buzzer goes silent (the chirp ends itself; a
  tone needs the silence to arrive). Not when the program ends during
  "Charge" (a stop request, an error, a failed pre-check): the tone stays on
  until power-off (backlog #59).

## Consequences

- **Risks I accept knowingly:** a lost silence leaves the tone on, with the
  drone landed and its motors off; radio delays make the notes a little
  uneven; a chirp's effect may still be too small to see.
- Each chirp and silence is one parameter write to the drone, and each note
  two (pitch, then effect): 13 for "Charge", 1 per 5 s for chirps. Backlog
  #47 (the drone's receive queue) applies.
- The first `--chirp` run also does ADR-0017's check: how loud the deck is
  under the Multi-ranger, and that the PC can start and stop a chirp.
- Code (drone interface, safety layer, Crazyflie and mock adapters, the
  Hover test behavior): Extra or Max effort, and a `/project-review`.
- Glossary: *Chirp* and *Tone* are new (proposed for my OK).
