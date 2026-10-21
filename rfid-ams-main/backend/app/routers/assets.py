from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..db import get_db
from .. import models
from ..schemas import AssetCreate, AssetUpdate, AssetOut
from ..deps import get_current_user, require_roles

router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("/", response_model=List[AssetOut])
def list_assets(db: Session = Depends(get_db), _: models.User = Depends(get_current_user)) -> List[AssetOut]:
    assets = db.query(models.Asset).order_by(models.Asset.created_at.desc()).all()
    return assets


@router.get("/{asset_id}", response_model=AssetOut)
def get_asset(asset_id: int, db: Session = Depends(get_db), _: models.User = Depends(get_current_user)) -> AssetOut:
    asset = db.get(models.Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.post("/", response_model=AssetOut, status_code=status.HTTP_201_CREATED)
def create_asset(
    payload: AssetCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles(["admin", "technician"])),
) -> AssetOut:
    if payload.room_id:
        room = db.get(models.Room, payload.room_id)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
    asset = models.Asset(**payload.model_dump())
    db.add(asset)
    db.flush()
    db.add(models.ActivityLog(action="asset_create", user_id=user.id, asset_id=asset.id))
    db.commit()
    db.refresh(asset)
    return asset


@router.put("/{asset_id}", response_model=AssetOut)
def update_asset(
    asset_id: int,
    payload: AssetUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles(["admin", "technician"])),
) -> AssetOut:
    asset = db.get(models.Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    if payload.room_id:
        room = db.get(models.Room, payload.room_id)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(asset, field, value)
    db.add(models.ActivityLog(action="asset_update", user_id=user.id, asset_id=asset.id))
    db.commit()
    db.refresh(asset)
    return asset


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles(["admin"])),
) -> None:
    asset = db.get(models.Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    db.delete(asset)
    db.add(models.ActivityLog(action="asset_delete", user_id=user.id, asset_id=asset_id))
    db.commit()
    return None

