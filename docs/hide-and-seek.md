# Hide-and-seek

The rules of the game ([ADR-0016](decisions/0016-first-game-hide-and-seek-drone-lands.md)).

## The idea

The drone hides and the player seeks. While the player waits, the drone flies
off, finds a spot behind a wall, lands and goes quiet. Then the player hunts for
it, and when they pick it up, the drone lights up and the computer plays a
fanfare.

## How to play

1. **Get ready:** the drone sits on the launch point. The player waits in the
   waiting area, behind the gate. An adult starts the round when the play area
   is clear.
2. **The drone hides:** it takes off, flies to a hiding spot with at least one
   wall between it and the launch point, lands, and turns its motors off.
3. **Seek:** the player goes looking for it. Every 15 s until it's found, the
   drone gives a hint: it flashes its lights and chirps.
4. **Found!** The player picks up the drone. It lights up and the computer plays
   a fanfare.
5. **Again:** the player brings the drone back to the launch point and returns
   to the waiting area, and the adult starts the next round.

The game has no end: play as many rounds as you like.

## What the drone does

| When | What it does |
|---|---|
| **Ready** | Sits still on the launch point |
| **Hiding** | Flies to its hiding spot, lands, and turns its motors off |
| **Hidden** | Waits with its motors off; every 15 s it flashes and chirps as a hint |
| **Found** | Lights its LEDs while the computer plays a fanfare |

## Later versions

- **Harder hiding spots:** two or more walls between the hiding spot and the
  launch point.
- **No mapping run:** the drone finds a hiding spot from scratch, with 30 s to
  hide.

## First-try settings

Starting values for the first playtests. Expect to tune all of them.

| Setting | First try |
|---|---|
| Mapping run | Up to 5 min, once before play |
| Walls between the hiding spot and the launch point | At least 1 |
| Hiding spot distance from the launch point | 2–5 m |
| Hiding spot distance from any wall | At least 0.3 m |
| Flying height while hiding | 0.5 m |
| Flying speed | 0.3 m/s |
| Time to hide | 15 s from takeoff to landing |
| What counts as found | The down reading rises above 0.2 m, or the drone tilts more than 30°, for at least 0.3 s |
| Hint | Every 15 s until found: the LEDs flash and the drone chirps for 1 s |
| Found reaction | LEDs flash for 5 s with the fanfare |
