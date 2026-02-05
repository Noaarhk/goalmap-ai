"""Add Status Enums for Node and Roadmap

Revision ID: 9d8e7f6a5b4c
Revises: f3d8acd0bc5c
Create Date: 2026-02-05 17:35:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9d8e7f6a5b4c"
down_revision: Union[str, Sequence[str], None] = "f3d8acd0bc5c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create Enums
    # Note: We must create the enum type in the database before using it
    node_status_enum = sa.Enum("pending", "in_progress", "completed", name="nodestatus")
    node_status_enum.create(op.get_bind())

    roadmap_status_enum = sa.Enum(
        "draft", "active", "completed", "archived", name="roadmapstatus"
    )
    roadmap_status_enum.create(op.get_bind())

    # 2. Convert Columns
    # Using raw SQL for the USING clause which is robust for Postgres Enum conversion
    op.execute(
        "ALTER TABLE nodes ALTER COLUMN status TYPE nodestatus USING status::nodestatus"
    )
    op.execute(
        "ALTER TABLE roadmaps ALTER COLUMN status TYPE roadmapstatus USING status::roadmapstatus"
    )


def downgrade() -> None:
    # 1. Revert Columns to String
    op.alter_column(
        "nodes",
        "status",
        existing_type=sa.Enum(name="nodestatus"),
        type_=sa.String(),
        postgresql_using="status::text",
    )

    op.alter_column(
        "roadmaps",
        "status",
        existing_type=sa.Enum(name="roadmapstatus"),
        type_=sa.String(),
        postgresql_using="status::text",
    )

    # 2. Drop Enums
    sa.Enum(name="nodestatus").drop(op.get_bind())
    sa.Enum(name="roadmapstatus").drop(op.get_bind())
