# 0015: The first game is Catch the bird

- **Status:** Accepted. Replaces hide-and-seek as the project's goal. The first-game choice is superseded by [ADR-0016](0016-first-game-hide-and-seek-drone-lands.md): Catch the bird becomes the second game, and its design here still stands.
- **Date:** 2026-10-20
- **Origin:** Mixed. Dropping hide-and-seek for safety, and using a toddler's height so the drone always flies out of reach: my ideas. The Catch the bird game: an AI suggestion I chose.

## Context

In hide-and-seek the drone hides, so its sensors can't see the player coming.
Distance alone (UWB) doesn't say *where from*, so any escape could fly into the
player; even escaping straight up can hit a child leaning over the couch. The
game has to be safe by design, interactive enough for a toddler, let the drone
do what drones do best (fly), and work with the cheapest hardware: the Flow and
Multi-ranger decks.

## Options considered

- **A. Hide-and-seek:** the drone can't tell where the player comes from;
  escaping risks a collision. Rejected.
- **B. Peek-a-boo in an arena, triggered by a button:** safe by a physical
  barrier, but less flying.
- **C. Obstacle course:** build, then watch: not interactive enough.
- **D. Catch the bird:** the drone flies like a bird in a "sky layer" above a
  child's reach; the child chases it and scores a catch by getting underneath.
- **E. Race the drone, Simon the drone:** good later candidates.

## Decision

Option D. The drone never comes to the child: it stays above reach, and the
child does the chasing. The down sensor measures what's directly below, so the
drone knows exactly where the danger is and can always move away sideways. A
timed round with a score and rising difficulty makes it a game, not just a
playful interaction.

## Consequences

- **Sky layer:** roughly 1.5 to 2.0 m in a room with a 2.4 m ceiling: above a
  toddler's reach, below the ceiling with a margin.
- **Clearance rule:** always keep about 1 m of clearance below; if something
  rises toward the drone, move away sideways.
- **Catch:** the down reading drops when the child is underneath; the bird
  reacts (sound from the PC, a wiggle) and flies to a new spot.
- **Hardware:** the Flow and Multi-ranger decks are enough (the STEM ranging
  bundle). UWB isn't needed for this game.
- **Risks accepted knowingly:** safety rests on rules and sensing, not a
  physical barrier. Climbing on furniture, adults standing up (the drone flies
  at adult face height), a failing drone falling, thrown toys, and a child
  tripping while looking up. Mitigations: keep away from furniture, adults sit
  while it plays, prop guards, slow speeds, a landing pad for failsafes, a clear
  floor, ceiling fans off, and testing with stand-ins before any child plays.
- Hide-and-seek, camera-free approach sensing and UWB player tracking are
  parked in the backlog.
