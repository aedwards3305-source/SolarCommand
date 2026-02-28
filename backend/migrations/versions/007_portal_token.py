"""Add portal_token column to lead table for customer portal URLs.

Revision ID: 007_portal_token
Revises: 006_add_lat_lon
Create Date: 2026-02-27
"""

from alembic import op

revision = "007_portal_token"
down_revision = "006_add_lat_lon"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE lead
        ADD COLUMN IF NOT EXISTS portal_token VARCHAR(20);
    """)
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_lead_portal_token "
        "ON lead(portal_token) WHERE portal_token IS NOT NULL;"
    )
    # Backfill existing leads with random tokens
    op.execute("""
        UPDATE lead
        SET portal_token = substr(md5(random()::text || id::text), 1, 12)
        WHERE portal_token IS NULL;
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_lead_portal_token;")
    op.execute("ALTER TABLE lead DROP COLUMN IF EXISTS portal_token;")
