import sqlite3
import tempfile
import unittest
from pathlib import Path

from rfid_app.ingest_client import IngestClient
from rfid_app.serial_manager import TagRead
from rfid_app import offline_queue


class _Resp:
    def __init__(self, status_code: int):
        self.status_code = status_code


class _ClientBase:
    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class IngestClientTestCase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmpdir.name) / "offline.db"
        offline_queue.DB_PATH = str(self.db_path)

    def tearDown(self):
        self.tmpdir.cleanup()

    def _pending_count(self) -> int:
        conn = sqlite3.connect(self.db_path)
        try:
            return conn.execute("SELECT COUNT(*) FROM pending_reads").fetchone()[0]
        finally:
            conn.close()

    def test_queue_on_http_error(self):
        import rfid_app.ingest_client as ingest_module

        class _ClientFail(_ClientBase):
            def post(self, *args, **kwargs):
                return _Resp(401)

        original = ingest_module.httpx.Client
        ingest_module.httpx.Client = _ClientFail
        try:
            client = IngestClient("http://localhost:8000", token="device-token")
            client.send_tag_read(TagRead(epc="E200FAIL", rssi=-50.0, antenna=1, device_id="m7e"))
            self.assertEqual(self._pending_count(), 1)
        finally:
            ingest_module.httpx.Client = original

    def test_try_sync_deletes_only_success(self):
        import rfid_app.ingest_client as ingest_module

        offline_queue.enqueue_read("E200ONE", -40.0, 1, "m7e")
        offline_queue.enqueue_read("E200TWO", -41.0, 1, "m7e")
        self.assertEqual(self._pending_count(), 2)

        calls = {"n": 0}

        class _ClientMixed(_ClientBase):
            def post(self, *args, **kwargs):
                calls["n"] += 1
                return _Resp(201 if calls["n"] == 1 else 500)

        original = ingest_module.httpx.Client
        ingest_module.httpx.Client = _ClientMixed
        try:
            client = IngestClient("http://localhost:8000", token="device-token")
            synced = client.try_sync()
            self.assertEqual(synced, 1)
            self.assertEqual(self._pending_count(), 1)
        finally:
            ingest_module.httpx.Client = original


if __name__ == "__main__":
    unittest.main()
