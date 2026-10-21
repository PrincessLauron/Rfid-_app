"""add memorandum receipts

Revision ID: c2a1d9f3b7ee
Revises: 9f12d3b4c5d6
Create Date: 2026-02-28 15:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c2a1d9f3b7ee"
down_revision: Union[str, Sequence[str], None] = "9f12d3b4c5d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "memorandum_receipts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("reference_no", sa.String(length=120), nullable=False),
        sa.Column("issued_to", sa.String(length=160), nullable=False),
        sa.Column("issued_by", sa.String(length=160), nullable=True),
        sa.Column("issued_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("room_id", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("reference_no"),
    )
    op.create_index(op.f("ix_memorandum_receipts_id"), "memorandum_receipts", ["id"], unique=False)
    op.create_index(op.f("ix_memorandum_receipts_reference_no"), "memorandum_receipts", ["reference_no"], unique=True)
    op.create_index(op.f("ix_memorandum_receipts_issued_at"), "memorandum_receipts", ["issued_at"], unique=False)
    op.create_index(op.f("ix_memorandum_receipts_status"), "memorandum_receipts", ["status"], unique=False)

    op.create_table(
        "memorandum_receipt_assets",
        sa.Column("memorandum_receipt_id", sa.Integer(), nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["memorandum_receipt_id"], ["memorandum_receipts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("memorandum_receipt_id", "asset_id"),
    )


def downgrade() -> None:
    op.drop_table("memorandum_receipt_assets")
    op.drop_index(op.f("ix_memorandum_receipts_status"), table_name="memorandum_receipts")
    op.drop_index(op.f("ix_memorandum_receipts_issued_at"), table_name="memorandum_receipts")
    op.drop_index(op.f("ix_memorandum_receipts_reference_no"), table_name="memorandum_receipts")
    op.drop_index(op.f("ix_memorandum_receipts_id"), table_name="memorandum_receipts")
    op.drop_table("memorandum_receipts")
