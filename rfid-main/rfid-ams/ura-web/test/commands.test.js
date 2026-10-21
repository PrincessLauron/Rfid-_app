import test from 'node:test';
import assert from 'node:assert/strict';
import { cmd, parseVersion, BLOCKED_OPCODES, OP } from '../src/protocol/commands.js';
import { hex } from '../src/protocol/frame.js';
import { ReaderError } from '../src/protocol/status.js';

test('version command bytes', () => assert.equal(hex(cmd.version().bytes), 'FF 00 03 1D 0C'));

test('parseVersion decodes firmware and the protocol bitmask', () => {
  const d = Uint8Array.from([1,2,3,4, 5,6,7,8, 0x20,0x24,0x05,0x23, 0x01,0x02,0x03,0x04, 0,0,0,0x10]);
  const v = parseVersion(d);
  assert.equal(v.firmware, '01.02.03.04');
  assert.equal(v.hardware, '05.06.07.08');
  assert.deepEqual(v.protocols, [5]); // bit 4 -> protocol id 5 (Gen2)
  assert.throws(() => parseVersion(new Uint8Array(3)), /too short/);
});

test('temperature parses as a signed byte', () => {
  assert.equal(cmd.temperature().parse(Uint8Array.from([0x2a])), 42);
  assert.equal(cmd.temperature().parse(Uint8Array.from([0xf6])), -10);
});

test('set/get read power use signed centi-dBm big-endian', () => {
  const set = cmd.setReadPower(2700);
  assert.deepEqual(Array.from(set.bytes.subarray(2, 5)), [0x92, 0x0a, 0x8c]);
  assert.equal(cmd.getReadPower().parse(Uint8Array.from([0x00, 0x0a, 0x8c])), 2700);
  assert.equal(cmd.getReadPower().parse(Uint8Array.from([0x00, 0xff, 0x9c])), -100);
});

test('setRegion / setProtocol payloads', () => {
  assert.deepEqual(Array.from(cmd.setRegion(1).bytes.subarray(2, 4)), [0x97, 0x01]);
  assert.deepEqual(Array.from(cmd.setProtocol().bytes.subarray(2, 5)), [0x93, 0x00, 0x05]);
});

test('read power limits parse', () => {
  const d = Uint8Array.from([1, 0x0a,0x8c, 0x0b,0xb8, 0x00,0x00]);
  assert.deepEqual(cmd.getReadPowerLimits().parse(d), { current: 2700, max: 3000, min: 0 });
});

test('blocked opcodes cannot be built', () => {
  for (const op of BLOCKED_OPCODES) assert.ok([OP.ERASE_FLASH, OP.BOOT_BOOTLOADER, OP.WRITE_FLASH, OP.MODIFY_FLASH, OP.KILL_TAG].includes(op));
  assert.equal(BLOCKED_OPCODES.size, 5);
});

test('ReaderError names the status and adds a hint for temperature faults', () => {
  const e = new ReaderError(0x0504, 0x22);
  assert.match(e.message, /AHAL_TEMPERATURE_EXCEED_LIMITS/);
  assert.match(e.hint, /heatsink/);
  assert.match(new ReaderError(0x9999, 1).message, /UNKNOWN_0x9999/);
});
