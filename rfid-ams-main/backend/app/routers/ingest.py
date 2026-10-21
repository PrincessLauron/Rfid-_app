from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from ..db import get_db
from .. import models
from ..schemas import TagReadIngest, TagReadOut
from ..deps import require_ingest_writer

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/tag-read", response_model=TagReadOut, status_code=status.HTTP_201_CREATED)
def ingest_tag_read(
    payload: TagReadIngest,
    db: Session = Depends(get_db),
    user: models.User | None = Depends(require_ingest_writer),
) -> TagReadOut:
    read_time = payload.read_at or datetime.utcnow()
    tag_read = models.TagRead(
        epc=payload.epc,
        rssi=payload.rssi,
        antenna=payload.antenna,
        device_id=payload.device_id,
        read_at=read_time,
    )

    # Link to asset if provided or try by EPC
    asset = None
    if payload.asset_id:
        asset = db.get(models.Asset, payload.asset_id)
    elif payload.epc:
        asset = db.query(models.Asset).filter(models.Asset.tag_epc == payload.epc).first()
        if not asset:
            registered_tag = db.query(models.Tag).filter(models.Tag.epc == payload.epc).first()
            if registered_tag and registered_tag.asset_id:
                asset = db.get(models.Asset, registered_tag.asset_id)
    if asset:
        tag_read.asset = asset

    db.add(tag_read)
    db.flush()
    db.add(
        models.ActivityLog(
            action="tag_ingest",
            user_id=user.id if user else None,
            details="ingested via device token" if user is None else None,
            tag_read_id=tag_read.id,
            asset_id=tag_read.asset_id,
        )
    )
    db.commit()
    db.refresh(tag_read)
    return tag_read

