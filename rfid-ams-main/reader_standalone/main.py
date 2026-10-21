"""Standalone RFID reader monitor — SparkFun M6E/M7E Mercury API serial protocol.

Frame format (sent):
    FF [LEN] [OP] [DATA...] [CRC_H] [CRC_L]
    CRC-16/CCITT over bytes [LEN, OP, DATA...]

Frame format (received response):
    FF [LEN] [OP] [S_H] [S_L] [DATA...] [CRC_H] [CRC_L]
    The two extra status bytes mean a response with LEN=N is LEN+7 bytes total.
    CRC is still over [LEN, OP, S_H, S_L, DATA...].

Tag record (opcode 0x22, LEN != 0x00 and LEN != 0x0A):
    [0]  FF          Header
    [1]  LEN         payload length
    [2]  22          opcode
    [3]  S_H         status high (must be 0x00)
    [4]  S_L         status low  (must be 0x00)
    [5..11]          RFU (7 bytes)
    [12] RSSI        unsigned byte; signed = RSSI - 256
    [13] ANT         antenna ID (4 MSB = TX port, 4 LSB = RX port)
    [14..16]         frequency kHz (3 bytes big-endian)
    [17..20]         timestamp ms (4 bytes big-endian)
    [21..22]         phase
    [23]             protocol ID
    [24..25]         embedded tag-data bit count (big-endian)  → M bits → ceil(M/8) bytes
    [26..26+M-1]     embedded tag data (M bytes, may be 0)
    [26+M]           RFU
    [27+M..28+M]     EPC bit count (big-endian)  → epcBytes = bits/8 - 4
    [29+M..30+M]     PC word (EPC Protocol Control)
    [31+M..31+M+epcBytes-1]  EPC data
    ...              EPC CRC, message CRC
"""
from __future__ import annotations

import os
import re
import threading
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import serial  # type: ignore
import serial.tools.list_ports  # type: ignore
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Opcode constants
# ---------------------------------------------------------------------------
TMR_SR_OPCODE_VERSION = 0x03
TMR_SR_OPCODE_SET_BAUD_RATE = 0x06
TMR_SR_OPCODE_READ_TAG_ID_SINGLE = 0x21
TMR_SR_OPCODE_READ_TAG_ID_MULTIPLE = 0x22
TMR_SR_OPCODE_MULTI_PROTOCOL_TAG_OP = 0x2F
TMR_SR_OPCODE_SET_ANTENNA_PORT = 0x91
TMR_SR_OPCODE_SET_TAG_PROTOCOL = 0x93
TMR_SR_OPCODE_SET_READ_TX_POWER = 0x92
TMR_SR_OPCODE_SET_REGION = 0x97
TMR_SR_OPCODE_SET_READER_OPTIONAL_PARAMS = 0x9A

# ---------------------------------------------------------------------------
# Region constants  (user setting: 1=NA, 4=PH/India, 5=JP, 6=CN, 8=EU, 11=AU, 255=Open)
# ---------------------------------------------------------------------------
REGION_NORTHAMERICA = 0x01
REGION_INDIA = 0x04
REGION_JAPAN = 0x05
REGION_CHINA = 0x06
REGION_EUROPE = 0x08
REGION_KOREA = 0x09
REGION_AUSTRALIA = 0x0B
REGION_NEWZEALAND = 0x0C
REGION_NORTHAMERICA2 = 0x0D
REGION_NORTHAMERICA3 = 0x0E
REGION_PHILIPPINES = 0x12  # Mercury API TMR_REGION_PH — used by JADAK URA for PH
REGION_OPEN = 0xFF

# ---------------------------------------------------------------------------
# Internal response classification codes (mirror SparkFun library)
# ---------------------------------------------------------------------------
ALL_GOOD = 0
ERROR_COMMAND_RESPONSE_TIMEOUT = 1
ERROR_CORRUPT_RESPONSE = 2
ERROR_WRONG_OPCODE_RESPONSE = 3
RESPONSE_IS_KEEPALIVE = 6
RESPONSE_IS_TEMPERATURE = 5
RESPONSE_IS_TEMPTHROTTLE = 7
RESPONSE_IS_TAGFOUND = 8
RESPONSE_IS_HIGHRETURNLOSS = 13

SCAN_MODE_CONTINUOUS = "continuous"
SCAN_MODE_SINGLE = "single"

# Tag protocol: GEN2 = 0x0005
TAG_PROTOCOL_GEN2 = 0x0005

# ---------------------------------------------------------------------------
# Connection state machine
# ---------------------------------------------------------------------------
CONN_DISCONNECTED = "disconnected"   # no port open
CONN_OPENING = "opening"             # port open, version probe in flight
CONN_CONNECTED = "connected"         # version confirmed, heartbeat healthy
CONN_STALE = "stale"                 # port open, heartbeat missed — recovering
CONN_LOST = "lost"                   # port error or heartbeat exhausted

# ---------------------------------------------------------------------------
# Port classification (Mac, Raspberry Pi OS, Windows)
# ---------------------------------------------------------------------------
PORT_LIKELY_READER = "likely_reader"   # /dev/cu.usbserial-*, /dev/ttyUSB*, COMx with CH340/FTDI desc
PORT_MAYBE_SERIAL = "maybe_serial"     # other real USB-serial devices
PORT_NOT_READER = "not_reader"         # Bluetooth, debug-console, etc.

# Regex patterns for port classification — ordered most-likely-first for rank
_READER_PATTERNS = [
    (100, re.compile(r"^/dev/cu\.wchusbserial", re.IGNORECASE)),       # Mac CH340/CH341 (WCH driver)
    (95, re.compile(r"^/dev/cu\.usbserial", re.IGNORECASE)),           # Mac generic USB-serial
    (90, re.compile(r"^/dev/cu\.SLAB_USBtoUART", re.IGNORECASE)),      # Mac CP210x
    (90, re.compile(r"^/dev/ttyUSB\d+$")),                             # Pi/Linux USB-serial
    (85, re.compile(r"^/dev/ttyACM\d+$")),                             # Pi/Linux CDC-ACM
    (80, re.compile(r"^/dev/cu\.usbmodem", re.IGNORECASE)),            # Mac CDC-ACM
    (90, re.compile(r"^COM\d+$", re.IGNORECASE)),                      # Windows COM port
    (90, re.compile(r"^\\\\\.\\.+COM\d+$", re.IGNORECASE)),            # Windows \\.\COMx (high-number)
]
_EXCLUDE_PATTERNS = [
    re.compile(r"Bluetooth", re.IGNORECASE),
    re.compile(r"debug-console", re.IGNORECASE),
    re.compile(r"WirelessDialUp", re.IGNORECASE),
    re.compile(r"iPhone", re.IGNORECASE),
]
# Windows: description keywords that boost a COM port to likely_reader
_WINDOWS_READER_DESC = re.compile(
    r"CH340|CH341|USB-SERIAL|USB Serial|FT232|FTDI|CP210|Silicon Labs|USB to UART|USB2\.0-Ser",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# CRC-16/CCITT (poly 0x1021, init 0xFFFF) — same table as SparkFun library
# ---------------------------------------------------------------------------
_CRC_TABLE = [
    0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50A5, 0x60C6, 0x70E7,
    0x8108, 0x9129, 0xA14A, 0xB16B, 0xC18C, 0xD1AD, 0xE1CE, 0xF1EF,
]


def _calc_crc(buf: bytes | bytearray) -> int:
    """CRC-16/CCITT over the given bytes.  Input should be [LEN, OP, DATA...]."""
    crc = 0xFFFF
    for b in buf:
        crc = ((crc << 4) | (b >> 4)) & 0xFFFF
        crc ^= _CRC_TABLE[(crc >> 12) & 0x0F]
        crc = ((crc << 4) | (b & 0x0F)) & 0xFFFF
        crc ^= _CRC_TABLE[(crc >> 12) & 0x0F]
    return crc & 0xFFFF


def _build_frame(opcode: int, data: bytes = b"") -> bytes:
    """Build a Mercury API request frame: FF [LEN] [OP] [DATA...] [CRC_H] [CRC_L]."""
    msg = bytearray()
    msg.append(0xFF)
    msg.append(len(data) & 0xFF)
    msg.append(opcode & 0xFF)
    msg.extend(data)
    crc = _calc_crc(msg[1:])  # CRC over LEN + OP + DATA
    msg.append((crc >> 8) & 0xFF)
    msg.append(crc & 0xFF)
    return bytes(msg)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------
@dataclass
class TagRow:
    epc: str
    rssi: float | None
    antenna: int | None
    count: int
    first_seen: str
    last_seen: str


# ---------------------------------------------------------------------------
# Response frame parser (stateless helpers)
# ---------------------------------------------------------------------------
def _pop_next_response_frame(buf: bytearray) -> tuple[bytes, bool] | None:
    """Try to extract one complete, CRC-valid response frame from buf (in-place).

    Returns (frame_bytes, has_status) or None if not enough data yet.
    - has_status=True  → response frame: FF LEN OP S_H S_L DATA CRC_H CRC_L  (total = LEN+7)
    - has_status=False → bare frame:     FF LEN OP DATA CRC_H CRC_L           (total = LEN+5)
    """
    while True:
        # Find the 0xFF header byte
        try:
            start = buf.index(0xFF)
        except ValueError:
            buf.clear()
            return None
        if start > 0:
            del buf[:start]
        if len(buf) < 3:
            return None

        length = buf[1]
        # A response frame (with status bytes) is LEN+7 bytes total.
        # A sent/bare frame is LEN+5 bytes total.
        # We try statusful first (more common for responses), then statusless.
        candidates: list[tuple[int, bool]] = []
        if len(buf) >= length + 7:
            candidates.append((length + 7, True))
        if len(buf) >= length + 5:
            candidates.append((length + 5, False))

        matched = False
        for frame_len, has_status in candidates:
            frame = bytes(buf[:frame_len])
            # CRC covers everything from byte 1 to byte frame_len-3 inclusive
            calc = _calc_crc(frame[1:-2])
            got = (frame[-2] << 8) | frame[-1]
            if calc == got:
                del buf[:frame_len]
                return frame, has_status

        if candidates:
            # Header byte present but no CRC match — skip this header byte and retry
            del buf[0]
            continue

        # Not enough data to form any candidate frame yet
        return None


def _parse_tag_frame(frame: bytes) -> dict[str, Any] | None:
    """Parse a tag-found response frame (opcode 0x22, has_status=True).

    Returns dict with 'epc', 'rssi', 'antenna' or None on parse error.
    The frame is:  FF LEN OP S_H S_L [RFU×7] RSSI ANT FREQ×3 TS×4 PH×2 PROTO TDBITS×2 [TDDATA×M] RFU EPCBITS×2 PC×2 EPC... EPCCRC×2 MSGCRC×2
    Indices (absolute in frame):
        [0]  FF
        [1]  LEN
        [2]  0x22
        [3]  S_H
        [4]  S_L
        [5..11] RFU  (7 bytes)
        [12] RSSI (unsigned; signed = val - 256)
        [13] ANT
        [14..16] freq
        [17..20] timestamp
        [21..22] phase
        [23] protocol
        [24..25] tag-data bit count  → M = ceil(bits/8)
        [26..26+M-1] tag data
        [26+M] RFU
        [27+M..28+M] EPC bit count
        [29+M..30+M] PC word
        [31+M..31+M+epcBytes-1] EPC bytes
    """
    if len(frame) < 7:
        return None
    if frame[0] != 0xFF or frame[2] != TMR_SR_OPCODE_READ_TAG_ID_MULTIPLE:
        return None
    # Must be a statusful frame with status 0x0000
    if frame[3] != 0x00 or frame[4] != 0x00:
        return None
    # Classify: keepalive has LEN==0x00, temperature has LEN==0x0A
    length = frame[1]
    if length == 0x00 or length == 0x0A:
        return None  # keepalive or temperature — not a tag record

    # Need at least up to tag-data bit count bytes (index 25)
    if len(frame) < 26:
        return None

    try:
        # RSSI
        rssi_raw = frame[12]
        rssi = rssi_raw - 256  # signed dBm

        # Antenna
        ant_byte = frame[13]
        tx_port = (ant_byte >> 4) & 0x0F
        # rx_port = ant_byte & 0x0F  (usually same as tx)
        antenna = tx_port if tx_port > 0 else (ant_byte & 0x0F)

        # Embedded tag-data length (bits at [24:26])
        td_bits = (frame[24] << 8) | frame[25]
        td_bytes = td_bits // 8 + (1 if td_bits % 8 else 0)  # ceil(td_bits/8)
        M = td_bytes

        # EPC bit count at [27+M:29+M]
        epc_bits_idx = 27 + M
        if len(frame) < epc_bits_idx + 2:
            return None
        epc_bits = (frame[epc_bits_idx] << 8) | frame[epc_bits_idx + 1]
        epc_bytes_total = epc_bits // 8
        # Subtract 4: first 2 bytes = PC word (already before EPC), last 2 = EPC CRC
        epc_bytes = epc_bytes_total - 4
        if epc_bytes <= 0:
            return None

        # EPC starts at [31+M]
        epc_start = 31 + M
        epc_end = epc_start + epc_bytes
        if epc_end > len(frame) - 2:  # -2 for message CRC
            return None

        epc = frame[epc_start:epc_end].hex().upper()
        return {"epc": epc, "rssi": rssi, "antenna": antenna}

    except (IndexError, Exception):
        return None


def _classify_0x22_frame(frame: bytes) -> int:
    """Classify an opcode-0x22 response frame.  Returns one of the RESPONSE_IS_* constants."""
    if len(frame) < 5:
        return ERROR_CORRUPT_RESPONSE
    length = frame[1]
    if length == 0x00:
        # keepalive — check status bytes at [3:5]
        if len(frame) < 5:
            return ERROR_CORRUPT_RESPONSE
        status = (frame[3] << 8) | frame[4]
        if status == 0x0400:
            return RESPONSE_IS_KEEPALIVE
        elif status == 0x0504:
            return RESPONSE_IS_TEMPTHROTTLE
        elif status == 0x0505:
            return RESPONSE_IS_HIGHRETURNLOSS
        return RESPONSE_IS_KEEPALIVE  # unknown keepalive variant
    elif length == 0x0A:
        return RESPONSE_IS_TEMPERATURE
    else:
        return RESPONSE_IS_TAGFOUND


# ---------------------------------------------------------------------------
# Main reader state machine
# ---------------------------------------------------------------------------
class ReaderState:
    def __init__(self) -> None:
        self.port: str | None = None
        self.baudrate: int = 115200
        self.safe_mode: bool = True
        self.read_mode: str = SCAN_MODE_CONTINUOUS
        self.antenna_port: int = 1
        self.region: int = REGION_PHILIPPINES
        self.read_power: int = 2700
        # Explicit connection state machine; `connected` is kept as a derived
        # convenience flag (True only when conn_state == CONN_CONNECTED).
        self.conn_state: str = CONN_DISCONNECTED
        self.connected: bool = False
        self.conn_detail: str | None = None   # human-readable status subtext
        self.scanning: bool = False
        self.version_text: str | None = None
        self._ser: serial.Serial | None = None
        self._thread: threading.Thread | None = None
        self._heartbeat_thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self.logs: deque[str] = deque(maxlen=500)
        self.tags: dict[str, TagRow] = {}
        self._rx = bytearray()
        self._last_scan_start: float | None = None
        self._scan_session_tag_count: int = 0
        self._last_rx_time: float | None = None
        self._last_activity_ts: float = 0.0   # any RX from reader (heartbeat uses this)
        self._heartbeat_misses: int = 0

    def _set_conn_state(self, new_state: str, detail: str | None = None) -> None:
        """Single point for state transitions — keeps `connected` consistent."""
        with self._lock:
            self.conn_state = new_state
            self.conn_detail = detail
            self.connected = (new_state == CONN_CONNECTED)

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------
    def _now(self) -> str:
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    def _log(self, message: str) -> None:
        with self._lock:
            self.logs.appendleft(f"[{self._now()}] {message}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def connect(
        self,
        port: str,
        baudrate: int,
        safe_mode: bool,
        read_mode: str,
        skip_handshake: bool = False,
    ) -> None:
        """Open the serial port and bring the reader online.

        skip_handshake=False (default): full Mercury handshake — version probe
            with stop-spam recovery, then region/antenna/power configuration.
            Refuses to mark connected unless the module replies.

        skip_handshake=True: raw mode — open the port, flush briefly, and mark
            connected without confirming the module is alive. No config
            commands are sent. Useful when JADAK URA works but our handshake
            fails (suggests a baud/timing/protocol mismatch in our probe).
            The read loop will still parse any tag frames the module emits.
        """
        if self.connected:
            raise RuntimeError("Already connected")
        normalized_port = self._normalize_port(port)
        self.port = normalized_port
        self.baudrate = baudrate
        self.safe_mode = safe_mode
        self.read_mode = self._normalize_read_mode(read_mode)
        self._set_conn_state(CONN_OPENING, f"Opening {normalized_port} @ {baudrate}")

        try:
            self._open_serial(normalized_port, baudrate)

            if skip_handshake:
                # Raw mode: open, brief drain, mark connected. We don't WAIT
                # for the version probe to succeed — but we DO send the full
                # SparkFun-canonical setup sequence (stop spam → tag protocol
                # Gen2 → antenna → region → read power) fire-and-forget so
                # the module is correctly configured even if it never ACKs.
                #
                # Why this is safe in "raw" mode: each helper catches its own
                # exceptions and just logs, so a silent module won't abort
                # the connect. Each command also has a small inter-command
                # gap so the module's UART input buffer doesn't overflow.
                self._flush_serial(drain_s=0.3)
                self.version_text = "(raw mode — handshake skipped)"
                self._log(
                    f"Raw connect to {normalized_port} @ {baudrate} — "
                    "sending full setup sequence fire-and-forget."
                )
                self.scanning = False
                self._last_activity_ts = time.time()
                self._heartbeat_misses = 0
                self._stop.clear()
                self._thread = threading.Thread(target=self._read_loop, daemon=True)
                self._thread.start()

                # Best-effort recovery: if the module is mid-continuous-read,
                # send the 3-method stop spam + small drain. Don't fail.
                try:
                    self._send_stop_raw()
                    time.sleep(0.3)
                    self._flush_serial(drain_s=0.5)
                except Exception as exc:
                    self._log(f"Stop-spam (raw): {exc}")

                # Full SparkFun setup sequence — each helper has try/except
                # internally, so failures are logged but don't abort connect.
                # 50ms gap between commands matches what JADAK URA does in
                # its transport logs.
                for label, fn in [
                    ("set protocol Gen2", self._set_tag_protocol_gen2),
                    ("set antenna",       self._set_antenna_port),
                    ("set region",        lambda: self._set_region(self.region)),
                    ("set read power",    lambda: self._set_read_power(self.read_power)),
                    ("disable filter",    self._disable_read_filter),
                ]:
                    try:
                        fn()
                    except Exception as exc:
                        self._log(f"raw setup: {label} skipped ({exc})")
                    time.sleep(0.05)

                self._set_conn_state(CONN_CONNECTED, "raw mode")
                return

            # Longer first-attempt drain so a reader that's already in continuous-read
            # mode (from a previous crashed session) can be cleared before the first
            # version probe. Previously 0.6s — often not enough on macOS.
            self._flush_serial(drain_s=1.5)

            version = self._try_version_with_recovery(baudrate)

            if version is None and baudrate != 9600:
                # Final fallback: swap to 9600 in case the reader was reconfigured
                self._log("Retrying at 9600 baud as fallback")
                self._close_serial_quiet()
                self._open_serial(normalized_port, 9600)
                self._flush_serial(drain_s=1.5)
                version = self._try_version_with_recovery(9600)
                if version is not None:
                    self.baudrate = 9600

            if version is not None and version.get("opcode") == TMR_SR_OPCODE_VERSION:
                payload = version.get("payload") or b""
                text = payload.decode("ascii", errors="ignore").strip("\x00 ").strip()
                self.version_text = text if text else "Reader responded"
                self._log(f"Reader identified: {self.version_text}")
            else:
                self._close_serial_quiet()
                self._set_conn_state(CONN_DISCONNECTED, "Reader did not respond to version command")
                raise RuntimeError(
                    "Reader did not respond to version command. "
                    "Try Advanced → 'Skip handshake (raw mode)' if JADAK URA works for you — "
                    "it bypasses the version probe and goes straight to scanning."
                )

            # --- Initialize the reader ---
            self._set_tag_protocol_gen2()
            self._set_antenna_port()
            self._set_region(self.region)
            self._set_read_power(self.read_power)

            # Mark connected only after successful init
            self.scanning = False
            self._last_activity_ts = time.time()
            self._heartbeat_misses = 0
            self._stop.clear()
            self._thread = threading.Thread(target=self._read_loop, daemon=True)
            self._thread.start()
            self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
            self._heartbeat_thread.start()
            self._set_conn_state(CONN_CONNECTED, self.version_text)
            self._log(f"Connected to {normalized_port} @ {self.baudrate} (safe_mode={safe_mode})")

        except Exception:
            self._close_serial_quiet()
            self.scanning = False
            if self.conn_state != CONN_DISCONNECTED:
                self._set_conn_state(CONN_DISCONNECTED, "Connect failed")
            raise

    def _try_version_with_recovery(self, baudrate: int) -> dict[str, Any] | None:
        """Attempt a version probe up to 3 times with escalating stop + DTR recovery."""
        drains = [1.5, 2.0, 2.5]
        probe_timeouts = [1.0, 1.5, 1.5]
        for attempt, (drain_s, timeout_s) in enumerate(zip(drains, probe_timeouts), start=1):
            version = self._request_version_blocking(timeout_s=timeout_s)
            if version is not None and version.get("opcode") == TMR_SR_OPCODE_VERSION:
                return version

            if version is not None:
                self._log(
                    f"Unexpected opcode 0x{version.get('opcode', 0):02X} on attempt {attempt}; "
                    "stopping continuous read and retrying"
                )
            else:
                self._log(
                    f"No version response on attempt {attempt}; "
                    "sending stop commands to clear continuous read mode"
                )
            try:
                self._send_stop_raw()
            except Exception as exc:
                self._log(f"Stop command error: {exc}")
            # DTR toggle — some CH340 adapters reset the module, aborting continuous read
            self._toggle_dtr()
            self._flush_serial(drain_s=drain_s)

        # Final diagnostic: did we ever see bytes?
        raw = self._peek_raw_bytes(0.5)
        if raw:
            self._log(f"Raw bytes from reader (first 64): {raw[:64].hex().upper()}")
        else:
            self._log(
                f"No bytes received from reader at {baudrate} baud — "
                "check cable is data-capable, reader is powered, and CH340 driver is active"
            )
        return None

    def _toggle_dtr(self) -> None:
        """Briefly toggle DTR to reset some USB-serial adapters."""
        if not self._ser:
            return
        try:
            self._ser.dtr = False
            time.sleep(0.05)
            self._ser.dtr = True
            time.sleep(0.05)
        except Exception:
            pass  # Not all backends support DTR control

    def disconnect(self) -> None:
        self.scanning = False
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            self._heartbeat_thread.join(timeout=2.0)
        self._close_serial_quiet()
        self._rx.clear()
        self.version_text = None
        self._last_scan_start = None
        self._scan_session_tag_count = 0
        self._heartbeat_misses = 0
        self._set_conn_state(CONN_DISCONNECTED, None)
        self._log("Disconnected")

    def start_scan(self) -> None:
        if not self.connected:
            raise RuntimeError("Not connected")
        # In raw mode the module hasn't ACK'd anything; commands that wait
        # for a status response (like _disable_read_filter) will hang. Just
        # fire the read command directly and let any tag frames flow.
        raw_mode = self.version_text == "(raw mode — handshake skipped)"
        if not raw_mode:
            try:
                self._disable_read_filter()
            except Exception as exc:
                self._log(f"Filter-disable skipped: {exc}")
        self.scanning = True
        self._last_scan_start = time.time()
        self._scan_session_tag_count = len(self.tags)
        self._send_start_read()
        self._log(f"Scan started ({self.read_mode}{' / raw' if raw_mode else ''})")

    def stop_scan(self) -> None:
        self._send_stop_read()
        self.scanning = False
        self._last_scan_start = None
        self._scan_session_tag_count = 0
        self._log("Scan stopped")

    def clear(self) -> None:
        with self._lock:
            self.tags.clear()
            self.logs.clear()

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "connected": self.connected,
                "conn_state": self.conn_state,
                "conn_detail": self.conn_detail,
                "scanning": self.scanning,
                "port": self.port,
                "baudrate": self.baudrate,
                "safe_mode": self.safe_mode,
                "read_mode": self.read_mode,
                "antenna_port": self.antenna_port,
                "region": self.region,
                "read_power": self.read_power,
                "version": self.version_text,
                "tags": [
                    {
                        "epc": t.epc,
                        "rssi": t.rssi,
                        "antenna": t.antenna,
                        "count": t.count,
                        "first_seen": t.first_seen,
                        "last_seen": t.last_seen,
                    }
                    for t in sorted(self.tags.values(), key=lambda x: x.last_seen, reverse=True)
                ],
                "logs": list(self.logs),
            }

    def send_ascii_command(self, command: str) -> None:
        """Send a raw ASCII command over the serial port (for diagnostics)."""
        if not self.connected or not self._ser:
            raise RuntimeError("Not connected")
        cmd = command.strip()
        if not cmd:
            return
        if self.safe_mode:
            allowed = {"t", "q", "v", "version", "help", "?"}
            if cmd.lower() not in allowed:
                raise RuntimeError(f"Safe mode: command '{cmd}' blocked (allowed: {sorted(allowed)})")
        self._ser.write((cmd + "\r\n").encode("utf-8"))
        self._log(f">>> {cmd}")

    def request_version(self) -> None:
        """Queue a version request (response will be processed by the read loop)."""
        if not self.connected:
            raise RuntimeError("Not connected")
        self._write_frame(TMR_SR_OPCODE_VERSION, b"")

    # ------------------------------------------------------------------
    # Background read loop
    # ------------------------------------------------------------------
    def _read_loop(self) -> None:
        assert self._ser is not None
        while not self._stop.is_set():
            try:
                chunk = self._ser.read(256)
                if not chunk:
                    time.sleep(0.02)
                    continue

                now = time.time()
                self._last_rx_time = now
                self._last_activity_ts = now
                self._heartbeat_misses = 0  # any RX resets heartbeat miss count
                self._rx.extend(chunk)
                # Mirror raw RX into the debug session events.
                try:
                    if 'debug_session' in globals():
                        debug_session._add_event("rx", chunk.hex(" "))
                except Exception:
                    pass
                # Mirror RX into the main Serial Monitor as well — but only
                # when not scanning (during scans, parsed tag rows are the
                # right place to look; raw bytes would spam thousands of
                # lines/s). When idle, the user is debugging and wants to
                # see EXACTLY what came back.
                if not self.scanning:
                    self._log(f"rx: {chunk.hex(' ').upper()} ({len(chunk)}B)")
                self._drain_frames()

                # Single-scan timeout / completion check
                if self.scanning and self.read_mode == SCAN_MODE_SINGLE:
                    if len(self.tags) > self._scan_session_tag_count:
                        self._finish_single_scan("Single scan complete")
                    elif (
                        self._last_scan_start
                        and (time.time() - self._last_scan_start) > 3.0
                    ):
                        self._finish_single_scan("Single scan timed out (no tag found)")
                elif (
                    self.scanning
                    and self._last_scan_start
                    and (time.time() - self._last_scan_start) > 5.0
                    and len(self.tags) == 0
                ):
                    self._log(
                        "No tags detected after 5 s. Check: tag is UHF EPC Gen2, "
                        "distance < 1 m, reader switch in UART mode, correct region/power."
                    )
                    self._last_scan_start = None

            except Exception as exc:
                # Serial error — the USB was likely yanked. Flip state to LOST
                # and stop polling. The heartbeat thread will have already
                # given up, or will on its next tick.
                self._log(f"Serial read error: {exc} — marking connection lost")
                self.scanning = False
                self._set_conn_state(CONN_LOST, f"Serial error: {exc}")
                self._close_serial_quiet()
                self._stop.set()
                break

    def _heartbeat_loop(self) -> None:
        """Periodically verify the reader is alive.

        While scanning, the reader sends keepalives/tag frames, so this mainly
        fires during idle. Two misses → STALE; three → LOST.
        """
        HEARTBEAT_INTERVAL = 5.0
        HEARTBEAT_ACTIVITY_WINDOW = 4.0  # ignore check if we saw bytes recently
        STALE_THRESHOLD = 2
        LOST_THRESHOLD = 3

        while not self._stop.is_set():
            # Sleep in small slices so disconnect is responsive
            for _ in range(int(HEARTBEAT_INTERVAL * 10)):
                if self._stop.is_set():
                    return
                time.sleep(0.1)

            if self.conn_state not in (CONN_CONNECTED, CONN_STALE):
                continue

            # Recent activity counts as a heartbeat — skip the explicit ping
            if (time.time() - self._last_activity_ts) < HEARTBEAT_ACTIVITY_WINDOW:
                if self.conn_state == CONN_STALE:
                    self._set_conn_state(CONN_CONNECTED, self.version_text)
                    self._heartbeat_misses = 0
                continue

            # Don't interrupt a scan with a version request — the reader is
            # streaming tag frames and the _read_loop resets activity on any RX
            if self.scanning:
                continue

            # Send a quiet version ping. Response arrives via _read_loop and
            # resets _heartbeat_misses automatically.
            try:
                if self._ser:
                    self._ser.write(_build_frame(TMR_SR_OPCODE_VERSION, b""))
            except Exception as exc:
                self._log(f"Heartbeat send error: {exc} — marking connection lost")
                self._set_conn_state(CONN_LOST, f"Heartbeat send failed: {exc}")
                self._close_serial_quiet()
                self._stop.set()
                return

            # Wait a moment for response
            time.sleep(0.8)
            if (time.time() - self._last_activity_ts) < HEARTBEAT_ACTIVITY_WINDOW:
                if self.conn_state == CONN_STALE:
                    self._set_conn_state(CONN_CONNECTED, self.version_text)
                self._heartbeat_misses = 0
            else:
                self._heartbeat_misses += 1
                if self._heartbeat_misses >= LOST_THRESHOLD:
                    self._log(
                        f"Heartbeat failed {self._heartbeat_misses} times — connection lost"
                    )
                    self._set_conn_state(CONN_LOST, "Reader stopped responding")
                    self._close_serial_quiet()
                    self._stop.set()
                    return
                elif self._heartbeat_misses >= STALE_THRESHOLD:
                    self._set_conn_state(
                        CONN_STALE,
                        f"Reader not responding (miss {self._heartbeat_misses})",
                    )

    def _drain_frames(self) -> None:
        """Parse all complete frames currently in _rx buffer."""
        while True:
            result = _pop_next_response_frame(self._rx)
            if result is None:
                return
            frame, has_status = result
            self._handle_frame(frame, has_status)

    def _handle_frame(self, frame: bytes, has_status: bool) -> None:
        """Dispatch a parsed frame to the appropriate handler."""
        if len(frame) < 3 or frame[0] != 0xFF:
            return

        opcode = frame[2]
        length = frame[1]

        if opcode == TMR_SR_OPCODE_READ_TAG_ID_MULTIPLE:
            kind = _classify_0x22_frame(frame)
            if kind == RESPONSE_IS_KEEPALIVE:
                self._log("Keepalive: reader is scanning")
            elif kind == RESPONSE_IS_TEMPERATURE:
                # Temperature frame: bytes [5..8] are temp in 1/1000 °C
                if len(frame) >= 13:
                    temp_raw = (frame[9] << 24) | (frame[10] << 16) | (frame[11] << 8) | frame[12]
                    self._log(f"Reader temperature: {temp_raw / 1000:.1f} °C")
                else:
                    self._log("Reader temperature frame received")
            elif kind == RESPONSE_IS_TEMPTHROTTLE:
                self._log("WARNING: Reader temperature throttling — reduce power or improve ventilation")
            elif kind == RESPONSE_IS_HIGHRETURNLOSS:
                self._log("WARNING: High return loss on antenna — check cable and antenna connection")
            elif kind == RESPONSE_IS_TAGFOUND:
                if self.scanning:
                    self._process_tag_frame(frame)
                    if self.read_mode == SCAN_MODE_SINGLE:
                        self._finish_single_scan("Single scan complete")
            return

        if opcode == TMR_SR_OPCODE_VERSION:
            # Version response: status at [3:5] if has_status, payload follows
            payload = frame[5:-2] if has_status else frame[3:-2]
            text = payload.decode("ascii", errors="ignore").strip("\x00 ").strip()
            if text:
                self.version_text = text
                self._log(f"Version: {text}")
            else:
                self._log(f"Version frame received (len={length})")
            return

        # Generic frame logging
        if has_status and len(frame) >= 5:
            status = (frame[3] << 8) | frame[4]
            if status != 0x0000:
                self._log(f"FRAME op=0x{opcode:02X} status=0x{status:04X} len={length}")
            else:
                self._log(f"FRAME op=0x{opcode:02X} OK len={length}")
        else:
            self._log(f"FRAME op=0x{opcode:02X} len={length}")

    def _process_tag_frame(self, frame: bytes) -> None:
        """Extract EPC/RSSI/antenna from a tag-found frame and update the tags dict."""
        result = _parse_tag_frame(frame)
        if result is None:
            self._log(f"Tag frame parse failed (raw len={len(frame)}): {frame.hex().upper()}")
            return

        epc = result["epc"]
        rssi = float(result["rssi"])
        antenna = result["antenna"]
        now = self._now()

        with self._lock:
            cur = self.tags.get(epc)
            if cur is None:
                self.tags[epc] = TagRow(
                    epc=epc, rssi=rssi, antenna=antenna,
                    count=1, first_seen=now, last_seen=now
                )
                self._log(f"New tag: {epc}  RSSI={rssi} dBm  ant={antenna}")
            else:
                cur.count += 1
                cur.last_seen = now
                cur.rssi = rssi
                cur.antenna = antenna

    def _finish_single_scan(self, message: str) -> None:
        self._send_stop_read()
        self.scanning = False
        self._last_scan_start = None
        self._scan_session_tag_count = 0
        self._log(message)

    # ------------------------------------------------------------------
    # Command senders
    # ------------------------------------------------------------------
    def _write_frame(self, opcode: int, data: bytes) -> None:
        """Build and send one Mercury API request frame."""
        if not self._ser:
            raise RuntimeError("Serial port not open")
        frame = _build_frame(opcode, data)
        self._ser.write(frame)
        self._log(f"TX op=0x{opcode:02X} data_len={len(data)}")

    def _send_start_read(self) -> None:
        """Start continuous multi-tag reading (MULTI_PROTOCOL_TAG_OP with embedded READ_TAG_ID_MULTIPLE)."""
        if not self._ser:
            return
        # This is the SparkFun startReading() config blob:
        # sub-opcode 0x22 (READ_TAG_ID_MULTIPLE), timeout 0, flags, GEN2, ...
        config_blob = bytes([
            0x00, 0x00,                          # timeout high/low (0 = continuous)
            0x01,                                # option flags: 0x01 = enable embedded ops
            0x22,                                # sub-opcode: READ_TAG_ID_MULTIPLE
            0x00, 0x00,                          # search flags
            0x05, 0x07,                          # metadata flags (EPC + RSSI + antenna + ...)
            0x22, 0x10,                          # ??? (from SparkFun library constant)
            0x00, 0x1B,                          # ??? (from SparkFun library)
            0x03, 0xE8,                          # 0x03E8 = 1000 ms timeout per inventory round
            0x01,                                # antenna list count = 1
            0xFF,                                # antenna mask (all)
        ])
        try:
            self._write_frame(TMR_SR_OPCODE_MULTI_PROTOCOL_TAG_OP, config_blob)
        except Exception as exc:
            self._log(f"Start read command error: {exc}")

    def _send_stop_read(self) -> None:
        """Stop continuous reading (MULTI_PROTOCOL_TAG_OP with stop sub-command)."""
        if not self._ser:
            return
        try:
            self._send_stop_raw()
        except Exception as exc:
            self._log(f"Stop read command error: {exc}")

    def _send_stop_raw(self) -> None:
        """Send stop commands unconditionally — tries all known stop methods."""
        if not self._ser:
            return
        # Method 1: MULTI_PROTOCOL_TAG_OP with stop flag {0x00, 0x00, 0x02}
        self._ser.write(_build_frame(TMR_SR_OPCODE_MULTI_PROTOCOL_TAG_OP, bytes([0x00, 0x00, 0x02])))
        time.sleep(0.05)
        # Method 2: bare READ_TAG_ID_MULTIPLE with no payload (alternative stop)
        self._ser.write(_build_frame(TMR_SR_OPCODE_READ_TAG_ID_MULTIPLE, b""))
        time.sleep(0.05)
        # Method 3: ASCII 'q' (works on some firmware versions)
        self._ser.write(b"q\r\n")
        time.sleep(0.05)

    def _disable_read_filter(self) -> None:
        """Disable tag filter so all EPC Gen2 tags are reported."""
        if not self._ser:
            return
        try:
            # SET_READER_OPTIONAL_PARAMS: option 0x0C (tag filter), value 0x00 (off)
            self._write_frame(TMR_SR_OPCODE_SET_READER_OPTIONAL_PARAMS, bytes([0x01, 0x0C, 0x00]))
        except Exception as exc:
            self._log(f"Disable filter error: {exc}")

    def _set_tag_protocol_gen2(self) -> None:
        """Set tag protocol to EPC Gen2 (0x0005)."""
        if not self._ser:
            return
        try:
            # Two bytes big-endian: 0x00 0x05
            self._write_frame(TMR_SR_OPCODE_SET_TAG_PROTOCOL, bytes([0x00, 0x05]))
        except Exception as exc:
            self._log(f"Set tag protocol error: {exc}")

    def _set_antenna_port(self) -> None:
        """Set TX and RX antenna port to the configured antenna_port value."""
        if not self._ser:
            return
        try:
            antenna = max(1, min(16, int(self.antenna_port or 1)))
            self.antenna_port = antenna
            # SparkFun setAntennaPort() sends {0x01, 0x01} for port 1 (TX=1, RX=1)
            # For other ports: {tx_port, rx_port}
            port_byte = antenna & 0xFF
            self._write_frame(TMR_SR_OPCODE_SET_ANTENNA_PORT, bytes([port_byte, port_byte]))
            self._log(f"Antenna port set to {antenna}")
        except Exception as exc:
            self._log(f"Set antenna port error: {exc}")

    def _set_region(self, region: int) -> None:
        """Set the RF regulatory region."""
        if not self._ser:
            return
        try:
            self._write_frame(TMR_SR_OPCODE_SET_REGION, bytes([region & 0xFF]))
            self._log(f"Region set to 0x{region:02X}")
        except Exception as exc:
            self._log(f"Set region error: {exc}")

    def _set_read_power(self, power: int) -> None:
        """Set TX read power in centidBm (e.g. 2000 = 20.00 dBm, max 2700 = 27 dBm)."""
        if not self._ser:
            return
        try:
            power = max(0, min(2700, int(power)))
            self.read_power = power
            # Two bytes big-endian signed
            data = power.to_bytes(2, byteorder="big", signed=True)
            self._write_frame(TMR_SR_OPCODE_SET_READ_TX_POWER, data)
            self._log(f"Read power set to {power} ({power / 100:.2f} dBm)")
        except Exception as exc:
            self._log(f"Set read power error: {exc}")

    # ------------------------------------------------------------------
    # Blocking version request (used during connect() before the loop starts)
    # ------------------------------------------------------------------
    def _request_version_blocking(self, timeout_s: float = 1.0) -> dict[str, Any] | None:
        """Send a version request and wait synchronously for the response frame.

        Returns a dict with keys 'opcode', 'status', 'payload', or None on timeout.
        Called before the background reader thread is started.
        """
        if not self._ser:
            return None
        frame = _build_frame(TMR_SR_OPCODE_VERSION, b"")
        self._ser.write(frame)

        buf = bytearray()
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            chunk = self._ser.read(256)
            if chunk:
                self._last_rx_time = time.time()
                buf.extend(chunk)
                result = _pop_next_response_frame(buf)
                if result is not None:
                    resp_frame, has_status = result
                    opcode = resp_frame[2]
                    status: int | None = None
                    if has_status and len(resp_frame) >= 5:
                        status = (resp_frame[3] << 8) | resp_frame[4]
                    payload = resp_frame[5:-2] if has_status else resp_frame[3:-2]
                    return {"opcode": opcode, "status": status, "payload": payload}
            else:
                time.sleep(0.02)
        return None

    # ------------------------------------------------------------------
    # Serial helpers
    # ------------------------------------------------------------------
    def _open_serial(self, port: str, baudrate: int) -> None:
        if self._ser:
            try:
                self._ser.close()
            except Exception:
                pass
            self._ser = None
        self._ser = serial.serial_for_url(port, baudrate, timeout=0.2)
        self.baudrate = baudrate

    def _flush_serial(self, drain_s: float = 0.6) -> None:
        """Flush and drain serial buffers for drain_s seconds.

        Uses a timed approach so continuous-mode data that keeps arriving
        is discarded rather than looping forever on in_waiting.
        """
        if not self._ser:
            return
        self._ser.reset_input_buffer()
        self._ser.reset_output_buffer()
        deadline = time.time() + drain_s
        while time.time() < deadline:
            if self._ser.in_waiting:
                self._ser.read(self._ser.in_waiting)
            time.sleep(0.02)

    def _peek_raw_bytes(self, duration_s: float = 0.5) -> bytes:
        """Read whatever the reader sends in duration_s seconds without parsing."""
        if not self._ser:
            return b""
        buf = bytearray()
        deadline = time.time() + duration_s
        while time.time() < deadline:
            chunk = self._ser.read(256)
            if chunk:
                buf.extend(chunk)
            else:
                time.sleep(0.02)
        return bytes(buf)

    def _close_serial_quiet(self) -> None:
        if self._ser:
            try:
                self._ser.close()
            except Exception:
                pass
            self._ser = None

    # ------------------------------------------------------------------
    # Static helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _normalize_port(port: str) -> str:
        """Normalize a port identifier for Mac, Raspberry Pi OS, or Windows.

        Accepts:
        - Absolute Unix paths: /dev/cu.usbserial-*, /dev/ttyUSB*, etc.
        - Mac shorthand without /dev prefix: cu.usbserial-..., tty.*
        - Windows COM ports: COM3, COM10 (high-number ports get \\.\COMx prefix)
        - Network bridge URLs: socket://host:port, rfc2217://host:port
        """
        p = (port or "").strip()
        if not p:
            return p
        # Network bridge URLs — pass through as-is
        if p.startswith("socket://") or p.startswith("rfc2217://"):
            return p
        # Already absolute Unix path (Mac /dev/cu.* or Pi /dev/tty*)
        if p.startswith("/"):
            return p
        # Windows \\.\COMx — pass through as-is
        if p.startswith("\\\\.\\"):
            return p
        # Windows shorthand: COM3 → COM3 (low), COM10 → \\.\COM10 (high, requires prefix)
        import re as _re
        m = _re.match(r"^COM(\d+)$", p, _re.IGNORECASE)
        if m:
            num = int(m.group(1))
            return f"\\\\.\\COM{num}" if num >= 10 else p.upper()
        # Mac shorthand: cu.xxx or tty.xxx → /dev/cu.xxx
        if p.startswith("cu.") or p.startswith("tty."):
            return f"/dev/{p}"
        return p

    @staticmethod
    def _normalize_read_mode(read_mode: str) -> str:
        mode = (read_mode or "").strip().lower()
        return SCAN_MODE_SINGLE if mode == SCAN_MODE_SINGLE else SCAN_MODE_CONTINUOUS


# ---------------------------------------------------------------------------
# Port probe helper (used by /api/probe — runs outside the main state object)
# ---------------------------------------------------------------------------
def _try_version_probe(port: str, baudrate: int, timeout_s: float = 1.2) -> dict[str, Any]:
    """Open port, passively listen briefly, then send version command.

    Returns a dict with:
      ok: bool                  — got a valid version frame
      version: str | None       — parsed version string when ok
      preamble_bytes: int       — bytes received BEFORE we sent anything (>0 means the
                                   reader is streaming at this baud; probably mid
                                   continuous-read and needs recovery)
      bytes_received: int       — total bytes received during the probe
      hex_sample: str           — up to 32 bytes of what we saw, for diagnostics
      note: str | None          — human-readable detail (wrong opcode, error, etc.)
      mid_stream: bool          — True if preamble_bytes > 0 (baud likely right but
                                   reader needs a stop-command recovery pass)
    """
    try:
        ser = serial.serial_for_url(port, baudrate, timeout=0.1)
    except Exception as exc:
        return {
            "ok": False, "version": None, "preamble_bytes": 0,
            "bytes_received": 0, "hex_sample": "", "note": f"open failed: {exc}",
            "mid_stream": False, "error": str(exc),
        }

    try:
        # 1. Passive pre-read: if the reader is mid continuous-read at this baud,
        #    bytes will start arriving the moment we open the port, even before
        #    we TX anything.
        preamble = bytearray()
        pre_deadline = time.time() + 0.25
        while time.time() < pre_deadline:
            chunk = ser.read(256)
            if chunk:
                preamble.extend(chunk)
            else:
                time.sleep(0.01)

        preamble_bytes = len(preamble)

        # 2. Drain, then send version
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        frame = _build_frame(TMR_SR_OPCODE_VERSION, b"")
        ser.write(frame)

        # 3. Read for timeout_s, capturing everything
        buf = bytearray()
        # seed buf with preamble so parser can see it too (useful when a partial
        # frame straddled the reset_input_buffer call)
        note: str | None = None
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            chunk = ser.read(256)
            if chunk:
                buf.extend(chunk)
                result = _pop_next_response_frame(buf)
                if result is not None:
                    resp_frame, has_status = result
                    opcode = resp_frame[2]
                    if opcode == TMR_SR_OPCODE_VERSION:
                        payload = resp_frame[5:-2] if has_status else resp_frame[3:-2]
                        text = payload.decode("ascii", errors="ignore").strip("\x00 ").strip()
                        sample = (preamble + buf)[:32]
                        return {
                            "ok": True,
                            "version": text if text else "Reader responded",
                            "preamble_bytes": preamble_bytes,
                            "bytes_received": preamble_bytes + len(buf),
                            "hex_sample": sample.hex(" "),
                            "mid_stream": preamble_bytes > 0,
                            "note": None,
                        }
                    note = f"unexpected opcode 0x{opcode:02X}"
                    break
            else:
                time.sleep(0.02)

        total_bytes = preamble_bytes + len(buf)
        combined = (preamble + buf)[:32]
        if note is None:
            if total_bytes == 0:
                note = "silent — no bytes at this baud"
            elif preamble_bytes > 0:
                note = f"{preamble_bytes} pre-bytes (likely mid continuous-read)"
            else:
                note = f"{total_bytes} bytes but no valid frame"

        return {
            "ok": False,
            "version": None,
            "preamble_bytes": preamble_bytes,
            "bytes_received": total_bytes,
            "hex_sample": combined.hex(" "),
            "mid_stream": preamble_bytes > 0,
            "note": note,
        }
    finally:
        try:
            ser.close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Raw serial debug session — opens a port without the Mercury handshake so the
# user can poke at the module from the web UI ("Debug Terminal" panel).
# Mutually exclusive with the main reader connection — one process, one port.
# ---------------------------------------------------------------------------
class DebugSession:
    MAX_EVENTS = 500

    def __init__(self) -> None:
        self.ser: serial.Serial | None = None
        self.port: str | None = None
        self.baudrate: int | None = None
        self._lock = threading.Lock()
        self._events: list[dict[str, Any]] = []
        self._seq = 0
        self._reader_thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._frame_buf = bytearray()
        self.parse_frames = True

    @property
    def is_open(self) -> bool:
        return self.ser is not None

    def open(self, port: str, baudrate: int) -> None:
        if self.is_open:
            raise RuntimeError("Debug session already open — close first")
        normalized = _normalize_port(port)
        self.ser = serial.serial_for_url(normalized, baudrate, timeout=0.1)
        self.port = normalized
        self.baudrate = baudrate
        self._frame_buf.clear()
        self._stop = threading.Event()
        self._add_event(
            "open",
            f"{normalized} @ {baudrate}  dtr={self.ser.dtr} rts={self.ser.rts}",
        )
        self._reader_thread = threading.Thread(target=self._read_loop, daemon=True)
        self._reader_thread.start()

    def close(self) -> None:
        self._stop.set()
        if self._reader_thread is not None:
            self._reader_thread.join(timeout=1.0)
        if self.ser is not None:
            try:
                self.ser.close()
            except Exception:
                pass
        prev = self.port
        self.ser = None
        self.port = None
        self.baudrate = None
        self._reader_thread = None
        self._add_event("close", prev or "")

    def send(self, data: bytes, label: str = "tx") -> None:
        if not self.is_open or self.ser is None:
            raise RuntimeError("Debug session is not open")
        self.ser.write(data)
        self._add_event(label, data.hex(" "))

    def set_dtr(self, on: bool) -> None:
        if not self.is_open or self.ser is None:
            raise RuntimeError("Debug session is not open")
        self.ser.dtr = on
        self._add_event("dtr", "on" if on else "off")

    def set_rts(self, on: bool) -> None:
        if not self.is_open or self.ser is None:
            raise RuntimeError("Debug session is not open")
        self.ser.rts = on
        self._add_event("rts", "on" if on else "off")

    def reopen(self, baudrate: int) -> None:
        port = self.port
        if not port:
            raise RuntimeError("Not open — call open() first")
        self.close()
        time.sleep(0.1)
        self.open(port, baudrate)

    def clear(self) -> None:
        with self._lock:
            self._events.clear()

    def snapshot(self, since_seq: int = 0) -> dict[str, Any]:
        with self._lock:
            events = [e for e in self._events if e["seq"] > since_seq]
            last_seq = self._events[-1]["seq"] if self._events else 0
            # Shared mode: when the main reader is connected, the terminal
            # writes through that port. The user can always type.
            shared = bool(state.connected and state._ser is not None)
            return {
                "open": self.is_open or shared,
                "shared": shared,
                "port": (state.port if shared else self.port),
                "baudrate": (state.baudrate if shared else self.baudrate),
                "parse_frames": self.parse_frames,
                "last_seq": last_seq,
                "events": events,
            }

    def _add_event(self, kind: str, text: str) -> None:
        with self._lock:
            self._seq += 1
            self._events.append({
                "seq": self._seq,
                "ts": time.time(),
                "kind": kind,
                "text": text,
            })
            if len(self._events) > self.MAX_EVENTS:
                self._events = self._events[-self.MAX_EVENTS :]

    def _read_loop(self) -> None:
        assert self.ser is not None
        while not self._stop.is_set():
            try:
                chunk = self.ser.read(256)
            except serial.SerialException as exc:
                self._add_event("err", f"serial: {exc}")
                return
            except Exception as exc:  # pragma: no cover
                self._add_event("err", str(exc))
                return
            if not chunk:
                continue
            self._add_event("rx", chunk.hex(" "))
            if self.parse_frames:
                self._frame_buf.extend(chunk)
                while True:
                    r = _pop_next_response_frame(self._frame_buf)
                    if r is None:
                        break
                    frame, has_status = r
                    opcode = frame[2]
                    if has_status:
                        status = int.from_bytes(frame[3:5], "big")
                        payload = frame[5:-2]
                        self._add_event(
                            "frame",
                            f"op=0x{opcode:02X} status=0x{status:04X} payload={payload.hex(' ')}",
                        )
                    else:
                        payload = frame[3:-2]
                        self._add_event(
                            "frame",
                            f"op=0x{opcode:02X} payload={payload.hex(' ')}",
                        )


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------
state = ReaderState()
debug_session = DebugSession()
app = FastAPI(title="Standalone RFID Reader Monitor")
_BASE = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(_BASE, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(_BASE, "templates"))


# ---------------------------------------------------------------------------
# Pydantic request models
# ---------------------------------------------------------------------------
class ConnectPayload(BaseModel):
    port: str
    baudrate: int = 115200
    safe_mode: bool = True
    read_mode: str = SCAN_MODE_CONTINUOUS
    antenna_port: int = 1
    region: int = REGION_PHILIPPINES
    read_power: int = 2700
    skip_handshake: bool = False  # raw mode: open port, no version probe, no config


class StartPayload(BaseModel):
    read_mode: str = SCAN_MODE_CONTINUOUS


class CommandPayload(BaseModel):
    command: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/bridge")
def download_bridge() -> FileResponse:
    """Download the Windows serial-over-TCP bridge script."""
    bridge_path = Path(__file__).parent / "windows_bridge.py"
    return FileResponse(bridge_path, filename="windows_bridge.py", media_type="text/plain")


@app.get("/api/state")
def get_state() -> dict[str, Any]:
    return state.snapshot()


def _classify_port(device: str, description: str, hwid: str) -> tuple[str, int]:
    """Classify a serial port and assign a rank (higher = more likely the reader).

    Returns (category, rank) where category is one of PORT_LIKELY_READER,
    PORT_MAYBE_SERIAL, PORT_NOT_READER.

    Works on Mac (/dev/cu.*), Raspberry Pi (/dev/ttyUSB*), and Windows (COMx).
    """
    # Explicit exclusions first — Bluetooth, iPhone dial-up, debug console
    for pat in _EXCLUDE_PATTERNS:
        if pat.search(device) or pat.search(description or "") or pat.search(hwid or ""):
            return PORT_NOT_READER, 0

    # WCH CH340/CH341 USB vendor ID in hwid gets an extra boost
    hwid_upper = (hwid or "").upper()
    vid_boost = 15 if "1A86" in hwid_upper else 0

    # Windows COM port: promote to likely_reader if description matches known adapters
    import re as _re
    if _re.match(r"^(COM\d+|\\\\\.\\.+COM\d+)$", device, _re.IGNORECASE):
        desc_boost = 10 if _WINDOWS_READER_DESC.search(description or "") else 0
        if vid_boost or desc_boost:
            return PORT_LIKELY_READER, 90 + vid_boost + desc_boost
        # Generic COM port with USB hwid — maybe serial
        if "USB" in hwid_upper or "VID:PID" in hwid_upper:
            return PORT_MAYBE_SERIAL, 50
        return PORT_MAYBE_SERIAL, 20

    # Pattern match against known reader-adapter paths (Mac + Pi)
    for rank, pat in _READER_PATTERNS:
        if pat.match(device):
            return PORT_LIKELY_READER, rank + vid_boost

    # Generic USB serial (has a USB hwid but didn't match known patterns)
    if "USB" in hwid_upper or "VID:PID" in hwid_upper:
        return PORT_MAYBE_SERIAL, 50 + vid_boost

    # Anything else is unlikely
    return PORT_MAYBE_SERIAL, 10


_LOCATION_RE = re.compile(r"LOCATION=([^\s]+)", re.IGNORECASE)


def _extract_location(hwid: str) -> str | None:
    """Pull the USB LOCATION token out of a pyserial hwid string, if present.

    Two /dev/cu.* aliases created by the WCH DriverKit driver (e.g.
    /dev/cu.usbserial-11320 and /dev/cu.wchusbserial11320) share the same
    LOCATION and VID:PID — they are the same physical adapter.
    """
    if not hwid:
        return None
    m = _LOCATION_RE.search(hwid)
    return m.group(1) if m else None


def _list_classified_ports() -> list[dict[str, Any]]:
    """List all serial ports with category + rank, sorted highest rank first."""
    ports: list[dict[str, Any]] = []
    for p in serial.tools.list_ports.comports():
        category, rank = _classify_port(p.device, p.description or "", p.hwid or "")
        ports.append({
            "device": p.device,
            "description": p.description,
            "hwid": p.hwid,
            "location": _extract_location(p.hwid or ""),
            "category": category,
            "rank": rank,
        })
    ports.sort(key=lambda x: (-x["rank"], x["device"]))
    return ports


def _dedupe_by_location(ports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Collapse driver aliases (same USB LOCATION) to one representative port.

    When two ports share a LOCATION, prefer the higher-ranked one (wchusbserial
    tends to outrank usbserial because of the /dev/cu.wchusbserial pattern).
    Ports without a LOCATION (Bluetooth, debug-console) pass through unchanged.
    """
    seen: dict[str, dict[str, Any]] = {}
    out: list[dict[str, Any]] = []
    for p in ports:
        loc = p.get("location")
        if not loc:
            out.append(p)
            continue
        existing = seen.get(loc)
        if existing is None or p["rank"] > existing["rank"]:
            seen[loc] = p
    # append deduped USB devices in rank order
    out.extend(sorted(seen.values(), key=lambda x: (-x["rank"], x["device"])))
    return out


@app.get("/api/ports")
def get_ports() -> dict[str, Any]:
    """List classified serial ports and split out likely-reader candidates."""
    ports = _list_classified_ports()
    candidates = [p for p in ports if p["category"] == PORT_LIKELY_READER]
    return {"ports": ports, "reader_candidates": candidates}


@app.get("/api/diagnostics")
def get_diagnostics() -> dict[str, Any]:
    """Return Mac/Pi environment info so the UI can show troubleshooting hints."""
    import platform
    import subprocess

    ports = _list_classified_ports()
    candidates = [p for p in ports if p["category"] == PORT_LIKELY_READER]

    system = platform.system()  # "Darwin" on Mac, "Linux" on Pi
    mac_version = None
    driver_present = None
    has_usb_device = None
    dialout_ok = None

    if system == "Darwin":
        try:
            mac_version = platform.mac_ver()[0]
        except Exception:
            mac_version = None
        # Check WCH CH340 DriverKit extension is activated
        try:
            out = subprocess.run(
                ["systemextensionsctl", "list"],
                capture_output=True, text=True, timeout=2.0,
            )
            driver_present = (
                "cn.wch.CH34xVCPDriver" in (out.stdout or "")
                and "activated" in (out.stdout or "")
            )
        except Exception:
            driver_present = None
        # Check if any USB devices are enumerated at all
        try:
            out = subprocess.run(
                ["ioreg", "-p", "IOUSB", "-c", "IOUSBHostDevice"],
                capture_output=True, text=True, timeout=2.0,
            )
            # Any line with "IOUSBHostDevice" (non-root) means a device is attached
            has_usb_device = out.stdout.count("IOUSBHostDevice") > 1
        except Exception:
            has_usb_device = None
    elif system == "Linux":
        # Raspberry Pi: check if the user is in the `dialout` group
        try:
            out = subprocess.run(
                ["id", "-nG"], capture_output=True, text=True, timeout=2.0
            )
            groups = (out.stdout or "").split()
            dialout_ok = "dialout" in groups
        except Exception:
            dialout_ok = None
        has_usb_device = len([p for p in ports if "/dev/tty" in p["device"]]) > 0
    elif system == "Windows":
        # Check if any COM ports exist at all
        has_usb_device = len([p for p in ports if "COM" in p["device"].upper()]) > 0
        # Check WCH CH340 driver presence via registry (silently skip if unavailable)
        try:
            import winreg  # type: ignore[import]
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Services\CH341SER",
            )
            winreg.CloseKey(key)
            driver_present = True
        except Exception:
            driver_present = False

    # Health summary: if there's a likely-reader candidate, consider it healthy.
    healthy = len(candidates) > 0
    issues: list[str] = []
    if system == "Darwin":
        if driver_present is False:
            issues.append(
                "CH340 driver not activated. Open System Settings → Privacy & Security → "
                "scroll to the blocked kext entry and click Allow, or reinstall the WCH driver."
            )
        if has_usb_device is False:
            issues.append(
                "No USB devices detected on this Mac. Plug the reader in, try a different "
                "USB-C port, and confirm the cable is data-capable (not charge-only)."
            )
        if not candidates and has_usb_device:
            issues.append(
                "USB devices are present but none match a known USB-serial reader pattern. "
                "If the reader uses a non-CH340 chip, look under Advanced to select manually."
            )
    elif system == "Linux":
        if dialout_ok is False:
            issues.append(
                "Current user is not in the `dialout` group. Run: "
                "sudo usermod -aG dialout $USER && log out / back in."
            )
        if not candidates:
            issues.append(
                "No /dev/ttyUSB* or /dev/ttyACM* device found. "
                "Plug in the reader and check `dmesg | tail` for USB enumeration errors."
            )
    elif system == "Windows":
        if driver_present is False:
            issues.append(
                "CH340 driver not detected. Download and install from "
                "https://www.wch-ic.com/downloads/CH341SER_EXE.html then unplug/replug the reader."
            )
        if not has_usb_device:
            issues.append(
                "No COM ports found. Plug the reader in, confirm the CH340 driver is installed, "
                "and check Device Manager → Ports (COM & LPT) for the entry."
            )
        if not candidates and has_usb_device:
            issues.append(
                "COM ports present but none matched a known USB-serial reader description. "
                "Open Advanced and select the port manually (check Device Manager for the COM number)."
            )

    if not candidates and not issues:
        issues.append(
            "No reader candidate found. Plug the reader in and click Connect to Reader."
        )

    return {
        "system": system,
        "arch": platform.machine(),
        "mac_version": mac_version,
        "driver_present": driver_present,
        "has_usb_device": has_usb_device,
        "dialout_ok": dialout_ok,
        "reader_candidates": candidates,
        "healthy": healthy,
        "issues": issues,
    }


@app.post("/api/probe")
def probe_ports() -> dict[str, Any]:
    """Probe all serial ports across all baud rates. Returns matched readers and a raw scan."""
    baud_candidates = [115200, 9600, 38400, 57600, 19200, 230400]
    all_ports = serial.tools.list_ports.comports()
    found: list[dict[str, Any]] = []
    raw_scan: list[dict[str, Any]] = []

    for p in all_ports:
        port = p.device
        port_info: dict[str, Any] = {
            "port": port,
            "description": p.description,
            "baudrates_tried": [],
            "got_bytes": False,
            "raw_hex": None,
        }
        matched = False
        for baud in baud_candidates:
            try:
                result = _try_version_probe(port, baud)
                port_info["baudrates_tried"].append(baud)
                if result["ok"]:
                    found.append({"port": port, "baudrate": baud, "version": result["version"]})
                    port_info["got_bytes"] = True
                    matched = True
                    break
            except Exception:
                continue

        if not matched:
            # Raw probe: just open at 115200 and see if any bytes arrive
            try:
                ser = serial.serial_for_url(port, 115200, timeout=0.1)
                raw = bytearray()
                deadline = time.time() + 0.5
                # Send stop + version to provoke a response
                ser.write(_build_frame(TMR_SR_OPCODE_MULTI_PROTOCOL_TAG_OP, bytes([0x00, 0x00, 0x02])))
                ser.write(_build_frame(TMR_SR_OPCODE_VERSION, b""))
                while time.time() < deadline:
                    chunk = ser.read(64)
                    if chunk:
                        raw.extend(chunk)
                    else:
                        time.sleep(0.02)
                ser.close()
                if raw:
                    port_info["got_bytes"] = True
                    port_info["raw_hex"] = raw[:64].hex().upper()
            except Exception:
                pass
        raw_scan.append(port_info)

    return {"matches": found, "raw_scan": raw_scan}


@app.post("/api/connect")
def connect(payload: ConnectPayload) -> dict[str, Any]:
    try:
        state.region = payload.region
        state.read_power = payload.read_power
        state.antenna_port = payload.antenna_port
        state.connect(
            payload.port,
            payload.baudrate,
            payload.safe_mode,
            payload.read_mode,
            skip_handshake=payload.skip_handshake,
        )
        return {"ok": True, "state": state.snapshot()}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


class ConnectAutoPayload(BaseModel):
    """Optional settings for the one-button auto-connect flow."""
    safe_mode: bool = True
    read_mode: str = SCAN_MODE_CONTINUOUS
    antenna_port: int = 1
    region: int = REGION_PHILIPPINES
    read_power: int = 2700


@app.post("/api/connect_auto")
def connect_auto(payload: ConnectAutoPayload) -> dict[str, Any]:
    """One-button flow: scan likely reader ports, probe each across the
    ThingMagic baud table, connect on the first match.

    Probe result semantics:
      - ok=True                     → valid version frame; full connect at this baud
      - mid_stream=True             → reader is streaming at this baud but no
                                       version frame yet; full connect does the
                                       stop-spam + DTR recovery
      - bytes_received>0, no frame  → wrong baud or bad framing; keep trying
      - bytes_received==0 every try → silent (wiring / power / mode switch)
    """
    if state.connected:
        raise HTTPException(status_code=400, detail="Already connected — disconnect first")

    ports = _list_classified_ports()
    likely = [p for p in ports if p["category"] == PORT_LIKELY_READER]
    candidates = _dedupe_by_location(likely)

    if not candidates:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "No likely-reader USB-serial device found. Plug in the reader and try again.",
                "ports": ports,
            },
        )

    # ThingMagic M6E/M7E supported bauds; 115200 is the factory default and
    # by far the most common. Full sweep catches reprogrammed modules.
    baud_candidates = [115200, 9600, 19200, 38400, 57600, 230400, 460800]
    attempts: list[dict[str, Any]] = []
    # Track the "best" fallback: a port+baud where we saw bytes but no frame
    fallback: dict[str, Any] | None = None

    def _attempted(port_dev: str, baud: int, r: dict[str, Any]) -> dict[str, Any]:
        return {
            "port": port_dev,
            "baudrate": baud,
            "ok": r.get("ok", False),
            "bytes_received": r.get("bytes_received", 0),
            "preamble_bytes": r.get("preamble_bytes", 0),
            "mid_stream": r.get("mid_stream", False),
            "hex_sample": r.get("hex_sample", ""),
            "note": r.get("note"),
        }

    def _do_full_connect(port_dev: str, baud: int, reason: str) -> dict[str, Any]:
        state.region = payload.region
        state.read_power = payload.read_power
        state.antenna_port = payload.antenna_port
        try:
            state.connect(port_dev, baud, payload.safe_mode, payload.read_mode)
        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": f"Matched {port_dev} @ {baud} ({reason}) but connect failed: {exc}",
                    "attempts": attempts,
                },
            ) from exc
        # Log the diagnostic attempts into the state log for on-page visibility
        for a in attempts:
            if a["bytes_received"] or a["note"]:
                state._log(
                    f"probe {a['port']} @ {a['baudrate']}: "
                    f"{a['bytes_received']}B ({a['note'] or 'ok'})"
                )
        return {
            "ok": True,
            "state": state.snapshot(),
            "attempts": attempts,
            "selected": {"port": port_dev, "baudrate": baud, "reason": reason},
        }

    for cand in candidates:
        port_dev = cand["device"]
        for baud in baud_candidates:
            result = _try_version_probe(port_dev, baud, timeout_s=1.2)
            attempts.append(_attempted(port_dev, baud, result))

            if result.get("ok"):
                return _do_full_connect(port_dev, baud, "version frame")

            # Reader streaming at this baud → baud is right, just needs recovery.
            # Do a full connect now; it will run stop-spam + DTR + 3 retries.
            if result.get("mid_stream"):
                return _do_full_connect(port_dev, baud, "mid-stream recovery")

            # Remember the best "saw bytes but no frame" attempt as a last-resort
            # fallback; prefer 115200 if we have it.
            if result.get("bytes_received", 0) > 0:
                if fallback is None or baud == 115200:
                    fallback = {"port": port_dev, "baudrate": baud}

    # No clean match. If we saw ANY bytes, try one full connect at the best
    # fallback; state.connect() has the recovery logic.
    if fallback is not None:
        return _do_full_connect(
            fallback["port"], fallback["baudrate"],
            "bytes-seen fallback",
        )

    # All attempts silent → wiring, power, or module boot issue.
    raise HTTPException(
        status_code=404,
        detail={
            "message": (
                "The CH340 USB-serial adapter enumerated, but no bytes came "
                "back from the module on any baud. Checklist:\n"
                " • Power: the module needs a clean 5V supply. Try a different "
                "USB port (not a bus-powered hub) or use an external 5V input.\n"
                " • Wiring (bare M7E-Nano): TX→RX crossover, GND common.\n"
                " • Mode switch on breakouts: ensure USB-mode (not UART-only).\n"
                " • Cable: confirm it's data-capable, not charge-only.\n"
                " • Was the reader last used by JADAK URA? Close URA completely — "
                "it can hold the port open and leave the module mid-scan."
            ),
            "attempts": attempts,
            "ports": ports,
        },
    )


@app.post("/api/disconnect")
def disconnect() -> dict[str, Any]:
    try:
        if state.connected:
            state.disconnect()
        return {"ok": True, "state": state.snapshot()}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/start")
def start_scan(payload: StartPayload) -> dict[str, Any]:
    try:
        state.read_mode = state._normalize_read_mode(payload.read_mode)
        state.start_scan()
        return {"ok": True, "state": state.snapshot()}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/stop")
def stop_scan() -> dict[str, Any]:
    try:
        state.stop_scan()
        return {"ok": True, "state": state.snapshot()}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/clear")
def clear_data() -> dict[str, Any]:
    state.clear()
    return {"ok": True, "state": state.snapshot()}


@app.post("/api/send")
def send_command(payload: CommandPayload) -> dict[str, Any]:
    try:
        state.send_ascii_command(payload.command)
        return {"ok": True}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/version")
def request_version() -> dict[str, Any]:
    try:
        state.request_version()
        return {"ok": True}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Debug terminal — raw serial without the Mercury handshake
# ---------------------------------------------------------------------------
class DebugOpenPayload(BaseModel):
    port: str
    baudrate: int = 115200


class DebugSendPayload(BaseModel):
    hex: str = ""           # raw hex bytes ("FF 00 03" etc.)
    shortcut: str = ""      # "version" | "stop" — convenience helpers


class DebugControlPayload(BaseModel):
    dtr: bool | None = None
    rts: bool | None = None
    baudrate: int | None = None
    parse_frames: bool | None = None


def _parse_hex_payload(s: str) -> bytes:
    cleaned = s.replace(",", " ").replace("0x", " ").replace("0X", " ")
    cleaned = "".join(cleaned.split())
    if not cleaned:
        raise ValueError("empty hex string")
    if len(cleaned) % 2 != 0:
        raise ValueError("hex string must have an even number of digits")
    try:
        return bytes.fromhex(cleaned)
    except ValueError as exc:
        raise ValueError(f"not valid hex: {exc}") from exc


@app.get("/api/debug/state")
def debug_state(since: int = 0) -> dict[str, Any]:
    """Snapshot of the debug session, with events newer than `since`."""
    return debug_session.snapshot(since_seq=since)


@app.post("/api/debug/open")
def debug_open(payload: DebugOpenPayload) -> dict[str, Any]:
    if state.connected:
        raise HTTPException(
            status_code=409,
            detail="Main reader is connected — disconnect from the reader first; only one process can hold the port.",
        )
    if debug_session.is_open:
        raise HTTPException(status_code=409, detail="Debug session already open — close it first.")
    try:
        debug_session.open(payload.port, payload.baudrate)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"open failed: {exc}") from exc
    return {"ok": True, "state": debug_session.snapshot()}


@app.post("/api/debug/close")
def debug_close() -> dict[str, Any]:
    debug_session.close()
    return {"ok": True, "state": debug_session.snapshot()}


def _shared_send(data: bytes, label: str) -> None:
    """Send bytes via whichever port is currently active.

    Priority:
      1. Main reader connection — write through state._ser, log to BOTH the
         debug_session events AND state.logs so the unified Serial Monitor
         shows the TX line.
      2. Standalone debug session.
    """
    if state.connected and state._ser is not None:
        state._ser.write(data)
        debug_session._add_event(label, data.hex(" "))
        # Mirror into the main log pane so the user sees what they sent
        state._log(f"{label}: {data.hex(' ').upper()} ({len(data)}B)")
        return
    if debug_session.is_open:
        debug_session.send(data, label=label)
        return
    raise RuntimeError(
        "Nothing is open — connect the main reader (Connect Raw) "
        "or open a debug session first."
    )


@app.post("/api/debug/send")
def debug_send(payload: DebugSendPayload) -> dict[str, Any]:
    try:
        if payload.shortcut == "version":
            _shared_send(_build_frame(TMR_SR_OPCODE_VERSION, b""), label="tx VERSION")
        elif payload.shortcut == "stop":
            _shared_send(_build_frame(0x2F, bytes([0x00, 0x00, 0x02])), label="tx STOP_2F")
            time.sleep(0.05)
            _shared_send(_build_frame(0x22, b""), label="tx STOP_22")
        elif payload.hex:
            data = _parse_hex_payload(payload.hex)
            _shared_send(data, label="tx")
        else:
            raise ValueError("provide either 'hex' or 'shortcut'")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"ok": True, "state": debug_session.snapshot()}


@app.post("/api/debug/control")
def debug_control(payload: DebugControlPayload) -> dict[str, Any]:
    """DTR/RTS/baud/parse controls.

    Operates on the main reader's port when state.connected, otherwise on
    the standalone debug session. Refuses if neither is open.
    """
    using_main = state.connected and state._ser is not None
    if not using_main and not debug_session.is_open:
        raise HTTPException(status_code=400, detail="Nothing is open")
    try:
        if payload.dtr is not None:
            if using_main:
                state._ser.dtr = payload.dtr  # type: ignore[union-attr]
                debug_session._add_event("dtr", "on" if payload.dtr else "off")
            else:
                debug_session.set_dtr(payload.dtr)
        if payload.rts is not None:
            if using_main:
                state._ser.rts = payload.rts  # type: ignore[union-attr]
                debug_session._add_event("rts", "on" if payload.rts else "off")
            else:
                debug_session.set_rts(payload.rts)
        if payload.parse_frames is not None:
            debug_session.parse_frames = payload.parse_frames
            debug_session._add_event("parse", "on" if payload.parse_frames else "off")
        if payload.baudrate is not None:
            if using_main:
                raise RuntimeError(
                    "Can't change baud while main reader is connected — disconnect first"
                )
            debug_session.reopen(payload.baudrate)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "state": debug_session.snapshot()}


@app.post("/api/debug/clear")
def debug_clear() -> dict[str, Any]:
    debug_session.clear()
    return {"ok": True, "state": debug_session.snapshot()}
