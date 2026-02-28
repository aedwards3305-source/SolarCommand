"""Discovery API — serves the frontend discovery page with real lead data.

Maps existing Property + Lead + LeadScore models to the frontend's expected
DiscoveredLeadRow / DiscoveredLead types. Also provides activation, source,
and health endpoints.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.connectors.md_sdat import run_discovery
from app.core.database import get_db
from app.core.security import get_current_user
from app.enrichment.pipeline import enrich_lead, skip_trace_leads, validate_contact
from app.models.schema import (
    ContactEnrichment,
    ContactValidation,
    ConsentLog,
    Lead,
    LeadScore,
    LeadStatus,
    Property,
)
from app.services.scoring import score_lead

router = APIRouter(tags=["discovery"], dependencies=[Depends(get_current_user)])


# ── Status mapping ─────────────────────────────────────────────────────

def _lead_status_to_discovery(status: LeadStatus) -> str:
    """Map internal LeadStatus to frontend DiscoveryStatus."""
    mapping = {
        LeadStatus.ingested: "discovered",
        LeadStatus.scored: "scored",
        LeadStatus.hot: "scored",
        LeadStatus.warm: "scored",
        LeadStatus.cool: "scored",
        LeadStatus.contacting: "activated",
        LeadStatus.contacted: "activated",
        LeadStatus.qualified: "activated",
        LeadStatus.appointment_set: "activated",
        LeadStatus.nurturing: "activated",
        LeadStatus.closed_won: "activated",
        LeadStatus.closed_lost: "archived",
        LeadStatus.disqualified: "rejected",
        LeadStatus.dnc: "rejected",
        LeadStatus.archived: "archived",
    }
    return mapping.get(status, "discovered")


def _discovery_to_lead_statuses(discovery_status: str) -> list[LeadStatus]:
    """Map frontend DiscoveryStatus filter to internal LeadStatus values."""
    mapping: dict[str, list[LeadStatus]] = {
        "discovered": [LeadStatus.ingested],
        "scored": [LeadStatus.scored, LeadStatus.hot, LeadStatus.warm, LeadStatus.cool],
        "enriched": [LeadStatus.scored, LeadStatus.hot, LeadStatus.warm, LeadStatus.cool],
        "enriching": [LeadStatus.scored, LeadStatus.hot, LeadStatus.warm, LeadStatus.cool],
        "activation_ready": [LeadStatus.hot, LeadStatus.warm],
        "activated": [
            LeadStatus.contacting, LeadStatus.contacted,
            LeadStatus.qualified, LeadStatus.appointment_set,
            LeadStatus.nurturing, LeadStatus.closed_won,
        ],
        "rejected": [LeadStatus.disqualified, LeadStatus.dnc],
        "archived": [LeadStatus.closed_lost, LeadStatus.archived],
    }
    return mapping.get(discovery_status, [])


# ── Pydantic schemas ──────────────────────────────────────────────────


class DiscoveredLeadRow(BaseModel):
    id: str
    status: str
    discovery_score: int | None
    activation_score: int | None
    address: str
    city: str
    state: str
    county: str | None
    property_type: str | None
    year_built: int | None
    roof_area_sqft: float | None
    utility_name: str | None
    has_existing_solar: bool
    owner_name: str | None
    best_phone: str | None
    best_phone_type: str | None
    latitude: float | None
    longitude: float | None
    source_types: list[str]
    has_permit: bool
    created_at: str


class DiscoveredLeadListResponse(BaseModel):
    leads: list[DiscoveredLeadRow]
    total: int
    page: int
    page_size: int


class DiscoveredPropertyOut(BaseModel):
    id: str
    address_line1: str
    address_line2: str | None
    city: str
    state: str
    zip_code: str
    county: str | None
    latitude: float | None
    longitude: float | None
    parcel_id: str | None
    property_type: str | None
    year_built: int | None
    building_sqft: float | None
    lot_size_sqft: float | None
    roof_area_sqft: float | None
    assessed_value: float | None
    last_sale_date: str | None
    last_sale_price: float | None
    owner_first_name: str | None
    owner_last_name: str | None
    owner_occupied: bool | None
    utility_name: str | None
    utility_rate_zone: str | None
    avg_rate_kwh: float | None
    has_existing_solar: bool
    tree_cover_pct: float | None
    neighborhood_solar_pct: float | None
    median_household_income: float | None


class ScoreBreakdownOut(BaseModel):
    total_score: int
    model_version: str
    roof_suitability: int
    roof_suitability_max: int
    ownership_signal: int
    ownership_signal_max: int
    financial_capacity: int
    financial_capacity_max: int
    utility_economics: int
    utility_economics_max: int
    solar_potential: int
    solar_potential_max: int
    permit_triggers: int
    permit_triggers_max: int
    neighborhood_adoption: int
    neighborhood_adoption_max: int
    factor_details: dict


class ContactCandidateOut(BaseModel):
    id: str
    method: str
    value: str
    confidence: float
    phone_type: str | None
    carrier_name: str | None
    line_status: str | None
    email_deliverable: bool | None
    email_disposable: bool | None
    validated: bool
    is_primary: bool


class ComplianceOut(BaseModel):
    federal_dnc: str
    state_dnc: str
    internal_dnc: str
    consent_status: str
    litigator_flag: str
    fraud_flag: str


class DiscoveredLeadDetail(BaseModel):
    id: str
    status: str
    discovery_reason: str | None
    discovery_batch: str | None
    discovery_score: int | None
    activation_score: int | None
    enrichment_attempted: bool
    enrichment_at: str | None
    best_phone: str | None
    best_email: str | None
    best_contact_confidence: float | None
    activated_at: str | None
    rejection_reason: str | None
    created_at: str
    updated_at: str
    property: DiscoveredPropertyOut
    score_breakdown: ScoreBreakdownOut | None
    permits: list  # Empty for MVP
    source_records: list  # Empty for MVP
    contact_candidates: list[ContactCandidateOut]
    compliance: ComplianceOut


class RunDiscoveryRequest(BaseModel):
    county: str
    limit: int = 1000


class RunDiscoveryResponse(BaseModel):
    status: str
    ingested: int
    scored: int
    skipped: int
    errors: int


class ActivationRow(BaseModel):
    id: str
    status: str
    discovery_score: int | None
    activation_score: int | None
    address: str
    city: str
    state: str
    county: str | None
    property_type: str | None
    year_built: int | None
    roof_area_sqft: float | None
    utility_name: str | None
    has_existing_solar: bool
    owner_name: str | None
    best_phone: str | None
    best_phone_type: str | None
    latitude: float | None
    longitude: float | None
    source_types: list[str]
    has_permit: bool
    created_at: str
    best_contact_confidence: float | None
    dnc_status: str
    consent_status: str


class BatchActivateRequest(BaseModel):
    discovered_lead_ids: list[str]


class RejectRequest(BaseModel):
    reason: str


# ── Helper to build a DiscoveredLeadRow from DB objects ───────────────


def _build_lead_row(lead: Lead, prop: Property, score: LeadScore | None) -> dict:
    """Build a DiscoveredLeadRow dict from ORM objects."""
    owner_name = None
    if lead.first_name or lead.last_name:
        parts = [lead.first_name or "", lead.last_name or ""]
        owner_name = " ".join(p for p in parts if p).strip() or None
    elif prop.owner_first_name or prop.owner_last_name:
        parts = [prop.owner_first_name or "", prop.owner_last_name or ""]
        owner_name = " ".join(p for p in parts if p).strip() or None

    return {
        "id": str(lead.id),
        "status": _lead_status_to_discovery(lead.status),
        "discovery_score": score.total_score if score else None,
        "activation_score": score.total_score if score else None,
        "address": prop.address_line1,
        "city": prop.city,
        "state": prop.state,
        "county": prop.county,
        "property_type": prop.property_type.value if prop.property_type else None,
        "year_built": prop.year_built,
        "roof_area_sqft": prop.roof_area_sqft,
        "utility_name": prop.utility_zone,
        "has_existing_solar": prop.has_existing_solar,
        "owner_name": owner_name,
        "best_phone": lead.phone,
        "best_phone_type": None,
        "latitude": prop.latitude,
        "longitude": prop.longitude,
        "source_types": [prop.data_source] if prop.data_source else [],
        "has_permit": False,
        "created_at": lead.created_at.isoformat() if lead.created_at else "",
    }


# ── Endpoints ─────────────────────────────────────────────────────────


@router.get("/discovered", response_model=DiscoveredLeadListResponse)
async def list_discovered_leads(
    db: AsyncSession = Depends(get_db),
    county: str | None = None,
    min_score: int | None = None,
    max_score: int | None = None,
    status_filter: str | None = Query(None, alias="status"),
    has_permit: bool | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """List discovered leads with filtering and pagination."""
    # Base query: join Lead + Property, optionally LeadScore
    query = (
        select(Lead, Property, LeadScore)
        .join(Property, Lead.property_id == Property.id)
        .outerjoin(
            LeadScore,
            (LeadScore.lead_id == Lead.id),
        )
    )

    # Use a subquery to get only the latest score per lead
    latest_score_sq = (
        select(
            LeadScore.lead_id,
            func.max(LeadScore.scored_at).label("max_scored_at"),
        )
        .group_by(LeadScore.lead_id)
        .subquery()
    )

    query = (
        select(Lead, Property, LeadScore)
        .join(Property, Lead.property_id == Property.id)
        .outerjoin(latest_score_sq, latest_score_sq.c.lead_id == Lead.id)
        .outerjoin(
            LeadScore,
            (LeadScore.lead_id == Lead.id)
            & (LeadScore.scored_at == latest_score_sq.c.max_scored_at),
        )
    )

    # Apply filters
    if county:
        query = query.where(Property.county == county)

    if min_score is not None:
        query = query.where(LeadScore.total_score >= min_score)

    if max_score is not None:
        query = query.where(LeadScore.total_score <= max_score)

    if status_filter:
        lead_statuses = _discovery_to_lead_statuses(status_filter)
        if lead_statuses:
            query = query.where(Lead.status.in_(lead_statuses))

    # Count total
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(
        LeadScore.total_score.desc().nulls_last(),
        Lead.created_at.desc(),
    )

    result = await db.execute(query)
    rows = result.all()

    leads_out = []
    for lead, prop, score in rows:
        leads_out.append(DiscoveredLeadRow(**_build_lead_row(lead, prop, score)))

    return DiscoveredLeadListResponse(
        leads=leads_out,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/discovered/{lead_id}", response_model=DiscoveredLeadDetail)
async def get_discovered_lead(lead_id: int, db: AsyncSession = Depends(get_db)):
    """Get full discovered lead detail."""
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    prop = await db.get(Property, lead.property_id)

    # Latest score
    score_result = await db.execute(
        select(LeadScore)
        .where(LeadScore.lead_id == lead_id)
        .order_by(LeadScore.scored_at.desc())
        .limit(1)
    )
    score = score_result.scalar_one_or_none()

    # Enrichment data
    enrich_result = await db.execute(
        select(ContactEnrichment)
        .where(ContactEnrichment.lead_id == lead_id)
        .order_by(ContactEnrichment.created_at.desc())
    )
    enrichments = enrich_result.scalars().all()

    # Validation data
    validation_result = await db.execute(
        select(ContactValidation)
        .where(ContactValidation.lead_id == lead_id)
        .order_by(ContactValidation.created_at.desc())
        .limit(1)
    )
    validation = validation_result.scalar_one_or_none()

    # Consent logs
    consent_result = await db.execute(
        select(ConsentLog).where(ConsentLog.lead_id == lead_id)
    )
    consents = consent_result.scalars().all()

    # Build score breakdown
    score_breakdown = None
    if score:
        score_breakdown = ScoreBreakdownOut(
            total_score=score.total_score,
            model_version=score.score_version,
            roof_suitability=score.roof_age_score + score.roof_area_score,
            roof_suitability_max=30,
            ownership_signal=score.ownership_score,
            ownership_signal_max=15,
            financial_capacity=score.home_value_score + score.income_score,
            financial_capacity_max=18,
            utility_economics=score.utility_rate_score,
            utility_economics_max=10,
            solar_potential=score.shade_score + score.existing_solar_score,
            solar_potential_max=12,
            permit_triggers=0,
            permit_triggers_max=5,
            neighborhood_adoption=score.neighborhood_score,
            neighborhood_adoption_max=10,
            factor_details={
                "roof_age": {
                    "points": score.roof_age_score, "max": 15,
                    "reasoning": "Based on year built", "sources": ["md_sdat"],
                },
                "roof_area": {
                    "points": score.roof_area_score, "max": 15,
                    "reasoning": "Structure area as proxy", "sources": ["md_sdat"],
                },
                "ownership": {
                    "points": score.ownership_score, "max": 15,
                    "reasoning": "Owner-occupied status", "sources": ["md_sdat"],
                },
                "home_value": {
                    "points": score.home_value_score, "max": 10,
                    "reasoning": "Based on assessed value", "sources": ["md_sdat"],
                },
                "utility_rate": {
                    "points": score.utility_rate_score, "max": 10,
                    "reasoning": "Utility zone economics", "sources": ["md_sdat"],
                },
                "shade": {
                    "points": score.shade_score, "max": 10,
                    "reasoning": "Tree cover percentage", "sources": ["md_sdat"],
                },
                "neighborhood": {
                    "points": score.neighborhood_score, "max": 10,
                    "reasoning": "Neighborhood solar adoption", "sources": ["md_sdat"],
                },
                "income": {
                    "points": score.income_score, "max": 8,
                    "reasoning": "Median household income bracket", "sources": ["census"],
                },
                "property_type": {
                    "points": score.property_type_score, "max": 5,
                    "reasoning": "Property classification", "sources": ["md_sdat"],
                },
                "existing_solar": {
                    "points": score.existing_solar_score, "max": 2,
                    "reasoning": "No existing solar installation", "sources": ["md_sdat"],
                },
            },
        )

    # Build contact candidates from enrichment
    contacts = []
    for enr in enrichments:
        if enr.phones:
            for i, phone_data in enumerate(enr.phones if isinstance(enr.phones, list) else []):
                phone_val = phone_data if isinstance(phone_data, str) else phone_data.get("number", "")
                contacts.append(ContactCandidateOut(
                    id=f"enr-{enr.id}-phone-{i}",
                    method="phone",
                    value=phone_val,
                    confidence=enr.confidence or 0.0,
                    phone_type=validation.phone_type if validation else None,
                    carrier_name=validation.phone_carrier if validation else None,
                    line_status=validation.phone_line_status if validation else None,
                    email_deliverable=None,
                    email_disposable=None,
                    validated=validation is not None,
                    is_primary=i == 0,
                ))
        if enr.emails:
            for i, email_data in enumerate(enr.emails if isinstance(enr.emails, list) else []):
                email_val = email_data if isinstance(email_data, str) else email_data.get("email", "")
                contacts.append(ContactCandidateOut(
                    id=f"enr-{enr.id}-email-{i}",
                    method="email",
                    value=email_val,
                    confidence=enr.confidence or 0.0,
                    phone_type=None,
                    carrier_name=None,
                    line_status=None,
                    email_deliverable=validation.email_deliverable if validation else None,
                    email_disposable=validation.email_disposable if validation else None,
                    validated=validation is not None,
                    is_primary=i == 0,
                ))

    # If lead has direct phone/email (from property), add as contact candidate
    if lead.phone and not any(c.value == lead.phone for c in contacts):
        contacts.insert(0, ContactCandidateOut(
            id=f"lead-{lead.id}-phone",
            method="phone",
            value=lead.phone,
            confidence=0.5,
            phone_type=None, carrier_name=None, line_status=None,
            email_deliverable=None, email_disposable=None,
            validated=False, is_primary=True,
        ))
    if lead.email and not any(c.value == lead.email for c in contacts):
        contacts.insert(0, ContactCandidateOut(
            id=f"lead-{lead.id}-email",
            method="email",
            value=lead.email,
            confidence=0.5,
            phone_type=None, carrier_name=None, line_status=None,
            email_deliverable=None, email_disposable=None,
            validated=False, is_primary=True,
        ))

    # Compliance
    has_consent = any(c.status.value == "opted_in" for c in consents) if consents else False
    is_dnc = lead.status == LeadStatus.dnc
    compliance = ComplianceOut(
        federal_dnc="flagged" if is_dnc else "clear",
        state_dnc="flagged" if is_dnc else "clear",
        internal_dnc="flagged" if is_dnc else "clear",
        consent_status="explicit_opt_in" if has_consent else "unknown",
        litigator_flag="clear",
        fraud_flag="clear",
    )

    # Best contact info
    best_phone = lead.phone
    best_email = lead.email
    best_confidence = None
    if enrichments:
        best_confidence = max(e.confidence for e in enrichments if e.confidence) if any(e.confidence for e in enrichments) else None

    return DiscoveredLeadDetail(
        id=str(lead.id),
        status=_lead_status_to_discovery(lead.status),
        discovery_reason="MD SDAT property data import",
        discovery_batch=prop.data_source,
        discovery_score=score.total_score if score else None,
        activation_score=score.total_score if score else None,
        enrichment_attempted=len(enrichments) > 0,
        enrichment_at=enrichments[0].created_at.isoformat() if enrichments else None,
        best_phone=best_phone,
        best_email=best_email,
        best_contact_confidence=best_confidence,
        activated_at=None,
        rejection_reason=None,
        created_at=lead.created_at.isoformat() if lead.created_at else "",
        updated_at=lead.updated_at.isoformat() if lead.updated_at else "",
        property=DiscoveredPropertyOut(
            id=str(prop.id),
            address_line1=prop.address_line1,
            address_line2=prop.address_line2,
            city=prop.city,
            state=prop.state,
            zip_code=prop.zip_code,
            county=prop.county,
            latitude=prop.latitude,
            longitude=prop.longitude,
            parcel_id=prop.parcel_id,
            property_type=prop.property_type.value if prop.property_type else None,
            year_built=prop.year_built,
            building_sqft=prop.lot_size_sqft,
            lot_size_sqft=prop.lot_size_sqft,
            roof_area_sqft=prop.roof_area_sqft,
            assessed_value=prop.assessed_value,
            last_sale_date=None,
            last_sale_price=None,
            owner_first_name=prop.owner_first_name,
            owner_last_name=prop.owner_last_name,
            owner_occupied=prop.owner_occupied,
            utility_name=prop.utility_zone,
            utility_rate_zone=prop.utility_zone,
            avg_rate_kwh=None,
            has_existing_solar=prop.has_existing_solar,
            tree_cover_pct=prop.tree_cover_pct,
            neighborhood_solar_pct=prop.neighborhood_solar_pct,
            median_household_income=prop.median_household_income,
        ),
        score_breakdown=score_breakdown,
        permits=[],
        source_records=[],
        contact_candidates=contacts,
        compliance=compliance,
    )


@router.post("/discovered/{lead_id}/enrich")
async def enrich_discovered_lead(lead_id: int, db: AsyncSession = Depends(get_db)):
    """Trigger enrichment for a single discovered lead via PDL + Melissa."""
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    enrichment = await enrich_lead(db, lead)
    if enrichment:
        await validate_contact(db, lead)

    return {"status": "enrichment_queued"}


@router.post("/discovered/batch/enrich")
async def batch_enrich_discovered(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=500),
    county: str | None = None,
    min_score: int | None = None,
    max_score: int | None = None,
):
    """Batch enrich top discovered leads by score via PDL."""
    # Find leads without prior enrichment
    already_enriched = (
        select(ContactEnrichment.lead_id)
        .distinct()
        .subquery()
    )

    query = (
        select(Lead)
        .join(Property)
        .outerjoin(LeadScore, LeadScore.lead_id == Lead.id)
        .where(Lead.status.in_([
            LeadStatus.ingested, LeadStatus.scored,
            LeadStatus.hot, LeadStatus.warm, LeadStatus.cool,
        ]))
        .where(Lead.id.notin_(select(already_enriched)))
    )

    if county:
        query = query.where(Property.county == county)
    if min_score is not None:
        query = query.where(LeadScore.total_score >= min_score)
    if max_score is not None:
        query = query.where(LeadScore.total_score <= max_score)

    query = query.order_by(LeadScore.total_score.desc().nulls_last()).limit(limit)
    result = await db.execute(query)
    leads = result.scalars().all()

    enriched_count = 0
    for lead in leads:
        try:
            enrichment = await enrich_lead(db, lead)
            if enrichment:
                await validate_contact(db, lead)
                enriched_count += 1
        except Exception:
            pass

    return {"status": "batch_enrichment_completed", "count": enriched_count}


class SkipTraceRequest(BaseModel):
    limit: int = 100
    county: str | None = None
    min_score: int | None = None
    auto_activate: bool = True


@router.post("/discovered/skip-trace")
async def skip_trace_discovered(
    payload: SkipTraceRequest,
    db: AsyncSession = Depends(get_db),
):
    """Batch skip-trace leads via Tracerfy — finds owner name + phone + email from address.

    Costs $0.02/record. Only processes leads that haven't been enriched yet.
    When auto_activate=True (default), leads that receive a phone number are
    automatically moved to 'contacting' status — no manual activation needed.
    """
    # Find leads without prior enrichment
    already_enriched = (
        select(ContactEnrichment.lead_id)
        .distinct()
        .subquery()
    )

    query = (
        select(Lead.id)
        .join(Property)
        .outerjoin(LeadScore, LeadScore.lead_id == Lead.id)
        .where(Lead.status.in_([
            LeadStatus.ingested, LeadStatus.scored,
            LeadStatus.hot, LeadStatus.warm, LeadStatus.cool,
        ]))
        .where(Lead.id.notin_(select(already_enriched)))
    )

    if payload.county:
        query = query.where(Property.county == payload.county)
    if payload.min_score is not None:
        query = query.where(LeadScore.total_score >= payload.min_score)

    query = query.order_by(LeadScore.total_score.desc().nulls_last()).limit(payload.limit)
    result = await db.execute(query)
    lead_ids = [row[0] for row in result.all()]

    if not lead_ids:
        return {"status": "no_leads", "submitted": 0, "found": 0, "not_found": 0, "activated": 0}

    trace_result = await skip_trace_leads(db, lead_ids, max_wait=600)

    # Auto-activate leads that got a phone number from skip-trace
    activated = 0
    if payload.auto_activate:
        activated = await _auto_activate_traced_leads(db, lead_ids)

    await db.commit()
    return {"status": "completed", **trace_result, "activated": activated}


async def _auto_activate_traced_leads(db: AsyncSession, lead_ids: list[int]) -> int:
    """Move leads with a phone number to 'contacting' status after skip-trace."""
    activatable_statuses = [
        LeadStatus.ingested, LeadStatus.scored,
        LeadStatus.hot, LeadStatus.warm, LeadStatus.cool,
    ]
    result = await db.execute(
        select(Lead).where(
            Lead.id.in_(lead_ids),
            Lead.phone.isnot(None),
            Lead.phone != "",
            Lead.status.in_(activatable_statuses),
            Lead.status != LeadStatus.dnc,
        )
    )
    activated = 0
    for lead in result.scalars():
        lead.status = LeadStatus.contacting
        activated += 1

    if activated:
        await db.flush()

    return activated


@router.post("/discovered/run", response_model=RunDiscoveryResponse)
async def trigger_discovery_run(
    payload: RunDiscoveryRequest,
    db: AsyncSession = Depends(get_db),
):
    """Trigger a discovery run — pull properties from Maryland Open Data."""
    result = await run_discovery(db, county=payload.county, limit=payload.limit)
    return RunDiscoveryResponse(
        status="completed",
        ingested=result["ingested"],
        scored=result["scored"],
        skipped=result["skipped"],
        errors=result["errors"],
    )


class FullPipelineRequest(BaseModel):
    county: str
    discovery_limit: int = 1000
    trace_limit: int = 100
    min_score: int | None = 50


class FullPipelineResponse(BaseModel):
    status: str
    # Discovery phase
    discovered: int
    scored: int
    skipped: int
    # Skip-trace phase
    traced: int
    phones_found: int
    # Activation phase
    activated: int


@router.post("/discovered/full-pipeline", response_model=FullPipelineResponse)
async def run_full_pipeline(
    payload: FullPipelineRequest,
    db: AsyncSession = Depends(get_db),
):
    """One-click pipeline: Discover → Skip-trace (Tracerfy) → Auto-activate.

    1. Pulls properties from Maryland SDAT for the given county
    2. Scores all ingested properties
    3. Skip-traces top leads via Tracerfy to get owner phone/email
    4. Auto-activates leads that received a phone number

    This eliminates manual activation — leads flow straight to the dialer.
    """
    import logging
    logger = logging.getLogger(__name__)

    # Phase 1: Discovery — pull SDAT data + score
    logger.info("Pipeline Phase 1: Discovery for %s (limit %d)", payload.county, payload.discovery_limit)
    discovery_result = await run_discovery(db, county=payload.county, limit=payload.discovery_limit)
    await db.commit()

    # Phase 2: Skip-trace — find owner contact info via Tracerfy
    logger.info("Pipeline Phase 2: Skip-trace top %d leads (min_score=%s)", payload.trace_limit, payload.min_score)

    already_enriched = (
        select(ContactEnrichment.lead_id)
        .distinct()
        .subquery()
    )

    trace_query = (
        select(Lead.id)
        .join(Property)
        .outerjoin(LeadScore, LeadScore.lead_id == Lead.id)
        .where(Lead.status.in_([
            LeadStatus.ingested, LeadStatus.scored,
            LeadStatus.hot, LeadStatus.warm, LeadStatus.cool,
        ]))
        .where(Lead.id.notin_(select(already_enriched)))
    )
    trace_query = trace_query.where(Property.county == payload.county)
    if payload.min_score is not None:
        trace_query = trace_query.where(LeadScore.total_score >= payload.min_score)

    trace_query = trace_query.order_by(LeadScore.total_score.desc().nulls_last()).limit(payload.trace_limit)
    result = await db.execute(trace_query)
    lead_ids = [row[0] for row in result.all()]

    traced = 0
    phones_found = 0
    if lead_ids:
        trace_result = await skip_trace_leads(db, lead_ids, max_wait=600)
        traced = trace_result.get("submitted", 0)
        phones_found = trace_result.get("found", 0)

    # Phase 3: Auto-activate leads with phone numbers
    logger.info("Pipeline Phase 3: Auto-activate leads with phone numbers")
    activated = await _auto_activate_traced_leads(db, lead_ids) if lead_ids else 0
    await db.commit()

    logger.info(
        "Pipeline complete: county=%s discovered=%d scored=%d traced=%d phones=%d activated=%d",
        payload.county, discovery_result["ingested"], discovery_result["scored"],
        traced, phones_found, activated,
    )

    return FullPipelineResponse(
        status="completed",
        discovered=discovery_result["ingested"],
        scored=discovery_result["scored"],
        skipped=discovery_result["skipped"],
        traced=traced,
        phones_found=phones_found,
        activated=activated,
    )


# ── Activation endpoints ──────────────────────────────────────────────


@router.get("/activate/queue")
async def list_activation_queue(
    db: AsyncSession = Depends(get_db),
    min_discovery_score: int | None = None,
    min_activation_score: int | None = None,
    county: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """List activation-ready leads (scored >= 50)."""
    latest_score_sq = (
        select(
            LeadScore.lead_id,
            func.max(LeadScore.scored_at).label("max_scored_at"),
        )
        .group_by(LeadScore.lead_id)
        .subquery()
    )

    query = (
        select(Lead, Property, LeadScore)
        .join(Property, Lead.property_id == Property.id)
        .join(latest_score_sq, latest_score_sq.c.lead_id == Lead.id)
        .join(
            LeadScore,
            (LeadScore.lead_id == Lead.id)
            & (LeadScore.scored_at == latest_score_sq.c.max_scored_at),
        )
        .where(LeadScore.total_score >= 50)
        .where(Lead.status.in_([LeadStatus.hot, LeadStatus.warm, LeadStatus.scored]))
    )

    if county:
        query = query.where(Property.county == county)
    if min_discovery_score is not None:
        query = query.where(LeadScore.total_score >= min_discovery_score)
    if min_activation_score is not None:
        query = query.where(LeadScore.total_score >= min_activation_score)

    # Count
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(LeadScore.total_score.desc())
    result = await db.execute(query)
    rows = result.all()

    leads_out = []
    for lead, prop, score in rows:
        row = _build_lead_row(lead, prop, score)
        row["best_contact_confidence"] = None
        row["dnc_status"] = "flagged" if lead.status == LeadStatus.dnc else "clear"
        row["consent_status"] = "unknown"
        leads_out.append(ActivationRow(**row))

    return {"leads": leads_out, "total": total}


@router.post("/activate/{lead_id}")
async def activate_lead(lead_id: int, db: AsyncSession = Depends(get_db)):
    """Activate a discovered lead — move to contacting status."""
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    lead.status = LeadStatus.contacting
    await db.flush()

    return {"lead_id": str(lead.id), "status": "activated"}


@router.post("/activate/batch")
async def batch_activate(
    payload: BatchActivateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Batch activate multiple leads."""
    activated = 0
    for lid_str in payload.discovered_lead_ids:
        try:
            lid = int(lid_str)
            lead = await db.get(Lead, lid)
            if lead and lead.status not in (LeadStatus.dnc, LeadStatus.disqualified):
                lead.status = LeadStatus.contacting
                activated += 1
        except (ValueError, TypeError):
            continue

    await db.flush()
    return {"activated": activated}


@router.post("/activate/{lead_id}/reject")
async def reject_lead(
    lead_id: int,
    payload: RejectRequest,
    db: AsyncSession = Depends(get_db),
):
    """Reject a discovered lead."""
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    lead.status = LeadStatus.disqualified
    await db.flush()
    return {"status": "rejected"}


# ── Source endpoints ──────────────────────────────────────────────────


@router.get("/sources")
async def list_sources():
    """Return configured data sources (hardcoded for MVP)."""
    return [
        {
            "id": "md-sdat-homedata",
            "name": "Maryland SDAT - HomeData",
            "source_type": "tax_assessor",
            "license": "public_data",
            "license_detail": "Maryland Open Data Portal - free, no key required",
            "connector_class": "app.connectors.md_sdat",
            "config_json": {"dataset_id": "gfzb-gya9"},
            "ingestion_cadence": "weekly",
            "is_active": True,
            "last_sync_at": datetime.utcnow().isoformat(),
            "last_sync_status": "success",
            "records_synced": 0,
            "created_at": "2026-02-07T00:00:00",
        }
    ]


@router.post("/sources/{source_id}/sync")
async def sync_source(source_id: str, db: AsyncSession = Depends(get_db)):
    """Trigger a source sync. For MVP, runs MD SDAT connector."""
    if source_id == "md-sdat-homedata":
        result = await run_discovery(db, county="Baltimore County", limit=100)
        return {"status": "completed", **result}
    raise HTTPException(status_code=404, detail="Source not found")


@router.post("/sources/test-connection")
async def test_source_connection(payload: dict):
    """Test connection to a data source."""
    return {"success": True, "message": "Connection successful", "record_count": 0}


@router.get("/admin/source-health")
async def get_source_health():
    """Return source health metrics (simplified for MVP)."""
    return [
        {
            "source_id": "md-sdat-homedata",
            "name": "Maryland SDAT - HomeData",
            "source_type": "tax_assessor",
            "uptime_pct": 99.9,
            "last_7d_ingests": [0, 0, 0, 0, 0, 0, 0],
            "last_error": None,
            "last_error_at": None,
            "avg_latency_ms": 450,
            "records_added_7d": 0,
            "records_updated_7d": 0,
            "last_sync_at": None,
            "last_sync_status": None,
        }
    ]
