import { h, download } from './dom.js';

export function mountLog(root, app) {
  const box = h('textarea', { class: 'log', readonly: true, 'aria-label': 'Transport log' });
  root.append(
    h('div', { class: 'row' },
      h('button', { onclick: () => download(`transport-log-${new Date().toISOString().replace(/[:.]/g, '-')}.txt`, app.log.toText()) }, 'Download log'),
      h('button', { onclick: () => app.log.clear() }, 'Clear'),
      h('span', { class: 'note' }, 'Every byte sent (TX) and received (RX), as hex.')),
    box);
  let pending = false;
  app.log.onChange(() => {
    if (pending) return;
    pending = true;
    setTimeout(() => { pending = false; box.value = app.log.toText().split('\n').slice(-500).join('\n'); box.scrollTop = box.scrollHeight; }, 200);
  });
}
