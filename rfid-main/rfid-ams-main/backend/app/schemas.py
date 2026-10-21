from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


# User schemas
class RoleOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_active: bool
    roles: List[RoleOut] = []
    created_at: datetime

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    roles: Optional[List[str]] = None  # role names


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


# Inventory schemas
class RoomBase(BaseModel):
    name: str
    code: Optional[str] = None


class RoomCreate(RoomBase):
    pass


class RoomOut(RoomBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Asset schemas
class AssetBase(BaseModel):
    name: str
    serial_number: Optional[str] = None
    tag_epc: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    component_type: Optional[str] = None
    room_id: Optional[int] = None


class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseModel):
    name: Optional[str] = None
    serial_number: Optional[str] = None
    tag_epc: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    component_type: Optional[str] = None
    room_id: Optional[int] = None


class AssetOut(AssetBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TagBase(BaseModel):
    epc: str
    label: Optional[str] = None
    status: str = "active"
    asset_id: Optional[int] = None
    room_id: Optional[int] = None


class TagCreate(TagBase):
    pass


class TagUpdate(BaseModel):
    label: Optional[str] = None
    status: Optional[str] = None
    asset_id: Optional[int] = None
    room_id: Optional[int] = None


class TagOut(TagBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AssetGroupItemCreate(BaseModel):
    required_component: str
    asset_id: Optional[int] = None
    is_required: bool = True


class AssetGroupItemOut(BaseModel):
    id: int
    required_component: str
    asset_id: Optional[int] = None
    is_required: bool

    class Config:
        from_attributes = True


class AssetGroupCreate(BaseModel):
    name: str
    room_id: int
    items: List[AssetGroupItemCreate] = []


class AssetGroupOut(BaseModel):
    id: int
    name: str
    room_id: int
    created_at: datetime
    items: List[AssetGroupItemOut] = []

    class Config:
        from_attributes = True


class ScanSessionCreate(BaseModel):
    room_id: int
    max_unique_tags: int = 150


class ScanObserveIn(BaseModel):
    epcs: List[str] = Field(default_factory=list)


class ScanSessionOut(BaseModel):
    id: int
    room_id: int
    status: str
    max_unique_tags: int
    limit_reached: bool
    started_at: datetime
    ended_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AnomalyOut(BaseModel):
    id: int
    type: str
    status: str
    severity: str
    details: Optional[str] = None
    room_id: Optional[int] = None
    asset_id: Optional[int] = None
    group_id: Optional[int] = None
    consecutive_misses: int
    first_seen_at: datetime
    last_seen_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScanReconcileOut(BaseModel):
    session: ScanSessionOut
    observed_unique: int
    missing_asset_ids: List[int]
    transfer_asset_ids: List[int]
    incomplete_group_ids: List[int]


class AnomalyStatusUpdate(BaseModel):
    status: str = Field(pattern="^(open|acknowledged|resolved)$")


# Activity log schemas
class ActivityLogOut(BaseModel):
    id: int
    action: str
    details: Optional[str] = None
    created_at: datetime
    user_id: Optional[int] = None
    asset_id: Optional[int] = None
    tag_read_id: Optional[int] = None

    class Config:
        from_attributes = True


# TagRead schemas
class TagReadIngest(BaseModel):
    epc: str
    rssi: Optional[float] = None
    antenna: Optional[int] = None
    device_id: Optional[str] = None
    asset_id: Optional[int] = None
    read_at: Optional[datetime] = None


class TagReadOut(BaseModel):
    id: int
    epc: str
    rssi: Optional[float] = None
    antenna: Optional[int] = None
    device_id: Optional[str] = None
    read_at: datetime
    asset_id: Optional[int] = None

    class Config:
        from_attributes = True
