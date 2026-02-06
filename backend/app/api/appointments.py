"""Appointment endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.schema import (
    Appointment,
    AppointmentStatus,
    AuditLog,
    Lead,
    LeadStatus,
    RepUser,
)

router = APIRouter(prefix="/appointments", tags=["appointments"])


class AppointmentCreate(BaseModel):
    lead_id: int
    rep_id: int
    scheduled_start: datetime
    scheduled_end: datetime
    notes: str | None = None


class AppointmentOut(BaseModel):
    id: int
    lead_id: int
    rep_id: int
    rep_name: str | None
    status: str
    scheduled_start: str
    scheduled_end: str
    address: str | None
    notes: str | None


@router.post("", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    payload: AppointmentCreate, db: AsyncSession = Depends(get_db)
):
    """Book an appointment for a lead with a rep."""
    lead = await db.get(Lead, payload.lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    rep = await db.get(RepUser, payload.rep_id)
    if not rep:
        raise HTTPException(status_code=404, detail="Rep not found")

    # Get address from property
    prop = await db.get(
        __import__("app.models.schema", fromlist=["Property"]).Property,
        lead.property_id,
    )
    address = prop.address_line1 if prop else None

    appt = Appointment(
        lead_id=lead.id,
        rep_id=rep.id,
        status=AppointmentStatus.scheduled,
        scheduled_start=payload.scheduled_start,
        scheduled_end=payload.scheduled_end,
        address=address,
        notes=payload.notes,
    )
    db.add(appt)

    lead.status = LeadStatus.appointment_set
    lead.assigned_rep_id = rep.id

    db.add(
        AuditLog(
            actor="system",
            action="appointment.created",
            entity_type="appointment",
            entity_id=appt.id,
            new_value=f"lead={lead.id}, rep={rep.id}, time={payload.scheduled_start}",
        )
    )

    await db.flush()

    return AppointmentOut(
        id=appt.id,
        lead_id=appt.lead_id,
        rep_id=appt.rep_id,
        rep_name=rep.name,
        status=appt.status.value,
        scheduled_start=appt.scheduled_start.isoformat(),
        scheduled_end=appt.scheduled_end.isoformat(),
        address=address,
        notes=appt.notes,
    )


@router.get("", response_model=list[AppointmentOut])
async def list_appointments(
    db: AsyncSession = Depends(get_db),
    rep_id: int | None = None,
    status_filter: AppointmentStatus | None = None,
):
    """List appointments with optional filters."""
    query = select(Appointment)
    if rep_id:
        query = query.where(Appointment.rep_id == rep_id)
    if status_filter:
        query = query.where(Appointment.status == status_filter)
    query = query.order_by(Appointment.scheduled_start.asc())

    result = await db.execute(query)
    appts = result.scalars().all()

    out = []
    for appt in appts:
        rep = await db.get(RepUser, appt.rep_id)
        out.append(
            AppointmentOut(
                id=appt.id,
                lead_id=appt.lead_id,
                rep_id=appt.rep_id,
                rep_name=rep.name if rep else None,
                status=appt.status.value,
                scheduled_start=appt.scheduled_start.isoformat(),
                scheduled_end=appt.scheduled_end.isoformat(),
                address=appt.address,
                notes=appt.notes,
            )
        )
    return out
