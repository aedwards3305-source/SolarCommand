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
    sfh = "SFH"
    townhome = "TOWNHOME"
    condo = "CONDO"
    multi_family = "MULTI_FAMILY"
    other = "OTHER"


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
        Enum(PropertyType), default=PropertyType.sfh
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

    # API key hash for MVP auth
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
