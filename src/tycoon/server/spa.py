"""Embedded single-page application served at the root URL."""

SPA_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Tycoon Dashboard</title>
<style>
  :root {
    --bg: #0f1117;
    --surface: #1a1d27;
    --border: #2a2d3a;
    --text: #e1e4ed;
    --text-dim: #8b8fa3;
    --accent: #6c7aff;
    --green: #3dd68c;
    --red: #f5555d;
    --yellow: #f0c362;
    --font-mono: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
  }
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
  }
  header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 2rem;
    border-bottom: 1px solid var(--border);
    background: var(--surface);
  }
  header h1 { font-size: 1.25rem; font-weight: 600; }
  header .status-badge {
    font-size: 0.75rem;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    background: var(--green);
    color: #000;
    font-weight: 600;
  }
  header .status-badge.offline { background: var(--red); color: #fff; }
  main {
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-template-rows: auto 1fr;
    gap: 1rem;
    padding: 1.5rem 2rem;
    max-width: 1400px;
    margin: 0 auto;
    min-height: calc(100vh - 60px);
  }
  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.25rem;
  }
  .card h2 {
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-dim);
    margin-bottom: 1rem;
  }
  /* Services card */
  .services-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.5rem;
  }
  .svc {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.6rem 0.8rem;
    border-radius: 6px;
    background: var(--bg);
    font-size: 0.85rem;
    cursor: pointer;
    transition: border-color 0.15s;
    border: 1px solid transparent;
  }
  .svc:hover { border-color: var(--accent); }
  .svc .dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    margin-right: 0.5rem;
    flex-shrink: 0;
  }
  .svc .dot.up { background: var(--green); }
  .svc .dot.down { background: var(--red); }
  .svc .name { flex: 1; }
  .svc .port { color: var(--text-dim); font-family: var(--font-mono); font-size: 0.8rem; }
  /* Database card */
  .db-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
  .db-table th { text-align: left; color: var(--text-dim); padding: 0.4rem 0.6rem; border-bottom: 1px solid var(--border); }
  .db-table td { padding: 0.4rem 0.6rem; border-bottom: 1px solid var(--border); font-family: var(--font-mono); }
  /* Actions card */
  .actions { display: flex; flex-direction: column; gap: 0.5rem; }
  .actions button {
    padding: 0.6rem 1rem;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: var(--bg);
    color: var(--text);
    font-size: 0.85rem;
    cursor: pointer;
    text-align: left;
    transition: border-color 0.15s, background 0.15s;
  }
  .actions button:hover { border-color: var(--accent); background: #1e2133; }
  .actions button:disabled { opacity: 0.5; cursor: not-allowed; }
  /* Terminal card */
  .terminal-card { grid-column: 1 / -1; display: flex; flex-direction: column; }
  #terminal {
    flex: 1;
    min-height: 250px;
    max-height: 400px;
    overflow-y: auto;
    background: #000;
    border-radius: 6px;
    padding: 0.75rem;
    font-family: var(--font-mono);
    font-size: 0.8rem;
    line-height: 1.5;
    color: #ccc;
    white-space: pre-wrap;
    word-break: break-all;
  }
  #terminal .log-line { margin: 0; }
  /* Iframe viewer */
  .iframe-overlay {
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.8);
    z-index: 100;
    padding: 2rem;
  }
  .iframe-overlay.active { display: flex; flex-direction: column; }
  .iframe-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
    color: #fff;
  }
  .iframe-bar button {
    background: var(--red);
    border: none;
    color: #fff;
    padding: 0.4rem 1rem;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.85rem;
  }
  .iframe-overlay iframe {
    flex: 1;
    border: none;
    border-radius: 6px;
    width: 100%;
  }
</style>
</head>
<body>
<header>
  <h1>Tycoon Dashboard</h1>
  <span class="status-badge" id="global-status">loading</span>
</header>
<main>
  <div class="card">
    <h2>Services</h2>
    <div class="services-grid" id="services"></div>
  </div>
  <div class="card">
    <h2>Databases</h2>
    <table class="db-table">
      <thead><tr><th>Database</th><th>Size</th><th>Tables</th></tr></thead>
      <tbody id="db-info"></tbody>
    </table>
    <h2 style="margin-top:1rem">dbt Last Run</h2>
    <div id="dbt-info" style="font-size:0.85rem;color:var(--text-dim)">--</div>
  </div>
  <div class="card">
    <h2>Run</h2>
    <div class="actions">
      <button id="btn-pipeline" onclick="runPipeline()">Run dlt pipeline</button>
      <button id="btn-dbt" onclick="runDbt()">Run dbt build</button>
    </div>
  </div>
  <div class="card terminal-card">
    <h2>Output</h2>
    <div id="terminal"></div>
  </div>
</main>
<div class="iframe-overlay" id="iframe-overlay">
  <div class="iframe-bar">
    <span id="iframe-title"></span>
    <button onclick="closeViewer()">Close</button>
  </div>
  <iframe id="viewer-iframe"></iframe>
</div>
<script>
const API = window.location.origin;
let ws = null;

async function fetchStatus() {
  try {
    const r = await fetch(API + '/api/status');
    const d = await r.json();
    renderServices(d.services || {});
    renderDatabases(d.databases || {});
    renderDbt(d.dbt || {});
    const badge = document.getElementById('global-status');
    badge.textContent = 'live';
    badge.classList.remove('offline');
    const busy = d.busy || false;
    document.getElementById('btn-pipeline').disabled = busy;
    document.getElementById('btn-dbt').disabled = busy;
  } catch {
    document.getElementById('global-status').textContent = 'offline';
    document.getElementById('global-status').classList.add('offline');
  }
}

function renderServices(svcs) {
  const el = document.getElementById('services');
  el.innerHTML = '';
  for (const [name, info] of Object.entries(svcs)) {
    const div = document.createElement('div');
    div.className = 'svc';
    div.onclick = () => openViewer(name, info.port);
    div.innerHTML = '<span class="dot ' + (info.healthy ? 'up' : 'down') + '"></span>'
      + '<span class="name">' + name + '</span>'
      + '<span class="port">:' + info.port + '</span>';
    el.appendChild(div);
  }
}

function renderDatabases(dbs) {
  const el = document.getElementById('db-info');
  el.innerHTML = '';
  for (const [name, info] of Object.entries(dbs)) {
    const tr = document.createElement('tr');
    tr.innerHTML = '<td>' + name + '</td>'
      + '<td>' + (info.size_mb !== null ? info.size_mb.toFixed(1) + ' MB' : '--') + '</td>'
      + '<td>' + (info.table_count !== null ? info.table_count : '--') + '</td>';
    el.appendChild(tr);
  }
}

function renderDbt(dbt) {
  const el = document.getElementById('dbt-info');
  if (!dbt || !dbt.elapsed_time) { el.textContent = 'No results found'; return; }
  el.innerHTML = 'Elapsed: ' + dbt.elapsed_time.toFixed(1) + 's | '
    + 'Pass: ' + (dbt.pass || 0) + ' | '
    + 'Error: ' + (dbt.error || 0) + ' | '
    + 'Warn: ' + (dbt.warn || 0);
}

function appendLog(line) {
  const term = document.getElementById('terminal');
  const p = document.createElement('div');
  p.className = 'log-line';
  p.textContent = line;
  term.appendChild(p);
  term.scrollTop = term.scrollHeight;
}

function connectWS(runId) {
  if (ws) { ws.close(); }
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  ws = new WebSocket(proto + '//' + location.host + '/ws/logs/' + runId);
  ws.onmessage = (e) => appendLog(e.data);
  ws.onclose = () => appendLog('[stream closed]');
}

async function runPipeline() {
  document.getElementById('terminal').innerHTML = '';
  try {
    const r = await fetch(API + '/api/run/pipeline/default', { method: 'POST' });
    const d = await r.json();
    if (d.run_id) { connectWS(d.run_id); }
    else { appendLog('Error: ' + (d.detail || JSON.stringify(d))); }
  } catch (e) { appendLog('Request failed: ' + e); }
}

async function runDbt() {
  document.getElementById('terminal').innerHTML = '';
  try {
    const r = await fetch(API + '/api/run/dbt', { method: 'POST' });
    const d = await r.json();
    if (d.run_id) { connectWS(d.run_id); }
    else { appendLog('Error: ' + (d.detail || JSON.stringify(d))); }
  } catch (e) { appendLog('Request failed: ' + e); }
}

function openViewer(name, port) {
  const url = 'http://localhost:' + port;
  document.getElementById('iframe-title').textContent = name + ' (:' + port + ')';
  document.getElementById('viewer-iframe').src = url;
  document.getElementById('iframe-overlay').classList.add('active');
}

function closeViewer() {
  document.getElementById('iframe-overlay').classList.remove('active');
  document.getElementById('viewer-iframe').src = '';
}

fetchStatus();
setInterval(fetchStatus, 5000);
</script>
</body>
</html>
"""
