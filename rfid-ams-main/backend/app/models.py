from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Table,
    Float,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime


from .db import Base


# Association table for many-to-many between users and roles
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)


memorandum_receipt_assets = Table(
    "memorandum_receipt_assets",
    Base.metadata,
    Column("memorandum_receipt_id", ForeignKey("memorandum_receipts.id", ondelete="CASCADE"), primary_key=True),
    Column("asset_id", ForeignKey("assets.id", ondelete="CASCADE"), primary_key=True),
)




class User(Base):
    __tablename__ = "users"


    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


    roles: Mapped[list["Role"]] = relationship(
        "Role", secondary=user_roles, back_populates="users", lazy="joined"
    )
    activity_logs: Mapped[list["ActivityLog"]] = relationship(
        "ActivityLog", back_populates="user", cascade="all,delete-orphan"
    )




class Role(Base):
    __tablename__ = "roles"


    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)


    users: Mapped[list["User"]] = relationship("User", secondary=user_roles, back_populates="roles")




class Asset(Base):
    __tablename__ = "assets"


    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    serial_number: Mapped[str | None] = mapped_column(String(120), index=True)
    tag_epc: Mapped[str | None] = mapped_column(String(128), index=True)  # optional linked EPC
    location: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[str | None] = mapped_column(String(50))  # e.g., in_service, retired, maintenance
    component_type: Mapped[str | None] = mapped_column(String(50))  # e.g., pc, keyboard, mouse, cables, monitor
    specs: Mapped[str | None] = mapped_column(Text)  # free-form hardware specs/details
    room_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("rooms.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


    room: Mapped["Room | None"] = relationship("Room", back_populates="assets")
    registered_tags: Mapped[list["Tag"]] = relationship("Tag", back_populates="asset")
    tag_reads: Mapped[list["TagRead"]] = relationship(
        "TagRead", back_populates="asset", cascade="all,delete-orphan"
    )
    activity_logs: Mapped[list["ActivityLog"]] = relationship(
        "ActivityLog", back_populates="asset", cascade="all,delete-orphan"
    )
    group_items: Mapped[list["AssetGroupItem"]] = relationship("AssetGroupItem", back_populates="asset")
    memorandum_receipts: Mapped[list["MemorandumReceipt"]] = relationship(
        "MemorandumReceipt", secondary=memorandum_receipt_assets, back_populates="assets"
    )




class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = (UniqueConstraint("epc", name="uq_tags_epc"),)


    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    epc: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    label: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)  # active/inactive
    asset_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("assets.id", ondelete="SET NULL"))
    room_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("rooms.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


    asset: Mapped["Asset | None"] = relationship("Asset", back_populates="registered_tags")
    room: Mapped["Room | None"] = relationship("Room", back_populates="tags")
    observations: Mapped[list["ScanObservation"]] = relationship("ScanObservation", back_populates="tag")




class Room(Base):
    __tablename__ = "rooms"


    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    code: Mapped[str | None] = mapped_column(String(60), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


    assets: Mapped[list["Asset"]] = relationship("Asset", back_populates="room")
    tags: Mapped[list["Tag"]] = relationship("Tag", back_populates="room")
    scan_sessions: Mapped[list["ScanSession"]] = relationship("ScanSession", back_populates="room")
    anomalies: Mapped[list["Anomaly"]] = relationship("Anomaly", back_populates="room")
    groups: Mapped[list["AssetGroup"]] = relationship("AssetGroup", back_populates="room")




class ScanSession(Base):
    __tablename__ = "scan_sessions"


    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    room_id: Mapped[int] = mapped_column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)  # open/closed
    max_unique_tags: Mapped[int] = mapped_column(Integer, default=150, nullable=False)
    limit_reached: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    started_by_user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime)


    room: Mapped["Room"] = relationship("Room", back_populates="scan_sessions")
    observations: Mapped[list["ScanObservation"]] = relationship(
        "ScanObservation", back_populates="scan_session", cascade="all,delete-orphan"
    )




class ScanObservation(Base):
    __tablename__ = "scan_observations"
    __table_args__ = (UniqueConstraint("scan_session_id", "epc", name="uq_scan_observations_session_epc"),)


    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    scan_session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("scan_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tag_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("tags.id", ondelete="SET NULL"))
    epc: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    read_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


    scan_session: Mapped["ScanSession"] = relationship("ScanSession", back_populates="observations")
    tag: Mapped["Tag | None"] = relationship("Tag", back_populates="observations")




class AssetGroup(Base):
    __tablename__ = "asset_groups"


    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    room_id: Mapped[int] = mapped_column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


    room: Mapped["Room"] = relationship("Room", back_populates="groups")
    items: Mapped[list["AssetGroupItem"]] = relationship(
        "AssetGroupItem", back_populates="group", cascade="all,delete-orphan"
    )
    anomalies: Mapped[list["Anomaly"]] = relationship("Anomaly", back_populates="group")




class AssetGroupItem(Base):
    __tablename__ = "asset_group_items"


    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("asset_groups.id", ondelete="CASCADE"), nullable=False)
    required_component: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    asset_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("assets.id", ondelete="SET NULL"))
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


    group: Mapped["AssetGroup"] = relationship("AssetGroup", back_populates="items")
    asset: Mapped["Asset | None"] = relationship("Asset", back_populates="group_items")




class Anomaly(Base):
    __tablename__ = "anomalies"


    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # missing/transfer/incomplete_group
    status: Mapped[str] = mapped_column(String(30), default="open", nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    details: Mapped[str | None] = mapped_column(Text)
    room_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("rooms.id", ondelete="SET NULL"), index=True)
    asset_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("assets.id", ondelete="SET NULL"))
    group_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("asset_groups.id", ondelete="SET NULL"))
    consecutive_misses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)


    room: Mapped["Room | None"] = relationship("Room", back_populates="anomalies")
    asset: Mapped["Asset | None"] = relationship("Asset")
    group: Mapped["AssetGroup | None"] = relationship("AssetGroup", back_populates="anomalies")




class TagRead(Base):
    __tablename__ = "tag_reads"


    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    epc: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    rssi: Mapped[float | None] = mapped_column(Float)
    antenna: Mapped[int | None] = mapped_column(Integer)
    device_id: Mapped[str | None] = mapped_column(String(120))
    read_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True, nullable=False)


    asset_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("assets.id", ondelete="SET NULL"))
    asset: Mapped["Asset | None"] = relationship("Asset", back_populates="tag_reads")


    # Optional link to activity log
    activity_logs: Mapped[list["ActivityLog"]] = relationship(
        "ActivityLog", back_populates="tag_read", cascade="all,delete-orphan"
    )




class ActivityLog(Base):
    __tablename__ = "activity_logs"


    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    action: Mapped[str] = mapped_column(String(120), index=True, nullable=False)  # e.g., login, asset_update, tag_ingest
    details: Mapped[str | None] = mapped_column(Text)  # optional JSON/text payload
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    asset_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("assets.id", ondelete="SET NULL"))
    tag_read_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("tag_reads.id", ondelete="SET NULL"))


    user: Mapped["User | None"] = relationship("User", back_populates="activity_logs")
    asset: Mapped["Asset | None"] = relationship("Asset", back_populates="activity_logs")
    tag_read: Mapped["TagRead | None"] = relationship("TagRead", back_populates="activity_logs")




class MemorandumReceipt(Base):
    __tablename__ = "memorandum_receipts"


    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    reference_no: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    issued_to: Mapped[str] = mapped_column(String(160), nullable=False)
    assignee_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("mr_assignees.id", ondelete="SET NULL"))
    issued_by: Mapped[str | None] = mapped_column(String(160))
    issued_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False, index=True)  # active/returned
    room_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("rooms.id", ondelete="SET NULL"))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


    room: Mapped["Room | None"] = relationship("Room")
    assignee: Mapped["MRAssignee | None"] = relationship("MRAssignee", back_populates="memorandum_receipts")
    assets: Mapped[list["Asset"]] = relationship(
        "Asset", secondary=memorandum_receipt_assets, back_populates="memorandum_receipts"
    )




class MRAssignee(Base):
    __tablename__ = "mr_assignees"


    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False, unique=True, index=True)
    initials: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


    memorandum_receipts: Mapped[list["MemorandumReceipt"]] = relationship("MemorandumReceipt", back_populates="assignee")




    
