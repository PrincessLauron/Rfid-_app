import { h, describeError } from './dom.js';
import { cmdTag, BANK, hexToBytes } from '../protocol/commands.js';

export function mountMemory(root, app) {
  const epc = h('input', { type: 'text', placeholder: 'EPC of the target tag (hex)', 'aria-label': 'Target EPC', class: 'mono' });
  const pick = h('select', { 'aria-label': 'Choose from tags seen' });
  const password = h('input', { type: 'text', value: '00000000', size: 10, class: 'mono', 'aria-label': 'Access password (hex)' });
  const enable = h('input', { type: 'checkbox', id: 'enable-writes' });
  const out = h('pre', { class: 'mono note', role: 'status' });
  const newEpc = h('input', { type: 'text', placeholder: 'new EPC (hex, whole words)', class: 'mono' });
  const addr = h('input', { type: 'number', value: 0, min: 0, style: 'width:6em', 'aria-label': 'Word address' });
  const words = h('input', { type: 'number', value: 2, min: 1, max: 32, style: 'width:5em', 'aria-label': 'Word count' });
  const data = h('input', { type: 'text', placeholder: 'data (hex, whole words)', class: 'mono' });
  const area = h('select', {}, ['epc', 'user', 'tid', 'access', 'kill'].map((a) => h('option', { value: a }, a)));

  const refreshPick = () => pick.replaceChildren(h('option', { value: '' }, 'tags seen…'), ...app.table.list().slice(0, 100).map((r) => h('option', { value: r.epc }, r.epc)));
  pick.addEventListener('focus', refreshPick);
  pick.addEventListener('change', () => { if (pick.value) epc.value = pick.value; });

  const pw = () => { const b = hexToBytes(password.value); if (b.length !== 4) throw new Error('password must be 4 bytes (8 hex digits)'); return ((b[0] << 24) | (b[1] << 16) | (b[2] << 8) | b[3]) >>> 0; };
  const run = (label, needsWrite, fn) => async () => {
    try {
      if (needsWrite && !enable.checked) throw new Error('Turn on "Enable writes" first.');
      if (!epc.value.trim()) throw new Error('Enter the EPC of the tag to operate on.');
      if (app.reader.running) await app.reader.stop();
      out.textContent = `${label}…`;
      out.textContent = `${label}: ${await fn()}`;
      app.clearBanner();
    } catch (e) { out.textContent = ''; app.showError(e); }
  };
  const sure = (msg) => { if (!confirm(msg)) throw new Error('Cancelled.'); };
  const target = () => epc.value.replace(/\s+/g, '').toUpperCase();

  root.append(
    h('div', { class: 'card' }, h('h3', {}, 'Target tag'),
      h('div', { class: 'row' }, epc, pick, h('label', {}, 'Password', password)),
      h('div', { class: 'row' }, h('label', {}, enable, 'Enable writes'),
        h('span', { class: 'note' }, 'Every operation is aimed at the EPC above, so other tags in range are not touched.'))),
    h('div', { class: 'card' }, h('h3', {}, 'Write EPC'),
      h('div', { class: 'row' }, newEpc, h('button', { class: 'danger', onclick: run('Write EPC', true, async () => {
        sure(`Change EPC of ${target()} to ${newEpc.value.trim().toUpperCase()}?`);
        await app.session.send(cmdTag.writeEpc({ epc: target(), newEpc: newEpc.value, password: pw() }));
        epc.value = newEpc.value.replace(/\s+/g, '').toUpperCase();
        return `done. Target is now ${epc.value}. Read again to confirm.`;
      }) }, 'Write EPC'))),
    h('div', { class: 'card' }, h('h3', {}, 'User memory'),
      h('div', { class: 'row' }, h('label', {}, 'Word address', addr), h('label', {}, 'Words', words),
        h('button', { onclick: run('Read user memory', false, async () => app.session.send(cmdTag.readData({ epc: target(), bank: BANK.USER, wordAddress: Number(addr.value), wordCount: Number(words.value), password: pw() }))) }, 'Read')),
      h('div', { class: 'row' }, data, h('button', { class: 'danger', onclick: run('Write user memory', true, async () => {
        const want = data.value.replace(/\s+/g, '').toUpperCase();
        sure(`Write ${want} to user memory word ${addr.value} of ${target()}?`);
        await app.session.send(cmdTag.writeData({ epc: target(), bank: BANK.USER, wordAddress: Number(addr.value), dataHex: want, password: pw() }));
        const back = await app.session.send(cmdTag.readData({ epc: target(), bank: BANK.USER, wordAddress: Number(addr.value), wordCount: want.length / 4, password: pw() }));
        if (back !== want) throw new Error(`Read-back mismatch: wrote ${want}, read ${back}.`);
        return `written and verified (${back}).`;
      }) }, 'Write'))),
    h('div', { class: 'card' }, h('h3', {}, 'Lock'),
      h('div', { class: 'row' }, area,
        h('button', { class: 'danger', onclick: run('Lock', true, async () => {
          sure(`Lock the ${area.value} area of ${target()}? Writes will then need the access password.`);
          await app.session.send(cmdTag.lock({ epc: target(), area: area.value, locked: true, password: pw() })); return 'locked.';
        }) }, 'Lock'),
        h('button', { class: 'danger', onclick: run('Unlock', true, async () => {
          sure(`Unlock the ${area.value} area of ${target()}?`);
          await app.session.send(cmdTag.lock({ epc: target(), area: area.value, locked: false, password: pw() })); return 'unlocked.';
        }) }, 'Unlock')),
      h('p', { class: 'note' }, 'Permanent locks are not offered.')),
    out);
}
