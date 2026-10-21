import { MockReader } from './transport/mock.js';
import { buildResponse } from './protocol/frame.js';
import { STREAM_LAYOUT } from './reader/reading.js';
import { DEFAULT_FLAGS } from './protocol/tagrecord.js';

const DEMO_EPCS = ['E28011606000020A10F2428D', 'E2801160600002090F9F5A41', '3034257BF7194E4000000001'];

function tagRecord(epcHex, rssi, count) {
  const epc = epcHex.match(/../g).map((h) => parseInt(h, 16));
  const bits = (epc.length + 2 + 2) * 8;
  return [count, rssi & 0xff, 1, 0x0e, 0x7a, 0xd8, 0, 0, 0, 0, 0x05, 0x00, bits, 0x30, 0x00, ...epc, 0xab, 0xcd];
}

function streamData(record) {
  const head = new Array(STREAM_LAYOUT.recordAt).fill(0);
  head[STREAM_LAYOUT.flagsAt] = DEFAULT_FLAGS >> 8;
  head[STREAM_LAYOUT.flagsAt + 1] = DEFAULT_FLAGS & 0xff;
  return [...head, ...record];
}

/** A fake M7E for trying the UI without hardware. */
export function createDemoTransport() {
  // region 0 = none, like a freshly powered M7E, so Demo mode shows the region prompt
  const state = { region: 0, power: 2700, session: 0, target: [1, 0], encoding: 2, tari: 0, timer: null };
  const mem = new Map();
  const mock = new MockReader({
    handlers: {
      0x03: () => [1, 2, 3, 4, 24, 0, 0, 0, 0x20, 0x24, 0x05, 0x23, 0x01, 0x09, 0x00, 0x00, 0, 0, 0, 0x10],
      0x10: () => [0, 0, 0, 7, ...'DEMO001'.split('').map((c) => c.charCodeAt(0))],
      0x93: () => [], 0x72: () => [38 + Math.round(Math.random() * 4)],
      0x67: () => [state.region], 0x97: ([r]) => { state.region = r; return []; },
      0x71: () => [1, 2, 3, 4, 5, 6, 11, 12],
      0x62: ([opt]) => (opt === 1
        ? [1, state.power >> 8, state.power & 0xff, 0x0b, 0xb8, 0x00, 0x00]
        : [0, state.power >> 8, state.power & 0xff]),
      0x92: ([hi, lo]) => { state.power = (hi << 8) | lo; return []; },
      0x6b: ([, param]) => ({ 0: [5, 0, state.session], 1: [5, 1, ...state.target], 2: [5, 2, state.encoding], 17: [5, 17, state.tari] }[param] ?? { status: 0x0105 }),
      0x9b: ([, param, ...v]) => { if (param === 0) state.session = v[0]; if (param === 1) state.target = v; if (param === 2) state.encoding = v[0]; if (param === 17) state.tari = v[0]; return []; },
      0x2f: (data) => {
        if (data[2] === 0x01 && state.region === 0) return { status: 0x0405 }; // AFE_NOT_ON, as on real hardware
        clearInterval(state.timer);
        if (data[2] === 0x01) {
          state.timer = setInterval(() => {
            DEMO_EPCS.forEach((epc, i) => {
              if (Math.random() < 0.7) mock.emit(buildResponse(0x22, 0, streamData(tagRecord(epc, -45 - i * 8 - Math.round(Math.random() * 6), 1))));
            });
          }, 250);
        }
        return [];
      },
      0x23: () => [], 0x25: () => [],
      0x24: (d) => { mem.set('user', d.slice(-4)); return []; },
      0x28: () => [0x11, 0, 0, ...(mem.get('user') ?? [0xde, 0xad, 0xbe, 0xef])],
    },
  });
  const origClose = mock.close.bind(mock);
  mock.close = async () => { clearInterval(state.timer); await origClose(); };
  return mock;
}
