from datetime import datetime
from sqlalchemy.orm import Session

from . import models


def _upsert_anomaly(
    db: Session,
    *,
    anomaly_type: str,
    room_id: int,
    asset_id: int | None = None,
    group_id: int | None = None,
    severity: str = "medium",
    details: str | None = None,
    consecutive_misses: int | None = None,
) -> models.Anomaly:
    anomaly = (
        db.query(models.Anomaly)
        .filter(
            models.Anomaly.type == anomaly_type,
            models.Anomaly.room_id == room_id,
            models.Anomaly.asset_id == asset_id,
            models.Anomaly.group_id == group_id,
            models.Anomaly.status != "resolved",
        )
        .first()
    )
    now = datetime.utcnow()
    if anomaly:
        anomaly.last_seen_at = now
        anomaly.details = details
        anomaly.severity = severity
        if consecutive_misses is not None:
            anomaly.consecutive_misses = consecutive_misses
    else:
        anomaly = models.Anomaly(
            type=anomaly_type,
            status="open",
            severity=severity,
            details=details,
            room_id=room_id,
            asset_id=asset_id,
            group_id=group_id,
            consecutive_misses=consecutive_misses or 0,
            first_seen_at=now,
            last_seen_at=now,
        )
        db.add(anomaly)
    return anomaly


def _resolve_anomaly(db: Session, anomaly_type: str, room_id: int, asset_id: int | None = None, group_id: int | None = None) -> None:
    active = (
        db.query(models.Anomaly)
        .filter(
            models.Anomaly.type == anomaly_type,
            models.Anomaly.room_id == room_id,
            models.Anomaly.asset_id == asset_id,
            models.Anomaly.group_id == group_id,
            models.Anomaly.status != "resolved",
        )
        .all()
    )
    for anomaly in active:
        anomaly.status = "resolved"
        anomaly.resolved_at = datetime.utcnow()
        anomaly.last_seen_at = anomaly.resolved_at


def reconcile_session(db: Session, session: models.ScanSession) -> dict[str, list[int]]:
    observed_epcs = {o.epc for o in session.observations}

    room_tags = db.query(models.Tag).filter(models.Tag.room_id == session.room_id, models.Tag.status == "active").all()
    missing_asset_ids: list[int] = []
    transfer_asset_ids: list[int] = []

    for tag in room_tags:
        if not tag.asset_id:
            continue
        if tag.epc in observed_epcs:
            _resolve_anomaly(db, "missing", session.room_id, asset_id=tag.asset_id)
            continue

        history_sessions = (
            db.query(models.ScanSession)
            .filter(models.ScanSession.room_id == session.room_id, models.ScanSession.status == "closed")
            .order_by(models.ScanSession.started_at.desc())
            .limit(2)
            .all()
        )
        consecutive_misses = 0
        for hist in history_sessions:
            epcs = {o.epc for o in hist.observations}
            if tag.epc not in epcs:
                consecutive_misses += 1
            else:
                break

        if consecutive_misses >= 2:
            missing_asset_ids.append(tag.asset_id)
            _upsert_anomaly(
                db,
                anomaly_type="missing",
                room_id=session.room_id,
                asset_id=tag.asset_id,
                severity="high",
                details=f"Asset with EPC {tag.epc} missing in {consecutive_misses} consecutive scans",
                consecutive_misses=consecutive_misses,
            )

    observed_tags = db.query(models.Tag).filter(models.Tag.epc.in_(list(observed_epcs))).all() if observed_epcs else []
    for tag in observed_tags:
        if tag.asset_id and tag.room_id and tag.room_id != session.room_id:
            transfer_asset_ids.append(tag.asset_id)
            _upsert_anomaly(
                db,
                anomaly_type="transfer",
                room_id=session.room_id,
                asset_id=tag.asset_id,
                severity="high",
                details=f"EPC {tag.epc} observed in room {session.room_id} but assigned to room {tag.room_id}",
            )

    incomplete_group_ids: list[int] = []
    groups = db.query(models.AssetGroup).filter(models.AssetGroup.room_id == session.room_id).all()
    for group in groups:
        missing_components: list[str] = []
        for item in group.items:
            if not item.is_required:
                continue
            matched = False
            if item.asset and item.asset.tag_epc:
                matched = item.asset.tag_epc in observed_epcs
            elif item.asset:
                linked_tag = db.query(models.Tag).filter(models.Tag.asset_id == item.asset.id, models.Tag.status == "active").first()
                matched = bool(linked_tag and linked_tag.epc in observed_epcs)
            if not matched:
                missing_components.append(item.required_component)

        if missing_components:
            incomplete_group_ids.append(group.id)
            _upsert_anomaly(
                db,
                anomaly_type="incomplete_group",
                room_id=session.room_id,
                group_id=group.id,
                severity="medium",
                details=f"Group '{group.name}' missing required components: {', '.join(sorted(set(missing_components)))}",
            )
        else:
            _resolve_anomaly(db, "incomplete_group", session.room_id, group_id=group.id)

    return {
        "missing_asset_ids": sorted(set(missing_asset_ids)),
        "transfer_asset_ids": sorted(set(transfer_asset_ids)),
        "incomplete_group_ids": sorted(set(incomplete_group_ids)),
    }
