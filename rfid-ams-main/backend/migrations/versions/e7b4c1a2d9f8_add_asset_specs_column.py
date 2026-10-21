"""add asset specs column

Revision ID: e7b4c1a2d9f8
Revises: d4e6a1c9b2f0
Create Date: 2026-02-28 17:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e7b4c1a2d9f8"
down_revision: Union[str, Sequence[str], None] = "d4e6a1c9b2f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("assets") as batch_op:
        batch_op.add_column(sa.Column("specs", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("assets") as batch_op:
        batch_op.drop_column("specs")
