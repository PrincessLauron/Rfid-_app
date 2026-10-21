import { h } from './dom.js';
import { cmd, cmdTag, GEN2, TARGETS, REGIONS, clampPower } from '../protocol/commands.js';

const SESSIONS = ['S0', 'S1', 'S2', 'S3'];
const ENCODINGS = ['FM0', 'M2', 'M4', 'M8'];
const TARIS = ['25 µs', '12.5 µs', '6.25 µs'];
const targetName = (pair) => Object.entries(TARGETS).find(([, v]) => v[0] === pair[0] && v[1] === pair[1])?.[0] ?? 'A';

export function mountSettings(root, app) {
  const region = h('select');
  const power = h('input', { type: 'number', step: '0.25', 'aria-label': 'Read power in dBm' });
  const powerNote = h('span', { class: 'note' });
  const selects = {
    session: h('select', {}, SESSIONS.map((s, i) => h('option', { value: i }, s))),
    target: h('select', {}, Object.keys(TARGETS).map((t) => h('option', { value: t }, t))),
    encoding: h('select', {}, ENCODINGS.map((s, i) => h('option', { value: i }, s))),
    tari: h('select', {}, TARIS.map((s, i) => h('option', { value: i }, s))),
  };
  let limits = { min: 0, max: 3000 };

  const apply = (fn) => async () => { try { await fn(); app.clearBanner(); } catch (e) { app.showError(e); } };
  const reload = async () => {
    const ids = await app.session.send(cmd.availableRegions());
    const current = await app.session.send(cmd.getRegion());
    region.replaceChildren(...ids.map((id) => h('option', { value: id }, REGIONS[id] ?? `Region ${id}`)));
    region.value = String(current);
    limits = await app.session.send(cmd.getReadPowerLimits());
    power.min = limits.min / 100; power.max = limits.max / 100; power.value = limits.current / 100;
    powerNote.textContent = `Allowed ${limits.min / 100}–${limits.max / 100} dBm. Lower power reduces heat.`;
    selects.session.value = await app.session.send(cmdTag.getGen2(GEN2.SESSION));
    selects.target.value = targetName(await app.session.send(cmdTag.getGen2(GEN2.TARGET)));
    selects.encoding.value = await app.session.send(cmdTag.getGen2(GEN2.ENCODING));
    selects.tari.value = await app.session.send(cmdTag.getGen2(GEN2.TARI));
  };

  root.append(
    h('div', { class: 'card' }, h('h3', {}, 'Region'),
      h('div', { class: 'row' }, region, h('button', { onclick: apply(async () => {
        if (!confirm(`Set region to ${region.selectedOptions[0].text}? It must match local radio regulations.`)) return;
        await app.session.send(cmd.setRegion(Number(region.value)));
      }) }, 'Apply'))),
    h('div', { class: 'card' }, h('h3', {}, 'Read power (dBm)'),
      h('div', { class: 'row' }, power, h('button', { onclick: apply(async () => {
        const centi = clampPower(Number(power.value) * 100, limits);
        power.value = centi / 100;
        await app.session.send(cmd.setReadPower(centi));
      }) }, 'Apply'), powerNote)),
    h('div', { class: 'card' }, h('h3', {}, 'Gen2'),
      h('div', { class: 'row' },
        ...Object.entries({ session: 'Session', target: 'Target', encoding: 'Encoding', tari: 'Tari' }).map(([k, label]) => h('label', {}, label, selects[k])),
        h('button', { onclick: apply(async () => {
          await app.session.send(cmdTag.setGen2(GEN2.SESSION, Number(selects.session.value)));
          await app.session.send(cmdTag.setGen2(GEN2.TARGET, TARGETS[selects.target.value]));
          await app.session.send(cmdTag.setGen2(GEN2.ENCODING, Number(selects.encoding.value)));
          await app.session.send(cmdTag.setGen2(GEN2.TARI, Number(selects.tari.value)));
        }) }, 'Apply')),
      h('p', { class: 'note' }, 'Gen2 values are unverified on hardware until the verification checklist passes.')),
    h('div', { class: 'row' }, h('button', { onclick: apply(reload) }, 'Reload from module')),
  );
  app.reloadSettings = reload;
  app.setConnected.push(async (on) => { if (on) { try { await reload(); } catch (e) { app.showError(e); } } });
}
