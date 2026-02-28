"""QA Review endpoints — per-lead and admin queue."""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.schema import Lead, QAReview

router = APIRouter(tags=["qa"])

# ── Auth-protected lead-level QA ─────────────────────────────────────────

lead_router = APIRouter(
    prefix="/leads",
    dependencies=[Depends(get_current_user)],
)


class QAReviewOut(BaseModel):
    id: int
    lead_id: int
    conversation_id: int | None
    compliance_score: int
    flags: list | None
    checklist_pass: bool
    rationale: str | None
    reviewed_by: str
    created_at: str


@lead_router.get("/{lead_id}/qa", response_model=list[QAReviewOut])
async def get_lead_qa(lead_id: int, db: AsyncSession = Depends(get_db)):
    """Get QA reviews for a specific lead."""
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    result = await db.execute(
        select(QAReview)
        .where(QAReview.lead_id == lead_id)
        .order_by(QAReview.created_at.desc())
    )
    reviews = result.scalars().all()

    return [
        QAReviewOut(
            id=r.id,
            lead_id=r.lead_id,
            conversation_id=r.conversation_id,
            compliance_score=r.compliance_score,
            flags=r.flags,
            checklist_pass=r.checklist_pass,
            rationale=r.rationale,
            reviewed_by=r.reviewed_by,
            created_at=r.created_at.isoformat() if r.created_at else "",
        )
        for r in reviews
    ]


# ── Admin QA queue ───────────────────────────────────────────────────────

admin_router = APIRouter(
    prefix="/admin",
    dependencies=[Depends(require_role("admin"))],
)


class QAQueueItem(BaseModel):
    id: int
    lead_id: int
    lead_name: str
    conversation_id: int | None
    compliance_score: int
    flags: list | None
    checklist_pass: bool
    reviewed_by: str
    created_at: str


@admin_router.get("/qa", response_model=list[QAQueueItem])
async def get_qa_queue(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    min_score: int | None = None,
    max_score: int | None = None,
    flagged_only: bool = False,
):
    """Admin QA review queue with filters."""
    query = select(QAReview, Lead).join(Lead, QAReview.lead_id == Lead.id)

    if min_score is not None:
        query = query.where(QAReview.compliance_score >= min_score)
    if max_score is not None:
        query = query.where(QAReview.compliance_score <= max_score)
    if flagged_only:
        query = query.where(QAReview.checklist_pass.is_(False))

    query = query.order_by(QAReview.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    rows = result.all()

    return [
        QAQueueItem(
            id=qa.id,
            lead_id=qa.lead_id,
            lead_name=f"{lead.first_name or ''} {lead.last_name or ''}".strip() or "Unknown",
            conversation_id=qa.conversation_id,
            compliance_score=qa.compliance_score,
            flags=qa.flags,
            checklist_pass=qa.checklist_pass,
            reviewed_by=qa.reviewed_by,
            created_at=qa.created_at.isoformat() if qa.created_at else "",
        )
        for qa, lead in rows
    ]


router.include_router(lead_router)
router.include_router(admin_router)
