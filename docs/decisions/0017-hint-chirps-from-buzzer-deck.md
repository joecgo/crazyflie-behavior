# 0017: Hint chirps come from a Buzzer deck, not the motors

- **Status:** Accepted
- **Date:** 2026-10-21
- **Origin:** Mixed. Hints every 15 s, with sound as well as lights: my idea. The Buzzer deck instead of motor tones: AI recommendation accepted.

## Context

In hide-and-seek ([ADR-0016](0016-first-game-hide-and-seek-drone-lands.md)),
the hidden drone gives a hint every 15 s until it's found. The LEDs alone are a
weak hint, and the PC's sounds come from the waiting area, not the hiding spot.
The chirp has to come from the drone.

## Options considered

- **A. Motor tones:** the firmware can play tones through the motors (its
  power-on tune), but no parameter lets the PC trigger one, so it needs custom
  firmware. It also powers the motors while a child may be reaching for the
  drone, which breaks ADR-0016's rule that the motors never restart in a child's
  hands, and the tone bypasses arming.
- **B. Buzzer deck:** a small piezo buzzer (1.8 g) that the PC controls through
  the stock firmware's `sound` parameters. No moving parts.

## Decision

Option B. It keeps the motor rule intact and works with the stock firmware.

## Consequences

- **Checked against the firmware source (2026-10-21):** the Buzzer deck's
  driver uses TIMER5 and UART2; the Flow deck uses I2C, SPI and IO_3, and the
  Multi-ranger I2C, so they don't conflict. `sound.effect` picks a built-in
  effect, and `sound.freq` sets the tone of the steady "bypass" effect. New
  melodies need firmware changes.
- **Three decks need longer pins** (Long Pins 19+2+4 mm): two decks on top (the
  Buzzer deck under the Multi-ranger), the Flow deck underneath.
- A little less flight time from the extra weight.
- Glossary terms: *Buzzer deck*, *Hint*.
- Check on the drone: how loud it is under the Multi-ranger, and that the PC can
  start and stop a short chirp.
