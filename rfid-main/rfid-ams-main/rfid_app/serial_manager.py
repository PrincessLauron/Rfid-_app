from dataclasses import dataclass
from typing import Generator, Optional, Union
import time
import threading
import serial  # type: ignore


@dataclass
class TagRead:
    epc: str
    rssi: Optional[float] = None
    antenna: Optional[int] = None
    device_id: Optional[str] = None


class SerialManager:
    def __init__(self, port: str, baudrate: int = 115200):
        self.port = port
        self.baudrate = baudrate
        self._ser: Optional[serial.Serial] = None
        self._mode: str = "single"
        self._running = False

    def connect(self) -> tuple[bool, str]:
        try:
            if self._ser and self._ser.is_open:
                return True, "Already connected"
            self._ser = serial.Serial(self.port, self.baudrate, timeout=0.1)
            return True, f"Connected to {self.port} @ {self.baudrate}"
        except Exception as exc:
            return False, f"Connect failed: {exc}"

    def set_power(self, dbm: int) -> None:
        # TODO: Send device-specific command to set power for SparkFun M7E
        pass

    def set_mode(self, mode: str) -> None:
        self._mode = mode

    def read_loop(self) -> Generator[Union[TagRead, str], None, None]:
        self._running = True
        # In absence of real device protocol, emit mock data if not connected
        device_id = "sparkfun-m7e"
        if not self._ser:
            # Mock generator for development
            while self._running:
                yield TagRead(epc="E2000016591702080730B6B5", rssi=-45.0, antenna=1, device_id=device_id)
                time.sleep(1.0)
            return

        # Real read loop placeholder
        while self._running:
            try:
                line = self._ser.readline().decode(errors="ignore").strip()
                if not line:
                    continue
                # Parse EPC/RSSI from device-specific format (placeholder)
                # Expected: "EPC:<hex> RSSI:<float>"
                if line.startswith("EPC:"):
                    parts = line.split()
                    epc = parts[0].split(":")[1]
                    rssi = None
                    if len(parts) > 1 and parts[1].startswith("RSSI:"):
                        try:
                            rssi = float(parts[1].split(":")[1])
                        except Exception:
                            rssi = None
                    yield TagRead(epc=epc, rssi=rssi, device_id=device_id)
            except Exception as exc:
                yield f"Serial read error: {exc}"
                time.sleep(0.5)

    def stop(self) -> None:
        self._running = False
        if self._ser:
            try:
                self._ser.close()
            except Exception:
                pass


