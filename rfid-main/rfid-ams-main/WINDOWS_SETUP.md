# Windows Setup Guide — RFID AMS

This guide covers running both the **main dashboard** and the **standalone reader monitor** on Windows 10/11.

---

## Requirements

| Tool | Version | Download |
|---|---|---|
| Python | 3.10 or later | https://www.python.org/downloads/ |
| Git | any recent | https://git-scm.com/download/win |
| CH340 USB-serial driver | latest | https://www.wch-ic.com/downloads/CH341SER_EXE.html |

> **Python install tip:** During installation tick **"Add Python to PATH"** and **"pip"**. After installing, open a new Command Prompt and verify:
> ```
> python --version
> pip --version
> ```

---

## 1. Clone the Repository

```cmd
git clone https://github.com/JomVill/rfid-ams.git
cd rfid-ams
```

---

## 2. Install the CH340 Driver (for the RFID reader)

The SparkFun M7E-Nano uses a WCH CH340 USB-to-serial adapter. Windows does not ship this driver by default.

1. Download `CH341SER.EXE` from https://www.wch-ic.com/downloads/CH341SER_EXE.html
2. Run the installer as Administrator and click **Install**.
3. Plug in your USB-serial adapter.
4. Open **Device Manager** (Win + X → Device Manager) and expand **Ports (COM & LPT)**.
5. You should see an entry like `USB-SERIAL CH340 (COM3)` — note the COM number, you will need it.

> **Charge-only cable warning:** Many USB-C and micro-USB cables are charge-only and carry no data. If the adapter does not appear in Device Manager after installing the driver, try a different cable.

---

## 3. Run the Main Dashboard

Double-click **`start_webapp.bat`** — or from Command Prompt:

```cmd
start_webapp.bat
```

This will automatically:
- Create a Python virtual environment (`.venv\`)
- Install dependencies from `requirements-windows.txt`
- Run database migrations (`alembic upgrade head`)
- Seed default admin account
- Start the web server

Open your browser at: **http://127.0.0.1:8000**

**Default login:**
- Username: `admin`
- Password: `admin123`

> Change the admin password in production by setting the `AMS_ADMIN_PASSWORD` environment variable before first run.

### Manual start (alternative)

```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-windows.txt
alembic upgrade head
python -m backend.app.seed
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

---

## 4. Run the Standalone Reader Monitor

Double-click **`start_reader_monitor.bat`** — or from Command Prompt:

```cmd
start_reader_monitor.bat
```

Open your browser at: **http://127.0.0.1:8010**

### Connecting the M7E-Nano on Windows

1. Plug the reader's USB-serial adapter into your PC.
2. Check Device Manager for the COM port number (e.g. `COM3`).
3. In the reader monitor UI, the port dropdown should automatically show the COM port as a **likely reader** candidate.
4. If it doesn't appear, open the **Advanced** panel and type the port manually (e.g. `COM3`).
5. Leave baud rate at **115200** (the M7E-Nano default).
6. Click **Connect to Reader**.

> **COM ports above 9 (COM10+):** Windows requires the `\\.\COM10` format for these. The app handles this automatically when you select or type the port.

### Raw (skip-handshake) mode

If the reader is stuck in continuous-read mode or its RX wire is unreliable:

1. Expand the **Advanced** panel.
2. Tick **Skip handshake (raw mode)**.
3. Click **Connect Raw (no handshake)**.

The app will send the full setup sequence (stop → Gen2 protocol → antenna → region → power) without waiting for acknowledgements.

### CLI debug tool (advanced)

For low-level byte inspection without the browser UI:

```cmd
.venv\Scripts\activate
python -m reader_standalone.debug_terminal COM3
```

Or list detected ports:

```cmd
python -m reader_standalone.debug_terminal --list
```

---

## 5. Environment Variables

Create a `.env` file in the repo root (never commit this file):

```env
# Admin credentials (override seed defaults)
AMS_ADMIN_USERNAME=admin
AMS_ADMIN_EMAIL=admin@example.com
AMS_ADMIN_PASSWORD=your-secure-password

# Device ingest token (for scanner clients)
AMS_INGEST_DEVICE_TOKEN=your-device-token
AMS_API_TOKEN=your-api-token
```

---

## 6. Running as a Windows Service (optional)

To run the dashboard automatically on startup, use [NSSM](https://nssm.cc/):

```cmd
:: Download nssm.exe and place it somewhere on your PATH, then:
nssm install rfid-ams-web "C:\path\to\rfid-ams\.venv\Scripts\uvicorn.exe"
nssm set rfid-ams-web AppParameters "backend.app.main:app --host 127.0.0.1 --port 8000"
nssm set rfid-ams-web AppDirectory "C:\path\to\rfid-ams"
nssm start rfid-ams-web
```

---

## 7. Troubleshooting

### "python is not recognized"
Python is not on your PATH. Re-run the Python installer, tick "Add Python to PATH", then open a **new** Command Prompt.

### "pip is not recognized"
Run: `python -m ensurepip --upgrade`

### Port does not appear in the dropdown
- Check Device Manager → Ports (COM & LPT). If absent, the driver is not installed or the cable is charge-only.
- After installing/reinstalling the CH340 driver, unplug and replug the adapter.
- Try a different USB port or a different cable.

### "Access is denied" on COM port
Another application (Arduino IDE, another terminal, the reader monitor itself) is already holding the port. Close it first. Only one process can open a serial port at a time.

### App shows "Connected" but no tags appear
- Confirm the M7E antenna is attached (bare module with no antenna will not read).
- Try **raw mode** (see section 4) to bypass the handshake.
- Use the CLI debug tool to check if any bytes come back from the module after sending a `stop` or `version` command. If nothing comes back, the RX wire may be broken — try a different cable.

### `alembic upgrade head` fails
Delete `backend/app/app.db` and re-run — this only works on a fresh dev database. For production, do not delete the DB; check the migration error message instead.

### `uvloop` install error
`uvloop` is not available on Windows. Use `requirements-windows.txt` (already done by the bat scripts), which omits it. Uvicorn runs fine without it on Windows.

---

## 8. What's Different on Windows vs Mac/Pi

| Feature | Mac / Pi | Windows |
|---|---|---|
| Serial port format | `/dev/cu.usbserial-N` | `COM3`, `COM10` (auto-prefixed to `\\.\COM10`) |
| CH340 driver | System extension (WCH DriverKit) | `CH341SER.EXE` installer |
| Launcher | `./start_webapp.sh` | `start_webapp.bat` |
| Requirements | `requirements.txt` | `requirements-windows.txt` (no `uvloop`) |
| Dialout group | Required on Pi | Not applicable |
| Port auto-detect | Ranks `/dev/cu.wchusbserial*` highest | Ranks COM ports with CH340/FTDI description highest |
