// worker.js — runs the MyxoHunt simulation (Python, via Pyodide) in the background, so the page's
// sliders stay responsive (B94). It steps the world in slices of computing time and sends each
// frame to the page as plain arrays.
importScripts("https://cdn.jsdelivr.net/pyodide/v0.27.2/full/pyodide.js");

const BUDGET_MS = 90;          // computing per slice; a frame is sent after each slice (~10 a second)
const DT = 0.005;              // real minutes per tick (settings.dt)
let ctl = null, running = true, warp = 0, debt = 0, last = 0;

function status(text) { postMessage({ type: "status", text }); }

async function boot() {
  try {
    status("Loading Python in your browser…");
    const py = await loadPyodide();
    status("Loading numpy and scipy (first visit only, ~25 MB)…");
    await py.loadPackage(["numpy", "scipy"]);
    status("Loading the simulation…");
    const fresh = { cache: "no-cache" };          // always check for updated simulation files
    const files = await (await fetch("py/manifest.json", fresh)).json();
    py.FS.mkdirTree("/sim");
    for (const name of files) {
      py.FS.writeFile("/sim/" + name, await (await fetch("py/" + name, fresh)).text());
    }
    py.runPython("import sys; sys.path.insert(0, '/sim')");
    status("Building the world…");
    ctl = py.runPython("import web_controller; web_controller.Controller()");
    postMessage({ type: "catalog", catalog: ctl.catalog_json(), state: ctl.state_json() });
    last = performance.now();
    loop();
  } catch (err) {
    postMessage({ type: "error", text: String(err) });
  }
}

function asBuffer(bytes) {
  // A Uint8Array copy of a Python bytes object, as a whole ArrayBuffer we can hand over.
  return bytes.byteOffset === 0 && bytes.byteLength === bytes.buffer.byteLength ? bytes.buffer : bytes.slice().buffer;
}

function sendFrame() {
  const proxy = ctl.frame();
  const d = proxy.toJs({ dict_converter: Object.fromEntries });
  proxy.destroy();
  const msg = { type: "frame", meta: d.meta };
  const transfer = [];
  for (const k of ["ground", "slime", "rods", "kind", "nodes", "colours", "killing", "spores"]) {
    msg[k] = asBuffer(d[k]);
    transfer.push(msg[k]);
  }
  postMessage(msg, transfer);
}

function loop() {
  try {
    const now = performance.now();
    const wall = (now - last) / 1000;
    last = now;
    if (running) {
      if (warp === 0) {
        ctl.run(BUDGET_MS, 0);
      } else {
        debt = Math.min(debt + (warp * wall) / 60, 200 * DT);
        if (debt >= DT) debt -= ctl.run(BUDGET_MS, debt);
      }
    }
    sendFrame();
  } catch (err) {
    postMessage({ type: "error", text: String(err) });
    return;
  }
  setTimeout(loop, running ? 0 : 120);
}

onmessage = (e) => {
  const m = e.data;
  if (!ctl) return;
  try {
    switch (m.type) {
      case "param": ctl.set_param(m.key, m.value); break;
      case "switch": ctl.set_switch(m.index, m.on); break;
      case "evidence": ctl.set_evidence(m.index, m.option); break;
      case "reset": ctl.reset(); break;
      case "recommended": ctl.recommended(); break;
      case "run": running = m.on; break;
      case "speed": warp = m.warp; debt = 0; break;
    }
    if (["param", "switch", "evidence", "reset", "recommended"].includes(m.type)) {
      postMessage({ type: "state", state: ctl.state_json() });
    }
  } catch (err) {
    postMessage({ type: "error", text: String(err) });
  }
};

boot();
