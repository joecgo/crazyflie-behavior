# 0016: The first game is hide-and-seek, where the drone hides and lands

- **Status:** Accepted. Supersedes the first-game choice in [ADR-0015](0015-first-game-catch-the-bird.md): Catch the bird becomes the second game.
- **Date:** 2026-10-21
- **Origin:** My idea: the game (an adult starts each round when the play area is clear, motors off while hidden, a reaction when found), the mapping run before play, the safety gate, and the launch point as a stand-in for the waiting area.

## Context

ADR-0015 dropped the original hide-and-seek because a hiding drone can't see
the player coming, so any escape could fly into the child. A new version
removes that problem: the drone flies only while the play area is empty, and
its motors are off before the player starts searching. It brings back the game
I wanted first.

## Options considered

- **A. Catch the bird first:** a child is near a flying drone the whole round,
  drift builds up over a 60 s round, and a battery lasts one or two rounds.
- **B. Hide-and-seek with a landed drone first:** a child is never near a
  flying drone; short flights from a known start, so drift resets each round;
  long play per battery, since the drone sits with its motors off while hidden.
  The hard part is finding a spot behind a wall.

## Decision

Option B. A round:

1. The player waits in the waiting area, right behind the launch point, with a
   safety gate between it and the play area. An adult starts the round only when
   the play area is clear.
2. The drone takes off from the launch point, flies to a hiding spot on the
   floor with at least one wall between it and the launch point, lands, and
   stops its motors.
3. The player searches. Picking the drone up is **found**: the down reading
   jumps and the motion sensors spike. The drone lights its LEDs and the PC
   plays a fanfare.
4. The player brings the drone back to the launch point. The game has no end.

**A mapping run first.** Ten seconds isn't enough to find a wall from scratch,
so before play the drone makes a mapping run of up to 5 minutes with the play
area clear, and every hiding flight uses that map. If mapping gets fast enough,
try a version with no mapping run and a 30 s hiding flight.

**The motors never restart in a child's hands.** After landing the drone
disarms. It re-arms only when the adult starts a round with the drone back on
the launch point, never automatically.

## Consequences

- **Safety by structure:** the player and a flying drone are never in the play
  area together. That rests on the adult's check and the gate, not on sensing.
- **LEDs checked against the firmware source (2026-10-21):** the onboard LEDs
  (red, green and blue, left and right) are set by the `led.bitmask` parameter;
  bit 7 overrides the firmware's own LED patterns. No extra deck needed. Check on
  the drone that its firmware has the parameter and the LEDs show under the decks.
- **The position estimate is reset on the launch point before each round:** it
  is meaningless after the drone has been carried around.
- **Hardware:** the Flow and Multi-ranger decks, plus a Buzzer deck for hints
  ([ADR-0017](0017-hint-chirps-from-buzzer-deck.md)). No UWB or webcam needed.
- **Risks I accept knowingly:**
  - A 5-minute mapping run uses most of a battery (about 7 minutes of flight
    without decks, less with them).
  - The map lines up only if every round starts on the same launch point, facing
    the same way: a 5° heading error moves a wall 4 m away by about 35 cm. The
    launch point needs a marked pad that fixes the heading.
  - Drift during the mapping run places walls seen late less accurately, so
    hiding flights keep a margin from walls.
  - A spot hidden from the launch point may still be visible from the side of
    the waiting area.
  - The map goes stale when furniture moves or doors change; then map again.
  - A young child handles the drone. Its propellers press onto the motor
    shafts and can come off, a choking risk, so play is supervised.
- Glossary terms, in a new Hide-and-seek section: *Launch point*, *Waiting
  area*, *Play area*, *Mapping run*, *Hiding spot*, *Found*.
- Open questions (mapping, choosing hiding spots, found detection, re-arming,
  a response when someone enters the play area) are in the
  [decision backlog](../decision-backlog.md).
