// app.js — the MyxoHunt page (B94): draws the world and the counts graph from the frames the
// simulation worker sends, and turns the sliders, switches and options into messages for it.
"use strict";

const SPEEDS = [1, 5, 15, 30, 60, 120, 300, 600, 0];      // × real time; 0 = as fast as possible
const COL = { ecoli: "#e63ca0", dormant: "#962369", dead: "#bea0b2", pole: "#ffffff", rim: "#ffffff",
  spore: "#cdf0a5", sporeEdge: "#1f9d3a", myxo: "#46cd5f", starving: "#237837", grid: "#37373e", axis: "#afafb6" };
const $ = (id) => document.getElementById(id);
const worker = new Worker("worker.js");

let frame = null, worldId = 0, rows = [], drawPending = false, running = true;
let lastT = null, lastWall = 0, speedNow = 0, lastFocus = null;
const controls = {}, switches = [], evidence = [];
const groundC = document.createElement("canvas"), slimeC = document.createElement("canvas");

// ------------------------------------------------------------ layout
function layout() {
  const wide = window.innerWidth > 900;
  const availW = window.innerWidth - (wide ? 380 : 0) - 20;
  const availH = window.innerHeight - 170 - 30;
  const size = Math.floor(Math.max(280, Math.min(availW, wide ? availH : availW, 900)));
  document.documentElement.style.setProperty("--world", size + "px");
  const dpr = window.devicePixelRatio || 1;
  $("world").width = $("world").height = Math.round(size * dpr);
  $("graph").width = Math.round(size * dpr);
  $("graph").height = Math.round(170 * dpr);
  requestDraw();
}

// ------------------------------------------------------------ controls
const fmtNum = (v) => String(Number(Number(v).toPrecision(6)));
const fmtValue = (p, v) => (p.percent ? Math.round(v * 100) + "%" : p.prefix + fmtNum(v) + p.suffix);
const send = (msg) => worker.postMessage(msg);

function heading(parent, text, cls) {
  const h = document.createElement("h3");
  h.textContent = text;
  if (cls) h.className = cls;
  parent.appendChild(h);
}

function slider(p, parent) {
  const div = document.createElement("div");
  div.className = "control";
  const label = document.createElement("label");
  const name = document.createElement("span");
  const val = document.createElement("b");
  name.append(p.label + ": ", val);
  const note = document.createElement("span");
  note.className = "when";
  note.textContent = p.backing;
  label.append(name, note);
  const input = document.createElement("input");
  Object.assign(input, { type: "range", min: p.lo, max: p.hi, step: p.step });
  input.addEventListener("input", () => {
    val.textContent = fmtValue(p, +input.value);
    send({ type: "param", key: p.key, value: +input.value });
  });
  div.append(label, input);
  parent.appendChild(div);
  controls[p.key] = { input, val, p };
}

function buildControls(cat) {
  for (const p of cat.main) slider(p, p.when === "live" ? $("mainLive") : $("mainReset"));
  const body = $("overlayBody");
  heading(body, "Advanced settings (tuned or assumed)");
  for (const p of cat.advanced) slider(p, body);
  heading(body, "Switch a rule off");
  cat.switches.forEach((s, i) => {
    const row = document.createElement("label");
    row.className = "switch";
    const box = document.createElement("input");
    box.type = "checkbox";
    box.addEventListener("change", () => send({ type: "switch", index: i, on: box.checked }));
    const text = document.createElement("span");
    text.textContent = s.label;
    if (s.note) { const small = document.createElement("small"); small.textContent = s.note; text.appendChild(small); }
    row.append(box, text);
    body.appendChild(row);
    switches.push(box);
  });
  heading(body, "Where studies disagree (★ = recommended)", "star");
  cat.evidence.forEach((r, i) => {
    const div = document.createElement("div");
    div.className = "evidence";
    const label = document.createElement("label");
    label.textContent = r.label;
    const sel = document.createElement("select");
    r.options.forEach((o, k) => sel.add(new Option((k === r.best ? "★ " : "") + o, k)));
    sel.addEventListener("change", () => send({ type: "evidence", index: i, option: +sel.value }));
    div.append(label, sel);
    body.appendChild(div);
    evidence.push(sel);
  });
  heading(body, "Fixed: measured or from the paper (not adjustable)");
  for (const f of cat.fixed) {
    const div = document.createElement("div");
    div.className = "fixed";
    div.textContent = `${f.name}: ${f.value}`;
    const src = document.createElement("small");
    src.textContent = f.source;
    div.appendChild(src);
    body.appendChild(div);
  }
}

function applyState(st) {
  for (const [key, v] of Object.entries(st.params)) {
    const c = controls[key];
    if (!c) continue;
    if (document.activeElement !== c.input) c.input.value = v;
    c.val.textContent = fmtValue(c.p, v);
  }
  st.switches.forEach((on, i) => { switches[i].checked = on; });
  st.evidence.forEach((k, i) => { if (k >= 0) evidence[i].value = k; });
}

// ------------------------------------------------------------ messages from the simulation
worker.onmessage = (e) => {
  const m = e.data;
  if (m.type === "status") {
    $("loadingText").textContent = m.text;
  } else if (m.type === "error") {
    $("loading").hidden = false;
    $("loadingText").textContent = "Something went wrong: " + m.text;
  } else if (m.type === "catalog") {
    buildControls(JSON.parse(m.catalog));
    applyState(JSON.parse(m.state));
    $("loading").hidden = true;
  } else if (m.type === "state") {
    applyState(JSON.parse(m.state));
  } else if (m.type === "frame") {
    onFrame(m);
  }
};

function onFrame(m) {
  const meta = JSON.parse(m.meta);
  if (meta.world !== worldId) { worldId = meta.world; rows = []; lastT = null; view.cx = null; }
  if (meta.focus && !lastFocus) view.cx = null;
  lastFocus = meta.focus;
  for (const r of meta.rows) rows.push(r);
  const now = performance.now();
  if (lastT === null) { lastT = meta.t; lastWall = now; }
  else if (now - lastWall > 500) {
    const rate = ((meta.t - lastT) * 60) / ((now - lastWall) / 1000);
    speedNow = speedNow ? 0.6 * speedNow + 0.4 * rate : rate;
    lastT = meta.t; lastWall = now;
  }
  frame = { meta, ground: new Uint8ClampedArray(m.ground), slime: new Uint8ClampedArray(m.slime),
    rods: new Float32Array(m.rods), kind: new Uint8Array(m.kind), nodes: new Float32Array(m.nodes),
    colours: new Uint8Array(m.colours), killing: new Uint8Array(m.killing), spores: new Float32Array(m.spores) };
  requestDraw();
}

// ------------------------------------------------------------ drawing the world
function requestDraw() {
  if (drawPending) return;
  drawPending = true;
  const draw = () => {
    if (!drawPending) return;
    drawPending = false;
    drawWorld(); drawGraph(); drawText();
  };
  requestAnimationFrame(draw);
  setTimeout(draw, 250);          // in case the browser holds back animation frames
}

// The view: a square `span` µm wide around (cx, cy), wrap-around safe (zoom and pan; B95).
const view = { cx: null, cy: null, span: null, box: null };
const SCENE_HINTS = {
  world: "Two colonies grow; hunters arrive over the first 10 h and follow slime highways.",
  attack: "A grown colony; four drops of 60 hunters at its edge invade, kill (white rims) and ripple on the remains.",
  swarm: "370 cells on bare ground, biology at real speed: streams form; white dot = leading pole, orange = just reversed.",
  ripple: "1,000 cells on prey remains: waves travel left-right; reversals (orange) gather where waves collide.",
};

function fitView(box, focus) {
  view.box = box;
  if (focus) { [view.cx, view.cy, view.span] = focus; view.span = Math.min(view.span, box); }
  else { view.cx = view.cy = box / 2; view.span = box; }
}

function wrapView() {
  view.cx = ((view.cx % view.box) + view.box) % view.box;
  view.cy = ((view.cy % view.box) + view.box) % view.box;
}

function mapper(S) {
  wrapView();
  const { cx, cy, span, box } = view, k = S / span, h = span / 2;
  const wrap = (d) => d - box * Math.round(d / box);
  return { k, X: (x) => (wrap(x - cx) + h) * k, Y: (y) => S - (wrap(y - cy) + h) * k };
}

function blitImage(ctx, canvas, bytes, n, S) {
  canvas.width = canvas.height = n;
  canvas.getContext("2d").putImageData(new ImageData(bytes, n, n), 0, 0);
  ctx.imageSmoothingEnabled = true;
  const { cx, cy, span, box } = view, k = S / span, size = box * k;
  const x0 = (span / 2 - cx) * k, y0 = S - (box - cy + span / 2) * k;     // where the world's corner lands
  for (const i of [-1, 0, 1]) for (const j of [-1, 0, 1]) {
    const x = x0 + i * size, y = y0 + j * size;
    if (x < S && x + size > 0 && y < S && y + size > 0) ctx.drawImage(canvas, x, y, size, size);
  }
}

function cellPath(nodes, i, M, S) {
  // break the line where a cell crosses the world's wrap-around edge or the view's own seam
  const p = new Path2D();
  let px = 0, py = 0;
  for (let j = 0; j < 10; j++) {
    const X = M.X(nodes[(i * 10 + j) * 2]), Y = M.Y(nodes[(i * 10 + j) * 2 + 1]);
    if (j === 0 || Math.abs(X - px) > S / 4 || Math.abs(Y - py) > S / 4) p.moveTo(X, Y);
    else p.lineTo(X, Y);
    px = X; py = Y;
  }
  return p;
}

function drawWorld() {
  const f = frame;
  if (!f) return;
  const canvas = $("world"), ctx = canvas.getContext("2d"), S = canvas.width;
  const box = f.meta.box, half = box / 2;
  if (view.box !== box || view.cx === null) fitView(box, f.meta.focus);
  const M = mapper(S), sc = M.k;
  ctx.fillStyle = "#fffaea"; ctx.fillRect(0, 0, S, S);
  blitImage(ctx, groundC, f.ground, f.meta.ground_n, S);
  blitImage(ctx, slimeC, f.slime, f.meta.slime_n, S);
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  ctx.fillStyle = COL.spore; ctx.strokeStyle = COL.sporeEdge; ctx.lineWidth = 1;
  for (let i = 0; i < f.spores.length; i += 2) {
    ctx.beginPath(); ctx.arc(M.X(f.spores[i]), M.Y(f.spores[i + 1]), Math.max(2, 0.75 * sc), 0, 2 * Math.PI);
    ctx.fill(); ctx.stroke();
  }
  const paths = [new Path2D(), new Path2D(), new Path2D()];
  const r = f.rods;
  for (let i = 0; i < f.kind.length; i++) {
    const x0 = r[4 * i], y0 = r[4 * i + 1], x1 = r[4 * i + 2], y1 = r[4 * i + 3];
    if (Math.abs(x1 - x0) > half || Math.abs(y1 - y0) > half) continue;
    const X0 = M.X(x0), X1 = M.X(x1), Y0 = M.Y(y0), Y1 = M.Y(y1);
    if (Math.abs(X1 - X0) > S / 2 || Math.abs(Y1 - Y0) > S / 2) continue;   // split by the view's edge
    paths[f.kind[i]].moveTo(X0, Y0);
    paths[f.kind[i]].lineTo(X1, Y1);
  }
  ctx.lineWidth = Math.max(1, sc * 1.0);
  [COL.ecoli, COL.dormant, COL.dead].forEach((c, k) => { ctx.strokeStyle = c; ctx.stroke(paths[k]); });
  const n = f.killing.length, w = Math.max(1, 0.7 * sc), cells = [];
  for (let i = 0; i < n; i++) cells.push(cellPath(f.nodes, i, M, S));
  ctx.strokeStyle = COL.rim;
  ctx.lineWidth = w + Math.max(4, 0.8 * w);
  for (let i = 0; i < n; i++) if (f.killing[i]) ctx.stroke(cells[i]);
  ctx.lineWidth = w;
  for (let i = 0; i < n; i++) {
    const c = f.colours;
    ctx.strokeStyle = `rgb(${c[3 * i]},${c[3 * i + 1]},${c[3 * i + 2]})`;
    ctx.stroke(cells[i]);
  }
  const poles = new Path2D(), pr = Math.max(1.5, 0.8 * w);
  for (let i = 0; i < n; i++) {
    const x = M.X(f.nodes[i * 20]), y = M.Y(f.nodes[i * 20 + 1]);
    poles.moveTo(x + pr, y);
    poles.arc(x, y, pr, 0, 2 * Math.PI);
  }
  ctx.fillStyle = COL.pole;
  ctx.fill(poles);
  const dpr = window.devicePixelRatio || 1, span = view.span;
  const len = span > 80 ? 20 : span > 30 ? 10 : 5, px = len * sc;
  ctx.fillStyle = "#1e1e1e";
  ctx.fillRect(S - 16 * dpr - px, S - 16 * dpr, px, 4 * dpr);
  ctx.font = `${12 * dpr}px "Segoe UI", system-ui, sans-serif`;
  ctx.textAlign = "center";
  ctx.fillText(`${len} µm`, S - 16 * dpr - px / 2, S - 22 * dpr);
}

// zoom with the wheel around the pointer, drag to move, double-click to fit
(function zoomAndPan() {
  const canvas = $("world");
  let drag = null;
  const toWorld = (e) => {
    const r = canvas.getBoundingClientRect(), fx = (e.clientX - r.left) / r.width, fy = (e.clientY - r.top) / r.height;
    return [view.cx + (fx - 0.5) * view.span, view.cy - (fy - 0.5) * view.span];
  };
  canvas.addEventListener("wheel", (e) => {
    if (view.box === null) return;
    e.preventDefault();
    const [wx, wy] = toWorld(e), factor = e.deltaY < 0 ? 0.8 : 1.25;
    const span = Math.min(view.box, Math.max(view.box / 16, view.span * factor));
    const s = span / view.span;
    view.cx = wx + (view.cx - wx) * s; view.cy = wy + (view.cy - wy) * s; view.span = span;
    requestDraw();
  }, { passive: false });
  canvas.addEventListener("pointerdown", (e) => { drag = [e.clientX, e.clientY]; canvas.setPointerCapture(e.pointerId); });
  canvas.addEventListener("pointermove", (e) => {
    if (!drag || view.box === null) return;
    const r = canvas.getBoundingClientRect(), k = view.span / r.width;
    view.cx -= (e.clientX - drag[0]) * k; view.cy += (e.clientY - drag[1]) * k;
    drag = [e.clientX, e.clientY];
    requestDraw();
  });
  canvas.addEventListener("pointerup", () => { drag = null; });
  canvas.addEventListener("dblclick", () => { if (frame) { fitView(frame.meta.box, frame.meta.focus); requestDraw(); } });
})();

// ------------------------------------------------------------ the counts graph
function niceTop(v) {
  const p = Math.pow(10, Math.floor(Math.log10(Math.max(v, 1))));
  for (const m of [1, 2, 5, 10]) if (m * p >= v) return m * p;
  return 10 * p;
}

function drawGraph() {
  const c = $("graph"), ctx = c.getContext("2d"), W = c.width, H = c.height, dpr = window.devicePixelRatio || 1;
  ctx.fillStyle = "#1a1a1f";
  ctx.fillRect(0, 0, W, H);
  if (rows.length < 2) return;
  const L = 52 * dpr, R = W - 12 * dpr, T = 28 * dpr, B = H - 22 * dpr;
  const tEnd = Math.max(rows[rows.length - 1][0], 1);
  let peak = 1;
  for (const r of rows) peak = Math.max(peak, r[1], r[3]);
  const top = niceTop(peak * 1.05);
  ctx.font = `${11 * dpr}px "Segoe UI", system-ui, sans-serif`;
  ctx.fillStyle = COL.axis; ctx.strokeStyle = COL.grid; ctx.lineWidth = 1;
  for (const frac of [0, 0.5, 1]) {
    const y = B - frac * (B - T);
    ctx.beginPath(); ctx.moveTo(L, y); ctx.lineTo(R, y); ctx.stroke();
    ctx.textAlign = "right"; ctx.fillText((top * frac).toLocaleString(), L - 6 * dpr, y + 4 * dpr);
    ctx.textAlign = "center";
    ctx.fillText(`${(tEnd * frac).toFixed(tEnd >= 10 ? 0 : 1)} h`, L + frac * (R - L), H - 6 * dpr);
  }
  const series = [[1, "E. coli", COL.ecoli, 2], [2, "dormant", COL.dormant, 1],
    [3, "M. xanthus", COL.myxo, 2], [4, "starving", COL.starving, 1]];
  const stride = Math.max(1, Math.floor(rows.length / (R - L)));
  let xLegend = 10 * dpr;
  const last = rows[rows.length - 1];
  for (const [col, name, colour, width] of series) {
    ctx.strokeStyle = colour; ctx.lineWidth = width * dpr;
    ctx.beginPath();
    for (let i = 0; i < rows.length; i += stride) {
      const x = L + (rows[i][0] / tEnd) * (R - L), y = B - (rows[i][col] / top) * (B - T);
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.stroke();
    ctx.fillStyle = colour; ctx.textAlign = "left";
    const label = `${name} ${Math.round(last[col]).toLocaleString()}`;
    ctx.fillText(label, xLegend, 16 * dpr);
    xLegend += ctx.measureText(label).width + 16 * dpr;
  }
  ctx.fillStyle = COL.axis; ctx.textAlign = "right";
  ctx.fillText("cells vs hours of biology", R, 16 * dpr);
}

function drawText() {
  if (!frame) return;
  const m = frame.meta;
  $("clock").textContent = `${m.bio_h.toFixed(1)} h of biology`;
  $("counts").textContent = `E. coli ${m.n_ecoli.toLocaleString()} (${m.dormant.toLocaleString()} dormant) · ` +
    `M. xanthus ${m.n_myxo.toLocaleString()} (${m.killing} killing, ${m.starving} starving)`;
  $("status").textContent = running
    ? `now ×${speedNow < 10 ? speedNow.toFixed(1) : Math.round(speedNow)} real time · ${m.ms_per_step.toFixed(0)} ms per 0.3 s step`
    : "paused";
}

// ------------------------------------------------------------ buttons and speed
function speedLabel(i) {
  const w = SPEEDS[i];
  return w === 0 ? "as fast as possible" : w === 1 ? "×1 = real time" : `×${w} real time`;
}
$("speed").addEventListener("input", () => {
  $("speedText").textContent = speedLabel(+$("speed").value);
  send({ type: "speed", warp: SPEEDS[+$("speed").value] });
});
$("runBtn").addEventListener("click", () => {
  running = !running;
  $("runBtn").textContent = running ? "Pause" : "Run";
  send({ type: "run", on: running });
});
$("resetBtn").addEventListener("click", () => send({ type: "reset" }));
$("scene").addEventListener("change", () => {
  const sc = $("scene").value;
  $("sceneHint").textContent = SCENE_HINTS[sc];
  lastFocus = null;
  send({ type: "scene", scene: sc });
});
$("sceneHint").textContent = SCENE_HINTS.world;
$("recBtn").addEventListener("click", () => send({ type: "recommended" }));
$("settingsBtn").addEventListener("click", () => { $("overlay").hidden = false; });
$("closeBtn").addEventListener("click", () => { $("overlay").hidden = true; });
document.addEventListener("keydown", (e) => { if (e.key === "Escape") $("overlay").hidden = true; });

$("speedText").textContent = speedLabel(+$("speed").value);
window.addEventListener("resize", layout);
layout();
