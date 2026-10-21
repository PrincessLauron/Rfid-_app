import test from 'node:test';
import assert from 'node:assert/strict';
import { MockReader } from '../src/transport/mock.js';
import { ReaderSession } from '../src/reader/session.js';
import { TagReader, TagTable, decodeStreamFrame, STREAM_LAYOUT, START_STREAM } from '../src/reader/reading.js';
import { buildResponse } from '../src/protocol/frame.js';
import { DEFAULT_FLAGS } from '../src/protocol/tagrecord.js';

const epc = [0xe2,0x80,0x11,0x60,0x60,0x00,0x02,0x0a,0x10,0xf2,0x42,0x8d];
const record = [0x01, 0xd8, 0x01, 0x0e,0x7a,0xd8, 0,0,0x01,0x00, 0x05, 0x00,0x80, 0x30,0x00, ...epc, 0xab,0xcd];

function streamFrameData(recordBytes = record) {
  const d = new Array(STREAM_LAYOUT.recordAt).fill(0);
  d[STREAM_LAYOUT.flagsAt] = DEFAULT_FLAGS >> 8;
  d[STREAM_LAYOUT.flagsAt + 1] = DEFAULT_FLAGS & 0xff;
  return [...d, ...recordBytes];
}
const streamFrame = (data = streamFrameData(), status = 0) => ({ opcode: 0x22, status, data: Uint8Array.from(data) });

test('decodeStreamFrame returns the tag for a good frame', () => {
  const tag = decodeStreamFrame(streamFrame());
  assert.equal(tag.epc, 'E28011606000020A10F2428D');
  assert.equal(tag.rssi, -40);
});

test('decodeStreamFrame ignores keep-alives, other opcodes, error status and truncated records', () => {
  assert.equal(decodeStreamFrame({ opcode: 0x22, status: 0, data: Uint8Array.from([1, 2]) }), null);
  assert.equal(decodeStreamFrame({ opcode: 0x03, status: 0, data: new Uint8Array(40) }), null);
  assert.equal(decodeStreamFrame(streamFrame(undefined, 0x0400)), null);
  assert.equal(decodeStreamFrame(streamFrame(streamFrameData(record.slice(0, 12)))), null);
});

test('TagReader sends the start payload, emits tags, then stops', async () => {
  const mock = new MockReader({ handlers: { 0x2f: () => [] } });
  const s = new ReaderSession(mock, { commandTimeoutMs: 100 });
  await mock.open(115200);
  const reader = new TagReader(s);
  const seen = [];
  reader.onTag((t) => seen.push(t.epc));
  await reader.start();
  assert.deepEqual(Array.from(mock.written[0].subarray(2, 3)), [0x2f]);
  assert.deepEqual(Array.from(mock.written[0].subarray(3, 3 + START_STREAM.length)), START_STREAM);
  mock.emit(buildResponse(0x22, 0, streamFrameData()));
  mock.emit(buildResponse(0x22, 0, streamFrameData()));
  await new Promise((r) => setTimeout(r, 5));
  assert.equal(seen.length, 2);
  await reader.stop();
  assert.equal(reader.running, false);
  mock.emit(buildResponse(0x22, 0, streamFrameData()));
  await new Promise((r) => setTimeout(r, 5));
  assert.equal(seen.length, 2, 'no tags delivered after stop');
});

test('TagTable aggregates by EPC, tracks best RSSI, caps rows, and exports CSV', () => {
  const t = new TagTable();
  t.add({ epc: 'AA', rssi: -60, readCount: 2 }, 1000);
  t.add({ epc: 'AA', rssi: -40 }, 2000);
  t.add({ epc: 'BB', rssi: -70, antenna: 1, frequencyKhz: 915000 }, 3000);
  const aa = t.rows.get('AA');
  assert.equal(aa.count, 3);
  assert.equal(aa.bestRssi, -40);
  assert.equal(aa.rssi, -40);
  assert.equal(t.list()[0].epc, 'BB'); // most recent first
  const csv = t.toCsv().trim().split('\n');
  assert.equal(csv.length, 3);
  assert.match(csv[1], /^BB,1,-70,-70,1,915000,/);
});

test('TagTable stops adding new EPCs at the cap but keeps updating existing ones', () => {
  const t = new TagTable();
  for (let i = 0; i < 5005; i++) t.add({ epc: i.toString(16).padStart(8, '0') }, i);
  assert.equal(t.rows.size, 5000);
  assert.equal(t.dropped, 5);
  t.add({ epc: '00000000' }, 9999);
  assert.equal(t.rows.get('00000000').count, 2);
});
