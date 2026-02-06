-- ============================================================================
-- SolarCommand Database Schema (Deliverable C)
-- PostgreSQL 16
-- ============================================================================

-- ── Enums ──────────────────────────────────────────────────────────────────

CREATE TYPE propertytype AS ENUM ('SFH', 'TOWNHOME', 'CONDO', 'MULTI_FAMILY', 'OTHER');

CREATE TYPE leadstatus AS ENUM (
    'ingested', 'scored', 'hot', 'warm', 'cool',
    'contacting', 'contacted', 'qualified', 'appointment_set',
    'nurturing', 'closed_won', 'closed_lost', 'disqualified', 'dnc', 'archived'
);

CREATE TYPE contactchannel AS ENUM ('voice', 'sms', 'email');

CREATE TYPE contactdisposition AS ENUM (
    'appointment_booked', 'callback_scheduled', 'interested_not_ready',
    'not_interested', 'not_homeowner', 'wrong_number', 'voicemail',
    'no_answer', 'do_not_call', 'completed', 'failed'
);

CREATE TYPE consentstatus AS ENUM ('opted_in', 'opted_out', 'pending', 'revoked');

CREATE TYPE consenttype AS ENUM ('voice_call', 'sms', 'email', 'all_channels');

CREATE TYPE appointmentstatus AS ENUM (
    'scheduled', 'confirmed', 'completed', 'no_show', 'cancelled', 'rescheduled'
);

CREATE TYPE userrole AS ENUM ('admin', 'rep', 'ops');


-- ── property ───────────────────────────────────────────────────────────────

CREATE TABLE property (
    id                       SERIAL PRIMARY KEY,
    address_line1            VARCHAR(255) NOT NULL,
    address_line2            VARCHAR(255),
    city                     VARCHAR(100) NOT NULL,
    state                    VARCHAR(2) NOT NULL DEFAULT 'MD',
    zip_code                 VARCHAR(10) NOT NULL,
    county                   VARCHAR(100) NOT NULL,
    parcel_id                VARCHAR(50) UNIQUE,

    -- Property details
    property_type            propertytype DEFAULT 'SFH',
    year_built               INTEGER,
    roof_area_sqft           DOUBLE PRECISION,
    assessed_value           DOUBLE PRECISION,
    lot_size_sqft            DOUBLE PRECISION,

    -- Solar factors
    utility_zone             VARCHAR(20),
    tree_cover_pct           DOUBLE PRECISION,
    neighborhood_solar_pct   DOUBLE PRECISION,
    has_existing_solar       BOOLEAN DEFAULT FALSE,

    -- Owner info (denormalized for MVP)
    owner_first_name         VARCHAR(100),
    owner_last_name          VARCHAR(100),
    owner_occupied           BOOLEAN DEFAULT TRUE,
    owner_phone              VARCHAR(20),
    owner_email              VARCHAR(255),

    -- Census / demographics
    median_household_income  DOUBLE PRECISION,

    -- Meta
    data_source              VARCHAR(50),
    raw_data                 JSONB,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_property_county ON property (county);
CREATE INDEX ix_property_zip ON property (zip_code);
CREATE INDEX ix_property_state ON property (state);


-- ── rep_user ───────────────────────────────────────────────────────────────

CREATE TABLE rep_user (
    id            SERIAL PRIMARY KEY,
    email         VARCHAR(255) UNIQUE NOT NULL,
    name          VARCHAR(200) NOT NULL,
    phone         VARCHAR(20),
    role          userrole DEFAULT 'rep',
    is_active     BOOLEAN DEFAULT TRUE,
    api_key_hash  VARCHAR(255),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ── lead ───────────────────────────────────────────────────────────────────

CREATE TABLE lead (
    id                     SERIAL PRIMARY KEY,
    property_id            INTEGER NOT NULL UNIQUE REFERENCES property(id),
    status                 leadstatus NOT NULL DEFAULT 'ingested',
    assigned_rep_id        INTEGER REFERENCES rep_user(id),

    -- Contact info (denormalized from property)
    first_name             VARCHAR(100),
    last_name              VARCHAR(100),
    phone                  VARCHAR(20),
    email                  VARCHAR(255),

    -- Outreach tracking
    last_contacted_at      TIMESTAMPTZ,
    total_call_attempts    INTEGER DEFAULT 0,
    total_sms_sent         INTEGER DEFAULT 0,
    total_emails_sent      INTEGER DEFAULT 0,
    next_outreach_at       TIMESTAMPTZ,
    next_outreach_channel  contactchannel,

    -- Meta
    created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_lead_status ON lead (status);
CREATE INDEX ix_lead_next_outreach ON lead (next_outreach_at);
CREATE INDEX ix_lead_assigned_rep ON lead (assigned_rep_id);


-- ── lead_score ─────────────────────────────────────────────────────────────

CREATE TABLE lead_score (
    id                   SERIAL PRIMARY KEY,
    lead_id              INTEGER NOT NULL REFERENCES lead(id),
    total_score          INTEGER NOT NULL,
    score_version        VARCHAR(10) NOT NULL DEFAULT 'v1',

    -- Individual factor scores (explainability)
    roof_age_score       INTEGER DEFAULT 0,
    ownership_score      INTEGER DEFAULT 0,
    roof_area_score      INTEGER DEFAULT 0,
    home_value_score     INTEGER DEFAULT 0,
    utility_rate_score   INTEGER DEFAULT 0,
    shade_score          INTEGER DEFAULT 0,
    neighborhood_score   INTEGER DEFAULT 0,
    income_score         INTEGER DEFAULT 0,
    property_type_score  INTEGER DEFAULT 0,
    existing_solar_score INTEGER DEFAULT 0,

    scored_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_lead_score_lead_id ON lead_score (lead_id);
CREATE INDEX ix_lead_score_total ON lead_score (total_score);


-- ── script_version ─────────────────────────────────────────────────────────

CREATE TABLE script_version (
    id              SERIAL PRIMARY KEY,
    version_label   VARCHAR(20) NOT NULL,
    channel         contactchannel NOT NULL,
    content         TEXT NOT NULL,
    is_active       BOOLEAN DEFAULT FALSE,
    created_by      VARCHAR(100),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_script_channel_active ON script_version (channel, is_active);


-- ── outreach_attempt ───────────────────────────────────────────────────────

CREATE TABLE outreach_attempt (
    id                  SERIAL PRIMARY KEY,
    lead_id             INTEGER NOT NULL REFERENCES lead(id),
    channel             contactchannel NOT NULL,
    disposition         contactdisposition,
    script_version_id   INTEGER REFERENCES script_version(id),

    -- Call details
    external_call_id    VARCHAR(100),
    duration_seconds    INTEGER,
    recording_url       VARCHAR(500),
    transcript          TEXT,

    -- SMS/Email details
    message_body        TEXT,
    template_id         VARCHAR(50),

    -- Qualification result
    qualified           BOOLEAN,
    qualification_data  JSONB,

    -- Timing
    started_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at            TIMESTAMPTZ
);

CREATE INDEX ix_outreach_lead_id ON outreach_attempt (lead_id);
CREATE INDEX ix_outreach_channel ON outreach_attempt (channel);
CREATE INDEX ix_outreach_started_at ON outreach_attempt (started_at);


-- ── consent_log ────────────────────────────────────────────────────────────

CREATE TABLE consent_log (
    id              SERIAL PRIMARY KEY,
    lead_id         INTEGER NOT NULL REFERENCES lead(id),
    consent_type    consenttype NOT NULL,
    status          consentstatus NOT NULL,
    channel         contactchannel NOT NULL,

    -- Evidence of consent
    evidence_type   VARCHAR(50),    -- 'verbal', 'sms_reply', 'web_form', 'written'
    evidence_url    VARCHAR(500),   -- recording URL, screenshot, etc.
    ip_address      VARCHAR(45),
    user_agent      VARCHAR(500),

    recorded_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_consent_lead_id ON consent_log (lead_id);
CREATE INDEX ix_consent_status ON consent_log (status);


-- ── appointment ────────────────────────────────────────────────────────────

CREATE TABLE appointment (
    id               SERIAL PRIMARY KEY,
    lead_id          INTEGER NOT NULL REFERENCES lead(id),
    rep_id           INTEGER NOT NULL REFERENCES rep_user(id),
    status           appointmentstatus DEFAULT 'scheduled',
    scheduled_start  TIMESTAMPTZ NOT NULL,
    scheduled_end    TIMESTAMPTZ NOT NULL,
    address          VARCHAR(500),
    notes            TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_appointment_rep_id ON appointment (rep_id);
CREATE INDEX ix_appointment_scheduled ON appointment (scheduled_start);
CREATE INDEX ix_appointment_status ON appointment (status);


-- ── audit_log ──────────────────────────────────────────────────────────────

CREATE TABLE audit_log (
    id             SERIAL PRIMARY KEY,
    actor          VARCHAR(100) NOT NULL,   -- 'system', 'ai_agent', user email
    action         VARCHAR(100) NOT NULL,   -- 'lead.status_change', 'outreach.call', etc.
    entity_type    VARCHAR(50) NOT NULL,    -- 'lead', 'property', 'appointment'
    entity_id      INTEGER,
    old_value      TEXT,
    new_value      TEXT,
    metadata_json  JSONB,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_audit_entity ON audit_log (entity_type, entity_id);
CREATE INDEX ix_audit_created_at ON audit_log (created_at);
CREATE INDEX ix_audit_actor ON audit_log (actor);


-- ── note ───────────────────────────────────────────────────────────────────

CREATE TABLE note (
    id          SERIAL PRIMARY KEY,
    lead_id     INTEGER NOT NULL REFERENCES lead(id),
    author      VARCHAR(100) NOT NULL,
    content     TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_note_lead_id ON note (lead_id);
