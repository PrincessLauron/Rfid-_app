from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from ..db import get_db
from .. import models
from ..schemas import ActivityLogOut
from ..deps import require_roles

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("/", response_model=List[ActivityLogOut])
def list_logs(
    db: Session = Depends(get_db),
    _: models.User = Depends(require_roles(["admin"])),
) -> List[ActivityLogOut]:
    logs = db.query(models.ActivityLog).order_by(models.ActivityLog.created_at.desc()).limit(500).all()
    return logs


