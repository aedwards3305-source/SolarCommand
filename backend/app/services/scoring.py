"""Solar Readiness Scoring Engine v1 (heuristic-based)."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schema import Lead, LeadScore, LeadStatus, Property


class ScoringResult:
    """Holds individual factor scores and total."""

    def __init__(self) -> None:
        self.roof_age_score: int = 0
        self.ownership_score: int = 0
        self.roof_area_score: int = 0
        self.home_value_score: int = 0
        self.utility_rate_score: int = 0
        self.shade_score: int = 0
        self.neighborhood_score: int = 0
        self.income_score: int = 0
        self.property_type_score: int = 0
        self.existing_solar_score: int = 0

    @property
    def total(self) -> int:
        return min(
            self.roof_age_score
            + self.ownership_score
            + self.roof_area_score
            + self.home_value_score
            + self.utility_rate_score
            + self.shade_score
            + self.neighborhood_score
            + self.income_score
            + self.property_type_score
            + self.existing_solar_score,
            100,
        )


def compute_score(prop: Property) -> ScoringResult:
    """Compute Solar Readiness Score from property data."""
    result = ScoringResult()
    current_year = datetime.now(tz=timezone.utc).year

    # ── Roof age (max 15) ──
    year_built = prop.year_built or 1970
    roof_age = current_year - year_built
    if roof_age < 5:
        result.roof_age_score = 15
    elif roof_age < 15:
        result.roof_age_score = 12
    elif roof_age < 25:
        result.roof_age_score = 8
    else:
        result.roof_age_score = 3

    # ── Ownership (max 15) ──
    result.ownership_score = 15 if prop.owner_occupied else 0

    # ── Roof area (max 15) ──
    roof_sqft = prop.roof_area_sqft or 0
    if roof_sqft > 1500:
        result.roof_area_score = 15
    elif roof_sqft > 1000:
        result.roof_area_score = 12
    elif roof_sqft > 500:
        result.roof_area_score = 8
    else:
        result.roof_area_score = 3

    # ── Home value (max 10) ──
    value = prop.assessed_value or 0
    if 250_000 <= value <= 750_000:
        result.home_value_score = 10
    elif 150_000 <= value < 250_000:
        result.home_value_score = 7
    elif value > 750_000:
        result.home_value_score = 5
    else:
        result.home_value_score = 2

    # ── Utility rate zone (max 10) ──
    if prop.utility_zone and prop.utility_zone.upper() == "BGE":
        result.utility_rate_score = 10
    else:
        result.utility_rate_score = 7

    # ── Shade / tree cover (max 10) ──
    shade_pct = prop.tree_cover_pct if prop.tree_cover_pct is not None else 50
    if shade_pct < 10:
        result.shade_score = 10
    elif shade_pct < 25:
        result.shade_score = 7
    elif shade_pct < 50:
        result.shade_score = 4
    else:
        result.shade_score = 1

    # ── Neighborhood solar adoption (max 10) ──
    adoption_pct = prop.neighborhood_solar_pct or 0
    if adoption_pct > 10:
        result.neighborhood_score = 10
    elif adoption_pct > 5:
        result.neighborhood_score = 7
    elif adoption_pct > 1:
        result.neighborhood_score = 4
    else:
        result.neighborhood_score = 1

    # ── Income bracket (max 8) ──
    income = prop.median_household_income or 0
    if 75_000 <= income <= 200_000:
        result.income_score = 8
    elif 50_000 <= income < 75_000:
        result.income_score = 5
    elif income > 200_000:
        result.income_score = 4
    else:
        result.income_score = 2

    # ── Property type (max 5) ──
    ptype = prop.property_type
    if ptype and ptype.value == "SFH":
        result.property_type_score = 5
    elif ptype and ptype.value == "TOWNHOME":
        result.property_type_score = 3
    else:
        result.property_type_score = 0

    # ── Existing solar (max 2) ──
    result.existing_solar_score = 0 if prop.has_existing_solar else 2

    return result


async def score_lead(db: AsyncSession, lead_id: int) -> LeadScore:
    """Score a lead and persist the result."""
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise ValueError(f"Lead {lead_id} not found")

    prop = await db.get(Property, lead.property_id)
    if not prop:
        raise ValueError(f"Property {lead.property_id} not found for lead {lead_id}")

    result = compute_score(prop)

    score_record = LeadScore(
        lead_id=lead.id,
        total_score=result.total,
        score_version="v1",
        roof_age_score=result.roof_age_score,
        ownership_score=result.ownership_score,
        roof_area_score=result.roof_area_score,
        home_value_score=result.home_value_score,
        utility_rate_score=result.utility_rate_score,
        shade_score=result.shade_score,
        neighborhood_score=result.neighborhood_score,
        income_score=result.income_score,
        property_type_score=result.property_type_score,
        existing_solar_score=result.existing_solar_score,
    )
    db.add(score_record)

    # Update lead status based on score — but never downgrade from protected statuses
    protected_statuses = {
        LeadStatus.appointment_set,
        LeadStatus.qualified,
        LeadStatus.closed_won,
    }
    if lead.status not in protected_statuses:
        if result.total >= 75:
            lead.status = LeadStatus.hot
        elif result.total >= 50:
            lead.status = LeadStatus.warm
        else:
            lead.status = LeadStatus.cool

    await db.flush()
    return score_record
