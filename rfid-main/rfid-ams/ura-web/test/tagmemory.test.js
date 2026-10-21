import test from 'node:test';
import assert from 'node:assert/strict';
import { cmdTag, lockMaskAction, clampPower, hexToBytes, BANK, GEN2, TARGETS } from '../src/protocol/commands.js';

const body = (c) => Array.from(c.bytes.subarray(3, c.bytes.length - 2)); // payload after FF LEN OP, before CRC
const EPC = 'E28011606000020A10F2428D';

test('write EPC targets a specific tag: opcode 23, option 01, password, bit length, old EPC, new EPC', () => {
  const c = cmdTag.writeEpc({ epc: 'AABB', newEpc: '1122', timeoutMs: 1000 });
  assert.equal(c.bytes[2], 0x23);
  assert.deepEqual(body(c), [0x03, 0xe8, 0x01, 0, 0, 0, 0, 16, 0xaa, 0xbb, 0x11, 0x22]);
});

test('write data: address, bank, password, selector, then data', () => {
  const c = cmdTag.writeData({ epc: 'AABB', bank: BANK.USER, wordAddress: 2, dataHex: 'DEADBEEF' });
  assert.equal(c.bytes[2], 0x24);
  assert.deepEqual(body(c), [0x03, 0xe8, 0x01, 0, 0, 0, 2, 3, 0, 0, 0, 0, 16, 0xaa, 0xbb, 0xde, 0xad, 0xbe, 0xef]);
});

test('read data: option 0x11, flags 0, bank, address, word count, password, selector; response skips 3-byte echo', () => {
  const c = cmdTag.readData({ epc: 'AABB', bank: BANK.USER, wordAddress: 0, wordCount: 2 });
  assert.equal(c.bytes[2], 0x28);
  assert.deepEqual(body(c), [0x03, 0xe8, 0x11, 0, 0, 3, 0, 0, 0, 0, 2, 0, 0, 0, 0, 16, 0xaa, 0xbb]);
  assert.equal(c.parse(Uint8Array.from([0x11, 0, 0, 0xde, 0xad, 0xbe, 0xef])), 'DEADBEEF');
});

test('lock: lock EPC area sets mask 0x30 action 0x20; unlock clears the action; permalock bit is never set', () => {
  assert.deepEqual(lockMaskAction('epc', true), { mask: 0x30, action: 0x20 });
  assert.deepEqual(lockMaskAction('epc', false), { mask: 0x30, action: 0x00 });
  assert.deepEqual(lockMaskAction('user', true), { mask: 0x03, action: 0x02 });
  for (const area of ['kill', 'access', 'epc', 'tid', 'user']) assert.equal(lockMaskAction(area, true).action & 0x155, 0);
  assert.throws(() => lockMaskAction('nope', true), /unknown lock area/);
  const c = cmdTag.lock({ epc: 'AABB', area: 'epc', locked: true, password: 0x12345678 });
  assert.equal(c.bytes[2], 0x25);
  assert.deepEqual(body(c), [0x03, 0xe8, 0x01, 0x12, 0x34, 0x56, 0x78, 0x00, 0x30, 0x00, 0x20, 16, 0xaa, 0xbb]);
});

test('every tag operation refuses to run without an EPC selector', () => {
  assert.throws(() => cmdTag.writeEpc({ newEpc: '1122' }), /specific tag/);
  assert.throws(() => cmdTag.writeData({ bank: 3, wordAddress: 0, dataHex: '1122' }), /specific tag/);
  assert.throws(() => cmdTag.readData({ bank: 3, wordAddress: 0, wordCount: 1 }), /specific tag/);
  assert.throws(() => cmdTag.lock({ area: 'epc', locked: true, password: 0 }), /specific tag/);
});

test('bad hex and odd-word data are rejected before any bytes are built', () => {
  assert.throws(() => hexToBytes('ZZ'), /hex/);
  assert.throws(() => hexToBytes('ABC'), /even/);
  assert.throws(() => cmdTag.writeData({ epc: EPC, bank: 3, wordAddress: 0, dataHex: 'AABBCC' }), /16-bit words/);
  assert.throws(() => cmdTag.writeEpc({ epc: EPC, newEpc: 'AABBCC' }), /whole words/);
});

test('Gen2 settings payloads', () => {
  assert.deepEqual(body(cmdTag.getGen2(GEN2.SESSION)), [0x05, 0x00]);
  assert.equal(cmdTag.getGen2(GEN2.SESSION).bytes[2], 0x6b);
  assert.deepEqual(body(cmdTag.setGen2(GEN2.TARGET, TARGETS.A)), [0x05, 0x01, 0x01, 0x00]);
  assert.equal(cmdTag.setGen2(GEN2.SESSION, 1).bytes[2], 0x9b);
  assert.deepEqual(cmdTag.getGen2(GEN2.TARGET).parse(Uint8Array.from([5, 1, 1, 0])), [1, 0]);
  assert.equal(cmdTag.getGen2(GEN2.SESSION).parse(Uint8Array.from([5, 0, 2])), 2);
});

test('clampPower keeps the request inside the module limits', () => {
  const limits = { min: 500, max: 2700 };
  assert.equal(clampPower(3100, limits), 2700);
  assert.equal(clampPower(100, limits), 500);
  assert.equal(clampPower(1234.6, limits), 1235);
});
