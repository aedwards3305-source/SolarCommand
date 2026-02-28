"""Add AI Operator tables: ai_run, ai_memory.

Revision ID: 004_ai_operator
Revises: 003_ai_modules
Create Date: 2026-02-06
"""

from alembic import op

revision = "004_ai_operator"
down_revision = "003_ai_modules"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS ai_run (
            id SERIAL PRIMARY KEY,
            task_type VARCHAR(50) NOT NULL,
            lead_id INTEGER REFERENCES lead(id),
            conversation_id INTEGER REFERENCES conversation_transcript(id),
            model VARCHAR(100) NOT NULL,
            temperature FLOAT DEFAULT 0.2,
            prompt_version VARCHAR(20) DEFAULT 'v1',
            input_json JSONB,
            output_json JSONB,
            tokens_in INTEGER,
            tokens_out INTEGER,
            cost_usd FLOAT,
            latency_ms INTEGER,
            status VARCHAR(20) DEFAULT 'pending',
            error TEXT,
            created_at TIMESTAMPTZ DEFAULT now()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_ai_run_task_type ON ai_run(task_type);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_ai_run_lead_id ON ai_run(lead_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_ai_run_created_at ON ai_run(created_at);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_ai_run_status ON ai_run(status);")

    op.execute("""
        CREATE TABLE IF NOT EXISTS ai_memory (
            id SERIAL PRIMARY KEY,
            scope VARCHAR(50) NOT NULL,
            key VARCHAR(200) NOT NULL,
            content TEXT NOT NULL,
            meta_json JSONB,
            updated_at TIMESTAMPTZ DEFAULT now(),
            created_at TIMESTAMPTZ DEFAULT now()
        );
    """)
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_ai_memory_scope_key ON ai_memory(scope, key);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_ai_memory_scope ON ai_memory(scope);")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ai_memory;")
    op.execute("DROP TABLE IF EXISTS ai_run;")
