import httpx
import logging
from typing import Optional
from .serial_manager import TagRead
from .offline_queue import enqueue_read, get_batch, delete_ids

logger = logging.getLogger(__name__)


class IngestClient:
    def __init__(self, base_url: str, token: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.token = token

    def send_tag_read(self, tag: TagRead) -> None:
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        try:
            with httpx.Client(timeout=3.0, headers=headers) as client:
                resp = client.post(
                    f"{self.base_url}/ingest/tag-read",
                    json={
                        "epc": tag.epc,
                        "rssi": tag.rssi,
                        "antenna": tag.antenna,
                        "device_id": tag.device_id,
                    },
                )
                if resp.status_code >= 300:
                    enqueue_read(tag.epc, tag.rssi, tag.antenna, tag.device_id)
                    logger.warning("Tag read queued after HTTP %s for EPC %s", resp.status_code, tag.epc)
        except Exception:
            # enqueue for offline sync
            enqueue_read(tag.epc, tag.rssi, tag.antenna, tag.device_id)
            logger.exception("Tag read queued after transport failure for EPC %s", tag.epc)

    def try_sync(self) -> int:
        """Attempt to push a batch of pending reads. Returns count synced."""
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        synced_ids = []
        with httpx.Client(timeout=5.0, headers=headers) as client:
            for row in get_batch(200):
                row_id, epc, rssi, antenna, device_id = row
                try:
                    resp = client.post(
                        f"{self.base_url}/ingest/tag-read",
                        json={
                            "epc": epc,
                            "rssi": rssi,
                            "antenna": antenna,
                            "device_id": device_id,
                        },
                    )
                    if resp.status_code < 300:
                        synced_ids.append(row_id)
                    else:
                        logger.warning("Pending read %s not synced, HTTP %s", row_id, resp.status_code)
                except Exception:
                    logger.exception("Pending read %s failed to sync", row_id)

        if synced_ids:
            delete_ids(synced_ids)
            logger.info("Synced %s pending reads", len(synced_ids))
        return len(synced_ids)

