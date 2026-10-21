import threading
import time
from .ingest_client import IngestClient


class SyncWorker:
    def __init__(self, client: IngestClient, interval_seconds: int = 10):
        self.client = client
        self.interval_seconds = interval_seconds
        self._thread: threading.Thread | None = None
        self._stop = False

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop = False
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        while not self._stop:
            try:
                self.client.try_sync()
            except Exception:
                pass
            time.sleep(self.interval_seconds)

    def stop(self):
        self._stop = True
        if self._thread:
            self._thread.join(timeout=2.0)


