"""Add password_hash column to rep_user.

Revision ID: 002_password_hash
Revises: 001_initial
Create Date: 2025-02-06
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_password_hash"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("rep_user", sa.Column("password_hash", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("rep_user", "password_hash")
