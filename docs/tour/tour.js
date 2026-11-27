// The project tour's shared script: the depth switch, glossary pop-overs, clickable figures,
// and the adapter chapter's two animations. No libraries, no build step.
(function () {
  "use strict";

  // Definitions copied from docs/glossary.md at the pinned commit, link markup removed.
  const TERMS = {
    "Project tour": "An interactive guide that walks a reader through the project: what's interesting and unique about it, and how it's designed to be easy to understand and change. Each claim links to its evidence in the repository (an ADR, a test, a flight log or a doc).",
    "Chapter": "One page of the project tour, on one part of the project, such as the Crazyflie adapter.",
    "Crazyflie adapter": "Adapter that talks to a physical Crazyflie through cflib: the drone/crazyflie/ package, the only code in src/ allowed to import cflib. Inside it, only its adapter, link, log-block and command modules do; a fitness function checks it.",
    "cflib": "Bitcraze's official Python library for talking to the Crazyflie.",
    "Crazyradio": "USB radio dongle the PC uses to talk to the Crazyflie.",
    "Firmware": "Code running on the drone itself: stabilization, estimation, motor control at about 1 kHz.",
    "Behavior": "Decision-making logic that turns sensed state into commands. Never imports cflib.",
    "Safety layer": "The layer between behaviors and the drone interface. It runs the safety pre-check on each snapshot, answers command requests at once, and is the only code that sends commands to the drone, apart from the kill switch (ADR-0013) and the forged low battery drone, which only passes them on (ADR-0041): it approves, clamps to the speed envelope, or overrides command requests.",
    "Safety pre-check": "The safety layer's check of each snapshot at the start of the tick, before behaviors run (missing or stale values, a value that isn't finite, low battery, a crash or tumble the drone reports, too much velocity uncertainty while the drone may be flying, outside the initial climb; a geofence later). If it passes, behaviors run and their requests are judged against it; if it fails, behaviors are skipped and the failsafe takes over.",
    "Drone interface": "The abstraction behavior code uses to sense and command a drone, with no knowledge of cflib.",
    "CRTP": "The packet protocol between PC and drone. Everything in cflib is built on it.",
    "High-level commander": "Firmware feature that plans a smooth trajectory to a goal on the drone itself (takeoff, go_to, land).",
    "Part": "One of the smaller classes a large class is split into in a refactor, each in its own module and owned by the class it came from. The Crazyflie adapter's parts are an example (LogBlocks, CrazyflieCommands, ADR-0093): connect() builds each one afresh, so none carries state from an earlier link.",
    "Log block": "A cflib LogConfig: a named group of variables streamed at a fixed period (max 26 bytes per block).",
    "Telemetry buffer": "Thread-safe store of the latest value of each telemetry variable, written in the background as data arrives (by the Crazyflie adapter, or by the mock or simulator).",
    "Setpoint stream": "Sending low-level setpoints continuously (≥ every few hundred ms). If they stop, the firmware stops following.",
    "Link": "An open connection to one drone.",
    "Initial climb": "The first part of every take-off: a level climb through the bad-flow zone that ends at the final descent height. If the velocity uncertainty there shows flow, a high-level move climbs to the target; without flow, or if the climb hasn't ended within a time limit, the drone lands. Land, the motor stop, arm and buzzer commands go through; the rest are ignored. It can start without flow, in low light; the safety pre-check doesn't check the velocity uncertainty during it.",
    "May be flying": "An adapter's judgment of whether the drone could be in the air, so that stopping it needs a landing, not a motor stop. Every snapshot carries it, and the safety pre-check checks the velocity uncertainty only while it's true. In the Crazyflie adapter: not flying if our code hasn't started or taken over a flight since our last motor stop was sent. Otherwise flying, unless a drone status that isn't stale says not flying and the take-off grace is over. In the mock adapter, it always matches the mock's drone status, which has no delay.",
    "Landing phase": "Where a landing is: not landing, the landing approach, or the final descent. The Crazyflie adapter holds it.",
    "Bad-flow zone": "The heights just above the floor where the Flow deck's flow can't be trusted, so the estimated horizontal speed and position go wrong. It reaches at least 0.1 m in any light (the firmware's flow model), higher in dim light. Take-off and landing cross it level (ADR-0048).",
    "Fitness function": "A test that enforces a structural rule from an ADR, such as \"only the Crazyflie adapter imports cflib\". It reads the code, for example its imports, instead of running it, and fails continuous integration when the rule is broken. Fitness functions live in tests/architecture/.",
    "Import scanner": "The fitness functions' reader of a source file's import statements, without running it: the modules each import and from names, relative imports resolved (ADR-0002).",
    "Import follower": "The fitness functions' reader that follows a file's imports through src/, file by file, to every file importing it may run, imports inside functions and for type checking only included. It shows whether take-off and landing reaches cflib through another module (ADR-0093).",
    "Comment scanner": "The fitness functions' reader of a source file's comments: it finds each # pyright: or # type: ignore comment, the comments that can change what pyright checks (ADR-0093).",
    "Telemetry": "Data streamed from the drone to the PC.",
    "Tick": "One iteration of the behavior update loop.",
    "Snapshot": "Read-only copy of the telemetry buffer, taken at the start of each tick. Every behavior in that tick sees the same snapshot. Each value carries its arrival time (PC clock) and the drone's timestamp. Its time is read after the copy, so no value in it arrived later than that time.",
    "Stale value": "A stamped value older than its age limit, so too old to trust. Every check uses one limit, STALE_AFTER in the drone interface, except the battery voltage's BATTERY_STALE_AFTER. A stale value stays in the snapshot until a newer one arrives. The opposite is fresh.",
    "State block": "The Crazyflie adapter's log block that carries the position estimate, velocity estimate and drone status together (6 floats and a 2-byte bitfield: the full 26 bytes), so all three come from the same moment (ADR-0021).",
    "Drone status": "Flags describing the drone's state as the drone reports it: armed, flying, crashed, tumbled, can arm, locked. Part of the snapshot. Its \"flying\" lags: it shows a take-off a little late and keeps saying flying for 2 s after the motors stop. \"Locked\" is the Crazyflie's term: the drone refuses to arm until it's power cycled.",
    "Stamped value": "A telemetry value together with its arrival time (PC clock) and the drone's timestamp (converted to seconds). Every value in a snapshot is stamped, so its age can always be checked.",
    "Streak": "An unbroken run of the same condition, counted in whatever repeats (ticks, command requests, state packets). It ends the first time the condition doesn't hold. A warning comes once per streak, so a long fault logs once, not every tick.",
    "Flow deck": "Deck with a downward optical-flow camera and height sensor. Needed to hold position.",
    "Level setpoint": "A low-level setpoint that holds roll and pitch at 0 and sets only a vertical speed (the firmware's altHold type). The initial climb and the final descent stream them (ADR-0048).",
    "Touchdown": "The drone resting on the floor, confirmed by the down range, or assumed when the final descent's time limit runs out. Then the motors stop.",
    "Transcript test": "A test that flies a scripted flight against a fake cflib (a stand-in for cflib's Crazyflie object that records each call the adapter makes instead of sending it to the drone) and compares that list of calls, in order, with a stored one. It fails when a change reorders or alters one of those sends, which the setpoint priority depends on. A send no flight reaches needs its own test.",
    "Final descent height": "The down range where the final descent starts and the initial climb ends: a fixed height just above the bad-flow zone, the same for every take-off and landing. Take-off targets must be above it.",
    "Hand-over": "A high-level move taking over from a setpoint stream: a level stream's last setpoint, the move, then the setpoint priority's release. The initial climb ends with one at the final descent height, made only with flow; without flow the drone lands.",
    "Velocity uncertainty": "How far off the estimator thinks its horizontal velocity estimate may be: its standard deviation in meters per second, the larger of the drone's forward and sideways directions (kalman.varPX, varPY). It grows while the estimator gets no flow and stays small while flow arrives, even wrong flow.",
    "Landing approach": "The first landing phase: a high-level move straight down at the estimated position, aimed 5 cm below the final descent height. The final descent starts when the down range reaches that height, or at a backup time if it never does. Skipped when a landing is requested during the initial climb: the final descent starts at once. Was called the planned landing.",
    "Final descent": "The last part of every landing, after the landing approach (none for a landing during the initial climb): a level descent through the bad-flow zone from the final descent height, until the down range confirms touchdown or a time limit says the drone must be on the floor. Then the motors stop. With no usable down range, a slow high-level descent instead. Land, the motor stop, arm and buzzer commands go through; the rest are ignored.",
    "Touchdown hold": "How long the down range must stay at or below the touchdown threshold before touchdown is confirmed, so one noisy reading can't confirm it. A higher, missing or stale reading starts it over.",
    "Drift": "Slow, growing error in the state estimate over a flight (flow deck has no absolute reference).",
    "Setpoint priority": "The firmware follows one source of setpoints at a time, and a setpoint stream outranks the high-level commander. After a stream, the adapter releases the priority so the high-level commander is followed again; until then the drone refuses its setpoints (ADR-0058).",
  };

  const SVG = "http://www.w3.org/2000/svg";
  const reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // The code's numbers at the pinned commit, which tools/tour_numbers.py writes into the page.
  const NUMBERS = readNumbers();
  function readNumbers() {
    const node = document.getElementById("tour-numbers");
    return node ? JSON.parse(node.textContent) : { constants: {}, formulas: {}, adrs: {} };
  }
  function constant(name) {
    const found = NUMBERS.constants[name];
    if (!found) throw new Error("The page's tour-numbers has no " + name + ": add it to tools/tour_numbers.py");
    return found;
  }
  function value(name) { return constant(name).value; }
  function text(name) { return constant(name).text; }

  function el(tag, attrs, parent, text) {
    const node = document.createElementNS(SVG, tag);
    for (const key in attrs) node.setAttribute(key, attrs[key]);
    if (text !== undefined) node.textContent = text;
    if (parent) parent.appendChild(node);
    return node;
  }
  function fmt(x, digits) { return x.toFixed(digits === undefined ? 2 : digits); }
  function store(key, value) { try { localStorage.setItem(key, value); } catch (e) { /* storage may be blocked */ } }
  function recall(key) { try { return localStorage.getItem(key); } catch (e) { return null; } }
  function onActivate(node, handler) {
    node.addEventListener("click", handler);
    node.addEventListener("keydown", function (event) {
      if (event.key === "Enter" || event.key === " ") { event.preventDefault(); handler(event); }
    });
  }

  // --- The depth switch: summaries only, or every drop-down open -----------------------
  function setupDepth() {
    const tour = document.getElementById("depth-tour");
    const all = document.getElementById("depth-all");
    if (!tour || !all) return;
    function apply(mode, save) {
      const open = mode === "all";
      document.querySelectorAll("main details").forEach(function (d) { d.open = open; });
      tour.setAttribute("aria-pressed", String(!open));
      all.setAttribute("aria-pressed", String(open));
      if (save) store("tour-depth", mode);
    }
    tour.addEventListener("click", function () { apply("tour", true); });
    all.addEventListener("click", function () { apply("all", true); });
    if (recall("tour-depth") === "all") apply("all", false);
  }

  // --- Pop-overs: glossary terms, and numbers from the code ------------------------------
  const POPS = ".term, .from-code";
  function newTabLink(href, label) {
    const a = document.createElement("a");
    a.href = href;
    a.target = "_blank";
    a.rel = "noopener";
    a.textContent = label;
    return a;
  }
  function popTitle(label, isCode) {
    const title = document.createElement("b");
    if (isCode) {
      const code = document.createElement("code");
      code.textContent = label;
      title.appendChild(code);
    } else {
      title.textContent = label;
    }
    return title;
  }
  function popNote(className, parts) {
    const note = document.createElement("span");
    note.className = className;
    note.append.apply(note, parts);
    return note;
  }
  // A docstring's text, with each ADR it cites as a link.
  function cited(description) {
    return description.split(/(ADR-\d{4})/).map(function (part) {
      return NUMBERS.adrs[part] ? newTabLink(NUMBERS.adrs[part], part) : document.createTextNode(part);
    });
  }
  function popContent(node) {
    const term = node.getAttribute("data-term");
    if (term !== null) {
      if (!TERMS[term]) return null;
      return [popTitle(term, false), document.createTextNode(TERMS[term]), popNote("from", ["From the project's glossary"])];
    }
    const name = node.getAttribute("data-const");
    const found = name !== null ? NUMBERS.constants[name] : null;
    if (found) {
      return [popTitle(found.code, true)].concat(cited(found.description), [
        popNote("from", ["From the code: ", newTabLink(found.url, found.label)]),
      ]);
    }
    // A pop-up written on the page itself, for a word that isn't a glossary term.
    const title = node.getAttribute("data-pop-title");
    if (title !== null) {
      return [popTitle(title, false), document.createTextNode(node.getAttribute("data-pop-text") || ""),
        popNote("from", [node.getAttribute("data-pop-from") || ""])];
    }
    const key = node.getAttribute("data-formula");
    const formula = key !== null ? NUMBERS.formulas[key] : null;
    if (formula) {
      return [
        popTitle(formula.formula, true),
        document.createTextNode(formula.description),
        popNote("worked", [formula.worked + " = " + formula.text]),
        popNote("from", ["Worked out from the code's numbers"]),
      ];
    }
    return null;
  }
  function setupTerms() {
    const pop = document.getElementById("term-pop");
    if (!pop) return;
    let pinned = null;
    function show(node) {
      const content = popContent(node);
      if (!content) return;
      pop.textContent = "";
      pop.append.apply(pop, content);
      pop.hidden = false;
      const rect = node.getBoundingClientRect();
      const width = pop.offsetWidth;
      const left = Math.max(16, Math.min(rect.left + window.scrollX, window.scrollX + document.documentElement.clientWidth - width - 16));
      pop.style.left = left + "px";
      pop.style.top = rect.bottom + window.scrollY + 8 + "px";
    }
    function hide() { pop.hidden = true; pinned = null; }
    document.addEventListener("mouseover", function (event) {
      const node = event.target.closest && event.target.closest(POPS);
      if (node && !pinned) show(node);
    });
    document.addEventListener("mouseout", function (event) {
      const node = event.target.closest && event.target.closest(POPS);
      if (node && !pinned) hide();
    });
    document.addEventListener("focusin", function (event) {
      if (event.target.matches && event.target.matches(POPS)) show(event.target);
    });
    document.addEventListener("focusout", function (event) {
      if (event.target.matches && event.target.matches(POPS) && !pinned) hide();
    });
    document.addEventListener("click", function (event) {
      const node = event.target.closest && event.target.closest(POPS);
      if (node) {
        event.preventDefault();
        if (pinned === node) { hide(); return; }
        show(node);
        pinned = node;
      } else if (pinned && !pop.contains(event.target)) {
        hide();
      }
    });
    document.addEventListener("keydown", function (event) { if (event.key === "Escape") hide(); });
    window.addEventListener("resize", hide);
  }

  // --- Click-to-select figures: the layers, the modules, the failure branches ---------
  function setupSelect(itemSelector, keyAttr, cardSelector, onPick) {
    const items = document.querySelectorAll(itemSelector);
    items.forEach(function (item) {
      onActivate(item, function () {
        const key = item.getAttribute(keyAttr);
        items.forEach(function (other) {
          const on = other === item;
          other.classList.toggle("sel", on);
          if (other.tagName === "BUTTON") other.setAttribute("aria-pressed", String(on));
        });
        document.querySelectorAll(cardSelector).forEach(function (card) {
          card.hidden = card.getAttribute("data-for") !== key;
        });
        if (onPick) onPick(key);
      });
    });
  }

  // --- Section 3: two threads, one lock --------------------------------------------------
  // The code's numbers come from the page. The window, the lost packets and where each stream starts are
  // chosen for the drawing.
  const WINDOW = 1.2;
  const GAP = [0.45, 0.85];
  function timelineNumbers() {
    const stale = value("STALE_AFTER");
    function stream(key, label, periodName, phase, color) {
      return { key: key, label: label, sub: "every " + text(periodName), period: value(periodName) / 1000, phase: phase, color: color };
    }
    return {
      tick: 1 / value("TICK_RATE"),
      streams: [
        stream("state", "State block", "STATE_PERIOD_MS", 0.004, "var(--s-state)"),
        stream("down", "Down range block", "DOWN_RANGE_PERIOD_MS", 0.013, "var(--s-down)"),
        stream("ranger", "Multi-ranger", "MULTIRANGER_PERIOD_MS", 0.037, "var(--s-ranger)"),
        stream("battery", "Battery", "BATTERY_PERIOD_MS", 0.42, "var(--s-battery)"),
      ],
      values: [
        // `checked` tags what the safety pre-check checks (safety_layer.py 94-100 and, in flight, 139-163).
        { name: "position estimate", stream: "state", limit: stale, checked: "pre-check" },
        { name: "velocity estimate", stream: "state", limit: stale, checked: "" },
        { name: "drone status", stream: "state", limit: stale, checked: "pre-check" },
        { name: "down range", stream: "down", limit: stale, checked: "pre-check" },
        { name: "velocity uncertainty", stream: "down", limit: stale, checked: "pre-check, in flight" },
        { name: "front, back, left, right, up", stream: "ranger", limit: stale, checked: "" },
        { name: "battery voltage", stream: "battery", limit: value("BATTERY_STALE_AFTER"), checked: "pre-check" },
      ],
    };
  }

  function setupTimeline() {
    const svg = document.getElementById("timeline");
    if (!svg) return;
    const numbers = timelineNumbers();
    const TICK = numbers.tick, STREAMS = numbers.streams, VALUES = numbers.values;
    const x0 = 170, x1 = 740, laneTop = 22, laneStep = 44, tickY = 22 + 4 * 44 + 4;
    const scale = (x1 - x0) / WINDOW;
    const X = function (t) { return x0 + t * scale; };
    let gapOn = false;
    let playing = !reduceMotion;
    let now = 0;
    let pinnedTick = reduceMotion ? 12 : null;
    let last = null;

    function arrivals(stream) {
      const list = [];
      for (let k = -60; ; k++) {
        const t = stream.phase + k * stream.period;
        if (t > WINDOW) break;
        if (gapOn && t >= GAP[0] && t < GAP[1]) continue;
        list.push(t);
      }
      return list;
    }

    let packetNodes = [];
    let tickNodes = [];
    let playhead = null;
    function draw() {
      svg.textContent = "";
      packetNodes = [];
      tickNodes = [];
      if (gapOn) {
        el("rect", { x: X(GAP[0]), y: 8, width: X(GAP[1]) - X(GAP[0]), height: tickY + 14, style: "fill:var(--critical);opacity:0.12" }, svg);
        el("text", { x: X(GAP[0]) + 6, y: 18, class: "axis-text", style: "fill:#ff8a8a" }, svg, "no packets");
      }
      for (let t = 0; t <= WINDOW + 1e-9; t += 0.2) {
        el("line", { x1: X(t), y1: 10, x2: X(t), y2: tickY + 18, class: "grid-line" }, svg);
        el("text", { x: X(t), y: tickY + 34, "text-anchor": "middle", class: "axis-text" }, svg, fmt(t, 1) + " s");
      }
      STREAMS.forEach(function (stream, i) {
        const y = laneTop + i * laneStep;
        el("text", { x: 0, y: y + 13, class: "lane-label" }, svg, stream.label);
        el("text", { x: 0, y: y + 28, class: "lane-sub" }, svg, stream.sub);
        el("line", { x1: x0, y1: y + 22, x2: x1, y2: y + 22, class: "grid-line" }, svg);
        arrivals(stream).forEach(function (t) {
          if (t < 0) return;
          const node = el("rect", { x: X(t) - 2, y: y + 6, width: 4, height: 22, rx: 2, style: "fill:" + stream.color }, svg);
          packetNodes.push({ node: node, t: t });
        });
      });
      el("text", { x: 0, y: tickY + 6, class: "lane-label" }, svg, "Tick");
      el("text", { x: 0, y: tickY + 21, class: "lane-sub" }, svg, "snapshot, " + text("TICK_RATE"));
      for (let k = 0; k * TICK <= WINDOW + 1e-9; k++) {
        const t = k * TICK;
        const group = el("g", { class: "click", tabindex: "0", role: "button", "aria-label": "Tick at " + fmt(t) + " s" }, svg);
        const line = el("line", { x1: X(t), y1: 14, x2: X(t), y2: tickY + 16, style: "stroke:var(--ink-3);stroke-width:1;stroke-dasharray:2 3;opacity:0.5" }, group);
        const mark = el("circle", { cx: X(t), cy: tickY + 8, r: 4.5, style: "fill:var(--ink)" }, group);
        el("rect", { x: X(t) - 6, y: 10, width: 12, height: tickY + 10, style: "fill:transparent" }, group);
        tickNodes.push({ line: line, mark: mark, k: k });
        onActivate(group, function () { pinnedTick = k; setPlaying(false); now = t; render(); });
      }
      playhead = el("line", { x1: X(0), y1: 8, x2: X(0), y2: tickY + 18, class: "playhead" }, svg);
    }

    function lastArrival(streamKey, t) {
      const stream = STREAMS.find(function (s) { return s.key === streamKey; });
      let best = null;
      arrivals(stream).forEach(function (a) { if (a <= t + 1e-9) best = a; });
      return best;
    }

    const title = document.getElementById("ages-title");
    const body = document.querySelector("#ages tbody");
    const verdict = document.getElementById("ages-verdict");
    function showAges(k) {
      const t = k * TICK;
      title.textContent = "Ages at tick " + k + ", t = " + fmt(t) + " s";
      body.textContent = "";
      const stale = [];
      VALUES.forEach(function (value) {
        const arrived = lastArrival(value.stream, t);
        const age = arrived === null ? Infinity : t - arrived;
        const isStale = age > value.limit;
        if (isStale && value.checked) stale.push(value.name + " (" + fmt(age) + " s)");
        const row = document.createElement("tr");
        const stream = STREAMS.find(function (s) { return s.key === value.stream; });
        [value.name, stream.label, fmt(age) + " s", fmt(value.limit) + " s"].forEach(function (text, i) {
          const cell = document.createElement("td");
          cell.textContent = text;
          if (i >= 2) cell.className = "num";
          if (i === 0 && value.checked) {
            const tag = document.createElement("span");
            tag.className = "checked";
            tag.textContent = value.checked;
            cell.append(" ", tag);
          }
          row.appendChild(cell);
        });
        const chipCell = document.createElement("td");
        const chip = document.createElement("span");
        chip.className = "state-chip " + (isStale ? "stale" : "fresh");
        chip.textContent = isStale ? "stale" : "fresh";
        chipCell.appendChild(chip);
        row.appendChild(chipCell);
        body.appendChild(row);
      });
      verdict.textContent = stale.length
        ? "The safety pre-check fails on this snapshot: " + stale.join(", ") + " too old. The drone lands."
        : "The safety pre-check passes on these ages: every value it checks is fresh.";
      tickNodes.forEach(function (n) {
        const on = n.k === k;
        n.mark.setAttribute("r", on ? 7 : 4.5);
        n.mark.style.fill = on ? "var(--accent)" : "var(--ink)";
        n.line.style.opacity = on ? "1" : "0.5";
        n.line.style.stroke = on ? "var(--accent)" : "var(--ink-3)";
      });
    }

    let shownTick = -1;
    function render() {
      playhead.setAttribute("x1", X(now));
      playhead.setAttribute("x2", X(now));
      packetNodes.forEach(function (p) { p.node.style.opacity = p.t <= now ? "1" : "0.22"; });
      const k = pinnedTick !== null ? pinnedTick : Math.floor(now / TICK + 1e-9);
      if (k !== shownTick) { showAges(k); shownTick = k; }
    }
    function frame(stamp) {
      if (!playing) { last = null; return; }
      if (last !== null) now += ((stamp - last) / 1000) * 0.2;
      last = stamp;
      if (now > WINDOW) now = 0;
      render();
      requestAnimationFrame(frame);
    }
    const playButton = document.getElementById("tl-play");
    function setPlaying(on) {
      playing = on;
      playButton.textContent = on ? "Pause" : "Play";
      if (on) { pinnedTick = null; requestAnimationFrame(frame); }
    }
    playButton.addEventListener("click", function () { setPlaying(!playing); });
    const gapButton = document.getElementById("tl-gap");
    gapButton.addEventListener("click", function () {
      gapOn = !gapOn;
      gapButton.setAttribute("aria-pressed", String(gapOn));
      draw();
      shownTick = -1;
      pinnedTick = gapOn ? 16 : 12;
      now = pinnedTick * TICK;
      setPlaying(false);
      render();
    });
    draw();
    if (pinnedTick !== null) now = pinnedTick * TICK;
    render();
    setPlaying(playing);
  }

  // --- Section 5: crossing the bad-flow zone ---------------------------------------------
  // The code's numbers come from the page. The take-off target (as in the transcript), the hover's length
  // and when the down range is read are the model's. The drone follows each command at once; readings are exact.
  function flightNumbers() {
    return {
      tick: 1 / value("TICK_RATE"),
      climbSpeed: value("INITIAL_CLIMB_SPEED"),
      finalHeight: value("FINAL_DESCENT_HEIGHT"),
      climbLimit: value("INITIAL_CLIMB_TIME_LIMIT"),
      vertical: value("VERTICAL_SPEED"),
      minMove: value("MIN_MOVE_DURATION"),
      aimBelow: value("LANDING_APPROACH_AIM_BELOW"),
      backup: value("LANDING_APPROACH_BACKUP"),
      finalSpeed: value("FINAL_DESCENT_SPEED"),
      touchdownRange: value("TOUCHDOWN_DOWN_RANGE"),
      hold: value("TOUCHDOWN_HOLD"),
      recent: value("RECENT_WINDOW"),
      margin: value("FINAL_DESCENT_MARGIN"),
      readPeriod: value("DOWN_RANGE_PERIOD_MS") / 1000,
      target: 0.5, hover: 2.0, readPhase: 0.005,
    };
  }
  function smooth(s) { return s <= 0 ? 0 : s >= 1 ? 1 : s * s * s * (10 - 15 * s + 6 * s * s); }

  function flightModel(F) {
    const TICK = F.tick;
    const m = {};
    const readingBefore = function (t, h) {
      const k = Math.floor((t - F.readPhase) / F.readPeriod + 1e-9);
      const at = F.readPhase + k * F.readPeriod;
      return { at: at, value: h(at) };
    };
    // Initial climb: level, one setpoint each tick, until a reading at or above the final descent height.
    const climb = function (t) { return F.climbSpeed * Math.max(t, 0); };
    let t = 0;
    while (true) {
      t += TICK;
      if (readingBefore(t, climb).value >= F.finalHeight) break;
    }
    m.tH = t;
    m.z0 = climb(m.tH);
    m.d1 = Math.max((F.target - m.z0) / F.vertical, F.minMove);
    m.tHoverStart = m.tH + m.d1;
    m.tL = Math.ceil((m.tHoverStart + F.hover) / TICK - 1e-9) * TICK;
    m.aim = Math.min(F.target, F.finalHeight - F.aimBelow);
    m.d2 = Math.max((F.target - m.aim) / F.vertical, F.minMove);
    m.backupAt = m.tL + m.d2 + F.backup;
    const before = function (x) {
      if (x <= m.tH) return climb(x);
      if (x <= m.tHoverStart) return m.z0 + (F.target - m.z0) * smooth((x - m.tH) / m.d1);
      if (x <= m.tL) return F.target;
      return F.target - (F.target - m.aim) * smooth((x - m.tL) / m.d2);
    };
    // Landing approach: ends at the first tick whose reading is at or below the final descent height.
    const seen = [];
    t = m.tL;
    while (true) {
      t += TICK;
      const r = readingBefore(t, before);
      if (!seen.length || seen[seen.length - 1].at !== r.at) seen.push(r);
      if (r.value <= F.finalHeight) { m.downAtF = r.value; break; }
    }
    m.tF = t;
    m.hF = before(m.tF);
    const recent = seen.filter(function (r) { return m.tF - r.at <= F.recent; }).map(function (r) { return r.value; });
    m.highest = Math.max.apply(null, recent.concat([m.downAtF]));
    m.deadline = m.tF + m.highest / F.finalSpeed + F.margin;
    m.floorAt = m.tF + m.hF / F.finalSpeed;
    m.h = function (x) {
      if (x <= m.tF) return before(x);
      return Math.max(0, m.hF - F.finalSpeed * (x - m.tF));
    };
    // Final descent: the touchdown hold starts at the first low reading a tick sees.
    m.lowSince = null;
    t = m.tF;
    while (true) {
      t += TICK;
      const r = readingBefore(t, m.h);
      if (r.value > F.touchdownRange) m.lowSince = null;
      else if (m.lowSince === null) m.lowSince = r.at;
      if (m.lowSince !== null && t - m.lowSince >= F.hold - 1e-9) break;
    }
    m.tS = t;
    m.end = m.tS + 0.4;
    return m;
  }

  function setupFlight() {
    const svg = document.getElementById("flight");
    if (!svg) return;
    const F = flightNumbers();
    const TICK = F.tick;
    const m = flightModel(F);
    const x0 = 56, x1 = 744, yFloor = 286, yTop = 36, hMax = 0.6, tMax = 8.6;
    const X = function (t) { return x0 + (t / tMax) * (x1 - x0); };
    const Y = function (h) { return yFloor - (h / hMax) * (yFloor - yTop); };

    // Static layers: grid, zone, reference heights, time marks.
    for (let h = 0; h <= hMax + 1e-9; h += 0.1) {
      el("line", { x1: x0, y1: Y(h), x2: x1, y2: Y(h), class: "grid-line" }, svg);
      el("text", { x: x0 - 8, y: Y(h) + 4, "text-anchor": "end", class: "axis-text" }, svg, fmt(h, 1) + " m");
    }
    for (let s = 0; s <= 8; s += 1) {
      el("text", { x: X(s), y: yFloor + 18, "text-anchor": "middle", class: "axis-text" }, svg, s + " s");
    }
    for (let k = 0; k * TICK <= tMax; k++) {
      el("line", { x1: X(k * TICK), y1: yFloor, x2: X(k * TICK), y2: yFloor + (k % 10 === 0 ? 6 : 3), style: "stroke:var(--ink-3);stroke-width:0.6" }, svg);
    }
    el("rect", { x: x0, y: Y(0.1), width: x1 - x0, height: Y(0) - Y(0.1), style: "fill:var(--caution);opacity:0.13" }, svg);
    el("text", { x: X(0.7), y: Y(0.1) + 14, class: "axis-text", style: "fill:var(--caution)" }, svg, "bad-flow zone: at least 0.1 m");
    el("line", { x1: x0, y1: Y(F.finalHeight), x2: x1, y2: Y(F.finalHeight), style: "stroke:var(--ink-2);stroke-dasharray:6 4" }, svg);
    el("text", { x: x1 - 6, y: Y(F.finalHeight) - 6, "text-anchor": "end", class: "axis-text" }, svg, "final descent height " + text("FINAL_DESCENT_HEIGHT"));
    el("line", { x1: x0, y1: Y(F.touchdownRange), x2: x1, y2: Y(F.touchdownRange), style: "stroke:var(--ink-3);stroke-dasharray:1 3" }, svg);
    el("text", { x: X(6.2), y: Y(F.touchdownRange) - 4, class: "axis-text" }, svg, "touchdown: down range ≤ " + text("TOUCHDOWN_DOWN_RANGE"));
    el("line", { x1: x0, y1: yFloor, x2: x1, y2: yFloor, style: "stroke:var(--ink-2)" }, svg);

    function vmark(t, label, color, row) {
      el("line", { x1: X(t), y1: yTop - 6, x2: X(t), y2: yFloor, style: "stroke:" + color + ";stroke-dasharray:4 4;opacity:0.85" }, svg);
      const left = X(t) > x1 - 200; // near the right edge, the label goes left of its line
      el("text", { x: X(t) + (left ? -4 : 4), y: yTop + 4 + row * 13, "text-anchor": left ? "end" : "start", class: "axis-text", style: "fill:" + color }, svg, label);
    }
    vmark(F.climbLimit, "climb limit " + text("INITIAL_CLIMB_TIME_LIMIT") + ", not reached", "var(--caution)", 0);
    vmark(m.backupAt, "approach backup, not needed", "var(--caution)", 0);
    vmark(m.deadline, "deadline " + fmt(m.deadline, 1) + " s, not reached", "var(--caution)", 1);

    // The flight path, colored by who commands the motion.
    function path(from, to, color) {
      const points = [];
      for (let t = from; t <= to + 1e-9; t += 0.01) points.push(fmt(X(t), 1) + "," + fmt(Y(m.h(t)), 1));
      points.push(fmt(X(to), 1) + "," + fmt(Y(m.h(to)), 1));
      el("polyline", { points: points.join(" "), style: "fill:none;stroke:" + color + ";stroke-width:2.5;stroke-linejoin:round" }, svg);
    }
    path(0, m.tH, "var(--stream)");
    path(m.tH, m.tF, "var(--planner)");
    path(m.tF, m.tS, "var(--stream)");
    el("line", { x1: X(m.tS), y1: yFloor, x2: X(m.end), y2: yFloor, style: "stroke:var(--ink-3);stroke-width:2.5" }, svg);
    [[m.tH, "hand-over"], [m.tF, "final descent"]].forEach(function (pair) {
      el("circle", { cx: X(pair[0]), cy: Y(m.h(pair[0])), r: 4.5, style: "fill:var(--bg);stroke:var(--ink);stroke-width:2" }, svg);
    });
    el("text", { x: X(m.tH) + 8, y: Y(F.finalHeight) + 15, class: "axis-text" }, svg, "hand-over");
    el("text", { x: X(m.tF) + 10, y: Y(F.finalHeight) - 8, class: "axis-text" }, svg, "final descent");
    el("rect", { x: X(m.lowSince), y: yFloor - 18, width: X(m.tS) - X(m.lowSince), height: 12, rx: 3, style: "fill:var(--good);opacity:0.35" }, svg);
    el("text", { x: X(m.tS) + 8, y: yFloor - 8, class: "axis-text", style: "fill:#6fd66f" }, svg, "hold " + text("TOUCHDOWN_HOLD") + ", then the motor stop");

    // Moving parts: the playhead and the drone.
    const playhead = el("line", { x1: X(0), y1: yTop - 6, x2: X(0), y2: yFloor, class: "playhead", style: "opacity:0.5" }, svg);
    const drone = el("g", {}, svg);
    el("line", { x1: -11, y1: -5, x2: 11, y2: -5, style: "stroke:var(--ink);stroke-width:2" }, drone);
    el("rect", { x: -6, y: -5, width: 12, height: 7, rx: 2, style: "fill:var(--ink)" }, drone);
    const rotors = el("g", {}, drone);
    el("line", { x1: -16, y1: -8, x2: -6, y2: -8, style: "stroke:var(--accent);stroke-width:2" }, rotors);
    el("line", { x1: 6, y1: -8, x2: 16, y2: -8, style: "stroke:var(--accent);stroke-width:2" }, rotors);
    // Labels paint last, so their dark outline masks the lines and the playhead behind them.
    svg.querySelectorAll("text").forEach(function (t) { svg.appendChild(t); });

    const range = document.getElementById("fl-time");
    const out = document.getElementById("fl-out");
    const readout = document.getElementById("fl-readout");
    const speedSelect = document.getElementById("fl-speed");
    const playButton = document.getElementById("fl-play");
    range.max = String(Math.ceil(m.end * 100) * 10);
    const nodes = {};
    document.querySelectorAll("#sm .node").forEach(function (n) { nodes[n.getAttribute("data-node")] = n; });
    const sends = document.querySelectorAll("#sends > div");

    function phaseAt(t) {
      if (t < m.tH) return "climb";
      if (t < m.tHoverStart) return "handover";
      if (t < m.tL) return "hover";
      if (t < m.tF) return "approach";
      if (t < m.tS) return "final";
      return "stop";
    }
    const NODE_OF = { climb: "climb", handover: "flying", hover: "flying", approach: "approach", final: "final", stop: "stop" };
    function describe(t, phase, h) {
      const at = "t = " + fmt(t) + " s · height " + fmt(h) + " m";
      switch (phase) {
        case "climb":
          return at + "<br><b>Initial climb.</b> One level setpoint up at " + text("INITIAL_CLIMB_SPEED") + " each tick, roll and pitch held at 0.";
        case "handover":
          return at + "<br><b>Hand-over at " + fmt(m.tH) + " s</b>, at " + fmt(m.z0) + " m with flow: the last setpoint, go_to(0.5 m, " + fmt(m.d1) + " s), then the release. The drone's own planner climbs now.";
        case "hover":
          return at + "<br><b>Hovering.</b> The high-level commander holds the position until the behavior asks to land.";
        case "approach":
          return at + "<br><b>Landing approach.</b> go_to aimed at " + fmt(m.aim) + " m over " + fmt(m.d2) + " s. The down range reaching " + text("FINAL_DESCENT_HEIGHT") + " ends it.";
        case "final": {
          const hold = m.lowSince !== null && t >= m.lowSince ? " Touchdown hold: " + fmt(Math.min(t - m.lowSince, F.hold)) + " s of " + text("TOUCHDOWN_HOLD") + "." : "";
          return at + "<br><b>Final descent.</b> One level setpoint down at " + text("FINAL_DESCENT_SPEED") + " each tick. Deadline set at " + fmt(m.deadline) + " s." + hold;
        }
        default:
          return at + "<br><b>Touchdown confirmed at " + fmt(m.tS) + " s.</b> Motor stop: the stop setpoint, the high-level stop, then the release.";
      }
    }

    let t = 0;
    let playing = false;
    let last = null;
    function render() {
      const h = m.h(t);
      playhead.setAttribute("x1", X(t));
      playhead.setAttribute("x2", X(t));
      drone.setAttribute("transform", "translate(" + fmt(X(t), 1) + "," + fmt(Y(h) - 2, 1) + ")");
      rotors.style.opacity = t >= m.tS ? "0.25" : "1";
      const phase = phaseAt(t);
      for (const key in nodes) nodes[key].classList.toggle("on", key === NODE_OF[phase]);
      sends.forEach(function (line) { line.classList.toggle("on", line.getAttribute("data-phase") === phase); });
      range.value = String(Math.round(t * 1000));
      out.textContent = fmt(t) + " s";
      readout.innerHTML = describe(t, phase, h);
    }
    function frame(stamp) {
      if (!playing) { last = null; return; }
      if (last !== null) t += ((stamp - last) / 1000) * parseFloat(speedSelect.value);
      last = stamp;
      if (t >= m.end) { t = m.end; setPlaying(false); }
      render();
      if (playing) requestAnimationFrame(frame);
    }
    function setPlaying(on) {
      playing = on;
      playButton.textContent = on ? "Pause" : t >= m.end ? "Replay" : "Play";
      if (on) {
        last = null; // time spent stopped doesn't count
        requestAnimationFrame(frame);
      }
    }
    playButton.addEventListener("click", function () {
      if (!playing && t >= m.end) t = 0;
      setPlaying(!playing);
    });
    range.addEventListener("input", function () { setPlaying(false); t = parseInt(range.value, 10) / 1000; render(); });
    render();
  }

  // --- Evidence links open in a new tab, so the reader keeps their place in the tour ------
  function setupLinks() {
    document.querySelectorAll('a[href^="https://"]').forEach(function (a) {
      a.target = "_blank";
      a.rel = "noopener";
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    setupLinks();
    setupDepth();
    setupTerms();
    setupSelect("#layers .layer", "data-layer", ".layer-card");
    setupSelect("#modules .mod", "data-mod", ".mod-card");
    setupSelect("#sm .branch", "data-branch", ".branch-card");
    setupTimeline();
    setupFlight();
  });
})();
