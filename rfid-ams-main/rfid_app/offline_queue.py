import os
import sqlite3
from contextlib import contextmanager
from typing import Iterable, Optional, Tuple
from datetime import datetime


DB_PATH = os.path.join(os.path.dirname(__file__), "offline.db")


def _ensure_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pending_reads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            epc TEXT NOT NULL,
            rssi REAL NULL,
            antenna INTEGER NULL,
            device_id TEXT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()


@contextmanager
def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        _ensure_db(conn)
        yield conn
    finally:
        conn.close()


def enqueue_read(epc: str, rssi: Optional[float], antenna: Optional[int], device_id: Optional[str]) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO pending_reads (epc, rssi, antenna, device_id, created_at) VALUES (?,?,?,?,?)",
            (epc, rssi, antenna, device_id, datetime.utcnow().isoformat()),
        )
        conn.commit()


def get_batch(limit: int = 100) -> Iterable[Tuple[int, str, Optional[float], Optional[int], Optional[str]]]:
    with get_conn() as conn:
        for row in conn.execute(
            "SELECT id, epc, rssi, antenna, device_id FROM pending_reads ORDER BY id ASC LIMIT ?", (limit,)
        ):
            yield row


def delete_ids(ids: Iterable[int]) -> None:
    ids = list(ids)
    if not ids:
        return
    placeholders = ",".join("?" for _ in ids)
    with get_conn() as conn:
        conn.execute(f"DELETE FROM pending_reads WHERE id IN ({placeholders})", ids)
        conn.commit()


