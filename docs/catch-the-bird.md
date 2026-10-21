# Catch the bird

The rules of the game ([ADR-0015](decisions/0015-first-game-catch-the-bird.md)).

## The idea

The drone is a bird. It flies around the room, always above the player's reach,
and stops to rest. The player chases it, and when they get right underneath it,
that's a **catch**: the bird wiggles and chirps, then flies off to a new spot,
a little faster each time.

## How to play

1. **Start:** a round begins. The bird takes off from its nest and rises to its
   flying height.
2. **The bird rests:** it flies to a spot, hovers there and sings, so the player
   knows where it is.
3. **Catch!** The player runs underneath the bird. The bird sees them below,
   wiggles, chirps happily, and the player scores a point.
4. **Fly away:** the bird flies to a new resting spot. After each catch it
   rests a little less and flies a little faster.
5. **Bonus:** every 5 catches, the bird does a celebration dance.
6. **End of the round:** when time is up, the bird does a final celebration,
   announces the score, and flies home to its nest to land.

## Difficulty

- **It gets harder** with each catch: shorter rests and faster flights.
- **It helps a player who's struggling:** if a catch takes a long time, the
  bird slows back down and rests longer, so the game stays fun and the player
  wins often.

## The bird's moods

| Mood | What it does |
|---|---|
| **Resting** | Hovers gently with a little bob and sings |
| **Caught** | A happy wiggle and chirp |
| **Flying off** | Darts to its next spot |
| **Celebrating** | A little dance (every 5 catches, and at the end) |
| **Tired** (round over, or low battery) | A sleepy sound, then flies home to its nest and lands |

## First-try settings

Starting values for the first playtests. Expect to tune all of them.

| Setting | First try |
|---|---|
| Round length | 60 s |
| Flying height | 1.7 m |
| Next resting spot | 1–2 m from the last one |
| Rest time | Starts at 6 s; 0.5 s shorter per catch; never under 2 s |
| Flying speed | Starts at 0.3 m/s; +0.05 m/s per catch; never over 0.6 m/s |
| What counts as a catch | The down reading drops by 0.5 m or more (something tall underneath) for at least 0.3 s |
| After a catch | 2 s of wiggling before the bird flies off; no new catch counts during it |
| Helping a struggling player | No catch for 15 s: back to the starting speed, and 2 s more rest |
| Celebration | Every 5 catches |
