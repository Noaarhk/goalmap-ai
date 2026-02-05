"""Add progress and completion_criteria to nodes

Revision ID: a1b2c3d4e5f6
Revises: f3d8acd0bc5c
Create Date: 2026-02-05 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "9d8e7f6a5b4c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("nodes", sa.Column("progress", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("nodes", sa.Column("completion_criteria", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("nodes", "completion_criteria")
    op.drop_column("nodes", "progress")
