# Browser URA (Universal Reader Assistant) — Design

Status: draft for review · Date: 2026-10-14 · Branch: `codex/plan-standalone-mac-app-for`

## 1. Purpose

A browser version of SparkFun's Universal Reader Assistant for the M7E (ThingMagic M6e-family) module. It runs on Mac, Windows and Linux in Chrome/Edge, with no Python process between the browser and the reader. It replaces `reader_standalone/` and keeps the repo focused on the AMS dashboard plus this tool.

Success looks like: plug in an M7E over USB/serial, open the page, click Connect, and read tags, change power/region, and write EPC/user memory, with every serial byte inspectable in a log.

**Assumptions (from the user's decisions):** Web Serial API only (Chrome/Edge; Safari/Firefox unsupported); URA parity for the common tabs, not every feature; cleanup of the repo comes first.

## 2. Evidence base

The protocol was derived from the URA 6.3.29.29 installer (WiX bundle → MSI → `MercuryAPI.dll` 1.37.3.29), decompiled with ILSpy for analysis only. Findings are in `docs/protocol/m7e-serial-protocol.md`. **Clean-room rule:** the implementation is written from those documented facts (frame layout, opcodes, field orders), never by copying decompiled vendor code. Anything marked unverified there must be cross-checked against the public SparkFun Arduino library and real hardware before it is trusted.

## 3. Architecture

New top-level directory `ura-web/`. Plain ES modules, no framework, no bundler, no runtime dependencies. Served by any static server (`localhost` counts as a secure context for Web Serial). Tests use Node's built-in `node --test`.

```
ura-web/
  index.html
  src/
    protocol/        pure functions, no I/O (the testable core)
      crc.js         CRC-16 poly 0x1021, init 0xFFFF
      frame.js       build request / parse response (FF|LEN|OP|[STATUS]|DATA|CRC)
      opcodes.js     opcode + enum tables (region, protocol, Gen2 banks)
      commands.js    one builder + one parser per supported command
      tagrecord.js   metadata-flag-ordered tag record parser
      status.js      status code -> error object (e.g. temperature, invalid region)
    transport/
      webserial.js   Web Serial wrapper (open/close/read loop/write)
      mock.js        scripted fake reader for tests and demo mode
    reader/
      session.js     connect, baud probe, command queue, timeouts, events
      reading.js     continuous read start/stop, tag stream, de-dup/aggregation
    ui/              tabs: Connect, Settings, Read, Write EPC, User Memory, Lock, Log
    log/             transport log (hex tx/rx, timestamps, download)
  test/              frame/crc/commands/tagrecord/session vs mock
```

Boundaries: `protocol/` knows nothing about serial ports; `transport/` knows nothing about commands; `reader/session.js` is the only place that combines them; the UI talks only to `session`.

## 4. Behaviors

**Connect.** `navigator.serial.requestPort()` (user gesture), open at 115200 8N1. If the version query (`FF 00 03 1D 0C`) gets no valid reply, probe 9600, 921600, 19200, 38400, 57600, 230400, 460800 (the URA's order). On success read version (firmware, hardware, supported protocols), serial number and temperature, then select Gen2. If the module is in boot/bootloader state, send boot-firmware (`04`) and re-query. Surfaces a clear "no response" diagnostic that distinguishes no bytes at all (wiring/cable/RX) from bytes with a bad CRC (baud/noise).

**Read.** Start/stop continuous read (streaming opcode `2F`), configurable metadata (EPC, RSSI, antenna, frequency, read count, timestamp), with a results table that aggregates by EPC, shows count/RSSI/last seen, and exports CSV. A one-shot "read once" mode uses the timed read + tag buffer (`22` then `29`) rather than an app-level timer.

**Settings.** Region (from the module's supported list), read/write power (with the module's limits), Gen2 session/target/Q/BLF/tari/encoding, antenna port check, and temperature readout. A thermal-fault status raises a warning that tells the user to lower power or add heatsinking, as the URA does.

**Tag memory.** Write EPC, read/write user memory, lock/unlock with access password. Writes and locks are disabled until the user turns on "Enable writes".

**Transport log.** Every TX/RX frame is recorded as hex with timestamps and a decoded label, and downloadable. This is the debugging tool for the earlier RX problem.

## 5. Safety rules

- Command allow-list in `commands.js`: no flash write/erase/modify (`07`, `0D`, `0F`), no bootloader entry (`09`), no firmware load, no kill (`26`). Firmware update and kill are out of scope for v1 because a bad flash can brick an expensive module.
- Writes (EPC, user memory, lock) are off by default per session and show the target EPC and payload before sending.
- Power is clamped to the limits the module reports; region change warns that the region must match local regulations.
- Changing the baud rate (`06`) is allowed only through the probe/connect path, never as a free-form command.

## 6. Out of scope for v1

Firmware update, kill, Authenticate/Untraceable (Gen2v2), LLRP/network readers, non-Gen2 protocols, multi-antenna routing UI, saving/loading config files, and sending tags to the AMS dashboard. The session emits tag events so a later `POST /ingest/tag-read` adapter is a small addition.

## 7. Testing

- Golden vectors: CRC and frames (`[00 03]` → `1D 0C`, so version request is `FF 00 03 1D 0C`); every command builder and parser round-tripped against hand-built byte arrays.
- `tagrecord.js` tested for each metadata flag combination, error-flagged data, and PC/XPC handling.
- `session.js` tested against `mock.js`: baud probing order, timeouts, bad CRC, boot-response handling, streaming start/stop.
- A written hardware smoke checklist for a real M7E: connect, version, temperature, read a known tag, set power, write EPC to a spare tag.
- Unverified payloads (streaming start bytes, write EPC/data, lock) are not marked done until compared with the SparkFun library and confirmed on hardware.

## 8. Repo cleanup (done before the app work)

1. Remove tracked junk: `reader_standalone/static/style.css.bak`; make sure `.DS_Store`, `export.json`, `backups/`, `.pytest_cache/`, `__pycache__/` stay ignored (`.gitignore` already covers most).
2. After `ura-web` reaches read/write parity, delete `reader_standalone/`, `start_reader_monitor.sh/.bat`, and its tests; keep `rfid_app/` (the Pi UART scanner) and the dashboard untouched.
3. Update `README.md`, `WINDOWS_SETUP.md` (reader sections become "use Chrome/Edge"), and `CHANGELOG_COLLAB.md`.
4. Everything lands in small commits on a feature branch, with the old monitor removed in its own commit so it is easy to revert.

## 9. Risks and open questions

- Web Serial is Chromium-only and needs a user gesture; documented in the README.
- The old hardware problem (module not sending bytes back) may be a cable or adapter fault; the transport log and the no-bytes diagnostic are meant to expose it, but the app cannot fix hardware.
- URA/MercuryAPI behavior around streaming start bytes varies by firmware; v1 targets the user's module and records its firmware in the log.
- Serving: v1 is a static folder with a one-line launcher; mounting it under the FastAPI dashboard is a later option.
