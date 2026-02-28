"""Add AI module tables: contact_intelligence, inbound_message,
conversation_transcript, qa_review, objection_tag, nba_decision,
script_experiment.

Revision ID: 003_ai_modules
Revises: 002_password_hash
Create Date: 2026-02-06
"""

from alembic import op

revision = "003_ai_modules"
down_revision = "002_password_hash"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use raw SQL to avoid SQLAlchemy enum auto-creation conflicts
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE messagedirection AS ENUM ('inbound', 'outbound');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE nbaaction AS ENUM ('call', 'sms', 'email', 'wait', 'rep_handoff', 'nurture', 'close');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # ── contact_intelligence ──
    op.execute("""
        CREATE TABLE IF NOT EXISTS contact_intelligence (
            id SERIAL PRIMARY KEY,
            lead_id INTEGER NOT NULL REFERENCES lead(id),
            phone_valid BOOLEAN,
            phone_type VARCHAR(20),
            carrier_name VARCHAR(100),
            email_valid BOOLEAN,
            email_deliverable BOOLEAN,
            best_call_hour INTEGER,
            best_sms_hour INTEGER,
            timezone VARCHAR(50) DEFAULT 'America/New_York',
            provider_payload JSONB,
            validated_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_ci_lead_id ON contact_intelligence(lead_id);")

    # ── inbound_message ──
    op.execute("""
        CREATE TABLE IF NOT EXISTS inbound_message (
            id SERIAL PRIMARY KEY,
            lead_id INTEGER NOT NULL REFERENCES lead(id),
            direction messagedirection NOT NULL,
            channel contactchannel NOT NULL,
            from_number VARCHAR(20),
            to_number VARCHAR(20),
            body TEXT NOT NULL,
            ai_intent VARCHAR(50),
            ai_suggested_reply TEXT,
            ai_actions JSONB,
            ai_model VARCHAR(50),
            external_id VARCHAR(100),
            provider_payload JSONB,
            sent_by VARCHAR(100),
            script_version_id INTEGER REFERENCES script_version(id),
            outreach_attempt_id INTEGER REFERENCES outreach_attempt(id),
            created_at TIMESTAMPTZ DEFAULT now()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_msg_lead_id ON inbound_message(lead_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_msg_created_at ON inbound_message(created_at);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_msg_direction ON inbound_message(direction);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_msg_from_number ON inbound_message(from_number);")

    # ── conversation_transcript ──
    op.execute("""
        CREATE TABLE IF NOT EXISTS conversation_transcript (
            id SERIAL PRIMARY KEY,
            lead_id INTEGER NOT NULL REFERENCES lead(id),
            channel contactchannel NOT NULL,
            outreach_attempt_id INTEGER REFERENCES outreach_attempt(id),
            raw_transcript TEXT NOT NULL,
            ai_summary TEXT,
            ai_sentiment VARCHAR(20),
            ai_output JSONB,
            ai_model VARCHAR(50),
            duration_seconds INTEGER,
            started_at TIMESTAMPTZ,
            ended_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT now()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_transcript_lead_id ON conversation_transcript(lead_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_transcript_created_at ON conversation_transcript(created_at);")

    # ── qa_review ──
    op.execute("""
        CREATE TABLE IF NOT EXISTS qa_review (
            id SERIAL PRIMARY KEY,
            lead_id INTEGER NOT NULL REFERENCES lead(id),
            conversation_id INTEGER REFERENCES conversation_transcript(id),
            compliance_score INTEGER NOT NULL,
            flags JSONB,
            checklist_pass BOOLEAN DEFAULT true,
            rationale TEXT,
            reviewed_by VARCHAR(100) DEFAULT 'ai_agent',
            ai_output JSONB,
            ai_model VARCHAR(50),
            created_at TIMESTAMPTZ DEFAULT now()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_qa_lead_id ON qa_review(lead_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_qa_compliance_score ON qa_review(compliance_score);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_qa_created_at ON qa_review(created_at);")

    # ── objection_tag ──
    op.execute("""
        CREATE TABLE IF NOT EXISTS objection_tag (
            id SERIAL PRIMARY KEY,
            conversation_id INTEGER NOT NULL REFERENCES conversation_transcript(id),
            lead_id INTEGER NOT NULL REFERENCES lead(id),
            tag VARCHAR(100) NOT NULL,
            confidence FLOAT DEFAULT 0.0,
            evidence_span TEXT,
            ai_output JSONB,
            created_at TIMESTAMPTZ DEFAULT now()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_objection_conversation_id ON objection_tag(conversation_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_objection_tag ON objection_tag(tag);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_objection_lead_id ON objection_tag(lead_id);")

    # ── nba_decision ──
    op.execute("""
        CREATE TABLE IF NOT EXISTS nba_decision (
            id SERIAL PRIMARY KEY,
            lead_id INTEGER NOT NULL REFERENCES lead(id),
            recommended_action nbaaction NOT NULL,
            recommended_channel contactchannel,
            schedule_time TIMESTAMPTZ,
            reason_codes JSONB,
            confidence FLOAT DEFAULT 0.0,
            ai_output JSONB,
            ai_model VARCHAR(50),
            expires_at TIMESTAMPTZ,
            applied BOOLEAN DEFAULT false,
            applied_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT now()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_nba_lead_id ON nba_decision(lead_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_nba_created_at ON nba_decision(created_at);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_nba_expires_at ON nba_decision(expires_at);")

    # ── script_experiment ──
    op.execute("""
        CREATE TABLE IF NOT EXISTS script_experiment (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            channel contactchannel NOT NULL,
            control_script_id INTEGER NOT NULL REFERENCES script_version(id),
            variant_script_id INTEGER NOT NULL REFERENCES script_version(id),
            control_sends INTEGER DEFAULT 0,
            variant_sends INTEGER DEFAULT 0,
            control_responses INTEGER DEFAULT 0,
            variant_responses INTEGER DEFAULT 0,
            control_conversions INTEGER DEFAULT 0,
            variant_conversions INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT true,
            started_at TIMESTAMPTZ DEFAULT now(),
            ended_at TIMESTAMPTZ
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_experiment_active ON script_experiment(is_active);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_experiment_channel ON script_experiment(channel);")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS script_experiment;")
    op.execute("DROP TABLE IF EXISTS nba_decision;")
    op.execute("DROP TABLE IF EXISTS objection_tag;")
    op.execute("DROP TABLE IF EXISTS qa_review;")
    op.execute("DROP TABLE IF EXISTS conversation_transcript;")
    op.execute("DROP TABLE IF EXISTS inbound_message;")
    op.execute("DROP TABLE IF EXISTS contact_intelligence;")
    op.execute("DROP TYPE IF EXISTS nbaaction;")
    op.execute("DROP TYPE IF EXISTS messagedirection;")
