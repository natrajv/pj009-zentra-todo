"""add per-user grid width preferences

Revision ID: a21c6d19b404
Revises: 9bb7279eda37
"""

import sqlalchemy as sa
from alembic import op

revision = "a21c6d19b404"
down_revision = "9bb7279eda37"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("user_preferences") as batch_op:
        batch_op.add_column(
            sa.Column("grid_widths", sa.JSON(), nullable=False, server_default="{}")
        )


def downgrade():
    with op.batch_alter_table("user_preferences") as batch_op:
        batch_op.drop_column("grid_widths")
