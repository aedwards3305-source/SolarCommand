"""Add latitude/longitude to property table.

Revision ID: 006_add_lat_lon
Revises: 005_voice_enrichment
Create Date: 2026-02-07
"""

from alembic import op

revision = "006_add_lat_lon"
down_revision = "005_voice_enrichment"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE property
        ADD COLUMN IF NOT EXISTS latitude DOUBLE PRECISION,
        ADD COLUMN IF NOT EXISTS longitude DOUBLE PRECISION;
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_property_lat_lon "
        "ON property(latitude, longitude) WHERE latitude IS NOT NULL;"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_property_lat_lon;")
    op.execute("""
        ALTER TABLE property
        DROP COLUMN IF EXISTS latitude,
        DROP COLUMN IF EXISTS longitude;
    """)
