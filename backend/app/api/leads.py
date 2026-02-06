"""Lead endpoints — ingest properties, score leads, retrieve lead data."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.schema import (
    AuditLog,
    Lead,
    LeadScore,
    LeadStatus,
    Property,
    PropertyType,
)
from app.services.scoring import score_lead

router = APIRouter(prefix="/leads", tags=["leads"])


# ── Request / Response schemas ──────────────────────────────────────────


class PropertyIngest(BaseModel):
    address_line1: str
    address_line2: str | None = None
    city: str
    state: str = "MD"
    zip_code: str
    county: str
    parcel_id: str | None = None
    property_type: str = "SFH"
    year_built: int | None = None
    roof_area_sqft: float | None = None
    assessed_value: float | None = None
    lot_size_sqft: float | None = None
    utility_zone: str | None = None
    tree_cover_pct: float | None = None
    neighborhood_solar_pct: float | None = None
    has_existing_solar: bool = False
    owner_first_name: str | None = None
    owner_last_name: str | None = None
    owner_occupied: bool = True
    owner_phone: str | None = None
    owner_email: str | None = None
    median_household_income: float | None = None
    data_source: str | None = None


class IngestResponse(BaseModel):
    property_id: int
    lead_id: int
    message: str


class ScoreResponse(BaseModel):
    lead_id: int
    total_score: int
    tier: str
    factors: dict


class LeadSummary(BaseModel):
    id: int
    first_name: str | None
    last_name: str | None
    status: str
    score: int | None
    county: str | None
    address: str | None
    phone: str | None
    created_at: datetime


class LeadListResponse(BaseModel):
    leads: list[LeadSummary]
    total: int
    page: int
    page_size: int


# ── Endpoints ───────────────────────────────────────────────────────────


@router.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_property(payload: PropertyIngest, db: AsyncSession = Depends(get_db)):
    """Ingest a property record and create a lead."""
    # Check for duplicate by parcel_id
    if payload.parcel_id:
        existing = await db.execute(
            select(Property).where(Property.parcel_id == payload.parcel_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Property with parcel_id {payload.parcel_id} already exists",
            )

    # Map property type string to enum
    try:
        prop_type = PropertyType(payload.property_type)
    except ValueError:
        prop_type = PropertyType.OTHER

    prop = Property(
        address_line1=payload.address_line1,
        address_line2=payload.address_line2,
        city=payload.city,
        state=payload.state,
        zip_code=payload.zip_code,
        county=payload.county,
        parcel_id=payload.parcel_id,
        property_type=prop_type,
        year_built=payload.year_built,
        roof_area_sqft=payload.roof_area_sqft,
        assessed_value=payload.assessed_value,
        lot_size_sqft=payload.lot_size_sqft,
        utility_zone=payload.utility_zone,
        tree_cover_pct=payload.tree_cover_pct,
        neighborhood_solar_pct=payload.neighborhood_solar_pct,
        has_existing_solar=payload.has_existing_solar,
        owner_first_name=payload.owner_first_name,
        owner_last_name=payload.owner_last_name,
        owner_occupied=payload.owner_occupied,
        owner_phone=payload.owner_phone,
        owner_email=payload.owner_email,
        median_household_income=payload.median_household_income,
        data_source=payload.data_source,
    )
    db.add(prop)
    await db.flush()

    lead = Lead(
        property_id=prop.id,
        first_name=payload.owner_first_name,
        last_name=payload.owner_last_name,
        phone=payload.owner_phone,
        email=payload.owner_email,
        status=LeadStatus.ingested,
    )
    db.add(lead)
    await db.flush()

    # Audit log
    db.add(
        AuditLog(
            actor="system",
            action="lead.ingested",
            entity_type="lead",
            entity_id=lead.id,
            new_value=f"property_id={prop.id}",
        )
    )

    return IngestResponse(
        property_id=prop.id,
        lead_id=lead.id,
        message="Property ingested and lead created",
    )


@router.post("/{lead_id}/score", response_model=ScoreResponse)
async def score_lead_endpoint(lead_id: int, db: AsyncSession = Depends(get_db)):
    """Compute and store the Solar Readiness Score for a lead."""
    try:
        score_record = await score_lead(db, lead_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    # Determine tier
    if score_record.total_score >= 75:
        tier = "hot"
    elif score_record.total_score >= 50:
        tier = "warm"
    else:
        tier = "cool"

    # Audit log
    db.add(
        AuditLog(
            actor="system",
            action="lead.scored",
            entity_type="lead",
            entity_id=lead_id,
            new_value=f"score={score_record.total_score}, tier={tier}",
        )
    )

    return ScoreResponse(
        lead_id=lead_id,
        total_score=score_record.total_score,
        tier=tier,
        factors={
            "roof_age": score_record.roof_age_score,
            "ownership": score_record.ownership_score,
            "roof_area": score_record.roof_area_score,
            "home_value": score_record.home_value_score,
            "utility_rate": score_record.utility_rate_score,
            "shade": score_record.shade_score,
            "neighborhood": score_record.neighborhood_score,
            "income": score_record.income_score,
            "property_type": score_record.property_type_score,
            "existing_solar": score_record.existing_solar_score,
        },
    )


@router.get("", response_model=LeadListResponse)
async def list_leads(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status_filter: LeadStatus | None = None,
    county: str | None = None,
    min_score: int | None = None,
):
    """List leads with optional filters."""
    query = select(Lead).join(Property)

    if status_filter:
        query = query.where(Lead.status == status_filter)
    if county:
        query = query.where(Property.county == county)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Lead.created_at.desc())
    result = await db.execute(query)
    leads = result.scalars().all()

    # Build response with latest scores
    summaries = []
    for lead in leads:
        # Get latest score
        score_result = await db.execute(
            select(LeadScore.total_score)
            .where(LeadScore.lead_id == lead.id)
            .order_by(LeadScore.scored_at.desc())
            .limit(1)
        )
        score = score_result.scalar()

        prop = await db.get(Property, lead.property_id)
        summaries.append(
            LeadSummary(
                id=lead.id,
                first_name=lead.first_name,
                last_name=lead.last_name,
                status=lead.status.value,
                score=score,
                county=prop.county if prop else None,
                address=prop.address_line1 if prop else None,
                phone=lead.phone,
                created_at=lead.created_at,
            )
        )

    return LeadListResponse(
        leads=summaries, total=total, page=page, page_size=page_size
    )
