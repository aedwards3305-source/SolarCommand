"""Initial schema — all tables for SolarCommand MVP.

Revision ID: 001_initial
Revises: None
Create Date: 2025-02-06
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Enums ──
    property_type = postgresql.ENUM(
        "SFH", "TOWNHOME", "CONDO", "MULTI_FAMILY", "OTHER",
        name="propertytype", create_type=False,
    )
    lead_status = postgresql.ENUM(
        "ingested", "scored", "hot", "warm", "cool", "contacting", "contacted",
        "qualified", "appointment_set", "nurturing", "closed_won", "closed_lost",
        "disqualified", "dnc", "archived",
        name="leadstatus", create_type=False,
    )
    contact_channel = postgresql.ENUM(
        "voice", "sms", "email",
        name="contactchannel", create_type=False,
    )
    contact_disposition = postgresql.ENUM(
        "appointment_booked", "callback_scheduled", "interested_not_ready",
        "not_interested", "not_homeowner", "wrong_number", "voicemail",
        "no_answer", "do_not_call", "completed", "failed",
        name="contactdisposition", create_type=False,
    )
    consent_status = postgresql.ENUM(
        "opted_in", "opted_out", "pending", "revoked",
        name="consentstatus", create_type=False,
    )
    consent_type = postgresql.ENUM(
        "voice_call", "sms", "email", "all_channels",
        name="consenttype", create_type=False,
    )
    appointment_status = postgresql.ENUM(
        "scheduled", "confirmed", "completed", "no_show", "cancelled", "rescheduled",
        name="appointmentstatus", create_type=False,
    )
    user_role = postgresql.ENUM(
        "admin", "rep", "ops",
        name="userrole", create_type=False,
    )

    # Create all enum types
    for enum in [property_type, lead_status, contact_channel, contact_disposition,
                 consent_status, consent_type, appointment_status, user_role]:
        enum.create(op.get_bind(), checkfirst=True)

    # ── property ──
    op.create_table(
        "property",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("address_line1", sa.String(255), nullable=False),
        sa.Column("address_line2", sa.String(255)),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("state", sa.String(2), nullable=False, server_default="MD"),
        sa.Column("zip_code", sa.String(10), nullable=False),
        sa.Column("county", sa.String(100), nullable=False),
        sa.Column("parcel_id", sa.String(50), unique=True),
        sa.Column("property_type", property_type, server_default="SFH"),
        sa.Column("year_built", sa.Integer()),
        sa.Column("roof_area_sqft", sa.Float()),
        sa.Column("assessed_value", sa.Float()),
        sa.Column("lot_size_sqft", sa.Float()),
        sa.Column("utility_zone", sa.String(20)),
        sa.Column("tree_cover_pct", sa.Float()),
        sa.Column("neighborhood_solar_pct", sa.Float()),
        sa.Column("has_existing_solar", sa.Boolean(), server_default="false"),
        sa.Column("owner_first_name", sa.String(100)),
        sa.Column("owner_last_name", sa.String(100)),
        sa.Column("owner_occupied", sa.Boolean(), server_default="true"),
        sa.Column("owner_phone", sa.String(20)),
        sa.Column("owner_email", sa.String(255)),
        sa.Column("median_household_income", sa.Float()),
        sa.Column("data_source", sa.String(50)),
        sa.Column("raw_data", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_property_county", "property", ["county"])
    op.create_index("ix_property_zip", "property", ["zip_code"])
    op.create_index("ix_property_state", "property", ["state"])

    # ── rep_user ──
    op.create_table(
        "rep_user",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("phone", sa.String(20)),
        sa.Column("role", user_role, server_default="rep"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("api_key_hash", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── lead ──
    op.create_table(
        "lead",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("property_id", sa.Integer(), sa.ForeignKey("property.id"), unique=True, nullable=False),
        sa.Column("status", lead_status, nullable=False, server_default="ingested"),
        sa.Column("assigned_rep_id", sa.Integer(), sa.ForeignKey("rep_user.id")),
        sa.Column("first_name", sa.String(100)),
        sa.Column("last_name", sa.String(100)),
        sa.Column("phone", sa.String(20)),
        sa.Column("email", sa.String(255)),
        sa.Column("last_contacted_at", sa.DateTime(timezone=True)),
        sa.Column("total_call_attempts", sa.Integer(), server_default="0"),
        sa.Column("total_sms_sent", sa.Integer(), server_default="0"),
        sa.Column("total_emails_sent", sa.Integer(), server_default="0"),
        sa.Column("next_outreach_at", sa.DateTime(timezone=True)),
        sa.Column("next_outreach_channel", contact_channel),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_lead_status", "lead", ["status"])
    op.create_index("ix_lead_next_outreach", "lead", ["next_outreach_at"])
    op.create_index("ix_lead_assigned_rep", "lead", ["assigned_rep_id"])

    # ── lead_score ──
    op.create_table(
        "lead_score",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("lead_id", sa.Integer(), sa.ForeignKey("lead.id"), nullable=False),
        sa.Column("total_score", sa.Integer(), nullable=False),
        sa.Column("score_version", sa.String(10), nullable=False, server_default="v1"),
        sa.Column("roof_age_score", sa.Integer(), server_default="0"),
        sa.Column("ownership_score", sa.Integer(), server_default="0"),
        sa.Column("roof_area_score", sa.Integer(), server_default="0"),
        sa.Column("home_value_score", sa.Integer(), server_default="0"),
        sa.Column("utility_rate_score", sa.Integer(), server_default="0"),
        sa.Column("shade_score", sa.Integer(), server_default="0"),
        sa.Column("neighborhood_score", sa.Integer(), server_default="0"),
        sa.Column("income_score", sa.Integer(), server_default="0"),
        sa.Column("property_type_score", sa.Integer(), server_default="0"),
        sa.Column("existing_solar_score", sa.Integer(), server_default="0"),
        sa.Column("scored_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_lead_score_lead_id", "lead_score", ["lead_id"])
    op.create_index("ix_lead_score_total", "lead_score", ["total_score"])

    # ── script_version ──
    op.create_table(
        "script_version",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("version_label", sa.String(20), nullable=False),
        sa.Column("channel", contact_channel, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="false"),
        sa.Column("created_by", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_script_channel_active", "script_version", ["channel", "is_active"])

    # ── outreach_attempt ──
    op.create_table(
        "outreach_attempt",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("lead_id", sa.Integer(), sa.ForeignKey("lead.id"), nullable=False),
        sa.Column("channel", contact_channel, nullable=False),
        sa.Column("disposition", contact_disposition),
        sa.Column("script_version_id", sa.Integer(), sa.ForeignKey("script_version.id")),
        sa.Column("external_call_id", sa.String(100)),
        sa.Column("duration_seconds", sa.Integer()),
        sa.Column("recording_url", sa.String(500)),
        sa.Column("transcript", sa.Text()),
        sa.Column("message_body", sa.Text()),
        sa.Column("template_id", sa.String(50)),
        sa.Column("qualified", sa.Boolean()),
        sa.Column("qualification_data", postgresql.JSONB()),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_outreach_lead_id", "outreach_attempt", ["lead_id"])
    op.create_index("ix_outreach_channel", "outreach_attempt", ["channel"])
    op.create_index("ix_outreach_started_at", "outreach_attempt", ["started_at"])

    # ── consent_log ──
    op.create_table(
        "consent_log",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("lead_id", sa.Integer(), sa.ForeignKey("lead.id"), nullable=False),
        sa.Column("consent_type", consent_type, nullable=False),
        sa.Column("status", consent_status, nullable=False),
        sa.Column("channel", contact_channel, nullable=False),
        sa.Column("evidence_type", sa.String(50)),
        sa.Column("evidence_url", sa.String(500)),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("user_agent", sa.String(500)),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_consent_lead_id", "consent_log", ["lead_id"])
    op.create_index("ix_consent_status", "consent_log", ["status"])

    # ── appointment ──
    op.create_table(
        "appointment",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("lead_id", sa.Integer(), sa.ForeignKey("lead.id"), nullable=False),
        sa.Column("rep_id", sa.Integer(), sa.ForeignKey("rep_user.id"), nullable=False),
        sa.Column("status", appointment_status, server_default="scheduled"),
        sa.Column("scheduled_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scheduled_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("address", sa.String(500)),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_appointment_rep_id", "appointment", ["rep_id"])
    op.create_index("ix_appointment_scheduled", "appointment", ["scheduled_start"])
    op.create_index("ix_appointment_status", "appointment", ["status"])

    # ── audit_log ──
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("actor", sa.String(100), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.Integer()),
        sa.Column("old_value", sa.Text()),
        sa.Column("new_value", sa.Text()),
        sa.Column("metadata_json", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_entity", "audit_log", ["entity_type", "entity_id"])
    op.create_index("ix_audit_created_at", "audit_log", ["created_at"])
    op.create_index("ix_audit_actor", "audit_log", ["actor"])

    # ── note ──
    op.create_table(
        "note",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("lead_id", sa.Integer(), sa.ForeignKey("lead.id"), nullable=False),
        sa.Column("author", sa.String(100), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_note_lead_id", "note", ["lead_id"])


def downgrade() -> None:
    op.drop_table("note")
    op.drop_table("audit_log")
    op.drop_table("appointment")
    op.drop_table("consent_log")
    op.drop_table("outreach_attempt")
    op.drop_table("script_version")
    op.drop_table("lead_score")
    op.drop_table("lead")
    op.drop_table("rep_user")
    op.drop_table("property")

    # Drop enums
    for name in ["userrole", "appointmentstatus", "consenttype", "consentstatus",
                 "contactdisposition", "contactchannel", "leadstatus", "propertytype"]:
        op.execute(f"DROP TYPE IF EXISTS {name}")
