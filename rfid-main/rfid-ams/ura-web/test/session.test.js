import test from 'node:test';
import assert from 'node:assert/strict';
import { MockReader } from '../src/transport/mock.js';
import { ReaderSession, NoResponseError, PROBE_BAUDS } from '../src/reader/session.js';
import { cmd } from '../src/protocol/commands.js';
import { ReaderError } from '../src/protocol/status.js';

const versionData = Uint8Array.from([1,2,3,4, 5,6,7,8, 0x20,0x24,0x05,0x23, 0x01,0x02,0x03,0x04, 0,0,0,0x10]);
const handlers = {
  0x03: () => versionData,
  0x10: () => Uint8Array.from([0, 0, 0, 3, 0x41, 0x42, 0x43]),
  0x93: () => [],
  0x72: () => [0x2a],
  0x92: () => ({ status: 0x0103 }),
};
const fast = { probeTimeoutMs: 20, commandTimeoutMs: 100 };

test('connect succeeds at 115200 on the first try and reads identity', async () => {
  const mock = new MockReader({ handlers });
  const s = new ReaderSession(mock, fast);
  const info = await s.connect();
  assert.equal(info.firmware, '01.02.03.04');
  assert.equal(info.serial, 'ABC');
  assert.deepEqual(mock.openedAt, [115200]);
});

test('connect probes other baud rates in URA order until one answers', async () => {
  const mock = new MockReader({ answerBaud: 921600, handlers });
  const s = new ReaderSession(mock, fast);
  await s.connect();
  assert.deepEqual(mock.openedAt, [115200, 9600, 921600]);
  assert.equal(s.baud, 921600);
});

test('a silent module reports a NoResponseError of kind "silent" naming every baud tried', async () => {
  const mock = new MockReader({ answerBaud: -1, handlers });
  const s = new ReaderSession(mock, fast);
  await assert.rejects(s.connect(), (e) => e instanceof NoResponseError && e.kind === 'silent' && e.tried.length === PROBE_BAUDS.length);
});

test('bytes that never form a valid frame report kind "garbled"', async () => {
  const mock = new MockReader({ answerBaud: -1, handlers });
  const s = new ReaderSession(mock, fast);
  const origWrite = mock.write.bind(mock);
  mock.write = async (b) => { await origWrite(b); mock.emit(Uint8Array.from([0xff, 0x05, 0x03, 0x00])); };
  await assert.rejects(s.connect(), (e) => e.kind === 'garbled');
});

test('non-zero status becomes a ReaderError', async () => {
  const mock = new MockReader({ handlers });
  const s = new ReaderSession(mock, fast);
  await s.connect();
  await assert.rejects(s.send(cmd.setReadPower(9999)), (e) => e instanceof ReaderError && e.code === 'MSG_POWER_TOO_HIGH');
  assert.equal(await s.send(cmd.temperature()), 42);
});

test('commands are serialized and a stray byte before the frame is skipped', async () => {
  const mock = new MockReader({ handlers });
  const s = new ReaderSession(mock, fast);
  await s.connect();
  const a = s.send(cmd.temperature());
  const b = s.send(cmd.temperature());
  assert.deepEqual(await Promise.all([a, b]), [42, 42]);
  mock.emit(Uint8Array.from([0x00, 0x13])); // line noise
  assert.equal(await s.send(cmd.temperature()), 42);
});

test('send rejects on timeout and the queue keeps working afterwards', async () => {
  const mock = new MockReader({ handlers: { 0x03: handlers[0x03], 0x10: handlers[0x10], 0x93: handlers[0x93] } });
  const s = new ReaderSession(mock, fast);
  await s.connect();
  mock.handlers[0x72] = () => { throw new Error('never'); };
  mock.write = async () => {};
  await assert.rejects(s.send(cmd.temperature(), { timeoutMs: 20 }), /timeout/);
});

test('unplugging fires "disconnect", rejects the pending command and clears identity', async () => {
  const mock = new MockReader({ handlers });
  const s = new ReaderSession(mock, fast);
  await s.connect();
  let fired = 0;
  s.on('disconnect', () => fired++);
  mock.write = async () => {};
  const pending = s.send(cmd.temperature(), { timeoutMs: 500 });
  mock.unplug();
  await assert.rejects(pending, /disconnected/);
  assert.equal(fired, 1);
  assert.equal(s.info, null);
});
