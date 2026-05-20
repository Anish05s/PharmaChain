"""add shipment quantity_dispatched

Revision ID: a1b2c3d4e5f6
Revises: 716abecbce6c
Create Date: 2026-05-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "716abecbce6c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "shipments",
        sa.Column("quantity_dispatched", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("shipments", "quantity_dispatched")
