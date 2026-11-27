// The project tour's shared script: glossary pop-overs, clickable figures,
// and the adapter chapter's animations and calculator. No libraries, no build step.
(function () {
  "use strict";

  const SVG = "http://www.w3.org/2000/svg";
  const reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // The code's numbers and the glossary's definitions at the pinned commit, which
  // tools/tour_numbers.py writes into the page.
  const NUMBERS = readNumbers();
  function readNumbers() {
    const node = document.getElementById("tour-numbers");
    return node ? JSON.parse(node.textContent) : { constants: {}, formulas: {}, adrs: {}, terms: {} };
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
  function onActivate(node, handler) {
    node.addEventListener("click", handler);
    node.addEventListener("keydown", function (event) {
      if (event.key === "Enter" || event.key === " ") { event.preventDefault(); handler(event); }
    });
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
      const definition = NUMBERS.terms[term];
      if (!definition) return null;
      return [popTitle(term, false), document.createTextNode(definition), popNote("from", ["From the project's glossary"])];
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
      // The "dots" joke: its definition is "See dots", with a dotted word that opens it again.
      const body = node.hasAttribute("data-pop-see-itself")
        ? popNote("see", ["See ", node.cloneNode(true), "."])
        : document.createTextNode(node.getAttribute("data-pop-text") || "");
      return [popTitle(title, false), body, popNote("from", [node.getAttribute("data-pop-from") || ""])];
    }
    const key = node.getAttribute("data-formula");
    const formula = key !== null ? NUMBERS.formulas[key] : null;
    if (formula) {
      return [
        popTitle(formula.formula, true),
      ].concat(cited(formula.description), [
        popNote("worked", [formula.worked + " = " + formula.text]),
        popNote("from", ["Worked out from the code's numbers"]),
      ]);
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
      const rect = node.getBoundingClientRect(); // read first: the node may be inside the pop-up
      pop.textContent = "";
      pop.append.apply(pop, content);
      pop.hidden = false;
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
      // A word inside the pop-up waits for its click: moving the pop-up on focus would lose the click.
      if (event.target.matches && event.target.matches(POPS) && !pop.contains(event.target)) show(event.target);
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

  // --- Section 4: the firmware's setpoint watchdog ------------------------------------------
  // The 500 ms and 2000 ms are the firmware's, from the facts register. When the ticks stop and the
  // chart's length are the model's.
  const WATCHDOG_WARNING = 0.5;
  const WATCHDOG_TIMEOUT = 2.0;
  const TICKS_STOP = 1.0;
  const WATCHDOG_END = 3.2;
  function setupWatchdog() {
    const svg = document.getElementById("watchdog");
    if (!svg) return;
    const TICK = 1 / value("TICK_RATE");
    const x0 = 64, x1 = 744, yTop = 18, yBottom = 206, ageMax = 2.4;
    const X = function (t) { return x0 + (t / WATCHDOG_END) * (x1 - x0); };
    const Y = function (age) { return yBottom - (Math.min(age, ageMax) / ageMax) * (yBottom - yTop); };
    let mode = "stream";
    let now = 0;
    let playing = false;
    let last = null;

    function age(t) {
      if (mode === "high") return 0;
      const lastSend = Math.floor(Math.min(t, TICKS_STOP - 1e-9) / TICK + 1e-9) * TICK;
      return t - lastSend;
    }
    for (let a = 0; a <= 2 + 1e-9; a += 0.5) {
      el("line", { x1: x0, y1: Y(a), x2: x1, y2: Y(a), class: "grid-line" }, svg);
      el("text", { x: x0 - 8, y: Y(a) + 4, "text-anchor": "end", class: "axis-text" }, svg, fmt(a, 1) + " s");
    }
    for (let t = 0; t <= WATCHDOG_END + 1e-9; t += 0.5) {
      el("text", { x: X(t), y: yBottom + 18, "text-anchor": "middle", class: "axis-text" }, svg, fmt(t, 1) + " s");
    }
    el("text", { x: 4, y: yTop - 4, class: "axis-text" }, svg, "setpoint age");
    el("line", { x1: x0, y1: Y(WATCHDOG_WARNING), x2: x1, y2: Y(WATCHDOG_WARNING), style: "stroke:var(--caution);stroke-dasharray:6 4" }, svg);
    el("text", { x: x1 - 4, y: Y(WATCHDOG_WARNING) - 6, "text-anchor": "end", class: "axis-text", style: "fill:var(--caution)" }, svg, "500 ms: warning, levels out");
    el("line", { x1: x0, y1: Y(WATCHDOG_TIMEOUT), x2: x1, y2: Y(WATCHDOG_TIMEOUT), style: "stroke:var(--critical);stroke-dasharray:6 4" }, svg);
    el("text", { x: x1 - 4, y: Y(WATCHDOG_TIMEOUT) - 6, "text-anchor": "end", class: "axis-text", style: "fill:#ff8a8a" }, svg, "2000 ms: motors off");
    el("line", { x1: X(TICKS_STOP), y1: yTop, x2: X(TICKS_STOP), y2: yBottom, style: "stroke:var(--ink-3);stroke-dasharray:2 3" }, svg);
    el("text", { x: X(TICKS_STOP) + 6, y: yTop + 10, class: "axis-text" }, svg, "the ticks stop");
    el("line", { x1: x0, y1: yBottom, x2: x1, y2: yBottom, style: "stroke:var(--ink-2)" }, svg);
    const line = el("polyline", { style: "fill:none;stroke:var(--stream);stroke-width:2.5;stroke-linejoin:round" }, svg);
    const head = el("circle", { r: 4.5, style: "fill:var(--ink)" }, svg);
    // Labels paint last, so their dark outline masks the lines behind them.
    svg.querySelectorAll("text").forEach(function (t) { svg.appendChild(t); });

    const readout = document.getElementById("wd-readout");
    const playButton = document.getElementById("wd-play");
    function describe(t, a) {
      const at = "t = " + fmt(t) + " s · setpoint age " + fmt(a) + " s<br>";
      if (mode === "high") return at + "<b>A high-level move renews its own setpoint on the drone,</b> so the age stays at zero and the move goes on, ticks or not. Then the drone holds the move's target.";
      if (t < TICKS_STOP) return at + "<b>A setpoint every tick:</b> the age never passes one tick, " + fmt(TICK) + " s.";
      if (a < WATCHDOG_WARNING) return at + "<b>No new setpoints.</b> The drone still follows the last one.";
      if (a < WATCHDOG_TIMEOUT) return at + "<b>Past 500 ms:</b> the drone warns and levels out.";
      return at + "<b>Past 2000 ms: the motors go off.</b> The drone drops, and it refuses to arm again until it's power cycled.";
    }
    function render() {
      const points = [];
      for (let t = 0; t <= now + 1e-9; t += 0.005) points.push(fmt(X(t), 1) + "," + fmt(Y(age(t)), 1));
      points.push(fmt(X(now), 1) + "," + fmt(Y(age(now)), 1));
      line.setAttribute("points", points.join(" "));
      line.style.stroke = mode === "high" ? "var(--planner)" : "var(--stream)";
      head.setAttribute("cx", X(now));
      head.setAttribute("cy", Y(age(now)));
      readout.innerHTML = describe(now, age(now));
    }
    function frame(stamp) {
      if (!playing) { last = null; return; }
      if (last !== null) now += (stamp - last) / 1000;
      last = stamp;
      if (now >= WATCHDOG_END) { now = WATCHDOG_END; setPlaying(false); }
      render();
      if (playing) requestAnimationFrame(frame);
    }
    function setPlaying(on) {
      playing = on;
      playButton.textContent = on ? "Pause" : now >= WATCHDOG_END ? "Replay" : "Play";
      if (on) {
        last = null; // time spent stopped doesn't count
        requestAnimationFrame(frame);
      }
    }
    playButton.addEventListener("click", function () {
      if (!playing && now >= WATCHDOG_END) now = 0;
      setPlaying(!playing);
    });
    const tabs = document.querySelectorAll("[data-wd]");
    tabs.forEach(function (tab) {
      tab.addEventListener("click", function () {
        mode = tab.getAttribute("data-wd");
        tabs.forEach(function (other) { other.setAttribute("aria-pressed", String(other === tab)); });
        document.querySelectorAll("[data-wd-for]").forEach(function (panel) {
          panel.hidden = panel.getAttribute("data-wd-for") !== mode;
        });
        now = reduceMotion ? WATCHDOG_END : 0;
        render();
        setPlaying(!reduceMotion);
      });
    });
    now = reduceMotion ? WATCHDOG_END : 0;
    render();
    setPlaying(false);
  }

  // --- Section 6: may be flying, the adapter's four rules --------------------------------------
  // The same rules as TakeOffAndLanding.may_be_flying, in the same order. The examples' inputs are the model's.
  const MBF_EXAMPLES = {
    hovering: { sent: "take-off", status: "flying", age: 0.02, since: 2.5 },
    "took-off": { sent: "take-off", status: "floor", age: 0.02, since: 0.3 },
    landed: { sent: "none", status: "flying", age: 0.02, since: 2.5 },
    stale: { sent: "take-off", status: "floor", age: 0.4, since: 2.5 },
    "taken-over": { sent: "take-over", status: "floor", age: 0.02, since: 0 },
  };
  function mayBeFlying(input) {
    if (input.sent === "none") return { flying: false, rule: 1 };
    if (input.status === "none" || input.age > value("STALE_AFTER") || input.status === "flying") return { flying: true, rule: 2 };
    // Taking over sets the take-off's time to minus infinity, so the grace is always over.
    const since = input.sent === "take-over" ? Infinity : input.since;
    return since < value("TAKE_OFF_STATUS_GRACE") ? { flying: true, rule: 3 } : { flying: false, rule: 4 };
  }
  function setupMayBeFlying() {
    const root = document.getElementById("mbf");
    if (!root) return;
    const age = document.getElementById("mbf-age");
    const since = document.getElementById("mbf-since");
    const ageOut = document.getElementById("mbf-age-out");
    const sinceOut = document.getElementById("mbf-since-out");
    const answer = document.getElementById("mbf-answer");
    const effects = document.getElementById("mbf-effects");
    const presets = root.querySelectorAll("[data-preset]");
    function checked(name) { return root.querySelector('input[name="' + name + '"]:checked').value; }
    function read() {
      return { sent: checked("mbf-sent"), status: checked("mbf-status"), age: parseFloat(age.value), since: parseFloat(since.value) };
    }
    function render() {
      const input = read();
      const result = mayBeFlying(input);
      age.disabled = input.status === "none";
      since.disabled = input.sent !== "take-off";
      ageOut.textContent = input.status === "none" ? "—" : fmt(input.age) + " s";
      sinceOut.textContent = input.sent === "take-off" ? fmt(input.since) + " s" : input.sent === "take-over" ? "taken over" : "—";
      answer.textContent = "May be flying: " + (result.flying ? "yes" : "no") + ", by rule " + result.rule;
      document.querySelectorAll("#mbf-rules li").forEach(function (li) {
        li.classList.toggle("on", li.getAttribute("data-rule") === String(result.rule));
      });
      const rows = result.flying
        ? [["land()", "a landing: the approach, then the final descent"], ["take_off()", "a high-level climb, no initial climb"], ["hover()", "a hover"], ["reset_estimate()", "ignored, with a warning"], ["Safety pre-check", "checks the velocity uncertainty, outside the initial climb"]]
        : [["land()", "only the motor stop"], ["take_off()", "the initial climb"], ["hover()", "ignored"], ["reset_estimate()", "sent"], ["Safety pre-check", "doesn't check the velocity uncertainty"]];
      effects.textContent = "";
      rows.forEach(function (row) {
        const dt = document.createElement("dt");
        if (row[0].indexOf("(") >= 0) {
          const code = document.createElement("code");
          code.textContent = row[0];
          dt.appendChild(code);
        } else {
          dt.textContent = row[0];
        }
        const dd = document.createElement("dd");
        dd.textContent = row[1];
        effects.append(dt, dd);
      });
    }
    function apply(example) {
      root.querySelector('input[name="mbf-sent"][value="' + example.sent + '"]').checked = true;
      root.querySelector('input[name="mbf-status"][value="' + example.status + '"]').checked = true;
      age.value = String(example.age);
      since.value = String(example.since);
    }
    function press(key) {
      presets.forEach(function (other) { other.setAttribute("aria-pressed", String(other.getAttribute("data-preset") === key)); });
    }
    presets.forEach(function (button) {
      button.addEventListener("click", function () {
        const key = button.getAttribute("data-preset");
        apply(MBF_EXAMPLES[key]);
        press(key);
        render();
      });
    });
    root.addEventListener("input", function (event) {
      if (event.target.matches("input")) { press(null); render(); }
    });
    apply(MBF_EXAMPLES["took-off"]);
    press("took-off");
    render();
  }

  // --- Section 7: each step's time limit as a bar, scaled to the longest -------------------
  function setupStepBars() {
    const bars = document.querySelectorAll("[data-bar]");
    let longest = 0;
    bars.forEach(function (bar) { longest = Math.max(longest, value(bar.getAttribute("data-bar"))); });
    bars.forEach(function (bar) { bar.style.width = (100 * value(bar.getAttribute("data-bar"))) / longest + "%"; });
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
    setupTerms();
    setupSelect("#layers .layer", "data-layer", ".layer-card");
    setupSelect("#modules .mod", "data-mod", ".mod-card");
    setupSelect("#sm .branch", "data-branch", ".branch-card");
    setupSelect("#steps .step", "data-step", ".step-card");
    setupSelect("#whatifs .wi", "data-wi", ".wi-card");
    setupSelect("#plants .plant", "data-plant", ".plant-card");
    setupTimeline();
    setupFlight();
    setupWatchdog();
    setupMayBeFlying();
    setupStepBars();
  });
})();
