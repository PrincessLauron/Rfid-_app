"""add mr assignees and workflow support

Revision ID: d4e6a1c9b2f0
Revises: c2a1d9f3b7ee
Create Date: 2026-02-28 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e6a1c9b2f0"
down_revision: Union[str, Sequence[str], None] = "c2a1d9f3b7ee"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "mr_assignees",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("initials", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_mr_assignees_id"), "mr_assignees", ["id"], unique=False)
    op.create_index(op.f("ix_mr_assignees_name"), "mr_assignees", ["name"], unique=True)

    with op.batch_alter_table("memorandum_receipts") as batch_op:
        batch_op.add_column(sa.Column("assignee_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_memorandum_receipts_assignee_id",
            "mr_assignees",
            ["assignee_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    with op.batch_alter_table("memorandum_receipts") as batch_op:
        batch_op.drop_constraint("fk_memorandum_receipts_assignee_id", type_="foreignkey")
        batch_op.drop_column("assignee_id")

    op.drop_index(op.f("ix_mr_assignees_name"), table_name="mr_assignees")
    op.drop_index(op.f("ix_mr_assignees_id"), table_name="mr_assignees")
    op.drop_table("mr_assignees")
