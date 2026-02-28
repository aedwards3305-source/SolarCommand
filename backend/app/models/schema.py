"""SQLAlchemy ORM models for SolarCommand."""

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# ── Enums ──────────────────────────────────────────────────────────────────


class LeadStatus(str, enum.Enum):
    ingested = "ingested"
    scored = "scored"
    hot = "hot"
    warm = "warm"
    cool = "cool"
    contacting = "contacting"
    contacted = "contacted"
    qualified = "qualified"
    appointment_set = "appointment_set"
    nurturing = "nurturing"
    closed_won = "closed_won"
    closed_lost = "closed_lost"
    disqualified = "disqualified"
    dnc = "dnc"
    archived = "archived"


class ContactChannel(str, enum.Enum):
    voice = "voice"
    sms = "sms"
    email = "email"


class ContactDisposition(str, enum.Enum):
    appointment_booked = "appointment_booked"
    callback_scheduled = "callback_scheduled"
    interested_not_ready = "interested_not_ready"
    not_interested = "not_interested"
    not_homeowner = "not_homeowner"
    wrong_number = "wrong_number"
    voicemail = "voicemail"
    no_answer = "no_answer"
    do_not_call = "do_not_call"
    completed = "completed"
    failed = "failed"


class ConsentStatus(str, enum.Enum):
    opted_in = "opted_in"
    opted_out = "opted_out"
    pending = "pending"
    revoked = "revoked"


class ConsentType(str, enum.Enum):
    voice_call = "voice_call"
    sms = "sms"
    email = "email"
    all_channels = "all_channels"


class AppointmentStatus(str, enum.Enum):
    scheduled = "scheduled"
    confirmed = "confirmed"
    completed = "completed"
    no_show = "no_show"
    cancelled = "cancelled"
    rescheduled = "rescheduled"


class UserRole(str, enum.Enum):
    admin = "admin"
    rep = "rep"
    ops = "ops"


class PropertyType(str, enum.Enum):
    SFH = "SFH"
    TOWNHOME = "TOWNHOME"
    CONDO = "CONDO"
    MULTI_FAMILY = "MULTI_FAMILY"
    OTHER = "OTHER"


# ── Models ─────────────────────────────────────────────────────────────────


class Property(Base):
    __tablename__ = "property"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    address_line1: Mapped[str] = mapped_column(String(255), nullable=False)
    address_line2: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(2), nullable=False, default="MD")
    zip_code: Mapped[str] = mapped_column(String(10), nullable=False)
    county: Mapped[str] = mapped_column(String(100), nullable=False)
    parcel_id: Mapped[str | None] = mapped_column(String(50), unique=True)

    # Property details
    property_type: Mapped[PropertyType] = mapped_column(
        Enum(PropertyType), default=PropertyType.SFH
    )
    year_built: Mapped[int | None] = mapped_column(Integer)
    roof_area_sqft: Mapped[float | None] = mapped_column(Float)
    assessed_value: Mapped[float | None] = mapped_column(Float)
    lot_size_sqft: Mapped[float | None] = mapped_column(Float)

    # Solar factors
    utility_zone: Mapped[str | None] = mapped_column(String(20))
    tree_cover_pct: Mapped[float | None] = mapped_column(Float)
    neighborhood_solar_pct: Mapped[float | None] = mapped_column(Float)
    has_existing_solar: Mapped[bool] = mapped_column(Boolean, default=False)

    # Owner info (denormalized for MVP — separate homeowner table in v2)
    owner_first_name: Mapped[str | None] = mapped_column(String(100))
    owner_last_name: Mapped[str | None] = mapped_column(String(100))
    owner_occupied: Mapped[bool] = mapped_column(Boolean, default=True)
    owner_phone: Mapped[str | None] = mapped_column(String(20))
    owner_email: Mapped[str | None] = mapped_column(String(255))

    # Geolocation
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)

    # Census / demographics
    median_household_income: Mapped[float | None] = mapped_column(Float)

    # Meta
    data_source: Mapped[str | None] = mapped_column(String(50))
    raw_data: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    lead: Mapped["Lead | None"] = relationship(back_populates="property")

    __table_args__ = (
        Index("ix_property_county", "county"),
        Index("ix_property_zip", "zip_code"),
        Index("ix_property_state", "state"),
    )


class Lead(Base):
    __tablename__ = "lead"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    property_id: Mapped[int] = mapped_column(
        ForeignKey("property.id"), unique=True, nullable=False
    )
    status: Mapped[LeadStatus] = mapped_column(
        Enum(LeadStatus), default=LeadStatus.ingested, nullable=False
    )
    assigned_rep_id: Mapped[int | None] = mapped_column(ForeignKey("rep_user.id"))

    # Portal access token (unique URL slug for customer-facing portal)
    portal_token: Mapped[str | None] = mapped_column(String(20), unique=True, index=True)

    # Contact info (copied from property for quick access)
    first_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100))
    phone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(255))

    # Outreach tracking
    last_contacted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    total_call_attempts: Mapped[int] = mapped_column(Integer, default=0)
    total_sms_sent: Mapped[int] = mapped_column(Integer, default=0)
    total_emails_sent: Mapped[int] = mapped_column(Integer, default=0)
    next_outreach_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_outreach_channel: Mapped[ContactChannel | None] = mapped_column(
        Enum(ContactChannel)
    )

    # Meta
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    property: Mapped["Property"] = relationship(back_populates="lead")
    scores: Mapped[list["LeadScore"]] = relationship(
        back_populates="lead", order_by="desc(LeadScore.scored_at)"
    )
    outreach_attempts: Mapped[list["OutreachAttempt"]] = relationship(
        back_populates="lead"
    )
    consent_logs: Mapped[list["ConsentLog"]] = relationship(back_populates="lead")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="lead")
    notes: Mapped[list["Note"]] = relationship(back_populates="lead")
    assigned_rep: Mapped["RepUser | None"] = relationship(back_populates="assigned_leads")

    __table_args__ = (
        Index("ix_lead_status", "status"),
        Index("ix_lead_next_outreach", "next_outreach_at"),
        Index("ix_lead_assigned_rep", "assigned_rep_id"),
    )


class LeadScore(Base):
    __tablename__ = "lead_score"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("lead.id"), nullable=False)

    total_score: Mapped[int] = mapped_column(Integer, nullable=False)
    score_version: Mapped[str] = mapped_column(
        String(10), nullable=False, default="v1"
    )

    # Individual factor scores (for explainability)
    roof_age_score: Mapped[int] = mapped_column(Integer, default=0)
    ownership_score: Mapped[int] = mapped_column(Integer, default=0)
    roof_area_score: Mapped[int] = mapped_column(Integer, default=0)
    home_value_score: Mapped[int] = mapped_column(Integer, default=0)
    utility_rate_score: Mapped[int] = mapped_column(Integer, default=0)
    shade_score: Mapped[int] = mapped_column(Integer, default=0)
    neighborhood_score: Mapped[int] = mapped_column(Integer, default=0)
    income_score: Mapped[int] = mapped_column(Integer, default=0)
    property_type_score: Mapped[int] = mapped_column(Integer, default=0)
    existing_solar_score: Mapped[int] = mapped_column(Integer, default=0)

    scored_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    lead: Mapped["Lead"] = relationship(back_populates="scores")

    __table_args__ = (
        Index("ix_lead_score_lead_id", "lead_id"),
        Index("ix_lead_score_total", "total_score"),
    )


class OutreachAttempt(Base):
    __tablename__ = "outreach_attempt"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("lead.id"), nullable=False)
    channel: Mapped[ContactChannel] = mapped_column(
        Enum(ContactChannel), nullable=False
    )
    disposition: Mapped[ContactDisposition | None] = mapped_column(
        Enum(ContactDisposition)
    )
    script_version_id: Mapped[int | None] = mapped_column(
        ForeignKey("script_version.id")
    )

    # Call details
    external_call_id: Mapped[str | None] = mapped_column(String(100))
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    recording_url: Mapped[str | None] = mapped_column(String(500))
    transcript: Mapped[str | None] = mapped_column(Text)

    # SMS/Email details
    message_body: Mapped[str | None] = mapped_column(Text)
    template_id: Mapped[str | None] = mapped_column(String(50))

    # Result
    qualified: Mapped[bool | None] = mapped_column(Boolean)
    qualification_data: Mapped[dict | None] = mapped_column(JSONB)

    # Timing
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    lead: Mapped["Lead"] = relationship(back_populates="outreach_attempts")
    script_version: Mapped["ScriptVersion | None"] = relationship()

    __table_args__ = (
        Index("ix_outreach_lead_id", "lead_id"),
        Index("ix_outreach_channel", "channel"),
        Index("ix_outreach_started_at", "started_at"),
    )


class ConsentLog(Base):
    __tablename__ = "consent_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("lead.id"), nullable=False)
    consent_type: Mapped[ConsentType] = mapped_column(
        Enum(ConsentType), nullable=False
    )
    status: Mapped[ConsentStatus] = mapped_column(
        Enum(ConsentStatus), nullable=False
    )
    channel: Mapped[ContactChannel] = mapped_column(
        Enum(ContactChannel), nullable=False
    )

    # Evidence
    evidence_type: Mapped[str | None] = mapped_column(
        String(50)
    )  # "verbal", "sms_reply", "web_form", "written"
    evidence_url: Mapped[str | None] = mapped_column(
        String(500)
    )  # recording URL, screenshot, etc.
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(500))

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    lead: Mapped["Lead"] = relationship(back_populates="consent_logs")

    __table_args__ = (
        Index("ix_consent_lead_id", "lead_id"),
        Index("ix_consent_status", "status"),
    )


class Appointment(Base):
    __tablename__ = "appointment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("lead.id"), nullable=False)
    rep_id: Mapped[int] = mapped_column(ForeignKey("rep_user.id"), nullable=False)
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus), default=AppointmentStatus.scheduled
    )

    scheduled_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    scheduled_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    address: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    lead: Mapped["Lead"] = relationship(back_populates="appointments")
    rep: Mapped["RepUser"] = relationship(back_populates="appointments")

    __table_args__ = (
        Index("ix_appointment_rep_id", "rep_id"),
        Index("ix_appointment_scheduled", "scheduled_start"),
        Index("ix_appointment_status", "status"),
    )


class RepUser(Base):
    __tablename__ = "rep_user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.rep)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Auth
    password_hash: Mapped[str | None] = mapped_column(String(255))
    api_key_hash: Mapped[str | None] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="rep")
    assigned_leads: Mapped[list["Lead"]] = relationship(back_populates="assigned_rep")


class ScriptVersion(Base):
    __tablename__ = "script_version"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version_label: Mapped[str] = mapped_column(String(20), nullable=False)
    channel: Mapped[ContactChannel] = mapped_column(
        Enum(ContactChannel), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[str | None] = mapped_column(String(100))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (Index("ix_script_channel_active", "channel", "is_active"),)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # "system", "ai_agent", user email
    action: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # "lead.status_change", "outreach.call", etc.
    entity_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # "lead", "property", "appointment"
    entity_id: Mapped[int | None] = mapped_column(Integer)
    old_value: Mapped[str | None] = mapped_column(Text)
    new_value: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("ix_audit_entity", "entity_type", "entity_id"),
        Index("ix_audit_created_at", "created_at"),
        Index("ix_audit_actor", "actor"),
    )


class Note(Base):
    __tablename__ = "note"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("lead.id"), nullable=False)
    author: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    lead: Mapped["Lead"] = relationship(back_populates="notes")

    __table_args__ = (Index("ix_note_lead_id", "lead_id"),)


# ── AI Module Enums ───────────────────────────────────────────────────────


class MessageDirection(str, enum.Enum):
    inbound = "inbound"
    outbound = "outbound"


class QAFlagSeverity(str, enum.Enum):
    info = "info"
    warning = "warning"
    critical = "critical"


class NBAAction(str, enum.Enum):
    call = "call"
    sms = "sms"
    email = "email"
    wait = "wait"
    rep_handoff = "rep_handoff"
    nurture = "nurture"
    close = "close"


class VoiceProviderEnum(str, enum.Enum):
    twilio = "twilio"
    vapi = "vapi"
    retell = "retell"


# ── AI Module Models ──────────────────────────────────────────────────────


class ContactIntelligence(Base):
    """Phone/email validation results and best contact time."""
    __tablename__ = "contact_intelligence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("lead.id"), nullable=False)

    # Phone validation
    phone_valid: Mapped[bool | None] = mapped_column(Boolean)
    phone_type: Mapped[str | None] = mapped_column(String(20))  # mobile, landline, voip
    carrier_name: Mapped[str | None] = mapped_column(String(100))

    # Email validation
    email_valid: Mapped[bool | None] = mapped_column(Boolean)
    email_deliverable: Mapped[bool | None] = mapped_column(Boolean)

    # Best contact time (learned from response patterns)
    best_call_hour: Mapped[int | None] = mapped_column(Integer)  # 0-23 ET
    best_sms_hour: Mapped[int | None] = mapped_column(Integer)
    timezone: Mapped[str] = mapped_column(String(50), default="America/New_York")

    # Provider raw response
    provider_payload: Mapped[dict | None] = mapped_column(JSONB)

    validated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    lead: Mapped["Lead"] = relationship()

    __table_args__ = (
        Index("ix_ci_lead_id", "lead_id"),
    )


class InboundMessage(Base):
    """SMS inbound/outbound message tracking with threading."""
    __tablename__ = "inbound_message"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("lead.id"), nullable=False)

    direction: Mapped[MessageDirection] = mapped_column(
        Enum(MessageDirection), nullable=False
    )
    channel: Mapped[ContactChannel] = mapped_column(
        Enum(ContactChannel), nullable=False, default=ContactChannel.sms
    )
    from_number: Mapped[str | None] = mapped_column(String(20))
    to_number: Mapped[str | None] = mapped_column(String(20))
    body: Mapped[str] = mapped_column(Text, nullable=False)

    # AI classification
    ai_intent: Mapped[str | None] = mapped_column(String(50))  # opt_out, interested, question, etc.
    ai_suggested_reply: Mapped[str | None] = mapped_column(Text)
    ai_actions: Mapped[dict | None] = mapped_column(JSONB)  # [{"action": "...", "params": {...}}]
    ai_model: Mapped[str | None] = mapped_column(String(50))

    # Twilio / provider fields
    external_id: Mapped[str | None] = mapped_column(String(100))
    provider_payload: Mapped[dict | None] = mapped_column(JSONB)

    # Tracking
    sent_by: Mapped[str | None] = mapped_column(String(100))  # "ai_agent", "rep:email", "system"
    script_version_id: Mapped[int | None] = mapped_column(ForeignKey("script_version.id"))
    outreach_attempt_id: Mapped[int | None] = mapped_column(ForeignKey("outreach_attempt.id"))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    lead: Mapped["Lead"] = relationship()

    __table_args__ = (
        Index("ix_msg_lead_id", "lead_id"),
        Index("ix_msg_created_at", "created_at"),
        Index("ix_msg_direction", "direction"),
        Index("ix_msg_from_number", "from_number"),
    )


class ConversationTranscript(Base):
    """Call/SMS transcript storage with AI-generated summary."""
    __tablename__ = "conversation_transcript"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("lead.id"), nullable=False)
    channel: Mapped[ContactChannel] = mapped_column(Enum(ContactChannel), nullable=False)
    outreach_attempt_id: Mapped[int | None] = mapped_column(ForeignKey("outreach_attempt.id"))

    raw_transcript: Mapped[str] = mapped_column(Text, nullable=False)
    ai_summary: Mapped[str | None] = mapped_column(Text)
    ai_sentiment: Mapped[str | None] = mapped_column(String(20))  # positive, neutral, negative
    ai_output: Mapped[dict | None] = mapped_column(JSONB)
    ai_model: Mapped[str | None] = mapped_column(String(50))

    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Voice provider fields
    provider: Mapped[str | None] = mapped_column(String(20))  # twilio, vapi, retell
    call_sid: Mapped[str | None] = mapped_column(String(100))
    recording_url: Mapped[str | None] = mapped_column(String(500))
    call_status: Mapped[str | None] = mapped_column(String(30))  # queued, ringing, in-progress, completed, failed

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    lead: Mapped["Lead"] = relationship()

    __table_args__ = (
        Index("ix_transcript_lead_id", "lead_id"),
        Index("ix_transcript_created_at", "created_at"),
        Index("ix_transcript_call_sid", "call_sid"),
    )


class QAReview(Base):
    """Compliance QA review for conversations."""
    __tablename__ = "qa_review"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("lead.id"), nullable=False)
    conversation_id: Mapped[int | None] = mapped_column(
        ForeignKey("conversation_transcript.id")
    )

    compliance_score: Mapped[int] = mapped_column(Integer, nullable=False)  # 0-100
    flags: Mapped[dict | None] = mapped_column(JSONB)  # [{"flag": "...", "severity": "..."}]
    checklist_pass: Mapped[bool] = mapped_column(Boolean, default=True)
    rationale: Mapped[str | None] = mapped_column(Text)

    reviewed_by: Mapped[str] = mapped_column(String(100), default="ai_agent")
    ai_output: Mapped[dict | None] = mapped_column(JSONB)
    ai_model: Mapped[str | None] = mapped_column(String(50))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    lead: Mapped["Lead"] = relationship()
    conversation: Mapped["ConversationTranscript | None"] = relationship()

    __table_args__ = (
        Index("ix_qa_lead_id", "lead_id"),
        Index("ix_qa_compliance_score", "compliance_score"),
        Index("ix_qa_created_at", "created_at"),
    )


class ObjectionTag(Base):
    """Objections extracted from conversations."""
    __tablename__ = "objection_tag"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversation_transcript.id"), nullable=False
    )
    lead_id: Mapped[int] = mapped_column(ForeignKey("lead.id"), nullable=False)

    tag: Mapped[str] = mapped_column(String(100), nullable=False)  # "too_expensive", "roof_condition"
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    evidence_span: Mapped[str | None] = mapped_column(Text)  # quoted text from transcript
    ai_output: Mapped[dict | None] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    conversation: Mapped["ConversationTranscript"] = relationship()

    __table_args__ = (
        Index("ix_objection_conversation_id", "conversation_id"),
        Index("ix_objection_tag", "tag"),
        Index("ix_objection_lead_id", "lead_id"),
    )


class NBADecision(Base):
    """Next-Best-Action recommendation for a lead."""
    __tablename__ = "nba_decision"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("lead.id"), nullable=False)

    recommended_action: Mapped[NBAAction] = mapped_column(
        Enum(NBAAction), nullable=False
    )
    recommended_channel: Mapped[ContactChannel | None] = mapped_column(
        Enum(ContactChannel)
    )
    schedule_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reason_codes: Mapped[dict | None] = mapped_column(JSONB)  # ["high_score", "best_call_time"]
    confidence: Mapped[float] = mapped_column(Float, default=0.0)

    ai_output: Mapped[dict | None] = mapped_column(JSONB)
    ai_model: Mapped[str | None] = mapped_column(String(50))

    # TTL: this decision is valid until...
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    applied: Mapped[bool] = mapped_column(Boolean, default=False)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    lead: Mapped["Lead"] = relationship()

    __table_args__ = (
        Index("ix_nba_lead_id", "lead_id"),
        Index("ix_nba_created_at", "created_at"),
        Index("ix_nba_expires_at", "expires_at"),
    )


class ScriptExperiment(Base):
    """A/B experiment tracking for script versions."""
    __tablename__ = "script_experiment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    channel: Mapped[ContactChannel] = mapped_column(Enum(ContactChannel), nullable=False)
    control_script_id: Mapped[int] = mapped_column(
        ForeignKey("script_version.id"), nullable=False
    )
    variant_script_id: Mapped[int] = mapped_column(
        ForeignKey("script_version.id"), nullable=False
    )

    # Metrics
    control_sends: Mapped[int] = mapped_column(Integer, default=0)
    variant_sends: Mapped[int] = mapped_column(Integer, default=0)
    control_responses: Mapped[int] = mapped_column(Integer, default=0)
    variant_responses: Mapped[int] = mapped_column(Integer, default=0)
    control_conversions: Mapped[int] = mapped_column(Integer, default=0)
    variant_conversions: Mapped[int] = mapped_column(Integer, default=0)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    control_script: Mapped["ScriptVersion"] = relationship(foreign_keys=[control_script_id])
    variant_script: Mapped["ScriptVersion"] = relationship(foreign_keys=[variant_script_id])

    __table_args__ = (
        Index("ix_experiment_active", "is_active"),
        Index("ix_experiment_channel", "channel"),
    )


# ── AI Operator Models ──────────────────────────────────────────────────


class AIRun(Base):
    """Audit trail for every AI API call — reproducibility + cost tracking."""
    __tablename__ = "ai_run"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)  # nba, qa, objection_tags, rep_brief, etc.
    lead_id: Mapped[int | None] = mapped_column(ForeignKey("lead.id"))
    conversation_id: Mapped[int | None] = mapped_column(ForeignKey("conversation_transcript.id"))

    # Model config (for reproducibility)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    temperature: Mapped[float] = mapped_column(Float, default=0.2)
    prompt_version: Mapped[str] = mapped_column(String(20), default="v1")

    # Input/output (full audit)
    input_json: Mapped[dict | None] = mapped_column(JSONB)
    output_json: Mapped[dict | None] = mapped_column(JSONB)

    # Cost + performance
    tokens_in: Mapped[int | None] = mapped_column(Integer)
    tokens_out: Mapped[int | None] = mapped_column(Integer)
    cost_usd: Mapped[float | None] = mapped_column(Float)
    latency_ms: Mapped[int | None] = mapped_column(Integer)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, success, error
    error: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("ix_ai_run_task_type", "task_type"),
        Index("ix_ai_run_lead_id", "lead_id"),
        Index("ix_ai_run_created_at", "created_at"),
        Index("ix_ai_run_status", "status"),
    )


class AIMemory(Base):
    """Durable learning store — lessons, patterns, summaries for RAG retrieval."""
    __tablename__ = "ai_memory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scope: Mapped[str] = mapped_column(String(50), nullable=False)  # global, county, utility, script, rep
    key: Mapped[str] = mapped_column(String(200), nullable=False)  # e.g. "top_objections", "best_call_hours"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    meta_json: Mapped[dict | None] = mapped_column(JSONB)  # Additional structured data

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("ix_ai_memory_scope_key", "scope", "key", unique=True),
        Index("ix_ai_memory_scope", "scope"),
    )


# ── Enrichment Models ─────────────────────────────────────────────────


class ContactEnrichment(Base):
    """Third-party enrichment data (People Data Labs, etc.)."""
    __tablename__ = "contact_enrichment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("lead.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # pdl, clearbit, etc.

    full_name: Mapped[str | None] = mapped_column(String(200))
    emails: Mapped[dict | None] = mapped_column(JSONB)  # [{"email": "...", "type": "..."}]
    phones: Mapped[dict | None] = mapped_column(JSONB)  # [{"number": "...", "type": "..."}]
    job_title: Mapped[str | None] = mapped_column(String(200))
    linkedin_url: Mapped[str | None] = mapped_column(String(500))
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    raw_response: Mapped[dict | None] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    lead: Mapped["Lead"] = relationship()

    __table_args__ = (
        Index("ix_enrichment_lead_id", "lead_id"),
    )


class ContactValidation(Base):
    """Contact validation results (Melissa, etc.)."""
    __tablename__ = "contact_validation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("lead.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # melissa, twilio_lookup

    # Phone validation
    phone_valid: Mapped[bool | None] = mapped_column(Boolean)
    phone_type: Mapped[str | None] = mapped_column(String(20))
    phone_carrier: Mapped[str | None] = mapped_column(String(100))
    phone_line_status: Mapped[str | None] = mapped_column(String(30))

    # Email validation
    email_valid: Mapped[bool | None] = mapped_column(Boolean)
    email_deliverable: Mapped[bool | None] = mapped_column(Boolean)
    email_disposable: Mapped[bool | None] = mapped_column(Boolean)

    # Address validation
    address_valid: Mapped[bool | None] = mapped_column(Boolean)
    address_deliverable: Mapped[bool | None] = mapped_column(Boolean)

    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    raw_response: Mapped[dict | None] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    lead: Mapped["Lead"] = relationship()

    __table_args__ = (
        Index("ix_validation_lead_id", "lead_id"),
    )
