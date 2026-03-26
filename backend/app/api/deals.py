"""Sales / Deals endpoints — record, list, update closed deals."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.schema import (
    AuditLog,
    DealStatus,
    FinancingType,
    Lead,
    LeadStatus,
    Property,
    RepUser,
    Sale,
)

router = APIRouter(prefix="/sales/deals", tags=["deals"], dependencies=[Depends(get_current_user)])


# ── Schemas ───────────────────────────────────────────────────────────────


class DealCreate(BaseModel):
    lead_id: int
    contract_value: float
    system_size_kw: float
    financing_type: str = "cash"
    commission_amount: float | None = None
    adders_total: float | None = None
    panel_count: int | None = None
    panel_brand: str | None = None
    inverter_type: str | None = None
    battery_included: bool = False
    annual_production_kwh: float | None = None
    sale_date: datetime
    install_date: datetime | None = None
    notes: str | None = None


class DealUpdate(BaseModel):
    contract_value: float | None = None
    system_size_kw: float | None = None
    financing_type: str | None = None
    commission_amount: float | None = None
    adders_total: float | None = None
    panel_count: int | None = None
    panel_brand: str | None = None
    inverter_type: str | None = None
    battery_included: bool | None = None
    annual_production_kwh: float | None = None
    status: str | None = None
    install_date: datetime | None = None
    pto_date: datetime | None = None
    notes: str | None = None


class DealOut(BaseModel):
    id: int
    lead_id: int
    rep_id: int
    rep_name: str | None
    contract_value: float
    system_size_kw: float
    financing_type: str
    commission_amount: float | None
    adders_total: float | None
    panel_count: int | None
    panel_brand: str | None
    inverter_type: str | None
    battery_included: bool
    annual_production_kwh: float | None
    status: str
    sale_date: str
    install_date: str | None
    pto_date: str | None
    customer_name: str
    customer_address: str | None
    customer_phone: str | None
    customer_email: str | None
    notes: str | None
    created_at: str


class DealsSummary(BaseModel):
    total_deals: int
    total_revenue: float
    total_commission: float
    avg_deal_value: float
    total_kw_sold: float
    deals_by_status: dict[str, int]
    deals_by_financing: dict[str, int]


# ── Helpers ───────────────────────────────────────────────────────────────


async def sale_to_out(sale: Sale, db: AsyncSession) -> DealOut:
    rep = await db.get(RepUser, sale.rep_id)
    return DealOut(
        id=sale.id,
        lead_id=sale.lead_id,
        rep_id=sale.rep_id,
        rep_name=rep.name if rep else None,
        contract_value=sale.contract_value,
        system_size_kw=sale.system_size_kw,
        financing_type=sale.financing_type.value,
        commission_amount=sale.commission_amount,
        adders_total=sale.adders_total,
        panel_count=sale.panel_count,
        panel_brand=sale.panel_brand,
        inverter_type=sale.inverter_type,
        battery_included=sale.battery_included,
        annual_production_kwh=sale.annual_production_kwh,
        status=sale.status.value,
        sale_date=sale.sale_date.isoformat(),
        install_date=sale.install_date.isoformat() if sale.install_date else None,
        pto_date=sale.pto_date.isoformat() if sale.pto_date else None,
        customer_name=sale.customer_name,
        customer_address=sale.customer_address,
        customer_phone=sale.customer_phone,
        customer_email=sale.customer_email,
        notes=sale.notes,
        created_at=sale.created_at.isoformat(),
    )


# ── Endpoints ─────────────────────────────────────────────────────────────


@router.post("", response_model=DealOut, status_code=status.HTTP_201_CREATED)
async def create_deal(
    payload: DealCreate,
    current_user: RepUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Record a new sale / closed deal."""
    lead = await db.get(Lead, payload.lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Get customer info from lead + property
    prop = await db.get(Property, lead.property_id)
    customer_name = f"{lead.first_name or ''} {lead.last_name or ''}".strip() or "Unknown"
    customer_address = prop.address_line1 if prop else None
    customer_phone = lead.phone
    customer_email = lead.email

    try:
        financing = FinancingType(payload.financing_type)
    except ValueError:
        financing = FinancingType.cash

    sale = Sale(
        lead_id=lead.id,
        rep_id=current_user.id,
        contract_value=payload.contract_value,
        system_size_kw=payload.system_size_kw,
        financing_type=financing,
        commission_amount=payload.commission_amount,
        adders_total=payload.adders_total,
        panel_count=payload.panel_count,
        panel_brand=payload.panel_brand,
        inverter_type=payload.inverter_type,
        battery_included=payload.battery_included,
        annual_production_kwh=payload.annual_production_kwh,
        sale_date=payload.sale_date,
        install_date=payload.install_date,
        status=DealStatus.pending_contract,
        customer_name=customer_name,
        customer_address=customer_address,
        customer_phone=customer_phone,
        customer_email=customer_email,
        notes=payload.notes,
    )
    db.add(sale)

    # Mark lead as closed_won
    lead.status = LeadStatus.closed_won
    if not lead.assigned_rep_id:
        lead.assigned_rep_id = current_user.id

    db.add(AuditLog(
        actor=current_user.name,
        action="sale.created",
        entity_type="sale",
        entity_id=sale.id,
        new_value=f"lead={lead.id}, value=${payload.contract_value}, size={payload.system_size_kw}kW",
    ))

    await db.flush()
    return await sale_to_out(sale, db)


@router.get("", response_model=list[DealOut])
async def list_deals(
    current_user: RepUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    mine_only: bool = Query(default=False),
    status_filter: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, le=100),
):
    """List all deals, optionally filtered."""
    query = select(Sale)

    if mine_only:
        query = query.where(Sale.rep_id == current_user.id)
    if status_filter:
        try:
            query = query.where(Sale.status == DealStatus(status_filter))
        except ValueError:
            pass

    query = query.order_by(Sale.sale_date.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    sales = result.scalars().all()
    return [await sale_to_out(s, db) for s in sales]


@router.get("/summary", response_model=DealsSummary)
async def deals_summary(
    current_user: RepUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    mine_only: bool = Query(default=False),
):
    """Aggregate deal metrics."""
    base = select(Sale)
    if mine_only:
        base = base.where(Sale.rep_id == current_user.id)

    # Totals
    total = (await db.execute(select(func.count(Sale.id)).select_from(base.subquery()))).scalar() or 0
    revenue = (await db.execute(
        select(func.sum(Sale.contract_value)).where(Sale.status != DealStatus.cancelled)
        .where(Sale.rep_id == current_user.id if mine_only else True)
    )).scalar() or 0.0
    commission = (await db.execute(
        select(func.sum(Sale.commission_amount)).where(Sale.status != DealStatus.cancelled)
        .where(Sale.rep_id == current_user.id if mine_only else True)
    )).scalar() or 0.0
    kw = (await db.execute(
        select(func.sum(Sale.system_size_kw)).where(Sale.status != DealStatus.cancelled)
        .where(Sale.rep_id == current_user.id if mine_only else True)
    )).scalar() or 0.0

    avg_val = revenue / total if total > 0 else 0.0

    # By status
    status_result = await db.execute(
        select(Sale.status, func.count(Sale.id))
        .where(Sale.rep_id == current_user.id if mine_only else True)
        .group_by(Sale.status)
    )
    by_status = {row[0].value: row[1] for row in status_result.all()}

    # By financing
    fin_result = await db.execute(
        select(Sale.financing_type, func.count(Sale.id))
        .where(Sale.rep_id == current_user.id if mine_only else True)
        .group_by(Sale.financing_type)
    )
    by_financing = {row[0].value: row[1] for row in fin_result.all()}

    return DealsSummary(
        total_deals=total,
        total_revenue=round(revenue, 2),
        total_commission=round(commission, 2),
        avg_deal_value=round(avg_val, 2),
        total_kw_sold=round(kw, 2),
        deals_by_status=by_status,
        deals_by_financing=by_financing,
    )


@router.get("/{deal_id}", response_model=DealOut)
async def get_deal(
    deal_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: RepUser = Depends(get_current_user),
):
    """Get a single deal."""
    sale = await db.get(Sale, deal_id)
    if not sale:
        raise HTTPException(status_code=404, detail="Deal not found")
    return await sale_to_out(sale, db)


@router.put("/{deal_id}", response_model=DealOut)
async def update_deal(
    deal_id: int,
    payload: DealUpdate,
    current_user: RepUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a deal — status, financials, install date, etc."""
    sale = await db.get(Sale, deal_id)
    if not sale:
        raise HTTPException(status_code=404, detail="Deal not found")

    changes = []

    if payload.contract_value is not None:
        old = sale.contract_value
        sale.contract_value = payload.contract_value
        changes.append(f"value ${old} → ${payload.contract_value}")
    if payload.system_size_kw is not None:
        sale.system_size_kw = payload.system_size_kw
    if payload.financing_type is not None:
        try:
            sale.financing_type = FinancingType(payload.financing_type)
        except ValueError:
            pass
    if payload.commission_amount is not None:
        sale.commission_amount = payload.commission_amount
    if payload.adders_total is not None:
        sale.adders_total = payload.adders_total
    if payload.panel_count is not None:
        sale.panel_count = payload.panel_count
    if payload.panel_brand is not None:
        sale.panel_brand = payload.panel_brand
    if payload.inverter_type is not None:
        sale.inverter_type = payload.inverter_type
    if payload.battery_included is not None:
        sale.battery_included = payload.battery_included
    if payload.annual_production_kwh is not None:
        sale.annual_production_kwh = payload.annual_production_kwh
    if payload.status is not None:
        old_status = sale.status.value
        try:
            sale.status = DealStatus(payload.status)
            changes.append(f"status {old_status} → {payload.status}")
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {payload.status}")
    if payload.install_date is not None:
        sale.install_date = payload.install_date
    if payload.pto_date is not None:
        sale.pto_date = payload.pto_date
    if payload.notes is not None:
        sale.notes = payload.notes

    if changes:
        db.add(AuditLog(
            actor=current_user.name,
            action="sale.updated",
            entity_type="sale",
            entity_id=sale.id,
            new_value="; ".join(changes),
        ))

    await db.flush()
    return await sale_to_out(sale, db)
