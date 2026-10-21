#!/usr/bin/env python3
"""Raw serial debug terminal for the M7E-Nano (or any UART device).

Opens the serial port WITHOUT the Mercury handshake, version probe, or any
configuration. Prints every byte received as hex+ASCII, and lets you type
arbitrary hex from the terminal to send.

Usage:
    python3 -m reader_standalone.debug_terminal                    # auto-pick port @ 115200
    python3 -m reader_standalone.debug_terminal /dev/cu.usbserial-10
    python3 -m reader_standalone.debug_terminal /dev/cu.usbserial-10 9600
    python3 -m reader_standalone.debug_terminal --list             # list ports and exit

Commands at the > prompt:
    <hex bytes>     send raw bytes (e.g. "FF 00 03 1D 0C" or "ff0003 1d0c")
    version         send Mercury VERSION command (helper, builds the frame)
    stop            send Mercury continuous-read stop sequence
    dtr on|off      toggle DTR line (CH340 reset trick)
    rts on|off      toggle RTS line
    baud <rate>     reopen the port at a new baud rate
    parse on|off    toggle on-the-fly Mercury frame parsing of incoming bytes
    help            print this help
    quit            exit  (Ctrl+C also works)

If the FastAPI app already holds the port, disconnect from the web UI first
(or stop the uvicorn server) — only one process can open a serial port at
a time.
"""

from __future__ import annotations

import argparse
import sys
import threading
import time
from typing import Optional

import serial
import serial.tools.list_ports

# Allow running both as `python3 -m reader_standalone.debug_terminal` and
# as `python3 reader_standalone/debug_terminal.py` from the repo root.
try:
    from .main import (
        _build_frame,
        _classify_port,
        _pop_next_response_frame,
        PORT_LIKELY_READER,
        TMR_SR_OPCODE_VERSION,
    )
except ImportError:  # pragma: no cover
    from reader_standalone.main import (  # type: ignore
        _build_frame,
        _classify_port,
        _pop_next_response_frame,
        PORT_LIKELY_READER,
        TMR_SR_OPCODE_VERSION,
    )


def _auto_pick_port() -> Optional[str]:
    """Return the highest-ranked likely_reader port, or None."""
    best: tuple[int, str] | None = None
    for p in serial.tools.list_ports.comports():
        cat, rank = _classify_port(p.device, p.description or "", p.hwid or "")
        if cat != PORT_LIKELY_READER:
            continue
        if best is None or rank > best[0]:
            best = (rank, p.device)
    return best[1] if best else None


def _hex_pretty(data: bytes) -> str:
    """Format bytes as `XX XX XX    ascii`."""
    hex_part = " ".join(f"{b:02X}" for b in data)
    ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in data)
    return f"{hex_part}    |{ascii_part}|"


def _parse_hex_line(s: str) -> bytes | None:
    """Parse a freeform hex string into bytes. Tolerates spaces, commas, 0x prefixes."""
    cleaned = s.replace(",", " ").replace("0x", " ").replace("0X", " ")
    cleaned = "".join(cleaned.split())
    if not cleaned or len(cleaned) % 2 != 0:
        return None
    try:
        return bytes.fromhex(cleaned)
    except ValueError:
        return None


class RawSerialDebug:
    def __init__(self, port: str, baudrate: int):
        self.port = port
        self.baudrate = baudrate
        self.ser: serial.Serial | None = None
        self._stop = threading.Event()
        self._reader_thread: threading.Thread | None = None
        self.parse_frames = True
        self._buf = bytearray()
        self._lock = threading.Lock()

    def open(self) -> None:
        self.ser = serial.serial_for_url(self.port, self.baudrate, timeout=0.1)
        self._println(f"[open] {self.port} @ {self.baudrate}  dtr={self.ser.dtr} rts={self.ser.rts}")

    def close(self) -> None:
        self._stop.set()
        if self._reader_thread:
            self._reader_thread.join(timeout=1.0)
        if self.ser:
            try:
                self.ser.close()
            except Exception:
                pass
        self._println("[close]")

    def start_reader(self) -> None:
        self._stop = threading.Event()
        self._reader_thread = threading.Thread(target=self._read_loop, daemon=True)
        self._reader_thread.start()

    def _println(self, line: str) -> None:
        """Write a line, with a newline first to avoid clobbering the prompt."""
        with self._lock:
            sys.stdout.write("\r" + line + "\n> ")
            sys.stdout.flush()

    def _read_loop(self) -> None:
        assert self.ser is not None
        while not self._stop.is_set():
            try:
                data = self.ser.read(256)
            except serial.SerialException as e:
                self._println(f"[err] serial: {e}")
                return
            except Exception as e:
                self._println(f"[err] {e}")
                return
            if not data:
                continue
            self._println(f"[rx {len(data):>3}B] {_hex_pretty(data)}")
            if self.parse_frames:
                self._buf.extend(data)
                while True:
                    r = _pop_next_response_frame(self._buf)
                    if r is None:
                        break
                    frame, has_status = r
                    opcode = frame[2]
                    if has_status:
                        status = int.from_bytes(frame[3:5], "big")
                        payload = frame[5:-2]
                        self._println(
                            f"  └─ frame op=0x{opcode:02X} status=0x{status:04X} "
                            f"payload={payload.hex(' ')} ({len(payload)}B)"
                        )
                    else:
                        payload = frame[3:-2]
                        self._println(
                            f"  └─ frame op=0x{opcode:02X} (no status) "
                            f"payload={payload.hex(' ')} ({len(payload)}B)"
                        )

    def send(self, data: bytes, label: str = "tx") -> None:
        assert self.ser is not None
        self.ser.write(data)
        # Print directly without prompt-restore, since we're at the prompt
        sys.stdout.write(f"[{label} {len(data):>3}B] {_hex_pretty(data)}\n")
        sys.stdout.flush()

    def reopen(self, baudrate: int) -> None:
        self._stop.set()
        if self._reader_thread:
            self._reader_thread.join(timeout=1.0)
        if self.ser:
            try:
                self.ser.close()
            except Exception:
                pass
        time.sleep(0.1)
        self.baudrate = baudrate
        self.open()
        self.start_reader()


def _print_help() -> None:
    print(__doc__)


def run(port: str, baudrate: int) -> None:
    dbg = RawSerialDebug(port, baudrate)
    try:
        dbg.open()
    except Exception as e:
        print(f"\nCould not open {port}: {e}\n", file=sys.stderr)
        print("Tips:", file=sys.stderr)
        print("  - is the FastAPI app connected to the same port? disconnect first", file=sys.stderr)
        print("  - is the cable plugged in and CH340 driver active?", file=sys.stderr)
        print("  - run with --list to see available ports", file=sys.stderr)
        sys.exit(1)

    dbg.start_reader()
    print("\nType hex bytes to send (e.g. 'FF 00 03 1D 0C'), or a command. 'help' for list, 'quit' to exit.\n")

    try:
        while True:
            try:
                line = input("> ").strip()
            except EOFError:
                break
            if not line:
                continue
            head = line.lower().split()
            if head[0] in ("quit", "exit", "q"):
                break
            if head[0] in ("help", "?"):
                _print_help()
                continue
            if head[0] == "version":
                dbg.send(_build_frame(TMR_SR_OPCODE_VERSION, b""), label="tx VERSION")
                continue
            if head[0] == "stop":
                # Mercury continuous-read stop escalation (matches main.py)
                dbg.send(_build_frame(0x2F, bytes([0x00, 0x00, 0x02])), label="tx STOP_2F")
                time.sleep(0.05)
                dbg.send(_build_frame(0x22, b""), label="tx STOP_22")
                continue
            if head[0] == "dtr" and len(head) == 2 and head[1] in ("on", "off"):
                dbg.ser.dtr = (head[1] == "on")  # type: ignore[union-attr]
                print(f"[dtr] {head[1]}")
                continue
            if head[0] == "rts" and len(head) == 2 and head[1] in ("on", "off"):
                dbg.ser.rts = (head[1] == "on")  # type: ignore[union-attr]
                print(f"[rts] {head[1]}")
                continue
            if head[0] == "baud" and len(head) == 2:
                try:
                    new = int(head[1])
                except ValueError:
                    print("?? invalid baud")
                    continue
                print(f"[reopen] {dbg.port} @ {new}")
                dbg.reopen(new)
                continue
            if head[0] == "parse" and len(head) == 2 and head[1] in ("on", "off"):
                dbg.parse_frames = (head[1] == "on")
                print(f"[parse] {head[1]}")
                continue
            # Anything else: try to interpret as hex bytes to send
            data = _parse_hex_line(line)
            if data is None:
                print("?? not a recognized command and not valid hex; type 'help'")
                continue
            dbg.send(data)
    except KeyboardInterrupt:
        print()
    finally:
        dbg.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("port", nargs="?", help="serial port path (auto-detect if omitted)")
    parser.add_argument(
        "baudrate", nargs="?", default=115200, type=int,
        help="baud rate (default: 115200)",
    )
    parser.add_argument(
        "--list", action="store_true",
        help="list discovered serial ports with reader-likelihood ranking and exit",
    )
    args = parser.parse_args()

    if args.list:
        any_port = False
        for p in serial.tools.list_ports.comports():
            any_port = True
            cat, rank = _classify_port(p.device, p.description or "", p.hwid or "")
            star = "★" if cat == PORT_LIKELY_READER else " "
            print(f" {star} {p.device:<36} rank={rank:<3} {p.description or ''}  {p.hwid or ''}")
        if not any_port:
            print("(no serial ports found)")
        return

    port = args.port or _auto_pick_port()
    if not port:
        print(
            "No port specified and no likely-reader candidates found.\n"
            "Use --list to see available ports, or pass one explicitly.",
            file=sys.stderr,
        )
        sys.exit(1)

    run(port, args.baudrate)


if __name__ == "__main__":
    main()
