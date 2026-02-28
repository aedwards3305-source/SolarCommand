"""Add voice provider fields and enrichment tables.

Revision ID: 005_voice_enrichment
Revises: 004_ai_operator
Create Date: 2026-02-06
"""

from alembic import op

revision = "005_voice_enrichment"
down_revision = "004_ai_operator"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Voice fields on conversation_transcript ────────────────────────
    op.execute("""
        ALTER TABLE conversation_transcript
        ADD COLUMN IF NOT EXISTS provider VARCHAR(20),
        ADD COLUMN IF NOT EXISTS call_sid VARCHAR(100),
        ADD COLUMN IF NOT EXISTS recording_url VARCHAR(500),
        ADD COLUMN IF NOT EXISTS call_status VARCHAR(30);
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_transcript_call_sid "
        "ON conversation_transcript(call_sid);"
    )

    # ── Contact Enrichment ─────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS contact_enrichment (
            id SERIAL PRIMARY KEY,
            lead_id INTEGER NOT NULL REFERENCES lead(id),
            provider VARCHAR(50) NOT NULL,
            full_name VARCHAR(200),
            emails JSONB,
            phones JSONB,
            job_title VARCHAR(200),
            linkedin_url VARCHAR(500),
            confidence FLOAT DEFAULT 0.0,
            raw_response JSONB,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        );
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_enrichment_lead_id "
        "ON contact_enrichment(lead_id);"
    )

    # ── Contact Validation ─────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS contact_validation (
            id SERIAL PRIMARY KEY,
            lead_id INTEGER NOT NULL REFERENCES lead(id),
            provider VARCHAR(50) NOT NULL,
            phone_valid BOOLEAN,
            phone_type VARCHAR(20),
            phone_carrier VARCHAR(100),
            phone_line_status VARCHAR(30),
            email_valid BOOLEAN,
            email_deliverable BOOLEAN,
            email_disposable BOOLEAN,
            address_valid BOOLEAN,
            address_deliverable BOOLEAN,
            confidence FLOAT DEFAULT 0.0,
            raw_response JSONB,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        );
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_validation_lead_id "
        "ON contact_validation(lead_id);"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS contact_validation;")
    op.execute("DROP TABLE IF EXISTS contact_enrichment;")
    op.execute("""
        ALTER TABLE conversation_transcript
        DROP COLUMN IF EXISTS provider,
        DROP COLUMN IF EXISTS call_sid,
        DROP COLUMN IF EXISTS recording_url,
        DROP COLUMN IF EXISTS call_status;
    """)
