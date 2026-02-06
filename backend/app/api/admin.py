"""Admin endpoints — audit log, scripts, reps."""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.schema import AuditLog, RepUser, ScriptVersion

router = APIRouter(prefix="/admin", tags=["admin"])


class AuditLogOut(BaseModel):
    id: int
    actor: str
    action: str
    entity_type: str
    entity_id: int | None
    old_value: str | None
    new_value: str | None
    created_at: str


@router.get("/audit-log", response_model=list[AuditLogOut])
async def get_audit_log(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    entity_type: str | None = None,
    actor: str | None = None,
):
    """Browse the audit log with filters."""
    query = select(AuditLog)
    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
    if actor:
        query = query.where(AuditLog.actor == actor)
    query = query.order_by(AuditLog.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    logs = result.scalars().all()

    return [
        AuditLogOut(
            id=log.id,
            actor=log.actor,
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            old_value=log.old_value,
            new_value=log.new_value,
            created_at=log.created_at.isoformat() if log.created_at else "",
        )
        for log in logs
    ]


class ScriptVersionOut(BaseModel):
    id: int
    version_label: str
    channel: str
    content: str | None
    is_active: bool
    created_by: str | None
    created_at: str


@router.get("/scripts", response_model=list[ScriptVersionOut])
async def list_scripts(db: AsyncSession = Depends(get_db)):
    """List all script versions."""
    result = await db.execute(
        select(ScriptVersion).order_by(ScriptVersion.created_at.desc())
    )
    scripts = result.scalars().all()
    return [
        ScriptVersionOut(
            id=s.id,
            version_label=s.version_label,
            channel=s.channel.value,
            content=s.content,
            is_active=s.is_active,
            created_by=s.created_by,
            created_at=s.created_at.isoformat() if s.created_at else "",
        )
        for s in scripts
    ]


class RepOut(BaseModel):
    id: int
    email: str
    name: str
    phone: str | None
    role: str
    is_active: bool


@router.get("/reps", response_model=list[RepOut])
async def list_reps(db: AsyncSession = Depends(get_db)):
    """List all reps."""
    result = await db.execute(select(RepUser).order_by(RepUser.name))
    reps = result.scalars().all()
    return [
        RepOut(
            id=r.id,
            email=r.email,
            name=r.name,
            phone=r.phone,
            role=r.role.value,
            is_active=r.is_active,
        )
        for r in reps
    ]
