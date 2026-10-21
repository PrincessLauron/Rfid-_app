from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..db import get_db
from .. import models
from ..deps import get_current_user, require_roles
from ..schemas import (
    RoomCreate,
    RoomOut,
    AssetGroupCreate,
    AssetGroupOut,
    ScanSessionCreate,
    ScanSessionOut,
    ScanObserveIn,
    ScanReconcileOut,
    AnomalyOut,
    AnomalyStatusUpdate,
)
from ..reconciliation import reconcile_session

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post("/rooms", response_model=RoomOut, status_code=status.HTTP_201_CREATED)
def create_room(
    payload: RoomCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles(["admin"])),
) -> RoomOut:
    existing = db.query(models.Room).filter(models.Room.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=409, detail="Room already exists")
    room = models.Room(**payload.model_dump())
    db.add(room)
    db.flush()
    db.add(models.ActivityLog(action="room_create", user_id=user.id, details=f"Created room {room.name}"))
    db.commit()
    db.refresh(room)
    return room


@router.get("/rooms", response_model=List[RoomOut])
def list_rooms(db: Session = Depends(get_db), _: models.User = Depends(get_current_user)) -> List[RoomOut]:
    return db.query(models.Room).order_by(models.Room.name.asc()).all()


@router.post("/groups", response_model=AssetGroupOut, status_code=status.HTTP_201_CREATED)
def create_group(
    payload: AssetGroupCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles(["admin"])),
) -> AssetGroupOut:
    room = db.get(models.Room, payload.room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    group = models.AssetGroup(name=payload.name, room_id=payload.room_id)
    db.add(group)
    db.flush()
    for item in payload.items:
        if item.asset_id:
            asset = db.get(models.Asset, item.asset_id)
            if not asset:
                raise HTTPException(status_code=404, detail=f"Asset {item.asset_id} not found")
        db.add(
            models.AssetGroupItem(
                group_id=group.id,
                required_component=item.required_component,
                asset_id=item.asset_id,
                is_required=item.is_required,
            )
        )

    db.add(models.ActivityLog(action="group_create", user_id=user.id, details=f"Created group {group.name}"))
    db.commit()
    db.refresh(group)
    return group


@router.get("/groups", response_model=List[AssetGroupOut])
def list_groups(db: Session = Depends(get_db), _: models.User = Depends(get_current_user)) -> List[AssetGroupOut]:
    return db.query(models.AssetGroup).order_by(models.AssetGroup.created_at.desc()).all()


@router.post("/sessions", response_model=ScanSessionOut, status_code=status.HTTP_201_CREATED)
def start_session(
    payload: ScanSessionCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles(["admin", "technician"])),
) -> ScanSessionOut:
    room = db.get(models.Room, payload.room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    session = models.ScanSession(
        room_id=payload.room_id,
        max_unique_tags=max(payload.max_unique_tags, 1),
        started_by_user_id=user.id,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.post("/sessions/{session_id}/observe", response_model=ScanSessionOut)
def observe_tags(
    session_id: int,
    payload: ScanObserveIn,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_roles(["admin", "technician"])),
) -> ScanSessionOut:
    session = db.get(models.ScanSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != "open":
        raise HTTPException(status_code=400, detail="Session already closed")

    for epc in payload.epcs:
        normalized = epc.strip()
        if not normalized:
            continue
        existing = (
            db.query(models.ScanObservation)
            .filter(models.ScanObservation.scan_session_id == session.id, models.ScanObservation.epc == normalized)
            .first()
        )
        if existing:
            existing.read_count += 1
            existing.last_seen_at = datetime.utcnow()
            continue

        unique_count = db.query(models.ScanObservation).filter(models.ScanObservation.scan_session_id == session.id).count()
        if unique_count >= session.max_unique_tags:
            session.limit_reached = True
            continue

        tag = db.query(models.Tag).filter(models.Tag.epc == normalized).first()
        db.add(
            models.ScanObservation(
                scan_session_id=session.id,
                tag_id=tag.id if tag else None,
                epc=normalized,
                read_count=1,
            )
        )

    db.commit()
    db.refresh(session)
    return session


@router.post("/sessions/{session_id}/close", response_model=ScanReconcileOut)
def close_session(
    session_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_roles(["admin", "technician"])),
) -> ScanReconcileOut:
    session = db.get(models.ScanSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status == "closed":
        observed_count = db.query(models.ScanObservation).filter(models.ScanObservation.scan_session_id == session.id).count()
        return ScanReconcileOut(
            session=session,
            observed_unique=observed_count,
            missing_asset_ids=[],
            transfer_asset_ids=[],
            incomplete_group_ids=[],
        )

    session.status = "closed"
    session.ended_at = datetime.utcnow()
    db.flush()

    result = reconcile_session(db, session)
    db.commit()
    db.refresh(session)

    observed_count = db.query(models.ScanObservation).filter(models.ScanObservation.scan_session_id == session.id).count()
    return ScanReconcileOut(
        session=session,
        observed_unique=observed_count,
        missing_asset_ids=result["missing_asset_ids"],
        transfer_asset_ids=result["transfer_asset_ids"],
        incomplete_group_ids=result["incomplete_group_ids"],
    )


@router.get("/anomalies", response_model=List[AnomalyOut])
def list_anomalies(db: Session = Depends(get_db), _: models.User = Depends(get_current_user)) -> List[AnomalyOut]:
    return db.query(models.Anomaly).order_by(models.Anomaly.last_seen_at.desc()).all()


@router.patch("/anomalies/{anomaly_id}", response_model=AnomalyOut)
def update_anomaly_status(
    anomaly_id: int,
    payload: AnomalyStatusUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles(["admin"])),
) -> AnomalyOut:
    anomaly = db.get(models.Anomaly, anomaly_id)
    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found")

    anomaly.status = payload.status
    if payload.status == "resolved":
        anomaly.resolved_at = datetime.utcnow()

    db.add(
        models.ActivityLog(
            action="anomaly_status_update",
            user_id=user.id,
            details=f"Anomaly {anomaly.id} status -> {payload.status}",
        )
    )
    db.commit()
    db.refresh(anomaly)
    return anomaly
