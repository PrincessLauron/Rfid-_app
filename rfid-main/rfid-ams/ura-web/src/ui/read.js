import { h, download, describeError } from './dom.js';

export function mountRead(root, app) {
  const start = h('button', { class: 'primary' }, 'Start reading');
  const once = h('button', {}, 'Read once (3 s)');
  const clear = h('button', {}, 'Clear');
  const exportBtn = h('button', {}, 'Export CSV');
  const summary = h('span', { class: 'note' });
  const tbody = h('tbody');
  const table = h('div', { class: 'table-wrap' }, h('table', {}, h('thead', {}, h('tr', {}, ...['EPC', 'Reads', 'RSSI (dBm)', 'Best', 'Ant', 'Freq (kHz)', 'Last seen'].map((t) => h('th', {}, t)))), tbody));
  root.append(h('div', { class: 'row' }, start, once, clear, exportBtn, summary), table);

  let dirty = true;
  const render = () => {
    if (!dirty) return;
    dirty = false;
    const rows = app.table.list();
    summary.textContent = `${rows.length} unique tag${rows.length === 1 ? '' : 's'}${app.table.dropped ? ` (${app.table.dropped} new tags ignored: table full)` : ''}`;
    tbody.replaceChildren(...rows.slice(0, 500).map((r) => h('tr', {},
      h('td', { class: 'mono' }, r.epc), h('td', { class: 'num' }, r.count), h('td', { class: 'num' }, r.rssi ?? ''),
      h('td', { class: 'num' }, Number.isFinite(r.bestRssi) ? r.bestRssi : ''), h('td', { class: 'num' }, r.antenna ?? ''),
      h('td', { class: 'num' }, r.frequencyKhz ?? ''), h('td', {}, new Date(r.lastSeen).toLocaleTimeString()))));
  };
  setInterval(render, 250);
  app.onTag = (tag) => { app.table.add(tag); dirty = true; };

  const setRunning = (running) => {
    start.textContent = running ? 'Stop reading' : 'Start reading';
    start.classList.toggle('danger', running);
    start.classList.toggle('primary', !running);
    once.disabled = running;
  };
  app.onReadingChanged = setRunning;

  start.addEventListener('click', async () => {
    try {
      if (app.reader.running) await app.reader.stop();
      else if (await app.ensureRegion()) await app.reader.start();
      setRunning(app.reader.running);
    } catch (e) { app.showError(e); setRunning(false); }
  });
  once.addEventListener('click', async () => {
    try {
      if (!(await app.ensureRegion())) return;
      setRunning(true);
      await app.reader.readFor(3000);
    } catch (e) { app.showError(e); } finally { setRunning(false); }
  });
  clear.addEventListener('click', () => { app.table.clear(); dirty = true; render(); });
  exportBtn.addEventListener('click', () => download(`tags-${new Date().toISOString().replace(/[:.]/g, '-')}.csv`, app.table.toCsv(), 'text/csv'));
  app.setConnected.push((on) => { start.disabled = once.disabled = !on; if (!on) setRunning(false); });
  start.disabled = once.disabled = true;
  render();
}
