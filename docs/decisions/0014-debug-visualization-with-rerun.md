# 0014: Debug visualization uses Rerun

- **Status:** Accepted
- **Date:** 2026-10-20
- **Origin:** Mixed. Using an off-the-shelf robotics tool now, and building a custom editor only if a real need appears: my call. Rerun specifically: AI recommendation accepted.

## Context

To confirm things work, I need to see what the drone "thinks": its position
estimate, range readings, the map, and later the tracked player and
hiding-spot scores. It's the robotics version of UE's Gameplay Debugger or EQS
debug view, and it's needed from the first behavior on.

## Options considered

- **A. Rerun:** a Python SDK plus a viewer for 3D data and values over time,
  with a timeline to scrub through and recordings to replay. Quick to integrate
  and widely used in robotics. Pre-1.0, so its API still changes.
- **B. Foxglove:** strong robotics visualizer, but built around ROS-style data.
- **C. RViz:** the ROS standard; needs ROS 2, so Linux or WSL2. Heavy.
- **D. A UE project (digital twin):** a showcase for my UE skills, but more
  plumbing and a frame conversion (UE is left-handed, in centimeters).
- **E. My own editor:** the most custom, and the most work.

## Decision

Option A. I'm not familiar with robotics visualization tools, and Rerun gets
results fastest with the least plumbing. A UE project or my own editor can come
later if something custom is really needed.

## Consequences

- `rerun-sdk` becomes a pinned dependency when the first visualization is
  built, with the vertical slice.
- Visualization only observes: it reads snapshots and logs, never commands the
  drone. Tests and continuous integration run without it.
- Rerun supports a right-handed, z-up world, matching ours, so no frame
  conversion is needed.
- Its recordings could double as a way to view recorded flights (backlog:
  recorded flight data).
