# Browser URA Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Web Serial browser version of SparkFun's Universal Reader Assistant for the M7E module in a new `ura-web/` folder, then retire the old Python `reader_standalone/` monitor.

**Architecture:** Plain ES modules with no framework, bundler or runtime dependencies. A pure protocol core (`protocol/`) is wrapped by a transport (`transport/`: Web Serial or mock) and a session (`reader/`), and the UI tabs talk only to the session. All protocol logic is unit-tested in Node against hand-built byte vectors and a mock reader; the UI is smoke-tested in the browser using a built-in Demo mode.

**Tech Stack:** JavaScript (ES2022 modules), Web Serial API (Chrome/Edge), Node's built-in `node --test` (Node 20+), plain HTML/CSS.

**Spec:** `docs/superpowers/specs/2026-10-14-browser-ura-design.md` (protocol facts: `docs/protocol/m7e-serial-protocol.md`)

## Global Constraints

- Web Serial API only (Chrome/Edge); no Python bridge, no Safari/Firefox support.
- `ura-web/` uses plain ES modules: no framework, no bundler, no runtime dependencies. Tests use `node --test`.
- Clean-room: implement from the documented protocol facts; never copy decompiled vendor code into the repo.
- Frame format: request `FF | LEN | OPCODE | DATA… | CRC16(BE)`; response `FF | LEN | OPCODE | STATUS(2,BE) | DATA… | CRC16(BE)`. CRC-16 poly `0x1021`, init `0xFFFF`. Version request must be exactly `FF 00 03 1D 0C`.
- Default baud 115200; probe order 115200, 9600, 921600, 19200, 38400, 57600, 230400, 460800.
- Blocked opcodes (never sent): `07` erase flash, `09` boot bootloader, `0D` write flash, `0F` modify flash, `26` kill.
- Writes (EPC, user memory, lock) are off until the user ticks "Enable writes"; every tag operation targets one specific EPC; permanent lock is never offered.
- Power is clamped to the limits the module reports; region changes ask for confirmation.
- Streaming start/stop bytes, stream frame offsets, Gen2 config values and tag write/lock/read payloads are **unverified on hardware** until Task 8 passes.
- **Deviations from the spec (both are recorded in the spec by Task 1):** "Read once" is a fixed 3-second streaming window, not opcodes `22`+`29`; Gen2 Q and BLF settings are deferred because their value encodings are not yet verified.
- Commit trailer on every commit: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

## Review Focus

- **Cable pulled mid-read:** the session must emit `disconnect`, reject the pending command, clear identity, and the UI must reset to "Not connected" without hanging (Task 4 test; Task 6 browser step).
- **A flood of reads:** the same EPC read thousands of times must aggregate into one row, and more than 5000 distinct EPCs must not freeze the page (Task 5 tests).
- **Several tags in range during a write or lock:** every tag operation must refuse to build without an EPC selector so the wrong tag is never touched (Task 2 test).
- **Noise or silence on the line:** stray bytes before or inside a frame must resync, a module that sends nothing must be reported as `silent` (wiring) and one that sends junk as `garbled` (baud/noise) (Task 4 tests).
- **Power or region out of range:** a power typed above or below the module limits is clamped, and a rejected region/power returns a named error with a hint instead of a silent failure (Task 2 tests; Task 7 browser step).

## File Structure

```
ura-web/
  package.json            scripts: test
  README.md               how to run it
  index.html              page shell: header, 4 tabs
  styles.css              theme (light/dark), layout
  src/
    protocol/crc.js       CRC-16
    protocol/frame.js     build request / parse response / hex helpers
    protocol/status.js    status code table + ReaderError
    protocol/commands.js  opcodes, command builders+parsers, tag-memory builders, safety allow-list
    protocol/tagrecord.js metadata-ordered tag record parser
    transport/mock.js     scripted fake reader (tests + demo)
    transport/webserial.js Web Serial wrapper
    reader/session.js     connect, baud probe, serialized commands, events
    reader/reading.js     stream start/stop/decode, TagReader, TagTable (+CSV)
    log.js                TransportLog (hex ring buffer)
    demo.js               demo reader used by the "Demo mode" button
    app.js                wiring
    ui/dom.js             element helper, download, error text
    ui/read.js            Read tab
    ui/settings.js        Settings tab
    ui/memory.js          Tag memory tab
    ui/logview.js         Log tab
  test/                   *.test.js (+ fixtures/ from hardware)
docs/protocol/verification.md   hardware verification record (Task 8)
```

---

### Task 1: Branch, repo tidy-up, scaffold, CRC and framing

**Files:**
- Modify: `docs/superpowers/specs/2026-10-14-browser-ura-design.md` (record the two deviations)
- Delete: `reader_standalone/static/style.css.bak`
- Create: `ura-web/package.json`, `ura-web/src/protocol/crc.js`, `ura-web/src/protocol/frame.js`
- Test: `ura-web/test/frame.test.js`

**Interfaces:**
- Produces: `crc16(bytes: Iterable<number>): number`; `buildRequest(opcode: number, data?: number[]): Uint8Array`; `parseResponse(buf: Uint8Array): {frame:{opcode,status,data:Uint8Array}, consumed:number} | null` (throws `FrameError` with `.kind` `'no-sof'|'crc'`); `buildResponse(opcode, status, data?): Uint8Array`; `hex(bytes): string`; `fromHex(s): Uint8Array`; `class FrameError`.

- [ ] **Step 1: Create the feature branch and commit the existing design docs**

```bash
cd "/Users/jomvill/Developer/RFID AMS"
git checkout -b feat/browser-ura
git add docs/
git commit -m "docs: add browser URA design spec, protocol notes and implementation plan" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 2: Remove the stray backup file**

```bash
git rm reader_standalone/static/style.css.bak
git commit -m "chore: remove stray style.css.bak" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 3: Record the two deviations in the spec**

In `docs/superpowers/specs/2026-10-14-browser-ura-design.md`, section 4 "Read", replace the sentence `A one-shot "read once" mode uses the timed read + tag buffer (\`22\` then \`29\`) rather than an app-level timer.` with `"Read once" runs the stream for a fixed 3-second window and stops it.` In section 4 "Settings", replace `Gen2 session/target/Q/BLF/tari/encoding` with `Gen2 session/target/tari/encoding (Q and BLF are deferred until their value encodings are verified on hardware)`.

- [ ] **Step 4: Create `ura-web/package.json`**

```json
{
  "name": "ura-web",
  "private": true,
  "type": "module",
  "scripts": { "test": "node --test test/*.test.js" }
}
```

- [ ] **Step 5: Write the failing test `ura-web/test/frame.test.js`**

```js
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
```

- [ ] **Step 6: Run it and confirm it fails**

Run: `cd ura-web && npm test`
Expected: FAIL with `Cannot find module '../src/protocol/crc.js'`.

- [ ] **Step 7: Write `ura-web/src/protocol/crc.js`**

```js
/** CRC-16, polynomial 0x1021, init 0xFFFF, bit-serial "augmented" form used by the M7E (no final zero append). */
export function crc16(bytes) {
  let crc = 0xffff;
  for (const byte of bytes) {
    for (let bit = 0; bit < 8; bit++) {
      const top = crc & 0x8000;
      crc = (crc << 1) & 0xffff;
      if (byte & (0x80 >> bit)) crc |= 1;
      if (top) crc ^= 0x1021;
    }
  }
  return crc;
}
```

- [ ] **Step 8: Write `ura-web/src/protocol/frame.js`**

```js
import { crc16 } from './crc.js';

export class FrameError extends Error {
  constructor(message, kind) { super(message); this.name = 'FrameError'; this.kind = kind; }
}

/** Request: FF | LEN | OPCODE | DATA... | CRC16(BE). LEN counts DATA bytes only. */
export function buildRequest(opcode, data = []) {
  if (data.length > 250) throw new FrameError('payload too large', 'too-large');
  const body = [data.length, opcode, ...data];
  const crc = crc16(body);
  return Uint8Array.from([0xff, ...body, crc >> 8, crc & 0xff]);
}

/**
 * Try to parse one response frame at the start of `buf`.
 * Response: FF | LEN | OPCODE | STATUS(2,BE) | DATA(LEN bytes) | CRC16(BE).
 * Returns { frame, consumed } or null when more bytes are needed.
 * Throws FrameError('no-sof' | 'crc') for garbage.
 */
export function parseResponse(buf) {
  if (buf.length === 0) return null;
  if (buf[0] !== 0xff) throw new FrameError('start byte 0xFF not found', 'no-sof');
  if (buf.length < 2) return null;
  const len = buf[1];
  const total = 1 + 1 + 1 + 2 + len + 2;
  if (buf.length < total) return null;
  const crcExpected = crc16(buf.subarray(1, total - 2));
  const crcActual = (buf[total - 2] << 8) | buf[total - 1];
  if (crcExpected !== crcActual) throw new FrameError('CRC mismatch', 'crc');
  return {
    frame: {
      opcode: buf[2],
      status: (buf[3] << 8) | buf[4],
      data: buf.slice(5, 5 + len),
    },
    consumed: total,
  };
}

/** Build a response (used by the mock reader and tests). */
export function buildResponse(opcode, status, data = []) {
  const body = [data.length, opcode, status >> 8, status & 0xff, ...data];
  const crc = crc16(body);
  return Uint8Array.from([0xff, ...body, crc >> 8, crc & 0xff]);
}

export const hex = (bytes) => Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join(' ').toUpperCase();
export const fromHex = (s) => Uint8Array.from(s.trim().split(/\s+/).filter(Boolean).map((h) => parseInt(h, 16)));
```

- [ ] **Step 9: Run the tests and confirm they pass**

Run: `cd ura-web && npm test`
Expected: 6 tests pass.

- [ ] **Step 10: Commit**

```bash
git add docs/superpowers/specs ura-web
git commit -m "feat(ura-web): scaffold project with CRC-16 and frame codec" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Status codes, commands, tag-memory builders and the safety allow-list

**Files:**
- Create: `ura-web/src/protocol/status.js`, `ura-web/src/protocol/commands.js`
- Test: `ura-web/test/commands.test.js`, `ura-web/test/tagmemory.test.js`

**Interfaces:**
- Consumes: `buildRequest` from `frame.js`.
- Produces: `OP`, `BLOCKED_OPCODES`, `PROTOCOL_GEN2`, `REGIONS`, `GEN2`, `BANK`, `TARGETS`; `cmd.{version,temperature,serialNumber,getRegion,setRegion(id),availableRegions,getReadPower,getReadPowerLimits,setReadPower(centiDbm),setProtocol(id?),bootFirmware}`; `cmdTag.{getGen2(param),setGen2(param,values),writeEpc,writeData,readData,lock}`; `lockMaskAction(area, locked)`; `clampPower(requested, {min,max})`; `hexToBytes(hex)`; `parseVersion(data)`. Every builder returns `{opcode, bytes: Uint8Array, parse(data: Uint8Array): any}`. `ReaderError(status, opcode)` with `.code`, `.status`, `.hint`.

- [ ] **Step 1: Write the failing tests**

`ura-web/test/commands.test.js`:

```js
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
```

`ura-web/test/tagmemory.test.js`:

```js
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
```

- [ ] **Step 2: Run and confirm failure**

Run: `cd ura-web && npm test`
Expected: FAIL with `Cannot find module '../src/protocol/commands.js'`.

- [ ] **Step 3: Write `ura-web/src/protocol/status.js`**

```js
/** Status codes returned in bytes 3-4 of every response. 0x0000 = success. Names from the module's fault table. */
export const STATUS_NAMES = {
  0x0100: 'MSG_WRONG_NUMBER_OF_DATA', 0x0101: 'INVALID_OPCODE', 0x0102: 'UNIMPLEMENTED_OPCODE',
  0x0103: 'MSG_POWER_TOO_HIGH', 0x0104: 'MSG_INVALID_FREQ_RECEIVED', 0x0105: 'MSG_INVALID_PARAMETER_VALUE',
  0x0106: 'MSG_POWER_TOO_LOW', 0x0109: 'UNIMPLEMENTED_FEATURE', 0x010a: 'INVALID_BAUD_RATE',
  0x010b: 'INVALID_REGION', 0x010c: 'INVALID_LICENSE_KEY',
  0x0400: 'NO_TAGS_FOUND', 0x0401: 'NO_PROTOCOL_DEFINED', 0x0402: 'INVALID_PROTOCOL_SPECIFIED',
  0x0404: 'PROTOCOL_NO_DATA_READ', 0x0405: 'AFE_NOT_ON', 0x0406: 'PROTOCOL_WRITE_FAILED',
  0x0407: 'NOT_IMPLEMENTED_FOR_THIS_PROTOCOL', 0x0409: 'PROTOCOL_INVALID_ADDRESS', 0x040a: 'GENERAL_TAG_ERROR',
  0x040b: 'DATA_TOO_LARGE', 0x040e: 'PROTOCOL_KILL_FAILED', 0x0410: 'PROTOCOL_INVALID_EPC',
  0x0411: 'PROTOCOL_INVALID_NUM_DATA', 0x0413: 'PROTOCOL_INVALID_TAG_OP',
  0x0420: 'GEN2_PROTOCOL_OTHER_ERROR', 0x0423: 'GEN2_PROTOCOL_MEMORY_OVERRUN_BAD_PC',
  0x0424: 'GEN2_PROTOCOL_MEMORY_LOCKED', 0x042b: 'GEN2_PROTOCOL_INSUFFICIENT_POWER',
  0x042f: 'GEN2_PROTOCOL_NON_SPECIFIC_ERROR', 0x0430: 'GEN2_PROTOCOL_UNKNOWN_ERROR',
  0x0500: 'AHAL_INVALID_FREQ', 0x0501: 'AHAL_CHANNEL_OCCUPIED', 0x0502: 'AHAL_TRANSMITTER_ON',
  0x0503: 'AHAL_ANTENNA_NOT_CONNECTED', 0x0504: 'AHAL_TEMPERATURE_EXCEED_LIMITS',
  0x0505: 'AHAL_HIGH_RETURN_LOSS', 0x0509: 'IPVOLTAGE_EXCEEDED_LIMITS',
  0x0600: 'TAG_ID_BUFFER_NOT_ENOUGH_TAGS_AVAILABLE', 0x0601: 'TAG_ID_BUFFER_FULL',
  0x7f00: 'SYSTEM_UNKNOWN_ERROR', 0x7f01: 'TM_ASSERT_FAILED',
};

const HINTS = {
  0x0504: 'Module is outside its operating temperature. Lower the read power or add a heatsink, then retry.',
  0x0405: 'RF is off. Select a region first.',
  0x0503: 'No antenna detected. Check the antenna connector before transmitting.',
  0x0505: 'High return loss detected. Check the antenna and cable.',
  0x010b: 'The module rejected that region.',
  0x0103: 'Power is above what this module supports.',
  0x0106: 'Power is below what this module supports.',
  0x0424: 'The tag memory is locked. Use the access password or unlock it first.',
};

export class ReaderError extends Error {
  constructor(status, opcode) {
    const name = STATUS_NAMES[status] ?? `UNKNOWN_0x${status.toString(16).padStart(4, '0')}`;
    super(`${name} (status 0x${status.toString(16).padStart(4, '0')}, opcode 0x${opcode.toString(16).padStart(2, '0')})`);
    this.name = 'ReaderError';
    this.status = status;
    this.opcode = opcode;
    this.code = name;
    this.hint = HINTS[status] ?? null;
  }
}
```

- [ ] **Step 4: Write `ura-web/src/protocol/commands.js`**

```js
import { buildRequest } from './frame.js';

export const OP = {
  VERSION: 0x03, BOOT_FIRMWARE: 0x04, SET_BAUD: 0x06, HW_VERSION: 0x10,
  READ_TAG_MULTIPLE: 0x22, MULTI_PROTOCOL_TAG_OP: 0x2f, GET_TAG_BUFFER: 0x29, CLEAR_TAG_BUFFER: 0x2a,
  GET_READ_POWER: 0x62, GET_PROTOCOL: 0x63, GET_REGION: 0x67, GET_AVAILABLE_REGIONS: 0x71, GET_TEMPERATURE: 0x72,
  GET_PROTOCOL_CONFIG: 0x6b, SET_READ_POWER: 0x92, SET_PROTOCOL: 0x93, SET_REGION: 0x97, SET_PROTOCOL_CONFIG: 0x9b, SET_READER_CONFIG: 0x9a,
  WRITE_TAG_EPC: 0x23, WRITE_TAG_DATA: 0x24, LOCK_TAG: 0x25, READ_TAG_DATA: 0x28,
  // Never sent by this app (see BLOCKED_OPCODES)
  ERASE_FLASH: 0x07, BOOT_BOOTLOADER: 0x09, WRITE_FLASH: 0x0d, MODIFY_FLASH: 0x0f, KILL_TAG: 0x26,
};

/** Opcodes that can brick the module or destroy tags. buildCommand/session.send refuse them. */
export const BLOCKED_OPCODES = new Set([OP.ERASE_FLASH, OP.BOOT_BOOTLOADER, OP.WRITE_FLASH, OP.MODIFY_FLASH, OP.KILL_TAG]);

export const PROTOCOL_GEN2 = 0x05;

export const REGIONS = {
  1: 'NA', 2: 'EU', 3: 'KR', 4: 'IN', 5: 'JP', 6: 'PRC', 7: 'EU2', 8: 'EU3', 9: 'KR2', 10: 'PRC2', 11: 'AU', 12: 'NZ',
  13: 'NA2', 14: 'NA3', 15: 'IS', 16: 'MY', 17: 'ID', 18: 'PH', 19: 'TW', 20: 'MO', 21: 'RU', 22: 'SG', 23: 'JP2',
  24: 'JP3', 25: 'VN', 26: 'TH', 27: 'AR', 28: 'HK', 29: 'BD', 30: 'EU4', 31: 'UNIVERSAL', 32: 'IS2', 33: 'NA4',
  254: 'OPEN_EXTENDED', 255: 'OPEN',
};

function request(opcode, data = []) {
  if (BLOCKED_OPCODES.has(opcode)) throw new Error(`opcode 0x${opcode.toString(16)} is blocked by the safety allow-list`);
  return { opcode, bytes: buildRequest(opcode, data) };
}

const s16 = (hi, lo) => ((hi << 8) | lo) << 16 >> 16;
const be16 = (v) => [(v >> 8) & 0xff, v & 0xff];

export const cmd = {
  version: () => ({ ...request(OP.VERSION), parse: parseVersion }),
  temperature: () => ({ ...request(OP.GET_TEMPERATURE), parse: (d) => (d[0] << 24) >> 24 }),
  serialNumber: () => ({ ...request(OP.HW_VERSION, [0x00, 0x40]), parse: parseSerial }),
  getRegion: () => ({ ...request(OP.GET_REGION), parse: (d) => d[0] }),
  setRegion: (id) => ({ ...request(OP.SET_REGION, [id]), parse: () => undefined }),
  availableRegions: () => ({ ...request(OP.GET_AVAILABLE_REGIONS), parse: (d) => Array.from(d) }),
  /** Power values are centi-dBm (2700 = 27.00 dBm). */
  getReadPower: () => ({ ...request(OP.GET_READ_POWER, [0x00]), parse: (d) => s16(d[1], d[2]) }),
  getReadPowerLimits: () => ({ ...request(OP.GET_READ_POWER, [0x01]), parse: (d) => ({ current: s16(d[1], d[2]), max: s16(d[3], d[4]), min: s16(d[5], d[6]) }) }),
  setReadPower: (centiDbm) => ({ ...request(OP.SET_READ_POWER, be16(centiDbm & 0xffff)), parse: () => undefined }),
  setProtocol: (id = PROTOCOL_GEN2) => ({ ...request(OP.SET_PROTOCOL, be16(id)), parse: () => undefined }),
  bootFirmware: () => ({ ...request(OP.BOOT_FIRMWARE), parse: parseVersion }),
};

const ver = (d, o) => `${d[o].toString(16).padStart(2, '0')}.${d[o + 1].toString(16).padStart(2, '0')}.${d[o + 2].toString(16).padStart(2, '0')}.${d[o + 3].toString(16).padStart(2, '0')}`.toUpperCase();

export function parseVersion(d) {
  if (d.length < 20) throw new Error(`version response too short (${d.length} bytes)`);
  const mask = ((d[16] << 24) | (d[17] << 16) | (d[18] << 8) | d[19]) >>> 0;
  const protocols = [];
  for (let i = 0; i < 32; i++) if (mask & (1 << i)) protocols.push(i + 1);
  return { bootloader: ver(d, 0), hardware: ver(d, 4), firmwareDate: ver(d, 8), firmware: ver(d, 12), protocols };
}

function parseSerial(d) {
  const n = d[3];
  return String.fromCharCode(...d.slice(4, 4 + n));
}

// ---------------------------------------------------------------------------------------------
// Gen2 settings and tag memory. Payload layouts come from the decompiled MercuryAPI and are
// UNVERIFIED on hardware until Task 11 passes; every write is also followed by a read-back check.
// ---------------------------------------------------------------------------------------------
export const GEN2 = { SESSION: 0, TARGET: 1, ENCODING: 2, TARI: 17 };
export const BANK = { RESERVED: 0, EPC: 1, TID: 2, USER: 3 };
export const TARGETS = { A: [1, 0], B: [1, 1], AB: [0, 0], BA: [0, 1] };

const be32 = (v) => [(v >>> 24) & 0xff, (v >>> 16) & 0xff, (v >>> 8) & 0xff, v & 0xff];

export function hexToBytes(hex) {
  const clean = hex.replace(/\s+/g, '');
  if (clean.length === 0 || clean.length % 2 !== 0 || /[^0-9a-f]/i.test(clean)) throw new Error('hex string must have an even number of hex digits');
  return Array.from({ length: clean.length / 2 }, (_, i) => parseInt(clean.slice(i * 2, i * 2 + 2), 16));
}

/** Singulation by EPC: [bitLength, ...epc]. Required for every tag operation so we never touch the wrong tag. */
function epcSelector(epcHex) {
  if (!epcHex) throw new Error('an EPC is required: tag operations must target one specific tag');
  const bytes = hexToBytes(epcHex);
  if (bytes.length * 8 > 255) throw new Error('EPC selector longer than 255 bits is not supported');
  return [bytes.length * 8, ...bytes];
}

function checkWords(bytes) {
  if (bytes.length === 0 || bytes.length % 2 !== 0) throw new Error('data must be a whole number of 16-bit words');
}

const gen2Value = (d) => d[2];

export const cmdTag = {
  getGen2: (param) => ({ ...request(OP.GET_PROTOCOL_CONFIG, [PROTOCOL_GEN2, param]), parse: (d) => (param === GEN2.TARGET ? [d[2], d[3]] : gen2Value(d)) }),
  setGen2: (param, values) => ({ ...request(OP.SET_PROTOCOL_CONFIG, [PROTOCOL_GEN2, param, ...[].concat(values)]), parse: () => undefined }),

  writeEpc: ({ epc, newEpc, password = 0, timeoutMs = 1000 }) => {
    const next = hexToBytes(newEpc);
    if (next.length % 2 !== 0 || next.length > 62) throw new Error('new EPC must be 2-62 bytes in whole words');
    return { ...request(OP.WRITE_TAG_EPC, [...be16(timeoutMs), 0x01, ...be32(password), ...epcSelector(epc), ...next]), parse: () => undefined };
  },
  writeData: ({ epc, bank, wordAddress, dataHex, password = 0, timeoutMs = 1000 }) => {
    const data = hexToBytes(dataHex);
    checkWords(data);
    return { ...request(OP.WRITE_TAG_DATA, [...be16(timeoutMs), 0x01, ...be32(wordAddress), bank, ...be32(password), ...epcSelector(epc), ...data]), parse: () => undefined };
  },
  /** Reads `wordCount` 16-bit words. Response data starts with a 3-byte echo (option + metadata flags); the rest is memory. */
  readData: ({ epc, bank, wordAddress, wordCount, password = 0, timeoutMs = 1000 }) => ({
    ...request(OP.READ_TAG_DATA, [...be16(timeoutMs), 0x11, 0x00, 0x00, bank, ...be32(wordAddress), wordCount, ...be32(password), ...epcSelector(epc)]),
    parse: (d) => Array.from(d.slice(3), (b) => b.toString(16).padStart(2, '0')).join('').toUpperCase(),
  }),
  lock: ({ epc, area, locked, password, timeoutMs = 1000 }) => {
    const { mask, action } = lockMaskAction(area, locked);
    return { ...request(OP.LOCK_TAG, [...be16(timeoutMs), 0x01, ...be32(password), ...be16(mask), ...be16(action), ...epcSelector(epc)]), parse: () => undefined };
  },
};

const LOCK_SHIFT = { kill: 8, access: 6, epc: 4, tid: 2, user: 0 };

/**
 * Gen2 lock payload: 10-bit mask and action, two bits per area (high = lock, low = permalock).
 * We always set both mask bits (so permalock is explicitly left clear) and never request a permanent lock.
 */
export function lockMaskAction(area, locked) {
  if (!(area in LOCK_SHIFT)) throw new Error(`unknown lock area: ${area}`);
  const shift = LOCK_SHIFT[area];
  return { mask: 0b11 << shift, action: (locked ? 0b10 : 0b00) << shift };
}

/** Clamp a requested power (centi-dBm) to the module's reported limits. */
export function clampPower(requested, { min, max }) {
  return Math.min(max, Math.max(min, Math.round(requested)));
}
```

- [ ] **Step 5: Run and confirm pass**

Run: `cd ura-web && npm test`
Expected: all tests in `frame`, `commands` and `tagmemory` pass (`ℹ pass 22`).

- [ ] **Step 6: Commit**

```bash
git add ura-web
git commit -m "feat(ura-web): add status codes, command builders and safety allow-list" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Tag record parser

**Files:**
- Create: `ura-web/src/protocol/tagrecord.js`
- Test: `ura-web/test/tagrecord.test.js`

**Interfaces:**
- Produces: `FLAG` (metadata bit masks), `DEFAULT_FLAGS`, `parseTagRecord(buf: Uint8Array, offset: number, flags: number): { tag: {epc, epcCrc, pc, protocol, readCount?, rssi?, antenna?, frequencyKhz?, timestampMs?, phase?, data?, dataError?, gpio?, q?, linkFrequency?, target?}, next: number }`. Throws on truncated buffers and on `TAGTYPE`/`BRAND_ID` flags.

- [ ] **Step 1: Write the failing test `ura-web/test/tagrecord.test.js`**

```js
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
```

- [ ] **Step 2: Run and confirm failure**

Run: `cd ura-web && npm test`
Expected: FAIL with `Cannot find module '../src/protocol/tagrecord.js'`.

- [ ] **Step 3: Write `ura-web/src/protocol/tagrecord.js`**

```js
/** Metadata flag bits, in the order their fields appear in a tag record. */
export const FLAG = {
  READCOUNT: 0x0001, RSSI: 0x0002, ANTENNA: 0x0004, FREQUENCY: 0x0008, TIMESTAMP: 0x0010, PHASE: 0x0020,
  PROTOCOL: 0x0040, DATA: 0x0080, GPIO: 0x0100, GEN2_Q: 0x0200, GEN2_LF: 0x0400, GEN2_TARGET: 0x0800,
  BRAND_ID: 0x1000, TAGTYPE: 0x2000,
};
export const DEFAULT_FLAGS = FLAG.READCOUNT | FLAG.RSSI | FLAG.ANTENNA | FLAG.FREQUENCY | FLAG.TIMESTAMP | FLAG.PROTOCOL;

const hexOf = (bytes) => Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('').toUpperCase();

/**
 * Parse one tag record starting at `offset`. Returns { tag, next }.
 * Throws if the flags include fields this app does not decode (TAGTYPE, BRAND_ID) or the buffer is short.
 */
export function parseTagRecord(buf, offset, flags) {
  if (flags & (FLAG.TAGTYPE | FLAG.BRAND_ID)) throw new Error('TAGTYPE and BRAND_ID metadata are not supported');
  let o = offset;
  const need = (n) => { if (o + n > buf.length) throw new Error('tag record truncated'); };
  const u8 = () => { need(1); return buf[o++]; };
  const u16 = () => { need(2); const v = (buf[o] << 8) | buf[o + 1]; o += 2; return v; };
  const take = (n) => { need(n); const v = buf.slice(o, o + n); o += n; return v; };

  const tag = {};
  let protocol = 0x05;
  if (flags & FLAG.READCOUNT) tag.readCount = u8();
  if (flags & FLAG.RSSI) tag.rssi = (u8() << 24) >> 24;
  if (flags & FLAG.ANTENNA) tag.antenna = u8();
  if (flags & FLAG.FREQUENCY) tag.frequencyKhz = (u8() << 16) | (u8() << 8) | u8();
  if (flags & FLAG.TIMESTAMP) tag.timestampMs = ((u8() << 24) | (u8() << 16) | (u8() << 8) | u8()) >>> 0;
  if (flags & FLAG.PHASE) tag.phase = u16();
  if (flags & FLAG.PROTOCOL) protocol = u8();
  tag.protocol = protocol;
  if (flags & FLAG.DATA) {
    const bits = u16();
    if (bits & 0x8000) { tag.dataError = hexOf(take(2)); } else { tag.data = take((bits + 7) >> 3); }
  }
  if (flags & FLAG.GPIO) tag.gpio = u8();
  if (protocol === 0x05) {
    if (flags & FLAG.GEN2_Q) tag.q = u8();
    if (flags & FLAG.GEN2_LF) tag.linkFrequency = u8();
    if (flags & FLAG.GEN2_TARGET) tag.target = u8();
  }

  const epcBits = u16();
  if (epcBits % 8 !== 0) throw new Error('EPC length not a multiple of 8 bits');
  let epcLen = epcBits / 8;
  if (epcLen >= 2) epcLen -= 2; // trailing EPC CRC
  if (protocol === 0x05) {
    const pc = take(2);
    if (epcLen >= 2) epcLen -= 2;
    tag.pc = hexOf(pc);
    if (pc[0] & 0x02) { // XPC present
      const xpc = take(2);
      epcLen -= 2;
      if (xpc[0] & 0x80) { take(2); epcLen -= 2; }
    }
  }
  if (epcLen < 0) throw new Error('EPC length inconsistent');
  tag.epc = hexOf(take(epcLen));
  tag.epcCrc = hexOf(take(2));
  return { tag, next: o };
}
```

- [ ] **Step 4: Run and confirm pass**

Run: `cd ura-web && npm test`
Expected: all tests pass (`ℹ pass 28`).

- [ ] **Step 5: Commit**

```bash
git add ura-web
git commit -m "feat(ura-web): add metadata-ordered tag record parser" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Mock reader and reader session (connect, baud probe, command queue)

**Files:**
- Create: `ura-web/src/transport/mock.js`, `ura-web/src/reader/session.js`
- Test: `ura-web/test/session.test.js`

**Interfaces:**
- Consumes: `parseResponse`, `buildResponse`, `FrameError` (frame.js); `cmd`, `BLOCKED_OPCODES` (commands.js); `ReaderError` (status.js).
- Transport contract used by the session: `open(baud): Promise`, `close(): Promise`, `write(bytes): Promise`, `onData(cb(Uint8Array))`, `onClose?(cb())`, `isOpen: boolean`.
- Produces: `class MockReader({answerBaud=115200, handlers={}})` with `emit(bytes)`, `unplug()`, `openedAt[]`, `written[]`; `PROBE_BAUDS`; `class NoResponseError {kind:'silent'|'garbled', tried:number[]}`; `class ReaderSession(transport, {log, probeTimeoutMs=400, commandTimeoutMs=1500})` with `connect({bauds})`, `send(command, {timeoutMs})`, `disconnect()`, `on(event, fn)` (events `frame`, `frame-error`, `disconnect`), properties `info`, `baud`.

- [ ] **Step 1: Write the failing test `ura-web/test/session.test.js`**

```js
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
```

- [ ] **Step 2: Run and confirm failure**

Run: `cd ura-web && npm test`
Expected: FAIL with `Cannot find module '../src/transport/mock.js'`.

- [ ] **Step 3: Write `ura-web/src/transport/mock.js`**

```js
import { buildResponse, parseResponse } from '../protocol/frame.js';

/**
 * Scripted fake reader implementing the transport interface:
 *   open(baud), close(), write(bytes), onData(cb), isOpen
 * `handlers` maps opcode -> (data) => Uint8Array of response data, or { status, data }.
 * The mock only answers when opened at `answerBaud`; otherwise it stays silent (like a baud mismatch).
 */
export class MockReader {
  constructor({ answerBaud = 115200, handlers = {} } = {}) {
    this.answerBaud = answerBaud;
    this.handlers = handlers;
    this.isOpen = false;
    this.baud = null;
    this.openedAt = [];
    this.written = [];
    this._cb = null;
    this._closeCb = null;
  }
  async open(baud) { this.isOpen = true; this.baud = baud; this.openedAt.push(baud); }
  async close() { this.isOpen = false; }
  onData(cb) { this._cb = cb; }
  onClose(cb) { this._closeCb = cb; }
  /** Simulate the USB cable being pulled. */
  unplug() { this.isOpen = false; this._closeCb?.(); }
  /** Push raw bytes to the host as if the module sent them (used for streaming tests). */
  emit(bytes) { this._cb?.(bytes); }
  async write(bytes) {
    this.written.push(Uint8Array.from(bytes));
    if (this.baud !== this.answerBaud) return;
    const { frame } = parseResponse(rebuildAsResponse(bytes));
    const h = this.handlers[frame.opcode];
    if (!h) return this.emit(buildResponse(frame.opcode, 0x0101, []));
    const out = h(frame.data);
    const { status = 0, data = [] } = out instanceof Uint8Array || Array.isArray(out) ? { data: out } : out;
    queueMicrotask(() => this.emit(buildResponse(frame.opcode, status, data)));
  }
}

// A request is FF LEN OP DATA CRC; reuse the response parser by inserting a zero status.
function rebuildAsResponse(req) {
  const len = req[1];
  return buildResponse(req[2], 0, req.slice(3, 3 + len));
}
```

- [ ] **Step 4: Write `ura-web/src/reader/session.js`**

```js
import { parseResponse, FrameError, hex } from '../protocol/frame.js';
import { BLOCKED_OPCODES, cmd } from '../protocol/commands.js';
import { ReaderError } from '../protocol/status.js';

/** Baud rates in the order the URA tries them: default twice, then the rest. */
export const PROBE_BAUDS = [115200, 9600, 921600, 19200, 38400, 57600, 230400, 460800];

export class NoResponseError extends Error {
  constructor(kind, tried) {
    super(kind === 'silent'
      ? 'The module sent no bytes at any baud rate. Check power, the UART/USB switch, and especially the RX wire or USB data cable.'
      : 'The module sent bytes but none formed a valid reply. Check baud rate and noise.');
    this.name = 'NoResponseError';
    this.kind = kind; // 'silent' = zero bytes received, 'garbled' = bytes but no valid frame
    this.tried = tried;
  }
}

export class ReaderSession {
  /** @param transport open/close/write/onData/isOpen  @param log {add(entry)} optional */
  constructor(transport, { log = null, probeTimeoutMs = 400, commandTimeoutMs = 1500 } = {}) {
    this.transport = transport;
    this.log = log;
    this.probeTimeoutMs = probeTimeoutMs;
    this.commandTimeoutMs = commandTimeoutMs;
    this.info = null;
    this.baud = null;
    this.writesEnabled = false;
    this._rx = new Uint8Array(0);
    this._waiter = null;
    this._queue = Promise.resolve();
    this._listeners = {};
    this._bytesSeen = 0;
    transport.onData((chunk) => this._onData(chunk));
    transport.onClose?.(() => this._onTransportClosed());
  }

  on(event, fn) { (this._listeners[event] ??= new Set()).add(fn); return () => this._listeners[event].delete(fn); }
  _emit(event, payload) { this._listeners[event]?.forEach((fn) => fn(payload)); }

  _onTransportClosed() {
    this.info = null;
    this.baud = null;
    this._waiter?.reject?.(new Error('disconnected'));
    this._emit('disconnect');
  }

  _onData(chunk) {
    this._bytesSeen += chunk.length;
    this.log?.add({ dir: 'rx', bytes: chunk });
    const merged = new Uint8Array(this._rx.length + chunk.length);
    merged.set(this._rx); merged.set(chunk, this._rx.length);
    this._rx = merged;
    this._drain();
  }

  _drain() {
    for (;;) {
      // resync to the next start byte
      const i = this._rx.indexOf(0xff);
      if (i < 0) { this._rx = new Uint8Array(0); return; }
      if (i > 0) this._rx = this._rx.slice(i);
      let parsed;
      try { parsed = parseResponse(this._rx); } catch (e) {
        if (e instanceof FrameError) { this._rx = this._rx.slice(1); this._emit('frame-error', e); continue; }
        throw e;
      }
      if (!parsed) return;
      this._rx = this._rx.slice(parsed.consumed);
      if (this._waiter && this._waiter.opcode === parsed.frame.opcode) this._waiter.resolve(parsed.frame);
      else this._emit('frame', parsed.frame);
    }
  }

  /** Send one command and wait for its reply. Calls are serialized. */
  send(command, { timeoutMs = this.commandTimeoutMs } = {}) {
    if (BLOCKED_OPCODES.has(command.opcode)) return Promise.reject(new Error('blocked opcode'));
    const run = async () => {
      if (!this.transport.isOpen) throw new Error('disconnected');
      const reply = new Promise((resolve, reject) => {
        const timer = setTimeout(() => { this._waiter = null; reject(new Error(`timeout waiting for opcode 0x${command.opcode.toString(16)}`)); }, timeoutMs);
        this._waiter = {
          opcode: command.opcode,
          resolve: (f) => { clearTimeout(timer); this._waiter = null; resolve(f); },
          reject: (e) => { clearTimeout(timer); this._waiter = null; reject(e); },
        };
      });
      reply.catch(() => {});
      this.log?.add({ dir: 'tx', bytes: command.bytes });
      await this.transport.write(command.bytes);
      const frame = await reply;
      if (frame.status !== 0) throw new ReaderError(frame.status, frame.opcode);
      return command.parse(frame.data);
    };
    const next = this._queue.then(run, run);
    this._queue = next.catch(() => {});
    return next;
  }

  /** Probe baud rates until the version query succeeds, then load identity. */
  async connect({ bauds = PROBE_BAUDS } = {}) {
    const tried = [];
    this._bytesSeen = 0;
    for (const baud of bauds) {
      await this.transport.open(baud);
      tried.push(baud);
      try {
        this.info = await this.send(cmd.version(), { timeoutMs: this.probeTimeoutMs });
        this.baud = baud;
        break;
      } catch (e) {
        if (e instanceof ReaderError) { this.baud = baud; this.info = null; throw e; }
        await this.transport.close();
      }
    }
    if (this.baud === null) throw new NoResponseError(this._bytesSeen === 0 ? 'silent' : 'garbled', tried);
    this.info.serial = await this.send(cmd.serialNumber()).catch(() => null);
    await this.send(cmd.setProtocol()).catch(() => {});
    return this.info;
  }

  async disconnect() { await this.transport.close(); this.baud = null; this.info = null; }
}
```

- [ ] **Step 5: Run and confirm pass**

Run: `cd ura-web && npm test`
Expected: all tests pass (`ℹ pass 36`), including the 8 session tests (connect, probe order, silent, garbled, status error, serialized+noise, timeout, unplug).

- [ ] **Step 6: Commit**

```bash
git add ura-web
git commit -m "feat(ura-web): add mock reader and session with baud probing and disconnect handling" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Streaming reads and the tag table

**Files:**
- Create: `ura-web/src/reader/reading.js`
- Test: `ura-web/test/reading.test.js`

**Interfaces:**
- Consumes: `ReaderSession` (`send`, `on('frame')`); `parseTagRecord`, `DEFAULT_FLAGS`; `buildRequest`; `OP`.
- Produces: `START_STREAM`, `STOP_STREAM`, `STREAM_LAYOUT {flagsAt:3, recordAt:6}`, `STREAM_OPCODE`; `decodeStreamFrame(frame): tag|null`; `class TagReader(session)` with `start()`, `stop()`, `readFor(ms)`, `onTag(fn)`, `running`; `class TagTable` with `add(tag, now?)`, `list()`, `clear()`, `toCsv()`, `rows: Map`, `dropped: number` (cap 5000 distinct EPCs).

- [ ] **Step 1: Write the failing test `ura-web/test/reading.test.js`**

```js
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
```

- [ ] **Step 2: Run and confirm failure**

Run: `cd ura-web && npm test`
Expected: FAIL with `Cannot find module '../src/reader/reading.js'`.

- [ ] **Step 3: Write `ura-web/src/reader/reading.js`**

```js
import { buildRequest } from '../protocol/frame.js';
import { OP } from '../protocol/commands.js';
import { parseTagRecord } from '../protocol/tagrecord.js';

// UNVERIFIED until Task 11: the bytes SparkFun's library sends to start/stop continuous reading.
export const START_STREAM = [0x00, 0x00, 0x01, 0x22, 0x00, 0x00, 0x05, 0x07, 0x22, 0x10, 0x00, 0x1b, 0x03, 0xe8, 0x01, 0xff];
export const STOP_STREAM = [0x00, 0x00, 0x02];
/** Offsets inside frame.data (= frame bytes 8 and 11): metadata flags (u16) and the first tag record. */
export const STREAM_LAYOUT = { flagsAt: 3, recordAt: 6 };
export const STREAM_OPCODE = 0x22;

const ackCommand = (data) => ({ opcode: OP.MULTI_PROTOCOL_TAG_OP, bytes: buildRequest(OP.MULTI_PROTOCOL_TAG_OP, data), parse: () => undefined });

/** Turn one unsolicited frame into a tag, or null if it is a keep-alive/status/garbage frame. */
export function decodeStreamFrame(frame) {
  const { flagsAt, recordAt } = STREAM_LAYOUT;
  if (frame.opcode !== STREAM_OPCODE || frame.status !== 0 || frame.data.length < recordAt + 6) return null;
  const flags = (frame.data[flagsAt] << 8) | frame.data[flagsAt + 1];
  try { return parseTagRecord(frame.data, recordAt, flags).tag; } catch { return null; }
}

export class TagReader {
  constructor(session) {
    this.session = session;
    this.running = false;
    this._off = null;
    this._listeners = new Set();
  }
  onTag(fn) { this._listeners.add(fn); return () => this._listeners.delete(fn); }

  async start() {
    if (this.running) return;
    this._off = this.session.on('frame', (frame) => {
      const tag = decodeStreamFrame(frame);
      if (tag) this._listeners.forEach((fn) => fn(tag));
    });
    this.running = true;
    try { await this.session.send(ackCommand(START_STREAM)); } catch (e) { this._cleanup(); throw e; }
  }

  async stop() {
    if (!this.running) return;
    this._cleanup();
    await this.session.send(ackCommand(STOP_STREAM)).catch(() => {});
  }

  /** "Read once": run the stream for a fixed window, then stop. */
  async readFor(ms) {
    await this.start();
    await new Promise((r) => setTimeout(r, ms));
    await this.stop();
  }

  _cleanup() { this.running = false; this._off?.(); this._off = null; }
}

const MAX_ROWS = 5000;

/** Aggregates reads by EPC. */
export class TagTable {
  constructor() { this.rows = new Map(); this.dropped = 0; }
  add(tag, now = Date.now()) {
    let row = this.rows.get(tag.epc);
    if (!row) {
      if (this.rows.size >= MAX_ROWS) { this.dropped++; return; }
      row = { epc: tag.epc, count: 0, firstSeen: now, bestRssi: -Infinity };
      this.rows.set(tag.epc, row);
    }
    row.count += tag.readCount ?? 1;
    if (tag.rssi !== undefined) { row.rssi = tag.rssi; row.bestRssi = Math.max(row.bestRssi, tag.rssi); }
    if (tag.antenna !== undefined) row.antenna = tag.antenna;
    if (tag.frequencyKhz !== undefined) row.frequencyKhz = tag.frequencyKhz;
    row.lastSeen = now;
  }
  list() { return [...this.rows.values()].sort((a, b) => b.lastSeen - a.lastSeen); }
  clear() { this.rows.clear(); this.dropped = 0; }
  toCsv() {
    const head = 'epc,count,rssi_dbm,best_rssi_dbm,antenna,frequency_khz,first_seen,last_seen';
    const lines = this.list().map((r) => [r.epc, r.count, r.rssi ?? '', Number.isFinite(r.bestRssi) ? r.bestRssi : '', r.antenna ?? '', r.frequencyKhz ?? '', new Date(r.firstSeen).toISOString(), new Date(r.lastSeen).toISOString()].join(','));
    return [head, ...lines].join('\n') + '\n';
  }
}
```

- [ ] **Step 4: Run and confirm pass**

Run: `cd ura-web && npm test`
Expected: all tests pass (`ℹ pass 41`).

- [ ] **Step 5: Commit**

```bash
git add ura-web
git commit -m "feat(ura-web): add streaming tag reader and aggregating tag table" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 6: App shell, Web Serial transport, transport log, demo mode and the Read tab

**Files:**
- Create: `ura-web/index.html`, `ura-web/styles.css`, `ura-web/README.md`, `ura-web/src/log.js`, `ura-web/src/demo.js`, `ura-web/src/app.js`, `ura-web/src/transport/webserial.js`, `ura-web/src/ui/dom.js`, `ura-web/src/ui/read.js`, `ura-web/src/ui/logview.js`

**Interfaces:**
- Consumes: `ReaderSession`, `NoResponseError`, `TagReader`, `TagTable`, `cmd`, `MockReader`, `STREAM_LAYOUT`, `DEFAULT_FLAGS`.
- Produces: `WebSerialTransport` (`static supported`, `static request()`); `TransportLog` (`add`, `onChange`, `clear`, `toText`); `createDemoTransport()`; UI helpers `h`, `download`, `describeError`; the shared `app` object with `log`, `table`, `session`, `reader`, `setConnected[]` (callbacks `(on:boolean)=>void|Promise`), `onTag`, `onReadingChanged`, `showError(e)`, `clearBanner()`. Tab modules export `mountX(root, app)`.

There is no unit-testable logic here that is not already covered, so this task is verified in the browser with Demo mode.

- [ ] **Step 1: Write `ura-web/index.html`**

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Universal Reader Assistant (Web)</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <header class="bar">
    <h1>Universal Reader Assistant</h1>
    <div id="status" class="status" role="status" aria-live="polite">Not connected</div>
    <div class="actions">
      <button id="btn-connect" class="primary">Connect reader</button>
      <button id="btn-demo">Demo mode</button>
      <button id="btn-disconnect" hidden>Disconnect</button>
    </div>
  </header>
  <div id="banner" class="banner" role="alert" hidden></div>
  <nav class="tabs" role="tablist">
    <button role="tab" data-tab="read" aria-selected="true">Read</button>
    <button role="tab" data-tab="settings" aria-selected="false">Settings</button>
    <button role="tab" data-tab="memory" aria-selected="false">Tag memory</button>
    <button role="tab" data-tab="log" aria-selected="false">Log</button>
  </nav>
  <main>
    <section id="tab-read" role="tabpanel"></section>
    <section id="tab-settings" role="tabpanel" hidden></section>
    <section id="tab-memory" role="tabpanel" hidden></section>
    <section id="tab-log" role="tabpanel" hidden></section>
  </main>
  <script type="module" src="src/app.js"></script>
</body>
</html>
```

- [ ] **Step 2: Write `ura-web/styles.css`**

```css
:root {
  --bg: #f6f7f9; --panel: #ffffff; --text: #1b1f24; --muted: #5b6573; --line: #d8dde4;
  --accent: #1f6feb; --accent-text: #ffffff; --warn-bg: #fff4d6; --warn-text: #6b4a00; --bad-bg: #ffe3e0; --bad-text: #7a1b12;
  --ok: #1a7f37; --mono: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
@media (prefers-color-scheme: dark) {
  :root { --bg: #0f1216; --panel: #171b21; --text: #e6e9ee; --muted: #9aa5b4; --line: #2a313b; --accent: #4c8dff; --accent-text: #0b0f14;
    --warn-bg: #3a2f10; --warn-text: #ffd479; --bad-bg: #3d1a16; --bad-text: #ffb4aa; --ok: #3fb950; }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--text); font: 15px/1.45 system-ui, -apple-system, Segoe UI, sans-serif; }
.bar { display: flex; flex-wrap: wrap; gap: 12px 20px; align-items: center; padding: 12px 16px; background: var(--panel); border-bottom: 1px solid var(--line); }
.bar h1 { font-size: 17px; margin: 0; }
.status { color: var(--muted); flex: 1; min-width: 200px; }
.status.ok { color: var(--ok); }
.actions { display: flex; gap: 8px; }
button, select, input { font: inherit; color: var(--text); background: var(--panel); border: 1px solid var(--line); border-radius: 6px; padding: 6px 12px; }
button { cursor: pointer; }
button:hover:not(:disabled) { border-color: var(--accent); }
button:disabled { opacity: .5; cursor: not-allowed; }
button.primary { background: var(--accent); color: var(--accent-text); border-color: var(--accent); }
button.danger { border-color: var(--bad-text); color: var(--bad-text); }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.banner { margin: 12px 16px 0; padding: 10px 14px; border-radius: 6px; background: var(--warn-bg); color: var(--warn-text); }
.banner.bad { background: var(--bad-bg); color: var(--bad-text); }
.tabs { display: flex; gap: 4px; padding: 12px 16px 0; overflow-x: auto; }
.tabs button { border-radius: 6px 6px 0 0; border-bottom: none; }
.tabs button[aria-selected="true"] { background: var(--accent); color: var(--accent-text); border-color: var(--accent); }
main { padding: 0 16px 24px; }
section { background: var(--panel); border: 1px solid var(--line); border-radius: 0 6px 6px 6px; padding: 16px; }
.row { display: flex; flex-wrap: wrap; gap: 8px 12px; align-items: center; margin-bottom: 12px; }
.row label { display: flex; gap: 6px; align-items: center; color: var(--muted); }
.card { border: 1px solid var(--line); border-radius: 8px; padding: 12px; margin-bottom: 12px; }
.card h3 { margin: 0 0 8px; font-size: 14px; }
.note { color: var(--muted); font-size: 13px; }
table { width: 100%; border-collapse: collapse; }
th, td { text-align: left; padding: 6px 8px; border-bottom: 1px solid var(--line); }
td.mono, .mono, textarea.log { font-family: var(--mono); font-size: 13px; }
td.num { text-align: right; font-variant-numeric: tabular-nums; }
.table-wrap { overflow-x: auto; }
textarea.log { width: 100%; height: 55vh; background: var(--bg); color: var(--text); border: 1px solid var(--line); border-radius: 6px; padding: 8px; }
input[type="text"] { min-width: 260px; }
@media (max-width: 600px) { input[type="text"] { min-width: 0; width: 100%; } }
```

- [ ] **Step 3: Write `ura-web/src/log.js`**

```js
import { hex } from './protocol/frame.js';

/** Ring buffer of every TX/RX chunk, downloadable as text. */
export class TransportLog {
  constructor(max = 5000) { this.entries = []; this.max = max; this._listeners = new Set(); }
  add({ dir, bytes, note = '' }) {
    this.entries.push({ t: Date.now(), dir, hex: hex(bytes), note });
    if (this.entries.length > this.max) this.entries.splice(0, this.entries.length - this.max);
    this._listeners.forEach((fn) => fn());
  }
  onChange(fn) { this._listeners.add(fn); return () => this._listeners.delete(fn); }
  clear() { this.entries.length = 0; this._listeners.forEach((fn) => fn()); }
  toText() { return this.entries.map((e) => `${new Date(e.t).toISOString()} ${e.dir.toUpperCase()} ${e.hex}${e.note ? '  # ' + e.note : ''}`).join('\n') + '\n'; }
}
```

- [ ] **Step 4: Write `ura-web/src/transport/webserial.js`**

```js
/** Web Serial transport (Chrome/Edge). Implements: open(baud), close(), write(bytes), onData(cb), onClose(cb), isOpen. */
export class WebSerialTransport {
  static get supported() { return typeof navigator !== 'undefined' && 'serial' in navigator; }

  /** Shows the browser's port picker. Rejects with NotFoundError if the user cancels. */
  static async request() {
    const port = await navigator.serial.requestPort();
    return new WebSerialTransport(port);
  }

  constructor(port) {
    this.port = port;
    this.isOpen = false;
    this._data = null;
    this._close = null;
    this._reader = null;
    this._loop = null;
    port.addEventListener?.('disconnect', () => this._handleLost());
  }

  onData(cb) { this._data = cb; }
  onClose(cb) { this._close = cb; }

  async open(baud) {
    if (this.isOpen) await this.close();
    await this.port.open({ baudRate: baud, dataBits: 8, stopBits: 1, parity: 'none', flowControl: 'none', bufferSize: 4096 });
    this.isOpen = true;
    this._loop = this._readLoop();
  }

  async _readLoop() {
    this._reader = this.port.readable.getReader();
    try {
      for (;;) {
        const { value, done } = await this._reader.read();
        if (done) break;
        if (value?.length) this._data?.(value);
      }
    } catch {
      this._handleLost(); // device unplugged or fatal read error
    } finally {
      try { this._reader.releaseLock(); } catch { /* already released */ }
    }
  }

  _handleLost() {
    if (!this.isOpen) return;
    this.isOpen = false;
    this._close?.();
  }

  async write(bytes) {
    if (!this.isOpen) throw new Error('port is not open');
    const writer = this.port.writable.getWriter();
    try { await writer.write(bytes); } finally { writer.releaseLock(); }
  }

  async close() {
    const wasOpen = this.isOpen;
    this.isOpen = false;
    try { await this._reader?.cancel(); } catch { /* ignore */ }
    try { await this._loop; } catch { /* ignore */ }
    try { await this.port.close(); } catch { /* ignore */ }
    return wasOpen;
  }
}
```

- [ ] **Step 5: Write `ura-web/src/demo.js`**

```js
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
  const state = { region: 1, power: 2700, session: 0, target: [1, 0], encoding: 2, tari: 0, timer: null };
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
```

- [ ] **Step 6: Write `ura-web/src/ui/dom.js`**

```js
/** Tiny element helper: h('button', { onclick }, 'Label'). */
export function h(tag, attrs = {}, ...children) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k.startsWith('on')) el.addEventListener(k.slice(2), v);
    else if (k === 'class') el.className = v;
    else if (v === true) el.setAttribute(k, '');
    else if (v !== false && v != null) el.setAttribute(k, v);
  }
  for (const c of children.flat()) el.append(c instanceof Node ? c : document.createTextNode(String(c)));
  return el;
}

export function download(filename, text, type = 'text/plain') {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const a = h('a', { href: url, download: filename });
  document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/** Describe an error for the user: reader errors carry a hint. */
export function describeError(e) {
  return e?.hint ? `${e.message}. ${e.hint}` : (e?.message ?? String(e));
}
```

- [ ] **Step 7: Write `ura-web/src/ui/read.js`**

```js
import { h, download, describeError } from './dom.js';

export function mountRead(root, app) {
  const start = h('button', { class: 'primary' }, 'Start reading');
  const once = h('button', {}, 'Read once (3 s)');
  const clear = h('button', {}, 'Clear');
  const exportBtn = h('button', {}, 'Export CSV');
  const summary = h('span', { class: 'note' });
  const tbody = h('tbody');
  const table = h('div', { class: 'table-wrap' }, h('table', {}, h('thead', {}, h('tr', {}, ...['EPC', 'Reads', 'RSSI (dBm)', 'Best', 'Ant', 'Freq (kHz)', 'Last seen'].map((t) => h('th', {}, t)))), tbody));
  root.append(h('div', { class: 'row' }, start, once, clear, exportBtn, summary), table);

  let dirty = true;
  const render = () => {
    if (!dirty) return;
    dirty = false;
    const rows = app.table.list();
    summary.textContent = `${rows.length} unique tag${rows.length === 1 ? '' : 's'}${app.table.dropped ? ` (${app.table.dropped} new tags ignored: table full)` : ''}`;
    tbody.replaceChildren(...rows.slice(0, 500).map((r) => h('tr', {},
      h('td', { class: 'mono' }, r.epc), h('td', { class: 'num' }, r.count), h('td', { class: 'num' }, r.rssi ?? ''),
      h('td', { class: 'num' }, Number.isFinite(r.bestRssi) ? r.bestRssi : ''), h('td', { class: 'num' }, r.antenna ?? ''),
      h('td', { class: 'num' }, r.frequencyKhz ?? ''), h('td', {}, new Date(r.lastSeen).toLocaleTimeString()))));
  };
  setInterval(render, 250);
  app.onTag = (tag) => { app.table.add(tag); dirty = true; };

  const setRunning = (running) => {
    start.textContent = running ? 'Stop reading' : 'Start reading';
    start.classList.toggle('danger', running);
    start.classList.toggle('primary', !running);
    once.disabled = running;
  };
  app.onReadingChanged = setRunning;

  start.addEventListener('click', async () => {
    try {
      if (app.reader.running) await app.reader.stop(); else await app.reader.start();
      setRunning(app.reader.running);
    } catch (e) { app.showError(e); setRunning(false); }
  });
  once.addEventListener('click', async () => {
    try { setRunning(true); await app.reader.readFor(3000); } catch (e) { app.showError(e); } finally { setRunning(false); }
  });
  clear.addEventListener('click', () => { app.table.clear(); dirty = true; render(); });
  exportBtn.addEventListener('click', () => download(`tags-${new Date().toISOString().replace(/[:.]/g, '-')}.csv`, app.table.toCsv(), 'text/csv'));
  app.setConnected.push((on) => { start.disabled = once.disabled = !on; if (!on) setRunning(false); });
  start.disabled = once.disabled = true;
  render();
}
```

- [ ] **Step 8: Write `ura-web/src/ui/logview.js`**

```js
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
```

- [ ] **Step 9: Write `ura-web/src/app.js`** (Settings and Tag memory tabs are added in Task 7)

```js
import { WebSerialTransport } from './transport/webserial.js';
import { createDemoTransport } from './demo.js';
import { ReaderSession, NoResponseError } from './reader/session.js';
import { TagReader, TagTable } from './reader/reading.js';
import { TransportLog } from './log.js';
import { cmd } from './protocol/commands.js';
import { describeError } from './ui/dom.js';
import { mountRead } from './ui/read.js';
import { mountLog } from './ui/logview.js';

const $ = (id) => document.getElementById(id);
const app = {
  log: new TransportLog(), table: new TagTable(), session: null, reader: null,
  setConnected: [], onTag: null, onReadingChanged: null,
  showError(e) { banner(describeError(e), e instanceof NoResponseError ? 'bad' : e?.status === 0x0504 ? 'warn' : 'bad'); },
  clearBanner() { $('banner').hidden = true; },
};
const banner = (text, kind = 'bad') => { const b = $('banner'); b.textContent = text; b.className = `banner ${kind === 'warn' ? '' : 'bad'}`; b.hidden = false; };

mountRead($('tab-read'), app);
mountLog($('tab-log'), app);

for (const tab of document.querySelectorAll('[role=tab]')) {
  tab.addEventListener('click', () => {
    document.querySelectorAll('[role=tab]').forEach((t) => t.setAttribute('aria-selected', String(t === tab)));
    document.querySelectorAll('[role=tabpanel]').forEach((p) => { p.hidden = p.id !== `tab-${tab.dataset.tab}`; });
  });
}

let tempTimer = null;
async function setConnected(on, text) {
  $('btn-connect').hidden = $('btn-demo').hidden = on;
  $('btn-disconnect').hidden = !on;
  $('status').textContent = text;
  $('status').classList.toggle('ok', on);
  clearInterval(tempTimer);
  for (const fn of app.setConnected) await fn(on);
  if (on) tempTimer = setInterval(updateTemp, 5000);
}

async function updateTemp() {
  if (!app.session || app.reader.running) return;
  try {
    const t = await app.session.send(cmd.temperature());
    $('status').textContent = `${$('status').dataset.base} · ${t} °C`;
  } catch (e) { app.showError(e); }
}

async function connect(transport) {
  app.clearBanner();
  app.session = new ReaderSession(transport, { log: app.log });
  app.reader = new TagReader(app.session);
  app.reader.onTag((tag) => app.onTag?.(tag));
  app.session.on('disconnect', async () => {
    app.reader.running = false;
    app.onReadingChanged?.(false);
    banner('Reader disconnected.', 'bad');
    await setConnected(false, 'Not connected');
  });
  try {
    const info = await app.session.connect();
    const base = `Connected · ${info.serial ?? 'reader'} · fw ${info.firmware} · ${app.session.baud} baud`;
    $('status').dataset.base = base;
    await setConnected(true, base);
    updateTemp();
  } catch (e) {
    app.showError(e);
    await transport.close().catch(() => {});
    await setConnected(false, 'Not connected');
  }
}

$('btn-connect').addEventListener('click', async () => {
  if (!WebSerialTransport.supported) return banner('This browser has no Web Serial support. Use Chrome or Edge, or try Demo mode.', 'bad');
  let transport;
  try { transport = await WebSerialTransport.request(); } catch (e) {
    if (e?.name === 'NotFoundError') return; // user closed the picker
    return app.showError(e);
  }
  await connect(transport);
});
$('btn-demo').addEventListener('click', () => connect(createDemoTransport()));
$('btn-disconnect').addEventListener('click', async () => {
  try { if (app.reader.running) await app.reader.stop(); } catch { /* ignore */ }
  await app.session.disconnect();
  await setConnected(false, 'Not connected');
});

if (!WebSerialTransport.supported) banner('This browser has no Web Serial support. Use Chrome or Edge for real readers; Demo mode works anywhere.', 'warn');
```

- [ ] **Step 10: Write `ura-web/README.md`**

```markdown
# ura-web

Browser version of SparkFun's Universal Reader Assistant for the M7E module. Needs Chrome or Edge (Web Serial).

## Run

    cd ura-web
    python3 -m http.server 8080

Open http://localhost:8080, click **Connect reader** and pick the serial port, or click **Demo mode** to try it with a fake reader.

## Test

    npm test

## Notes
- Writes and locks are off until you tick "Enable writes" on the Tag memory tab.
- Firmware update, kill and permanent locks are intentionally not available.
- The Log tab records every byte sent and received; download it when reporting a problem.
```

- [ ] **Step 11: Smoke-test in the browser**

Run: `cd ura-web && python3 -m http.server 8080` and open `http://localhost:8080` in Chrome.
Expected, in order:
1. The Read tab shows with a disabled "Start reading" button and status "Not connected".
2. Click **Demo mode**: status turns green and reads like `Connected · DEMO001 · fw 01.09.00.00 · 115200 baud · 4x °C`.
3. Click **Start reading**: within 2 seconds three EPCs appear and their Reads counts grow; the button reads "Stop reading".
4. Click **Stop reading**, then **Export CSV**: a `.csv` downloads with a header and 3 rows.
5. Open the **Log** tab: the first lines are `TX FF 00 03 1D 0C` followed by an `RX FF 14 03 00 00 …` line.
6. Click **Disconnect**: status returns to "Not connected" and the Start button disables.
7. The browser console shows no errors.
8. In Safari or Firefox (no Web Serial), the page shows the yellow "no Web Serial support" banner, and **Demo mode** still works.
9. In Chrome, click **Connect reader** and then cancel the port picker: no error banner appears.

- [ ] **Step 12: Commit**

```bash
git add ura-web
git commit -m "feat(ura-web): add app shell, Web Serial transport, transport log, demo mode and Read tab" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Settings and Tag memory tabs

**Files:**
- Create: `ura-web/src/ui/settings.js`, `ura-web/src/ui/memory.js`
- Modify: `ura-web/src/app.js` (imports and mounts)

**Interfaces:**
- Consumes: `cmd`, `cmdTag`, `GEN2`, `TARGETS`, `REGIONS`, `BANK`, `clampPower`, `hexToBytes`; the `app` object from Task 6 (`session`, `reader`, `table`, `setConnected`, `showError`, `clearBanner`).

- [ ] **Step 1: Write `ura-web/src/ui/settings.js`**

```js
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
  app.setConnected.push(async (on) => { if (on) { try { await reload(); } catch (e) { app.showError(e); } } });
}
```

- [ ] **Step 2: Write `ura-web/src/ui/memory.js`**

```js
import { h, describeError } from './dom.js';
import { cmdTag, BANK, hexToBytes } from '../protocol/commands.js';

export function mountMemory(root, app) {
  const epc = h('input', { type: 'text', placeholder: 'EPC of the target tag (hex)', 'aria-label': 'Target EPC', class: 'mono' });
  const pick = h('select', { 'aria-label': 'Choose from tags seen' });
  const password = h('input', { type: 'text', value: '00000000', size: 10, class: 'mono', 'aria-label': 'Access password (hex)' });
  const enable = h('input', { type: 'checkbox', id: 'enable-writes' });
  const out = h('pre', { class: 'mono note', role: 'status' });
  const newEpc = h('input', { type: 'text', placeholder: 'new EPC (hex, whole words)', class: 'mono' });
  const addr = h('input', { type: 'number', value: 0, min: 0, style: 'width:6em', 'aria-label': 'Word address' });
  const words = h('input', { type: 'number', value: 2, min: 1, max: 32, style: 'width:5em', 'aria-label': 'Word count' });
  const data = h('input', { type: 'text', placeholder: 'data (hex, whole words)', class: 'mono' });
  const area = h('select', {}, ['epc', 'user', 'tid', 'access', 'kill'].map((a) => h('option', { value: a }, a)));

  const refreshPick = () => pick.replaceChildren(h('option', { value: '' }, 'tags seen…'), ...app.table.list().slice(0, 100).map((r) => h('option', { value: r.epc }, r.epc)));
  pick.addEventListener('focus', refreshPick);
  pick.addEventListener('change', () => { if (pick.value) epc.value = pick.value; });

  const pw = () => { const b = hexToBytes(password.value); if (b.length !== 4) throw new Error('password must be 4 bytes (8 hex digits)'); return ((b[0] << 24) | (b[1] << 16) | (b[2] << 8) | b[3]) >>> 0; };
  const run = (label, needsWrite, fn) => async () => {
    try {
      if (needsWrite && !enable.checked) throw new Error('Turn on "Enable writes" first.');
      if (!epc.value.trim()) throw new Error('Enter the EPC of the tag to operate on.');
      if (app.reader.running) await app.reader.stop();
      out.textContent = `${label}…`;
      out.textContent = `${label}: ${await fn()}`;
      app.clearBanner();
    } catch (e) { out.textContent = ''; app.showError(e); }
  };
  const sure = (msg) => { if (!confirm(msg)) throw new Error('Cancelled.'); };
  const target = () => epc.value.replace(/\s+/g, '').toUpperCase();

  root.append(
    h('div', { class: 'card' }, h('h3', {}, 'Target tag'),
      h('div', { class: 'row' }, epc, pick, h('label', {}, 'Password', password)),
      h('div', { class: 'row' }, h('label', {}, enable, 'Enable writes'),
        h('span', { class: 'note' }, 'Every operation is aimed at the EPC above, so other tags in range are not touched.'))),
    h('div', { class: 'card' }, h('h3', {}, 'Write EPC'),
      h('div', { class: 'row' }, newEpc, h('button', { class: 'danger', onclick: run('Write EPC', true, async () => {
        sure(`Change EPC of ${target()} to ${newEpc.value.trim().toUpperCase()}?`);
        await app.session.send(cmdTag.writeEpc({ epc: target(), newEpc: newEpc.value, password: pw() }));
        epc.value = newEpc.value.replace(/\s+/g, '').toUpperCase();
        return `done. Target is now ${epc.value}. Read again to confirm.`;
      }) }, 'Write EPC'))),
    h('div', { class: 'card' }, h('h3', {}, 'User memory'),
      h('div', { class: 'row' }, h('label', {}, 'Word address', addr), h('label', {}, 'Words', words),
        h('button', { onclick: run('Read user memory', false, async () => app.session.send(cmdTag.readData({ epc: target(), bank: BANK.USER, wordAddress: Number(addr.value), wordCount: Number(words.value), password: pw() }))) }, 'Read')),
      h('div', { class: 'row' }, data, h('button', { class: 'danger', onclick: run('Write user memory', true, async () => {
        const want = data.value.replace(/\s+/g, '').toUpperCase();
        sure(`Write ${want} to user memory word ${addr.value} of ${target()}?`);
        await app.session.send(cmdTag.writeData({ epc: target(), bank: BANK.USER, wordAddress: Number(addr.value), dataHex: want, password: pw() }));
        const back = await app.session.send(cmdTag.readData({ epc: target(), bank: BANK.USER, wordAddress: Number(addr.value), wordCount: want.length / 4, password: pw() }));
        if (back !== want) throw new Error(`Read-back mismatch: wrote ${want}, read ${back}.`);
        return `written and verified (${back}).`;
      }) }, 'Write'))),
    h('div', { class: 'card' }, h('h3', {}, 'Lock'),
      h('div', { class: 'row' }, area,
        h('button', { class: 'danger', onclick: run('Lock', true, async () => {
          sure(`Lock the ${area.value} area of ${target()}? Writes will then need the access password.`);
          await app.session.send(cmdTag.lock({ epc: target(), area: area.value, locked: true, password: pw() })); return 'locked.';
        }) }, 'Lock'),
        h('button', { class: 'danger', onclick: run('Unlock', true, async () => {
          sure(`Unlock the ${area.value} area of ${target()}?`);
          await app.session.send(cmdTag.lock({ epc: target(), area: area.value, locked: false, password: pw() })); return 'unlocked.';
        }) }, 'Unlock')),
      h('p', { class: 'note' }, 'Permanent locks are not offered.')),
    out);
}
```

- [ ] **Step 3: Wire both tabs into `ura-web/src/app.js`**

Add after the existing `import { mountRead } from './ui/read.js';` line:

```js
import { mountSettings } from './ui/settings.js';
import { mountMemory } from './ui/memory.js';
```

Add after the line `mountRead($('tab-read'), app);`:

```js
mountSettings($('tab-settings'), app);
mountMemory($('tab-memory'), app);
```

- [ ] **Step 4: Run the unit tests (nothing should regress)**

Run: `cd ura-web && npm test`
Expected: `ℹ pass 41`.

- [ ] **Step 5: Smoke-test in the browser with Demo mode**

Run: `cd ura-web && python3 -m http.server 8080`, open `http://localhost:8080`, click **Demo mode**.
Expected:
1. **Settings** tab: Region lists `NA, EU, KR, IN, JP, PRC, AU, NZ` with NA selected; power shows `27` with the note `Allowed 0–30 dBm`; Gen2 shows `S0 / A / M4 / 25 µs`.
2. Type `45` into Read power and click **Apply**: the field snaps back to `30` (clamped to the module maximum) and no error banner appears.
3. **Tag memory** tab: click **Write** with "Enable writes" unticked: the banner says `Turn on "Enable writes" first.`
4. Pick a tag from the "tags seen…" list after reading (EPC fills in), tick **Enable writes**, type `CAFEBABE` into the data field and click **Write**, accept the confirm dialog: the output says `written and verified (CAFEBABE).`
5. Click **Read**: output shows `CAFEBABE`. Console has no errors.

- [ ] **Step 6: Commit**

```bash
git add ura-web
git commit -m "feat(ura-web): add Settings and Tag memory tabs" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 8: Hardware verification gate

This is a human-in-the-loop task. Every payload marked unverified is checked here, and the results decide whether the old monitor may be removed. **If the module does not respond, stop here: do not run Task 9.**

**Files:**
- Create: `docs/protocol/verification.md`, `ura-web/test/fixtures/stream-frame.hex`, `ura-web/test/fixtures/stream-frame.expected.json`, `ura-web/test/stream-fixture.test.js`
- Modify: `ura-web/src/reader/reading.js` (only if the checks below require it), `docs/protocol/m7e-serial-protocol.md` (mark verified items)

- [ ] **Step 1: Cross-check constants against the public SparkFun Arduino library**

```bash
curl -fsSL https://raw.githubusercontent.com/sparkfun/SparkFun_Simultaneous_RFID_Tag_Reader_Library/master/src/SparkFun_UHF_RFID_Reader.cpp -o /tmp/sparkfun_uhf.cpp
grep -n -A6 "startReading\|stopReading\|void RFID::setRegion\|setReadPower\|setTagProtocol\|disableReadFilter" /tmp/sparkfun_uhf.cpp | head -120
```

Compare against `START_STREAM`, `STOP_STREAM` (reading.js), the region/power/protocol opcodes (commands.js: `97`, `92`, `93`). If any differ, fix the constant and its test in the same commit and note it in `docs/protocol/verification.md`.

- [ ] **Step 2: Create `docs/protocol/verification.md`**

```markdown
# M7E hardware verification

Module: ______  Firmware (from the Connect status line): ______  Cable/adapter: ______  Date: ______

Run `cd ura-web && python3 -m http.server 8080` and use Chrome. Mark each row Pass / Fail with the exact hex from the Log tab for any failure.

| # | Check | Expected | Result |
|---|-------|----------|--------|
| 1 | Connect | status shows serial and firmware; log starts `TX FF 00 03 1D 0C` | |
| 2 | Temperature | plausible number (15–60 °C) | |
| 3 | Region | list loads; setting NA/your region succeeds | |
| 4 | Read power | limits load; setting 20 dBm succeeds and re-reads as 20 | |
| 5 | Gen2 session/target/encoding/tari | reload returns what was applied | |
| 6 | Start reading with one known tag | tag appears, RSSI plausible, Reads grows | |
| 7 | Stop reading | tags stop; no stray frames in the log | |
| 8 | Read once (3 s) | tag appears once and reading stops | |
| 9 | Read user memory of a spare tag | returns the memory contents | |
| 10 | Write user memory + read-back on a spare tag | "written and verified" | |
| 11 | Write EPC on a spare tag, then read | new EPC appears | |
| 12 | Lock EPC then unlock on a spare tag (password 00000000 unless set) | both report success; write while locked fails with MEMORY_LOCKED | |
| 13 | Unplug the cable while reading | banner "Reader disconnected."; UI resets | |

Silent module (log shows no RX at any baud): try a different data-capable USB cable, check the UART/USB switch, check the adapter's RX/TX are not swapped, and try another adapter. The Connect error says `silent` for no bytes and `garbled` for bytes without a valid frame.
```

- [ ] **Step 3: Run the checklist on the real module and fill in the Result column**

Use spare tags for rows 9–12. Any Fail blocks Task 9 until fixed: capture the hex from the Log tab, correct the builder in `commands.js` or the constants in `reading.js`, update the matching test with the corrected bytes, and re-run the row.

- [ ] **Step 4: Capture a real streaming frame as a fixture**

In the Log tab after row 6, download the log and copy one `RX` line whose third byte is `22` (the line starts `RX FF xx 22 00 00`) into `ura-web/test/fixtures/stream-frame.hex`, one frame per file, bytes separated by spaces. Create `ura-web/test/fixtures/stream-frame.expected.json` containing the EPC of the physical tag you read, for example:

```json
{ "epc": "E28011606000020A10F2428D" }
```

- [ ] **Step 5: Write `ura-web/test/stream-fixture.test.js`**

```js
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fromHex, parseResponse } from '../src/protocol/frame.js';
import { decodeStreamFrame } from '../src/reader/reading.js';

const dir = new URL('./fixtures/', import.meta.url);

test('a frame captured from a real module decodes to the expected EPC', () => {
  const bytes = fromHex(readFileSync(new URL('stream-frame.hex', dir), 'utf8'));
  const { frame } = parseResponse(bytes);
  const tag = decodeStreamFrame(frame);
  const expected = JSON.parse(readFileSync(new URL('stream-frame.expected.json', dir), 'utf8'));
  assert.ok(tag, 'frame did not decode: adjust STREAM_LAYOUT in reading.js');
  assert.equal(tag.epc, expected.epc);
});
```

- [ ] **Step 6: Run it; if it fails, fix the layout**

Run: `cd ura-web && npm test`
If `frame did not decode`, read the hex: the tag record starts at the read-count byte (a small number) followed by RSSI (`0xB0`–`0xE8`), and the metadata flags are the two bytes just before it. Count their positions inside `frame.data` (frame byte index minus 5) and set `STREAM_LAYOUT.flagsAt` and `STREAM_LAYOUT.recordAt` in `reading.js` to match. Update `streamFrameData()` usage in `reading.test.js` only if it hard-codes offsets (it uses `STREAM_LAYOUT`, so it should not need changing).
Expected after the fix: all tests pass, including `a frame captured from a real module decodes to the expected EPC`.

- [ ] **Step 7: Mark verified items in `docs/protocol/m7e-serial-protocol.md`**

Append a section `## Hardware-verified (date, firmware)` listing each payload from the checklist rows that passed.

- [ ] **Step 8: Commit**

```bash
git add docs ura-web
git commit -m "test(ura-web): verify protocol on hardware and add real stream fixture" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 9: Retire the old reader monitor and update docs

Run only after Task 8's rows 1, 2, 6, 7 and 13 pass.

**Files:**
- Delete: `reader_standalone/` (all files), `start_reader_monitor.sh`, `start_reader_monitor.bat`
- Modify: `README.md`, `WINDOWS_SETUP.md`, `CHANGELOG_COLLAB.md`

- [ ] **Step 1: Confirm nothing else depends on the old monitor**

Run: `grep -rn "reader_standalone\|start_reader_monitor" --include="*.py" --include="*.sh" --include="*.bat" --include="*.service" --include="*.conf" . | grep -v "^./reader_standalone/" | grep -v "^./.venv"`
Expected: only `start_reader_monitor.sh` and `start_reader_monitor.bat` themselves. If anything else matches, stop and ask.

- [ ] **Step 2: Delete the old monitor**

```bash
git rm -r reader_standalone start_reader_monitor.sh start_reader_monitor.bat
git commit -m "chore: remove Python reader monitor, replaced by ura-web" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 3: Update `README.md`**

Replace these two lines in the Quick Start Mac/Linux block:
`./start_webapp.sh           # dashboard       → http://127.0.0.1:8000` and `./start_reader_monitor.sh   # reader monitor  → http://127.0.0.1:8010` with:

```bash
./start_webapp.sh           # dashboard       → http://127.0.0.1:8000
cd ura-web && python3 -m http.server 8080   # reader tool → http://localhost:8080 (Chrome/Edge)
```

Replace the two lines in the Windows block (`start_webapp.bat ...` and `start_reader_monitor.bat ...`) with:

```cmd
start_webapp.bat            :: dashboard       → http://127.0.0.1:8000
cd ura-web && python -m http.server 8080   :: reader tool → http://localhost:8080 (Chrome/Edge)
```

Replace the whole `## Standalone Reader Monitor (Separate App)` section (heading through its last bullet, ending `- If the module is stuck or handshake fails, use **raw mode** (Advanced panel → Skip handshake).`) with:

```markdown
## Browser Reader Tool (`ura-web/`)

A browser version of SparkFun's Universal Reader Assistant for the M7E. It talks to the reader directly over Web Serial, so it needs **Chrome or Edge** and no Python.

- Run: `cd ura-web && python3 -m http.server 8080`, open http://localhost:8080, click **Connect reader**.
- **Demo mode** works without hardware.
- Writes and locks are off until you tick **Enable writes**. Firmware update, kill and permanent locks are not offered.
- The **Log** tab records every byte sent and received. Download it when reporting a problem.
- Tests: `cd ura-web && npm test`. Hardware verification record: `docs/protocol/verification.md`.
```

- [ ] **Step 4: Update `WINDOWS_SETUP.md`**

Replace everything from the heading `## 4. Run the Standalone Reader Monitor` up to (not including) the `---` line before `## 5. Environment Variables` with:

````markdown
## 4. Run the Browser Reader Tool

The reader tool runs in Chrome or Edge and talks to the reader over Web Serial (no Python needed).

```cmd
cd ura-web
python -m http.server 8080
```

Open **http://localhost:8080** and click **Connect reader**. Pick the reader's COM port (the CH340 adapter, e.g. `COM3`) in the browser's port chooser. Check Device Manager → Ports (COM & LPT) if the port is missing. The default baud rate is 115200 and the tool probes other rates automatically.

Use **Demo mode** to try the interface without hardware. The **Log** tab shows every byte exchanged, which is the first thing to check if the reader does not respond.

> Firefox and Safari do not support Web Serial.
````

In section 7, replace the entry `### Port does not appear in the dropdown` heading with `### Port does not appear in the browser's port chooser`. Replace the sentence in `### "Access is denied" on COM port` that reads `(Arduino IDE, another terminal, the reader monitor itself)` with `(Arduino IDE, another terminal, another browser tab)`. Replace the whole `### App shows "Connected" but no tags appear` entry with:

```markdown
### Connected but no tags appear
- Confirm the M7E antenna is attached (a bare module with no antenna will not read).
- Open the **Log** tab. If you see `TX` lines but no `RX` lines, the module is not answering: try a different data-capable USB cable or adapter. The Connect error will say "silent".
- If `RX` bytes appear but are rejected, the baud rate or wiring is wrong. The Connect error will say "garbled".
```

- [ ] **Step 5: Append a `CHANGELOG_COLLAB.md` entry**

Insert before the `## Operational Notes For Claude/Codex` heading:

```markdown
### 2026-10-14 — Browser URA replaces Python reader monitor (Claude)
- agent: Claude
- branch: `feat/browser-ura`
- scope: new `ura-web/` Web Serial reader tool; removed `reader_standalone/` and `start_reader_monitor.*`
- summary:
  - Reverse-engineered the M7E serial protocol from SparkFun's URA 6.3.29.29 (MercuryAPI 1.37.3.29); facts in `docs/protocol/m7e-serial-protocol.md`, hardware results in `docs/protocol/verification.md`.
  - `ura-web/` implements connect with baud probing, read/stream, region/power/Gen2 settings, write EPC, user memory, lock, and a downloadable hex transport log. Firmware update, kill and permanent lock are deliberately not included.
- risks_followups:
  - Gen2 Q and BLF settings, Authenticate/Untraceable, and posting tags to the dashboard `/ingest` endpoint are not implemented.
  - Web Serial works only in Chrome/Edge.
```

- [ ] **Step 6: Run both test suites**

Run: `cd ura-web && npm test` then `cd .. && .venv/bin/python -m pytest tests -q`
Expected: ura-web passes; the backend tests pass as before (they do not touch `reader_standalone`).

- [ ] **Step 7: Commit**

```bash
git add README.md WINDOWS_SETUP.md CHANGELOG_COLLAB.md
git commit -m "docs: point README, Windows guide and changelog at the browser reader tool" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

## Self-Review Notes

- **Spec coverage:** connect/probe/diagnostics (Tasks 4, 6); read/stream/CSV/read-once (Tasks 5, 6); settings and thermal warning (Tasks 2, 7; the temperature hint lives in `status.js`, shown through `showError`); tag memory with writes gate (Tasks 2, 7); transport log (Task 6); safety allow-list (Task 2); testing strategy and fixtures (Tasks 1–5, 8); repo cleanup (Tasks 1, 9); verification of unverified payloads (Task 8). Spec items intentionally deferred are listed under Global Constraints.
- **Type consistency:** `cmd`/`cmdTag` builders all return `{opcode, bytes, parse}`; `session.send` takes that shape; `TagReader` builds the same shape locally for opcode `2F`; `app.setConnected` callbacks and `app.onTag`/`app.onReadingChanged` are defined in Task 6 and only consumed afterwards.
