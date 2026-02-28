"""Script experiment and suggestion endpoints (admin-only)."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_role
from app.models.schema import ScriptExperiment, ScriptVersion
from app.workers.ai_tasks import task_script_suggest

router = APIRouter(
    prefix="/admin/scripts",
    tags=["scripts"],
    dependencies=[Depends(require_role("admin"))],
)


class ExperimentOut(BaseModel):
    id: int
    name: str
    channel: str
    control_script_id: int
    variant_script_id: int
    control_sends: int
    variant_sends: int
    control_responses: int
    variant_responses: int
    control_conversions: int
    variant_conversions: int
    is_active: bool
    started_at: str
    ended_at: str | None

    # Computed metrics
    control_response_rate: float
    variant_response_rate: float
    control_conversion_rate: float
    variant_conversion_rate: float


@router.get("/experiments", response_model=list[ExperimentOut])
async def list_experiments(db: AsyncSession = Depends(get_db)):
    """List script A/B experiments with metrics."""
    result = await db.execute(
        select(ScriptExperiment).order_by(ScriptExperiment.started_at.desc())
    )
    experiments = result.scalars().all()

    return [
        ExperimentOut(
            id=e.id,
            name=e.name,
            channel=e.channel.value if e.channel else "",
            control_script_id=e.control_script_id,
            variant_script_id=e.variant_script_id,
            control_sends=e.control_sends,
            variant_sends=e.variant_sends,
            control_responses=e.control_responses,
            variant_responses=e.variant_responses,
            control_conversions=e.control_conversions,
            variant_conversions=e.variant_conversions,
            is_active=e.is_active,
            started_at=e.started_at.isoformat() if e.started_at else "",
            ended_at=e.ended_at.isoformat() if e.ended_at else None,
            control_response_rate=(
                e.control_responses / e.control_sends * 100 if e.control_sends > 0 else 0.0
            ),
            variant_response_rate=(
                e.variant_responses / e.variant_sends * 100 if e.variant_sends > 0 else 0.0
            ),
            control_conversion_rate=(
                e.control_conversions / e.control_sends * 100 if e.control_sends > 0 else 0.0
            ),
            variant_conversion_rate=(
                e.variant_conversions / e.variant_sends * 100 if e.variant_sends > 0 else 0.0
            ),
        )
        for e in experiments
    ]


class SuggestResponse(BaseModel):
    edits: list
    hypotheses: list
    expected_lift: float


@router.post("/{script_id}/suggest", response_model=SuggestResponse)
async def suggest_script_revision(
    script_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Generate AI-suggested script revision (returns proposal, doesn't auto-activate)."""
    script = await db.get(ScriptVersion, script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    # Run synchronously for immediate response (small task)
    result = task_script_suggest.apply(
        args=[script.channel.value, script_id, 30]
    ).get(timeout=60)

    return SuggestResponse(
        edits=result.get("edits", []),
        hypotheses=result.get("hypotheses", []),
        expected_lift=result.get("expected_lift", 0.0),
    )
