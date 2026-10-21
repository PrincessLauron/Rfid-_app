"""inventory and tags extensions

Revision ID: 9f12d3b4c5d6
Revises: e48a2e5ec2b1
Create Date: 2026-02-27 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9f12d3b4c5d6"
down_revision: Union[str, Sequence[str], None] = "e48a2e5ec2b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "rooms",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("code", sa.String(length=60), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_rooms_id"), "rooms", ["id"], unique=False)
    op.create_index(op.f("ix_rooms_name"), "rooms", ["name"], unique=True)
    op.create_index(op.f("ix_rooms_code"), "rooms", ["code"], unique=True)

    with op.batch_alter_table("assets") as batch_op:
        batch_op.add_column(sa.Column("component_type", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("room_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_assets_room_id", "rooms", ["room_id"], ["id"], ondelete="SET NULL")

    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("epc", sa.String(length=128), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=True),
        sa.Column("room_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("epc", name="uq_tags_epc"),
    )
    op.create_index(op.f("ix_tags_id"), "tags", ["id"], unique=False)
    op.create_index(op.f("ix_tags_epc"), "tags", ["epc"], unique=False)

    op.create_table(
        "scan_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("max_unique_tags", sa.Integer(), nullable=False),
        sa.Column("limit_reached", sa.Boolean(), nullable=False),
        sa.Column("started_by_user_id", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["started_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_scan_sessions_id"), "scan_sessions", ["id"], unique=False)
    op.create_index(op.f("ix_scan_sessions_room_id"), "scan_sessions", ["room_id"], unique=False)
    op.create_index(op.f("ix_scan_sessions_started_at"), "scan_sessions", ["started_at"], unique=False)

    op.create_table(
        "asset_groups",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_asset_groups_id"), "asset_groups", ["id"], unique=False)
    op.create_index(op.f("ix_asset_groups_name"), "asset_groups", ["name"], unique=False)
    op.create_index(op.f("ix_asset_groups_room_id"), "asset_groups", ["room_id"], unique=False)

    op.create_table(
        "asset_group_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("required_component", sa.String(length=50), nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=True),
        sa.Column("is_required", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["group_id"], ["asset_groups.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_asset_group_items_id"), "asset_group_items", ["id"], unique=False)
    op.create_index(op.f("ix_asset_group_items_required_component"), "asset_group_items", ["required_component"], unique=False)

    op.create_table(
        "scan_observations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("scan_session_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=True),
        sa.Column("epc", sa.String(length=128), nullable=False),
        sa.Column("read_count", sa.Integer(), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["scan_session_id"], ["scan_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scan_session_id", "epc", name="uq_scan_observations_session_epc"),
    )
    op.create_index(op.f("ix_scan_observations_id"), "scan_observations", ["id"], unique=False)
    op.create_index(op.f("ix_scan_observations_scan_session_id"), "scan_observations", ["scan_session_id"], unique=False)
    op.create_index(op.f("ix_scan_observations_epc"), "scan_observations", ["epc"], unique=False)

    op.create_table(
        "anomalies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("room_id", sa.Integer(), nullable=True),
        sa.Column("asset_id", sa.Integer(), nullable=True),
        sa.Column("group_id", sa.Integer(), nullable=True),
        sa.Column("consecutive_misses", sa.Integer(), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["group_id"], ["asset_groups.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_anomalies_id"), "anomalies", ["id"], unique=False)
    op.create_index(op.f("ix_anomalies_type"), "anomalies", ["type"], unique=False)
    op.create_index(op.f("ix_anomalies_status"), "anomalies", ["status"], unique=False)
    op.create_index(op.f("ix_anomalies_room_id"), "anomalies", ["room_id"], unique=False)
    op.create_index(op.f("ix_anomalies_first_seen_at"), "anomalies", ["first_seen_at"], unique=False)
    op.create_index(op.f("ix_anomalies_last_seen_at"), "anomalies", ["last_seen_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_anomalies_last_seen_at"), table_name="anomalies")
    op.drop_index(op.f("ix_anomalies_first_seen_at"), table_name="anomalies")
    op.drop_index(op.f("ix_anomalies_room_id"), table_name="anomalies")
    op.drop_index(op.f("ix_anomalies_status"), table_name="anomalies")
    op.drop_index(op.f("ix_anomalies_type"), table_name="anomalies")
    op.drop_index(op.f("ix_anomalies_id"), table_name="anomalies")
    op.drop_table("anomalies")

    op.drop_index(op.f("ix_scan_observations_epc"), table_name="scan_observations")
    op.drop_index(op.f("ix_scan_observations_scan_session_id"), table_name="scan_observations")
    op.drop_index(op.f("ix_scan_observations_id"), table_name="scan_observations")
    op.drop_table("scan_observations")

    op.drop_index(op.f("ix_asset_group_items_required_component"), table_name="asset_group_items")
    op.drop_index(op.f("ix_asset_group_items_id"), table_name="asset_group_items")
    op.drop_table("asset_group_items")

    op.drop_index(op.f("ix_asset_groups_room_id"), table_name="asset_groups")
    op.drop_index(op.f("ix_asset_groups_name"), table_name="asset_groups")
    op.drop_index(op.f("ix_asset_groups_id"), table_name="asset_groups")
    op.drop_table("asset_groups")

    op.drop_index(op.f("ix_scan_sessions_started_at"), table_name="scan_sessions")
    op.drop_index(op.f("ix_scan_sessions_room_id"), table_name="scan_sessions")
    op.drop_index(op.f("ix_scan_sessions_id"), table_name="scan_sessions")
    op.drop_table("scan_sessions")

    op.drop_index(op.f("ix_tags_epc"), table_name="tags")
    op.drop_index(op.f("ix_tags_id"), table_name="tags")
    op.drop_table("tags")

    with op.batch_alter_table("assets") as batch_op:
        batch_op.drop_constraint("fk_assets_room_id", type_="foreignkey")
        batch_op.drop_column("room_id")
        batch_op.drop_column("component_type")

    op.drop_index(op.f("ix_rooms_code"), table_name="rooms")
    op.drop_index(op.f("ix_rooms_name"), table_name="rooms")
    op.drop_index(op.f("ix_rooms_id"), table_name="rooms")
    op.drop_table("rooms")
