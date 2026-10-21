# RFID AMS

RFID Asset Management System for lab inventory control.

## Quick Start

### Mac / Linux
```bash
./start_webapp.sh           # dashboard       → http://127.0.0.1:8000
./start_reader_monitor.sh   # reader monitor  → http://127.0.0.1:8010
```

### Windows
```cmd
start_webapp.bat            :: dashboard       → http://127.0.0.1:8000
start_reader_monitor.bat    :: reader monitor  → http://127.0.0.1:8010
```

> **Windows users:** see **[WINDOWS_SETUP.md](WINDOWS_SETUP.md)** for driver install, COM port setup, and troubleshooting.

Both launchers auto-run: venv check/create → dependency install → Alembic migrations → seed → Uvicorn.

Default login: `admin` / `admin123`

---
## One-Command Web App Start
```bash
./start_webapp.sh
```

Alternative:
```bash
make web
```

This will auto-run:
- venv check/create
- dependency check/install
- Alembic migrations
- seed defaults
- Uvicorn startup

## Standalone Reader Monitor (Separate App)
This is independent from the dashboard/webapp and intended for safe serial monitoring and tag viewing.

```bash
./start_reader_monitor.sh
```

Open: `http://127.0.0.1:8010`

Notes:
- Safe mode is ON by default (no write/config commands sent).
- Best first connection for expensive modules: USB serial (`/dev/ttyUSB0`).

## What this MVP includes
- FastAPI backend + HTML admin UI
- SQLite database with Alembic migrations
- Admin-only Tag Registry CRUD (`/tags` + `/ui/tags`)
- Room scan sessions with reconciliation logic
- Missing asset alerts after 2 consecutive scans
- Transfer and incomplete workstation-group anomaly detection
- Headless scanner worker for Raspberry Pi (UART M7E)
- Offline queue + retry sync for ingest client

## Standalone Reader Monitor (Separate App)

Independent from the dashboard — safe serial monitoring and RFID tag viewing.

| Platform | Command | URL |
|---|---|---|
| Mac / Linux | `./start_reader_monitor.sh` | http://127.0.0.1:8010 |
| Windows | `start_reader_monitor.bat` | http://127.0.0.1:8010 |

Notes:
- Safe mode is ON by default (no write/config commands sent).
- Best first connection for expensive modules: USB serial (`/dev/ttyUSB0` on Pi, `COM3` on Windows).
- If the module is stuck or handshake fails, use **raw mode** (Advanced panel → Skip handshake).

## Repository workflow (Mac → GitHub → Pi)
1. Develop on Mac in a feature branch.
2. Push branch and open PR to `main`.
3. Merge PR.
4. On Pi: pull `main`, run setup/update, restart services.

## Local dev quickstart

### Mac / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m backend.app.seed
uvicorn backend.app.main:app --reload
```

### Windows
```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-windows.txt
alembic upgrade head
python -m backend.app.seed
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Open: `http://127.0.0.1:8000/login`

Default seed admin (change for production):
- username: `admin`
- password: `admin123`

## Scanner auth/env
`/ingest/tag-read` accepts:
- user JWT with `admin` or `technician` role
- or static device token via `AMS_INGEST_DEVICE_TOKEN`

Scanner client sends token with `AMS_API_TOKEN`.

## Key APIs
- Auth: `/auth/*`
- Assets: `/assets/*`
- Tag registry (admin CRUD): `/tags/*`
- Inventory:
  - `POST /inventory/rooms`
  - `POST /inventory/groups`
  - `POST /inventory/sessions`
  - `POST /inventory/sessions/{id}/observe`
  - `POST /inventory/sessions/{id}/close`
  - `GET /inventory/anomalies`

## Inventory policy defaults
- Max unique tags per scan session: `150`
- Overflow behavior: ignore new unique EPCs after limit and mark `limit_reached=true`
- Missing rule: anomaly opens after 2 consecutive closed sessions where expected EPC is absent

## Raspberry Pi 5 deployment (Pi OS Lite 64-bit)
```bash
cd /opt
sudo git clone https://github.com/JomVill/rfid-ams.git rfid-ams
cd /opt/rfid-ams
sudo bash deploy/setup_pi.sh
```

After setup:
```bash
sudo systemctl status backend.service
sudo systemctl status scanner.service
curl http://127.0.0.1:8000/health
```

## Runtime files on Pi
- Env file: `/etc/rfid-ams/rfid-ams.env`
- DB (default): `/opt/rfid-ams/backend/app/app.db`
- Services:
  - `backend.service`
  - `scanner.service`

## Smoke checks
```bash
# backend health
curl http://127.0.0.1:8000/health

# login token (example)
curl -X POST http://127.0.0.1:8000/auth/login -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}'
```
