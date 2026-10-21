# RFID AMS — M7E Browser Reader (proof of concept)

This repo currently holds a **browser version of SparkFun's Universal Reader Assistant** for the M7E UHF RFID module. It proves the reader and its serial protocol work before the main **CCS Laboratory Asset Management System** is built: an anti-theft system for university computer labs where PCs, monitors, keyboards and mice carry RFID tags, running on a Raspberry Pi with the M7E attached.

It runs in **Chrome or Edge** and talks to the reader directly over Web Serial. It needs no Python and no server beyond a static file host.

## Run

```bash
cd ura-web
python3 -m http.server 8080
```

Open http://localhost:8080 in Chrome or Edge, click **Connect reader** and pick the reader's serial port. **Demo mode** works without hardware.

- On connect it asks for the radio region (the M7E forgets it at power-up) and remembers your last choice.
- **Read:** start/stop streaming, read once, a table per EPC with RSSI, antenna and frequency, CSV export.
- **Settings:** region, read power (clamped to the module's limits), Gen2 session/target/encoding/tari.
- **Tag memory:** write EPC, read/write user memory with read-back, lock/unlock. Off until you tick **Enable writes**.
- **Log:** every byte sent and received, downloadable.
- Firmware update, kill and permanent locks are deliberately not available.

Arc, Safari, Firefox and embedded app browsers cannot show the serial port chooser. Use Chrome or Edge. On Windows, install the CH340 driver first.

## Test

```bash
cd ura-web && npm test     # Node 20+
```

## Status

Verified on a real M7E (firmware 02.01.06.08, CH340 adapter, macOS, Chrome): connect, firmware/serial/temperature, region, streaming reads. Write EPC, user-memory write, lock and Gen2 values are not yet verified on hardware; see Task 8 in the plan.

## Docs

- [docs/protocol/m7e-serial-protocol.md](docs/protocol/m7e-serial-protocol.md): M7E frame format, CRC, opcodes and tag record layout, reverse-engineered from the URA 6.3.29.29 installer
- [docs/superpowers/specs/2026-10-14-browser-ura-design.md](docs/superpowers/specs/2026-10-14-browser-ura-design.md): design
- [docs/superpowers/plans/2026-10-14-browser-ura.md](docs/superpowers/plans/2026-10-14-browser-ura.md): implementation plan and hardware checklist

## History

The earlier dashboard (FastAPI), Pi scanner and Python reader monitor are in git history before this cleanup. They will be rebuilt as the main asset management system.
