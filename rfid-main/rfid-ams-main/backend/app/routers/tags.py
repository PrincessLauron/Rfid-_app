from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List

from ..db import get_db
from .. import models
from ..schemas import TagCreate, TagOut, TagUpdate
from ..deps import get_current_user, require_roles

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("/", response_model=List[TagOut])
def list_tags(
    q: str | None = Query(default=None, description="Search EPC or label"),
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
) -> List[TagOut]:
    query = db.query(models.Tag)
    if q:
        like = f"%{q}%"
        query = query.filter((models.Tag.epc.like(like)) | (models.Tag.label.like(like)))
    return query.order_by(models.Tag.created_at.desc()).all()


@router.get("/{tag_id}", response_model=TagOut)
def get_tag(tag_id: int, db: Session = Depends(get_db), _: models.User = Depends(get_current_user)) -> TagOut:
    tag = db.get(models.Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag


@router.post("/", response_model=TagOut, status_code=status.HTTP_201_CREATED)
def create_tag(
    payload: TagCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles(["admin"])),
) -> TagOut:
    exists = db.query(models.Tag).filter(models.Tag.epc == payload.epc).first()
    if exists:
        raise HTTPException(status_code=409, detail="EPC already registered")

    tag = models.Tag(**payload.model_dump())
    db.add(tag)
    db.flush()
    db.add(
        models.ActivityLog(
            action="tag_create",
            user_id=user.id,
            details=f"Registered EPC {tag.epc}",
        )
    )
    db.commit()
    db.refresh(tag)
    return tag


@router.put("/{tag_id}", response_model=TagOut)
def update_tag(
    tag_id: int,
    payload: TagUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles(["admin"])),
) -> TagOut:
    tag = db.get(models.Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    if payload.asset_id is not None and payload.asset_id:
        asset = db.get(models.Asset, payload.asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")

    if payload.room_id is not None and payload.room_id:
        room = db.get(models.Room, payload.room_id)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(tag, field, value)

    db.add(
        models.ActivityLog(
            action="tag_update",
            user_id=user.id,
            details=f"Updated EPC {tag.epc}",
        )
    )
    db.commit()
    db.refresh(tag)
    return tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles(["admin"])),
) -> None:
    tag = db.get(models.Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    db.add(
        models.ActivityLog(
            action="tag_delete",
            user_id=user.id,
            details=f"Deleted EPC {tag.epc}",
        )
    )
    db.delete(tag)
    db.commit()
    return None
