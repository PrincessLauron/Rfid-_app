import { h } from './dom.js';
import { cmd, REGIONS } from '../protocol/commands.js';

const STORE_KEY = 'ura.lastRegion';
const remembered = () => { try { return localStorage.getItem(STORE_KEY); } catch { return null; } };
const remember = (id) => { try { localStorage.setItem(STORE_KEY, String(id)); } catch { /* storage unavailable */ } };

/**
 * The M7E forgets its region when it loses power, and RF stays off (AFE_NOT_ON) until one is set.
 * app.ensureRegion() resolves true once the module has a region, asking the user with a modal if needed.
 */
export function installRegionGate(app) {
  const select = h('select', { id: 'region-choice', 'aria-label': 'Region' });
  const error = h('p', { class: 'note bad-text', role: 'alert' });
  const apply = h('button', { class: 'primary', type: 'submit' }, 'Set region');
  const later = h('button', { type: 'button' }, 'Not now');
  const dialog = h('dialog', { class: 'modal', 'aria-labelledby': 'region-title' },
    h('form', { method: 'dialog' },
      h('h2', { id: 'region-title' }, 'Choose the reader region'),
      h('p', {}, 'The module has no region, so its radio is off. Pick the region that matches your country\'s radio rules. The module forgets it when unplugged, so this appears after each power-up.'),
      h('div', { class: 'row' }, select),
      error,
      h('div', { class: 'row end' }, later, apply)));
  document.body.append(dialog);

  let regionSet = false;
  let pending = null;

  const finish = (ok) => { const p = pending; pending = null; dialog.close(); p?.(ok); };
  later.addEventListener('click', () => finish(false));
  dialog.addEventListener('cancel', (e) => { e.preventDefault(); finish(false); });
  dialog.addEventListener('submit', async (e) => {
    e.preventDefault();
    apply.disabled = true;
    error.textContent = '';
    try {
      const id = Number(select.value);
      await app.session.send(cmd.setRegion(id));
      remember(id);
      regionSet = true;
      app.clearBanner();
      await app.reloadSettings?.();
      finish(true);
    } catch (err) {
      error.textContent = err?.hint ? `${err.message}. ${err.hint}` : String(err?.message ?? err);
    } finally {
      apply.disabled = false;
    }
  });

  app.ensureRegion = async () => {
    if (regionSet) return true;
    const current = await app.session.send(cmd.getRegion());
    if (current !== 0) { regionSet = true; return true; }
    const ids = await app.session.send(cmd.availableRegions());
    select.replaceChildren(...ids.map((id) => h('option', { value: id }, REGIONS[id] ?? `Region ${id}`)));
    const last = remembered();
    if (last && ids.includes(Number(last))) select.value = last;
    error.textContent = '';
    dialog.showModal();
    return new Promise((resolve) => { pending = resolve; });
  };

  app.setConnected.push((on) => { if (!on) { regionSet = false; if (dialog.open) finish(false); } });
}
