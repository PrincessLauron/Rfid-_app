import os
import signal
import sys
import time
from typing import Optional

from .serial_manager import SerialManager, TagRead
from .ingest_client import IngestClient
from .sync_worker import SyncWorker


class ScannerService:
    def __init__(self):
        self.api_base_url = os.getenv("AMS_API_BASE_URL", "http://127.0.0.1:8000")
        self.api_token = os.getenv("AMS_API_TOKEN")
        self.serial_port = os.getenv("AMS_SERIAL_PORT", "/dev/ttyAMA0")
        self.baudrate = int(os.getenv("AMS_BAUDRATE", "115200"))
        self.manager = SerialManager(self.serial_port, self.baudrate)
        self.ingest = IngestClient(self.api_base_url, self.api_token)
        self.sync = SyncWorker(self.ingest, interval_seconds=int(os.getenv("AMS_SYNC_INTERVAL", "10")))
        self.running = True

    def stop(self, *_: object) -> None:
        self.running = False
        self.manager.stop()
        self.sync.stop()

    def run(self) -> int:
        ok, msg = self.manager.connect()
        print(msg)
        if not ok:
            return 1

        self.sync.start()

        while self.running:
            for event in self.manager.read_loop():
                if not self.running:
                    break
                if isinstance(event, TagRead):
                    self.ingest.send_tag_read(event)
                elif isinstance(event, str):
                    print(event)
                    time.sleep(0.2)

        return 0


def main() -> int:
    service = ScannerService()
    signal.signal(signal.SIGINT, service.stop)
    signal.signal(signal.SIGTERM, service.stop)
    return service.run()


if __name__ == "__main__":
    sys.exit(main())
