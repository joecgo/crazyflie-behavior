# 0029: Connecting has time limits: each step waits on a helper thread

- **Status:** Accepted
- **Date:** 2026-10-30
- **Origin:** AI recommendation accepted, after I asked why the simpler option (time limits for two of the three waits) wasn't recommended.

## Context

Connecting to the Crazyflie has three cflib waits with no time limit
(backlog #29): opening the link, reading the parameters, and waiting for the
position estimate to settle. Each can wait forever: the link if it drops while
the drone's variable lists download, the estimate if it never settles. On
Windows, Python 3.12 can't interrupt such a wait, so Ctrl+C doesn't get
through either.

## Options considered

- **A. Each step on a helper thread**, with the main thread waiting in short
  slices and a time limit per step. cflib's code is used as it is.
- **B. Our own versions of cflib's three waits**, using its callbacks: no
  helper thread, but it copies part of cflib.
- **C. Our own versions of only the parameter and estimate waits:** simpler,
  but opening the link can still wait forever.
- **D. Leave it**, and close the window when connecting hangs.

## Decision

Option A.

- Each blocking step of connecting runs on its own helper thread. The main
  thread waits for it in 0.1 s slices, so Ctrl+C is noticed within 0.1 s,
  even on Windows. Closing the link afterwards can take a second or two more.
- **Time limits**, placeholders to measure at the bench (backlog #25): 15 s
  to open the link (a first connect, with nothing cached, downloads more),
  10 s for the parameters, 20 s for the position estimate (cflib needs at
  least 5 s).
- A step past its limit makes `connect()` close the link and raise
  `TimeoutError`, naming the step and what to check. The program refuses to
  start with that message (ADR-0020).

## Failure modes

- **Inputs:** with no drone answering, cflib fails at once and its own error
  passes through. A link that drops while connecting, or an estimate that
  never settles, is ended by the time limit. Ctrl+C is noticed within 0.1 s.
- **Backups:** the time limit is checked on the main thread, outside the
  cflib wait that may be stuck.
- **Never:** connecting waits forever; a failed connect leaves the radio
  claimed after the program exits.
- **Always eventually:** connected, or refused with a message, within the
  time limits.

## Consequences

- A helper thread stuck inside cflib can't be stopped, only abandoned. It
  doesn't keep the program alive, and an error it raises after being
  abandoned is still logged. It keeps its memory until the program exits,
  which only a program that reconnects again and again would notice.
- When opening the link is abandoned, the connection still under way is
  stopped. A Ctrl+C in the first moments of opening the link can come before
  cflib has a link to stop; that link then runs until the program exits,
  which it does after a refused connect, so the next run can connect.
- The time limits count on the injected clock (ADR-0009). The Crazyflie
  adapter only ever runs with the real clock; tests of the limits use it too.
- Ctrl+C while connecting now works on Windows too, which resolves
  ADR-0028's note.
- Backlog #29 is closed.
