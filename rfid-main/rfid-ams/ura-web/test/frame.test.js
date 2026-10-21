import test from 'node:test';
import assert from 'node:assert/strict';
import { crc16 } from '../src/protocol/crc.js';
import { buildRequest, parseResponse, buildResponse, hex, FrameError } from '../src/protocol/frame.js';

test('crc16 matches the known version-command vector', () => {
  assert.equal(crc16([0x00, 0x03]), 0x1d0c);
});

test('buildRequest produces FF 00 03 1D 0C for the version command', () => {
  assert.equal(hex(buildRequest(0x03)), 'FF 00 03 1D 0C');
});

test('parseResponse round-trips a built response', () => {
  const bytes = buildResponse(0x72, 0x0000, [0x2a]);
  const { frame, consumed } = parseResponse(bytes);
  assert.equal(consumed, bytes.length);
  assert.deepEqual({ ...frame, data: Array.from(frame.data) }, { opcode: 0x72, status: 0, data: [0x2a] });
});

test('parseResponse returns null until the whole frame has arrived', () => {
  const bytes = buildResponse(0x72, 0, [0x2a]);
  assert.equal(parseResponse(bytes.subarray(0, bytes.length - 1)), null);
  assert.equal(parseResponse(new Uint8Array(0)), null);
});

test('parseResponse rejects a bad CRC and a missing start byte', () => {
  const bytes = buildResponse(0x72, 0, [0x2a]);
  bytes[bytes.length - 1] ^= 0xff;
  assert.throws(() => parseResponse(bytes), (e) => e instanceof FrameError && e.kind === 'crc');
  assert.throws(() => parseResponse(Uint8Array.from([0x00, 0x01])), (e) => e.kind === 'no-sof');
});

test('parseResponse leaves trailing bytes for the next frame', () => {
  const a = buildResponse(0x03, 0, [1, 2]);
  const both = Uint8Array.from([...a, 0xff, 0x00]);
  assert.equal(parseResponse(both).consumed, a.length);
});
