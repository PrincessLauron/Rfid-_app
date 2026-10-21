import { WebSerialTransport } from './transport/webserial.js';
import { createDemoTransport } from './demo.js';
import { ReaderSession, NoResponseError } from './reader/session.js';
import { TagReader, TagTable } from './reader/reading.js';
import { TransportLog } from './log.js';
import { cmd } from './protocol/commands.js';
import { describeError } from './ui/dom.js';
import { mountRead } from './ui/read.js';
import { mountSettings } from './ui/settings.js';
import { mountMemory } from './ui/memory.js';
import { mountLog } from './ui/logview.js';
import { installRegionGate } from './ui/region.js';

const $ = (id) => document.getElementById(id);
const app = {
  log: new TransportLog(), table: new TagTable(), session: null, reader: null,
  setConnected: [], onTag: null, onReadingChanged: null,
  showError(e) { banner(describeError(e), e instanceof NoResponseError ? 'bad' : e?.status === 0x0504 ? 'warn' : 'bad'); },
  clearBanner() { $('banner').hidden = true; },
};
const banner = (text, kind = 'bad') => { const b = $('banner'); b.textContent = text; b.className = `banner ${kind === 'warn' ? '' : 'bad'}`; b.hidden = false; };

mountRead($('tab-read'), app);
mountSettings($('tab-settings'), app);
mountMemory($('tab-memory'), app);
mountLog($('tab-log'), app);
installRegionGate(app);

for (const tab of document.querySelectorAll('[role=tab]')) {
  tab.addEventListener('click', () => {
    document.querySelectorAll('[role=tab]').forEach((t) => t.setAttribute('aria-selected', String(t === tab)));
    document.querySelectorAll('[role=tabpanel]').forEach((p) => { p.hidden = p.id !== `tab-${tab.dataset.tab}`; });
  });
}

let tempTimer = null;
async function setConnected(on, text) {
  $('btn-connect').hidden = $('btn-demo').hidden = on;
  $('btn-disconnect').hidden = !on;
  $('status').textContent = text;
  $('status').classList.toggle('ok', on);
  clearInterval(tempTimer);
  for (const fn of app.setConnected) await fn(on);
  if (on) tempTimer = setInterval(updateTemp, 5000);
}

async function updateTemp() {
  if (!app.session || app.reader.running) return;
  try {
    const t = await app.session.send(cmd.temperature());
    $('status').textContent = `${$('status').dataset.base} · ${t} °C`;
  } catch (e) { app.showError(e); }
}

async function connect(transport) {
  app.clearBanner();
  app.session = new ReaderSession(transport, { log: app.log });
  app.reader = new TagReader(app.session);
  app.reader.onTag((tag) => app.onTag?.(tag));
  app.session.on('disconnect', async () => {
    app.reader.running = false;
    app.onReadingChanged?.(false);
    banner('Reader disconnected.', 'bad');
    await setConnected(false, 'Not connected');
  });
  try {
    const info = await app.session.connect();
    const base = `Connected · ${info.serial ?? 'reader'} · fw ${info.firmware} · ${app.session.baud} baud`;
    $('status').dataset.base = base;
    await setConnected(true, base);
    updateTemp();
    // A freshly powered M7E has no region, so RF stays off (AFE_NOT_ON) until one is chosen.
    await app.ensureRegion().catch((e) => app.showError(e));
  } catch (e) {
    app.showError(e);
    await transport.close().catch(() => {});
    await setConnected(false, 'Not connected');
  }
}

$('btn-connect').addEventListener('click', async () => {
  if (!WebSerialTransport.supported) return banner('This browser has no Web Serial support. Use Chrome or Edge, or try Demo mode.', 'bad');
  let transport;
  const asked = performance.now();
  try { transport = await WebSerialTransport.request(); } catch (e) {
    // A person needs more than ~400 ms to cancel the chooser; an instant NotFoundError means
    // this browser (e.g. an embedded app browser) has Web Serial but never showed a chooser.
    if (e?.name === 'NotFoundError' && performance.now() - asked < 400) {
      return banner('No serial port chooser appeared. This embedded browser cannot pick ports: open http://localhost:8080 in Chrome or Edge.', 'bad');
    }
    if (e?.name === 'NotFoundError') return; // user closed the chooser
    return app.showError(e);
  }
  await connect(transport);
});
$('btn-demo').addEventListener('click', () => connect(createDemoTransport()));
$('btn-disconnect').addEventListener('click', async () => {
  try { if (app.reader.running) await app.reader.stop(); } catch { /* ignore */ }
  await app.session.disconnect();
  await setConnected(false, 'Not connected');
});

if (!WebSerialTransport.supported) banner('This browser has no Web Serial support. Use Chrome or Edge for real readers; Demo mode works anywhere.', 'warn');
