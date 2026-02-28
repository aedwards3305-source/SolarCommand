# SolarCommand LeadGen — Complete Build Specification

**Version:** 1.0 | **Date:** 2026-02-06 | **Status:** Design Complete

---

# A) EXECUTIVE OVERVIEW

## What It Does

SolarCommand LeadGen is an upstream lead-discovery engine that finds high-intent homeowner leads from lawful public and licensed data sources, enriches them with verified contact information, scores solar intent, and activates them for multi-channel outreach — all with compliance enforcement and full audit trails.

It extends the existing SolarCommand outreach platform by adding the layer that answers: **"Who should we be calling in the first place?"**

## What It Does NOT Do

- Scrape websites, social media, or any source that prohibits automated collection.
- Bypass DNC registries, fabricate consent, or auto-dial without activation gates.
- Impersonate utilities, government agencies, or any entity the organization is not.
- Use AI to autonomously contact leads without human approval (suggest-only by default).
- Store or process data from sources where the license prohibits the use case.

## Why It's Different

1. **Discovers leads from defensible sources** — tax assessor records, building permits, utility territories, and licensed vendor feeds. Every data point has a `source_record` with provenance.
2. **Two-stage funnel** — Address-level discovery is separated from contact-level activation. A property can be "discovered" without anyone being contactable. Activation requires enriched contact data, compliance clearance, and minimum confidence thresholds.
3. **Compliance is structural** — TCPA quiet hours, DNC scrubbing, consent tracking, and opt-out detection are gates in the pipeline, not guidelines for reps.
4. **Auditable AI** — Every AI call logs inputs, outputs, tokens, cost, latency, and citations to the source records that informed the decision.
5. **Pluggable connectors** — New data sources (county datasets, vendor APIs, BYOD uploads) are added as connectors without changing the core pipeline.

## Lead Lifecycle

```
 DISCOVER        VALIDATE       ENRICH         SCORE
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ Ingest   │──▶│ Dedupe   │──▶│ Contact  │──▶│ Discovery│
│ property │   │ Normalize│   │ lookup   │   │ + Activ. │
│ data     │   │ Quality  │   │ Validate │   │ scoring  │
└──────────┘   └──────────┘   └──────────┘   └──────────┘
                                                   │
 FEEDBACK       OUTREACH       DISTRIBUTE    ACTIVATE
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ Outcome  │◀──│ Voice    │◀──│ Route to │◀──│ Compliance│
│ feeds    │   │ SMS      │   │ rep/team │   │ gate +   │
│ scoring  │   │ Email    │   │          │   │ approval │
└──────────┘   └──────────┘   └──────────┘   └──────────┘
```

---

# B) ARCHITECTURE

## High-Level Diagram

```
                          ┌─────────────────────────────────────┐
                          │           FRONTEND (Next.js)         │
                          │  Discovery Dashboard │ Source Wizard  │
                          │  Activation Queue    │ Lead Detail    │
                          │  Outreach Timeline   │ Admin/Audit    │
                          └───────────┬─────────────────────────┘
                                      │ HTTPS :3000
                          ┌───────────▼─────────────────────────┐
                          │           API GATEWAY (FastAPI)       │
                          │  Auth/RBAC │ Rate Limit │ Validation  │
                          │  /sources  /discover  /activate       │
                          │  /enrich   /leads     /outreach       │
                          │  /compliance /audit   /admin          │
                          └──┬────┬────┬────┬────┬──────────────┘
                             │    │    │    │    │
               ┌─────────────┘    │    │    │    └─────────────┐
               ▼                  ▼    │    ▼                  ▼
    ┌──────────────────┐  ┌──────────┐ │ ┌──────────────┐ ┌──────────────┐
    │  CONNECTOR        │  │ COMPLIANCE│ │ │ AI SERVICE   │ │ ENRICHMENT   │
    │  WORKERS (Celery) │  │ SERVICE   │ │ │ (Claude)     │ │ SERVICE      │
    │                   │  │           │ │ │              │ │              │
    │ Tax Assessor      │  │ DNC Scrub │ │ │ Classify     │ │ PDL          │
    │ Building Permits  │  │ TCPA Gate │ │ │ Score Assist │ │ Melissa      │
    │ Utility Zones     │  │ Consent   │ │ │ Rep Brief    │ │ Phone/Email  │
    │ Solar Suitability │  │ Quiet Hrs │ │ │ BYOD Mapper  │ │ Validation   │
    │ Vendor Feeds      │  │ Opt-Out   │ │ │ Source QA    │ │              │
    │ BYOD Uploads      │  │ Audit     │ │ │ Audit        │ │              │
    └────────┬─────────┘  └─────┬─────┘ │ └──────┬───────┘ └──────┬───────┘
             │                  │        │        │                │
             └──────────────────┴────────┼────────┴────────────────┘
                                         │
                              ┌──────────▼──────────┐
                              │   TASK QUEUE (Redis)  │
                              │   Celery Beat + Worker│
                              │   Distributed Locks   │
                              └──────────┬────────────┘
                                         │
                              ┌──────────▼──────────┐
                              │   PostgreSQL 16       │
                              │   22+ tables          │
                              │   Full audit trail    │
                              └───────────────────────┘
```

## Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Frontend | Next.js 14, TypeScript, Tailwind | Already in place; add map views with Mapbox GL |
| API | FastAPI (Python 3.12, async) | Already in place; extend with new routers |
| Database | PostgreSQL 16 + PostGIS | Add PostGIS for geo queries (radius, polygon, territory) |
| Queue | Redis 7 + Celery | Already in place; add connector worker queues |
| AI | Anthropic Claude (Sonnet 4.5) | Already integrated; extend with new task types |
| Enrichment | PDL + Melissa + Twilio Lookup | Already partially integrated |
| Voice | Twilio / Vapi | Already integrated |
| GIS | PostGIS + Mapbox GL JS | New: spatial indexing, map-based targeting |
| Observability | Structured JSON logs + Sentry | New: add tracing and alerting |

## Service Boundaries

**Connector Workers** — Isolated per data source. Each connector knows how to fetch, parse, normalize, and dedupe records from one source type. Connectors write to `source_record` + `property` tables. Failures in one connector never block others.

**Compliance Service** — Stateless rule engine. Takes a lead + org config, returns allow/deny + reasons. Called synchronously before any outreach action. Never bypassed.

**AI Service** — Thin wrapper around Claude API. Every call goes through a single client that logs to `ai_run`. Deterministic fallbacks for every task. Suggest-only by default.

**Enrichment Service** — Manages contact lookup lifecycle. Rate limiting, backoff, deduplication of lookup requests. Writes to `contact_candidate` + `contact_validation`.

---

# C) DATA SOURCES + CONNECTOR STRATEGY

## Lawful Data Sources

### 1. County Tax Assessor / Parcel Records

**What:** Property ownership, assessed values, parcel IDs, property characteristics, owner names and mailing addresses. Public records in most US jurisdictions.

**Ingestion methods:**
- Bulk CSV/shapefile downloads from county GIS portals (most common)
- State open-data portals (e.g., Maryland SDAT, California BOE)
- Licensed aggregators: ATTOM, CoreLogic, Regrid (mark as `license: vendor_feed`)
- County-specific APIs where available

**Cadence:** Weekly for high-priority counties; monthly for others. Parcel data changes slowly.

**Dedupe keys:** `parcel_id` (primary), normalized address (fallback).

**Rate limits:** Bulk downloads have no rate limit. APIs: respect `Retry-After` headers, default 1 req/sec.

**Data quality:** High for ownership/value/address. Variable for owner contact info (mailing address may be PO Box or property management company).

**Quality score factors:** Has parcel_id (+20), has owner name (+15), owner address matches property (+10), recent assessment date (+10), complete property characteristics (+10).

```python
# Connector config example
TAX_ASSESSOR_CONNECTOR = {
    "source_type": "tax_assessor",
    "license": "public_record",
    "ingestion": "bulk_csv",
    "cadence": "weekly",
    "dedupe_key": "parcel_id",
    "rate_limit": None,  # bulk download
    "counties": ["baltimore_county_md", "anne_arundel_md", "howard_md"],
    "fields_mapped": [
        "parcel_id", "address", "owner_name", "owner_mailing_address",
        "assessed_value", "year_built", "property_type", "lot_size_sqft",
        "building_sqft", "roof_area_estimate", "sale_date", "sale_price"
    ]
}
```

### 2. Building Permits

**What:** Roof replacement permits, electrical upgrade permits, solar installation permits (to identify homes that already have solar). High-intent signal: a homeowner who just replaced their roof is 3x more likely to consider solar.

**Ingestion methods:**
- Municipal open-data portals (Socrata, ArcGIS Hub)
- State licensing board records
- Licensed aggregators: BuildZoom, PermitData

**Cadence:** Daily for active counties (permits are time-sensitive signals).

**Dedupe keys:** `permit_number` + `jurisdiction`.

**Rate limits:** Socrata API: 1000 req/hour with app token. ArcGIS: 200 req/min.

**Data quality:** Moderate. Permit descriptions are free-text; AI-assisted classification needed to identify roof/electrical/solar permits. Address matching to parcel requires normalization.

**Quality score factors:** Permit type matched to solar-relevant (+25), permit is recent <6mo (+15), address links to known parcel (+10), permit is closed/final (+5).

```python
PERMIT_CONNECTOR = {
    "source_type": "building_permit",
    "license": "public_record",
    "ingestion": "api_paginated",
    "cadence": "daily",
    "dedupe_key": "permit_number+jurisdiction",
    "rate_limit": "1000/hour",
    "permit_types_of_interest": [
        "roof_replacement", "reroof", "electrical_upgrade",
        "solar_installation", "panel_upgrade", "ev_charger"
    ]
}
```

### 3. Utility Territory / Rate Zones

**What:** Which utility serves a given address, what rate class, estimated average bill. Higher utility rates = stronger solar economics = higher intent.

**Ingestion methods:**
- EIA (Energy Information Administration) — public, free API
- Utility company territory GIS layers (most publish as public shapefiles)
- OpenEI (NREL) utility rate database — public, free API
- Licensed: Genability / Arcadia for granular rate modeling

**Cadence:** Quarterly (rates change slowly; territory boundaries rarely change).

**Dedupe keys:** `utility_id` + `rate_schedule_id`.

**Rate limits:** EIA: 1000/hour. OpenEI: 500/hour.

**Data quality:** High for territory boundaries. Moderate for rate estimates (actual bills vary by usage).

```python
UTILITY_CONNECTOR = {
    "source_type": "utility_territory",
    "license": "public_data",
    "ingestion": "api_bulk",
    "cadence": "quarterly",
    "dedupe_key": "utility_id+rate_schedule",
    "rate_limit": "1000/hour",
    "data_provided": [
        "utility_name", "territory_geom", "rate_class",
        "avg_residential_rate_kwh", "avg_monthly_bill_estimate"
    ]
}
```

### 4. Solar Suitability Proxies

**What:** Estimates of solar potential based on publicly available geospatial data. NOT Google Sunroof (terms restrict automated access).

**Ingestion methods:**
- Building footprints: Microsoft US Building Footprints (open, CC-BY-4.0) → roof area estimate
- Tree cover: NLCD (National Land Cover Database) → shade proxy per census block
- Solar irradiance: NREL NSRDB (National Solar Radiation Database) → annual GHI per location
- Aspect/slope: USGS 3DEP elevation data → south-facing roof proxy

**Cadence:** Annual (these datasets update infrequently).

**Dedupe keys:** Spatial join to `parcel_id` / address point.

**Rate limits:** NREL API: 1000/hour. Raster datasets: bulk download + local processing.

**Data quality:** Moderate. Building footprints are estimates. Tree cover is per-block, not per-parcel. Good enough for scoring; not precise enough for system design.

**Assumption:** We use these as scoring proxies, not as engineering data. Sales reps are told "high solar potential based on available data" — never specific kWh projections.

```python
SOLAR_PROXY_CONNECTOR = {
    "source_type": "solar_suitability",
    "license": "public_data",
    "ingestion": "bulk_raster_spatial_join",
    "cadence": "annual",
    "data_provided": [
        "building_footprint_sqft", "estimated_roof_area_sqft",
        "tree_cover_pct_block", "annual_ghi_kwh_m2",
        "south_facing_probability"
    ]
}
```

### 5. Demographic Bands

**What:** Census-tract-level median income, homeownership rate, housing age distribution. Used for investment-capacity and ownership-likelihood proxies.

**Ingestion methods:**
- US Census ACS 5-Year Estimates (public, free API)
- Census TIGER/Line shapefiles for tract boundaries

**Cadence:** Annual (ACS releases annually).

**Dedupe keys:** `census_tract_geoid`.

**Rate limits:** Census API: 500/day without key, 50000/day with key.

```python
DEMOGRAPHIC_CONNECTOR = {
    "source_type": "demographic_band",
    "license": "public_data",
    "ingestion": "api_bulk",
    "cadence": "annual",
    "dedupe_key": "census_tract_geoid",
    "data_provided": [
        "median_household_income", "homeownership_rate",
        "median_year_built", "median_home_value",
        "population_density", "housing_units"
    ]
}
```

### 6. MLS Data (Licensed Only)

**What:** Active/recent home sales, listing details, days on market.

**Status:** **LICENSED VENDOR FEED ONLY.** MLS data is copyrighted and access requires a real estate license or authorized vendor agreement (e.g., CoreLogic, Black Knight, Zillow Bridge API). We do NOT scrape Zillow, Realtor.com, or any MLS-derived website.

**Ingestion:** Via licensed RETS/RESO API feed only.

**Cadence:** Daily (if licensed).

**Use case:** Recent home sales = new homeowner likely to invest. Long listing = motivated seller (less relevant for solar).

```python
MLS_CONNECTOR = {
    "source_type": "mls",
    "license": "vendor_feed_required",  # EXPLICIT: requires license
    "ingestion": "rets_api",
    "cadence": "daily",
    "requires_license_verification": True,
    "vendor_options": ["corelogic", "black_knight", "zillow_bridge"]
}
```

### 7. Contact Enrichment (Vendor)

**What:** Phone numbers, email addresses, job titles, LinkedIn, from people-data vendors.

**Vendors:** People Data Labs, Melissa Data, Twilio Lookup, FullContact.

**License:** All are paid API services with terms that permit B2B/B2C outreach use cases. Verify terms per vendor before enabling.

**Cadence:** On-demand per discovered lead (not bulk). Rate-limited.

**Confidence gating:** Only accept matches above configurable threshold (default 0.5).

```python
ENRICHMENT_CONNECTOR = {
    "source_type": "contact_enrichment",
    "license": "vendor_api",
    "ingestion": "on_demand",
    "providers": {
        "pdl": {"rate_limit": "100/min", "cost": "$0.10/lookup"},
        "melissa": {"rate_limit": "50/min", "cost": "$0.02/validation"},
        "twilio_lookup": {"rate_limit": "100/min", "cost": "$0.005/lookup"}
    },
    "confidence_threshold": 0.5,
    "max_daily_lookups": 500  # cost control
}
```

### 8. Bring Your Own Data (BYOD)

**What:** CSV/Excel uploads from the organization's existing lead lists, purchased lists, or manual exports.

**Ingestion:** Upload → AI-assisted column mapping → validation → normalization → insert.

**Quality:** Variable. BYOD uploads get a `source_quality_score` based on completeness, field consistency, and address matchability. The AI mapping assistant handles non-standard column names.

**Compliance note:** BYOD data inherits the organization's stated source/consent level. The system prompts the uploader to declare the data source and consent basis.

```python
BYOD_CONNECTOR = {
    "source_type": "byod_upload",
    "license": "org_declared",
    "ingestion": "file_upload",
    "supported_formats": ["csv", "xlsx"],
    "max_file_size_mb": 50,
    "max_rows": 50000,
    "requires_source_declaration": True,
    "requires_consent_declaration": True,
    "ai_column_mapping": True
}
```

---

# D) CORE DATABASE SCHEMA

## Assumptions

- Multi-tenant via `organization_id` on most tables.
- Address normalization: uppercase, strip apt/suite, standardize street suffixes.
- Phone normalization: E.164 format. Phone hash: SHA-256 of E.164 for DNC matching.
- Idempotency: upsert on dedupe keys; `idempotency_key` on mutation endpoints.
- Timestamps: UTC everywhere. Display in org timezone on frontend.
- Soft deletes: `deleted_at` where needed. Audit log is append-only (no deletes).

## Entity-Relationship Overview

```
organization
├── user (rbac via role)
├── data_source_config
│   └── source_record
│       └── property
│           ├── property_feature
│           ├── permit_record
│           └── discovered_lead
│               ├── discovery_score
│               ├── contact_candidate
│               │   ├── contact_validation
│               │   └── consent_event
│               ├── compliance_flag
│               └── lead (activated)
│                   ├── lead_score
│                   ├── distribution_assignment
│                   ├── outreach_attempt
│                   ├── message_thread
│                   ├── conversation_transcript
│                   ├── qa_review
│                   └── nba_decision
├── script_version
├── script_experiment
├── ai_run
└── audit_log
```

## Table Definitions

```sql
-- ============================================================
-- ORGANIZATION + USERS
-- ============================================================

CREATE TABLE organization (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    slug            TEXT UNIQUE NOT NULL,
    timezone        TEXT NOT NULL DEFAULT 'US/Eastern',
    settings_json   JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TYPE user_role AS ENUM ('owner', 'admin', 'manager', 'rep', 'ops', 'readonly');

CREATE TABLE app_user (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organization(id),
    email           TEXT NOT NULL,
    password_hash   TEXT,
    full_name       TEXT NOT NULL,
    role            user_role NOT NULL DEFAULT 'rep',
    api_key_hash    TEXT,
    is_active       BOOLEAN NOT NULL DEFAULT true,
    last_login_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(organization_id, email)
);

CREATE INDEX idx_user_org ON app_user(organization_id);

-- ============================================================
-- DATA SOURCE PROVENANCE
-- ============================================================

CREATE TYPE source_type AS ENUM (
    'tax_assessor', 'building_permit', 'utility_territory',
    'solar_suitability', 'demographic_band', 'mls',
    'contact_enrichment', 'byod_upload', 'vendor_feed'
);

CREATE TYPE license_type AS ENUM (
    'public_record', 'public_data', 'vendor_feed',
    'vendor_api', 'org_declared', 'mls_licensed'
);

CREATE TABLE data_source_config (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organization(id),
    source_type     source_type NOT NULL,
    name            TEXT NOT NULL,            -- "Baltimore County Tax Assessor 2026"
    license         license_type NOT NULL,
    license_detail  TEXT,                     -- license number, agreement ref
    connector_class TEXT NOT NULL,            -- "connectors.tax_assessor.BaltimoreCountyConnector"
    config_json     JSONB NOT NULL DEFAULT '{}',  -- connector-specific config
    ingestion_cadence TEXT,                   -- "daily", "weekly", "monthly", "manual"
    is_active       BOOLEAN NOT NULL DEFAULT true,
    last_sync_at    TIMESTAMPTZ,
    last_sync_status TEXT,
    records_synced  INTEGER DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_dsc_org ON data_source_config(organization_id);

CREATE TABLE source_record (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id     UUID NOT NULL REFERENCES organization(id),
    data_source_id      UUID NOT NULL REFERENCES data_source_config(id),
    source_type         source_type NOT NULL,
    license             license_type NOT NULL,
    retrieval_method    TEXT NOT NULL,        -- "bulk_csv_download", "api_call", "file_upload"
    retrieval_timestamp TIMESTAMPTZ NOT NULL,
    dataset_name        TEXT NOT NULL,        -- "baltimore_county_sdat_2026q1"
    dataset_version     TEXT,
    raw_record_id       TEXT,                 -- original ID in source (parcel_id, permit_number)
    raw_record_json     JSONB,               -- original record as received
    evidence_fields     JSONB NOT NULL,       -- {"parcel_id": "0412...", "address": "123 Main"}
    confidence          NUMERIC(3,2) NOT NULL DEFAULT 1.00,
    quality_score       INTEGER DEFAULT 0,    -- 0-100
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_sr_org ON source_record(organization_id);
CREATE INDEX idx_sr_source ON source_record(data_source_id);
CREATE INDEX idx_sr_raw_id ON source_record(raw_record_id);
CREATE INDEX idx_sr_created ON source_record(created_at);

-- ============================================================
-- PROPERTY (CANONICAL)
-- ============================================================

CREATE TYPE property_type AS ENUM (
    'single_family', 'townhome', 'condo', 'duplex',
    'triplex', 'quadplex', 'mobile_home', 'other'
);

CREATE TABLE property (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id     UUID NOT NULL REFERENCES organization(id),
    -- Address (normalized)
    address_line1       TEXT NOT NULL,
    address_line2       TEXT,
    city                TEXT NOT NULL,
    state               TEXT NOT NULL,        -- 2-letter
    zip_code            TEXT NOT NULL,
    county              TEXT,
    address_hash        TEXT NOT NULL,         -- SHA-256 of normalized full address
    -- Geo
    latitude            NUMERIC(10,7),
    longitude           NUMERIC(10,7),
    geom                GEOMETRY(Point, 4326), -- PostGIS
    census_tract        TEXT,
    -- Parcel
    parcel_id           TEXT,
    -- Property characteristics
    property_type       property_type,
    year_built          INTEGER,
    building_sqft       INTEGER,
    lot_size_sqft       INTEGER,
    roof_area_sqft      INTEGER,              -- estimated from footprint
    stories             INTEGER,
    -- Value
    assessed_value      NUMERIC(12,2),
    last_sale_date      DATE,
    last_sale_price     NUMERIC(12,2),
    -- Owner (from tax records — public record)
    owner_first_name    TEXT,
    owner_last_name     TEXT,
    owner_mailing_addr  TEXT,
    owner_occupied      BOOLEAN,
    -- Solar factors
    utility_name        TEXT,
    utility_rate_zone   TEXT,
    avg_rate_kwh        NUMERIC(6,4),
    has_existing_solar  BOOLEAN DEFAULT false,
    tree_cover_pct      NUMERIC(5,2),
    annual_ghi          NUMERIC(8,2),         -- kWh/m²/year
    south_facing_prob   NUMERIC(3,2),
    neighborhood_solar_pct NUMERIC(5,2),
    -- Demographics (tract-level, not individual)
    median_household_income INTEGER,
    homeownership_rate  NUMERIC(5,2),
    -- Provenance
    primary_source_id   UUID REFERENCES source_record(id),
    source_ids          UUID[] NOT NULL DEFAULT '{}', -- all contributing sources
    -- Meta
    data_quality_score  INTEGER DEFAULT 0,    -- 0-100
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(organization_id, address_hash)
);

CREATE INDEX idx_prop_org ON property(organization_id);
CREATE INDEX idx_prop_addr_hash ON property(address_hash);
CREATE INDEX idx_prop_parcel ON property(organization_id, parcel_id);
CREATE INDEX idx_prop_geom ON property USING GIST(geom);
CREATE INDEX idx_prop_county ON property(organization_id, county);
CREATE INDEX idx_prop_zip ON property(organization_id, zip_code);

-- ============================================================
-- PERMIT RECORDS
-- ============================================================

CREATE TYPE permit_category AS ENUM (
    'roof_replacement', 'electrical_upgrade', 'solar_installation',
    'panel_upgrade', 'ev_charger', 'hvac', 'other'
);

CREATE TABLE permit_record (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organization(id),
    property_id     UUID REFERENCES property(id),
    source_record_id UUID NOT NULL REFERENCES source_record(id),
    permit_number   TEXT NOT NULL,
    jurisdiction    TEXT NOT NULL,
    category        permit_category,          -- AI-classified or mapped
    raw_description TEXT,
    issue_date      DATE,
    final_date      DATE,
    status          TEXT,                     -- "issued", "final", "expired"
    contractor_name TEXT,
    estimated_cost  NUMERIC(12,2),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(organization_id, permit_number, jurisdiction)
);

CREATE INDEX idx_permit_prop ON permit_record(property_id);
CREATE INDEX idx_permit_cat ON permit_record(organization_id, category);
CREATE INDEX idx_permit_date ON permit_record(issue_date);

-- ============================================================
-- DISCOVERED LEAD (ADDRESS-LEVEL — STAGE A)
-- ============================================================

CREATE TYPE discovery_status AS ENUM (
    'discovered', 'scoring', 'scored',
    'enriching', 'enriched',
    'activation_ready', 'activated',
    'rejected', 'archived'
);

CREATE TABLE discovered_lead (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organization(id),
    property_id     UUID NOT NULL REFERENCES property(id),
    status          discovery_status NOT NULL DEFAULT 'discovered',
    -- Discovery context
    discovery_reason TEXT,                    -- "high_roof_age+owner_occupied+bge_zone"
    discovery_batch  TEXT,                    -- "nightly_2026-02-06"
    -- Scores
    discovery_score  INTEGER,                 -- 0-100
    activation_score INTEGER,                 -- 0-100 (set after enrichment)
    -- Enrichment tracking
    enrichment_attempted BOOLEAN DEFAULT false,
    enrichment_at    TIMESTAMPTZ,
    best_phone       TEXT,                    -- selected best contact
    best_email       TEXT,
    best_contact_confidence NUMERIC(3,2),
    -- Activation
    activated_at     TIMESTAMPTZ,
    activated_by     UUID REFERENCES app_user(id),
    rejection_reason TEXT,
    -- Source provenance
    source_record_ids UUID[] NOT NULL DEFAULT '{}',
    -- Meta
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(organization_id, property_id)     -- one discovered lead per property per org
);

CREATE INDEX idx_dl_org_status ON discovered_lead(organization_id, status);
CREATE INDEX idx_dl_score ON discovered_lead(organization_id, discovery_score DESC);
CREATE INDEX idx_dl_created ON discovered_lead(created_at);

-- ============================================================
-- DISCOVERY SCORE BREAKDOWN
-- ============================================================

CREATE TABLE discovery_score (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    discovered_lead_id  UUID NOT NULL REFERENCES discovered_lead(id),
    model_version       TEXT NOT NULL DEFAULT 'v1',
    total_score         INTEGER NOT NULL,     -- 0-100
    -- Factor breakdown (points earned / max)
    roof_suitability    INTEGER NOT NULL DEFAULT 0,   -- /20
    ownership_signal    INTEGER NOT NULL DEFAULT 0,   -- /15
    financial_capacity  INTEGER NOT NULL DEFAULT 0,   -- /15
    utility_economics   INTEGER NOT NULL DEFAULT 0,   -- /15
    solar_potential     INTEGER NOT NULL DEFAULT 0,   -- /15
    permit_triggers     INTEGER NOT NULL DEFAULT 0,   -- /10
    neighborhood_adoption INTEGER NOT NULL DEFAULT 0, -- /10
    -- Explanation
    factor_details_json JSONB NOT NULL DEFAULT '{}',  -- per-factor reasoning
    source_citations    JSONB NOT NULL DEFAULT '[]',  -- source_record_ids per factor
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_ds_lead ON discovery_score(discovered_lead_id);

-- ============================================================
-- CONTACT CANDIDATE (FROM ENRICHMENT)
-- ============================================================

CREATE TYPE contact_method AS ENUM ('phone', 'email');
CREATE TYPE phone_type AS ENUM ('mobile', 'landline', 'voip', 'unknown');

CREATE TABLE contact_candidate (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id     UUID NOT NULL REFERENCES organization(id),
    discovered_lead_id  UUID NOT NULL REFERENCES discovered_lead(id),
    source_record_id    UUID REFERENCES source_record(id),
    method              contact_method NOT NULL,
    value               TEXT NOT NULL,         -- phone (E.164) or email
    value_hash          TEXT NOT NULL,         -- SHA-256 for DNC matching
    confidence          NUMERIC(3,2) NOT NULL,
    -- Phone-specific
    phone_type          phone_type,
    carrier_name        TEXT,
    line_status         TEXT,                  -- "active", "disconnected"
    -- Email-specific
    email_deliverable   BOOLEAN,
    email_disposable    BOOLEAN,
    -- Validation
    validated           BOOLEAN DEFAULT false,
    validated_at        TIMESTAMPTZ,
    validation_provider TEXT,
    -- Selection
    is_primary          BOOLEAN DEFAULT false,
    -- Meta
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_cc_lead ON contact_candidate(discovered_lead_id);
CREATE INDEX idx_cc_hash ON contact_candidate(value_hash);

-- ============================================================
-- CONSENT + COMPLIANCE
-- ============================================================

CREATE TYPE consent_type AS ENUM (
    'voice_call', 'sms', 'email', 'all_channels'
);
CREATE TYPE consent_status AS ENUM (
    'explicit_opt_in', 'inferred', 'unknown', 'opted_out', 'revoked'
);

CREATE TABLE consent_event (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id     UUID NOT NULL REFERENCES organization(id),
    discovered_lead_id  UUID REFERENCES discovered_lead(id),
    lead_id             UUID,                 -- set after activation
    contact_value_hash  TEXT NOT NULL,         -- which phone/email
    consent_type        consent_type NOT NULL,
    consent_status      consent_status NOT NULL,
    -- Evidence
    evidence_method     TEXT NOT NULL,         -- "web_form", "verbal", "sms_keyword", "import_declaration"
    evidence_detail     TEXT,                  -- form URL, recording ID, import batch
    evidence_ip         INET,
    evidence_user_agent TEXT,
    -- Source
    recorded_by         UUID REFERENCES app_user(id),
    recorded_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at          TIMESTAMPTZ           -- consent can expire
);

CREATE INDEX idx_consent_lead ON consent_event(discovered_lead_id);
CREATE INDEX idx_consent_hash ON consent_event(contact_value_hash);
CREATE INDEX idx_consent_status ON consent_event(consent_status);

CREATE TYPE flag_type AS ENUM (
    'federal_dnc', 'state_dnc', 'internal_dnc',
    'litigation_risk', 'known_litigator',
    'fraud_flag', 'duplicate_contact', 'deceased'
);

CREATE TABLE compliance_flag (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id     UUID NOT NULL REFERENCES organization(id),
    contact_value_hash  TEXT NOT NULL,
    flag_type           flag_type NOT NULL,
    flag_source         TEXT NOT NULL,         -- "federal_dnc_2026q1", "internal_list"
    is_active           BOOLEAN NOT NULL DEFAULT true,
    detail              TEXT,
    detected_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at          TIMESTAMPTZ
);

CREATE INDEX idx_cf_hash ON compliance_flag(contact_value_hash, is_active);
CREATE INDEX idx_cf_org ON compliance_flag(organization_id);

-- ============================================================
-- LEAD (ACTIVATED — STAGE B)
-- ============================================================

CREATE TYPE lead_status AS ENUM (
    'activated', 'assigned', 'contacting', 'contacted',
    'qualified', 'appointment_set', 'nurturing',
    'closed_won', 'closed_lost', 'dnc', 'disqualified', 'archived'
);

CREATE TABLE lead (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id     UUID NOT NULL REFERENCES organization(id),
    discovered_lead_id  UUID NOT NULL REFERENCES discovered_lead(id),
    property_id         UUID NOT NULL REFERENCES property(id),
    status              lead_status NOT NULL DEFAULT 'activated',
    -- Best contact (copied from contact_candidate at activation)
    contact_phone       TEXT,
    contact_email       TEXT,
    contact_phone_type  phone_type,
    contact_confidence  NUMERIC(3,2),
    -- Assignment
    assigned_rep_id     UUID REFERENCES app_user(id),
    assigned_at         TIMESTAMPTZ,
    -- Outreach tracking
    total_call_attempts INTEGER NOT NULL DEFAULT 0,
    total_sms_sent      INTEGER NOT NULL DEFAULT 0,
    total_emails_sent   INTEGER NOT NULL DEFAULT 0,
    last_contacted_at   TIMESTAMPTZ,
    last_disposition     TEXT,
    -- Scores
    discovery_score     INTEGER,              -- copied from discovered_lead
    activation_score    INTEGER,
    -- Meta
    activated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_lead_org_status ON lead(organization_id, status);
CREATE INDEX idx_lead_rep ON lead(assigned_rep_id);
CREATE INDEX idx_lead_disc ON lead(discovered_lead_id);
CREATE INDEX idx_lead_score ON lead(organization_id, discovery_score DESC);

-- ============================================================
-- LEAD SCORE (ACTIVATION-LEVEL)
-- ============================================================

CREATE TABLE lead_score (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id             UUID NOT NULL REFERENCES lead(id),
    model_version       TEXT NOT NULL DEFAULT 'v1',
    total_score         INTEGER NOT NULL,
    -- Factors
    contact_confidence  INTEGER NOT NULL DEFAULT 0,   -- /25
    phone_quality       INTEGER NOT NULL DEFAULT 0,   -- /20
    email_quality       INTEGER NOT NULL DEFAULT 0,   -- /15
    compliance_ready    INTEGER NOT NULL DEFAULT 0,   -- /25
    risk_level          INTEGER NOT NULL DEFAULT 0,   -- /15
    factor_details_json JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_ls_lead ON lead_score(lead_id);

-- ============================================================
-- DISTRIBUTION
-- ============================================================

CREATE TYPE distribution_method AS ENUM (
    'round_robin', 'weighted', 'geographic', 'manual', 'ai_recommended'
);

CREATE TABLE distribution_assignment (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organization(id),
    lead_id         UUID NOT NULL REFERENCES lead(id),
    assigned_to     UUID NOT NULL REFERENCES app_user(id),
    method          distribution_method NOT NULL,
    reason          TEXT,
    assigned_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    accepted_at     TIMESTAMPTZ,
    rejected_at     TIMESTAMPTZ,
    rejection_reason TEXT
);

CREATE INDEX idx_da_lead ON distribution_assignment(lead_id);
CREATE INDEX idx_da_rep ON distribution_assignment(assigned_to);

-- ============================================================
-- OUTREACH + CONVERSATIONS
-- (Extends existing SolarCommand tables — shown here for completeness)
-- ============================================================

CREATE TYPE contact_channel AS ENUM ('voice', 'sms', 'email');
CREATE TYPE contact_disposition AS ENUM (
    'pending', 'in_progress',
    'appointment_booked', 'callback_scheduled',
    'interested_not_ready', 'not_interested',
    'voicemail_left', 'no_answer', 'busy', 'wrong_number',
    'opted_out', 'do_not_call', 'failed', 'skipped'
);

CREATE TABLE outreach_attempt (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id     UUID NOT NULL REFERENCES organization(id),
    lead_id             UUID NOT NULL REFERENCES lead(id),
    channel             contact_channel NOT NULL,
    disposition         contact_disposition NOT NULL DEFAULT 'pending',
    -- Call detail
    external_call_id    TEXT,
    duration_seconds    INTEGER,
    recording_url       TEXT,
    transcript          TEXT,
    -- SMS/Email detail
    message_body        TEXT,
    template_id         TEXT,
    -- Compliance snapshot
    compliance_check_json JSONB,              -- gates passed at time of attempt
    consent_event_id    UUID REFERENCES consent_event(id),
    -- Meta
    scheduled_at        TIMESTAMPTZ,
    started_at          TIMESTAMPTZ,
    completed_at        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_oa_lead ON outreach_attempt(lead_id);
CREATE INDEX idx_oa_org_status ON outreach_attempt(organization_id, disposition);

CREATE TYPE message_direction AS ENUM ('inbound', 'outbound');

CREATE TABLE message_thread (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id     UUID NOT NULL REFERENCES organization(id),
    lead_id             UUID NOT NULL REFERENCES lead(id),
    direction           message_direction NOT NULL,
    channel             contact_channel NOT NULL,
    body                TEXT NOT NULL,
    -- AI classification (inbound)
    ai_intent           TEXT,
    ai_suggested_reply  TEXT,
    ai_actions          JSONB,
    ai_confidence       NUMERIC(3,2),
    -- Meta
    external_id         TEXT,                 -- twilio SID etc.
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_mt_lead ON message_thread(lead_id, created_at);

CREATE TABLE conversation_transcript (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id     UUID NOT NULL REFERENCES organization(id),
    lead_id             UUID NOT NULL REFERENCES lead(id),
    outreach_attempt_id UUID REFERENCES outreach_attempt(id),
    -- Content
    transcript_text     TEXT,
    ai_summary          TEXT,
    ai_sentiment        TEXT,
    -- Provider
    provider            TEXT,
    call_sid            TEXT,
    recording_url       TEXT,
    call_status         TEXT,
    duration_seconds    INTEGER,
    -- Meta
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_ct_lead ON conversation_transcript(lead_id);

-- ============================================================
-- QA + NBA + OBJECTIONS
-- (Same as existing SolarCommand, adapted for new lead table)
-- ============================================================

CREATE TABLE qa_review (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id     UUID NOT NULL REFERENCES organization(id),
    lead_id             UUID NOT NULL REFERENCES lead(id),
    transcript_id       UUID REFERENCES conversation_transcript(id),
    compliance_score    INTEGER NOT NULL,     -- 0-100
    checklist_pass      BOOLEAN NOT NULL,
    flags               JSONB NOT NULL DEFAULT '[]',
    rationale           TEXT,
    reviewer            TEXT DEFAULT 'ai',
    ai_run_id           UUID,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TYPE nba_action AS ENUM (
    'call', 'sms', 'email', 'wait', 'rep_handoff', 'nurture', 'close'
);

CREATE TABLE nba_decision (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id     UUID NOT NULL REFERENCES organization(id),
    lead_id             UUID NOT NULL REFERENCES lead(id),
    action              nba_action NOT NULL,
    channel             contact_channel,
    schedule_at         TIMESTAMPTZ,
    reason_codes        TEXT[] NOT NULL DEFAULT '{}',
    confidence          NUMERIC(3,2),
    expires_at          TIMESTAMPTZ,
    ai_run_id           UUID,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE objection_tag (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id     UUID NOT NULL REFERENCES organization(id),
    lead_id             UUID NOT NULL REFERENCES lead(id),
    transcript_id       UUID REFERENCES conversation_transcript(id),
    tag                 TEXT NOT NULL,
    confidence          NUMERIC(3,2) NOT NULL,
    evidence_span       TEXT,
    ai_run_id           UUID,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- APPOINTMENTS
-- ============================================================

CREATE TYPE appointment_status AS ENUM (
    'scheduled', 'confirmed', 'completed', 'no_show',
    'cancelled', 'rescheduled'
);

CREATE TABLE appointment (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organization(id),
    lead_id         UUID NOT NULL REFERENCES lead(id),
    rep_id          UUID NOT NULL REFERENCES app_user(id),
    status          appointment_status NOT NULL DEFAULT 'scheduled',
    scheduled_at    TIMESTAMPTZ NOT NULL,
    completed_at    TIMESTAMPTZ,
    address         TEXT,
    notes           TEXT,
    outcome         TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- AI AUDIT
-- ============================================================

CREATE TABLE ai_run (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organization(id),
    task_type       TEXT NOT NULL,
    model           TEXT NOT NULL,
    temperature     NUMERIC(3,2),
    prompt_version  TEXT,
    -- I/O
    input_json      JSONB NOT NULL,
    output_json     JSONB,
    -- Source citations
    source_record_ids UUID[] DEFAULT '{}',
    -- Cost
    tokens_in       INTEGER,
    tokens_out      INTEGER,
    cost_usd        NUMERIC(8,6),
    latency_ms      INTEGER,
    -- Status
    status          TEXT NOT NULL DEFAULT 'pending',
    error_message   TEXT,
    -- Refs
    lead_id         UUID,
    discovered_lead_id UUID,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_air_org ON ai_run(organization_id, created_at DESC);
CREATE INDEX idx_air_task ON ai_run(task_type);
CREATE INDEX idx_air_lead ON ai_run(lead_id);

-- ============================================================
-- AUDIT LOG (APPEND-ONLY)
-- ============================================================

CREATE TABLE audit_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organization(id),
    actor_id        UUID REFERENCES app_user(id),
    actor_type      TEXT NOT NULL DEFAULT 'user',  -- "user", "system", "ai", "connector"
    action          TEXT NOT NULL,
    entity_type     TEXT NOT NULL,
    entity_id       UUID,
    old_value       JSONB,
    new_value       JSONB,
    metadata        JSONB,
    ip_address      INET,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_al_org ON audit_log(organization_id, created_at DESC);
CREATE INDEX idx_al_entity ON audit_log(entity_type, entity_id);

-- ============================================================
-- NOTES
-- ============================================================

CREATE TABLE note (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organization(id),
    lead_id         UUID REFERENCES lead(id),
    discovered_lead_id UUID REFERENCES discovered_lead(id),
    author_id       UUID REFERENCES app_user(id),
    body            TEXT NOT NULL,
    note_type       TEXT DEFAULT 'manual',    -- "manual", "ai_generated", "system"
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- SCRIPT MANAGEMENT + EXPERIMENTS
-- ============================================================

CREATE TABLE script_version (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organization(id),
    version_label   TEXT NOT NULL,
    channel         contact_channel NOT NULL,
    body            TEXT NOT NULL,
    is_active       BOOLEAN DEFAULT false,
    created_by      UUID REFERENCES app_user(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE script_experiment (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organization(id),
    name            TEXT NOT NULL,
    control_script_id UUID REFERENCES script_version(id),
    variant_script_id UUID REFERENCES script_version(id),
    status          TEXT DEFAULT 'active',
    control_sends   INTEGER DEFAULT 0,
    control_responses INTEGER DEFAULT 0,
    control_conversions INTEGER DEFAULT 0,
    variant_sends   INTEGER DEFAULT 0,
    variant_responses INTEGER DEFAULT 0,
    variant_conversions INTEGER DEFAULT 0,
    winner          TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at        TIMESTAMPTZ
);

-- ============================================================
-- AI MEMORY (ORGANIZATIONAL LEARNING)
-- ============================================================

CREATE TABLE ai_memory (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organization(id),
    scope           TEXT NOT NULL,            -- "global", "county:baltimore", "rep:uuid"
    key             TEXT NOT NULL,
    value           TEXT NOT NULL,
    meta_json       JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(organization_id, scope, key)
);
```

## Dedupe Strategy

**Address normalization pipeline:**
1. Uppercase all text
2. Expand abbreviations: ST→STREET, AVE→AVENUE, DR→DRIVE, etc.
3. Strip apartment/unit/suite designators for property-level dedupe
4. Remove extra whitespace
5. SHA-256 hash → `address_hash`

**Phone normalization:**
1. Strip all non-digits
2. If 10 digits, prepend +1
3. Validate E.164 format
4. SHA-256 hash → `value_hash` (for DNC matching without storing plaintext in flag tables)

**Property dedupe priority:** `parcel_id` (if available) > `address_hash` > geo-proximity (within 10m of existing point).

**Idempotency:** All mutation API endpoints accept an optional `Idempotency-Key` header. Keys are stored in Redis with 24-hour TTL. Duplicate requests return the original response.

---

# E) SCORING SYSTEM

## Layer 1: Discovery Score (Address-Level, 0-100)

Computed when a property is added to `discovered_lead`. Deterministic formula (no AI). Same inputs always produce same score.

| Factor | Max Points | Inputs | Logic |
|--------|-----------|--------|-------|
| **Roof Suitability** | 20 | `year_built`, `roof_area_sqft`, `building_sqft` | Roof age 20+yr: 15pts. Roof area ≥1500sqft: 5pts. Scale linearly for partial. |
| **Ownership Signal** | 15 | `owner_occupied`, `last_sale_date` | Owner-occupied: 10pts. Owned 3+yr: 5pts. |
| **Financial Capacity** | 15 | `assessed_value`, `median_household_income` | Value ≥$200k: 8pts. Income ≥$75k: 7pts. Scale linearly. |
| **Utility Economics** | 15 | `avg_rate_kwh`, `utility_rate_zone` | Rate ≥$0.14/kWh: 15pts. Scale linearly from $0.08. |
| **Solar Potential** | 15 | `has_existing_solar`, `tree_cover_pct`, `annual_ghi`, `south_facing_prob` | No existing solar: 5pts. Tree cover <30%: 5pts. GHI top quartile: 3pts. South-facing: 2pts. |
| **Permit Triggers** | 10 | `permit_record` joins | Roof permit <6mo: 10pts. Roof permit <12mo: 6pts. Electrical upgrade: 3pts. |
| **Neighborhood** | 10 | `neighborhood_solar_pct` | ≥30%: 10pts. Scale linearly from 0%. |

**Thresholds:**
- **Hot:** ≥ 75 (prioritize for immediate enrichment + activation)
- **Warm:** ≥ 50 (enrich in batch, activate if contact quality is high)
- **Cool:** < 50 (park; re-score if new data arrives)

**Explainability output:** Each factor stores points earned + reasoning in `factor_details_json`:

```json
{
  "roof_suitability": {
    "points": 17,
    "max": 20,
    "reasoning": "Roof age 24 years (15/15), roof area 1,340 sqft (2/5)",
    "sources": ["source_record:uuid1"]
  },
  "permit_triggers": {
    "points": 10,
    "max": 10,
    "reasoning": "Roof replacement permit issued 2026-01-15 (permit #BLT-2026-4821)",
    "sources": ["source_record:uuid2"]
  }
}
```

## Layer 2: Activation Score (Contact-Level, 0-100)

Computed after enrichment. Determines whether a discovered lead can be activated for outreach.

| Factor | Max Points | Inputs | Logic |
|--------|-----------|--------|-------|
| **Contact Confidence** | 25 | `contact_candidate.confidence` | Best phone confidence ≥0.8: 25pts. ≥0.6: 18pts. ≥0.4: 10pts. |
| **Phone Quality** | 20 | `phone_type`, `carrier_name`, `line_status` | Mobile: 15pts. Active line: 5pts. VoIP: 8pts. Landline: 5pts. |
| **Email Quality** | 15 | `email_deliverable`, `email_disposable` | Deliverable + not disposable: 15pts. Deliverable + disposable: 5pts. |
| **Compliance Ready** | 25 | `compliance_flag`, `consent_event` | No DNC flags: 15pts. Explicit consent: 10pts. Inferred: 5pts. Unknown: 0pts. |
| **Risk Level** | 15 | `compliance_flag` (litigation, fraud) | No litigation flag: 10pts. No fraud flag: 5pts. |

**Activation threshold:** ≥ 60 (configurable per org).

**Hard blockers (override score):**
- Any active `federal_dnc` or `state_dnc` flag → cannot activate
- `consent_status = opted_out` or `revoked` → cannot activate
- `phone_type = unknown` and no email → cannot activate (no contactable method)
- `known_litigator` flag → requires manual review

---

# F) AI LAYER

## Architecture

All AI calls route through a single `AIClient` class that:
1. Builds the prompt from templates + context
2. Injects organizational memory (RAG)
3. Sanitizes inputs (injection defense)
4. Calls Claude API
5. Parses structured JSON output
6. Logs to `ai_run` table (input, output, tokens, cost, latency, source citations)
7. Returns structured result or deterministic fallback

**Defaults:**
- Model: `claude-sonnet-4-5-20250929`
- Temperature: 0.2 (low variability for classification/scoring; 0.4 for creative tasks like script writing)
- Max tokens: 800
- Cost tracking: enabled by default

## Prompt 1: Inbound Message Intent Classifier

**When used:** Inbound SMS or email received from a lead.
**Temperature:** 0.2
**Deterministic first:** Before AI runs, check for opt-out keywords deterministically.

```
SYSTEM:
You are a message classifier for a solar energy company's lead management system.
Classify the inbound message from a homeowner prospect.

Rules:
- You MUST respond with valid JSON only. No other text.
- If the message contains ANY opt-out language (stop, unsubscribe, cancel,
  remove, do not contact, quit, end), classify as "opt_out" regardless of
  other content. This is a legal requirement.
- Never suggest replies that impersonate a government agency or utility company.
- Never suggest replies that make specific savings claims or guarantees.
- Never suggest replies that pressure or manipulate the recipient.
- If you are uncertain, set requires_human to true.
- Keep suggested_reply under 160 characters (1 SMS segment).

Output JSON schema:
{
  "intent": "opt_out|interested|question|not_interested|appointment_request|
             callback_request|wrong_number|greeting|unknown",
  "confidence": 0.0-1.0,
  "suggested_reply": "string or null",
  "actions": ["opt_out", "book_appointment", "rep_handoff", "update_status",
              "none"],
  "requires_human": true/false,
  "reasoning": "1-sentence explanation"
}

USER:
<lead_context>
  <name>{owner_first_name} {owner_last_name}</name>
  <property>{address_line1}, {city}, {state}</property>
  <status>{lead_status}</status>
  <last_outreach>{last_contacted_at}</last_outreach>
  <discovery_score>{discovery_score}/100</discovery_score>
  <prior_messages_count>{message_count}</prior_messages_count>
</lead_context>

<inbound_message>
  <from>{from_phone}</from>
  <body>{sanitized_message_body}</body>
  <received_at>{timestamp}</received_at>
</inbound_message>

Classify this message.
```

**Deterministic fallback (if AI unavailable):**
```python
def classify_deterministic(body: str) -> dict:
    body_lower = body.strip().lower()
    OPT_OUT = {"stop", "unsubscribe", "cancel", "remove", "quit", "end",
               "do not contact", "opt out", "optout"}
    if any(kw in body_lower for kw in OPT_OUT):
        return {"intent": "opt_out", "confidence": 1.0,
                "actions": ["opt_out"], "requires_human": False}
    INTERESTED = {"yes", "interested", "tell me more", "how much",
                  "sounds good", "info", "information"}
    if any(kw in body_lower for kw in INTERESTED):
        return {"intent": "interested", "confidence": 0.6,
                "actions": ["rep_handoff"], "requires_human": True}
    return {"intent": "unknown", "confidence": 0.0,
            "actions": ["none"], "requires_human": True}
```

## Prompt 2: Rep Brief Generator

**When used:** Rep requests a brief before contacting a lead.
**Temperature:** 0.3

```
SYSTEM:
You are a sales intelligence assistant for a solar energy company.
Generate a concise pre-call brief for a sales representative.

Rules:
- Base your brief ONLY on the data provided. Do not invent facts.
- Cite which data source informed each point (use source labels provided).
- Never suggest the rep impersonate a utility or government agency.
- Never suggest specific dollar savings — say "potential savings" instead.
- Never suggest high-pressure tactics.
- If data is sparse, say so. Do not fill gaps with assumptions.
- Keep the brief under 300 words total.

Output JSON schema:
{
  "summary": "2-3 sentence lead summary",
  "talk_track": ["point 1", "point 2", "point 3"],
  "likely_objections": [
    {"objection": "string", "handler": "string"}
  ],
  "recommended_approach": "string",
  "risk_factors": ["string"],
  "key_facts": [
    {"fact": "string", "source": "source_label"}
  ],
  "data_gaps": ["string"]
}

USER:
<lead_profile>
  <name>{owner_first_name} {owner_last_name}</name>
  <property>
    <address>{full_address}</address>
    <type>{property_type}</type>
    <year_built>{year_built}</year_built>
    <assessed_value>{assessed_value}</assessed_value>
    <roof_area>{roof_area_sqft} sqft</roof_area>
    <existing_solar>{has_existing_solar}</existing_solar>
  </property>
  <solar_factors>
    <utility>{utility_name} — {avg_rate_kwh}¢/kWh</utility>
    <tree_cover>{tree_cover_pct}%</tree_cover>
    <neighborhood_solar>{neighborhood_solar_pct}%</neighborhood_solar>
    <annual_ghi>{annual_ghi} kWh/m²/yr</annual_ghi>
  </solar_factors>
  <scores>
    <discovery_score>{discovery_score}/100</discovery_score>
    <score_breakdown>{factor_details_summary}</score_breakdown>
  </scores>
  <permits>{permit_summary}</permits>
  <outreach_history>{outreach_summary}</outreach_history>
  <prior_objections>{objection_tags}</prior_objections>
  <source_labels>{source_labels_json}</source_labels>
</lead_profile>

<org_memory>
{relevant_ai_memory_entries}
</org_memory>

Generate the rep brief.
```

## Prompt 3: BYOD Data Mapping Assistant

**When used:** User uploads a CSV and the system needs to map columns to the schema.
**Temperature:** 0.1 (highly deterministic)

```
SYSTEM:
You are a data mapping assistant. Given CSV column headers and sample values,
map them to the target schema fields.

Rules:
- Map ONLY columns that clearly correspond to target fields.
- If a column is ambiguous, set confidence to "low" and suggest but do not
  auto-map.
- Never guess PII mappings (phone, email, name) — require high confidence.
- If a column looks like it contains sensitive data not in the target schema
  (SSN, credit score, etc.), flag it as "sensitive_exclude" — do not import.
- Respond with valid JSON only.

Target fields:
address_line1, address_line2, city, state, zip_code, county,
parcel_id, property_type, year_built, building_sqft, lot_size_sqft,
roof_area_sqft, assessed_value, owner_first_name, owner_last_name,
owner_phone, owner_email, utility_zone, has_existing_solar,
tree_cover_pct, owner_occupied

Output JSON schema:
{
  "mappings": [
    {
      "source_column": "string",
      "target_field": "string or null",
      "confidence": "high|medium|low",
      "reasoning": "string"
    }
  ],
  "unmapped_columns": ["string"],
  "sensitive_columns": ["string"],
  "warnings": ["string"]
}

USER:
<csv_headers>{headers_list}</csv_headers>
<sample_rows>{first_3_rows_json}</sample_rows>

Map these columns to the target schema.
```

## Prompt 4: Source Quality Evaluator

**When used:** After connector ingestion, evaluate a batch of source records for quality.
**Temperature:** 0.1

```
SYSTEM:
You are a data quality evaluator for a lead generation system.
Evaluate the quality and reliability of a batch of ingested records.

Rules:
- Assess completeness, consistency, freshness, and accuracy signals.
- Flag records that appear fabricated, duplicated, or anomalous.
- Flag records where the stated source does not match the data characteristics.
- Score the batch 0-100 on overall quality.
- Be conservative: if something looks off, flag it.
- Respond with valid JSON only.

Output JSON schema:
{
  "batch_quality_score": 0-100,
  "total_records": integer,
  "flagged_records": [
    {
      "record_index": integer,
      "issue": "string",
      "severity": "info|warning|critical"
    }
  ],
  "quality_summary": "2-3 sentence assessment",
  "recommendations": ["string"]
}

USER:
<batch_metadata>
  <source>{source_name}</source>
  <license>{license_type}</license>
  <record_count>{count}</record_count>
  <ingestion_time>{timestamp}</ingestion_time>
</batch_metadata>
<sample_records>{first_10_records_json}</sample_records>
<field_statistics>{field_completeness_stats}</field_statistics>

Evaluate this batch.
```

## Prompt Injection Defenses

All user-supplied values inserted into prompts are:
1. Truncated to maximum length (message body: 500 chars; addresses: 200 chars; names: 100 chars)
2. XML-escaped (`<`, `>`, `&`, `"`, `'`)
3. Scanned for injection patterns:
   - "ignore previous instructions"
   - "you are now"
   - "system:" / "assistant:" / "human:" tags
   - Base64-encoded blocks
   - Excessive repetition
4. If injection detected: the value is replaced with `[content filtered]` and the AI run is flagged.

## When to Use AI vs. Deterministic Rules

| Task | Method | Rationale |
|------|--------|-----------|
| Opt-out detection | Deterministic (keyword match) | Legal requirement — must be instant and reliable |
| DNC scrub | Deterministic (hash lookup) | Cannot afford false negatives |
| Quiet hours check | Deterministic (time comparison) | Binary rule, no ambiguity |
| Consent tier check | Deterministic (policy lookup) | Policy-driven, not judgment |
| Scoring (discovery) | Deterministic (weighted formula) | Explainable, auditable, no variability |
| Scoring (activation) | Deterministic (weighted formula) | Same rationale |
| SMS intent classification | AI with deterministic pre-check | Opt-out caught deterministically first; AI handles nuance |
| Rep brief | AI | Creative synthesis, needs context |
| NBA recommendation | AI with deterministic hard stops | Terminal/protected statuses enforced first; AI reasons over active leads |
| QA review | AI | Requires understanding conversation context |
| BYOD column mapping | AI | Handles non-standard column names |
| Permit classification | AI | Free-text descriptions need NLP |
| Source quality evaluation | AI | Pattern detection over data |
| Script suggestions | AI | Creative, requires pattern analysis |

---

# G) COMPLIANCE ENGINE

## TCPA Policy Configuration

Per-organization, per-state rules stored in `organization.settings_json`:

```yaml
# Default compliance policy — conservative
compliance:
  # Quiet hours (all times in org timezone)
  quiet_hours:
    voice:
      weekday:  { start: "09:00", end: "20:00" }
      saturday: { start: "10:00", end: "17:00" }
      sunday:   null  # no calls
    sms:
      weekday:  { start: "09:00", end: "21:00" }
      saturday: { start: "10:00", end: "18:00" }
      sunday:   null  # no SMS
    email:
      weekday:  { start: "08:00", end: "21:00" }
      saturday: { start: "09:00", end: "18:00" }
      sunday:   { start: "10:00", end: "17:00" }

  # State-specific overrides
  state_overrides:
    FL:
      voice:
        weekday: { start: "08:00", end: "21:00" }  # Florida allows 8am
    CA:
      sms:
        require_explicit_consent: true  # California stricter on SMS

  # Attempt limits (per channel, per lead, rolling 30 days)
  max_attempts:
    voice: 3
    sms: 3
    email: 5

  # Channel escalation order
  channel_priority: ["voice", "sms", "email"]

  # Consent requirements per channel
  consent_requirements:
    voice:
      minimum_consent: "inferred"    # at minimum inferred consent required
      explicit_required_states: ["CA", "FL"]
    sms:
      minimum_consent: "inferred"
      explicit_required_states: ["CA"]
    email:
      minimum_consent: "unknown"     # CAN-SPAM allows with opt-out

  # DNC scrubbing
  dnc:
    federal_dnc_enabled: true
    state_dnc_enabled: true
    internal_dnc_enabled: true
    scrub_before_activation: true
    scrub_before_outreach: true      # double-check at outreach time

  # Opt-out
  opt_out:
    keywords: ["stop", "unsubscribe", "cancel", "remove", "quit",
               "end", "opt out", "optout", "do not contact",
               "take me off", "no more"]
    auto_confirm: true               # auto-send confirmation message
    confirmation_message: "You have been opted out and will not be contacted again. If this was a mistake, reply START."
    process_before_ai: true          # deterministic, before AI classification

  # AI safety
  ai:
    auto_actions_enabled: false      # suggest-only by default
    sms_auto_reply_enabled: false
    require_human_approval:
      - "place_voice_call"
      - "send_sms"
      - "activate_lead"
```

## Compliance Check Flow

Called synchronously before any outreach action:

```python
def check_compliance(lead, channel, org_config) -> ComplianceResult:
    """
    Returns: ComplianceResult(allowed=bool, reasons=[], warnings=[])
    ALL checks must pass. Any failure = blocked.
    """
    reasons = []
    warnings = []

    # 1. Lead status check
    TERMINAL = {"closed_won", "closed_lost", "dnc", "disqualified", "archived"}
    if lead.status in TERMINAL:
        reasons.append(f"lead_status_terminal:{lead.status}")

    # 2. DNC check (hash-based lookup)
    flags = get_active_flags(lead.contact_phone_hash)
    for f in flags:
        if f.flag_type in ("federal_dnc", "state_dnc", "internal_dnc"):
            reasons.append(f"dnc_flag:{f.flag_type}")
        if f.flag_type == "known_litigator":
            reasons.append("known_litigator")
        if f.flag_type == "litigation_risk":
            warnings.append("litigation_risk")

    # 3. Consent check
    consent = get_latest_consent(lead.contact_phone_hash, channel)
    if consent.status in ("opted_out", "revoked"):
        reasons.append("opted_out")
    min_required = org_config.consent_requirements[channel].minimum_consent
    state_explicit = lead.state in org_config.consent_requirements[channel].explicit_required_states
    if state_explicit and consent.status != "explicit_opt_in":
        reasons.append(f"explicit_consent_required:{lead.state}")
    elif min_required == "inferred" and consent.status == "unknown":
        reasons.append("no_consent")

    # 4. Quiet hours check
    now_local = now_in_timezone(org_config.timezone)
    window = get_quiet_hours(channel, now_local.weekday(), org_config)
    if window is None:
        reasons.append(f"quiet_hours:no_{channel}_on_{now_local.strftime('%A')}")
    elif not (window.start <= now_local.time() <= window.end):
        reasons.append(f"quiet_hours:outside_window")

    # 5. Attempt limit check
    attempts = count_recent_attempts(lead.id, channel, days=30)
    max_allowed = org_config.max_attempts[channel]
    if attempts >= max_allowed:
        reasons.append(f"max_attempts:{channel}:{attempts}/{max_allowed}")

    # 6. Contact method exists
    if channel == "voice" and not lead.contact_phone:
        reasons.append("no_phone_number")
    if channel == "email" and not lead.contact_email:
        reasons.append("no_email_address")

    allowed = len(reasons) == 0
    return ComplianceResult(allowed=allowed, reasons=reasons, warnings=warnings)
```

## Opt-Out Detection

**Deterministic, runs before AI classification:**

```python
OPT_OUT_KEYWORDS = frozenset([
    "stop", "unsubscribe", "cancel", "remove", "quit", "end",
    "opt out", "optout", "do not contact", "take me off",
    "no more", "leave me alone", "not interested"
])

def is_opt_out(message_body: str) -> bool:
    normalized = message_body.strip().lower()
    # Exact match for single-word messages
    if normalized in OPT_OUT_KEYWORDS:
        return True
    # Substring match for multi-word messages
    for kw in OPT_OUT_KEYWORDS:
        if kw in normalized:
            return True
    return False
```

When opt-out is detected:
1. Create `consent_event` with `consent_status=opted_out`, `evidence_method=sms_keyword`
2. Send confirmation message (if `auto_confirm=true`)
3. Create `compliance_flag` with `flag_type=internal_dnc`
4. Update lead status to `dnc`
5. Log to `audit_log`

## Dispute Evidence Trail

If a lead disputes that they were contacted or claims they opted out, the system provides:

1. **Source provenance:** Which data source provided the lead, when, with what license
2. **Consent history:** Every consent event with method, timestamp, and evidence
3. **Compliance snapshot:** The `compliance_check_json` stored on each `outreach_attempt` — the exact state of all gates at the moment of contact
4. **Communication log:** Every message sent and received, with timestamps
5. **Recording + transcript:** If voice call, with disclosure confirmation
6. **QA review:** Compliance score and checklist for the conversation
7. **Audit log:** Every system action related to this lead

---

# H) LEAD GENERATION WORKFLOWS

## Pipeline 1: Nightly Discovery Ingest

**Schedule:** 2:00 AM org timezone, daily

```
Step 1: For each active data_source_config
  │
  ├─ Acquire distributed lock: "connector:{source_id}" (TTL 30min)
  ├─ Call connector.fetch_new_records(since=last_sync_at)
  │   ├─ Retry: 3 attempts, exponential backoff (30s, 60s, 120s)
  │   ├─ Rate limit: per connector config
  │   └─ On failure: log error, release lock, skip to next source
  │
  ├─ For each raw record:
  │   ├─ Normalize address → address_hash
  │   ├─ Create source_record (raw_record_json, evidence_fields)
  │   ├─ Upsert property (dedupe on parcel_id or address_hash)
  │   │   ├─ If new: create property
  │   │   └─ If existing: merge fields (newer source wins for each field)
  │   └─ Audit log: "property_upserted"
  │
  ├─ Update data_source_config.last_sync_at, records_synced
  └─ Release lock
```

**Failure modes:**
- Connector timeout → retry with backoff; after 3 failures, mark source as `sync_failed`, alert ops
- Duplicate records → upsert handles gracefully; source_record still created for provenance
- Malformed data → skip record, log to `audit_log` with `action=record_skipped`
- Lock contention → skip this source this cycle; will run next cycle

## Pipeline 2: Feature Extraction + Discovery Scoring

**Schedule:** 3:00 AM daily (after ingest completes)

```
Step 1: Find properties without a discovered_lead or with stale scores
  │
  ├─ Query: properties where discovered_lead is null
  │   OR discovered_lead.discovery_score IS NULL
  │   OR property.updated_at > discovered_lead.updated_at
  │
  ├─ Batch size: 500 per run (configurable)
  │
  ├─ For each property:
  │   ├─ Join permit_records (category in roof/electrical, issued <12mo)
  │   ├─ Lookup utility rate from utility_territory spatial join
  │   ├─ Lookup demographics from census tract
  │   ├─ Compute discovery score (deterministic formula)
  │   │
  │   ├─ Upsert discovered_lead
  │   │   ├─ status = 'scored'
  │   │   ├─ discovery_score = computed
  │   │   ├─ discovery_reason = top factors summary
  │   │   ├─ source_record_ids = all sources used
  │   │   └─ discovery_batch = "nightly_YYYY-MM-DD"
  │   │
  │   └─ Create discovery_score record (full breakdown)
  │
  └─ Audit log: "discovery_scoring_batch_completed"
```

## Pipeline 3: Enrichment

**Schedule:** 4:00 AM daily (for batch); also on-demand via API

```
Step 1: Find discovered_leads eligible for enrichment
  │
  ├─ Criteria:
  │   ├─ discovery_score >= org.enrichment_threshold (default: 50)
  │   ├─ enrichment_attempted = false
  │   └─ status in ('scored')
  │
  ├─ Batch size: min(org.max_daily_lookups, 200) per run
  ├─ Sort: discovery_score DESC (enrich best leads first)
  │
  ├─ For each discovered_lead:
  │   ├─ Build search query: owner_name + address + any known phone/email
  │   │
  │   ├─ Call PDL API (rate-limited, with retry)
  │   │   ├─ On 429: backoff, requeue
  │   │   ├─ On 402 (credits): stop batch, alert ops
  │   │   └─ On success: filter by confidence >= threshold
  │   │
  │   ├─ For each result above threshold:
  │   │   ├─ Create contact_candidate (phone or email)
  │   │   ├─ Create source_record for enrichment result
  │   │   └─ If phone: queue Melissa/Twilio validation
  │   │
  │   ├─ Call Melissa API for phone/email validation
  │   │   ├─ Update contact_candidate: validated, phone_type, carrier
  │   │   └─ Create source_record for validation result
  │   │
  │   ├─ Select best_phone, best_email (highest confidence + validated)
  │   ├─ Update discovered_lead:
  │   │   ├─ enrichment_attempted = true
  │   │   ├─ enrichment_at = now
  │   │   ├─ best_phone, best_email, best_contact_confidence
  │   │   └─ status = 'enriched'
  │   │
  │   └─ Audit log: "lead_enriched"
  │
  └─ Cost tracking: log total PDL + Melissa costs
```

**Failure modes:**
- PDL returns no match → mark `enrichment_attempted=true`, status stays `scored` (can retry with different search params later)
- Melissa timeout → validation stays `false`, lead can still activate with lower score
- Credit limit hit → stop batch gracefully, alert via webhook/email

## Pipeline 4: Activation Gating

**Schedule:** 5:00 AM daily (for batch); also on-demand via API with human approval

```
Step 1: Find discovered_leads ready for activation
  │
  ├─ Criteria:
  │   ├─ status = 'enriched'
  │   ├─ best_contact_confidence >= org.min_contact_confidence (default: 0.5)
  │   └─ best_phone IS NOT NULL OR best_email IS NOT NULL
  │
  ├─ For each candidate:
  │   ├─ Compute activation_score (deterministic)
  │   │
  │   ├─ Check hard blockers:
  │   │   ├─ DNC scrub (federal + state + internal)
  │   │   ├─ Known litigator check
  │   │   └─ Deceased flag check
  │   │
  │   ├─ If blocked: status = 'rejected', rejection_reason = reason
  │   │
  │   ├─ If activation_score >= threshold AND no blockers:
  │   │   ├─ If org requires manual approval:
  │   │   │   └─ status = 'activation_ready' (appears in approval queue)
  │   │   ├─ Else (auto-activate enabled):
  │   │   │   ├─ Create lead record
  │   │   │   ├─ Create lead_score record
  │   │   │   ├─ Create initial consent_event (type based on source)
  │   │   │   ├─ discovered_lead.status = 'activated'
  │   │   │   ├─ Queue for distribution
  │   │   │   └─ Audit log: "lead_activated"
  │   │   └─ End
  │   │
  │   └─ If score < threshold: status stays 'enriched' (may improve with new data)
  │
  └─ Audit log: "activation_gating_batch_completed"
```

## Pipeline 5: Lead Distribution

**Schedule:** Continuous (event-driven on lead activation)

```
Step 1: New lead activated → distribution_queue event
  │
  ├─ Load org distribution config:
  │   ├─ method: round_robin | weighted | geographic | manual
  │   ├─ rep_availability: check is_active, not over capacity
  │   └─ geographic_rules: county/zip → rep mapping
  │
  ├─ Select rep:
  │   ├─ Round robin: next rep in rotation (skip unavailable)
  │   ├─ Weighted: weighted random by rep.weight (account for performance)
  │   ├─ Geographic: match lead county/zip to rep territory
  │   └─ Manual: place in unassigned queue for manager
  │
  ├─ Create distribution_assignment
  ├─ Update lead: assigned_rep_id, status = 'assigned'
  ├─ Audit log: "lead_distributed"
  │
  └─ Optional: send notification to rep (webhook / in-app)
```

## Pipeline 6: Outreach Orchestration

**Schedule:** Every 1 minute (process pending outreach); also on-demand

```
Step 1: Check for leads due for outreach
  │
  ├─ Query: leads with status in ('assigned', 'contacting', 'contacted', 'nurturing')
  │   WHERE nba_decision.schedule_at <= now
  │   OR (status = 'assigned' AND no outreach_attempt exists)
  │
  ├─ For each lead:
  │   ├─ Run compliance check (synchronous, all gates)
  │   │   ├─ If blocked: log reason, skip, audit
  │   │   └─ If allowed: proceed
  │   │
  │   ├─ Select channel (from NBA recommendation or escalation logic):
  │   │   ├─ If NBA exists and not expired: use NBA.channel
  │   │   └─ Else: escalation order (voice → sms → email)
  │   │       filtered by quiet hours and attempt limits
  │   │
  │   ├─ Create outreach_attempt (status=pending)
  │   ├─ Store compliance_check_json on attempt
  │   │
  │   ├─ Execute:
  │   │   ├─ Voice: queue task_place_voice_call
  │   │   ├─ SMS: queue task_send_sms
  │   │   └─ Email: queue task_send_email
  │   │
  │   ├─ Update lead: status = 'contacting', last_contacted_at = now
  │   └─ Audit log: "outreach_initiated"
  │
  └─ Post-completion:
      ├─ Update outreach_attempt with disposition
      ├─ Increment lead counters (total_call_attempts, etc.)
      ├─ Queue AI post-processing (summary, QA, objections)
      └─ Queue NBA recomputation
```

## Pipeline 7: Feedback Loop

**Schedule:** Weekly (Monday 7:00 AM)

```
Step 1: Aggregate outcomes from past 7 days
  │
  ├─ By discovery_score band: what % activated? appointed? closed?
  ├─ By source: which data sources produce leads that convert?
  ├─ By county/zip: geographic performance patterns
  ├─ By permit type: do roof permits actually predict conversion?
  │
  ├─ Feed aggregated metrics to AI memory update:
  │   ├─ "county:baltimore → 82% of hot leads from tax+permit combo"
  │   ├─ "objection:too_expensive appears 40% in howard_county"
  │   └─ "source:byod_upload has 30% lower activation rate than tax_assessor"
  │
  ├─ Store in ai_memory (scope: global, county, source, rep)
  │
  ├─ Generate weekly insights narrative (AI)
  │
  └─ Flag scoring factors that underperform expectations:
      ├─ If permit_triggers has <5% lift vs baseline: reduce weight in v2
      └─ Log recommendation for scoring model review
```

**No PII in feedback loop:** All aggregations are at cohort level (county, score band, source type). Individual lead data is not written to ai_memory.

---

# I) API SURFACE

## Authentication

- JWT tokens (HS256, configurable secret)
- Token lifetime: 480 minutes (8 hours)
- All endpoints require `Authorization: Bearer {token}` except `/auth/login` and `/health`
- RBAC: `owner` > `admin` > `manager` > `rep` > `ops` > `readonly`

## Endpoints

### Auth
```
POST   /auth/login                    # email + password → JWT
GET    /auth/me                       # current user profile
POST   /auth/register                 # admin+ only
```

### Data Sources
```
POST   /sources/register              # register a new data source config
  Body: { name, source_type, license, connector_class, config_json, cadence }
  Auth: admin+
  Response: { id, name, source_type, status }

GET    /sources                       # list configured sources
  Query: ?active=true
  Auth: manager+

POST   /sources/{id}/sync             # trigger manual sync
  Auth: admin+
  Response: { sync_id, status: "queued" }

GET    /sources/{id}/status           # sync history + stats
  Auth: manager+

DELETE /sources/{id}                  # deactivate source
  Auth: admin+
```

### Ingestion (BYOD)
```
POST   /ingest/upload                 # upload CSV/Excel file
  Body: multipart/form-data { file, source_name, license_declaration, consent_basis }
  Auth: manager+
  Response: { upload_id, status, column_headers, sample_rows }

POST   /ingest/upload/{id}/mapping    # confirm column mapping
  Body: { mappings: [{ source_column, target_field }], consent_type }
  Auth: manager+
  Response: { records_parsed, records_valid, records_skipped, errors }

POST   /ingest/upload/{id}/confirm    # commit ingestion
  Auth: manager+
  Response: { properties_created, properties_updated, discovered_leads_created }

POST   /ingest/property               # single property ingestion (API)
  Body: { address, parcel_id, owner_name, ... }
  Auth: ops+
  Headers: Idempotency-Key
```

### Properties
```
GET    /properties                    # list/search properties
  Query: ?county=X&zip=Y&min_value=Z&has_permits=true&bbox=lat1,lng1,lat2,lng2
  Auth: rep+
  Pagination: ?page=1&per_page=25

GET    /properties/{id}               # full property detail + source records
  Auth: rep+

GET    /properties/{id}/sources       # source provenance chain
  Auth: rep+
```

### Discovery
```
GET    /discovered                    # list discovered leads
  Query: ?status=scored&min_score=75&county=X&batch=Y&sort=score_desc
  Auth: rep+
  Pagination: ?page=1&per_page=25

GET    /discovered/{id}               # full discovered lead detail
  Auth: rep+
  Response: { lead, property, score_breakdown, contact_candidates, compliance_flags }

POST   /discovered/{id}/score         # trigger scoring (if not auto-scored)
  Auth: ops+

POST   /discovered/{id}/enrich        # trigger on-demand enrichment
  Auth: manager+

POST   /discovered/batch/score        # batch scoring
  Body: { filters: { county, min_quality_score }, max_count: 500 }
  Auth: admin+

POST   /discovered/batch/enrich       # batch enrichment
  Body: { filters: { min_score, max_count }, provider: "pdl" }
  Auth: admin+
```

### Activation
```
GET    /activate/queue                # leads pending manual activation
  Query: ?min_discovery_score=75&min_activation_score=60
  Auth: manager+

POST   /activate/{discovered_lead_id} # activate a discovered lead → lead
  Body: { consent_basis: "inferred|explicit", consent_evidence: "..." }
  Auth: manager+
  Response: { lead_id, status, assigned_rep_id }

POST   /activate/{discovered_lead_id}/reject
  Body: { reason: "string" }
  Auth: manager+

POST   /activate/batch                # batch activate
  Body: { discovered_lead_ids: [...], consent_basis, consent_evidence }
  Auth: admin+
```

### Leads (Activated)
```
GET    /leads                         # list activated leads
  Query: ?status=X&rep_id=Y&min_score=Z&county=W
  Auth: rep+
  Pagination: ?page=1&per_page=25

GET    /leads/{id}                    # full lead detail
  Auth: rep+
  Response: { lead, property, scores, outreach_history, messages,
              nba, objections, consent_history, compliance_flags, notes }

PATCH  /leads/{id}/status             # manual status update
  Body: { status, reason }
  Auth: rep+

PATCH  /leads/{id}/assign             # assign/reassign rep
  Body: { rep_id }
  Auth: manager+

POST   /leads/{id}/notes              # add note
  Body: { body }
  Auth: rep+

GET    /leads/{id}/notes              # list notes
  Auth: rep+
```

### Enrichment
```
GET    /enrich/{discovered_lead_id}   # get enrichment results
  Auth: rep+

POST   /enrich/{discovered_lead_id}/run  # trigger enrichment
  Body: { providers: ["pdl", "melissa"] }
  Auth: manager+

GET    /enrich/stats                  # enrichment stats (lookups, costs, yield)
  Auth: admin+
```

### Distribution
```
GET    /distribution/config           # get distribution rules
  Auth: admin+

PUT    /distribution/config           # update distribution rules
  Body: { method, rep_weights, geographic_rules }
  Auth: admin+

GET    /distribution/queue            # unassigned leads
  Auth: manager+

POST   /distribution/{lead_id}/assign # manual assignment
  Body: { rep_id, reason }
  Auth: manager+
```

### Outreach
```
POST   /outreach/{lead_id}/enqueue    # queue next outreach action
  Auth: rep+

GET    /outreach/{lead_id}/attempts   # list outreach attempts
  Auth: rep+

POST   /outreach/{lead_id}/voice      # place voice call
  Auth: rep+

POST   /outreach/{lead_id}/sms        # send SMS
  Body: { message }
  Auth: rep+

GET    /outreach/{lead_id}/messages   # message thread
  Auth: rep+

GET    /outreach/{lead_id}/recordings # voice recordings + transcripts
  Auth: rep+

GET    /outreach/{lead_id}/qa         # QA reviews
  Auth: rep+

GET    /outreach/{lead_id}/nba        # latest NBA decision
  Auth: rep+

POST   /outreach/{lead_id}/nba/recompute  # trigger NBA recomputation
  Auth: rep+
```

### Compliance
```
GET    /compliance/config             # org compliance policy
  Auth: admin+

PUT    /compliance/config             # update compliance policy
  Body: { quiet_hours, max_attempts, consent_requirements, ... }
  Auth: owner+

POST   /compliance/check              # check compliance for a lead + channel
  Body: { lead_id, channel }
  Auth: rep+
  Response: { allowed, reasons, warnings }

GET    /compliance/{lead_id}/consent  # consent history
  Auth: rep+

POST   /compliance/{lead_id}/consent  # record consent event
  Body: { consent_type, consent_status, evidence_method, evidence_detail }
  Auth: rep+

GET    /compliance/dnc/check          # check a phone against DNC
  Body: { phone }
  Auth: ops+

POST   /compliance/dnc/upload         # upload DNC list
  Body: multipart/form-data { file }
  Auth: admin+

GET    /compliance/{lead_id}/evidence # full dispute evidence package
  Auth: admin+
```

### Appointments
```
POST   /appointments                  # book appointment
  Body: { lead_id, rep_id, scheduled_at, address, notes }
  Auth: rep+

GET    /appointments                  # list appointments
  Query: ?rep_id=X&status=Y&date_from=Z&date_to=W
  Auth: rep+

PATCH  /appointments/{id}             # update appointment status
  Body: { status, outcome, notes }
  Auth: rep+
```

### Dashboard
```
GET    /dashboard/kpis                # org-wide KPIs
  Auth: rep+
  Response: { total_properties, total_discovered, total_activated,
              total_leads, appointments, by_score_band, by_status,
              by_source, enrichment_yield, connect_rate, cost_summary }

GET    /dashboard/insights            # AI weekly insights
  Auth: rep+

GET    /dashboard/discovery-map       # GeoJSON for map view
  Query: ?bbox=X&min_score=Y&status=Z
  Auth: rep+
  Response: GeoJSON FeatureCollection
```

### Admin
```
GET    /admin/audit-log               # browse audit log
  Query: ?entity_type=X&actor_id=Y&action=Z&from=D1&to=D2
  Auth: admin+
  Pagination: ?page=1&per_page=50

GET    /admin/ai/runs                 # list AI runs
  Query: ?task_type=X&status=Y&lead_id=Z
  Auth: admin+

GET    /admin/ai/runs/{id}            # full AI run detail (input/output)
  Auth: admin+

GET    /admin/ai/stats                # AI stats (runs, cost, errors, latency)
  Auth: admin+

GET    /admin/scripts                 # list script versions
  Auth: manager+

POST   /admin/scripts                 # create script version
  Body: { version_label, channel, body }
  Auth: admin+

GET    /admin/experiments             # list A/B experiments
  Auth: admin+

POST   /admin/experiments             # create experiment
  Body: { name, control_script_id, variant_script_id }
  Auth: admin+

GET    /admin/reps                    # list reps + performance stats
  Auth: manager+
```

### Webhooks (Inbound)
```
POST   /webhooks/sms                  # Twilio inbound SMS
  Verification: HMAC-SHA256 signature
  Rate limit: 60/min per IP

POST   /webhooks/voice/status         # voice call status callback
  Verification: signature or API key

POST   /webhooks/voice/recording      # recording ready callback
  Verification: signature or API key
```

### Health
```
GET    /health                        # service health
  No auth required
  Response: { status, service, version, db_ok, redis_ok, timestamp }
```

---

# J) FRONTEND UX

## Critical Screens

### 1. Data Source Setup Wizard (`/admin/sources/new`)

**Purpose:** Configure a new data connector or BYOD upload.

**Flow:**
1. Select source type (dropdown: Tax Assessor, Permits, Utility, BYOD Upload, Vendor Feed)
2. For BYOD: upload file → AI suggests column mapping → user confirms → preview → commit
3. For connectors: fill config form (county, API key, cadence) → test connection → activate
4. Declare license type and consent basis

**Components:** StepWizard, FileUpload, ColumnMappingTable, ConnectionTestStatus

### 2. Discovery Dashboard (`/discovery`)

**Purpose:** See all discovered properties, filter, and prioritize.

**Layout:**
- **Left panel:** Map view (Mapbox GL) showing properties as dots colored by score (red=hot, orange=warm, blue=cool). Click dot → property popup.
- **Right panel:** List/table view with columns: Address, County, Score, Status, Top Factors, Source, Created. Sortable, filterable.
- **Top bar:** Filters (county, score range, status, source, permit type, date range)
- **Bulk actions:** "Enrich Selected", "Activate Selected" (with confirmation)

**Components:** MapView, PropertyMarker, ScoreFilterSlider, DiscoveryTable, BulkActionBar

### 3. Activation Queue (`/activation`)

**Purpose:** Review and approve/reject leads for outreach.

**Layout:**
- Table: Name, Address, Discovery Score, Activation Score, Best Phone (masked), Phone Type, DNC Status, Consent Status, Source
- Each row expandable to show score breakdown, contact candidates, compliance flags
- Action buttons: Approve (single), Reject (with reason), Approve All Visible
- Filters: min discovery score, min activation score, county, source

**Components:** ActivationTable, ScoreBreakdownCard, ComplianceStatusBadge, RejectReasonModal

### 4. Lead Detail (`/leads/{id}`)

**Purpose:** Full command center for an activated lead.

**Layout:** (Extends existing SolarCommand lead detail page)
- **Header:** Name, status badge, discovery score, activation score, assigned rep, source badge
- **Left column:**
  - Property Details (address, type, year built, roof area, value, utility zone)
  - Score Breakdown (10 discovery factors with progress bars)
  - Source Provenance (which datasets contributed which fields, with timestamps)
  - Permit History (linked permits with dates and categories)
  - Outreach Timeline
  - Voice Recordings + QA
- **Right column:**
  - NBA Card
  - AI Rep Brief
  - Objections
  - Contact Info + Enrichment Badges
  - Consent History
  - Compliance Status
  - Notes

**Components:** PropertyCard, ScoreBreakdown, SourceProvenanceChain, PermitTimeline, NBACard, RepBriefCard, ComplianceStatusCard

### 5. Outreach Timeline (`/leads/{id}` — tab or inline)

**Purpose:** See all communication with a lead.

**Layout:** Vertical timeline showing:
- Outreach attempts (voice/sms/email) with disposition badges
- Inbound messages with AI intent classification
- AI suggested replies (with "Use this reply" button)
- Recordings with playback, AI summary, sentiment
- QA reviews with scores and flags

### 6. Admin Screens

**AI Runs** (`/admin/ai-runs`): Stats dashboard + filterable table + drill-down. Same as existing but with source_record_ids displayed as citation links.

**Audit Log** (`/admin/audit`): Filterable table of all system actions. Filter by entity type, actor, action, date range.

**Scripts** (`/admin/scripts`): Version list with A/B experiment status.

**Experiments** (`/admin/experiments`): Side-by-side control/variant metrics.

**Sources** (`/admin/sources`): List of configured connectors with sync status, record counts, last sync time, error badges.

## Design System (Minimal)

**Colors:**
- Primary: Solar amber/orange (existing)
- Score bands: Red (#EF4444) = Hot, Orange (#F97316) = Warm, Blue (#3B82F6) = Cool
- Compliance: Green (#22C55E) = Clear, Red (#EF4444) = Blocked, Yellow (#EAB308) = Warning
- Source types: Distinct muted colors per source type (for map + badges)

**Components:**
- `Badge` — status, score tier, channel, source type, compliance
- `ScoreBar` — horizontal progress bar with label (points/max)
- `MapView` — Mapbox GL JS with cluster + dot rendering
- `ProvenanceChain` — vertical list linking data point → source_record → data_source
- `ComplianceGate` — visual checklist (pass/fail per gate)
- `TimelineEvent` — card in vertical timeline with icon, timestamp, content
- `DataTable` — sortable, filterable, paginated table with row expansion
- `StepWizard` — multi-step form with progress indicator

---

# K) EVALUATION + TEST PLAN

## Unit Tests

```
tests/
├── test_scoring/
│   ├── test_discovery_score.py      # all 10 factors, edge cases, boundary values
│   ├── test_activation_score.py     # all 5 factors, hard blockers
│   └── test_score_determinism.py    # same inputs → same outputs, always
├── test_compliance/
│   ├── test_quiet_hours.py          # every day/time combination, timezone edge cases
│   ├── test_dnc_scrub.py            # hash matching, flag types, expiry
│   ├── test_opt_out_detection.py    # all keywords, partial matches, edge cases
│   ├── test_consent_tiers.py        # explicit, inferred, unknown, per-state
│   └── test_attempt_limits.py       # rolling window, per-channel
├── test_dedupe/
│   ├── test_address_normalization.py # abbreviations, whitespace, apt/suite
│   ├── test_phone_normalization.py   # formats, E.164, hashing
│   └── test_property_dedupe.py      # parcel_id priority, address fallback
├── test_connectors/
│   ├── test_tax_assessor.py         # parse, normalize, dedupe
│   ├── test_permit_connector.py     # classification, address matching
│   └── test_byod_upload.py          # column mapping, validation, error handling
├── test_activation/
│   ├── test_gating_logic.py         # all gate combinations
│   └── test_hard_blockers.py        # DNC, litigator, deceased
├── test_ai/
│   ├── test_prompt_sanitization.py  # injection patterns, truncation, escaping
│   ├── test_deterministic_fallbacks.py  # every AI task has a fallback
│   └── test_cost_tracking.py        # token counting, cost calculation
└── test_distribution/
    ├── test_round_robin.py          # rotation, skip unavailable
    └── test_geographic_routing.py   # county/zip matching
```

## Integration Tests (Mocked Connectors)

```
tests/integration/
├── test_discovery_pipeline.py       # ingest → score → discover (mocked data source)
├── test_enrichment_pipeline.py      # discover → enrich → contact_candidates (mocked PDL/Melissa)
├── test_activation_pipeline.py      # enrich → gate → activate → lead (mocked DNC)
├── test_outreach_pipeline.py        # activate → distribute → outreach (mocked Twilio)
├── test_full_lifecycle.py           # CSV upload → ... → appointment (all mocked externals)
└── test_compliance_enforcement.py   # verify gates block at every stage
```

## Load Test Assumptions

- Target: 10,000 properties ingested per nightly batch
- Target: 2,000 enrichment lookups per day
- Target: 500 activation decisions per day
- Target: 200 concurrent active leads in outreach
- Target: API response time p95 < 500ms for reads, < 2s for writes
- Target: Scoring batch completes within 15 minutes for 10,000 properties

## A/B Testing Strategy

**Scripts:** `script_experiment` table tracks control vs variant across sends, responses, conversions. Assignment is round-robin by lead_id modulo. Minimum sample: 200 per arm before declaring winner. Statistical significance: 95% confidence interval on conversion rate.

**Routing:** Test distribution methods (round robin vs weighted vs geographic) by assigning organizations to cohorts. Track cost-per-appointment by cohort.

**Scoring:** Version scoring models (v1, v2). Run both in parallel on same leads. Compare activation rate and downstream conversion. Promote winner after 30-day observation.

## Key Metrics

| Metric | Definition | Target |
|--------|-----------|--------|
| Cost per discovered lead | (data source costs + compute) / properties discovered | < $0.05 |
| Cost per activated lead | (enrichment + validation + AI) / leads activated | < $0.50 |
| Cost per appointment | (all costs) / appointments booked | < $15 |
| Enrichment yield | leads with valid phone / leads enriched | > 60% |
| Connect rate | calls connected / calls placed | > 20% |
| Opt-out rate | opt-outs / leads contacted | < 5% |
| Compliance flag rate | flagged QA reviews / total reviews | < 10% |
| Activation rate | leads activated / leads discovered (hot+warm) | > 40% |
| Discovery-to-appointment | appointments / leads discovered | > 2% |

---

# L) SECURITY + INFRASTRUCTURE

## Secrets Management

- **Development:** `.env` file (git-ignored)
- **Production:** Environment variables injected by platform (Render, AWS ECS, etc.)
- **Sensitive keys:** `JWT_SECRET`, `ANTHROPIC_API_KEY`, `TWILIO_AUTH_TOKEN`, `PDL_API_KEY`, `MELISSA_API_KEY`, database credentials
- **Rotation:** JWT secret rotated quarterly. API keys rotated on personnel change.
- **Never logged:** API keys, tokens, and password hashes are excluded from audit_log values and AI run inputs.

## Webhook Verification

- **Twilio SMS/Voice:** HMAC-SHA256 signature verification using `TWILIO_AUTH_TOKEN`
- **Custom webhooks:** API key in `X-Webhook-Secret` header, compared against `WEBHOOK_API_KEY`
- **All webhooks:** Rate-limited (60/min per IP), request body size limited (1MB)

## CORS + Rate Limiting

```python
# CORS
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

# Rate limiting (per endpoint group)
RATE_LIMITS = {
    "auth": "10/minute",        # login attempts
    "webhooks": "60/minute",    # per IP
    "api_read": "120/minute",   # per user
    "api_write": "30/minute",   # per user
    "enrichment": "10/minute",  # per org (cost control)
    "ai": "20/minute",          # per org (cost control)
}
```

## Request Validation

- All inputs validated via Pydantic models
- String lengths capped (addresses: 500 chars, message bodies: 2000 chars, names: 200 chars)
- UUID parameters validated as UUID format
- Pagination: max `per_page=100`
- File uploads: max 50MB, allowed types: `.csv`, `.xlsx`

## Docker Compose

```yaml
services:
  db:
    image: postgis/postgis:16-3.4-alpine  # PostGIS instead of plain Postgres
    ports: ["5432:5432"]
    environment:
      POSTGRES_USER: solar
      POSTGRES_PASSWORD: solar
      POSTGRES_DB: solarcommand
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./infrastructure/init.sql:/docker-entrypoint-initdb.d/init.sql
    deploy:
      resources:
        limits: { memory: 512M }
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U solar"]
      interval: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    deploy:
      resources:
        limits: { memory: 256M }
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s

  api:
    build: ./backend
    ports: ["8000:8000"]
    depends_on:
      db: { condition: service_healthy }
      redis: { condition: service_healthy }
    environment:
      DATABASE_URL: postgresql+asyncpg://solar:solar@db:5432/solarcommand
      DATABASE_URL_SYNC: postgresql://solar:solar@db:5432/solarcommand
      REDIS_URL: redis://redis:6379/0
    env_file: .env
    deploy:
      resources:
        limits: { memory: 1G }
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      retries: 3
    restart: unless-stopped

  worker:
    build: ./backend
    command: celery -A app.workers.celery_app worker --loglevel=info --beat
    depends_on:
      db: { condition: service_healthy }
      redis: { condition: service_healthy }
    environment:
      DATABASE_URL_SYNC: postgresql://solar:solar@db:5432/solarcommand
      REDIS_URL: redis://redis:6379/0
    env_file: .env
    deploy:
      resources:
        limits: { memory: 1G }
    healthcheck:
      test: ["CMD", "celery", "-A", "app.workers.celery_app", "inspect", "ping"]
      interval: 30s
      retries: 3
    restart: unless-stopped

  connector-worker:
    build: ./backend
    command: celery -A app.workers.celery_app worker --loglevel=info -Q connectors
    depends_on:
      db: { condition: service_healthy }
      redis: { condition: service_healthy }
    environment:
      DATABASE_URL_SYNC: postgresql://solar:solar@db:5432/solarcommand
      REDIS_URL: redis://redis:6379/0
    env_file: .env
    deploy:
      resources:
        limits: { memory: 1G }
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    depends_on:
      api: { condition: service_healthy }
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
      NEXT_PUBLIC_MAPBOX_TOKEN: ${MAPBOX_TOKEN}
    deploy:
      resources:
        limits: { memory: 1G }
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:3000"]
      interval: 30s
    restart: unless-stopped

volumes:
  pgdata:
```

## Observability

**Structured logging:**
```python
import structlog
logger = structlog.get_logger()
logger.info("lead_activated",
    lead_id=str(lead.id),
    discovery_score=lead.discovery_score,
    activation_score=activation_score,
    source_count=len(lead.source_record_ids),
    org_id=str(org.id))
```

**Dashboards (Grafana or equivalent):**
- Discovery pipeline: properties ingested/day, score distribution, source health
- Enrichment: lookups/day, yield rate, cost/day, provider error rates
- Activation: activated/day, rejected/day, rejection reasons
- Outreach: attempts/day, connect rate, disposition breakdown
- Compliance: blocks/day, opt-outs/day, QA flag rate
- AI: runs/day, error rate, p95 latency, cost/day
- Infrastructure: API response times, worker queue depth, DB connections

**Alerting:**
- Connector sync failure (2 consecutive) → ops alert
- Enrichment provider error rate > 10% → ops alert
- Compliance flag rate > 15% → compliance officer alert
- AI error rate > 5% → engineering alert
- Daily cost exceeds org budget → admin alert
- Worker queue depth > 1000 → infrastructure alert

## Data Retention + PII

- **Audit log:** Retained indefinitely (append-only, required for compliance disputes)
- **AI runs:** Retained 2 years (regulatory requirement assumption)
- **Source records:** Retained as long as derived data exists
- **Outreach recordings:** Retained per org policy (default 1 year)
- **Soft-deleted leads:** PII scrubbed after 90 days, metadata retained for analytics
- **Phone/email hashes:** Retained in compliance_flag for DNC matching even after lead deletion
- **Encryption at rest:** Database volume encrypted (platform-level)
- **Encryption in transit:** TLS 1.2+ on all connections

---

# M) IMPLEMENTATION PLAN

## Phase 1: BYOD Ingestion + Discovery Scoring + Evidence Trails (Weeks 1-3)

**Deliverables:**
- Multi-tenant schema: `organization`, `app_user`, `source_record`, `property`, `discovered_lead`, `discovery_score`, `audit_log`
- BYOD upload endpoint with AI column mapping
- Address normalization + deduplication
- 10-factor discovery scoring (deterministic)
- Source provenance chain (every data point traces to source_record)
- Discovery dashboard (list view, score breakdown, source badges)
- Audit log for all mutations

**Acceptance criteria:**
- Upload a CSV → properties created with source_records → scored → visible in dashboard
- Same CSV uploaded twice → no duplicates, source_records still created
- Score breakdown is deterministic and explainable
- Audit log shows every action

**Risks:**
- Address normalization edge cases (rural addresses, PO boxes) → mitigate with fallback to raw address + manual review flag
- AI column mapping inaccuracy → mitigate with human confirmation step

## Phase 2: Connectors + Enrichment + Activation Gate (Weeks 4-7)

**Deliverables:**
- Connector framework (base class, registry, health monitoring)
- Tax assessor connector (1-2 counties for pilot)
- Building permits connector (1-2 jurisdictions)
- Utility territory spatial join (PostGIS)
- Solar suitability proxy pipeline
- PDL + Melissa enrichment integration
- Contact candidate model with confidence scoring
- Activation score (5-factor)
- Activation gate (compliance checks, hard blockers)
- Activation queue UI (approve/reject)
- DNC upload + scrubbing
- Map view (Mapbox GL) on discovery dashboard

**Acceptance criteria:**
- Nightly connector sync ingests properties from configured counties
- Permits are classified and linked to properties
- Enrichment returns phone/email with confidence scores
- Activation gate blocks DNC leads, low-confidence contacts, no-consent leads
- Map shows properties colored by score

**Risks:**
- County data format variability → mitigate with per-county connector config + BYOD fallback
- Enrichment yield too low → mitigate with multiple provider fallback (PDL → FullContact → skip)
- PostGIS learning curve → mitigate with simple point-in-polygon queries first

## Phase 3: Outreach + Compliance + Full Audit (Weeks 8-11)

**Deliverables:**
- Compliance engine (TCPA policy config, quiet hours, consent tiers, attempt limits)
- Outreach orchestration (channel selection, escalation, scheduling)
- Voice integration (Twilio) with safety gates
- SMS integration with inbound processing
- AI post-processing pipeline (summary, QA, objections, NBA)
- Lead distribution (round-robin, geographic)
- Lead detail page (full command center)
- Outreach timeline UI
- AI Runs admin page
- Consent tracking UI
- Webhook handlers (SMS, voice status, recording)

**Acceptance criteria:**
- Outreach blocked for DNC/opted-out/quiet-hours leads (verified by integration tests)
- Inbound SMS opt-out processed deterministically within 1 second
- Every AI call logged with full I/O in ai_run table
- QA review runs on every conversation
- Compliance evidence package exportable for any lead

**Risks:**
- Twilio webhook reliability → mitigate with idempotent handlers + retry logic
- AI latency impacting UX → mitigate with async processing + polling UI pattern

## Phase 4: Optimization + Experiments + ML (Weeks 12-16)

**Deliverables:**
- Feedback loop pipeline (outcome → scoring model evaluation)
- AI memory / organizational learning
- Script A/B testing
- Distribution A/B testing
- Scoring model v2 (if data supports re-weighting)
- Weekly insights narrative
- Performance dashboards (cost per lead, per appointment, connect rate)
- Additional connectors (3-5 more counties, vendor feeds)
- Batch operations at scale (10K+ properties)

**Acceptance criteria:**
- Weekly insights reference actual performance data
- A/B test results show statistically significant differences at 95% CI
- Scoring v2 outperforms v1 on activation rate + downstream conversion
- System handles 10K property ingestion in < 15 minutes

**Risks:**
- Insufficient outcome data for ML → mitigate with longer observation period, use rule-based v1 longer
- A/B test sample sizes too small → mitigate with org-level (not lead-level) experiments for routing

---

# N) "BEST POSSIBLE" ENHANCEMENTS

## 1. GIS Map-Based Targeting
- Draw a polygon on the map → discover all properties within
- "Find properties similar to my best closed deals" → spatial + attribute query
- Heatmap overlay: score density, permit activity, neighborhood adoption rate
- Territory management: assign reps to geographic zones visually

## 2. Permit-Based Triggers
- Real-time monitoring: new roof permit filed → instant high-priority lead
- "Permit pulse" alerts: notify rep within hours of permit issuance
- Permit chain analysis: electrical upgrade → solar readiness signal
- Contractor network: if a known solar-friendly roofer pulled the permit, boost score

## 3. Neighborhood Adoption Modeling
- Calculate solar adoption % per census block group (from permit data + satellite imagery where licensed)
- Social proof scoring: "7 of your neighbors have gone solar" — verified from permit records
- Adoption trend: is the neighborhood accelerating or plateauing?
- Tipping point detection: neighborhoods approaching 15-20% adoption show fastest growth

## 4. Contact Graph Dedupe
- Link properties to the same owner across counties (investor detection)
- Detect property management companies (owner mailing address ≠ property address pattern)
- Household-level dedupe: multiple properties, one decision-maker
- Cross-org dedupe (opt-in): prevent multiple orgs from hammering the same lead

## 5. Multi-Touch Attribution
- Track which data source → which discovery → which outreach → which appointment → which close
- Source ROI: "Tax assessor data produces 3x more appointments per dollar than BYOD uploads"
- Channel attribution: "Voice after SMS produces 2x more appointments than voice-first"
- Time-to-conversion by discovery score band

## 6. Human-in-the-Loop Review Queues
- AI confidence < threshold → routes to human review queue
- Borderline activation decisions → manager approval required
- Flagged QA reviews → compliance officer review queue
- Anomalous source data → data quality analyst review
- Configurable thresholds per org risk tolerance

## 7. Fraud / Abuse Detection
- Detect properties that appear in multiple BYOD uploads from different sources with conflicting data
- Flag phone numbers associated with known TCPA litigator databases
- Detect potential "lead recycling" (same property re-ingested to reset attempt counts)
- Rate anomaly detection: sudden spike in opt-outs from a batch → flag source quality issue
- Honeypot numbers: internal test numbers that should never be dialed; alert if attempted

## 8. Predictive Scoring (ML)
- Once sufficient outcome data exists (500+ closed deals), train a gradient-boosted model
- Features: all discovery score factors + enrichment quality + outreach patterns + temporal signals
- Output: probability of appointment + probability of close
- Maintain deterministic v1 as baseline; ML as v2 with A/B validation
- Model cards: document training data, features, performance metrics, fairness analysis

## 9. Seasonal + Event Triggers
- Monitor utility rate increase announcements → boost scores in affected territories
- Storm/weather events → roof damage leads (with appropriate sensitivity)
- Tax credit / incentive changes → score adjustment for affected states
- New housing development permits → pre-populate properties before owners move in

## 10. White-Label + API-First
- Multi-tenant with org-level branding (logo, colors, domain)
- Full API for embedding lead intelligence into existing CRMs
- Webhook subscriptions: "notify me when a lead scores > 80 in my territory"
- Embeddable map widget for partner websites

---

# APPENDIX: Assumptions Made

| # | Assumption | Rationale |
|---|-----------|-----------|
| 1 | US-only market initially | TCPA/DNC framework is US-specific; international compliance differs |
| 2 | Solar is primary but schema supports other home services | Property-level signals (roof, utility, permits) apply to roofing, HVAC, etc. |
| 3 | Single timezone per org | Simplifies quiet hours; multi-timezone orgs use state overrides |
| 4 | Tax assessor data is public record | True in all 50 states; some charge for bulk access |
| 5 | Building permits are public record | True in most jurisdictions; some require FOIA |
| 6 | NREL/Census/EIA data is freely available | Confirmed; all are public federal datasets |
| 7 | Microsoft Building Footprints is CC-BY-4.0 | Confirmed; open for commercial use with attribution |
| 8 | PDL/Melissa terms permit outreach use case | Must verify per vendor agreement; marked as assumption |
| 9 | Google Sunroof is NOT used | Terms prohibit automated access; we use open alternatives |
| 10 | MLS data requires licensing | True universally; connector exists but requires license verification |
| 11 | 2-year data retention for AI runs | Conservative estimate pending legal review |
| 12 | Minimum 500 outcomes for ML scoring | Standard ML minimum for meaningful signal; use rules until then |
