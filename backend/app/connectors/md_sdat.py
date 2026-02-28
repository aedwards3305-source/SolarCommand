"""Maryland SDAT connector — pulls real property data from Maryland Open Data Portal.

Uses the Socrata Open Data API (SODA) — free, no API key required.
County-level datasets with verbose SDAT field names.

Supports full pagination to capture ALL residential properties (SFH, townhome,
condo, multi-family) — not just the top N by assessed value.
"""

import asyncio
import logging
import re
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schema import Lead, LeadStatus, Property, PropertyType
from app.services.scoring import score_lead

logger = logging.getLogger(__name__)

# County → SODA dataset ID
COUNTY_DATASETS: dict[str, str] = {
    "Baltimore County": "jpfc-qkxp",
    "Howard County": "9t52-zebk",
    "Anne Arundel County": "3w75-7rie",
    "Montgomery County": "kb22-is2w",
    "Prince George's County": "w3eb-4mzd",
}

# Real SDAT field names (the long verbose ones)
F_ADDRESS = "mdp_street_address_mdp_field_address"
F_CITY = "mdp_street_address_city_mdp_field_city"
F_ZIP = "mdp_street_address_zip_code_mdp_field_zipcode"
F_COUNTY = "county_name_mdp_field_cntyname"
F_YEAR_BUILT = "c_a_m_a_system_data_year_built_yyyy_mdp_field_yearblt_sdat_field_235"
F_SQFT = "c_a_m_a_system_data_structure_area_sq_ft_mdp_field_sqftstrc_sdat_field_241"
F_ASSESSED = "current_assessment_year_total_assessment_sdat_field_172"
F_LAND_USE = "land_use_code_mdp_field_lu_desclu_sdat_field_50"
F_LAT = "mdp_latitude_mdp_field_digycord_converted_to_wgs84"
F_LON = "mdp_longitude_mdp_field_digxcord_converted_to_wgs84"
F_ACCOUNT = "account_id_mdp_field_acctid"
F_OOI = "record_key_owner_occupancy_code_mdp_field_ooi_sdat_field_6"
# Fallback address from premise fields
F_PREM_NUM = "premise_address_number_mdp_field_premsnum_sdat_field_20"
F_PREM_DIR = "premise_address_direction_mdp_field_premsdir_sdat_field_22"
F_PREM_NAME = "premise_address_name_mdp_field_premsnam_sdat_field_23"
F_PREM_TYPE = "premise_address_type_mdp_field_premstyp_sdat_field_24"
F_PREM_CITY = "premise_address_city_mdp_field_premcity_sdat_field_25"
F_PREM_ZIP = "premise_address_zip_code_mdp_field_premzip_sdat_field_26"

# Land-use code extraction: "Residential (R)" → "R"
LAND_USE_RE = re.compile(r"\(([^)]+)\)")

LAND_USE_MAP: dict[str, PropertyType] = {
    "R": PropertyType.SFH,
    "TH": PropertyType.TOWNHOME,
    "MF": PropertyType.MULTI_FAMILY,
    "CO": PropertyType.CONDO,
}

# Land-use codes to fetch from SODA API — SFH + townhomes + condos + multi-family
RESIDENTIAL_LAND_USE_CODES = [
    "Residential (R)",
    "Residential Townhouse (TH)",
    "Residential Condominium (CO)",
    "Residential Multi-Family (MF)",
]

# Maryland zip code → utility company mapping
# BGE serves central MD, Pepco serves DC suburbs, SMECO serves southern MD,
# Delmarva serves Eastern Shore, Potomac Edison serves western MD
MD_ZIP_UTILITY: dict[str, str] = {}

# BGE — Baltimore Gas & Electric (Exelon)
# Baltimore City, Baltimore County, Anne Arundel, Howard, Harford, Cecil (partial)
for _z in [
    *range(21001, 21058), *range(21060, 21095), *range(21102, 21163),
    *range(21201, 21298), *range(21401, 21412), 21701, 21702,
    *range(21220, 21238), *range(21784, 21798),
    21042, 21043, 21044, 21045, 21046, 21075, 21076, 21090, 21093, 21094,
    21108, 21113, 21114, 21122, 21144, 21146, 21225, 21226, 21227, 21228,
    21229, 21230, 21244, 21250, 21286,
]:
    MD_ZIP_UTILITY[str(_z)] = "BGE"

# Pepco — Potomac Electric Power (Exelon)
# Montgomery County, Prince George's County
for _z in [
    *range(20601, 20623), *range(20700, 20800), *range(20810, 20920),
    20901, 20902, 20903, 20904, 20905, 20906, 20910, 20912,
    20850, 20851, 20852, 20853, 20854, 20855, 20860, 20861, 20862,
    20871, 20872, 20874, 20876, 20877, 20878, 20879, 20880, 20882, 20886,
    20770, 20771, 20772, 20774, 20781, 20782, 20783, 20784, 20785,
]:
    MD_ZIP_UTILITY[str(_z)] = "Pepco"

# SMECO — Southern Maryland Electric Cooperative
for _z in [20601, 20602, 20603, 20607, 20608, 20611, 20613, 20616, 20617,
           20618, 20619, 20620, 20621, 20622, 20623, 20624, 20625, 20628,
           20630, 20632, 20634, 20636, 20637, 20639, 20640, 20643, 20645,
           20646, 20650, 20653, 20657, 20658, 20659, 20661, 20662, 20667,
           20670, 20674, 20675, 20676, 20677, 20678, 20680, 20684, 20685,
           20686, 20687, 20688, 20689, 20690, 20692, 20693, 20695]:
    MD_ZIP_UTILITY.setdefault(str(_z), "SMECO")


def _lookup_utility(zip_code: str) -> str | None:
    """Look up the electric utility for a Maryland zip code."""
    z = (zip_code or "").strip()[:5]
    return MD_ZIP_UTILITY.get(z)


def _extract_land_use_code(raw: str) -> str:
    """Extract code from 'Residential (R)' → 'R'."""
    match = LAND_USE_RE.search(raw)
    return match.group(1).strip() if match else raw.strip()


def _build_residential_where() -> str:
    """Build SODA $where clause that captures all residential property types.

    Uses starts_with() to keep the URL short — Cloudflare blocks long URLs.
    This catches: Residential (R), Residential Townhouse (TH),
    Residential Condominium (CO), Residential Multi-Family (MF), and any
    other residential codes we don't know about yet.
    """
    return f"starts_with({F_LAND_USE}, 'Residential')"


async def fetch_county_properties(
    county: str,
    limit: int = 1000,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Fetch one page of residential properties from Maryland Open Data."""
    dataset_id = COUNTY_DATASETS.get(county)
    if not dataset_id:
        raise ValueError(
            f"Unknown county '{county}'. Available: {', '.join(COUNTY_DATASETS)}"
        )

    url = f"https://opendata.maryland.gov/resource/{dataset_id}.json"
    where = _build_residential_where()

    params = {
        "$where": where,
        "$limit": str(limit),
        "$offset": str(offset),
        "$order": f"{F_ASSESSED} DESC",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(
            url, params=params,
            headers={"User-Agent": "SolarCommand/1.0", "Accept": "application/json"},
        )
        resp.raise_for_status()
        records = resp.json()

    return records


async def fetch_all_county_properties(
    county: str,
    max_records: int = 10000,
    page_size: int = 1000,
) -> list[dict[str, Any]]:
    """Paginate through residential properties until limit reached or data exhausted.

    Args:
        county: County name (must be in COUNTY_DATASETS)
        max_records: Maximum total records to fetch (safety cap)
        page_size: Records per API request (max ~50000, but 1000 is safe for Cloudflare)

    Returns:
        List of raw SODA records
    """
    all_records: list[dict[str, Any]] = []
    offset = 0

    while len(all_records) < max_records:
        # Don't fetch more than we need
        remaining = max_records - len(all_records)
        fetch_limit = min(page_size, remaining)

        records = await fetch_county_properties(county, limit=fetch_limit, offset=offset)

        if not records:
            logger.info(
                "No more records at offset %d for %s — total fetched: %d",
                offset, county, len(all_records),
            )
            break

        all_records.extend(records)
        offset += len(records)

        logger.info(
            "Fetched page: %d records (offset %d, total so far: %d) for %s",
            len(records), offset, len(all_records), county,
        )

        # If we got fewer than requested, we've hit the end of the dataset
        if len(records) < fetch_limit:
            break

        # Rate limit: ~1 req/sec to be polite to the SODA API
        await asyncio.sleep(0.5)

    logger.info(
        "Fetch complete: %d total records from %s (max was %d)",
        len(all_records), county, max_records,
    )
    return all_records


def _safe_float(val: Any) -> float | None:
    try:
        return float(val) if val is not None else None
    except (ValueError, TypeError):
        return None


def _safe_int(val: Any) -> int | None:
    try:
        v = int(float(val)) if val is not None else None
        return v if v and v > 0 else None
    except (ValueError, TypeError):
        return None


def _build_address(record: dict[str, Any]) -> str:
    """Build street address from MDP address or premise fields."""
    # Try the MDP consolidated address first
    addr = (record.get(F_ADDRESS) or "").strip()
    if addr:
        return addr

    # Fall back to premise address components
    num = (record.get(F_PREM_NUM) or "").strip().lstrip("0")
    direction = (record.get(F_PREM_DIR) or "").strip()
    name = (record.get(F_PREM_NAME) or "").strip()
    typ = (record.get(F_PREM_TYPE) or "").strip()

    parts = [p for p in [num, direction, name, typ] if p]
    return " ".join(parts)


def map_to_property_kwargs(record: dict[str, Any]) -> dict[str, Any]:
    """Map a SODA record to Property model constructor kwargs."""
    raw_lu = record.get(F_LAND_USE, "Residential (R)")
    code = _extract_land_use_code(raw_lu)
    prop_type = LAND_USE_MAP.get(code, PropertyType.OTHER)

    ooi = (record.get(F_OOI) or "").strip().upper()
    owner_occupied = ooi != "N"  # Y, 1, or blank → True; N → False

    city = (record.get(F_CITY) or record.get(F_PREM_CITY) or "").strip()
    zip_code = (record.get(F_ZIP) or record.get(F_PREM_ZIP) or "").strip()

    return {
        "address_line1": _build_address(record),
        "city": city.title(),  # "COCKEYSVILLE" → "Cockeysville"
        "state": "MD",
        "zip_code": zip_code,
        "county": (record.get(F_COUNTY) or "").strip(),
        "parcel_id": (record.get(F_ACCOUNT) or "").strip() or None,
        "property_type": prop_type,
        "year_built": _safe_int(record.get(F_YEAR_BUILT)),
        "roof_area_sqft": _safe_float(record.get(F_SQFT)),
        "assessed_value": _safe_float(record.get(F_ASSESSED)),
        "latitude": _safe_float(record.get(F_LAT)),
        "longitude": _safe_float(record.get(F_LON)),
        "owner_occupied": owner_occupied,
        "utility_zone": _lookup_utility(zip_code),
        "data_source": "md_sdat",
    }


async def run_discovery(
    db: AsyncSession,
    county: str,
    limit: int = 1000,
) -> dict[str, int]:
    """Pull properties from MD Open Data, ingest, and score them.

    Uses pagination to fetch up to `limit` records, walking through the full
    dataset instead of only getting the first page.

    Returns: { ingested, scored, skipped, errors }
    """
    records = await fetch_all_county_properties(county, max_records=limit)

    ingested = 0
    scored = 0
    skipped = 0
    errors = 0

    for i, record in enumerate(records):
        try:
            kwargs = map_to_property_kwargs(record)

            # Skip if missing address or zip
            if not kwargs["address_line1"] or not kwargs["zip_code"]:
                skipped += 1
                continue

            # Skip if no coordinates (allow ingestion of properties without coords
            # only if we have a valid address — they just won't show on the map)
            if kwargs["latitude"] is None or kwargs["longitude"] is None:
                skipped += 1
                continue

            # Deduplicate by parcel_id
            if kwargs["parcel_id"]:
                existing = await db.execute(
                    select(Property.id).where(
                        Property.parcel_id == kwargs["parcel_id"]
                    )
                )
                if existing.scalar_one_or_none():
                    skipped += 1
                    continue

            # Also deduplicate by address + zip
            existing_addr = await db.execute(
                select(Property.id).where(
                    Property.address_line1 == kwargs["address_line1"],
                    Property.zip_code == kwargs["zip_code"],
                )
            )
            if existing_addr.scalar_one_or_none():
                skipped += 1
                continue

            # Create property
            prop = Property(**kwargs)
            db.add(prop)
            await db.flush()

            # Create lead
            lead = Lead(
                property_id=prop.id,
                status=LeadStatus.ingested,
            )
            db.add(lead)
            await db.flush()

            ingested += 1

            # Score immediately
            try:
                await score_lead(db, lead.id)
                scored += 1
            except Exception as e:
                logger.warning("Scoring failed for lead %d: %s", lead.id, e)

        except Exception as e:
            logger.error("Error ingesting record: %s", e)
            errors += 1

        # Commit in batches of 100 to avoid huge transactions
        if ingested > 0 and ingested % 100 == 0:
            await db.commit()
            logger.info(
                "Progress: %d/%d ingested (%d scored, %d skipped, %d errors)",
                ingested, len(records), scored, skipped, errors,
            )

    # Backfill utility_zone for any existing properties that are missing it
    backfill_result = await db.execute(
        select(Property).where(
            Property.utility_zone.is_(None),
            Property.zip_code.isnot(None),
            Property.state == "MD",
        )
    )
    backfilled = 0
    for prop in backfill_result.scalars():
        utility = _lookup_utility(prop.zip_code)
        if utility:
            prop.utility_zone = utility
            backfilled += 1

    await db.commit()

    if backfilled:
        logger.info("Backfilled utility_zone for %d existing properties", backfilled)

    logger.info(
        "Discovery complete: county=%s ingested=%d scored=%d skipped=%d errors=%d (fetched %d from API)",
        county, ingested, scored, skipped, errors, len(records),
    )
    return {
        "ingested": ingested,
        "scored": scored,
        "skipped": skipped,
        "errors": errors,
    }
