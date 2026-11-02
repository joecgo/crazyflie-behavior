# Next up (after the weekly usage reset)

Committed (lives in docs/, not the ignored drafts/) so cloud scheduled
tasks can read it. The weekly limit resets 2026-11-03 at
11:59 AM Pacific.

1. **ADR-0037 C: the auto-arming log line.** Open the stopped session "Log
   whether the drone arms itself (ADR-0037 C)" and say "continue". Crazyflie
   adapter code, with a `/project-review` before committing. Extra, Opus.
2. **Build ADR-0038: connecting to a flying drone.** Decided 2026-11-02.
   The reordered `connect()`, the safe link close, `take_over_flight`, the
   rescue-landing program and the emergency-stop script. Crazyflie adapter
   code, with a `/project-review`. Before First flight. Extra, Opus.
3. **Backlog #8: "one definition: the adapter decides."** Already decided;
   add a floor check to the adapter's `hover()` like `land()`'s, and fix the
   failsafe's "no landing sent" wording. Due with the operator controls
   (ADR-0027), before the "hover" key is built. Extra, Opus.

Later (not urgent): a field-test list in `docs/field-testing/` with two
sections, **Hardware checks** (the `VERIFY` notes: firmware and cflib
assumptions, stages 0-1) and **Safety tests** (each designed failsafe tried
for real, stage 3, e.g. kill the program mid-hover and run the rescue
landing, ADR-0038). Also fix the README's stale "Open decision" (ADR-0034).
