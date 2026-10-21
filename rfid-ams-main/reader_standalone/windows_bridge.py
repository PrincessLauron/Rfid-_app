"""
windows_bridge.py — Serial-over-TCP bridge for the RFID Reader Monitor
=======================================================================
Run this on the Windows machine that has the RFID reader plugged in.
It opens the COM port and exposes it as a TCP server so the Mac (or any
machine) running the main reader app can connect via:

    socket://WINDOWS_IP:9876

Usage:
    python windows_bridge.py                      # defaults: COM3, 115200, port 9876
    python windows_bridge.py COM4                 # different COM port
    python windows_bridge.py COM4 115200 9876     # explicit all options

Once running, enter  socket://<this-machine-IP>:9876  as the Port in the
Reader Monitor UI on any browser on the same network, then click Connect.
"""

import socket
import sys
import threading
import time

try:
    import serial
except ImportError:
    print("pyserial not found. Install it:  pip install pyserial")
    sys.exit(1)


def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def bridge(com_port: str, baudrate: int, tcp_port: int) -> None:
    print(f"\n{'='*55}")
    print(f"  RFID Reader Bridge")
    print(f"{'='*55}")
    print(f"  COM port  : {com_port} @ {baudrate} baud")
    print(f"  TCP port  : {tcp_port}")
    print(f"  Enter this in the Reader Monitor UI:")
    print(f"  socket://{get_local_ip()}:{tcp_port}")
    print(f"{'='*55}\n")

    # Open the serial port
    try:
        ser = serial.Serial(com_port, baudrate, timeout=0.05)
        print(f"[OK] Opened {com_port}")
    except Exception as e:
        print(f"[ERROR] Cannot open {com_port}: {e}")
        print("  Check the COM port name (Device Manager → Ports)")
        sys.exit(1)

    # Start TCP server
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        srv.bind(("0.0.0.0", tcp_port))
    except OSError as e:
        print(f"[ERROR] Cannot bind to port {tcp_port}: {e}")
        sys.exit(1)

    srv.listen(1)
    print(f"[OK] Listening on TCP port {tcp_port} — waiting for connection…\n")

    while True:
        try:
            conn, addr = srv.accept()
            print(f"[+] Connected from {addr[0]}:{addr[1]}")
            _handle_client(ser, conn)
            print(f"[-] Disconnected — waiting for next connection…\n")
        except KeyboardInterrupt:
            print("\n[STOP] Bridge stopped.")
            break
        except Exception as e:
            print(f"[WARN] Connection error: {e} — reconnecting…")
            time.sleep(0.5)

    ser.close()
    srv.close()


def _handle_client(ser: "serial.Serial", conn: socket.socket) -> None:
    stop = threading.Event()

    def serial_to_tcp():
        while not stop.is_set():
            try:
                data = ser.read(256)
                if data:
                    conn.sendall(data)
            except Exception:
                stop.set()
                break

    def tcp_to_serial():
        while not stop.is_set():
            try:
                data = conn.recv(256)
                if not data:
                    stop.set()
                    break
                ser.write(data)
            except Exception:
                stop.set()
                break

    t1 = threading.Thread(target=serial_to_tcp, daemon=True)
    t2 = threading.Thread(target=tcp_to_serial, daemon=True)
    t1.start()
    t2.start()
    stop.wait()
    try:
        conn.close()
    except Exception:
        pass


if __name__ == "__main__":
    args = sys.argv[1:]
    com  = args[0] if len(args) > 0 else "COM3"
    baud = int(args[1]) if len(args) > 1 else 115200
    port = int(args[2]) if len(args) > 2 else 9876
    bridge(com, baud, port)
