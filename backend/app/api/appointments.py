"""Appointment endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.schema import (
    Appointment,
    AppointmentStatus,
    AuditLog,
    Lead,
    LeadStatus,
    Property,
    RepUser,
)

router = APIRouter(prefix="/appointments", tags=["appointments"], dependencies=[Depends(get_current_user)])


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
    prop = await db.get(Property, lead.property_id)
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


class AppointmentUpdate(BaseModel):
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None
    notes: str | None = None
    status: str | None = None


@router.put("/{appt_id}", response_model=AppointmentOut)
async def update_appointment(
    appt_id: int,
    payload: AppointmentUpdate,
    current_user: RepUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an appointment — reschedule, change status, edit notes."""
    appt = await db.get(Appointment, appt_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    old_start = appt.scheduled_start.isoformat()
    old_status = appt.status.value

    if payload.scheduled_start is not None:
        appt.scheduled_start = payload.scheduled_start
    if payload.scheduled_end is not None:
        appt.scheduled_end = payload.scheduled_end
    if payload.notes is not None:
        appt.notes = payload.notes
    if payload.status is not None:
        try:
            new_status = AppointmentStatus(payload.status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {payload.status}")
        appt.status = new_status

        # If rescheduled, update the status
        if new_status == AppointmentStatus.rescheduled and payload.scheduled_start:
            appt.status = AppointmentStatus.scheduled

        # Sync lead status on completion or cancellation
        lead = await db.get(Lead, appt.lead_id)
        if lead:
            if new_status == AppointmentStatus.completed:
                lead.status = LeadStatus.qualified
            elif new_status == AppointmentStatus.cancelled:
                # Revert to previous pipeline stage
                if lead.status == LeadStatus.appointment_set:
                    lead.status = LeadStatus.contacted

    changes = []
    if payload.scheduled_start and old_start != appt.scheduled_start.isoformat():
        changes.append(f"rescheduled from {old_start}")
    if payload.status and old_status != appt.status.value:
        changes.append(f"status {old_status} → {appt.status.value}")

    if changes:
        db.add(AuditLog(
            actor=current_user.name,
            action="appointment.updated",
            entity_type="appointment",
            entity_id=appt.id,
            old_value=f"start={old_start}, status={old_status}",
            new_value="; ".join(changes),
        ))

    await db.flush()

    rep = await db.get(RepUser, appt.rep_id)
    return AppointmentOut(
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
