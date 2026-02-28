"""Public customer portal endpoints — NO authentication required.

These endpoints use portal_token for lead identification instead of JWT auth.
"""

import secrets
from datetime import date, datetime, time, timedelta, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.services.email import send_new_lead_notification
from app.models.schema import (
    Appointment,
    AppointmentStatus,
    ConsentLog,
    ConsentStatus,
    ConsentType,
    ContactChannel,
    InboundMessage,
    Lead,
    LeadStatus,
    MessageDirection,
    Property,
    RepUser,
    UserRole,
)

router = APIRouter(prefix="/portal", tags=["portal"])

# ── Helpers ───────────────────────────────────────────────────────────────


def _generate_token() -> str:
    """Generate a URL-safe 12-char token."""
    return secrets.token_urlsafe(9)[:12]


def _estimate_savings(prop: Property) -> dict:
    """Simple solar savings estimate from property data."""
    roof_sqft = prop.roof_area_sqft or 1500
    # ~15 sqft per panel, 400W per panel, ~1200 kWh/kW/yr (MD average)
    panels = int(roof_sqft * 0.5 / 15)  # 50% usable roof
    system_kw = panels * 0.4
    annual_kwh = system_kw * 1200
    rate_per_kwh = 0.15  # MD average
    annual_savings = round(annual_kwh * rate_per_kwh)
    lifetime_savings = annual_savings * 25
    assessed = prop.assessed_value or 0
    tax_credit = round(assessed * 0.03) if assessed else round(system_kw * 3000 * 0.30)

    return {
        "system_size_kw": round(system_kw, 1),
        "panel_count": panels,
        "annual_savings": annual_savings,
        "lifetime_savings": lifetime_savings,
        "federal_tax_credit": tax_credit,
        "monthly_savings": round(annual_savings / 12),
    }


# ── Request / Response Models ─────────────────────────────────────────────


class QuoteRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: str = Field(min_length=7, max_length=20)
    email: EmailStr
    address: str = Field(min_length=3, max_length=255)
    city: str = Field(min_length=1, max_length=100)
    state: str = Field(min_length=2, max_length=2, default="MD")
    zip_code: str = Field(min_length=5, max_length=10)


class AppointmentRequest(BaseModel):
    preferred_date: date
    time_preference: str = Field(pattern="^(morning|afternoon|evening)$")
    notes: str | None = Field(default=None, max_length=500)


class MessageRequest(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


# ── Endpoints ─────────────────────────────────────────────────────────────


@router.post("/quote")
async def submit_quote(data: QuoteRequest):
    """Public quote request — creates Property + Lead with portal_token."""
    async for db in get_db():
        # Check for existing lead by phone or email
        existing = await db.execute(
            select(Lead).where(
                (Lead.phone == data.phone) | (Lead.email == data.email)
            )
        )
        existing_lead = existing.scalars().first()
        if existing_lead:
            # Return existing portal token
            if not existing_lead.portal_token:
                existing_lead.portal_token = _generate_token()
                await db.commit()
            return {
                "token": existing_lead.portal_token,
                "message": "Welcome back! We already have your information on file.",
            }

        # Create property
        prop = Property(
            address_line1=data.address,
            city=data.city,
            state=data.state.upper(),
            zip_code=data.zip_code,
            county="",  # Will be enriched later
            owner_first_name=data.first_name,
            owner_last_name=data.last_name,
            owner_phone=data.phone,
            owner_email=data.email,
        )
        db.add(prop)
        await db.flush()

        # Create lead
        token = _generate_token()
        lead = Lead(
            property_id=prop.id,
            status=LeadStatus.ingested,
            portal_token=token,
            first_name=data.first_name,
            last_name=data.last_name,
            phone=data.phone,
            email=data.email,
        )
        db.add(lead)
        await db.flush()

        # Record consent
        consent = ConsentLog(
            lead_id=lead.id,
            consent_type=ConsentType.all_channels,
            status=ConsentStatus.opted_in,
            channel=ContactChannel.sms,
            evidence_type="web_form",
        )
        db.add(consent)
        await db.commit()

        # Send email notification to business owner (non-blocking)
        await send_new_lead_notification(
            first_name=data.first_name,
            last_name=data.last_name,
            phone=data.phone,
            email=data.email,
            address=data.address,
            city=data.city,
            state=data.state,
            zip_code=data.zip_code,
        )

        return {
            "token": token,
            "message": "Thank you! Your free solar quote request has been received.",
        }


@router.get("/lead/{token}")
async def get_lead_summary(token: str):
    """Get lead summary for personalized portal view."""
    async for db in get_db():
        result = await db.execute(
            select(Lead)
            .options(
                selectinload(Lead.property),
                selectinload(Lead.scores),
                selectinload(Lead.appointments),
            )
            .where(Lead.portal_token == token)
        )
        lead = result.scalars().first()
        if not lead:
            raise HTTPException(status_code=404, detail="Invalid portal link")

        prop = lead.property
        latest_score = lead.scores[0] if lead.scores else None
        savings = _estimate_savings(prop)

        appointments = []
        for apt in lead.appointments:
            appointments.append({
                "id": apt.id,
                "status": apt.status.value,
                "scheduled_start": apt.scheduled_start.isoformat(),
                "scheduled_end": apt.scheduled_end.isoformat(),
                "address": apt.address,
                "notes": apt.notes,
            })

        return {
            "first_name": lead.first_name,
            "last_name": lead.last_name,
            "address": f"{prop.address_line1}, {prop.city}, {prop.state} {prop.zip_code}",
            "solar_score": latest_score.total_score if latest_score else None,
            "savings": savings,
            "appointments": appointments,
            "status": lead.status.value,
        }


@router.post("/lead/{token}/appointment")
async def request_appointment(token: str, data: AppointmentRequest):
    """Request an appointment — customer picks date + time preference."""
    async for db in get_db():
        result = await db.execute(
            select(Lead)
            .options(selectinload(Lead.property))
            .where(Lead.portal_token == token)
        )
        lead = result.scalars().first()
        if not lead:
            raise HTTPException(status_code=404, detail="Invalid portal link")

        # Map time preference to hour
        hour_map = {"morning": 9, "afternoon": 13, "evening": 17}
        start_hour = hour_map.get(data.time_preference, 9)
        start_dt = datetime.combine(
            data.preferred_date, time(start_hour, 0), tzinfo=timezone.utc
        )
        end_dt = start_dt + timedelta(hours=1)

        # Find an available rep (prefer assigned, fallback to any admin)
        rep_id = lead.assigned_rep_id
        if not rep_id:
            rep_result = await db.execute(
                select(RepUser.id)
                .where(RepUser.is_active == True, RepUser.role == UserRole.admin)  # noqa: E712
                .limit(1)
            )
            rep_row = rep_result.scalars().first()
            rep_id = rep_row if rep_row else 1  # Fallback to user 1

        prop = lead.property
        address = f"{prop.address_line1}, {prop.city}, {prop.state} {prop.zip_code}"

        apt = Appointment(
            lead_id=lead.id,
            rep_id=rep_id,
            status=AppointmentStatus.scheduled,
            scheduled_start=start_dt,
            scheduled_end=end_dt,
            address=address,
            notes=data.notes or f"Requested via portal — {data.time_preference} preference",
        )
        db.add(apt)

        # Update lead status
        lead.status = LeadStatus.appointment_set
        await db.commit()
        await db.refresh(apt)

        return {
            "appointment_id": apt.id,
            "scheduled_start": start_dt.isoformat(),
            "scheduled_end": end_dt.isoformat(),
            "message": "Your consultation has been scheduled! We'll confirm via text.",
        }


@router.get("/lead/{token}/appointments")
async def get_appointments(token: str):
    """Get all appointments for a lead."""
    async for db in get_db():
        result = await db.execute(
            select(Lead)
            .options(selectinload(Lead.appointments))
            .where(Lead.portal_token == token)
        )
        lead = result.scalars().first()
        if not lead:
            raise HTTPException(status_code=404, detail="Invalid portal link")

        return {
            "appointments": [
                {
                    "id": apt.id,
                    "status": apt.status.value,
                    "scheduled_start": apt.scheduled_start.isoformat(),
                    "scheduled_end": apt.scheduled_end.isoformat(),
                    "address": apt.address,
                    "notes": apt.notes,
                }
                for apt in lead.appointments
            ]
        }


@router.post("/lead/{token}/message")
async def send_message(token: str, data: MessageRequest):
    """Customer sends a message to the Solar Command team."""
    async for db in get_db():
        result = await db.execute(
            select(Lead).where(Lead.portal_token == token)
        )
        lead = result.scalars().first()
        if not lead:
            raise HTTPException(status_code=404, detail="Invalid portal link")

        msg = InboundMessage(
            lead_id=lead.id,
            direction=MessageDirection.inbound,
            channel=ContactChannel.sms,
            from_number=lead.phone,
            body=data.body,
            sent_by="portal",
        )
        db.add(msg)
        await db.commit()
        await db.refresh(msg)

        return {
            "message_id": msg.id,
            "created_at": msg.created_at.isoformat(),
            "message": "Message sent! Our team typically responds within 1 business day.",
        }
