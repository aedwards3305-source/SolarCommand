"""Lead endpoints — ingest properties, score leads, retrieve lead data, notes, consent."""

import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.schema import (
    AuditLog,
    ConsentLog,
    ConsentStatus,
    ConsentType,
    ContactChannel,
    Lead,
    LeadScore,
    LeadStatus,
    Note,
    OutreachAttempt,
    Property,
    PropertyType,
    RepUser,
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


class ScoreDetail(BaseModel):
    total_score: int
    score_version: str
    roof_age_score: int
    ownership_score: int
    roof_area_score: int
    home_value_score: int
    utility_rate_score: int
    shade_score: int
    neighborhood_score: int
    income_score: int
    property_type_score: int
    existing_solar_score: int
    scored_at: str


class PropertyOut(BaseModel):
    id: int
    address_line1: str
    address_line2: str | None
    city: str
    state: str
    zip_code: str
    county: str
    parcel_id: str | None
    property_type: str
    year_built: int | None
    roof_area_sqft: float | None
    assessed_value: float | None
    utility_zone: str | None
    tree_cover_pct: float | None
    neighborhood_solar_pct: float | None
    has_existing_solar: bool
    owner_occupied: bool
    median_household_income: float | None


class OutreachAttemptBrief(BaseModel):
    id: int
    channel: str
    disposition: str | None
    started_at: str
    duration_seconds: int | None


class NoteOut(BaseModel):
    id: int
    author: str
    content: str
    created_at: str


class ConsentOut(BaseModel):
    id: int
    consent_type: str
    status: str
    channel: str
    evidence_type: str | None
    recorded_at: str


class LeadDetailResponse(BaseModel):
    id: int
    first_name: str | None
    last_name: str | None
    phone: str | None
    email: str | None
    status: str
    assigned_rep_id: int | None
    assigned_rep_name: str | None
    total_call_attempts: int
    total_sms_sent: int
    total_emails_sent: int
    last_contacted_at: str | None
    created_at: str
    updated_at: str
    property: PropertyOut
    scores: list[ScoreDetail]
    recent_outreach: list[OutreachAttemptBrief]
    notes: list[NoteOut]
    consent_logs: list[ConsentOut]


class NoteCreate(BaseModel):
    content: str
    author: str = "system"


class ConsentCreate(BaseModel):
    consent_type: str  # voice_call, sms, email, all_channels
    status: str  # opted_in, opted_out, pending, revoked
    channel: str  # voice, sms, email
    evidence_type: str | None = None
    evidence_url: str | None = None


class StatusUpdate(BaseModel):
    status: str


class AssignRep(BaseModel):
    rep_id: int


class CSVUploadResponse(BaseModel):
    ingested: int
    skipped: int
    errors: list[str]


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


@router.get("/{lead_id}", response_model=LeadDetailResponse)
async def get_lead_detail(lead_id: int, db: AsyncSession = Depends(get_db)):
    """Full lead detail with property, scores, outreach, notes, consent."""
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    prop = await db.get(Property, lead.property_id)

    # Scores
    score_result = await db.execute(
        select(LeadScore).where(LeadScore.lead_id == lead_id).order_by(LeadScore.scored_at.desc())
    )
    scores = score_result.scalars().all()

    # Recent outreach
    outreach_result = await db.execute(
        select(OutreachAttempt)
        .where(OutreachAttempt.lead_id == lead_id)
        .order_by(OutreachAttempt.started_at.desc())
        .limit(20)
    )
    attempts = outreach_result.scalars().all()

    # Notes
    notes_result = await db.execute(
        select(Note).where(Note.lead_id == lead_id).order_by(Note.created_at.desc())
    )
    notes = notes_result.scalars().all()

    # Consent
    consent_result = await db.execute(
        select(ConsentLog).where(ConsentLog.lead_id == lead_id).order_by(
            ConsentLog.recorded_at.desc()
        )
    )
    consents = consent_result.scalars().all()

    # Rep name
    rep_name = None
    if lead.assigned_rep_id:
        rep = await db.get(RepUser, lead.assigned_rep_id)
        rep_name = rep.name if rep else None

    return LeadDetailResponse(
        id=lead.id,
        first_name=lead.first_name,
        last_name=lead.last_name,
        phone=lead.phone,
        email=lead.email,
        status=lead.status.value,
        assigned_rep_id=lead.assigned_rep_id,
        assigned_rep_name=rep_name,
        total_call_attempts=lead.total_call_attempts or 0,
        total_sms_sent=lead.total_sms_sent or 0,
        total_emails_sent=lead.total_emails_sent or 0,
        last_contacted_at=lead.last_contacted_at.isoformat() if lead.last_contacted_at else None,
        created_at=lead.created_at.isoformat(),
        updated_at=lead.updated_at.isoformat(),
        property=PropertyOut(
            id=prop.id,
            address_line1=prop.address_line1,
            address_line2=prop.address_line2,
            city=prop.city,
            state=prop.state,
            zip_code=prop.zip_code,
            county=prop.county,
            parcel_id=prop.parcel_id,
            property_type=prop.property_type.value,
            year_built=prop.year_built,
            roof_area_sqft=prop.roof_area_sqft,
            assessed_value=prop.assessed_value,
            utility_zone=prop.utility_zone,
            tree_cover_pct=prop.tree_cover_pct,
            neighborhood_solar_pct=prop.neighborhood_solar_pct,
            has_existing_solar=prop.has_existing_solar,
            owner_occupied=prop.owner_occupied,
            median_household_income=prop.median_household_income,
        ),
        scores=[
            ScoreDetail(
                total_score=s.total_score,
                score_version=s.score_version,
                roof_age_score=s.roof_age_score,
                ownership_score=s.ownership_score,
                roof_area_score=s.roof_area_score,
                home_value_score=s.home_value_score,
                utility_rate_score=s.utility_rate_score,
                shade_score=s.shade_score,
                neighborhood_score=s.neighborhood_score,
                income_score=s.income_score,
                property_type_score=s.property_type_score,
                existing_solar_score=s.existing_solar_score,
                scored_at=s.scored_at.isoformat() if s.scored_at else "",
            )
            for s in scores
        ],
        recent_outreach=[
            OutreachAttemptBrief(
                id=a.id,
                channel=a.channel.value,
                disposition=a.disposition.value if a.disposition else None,
                started_at=a.started_at.isoformat() if a.started_at else "",
                duration_seconds=a.duration_seconds,
            )
            for a in attempts
        ],
        notes=[
            NoteOut(
                id=n.id,
                author=n.author,
                content=n.content,
                created_at=n.created_at.isoformat() if n.created_at else "",
            )
            for n in notes
        ],
        consent_logs=[
            ConsentOut(
                id=c.id,
                consent_type=c.consent_type.value,
                status=c.status.value,
                channel=c.channel.value,
                evidence_type=c.evidence_type,
                recorded_at=c.recorded_at.isoformat() if c.recorded_at else "",
            )
            for c in consents
        ],
    )


@router.post("/{lead_id}/notes", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
async def add_note(lead_id: int, payload: NoteCreate, db: AsyncSession = Depends(get_db)):
    """Add a note to a lead."""
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    note = Note(lead_id=lead_id, author=payload.author, content=payload.content)
    db.add(note)
    await db.flush()

    return NoteOut(
        id=note.id,
        author=note.author,
        content=note.content,
        created_at=note.created_at.isoformat() if note.created_at else "",
    )


@router.get("/{lead_id}/notes", response_model=list[NoteOut])
async def list_notes(lead_id: int, db: AsyncSession = Depends(get_db)):
    """List notes for a lead."""
    result = await db.execute(
        select(Note).where(Note.lead_id == lead_id).order_by(Note.created_at.desc())
    )
    notes = result.scalars().all()
    return [
        NoteOut(
            id=n.id,
            author=n.author,
            content=n.content,
            created_at=n.created_at.isoformat() if n.created_at else "",
        )
        for n in notes
    ]


@router.post(
    "/{lead_id}/consent", response_model=ConsentOut, status_code=status.HTTP_201_CREATED
)
async def add_consent(lead_id: int, payload: ConsentCreate, db: AsyncSession = Depends(get_db)):
    """Record a consent event for a lead."""
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    consent = ConsentLog(
        lead_id=lead_id,
        consent_type=ConsentType(payload.consent_type),
        status=ConsentStatus(payload.status),
        channel=ContactChannel(payload.channel),
        evidence_type=payload.evidence_type,
        evidence_url=payload.evidence_url,
    )
    db.add(consent)

    db.add(
        AuditLog(
            actor="system",
            action="consent.recorded",
            entity_type="consent_log",
            entity_id=lead_id,
            new_value=f"type={payload.consent_type}, status={payload.status}",
        )
    )

    await db.flush()

    return ConsentOut(
        id=consent.id,
        consent_type=consent.consent_type.value,
        status=consent.status.value,
        channel=consent.channel.value,
        evidence_type=consent.evidence_type,
        recorded_at=consent.recorded_at.isoformat() if consent.recorded_at else "",
    )


@router.get("/{lead_id}/consent", response_model=list[ConsentOut])
async def list_consent(lead_id: int, db: AsyncSession = Depends(get_db)):
    """List consent records for a lead."""
    result = await db.execute(
        select(ConsentLog)
        .where(ConsentLog.lead_id == lead_id)
        .order_by(ConsentLog.recorded_at.desc())
    )
    consents = result.scalars().all()
    return [
        ConsentOut(
            id=c.id,
            consent_type=c.consent_type.value,
            status=c.status.value,
            channel=c.channel.value,
            evidence_type=c.evidence_type,
            recorded_at=c.recorded_at.isoformat() if c.recorded_at else "",
        )
        for c in consents
    ]


@router.patch("/{lead_id}/status", response_model=dict)
async def update_lead_status(
    lead_id: int, payload: StatusUpdate, db: AsyncSession = Depends(get_db)
):
    """Manually update a lead's status."""
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    old_status = lead.status.value
    try:
        new_status = LeadStatus(payload.status)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid status: {payload.status}")

    lead.status = new_status

    db.add(
        AuditLog(
            actor="user",
            action="lead.status_change",
            entity_type="lead",
            entity_id=lead_id,
            old_value=old_status,
            new_value=new_status.value,
        )
    )

    return {"lead_id": lead_id, "old_status": old_status, "new_status": new_status.value}


@router.patch("/{lead_id}/assign", response_model=dict)
async def assign_rep(lead_id: int, payload: AssignRep, db: AsyncSession = Depends(get_db)):
    """Assign a rep to a lead."""
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    rep = await db.get(RepUser, payload.rep_id)
    if not rep:
        raise HTTPException(status_code=404, detail="Rep not found")

    lead.assigned_rep_id = rep.id

    db.add(
        AuditLog(
            actor="user",
            action="lead.assigned",
            entity_type="lead",
            entity_id=lead_id,
            new_value=f"rep_id={rep.id}, rep_name={rep.name}",
        )
    )

    return {"lead_id": lead_id, "assigned_rep_id": rep.id, "assigned_rep_name": rep.name}


@router.post("/ingest/csv", response_model=CSVUploadResponse)
async def ingest_csv(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """Bulk ingest properties from a CSV file."""
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=422, detail="File must be a .csv")

    contents = await file.read()
    text = contents.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    ingested = 0
    skipped = 0
    errors = []

    for i, row in enumerate(reader, start=2):  # row 2 = first data row
        try:
            parcel_id = row.get("parcel_id", "").strip() or None

            # Check duplicate
            if parcel_id:
                existing = await db.execute(
                    select(Property).where(Property.parcel_id == parcel_id)
                )
                if existing.scalar_one_or_none():
                    skipped += 1
                    continue

            try:
                prop_type = PropertyType(row.get("property_type", "SFH").strip())
            except ValueError:
                prop_type = PropertyType.OTHER

            def to_float(val):
                try:
                    return float(val) if val and val.strip() else None
                except (ValueError, AttributeError):
                    return None

            def to_int(val):
                try:
                    return int(val) if val and val.strip() else None
                except (ValueError, AttributeError):
                    return None

            def to_bool(val):
                if not val:
                    return False
                return val.strip().lower() in ("true", "1", "yes", "t")

            prop = Property(
                address_line1=row.get("address_line1", "").strip(),
                address_line2=row.get("address_line2", "").strip() or None,
                city=row.get("city", "").strip(),
                state=row.get("state", "MD").strip() or "MD",
                zip_code=row.get("zip_code", "").strip(),
                county=row.get("county", "").strip(),
                parcel_id=parcel_id,
                property_type=prop_type,
                year_built=to_int(row.get("year_built")),
                roof_area_sqft=to_float(row.get("roof_area_sqft")),
                assessed_value=to_float(row.get("assessed_value")),
                lot_size_sqft=to_float(row.get("lot_size_sqft")),
                utility_zone=row.get("utility_zone", "").strip() or None,
                tree_cover_pct=to_float(row.get("tree_cover_pct")),
                neighborhood_solar_pct=to_float(row.get("neighborhood_solar_pct")),
                has_existing_solar=to_bool(row.get("has_existing_solar")),
                owner_first_name=row.get("owner_first_name", "").strip() or None,
                owner_last_name=row.get("owner_last_name", "").strip() or None,
                owner_occupied=to_bool(row.get("owner_occupied", "true")),
                owner_phone=row.get("owner_phone", "").strip() or None,
                owner_email=row.get("owner_email", "").strip() or None,
                median_household_income=to_float(row.get("median_household_income")),
                data_source="csv_upload",
            )
            db.add(prop)
            await db.flush()

            lead = Lead(
                property_id=prop.id,
                first_name=prop.owner_first_name,
                last_name=prop.owner_last_name,
                phone=prop.owner_phone,
                email=prop.owner_email,
                status=LeadStatus.ingested,
            )
            db.add(lead)
            await db.flush()

            ingested += 1

        except Exception as e:
            errors.append(f"Row {i}: {str(e)}")

    if ingested > 0:
        db.add(
            AuditLog(
                actor="user",
                action="leads.csv_import",
                entity_type="lead",
                new_value=f"ingested={ingested}, skipped={skipped}, errors={len(errors)}",
            )
        )

    return CSVUploadResponse(ingested=ingested, skipped=skipped, errors=errors[:20])
