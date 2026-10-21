import test from 'node:test';
import assert from 'node:assert/strict';
import { parseTagRecord, FLAG, DEFAULT_FLAGS } from '../src/protocol/tagrecord.js';

const epc = [0xe2,0x80,0x11,0x60,0x60,0x00,0x02,0x0a,0x10,0xf2,0x42,0x8d];
// bits = (epc 12 + pc 2 + crc 2) * 8 = 128
const body = [0x00,0x80, 0x30,0x00, ...epc, 0xab,0xcd];

test('parses default metadata then the Gen2 EPC', () => {
  const meta = [0x03, 0xd8 /* -40 */, 0x01, 0x0e,0x7a,0xd8 /* 949976 kHz */, 0,0,0x01,0x00, 0x05];
  const buf = Uint8Array.from([...meta, ...body]);
  const { tag, next } = parseTagRecord(buf, 0, DEFAULT_FLAGS);
  assert.equal(tag.epc, 'E28011606000020A10F2428D');
  assert.equal(tag.readCount, 3);
  assert.equal(tag.rssi, -40);
  assert.equal(tag.antenna, 1);
  assert.equal(tag.frequencyKhz, 0x0e7ad8);
  assert.equal(tag.timestampMs, 256);
  assert.equal(tag.pc, '3000');
  assert.equal(tag.epcCrc, 'ABCD');
  assert.equal(next, buf.length);
});

test('honours a record offset and returns the next offset', () => {
  const buf = Uint8Array.from([0xff, 0xff, ...body, ...body]);
  const first = parseTagRecord(buf, 2, 0);
  const second = parseTagRecord(buf, first.next, 0);
  assert.equal(second.tag.epc, first.tag.epc);
  assert.equal(second.next, buf.length);
});

test('a truncated record throws instead of returning garbage', () => {
  assert.throws(() => parseTagRecord(Uint8Array.from(body.slice(0, 10)), 0, 0), /truncated/);
});

test('XPC words are skipped when the PC says they exist', () => {
  // PC byte0 has bit 0x02 -> 2 XPC bytes follow the PC; they sit inside the declared length.
  // Declared length = EPC(2) + PC(2) + XPC(2) + CRC(2) bytes.
  const e = [0x11, 0x22];
  const bits = (e.length + 2 + 2 + 2) * 8;
  const buf = Uint8Array.from([0x00, bits, 0x32,0x00, 0x00,0x00, ...e, 0xaa,0xbb]);
  const { tag } = parseTagRecord(buf, 0, 0);
  assert.equal(tag.epc, '1122');
});

test('unsupported metadata flags are rejected loudly', () => {
  assert.throws(() => parseTagRecord(new Uint8Array(40), 0, FLAG.TAGTYPE), /not supported/);
});

test('data field with the error bit set yields dataError, not data', () => {
  const buf = Uint8Array.from([0x80,0x00, 0x04,0x05, ...body]);
  const { tag } = parseTagRecord(buf, 0, FLAG.DATA);
  assert.equal(tag.dataError, '0405');
  assert.equal(tag.data, undefined);
});
