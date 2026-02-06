"""Test fixtures for SolarCommand."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    """Async HTTP client for testing FastAPI endpoints."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.fixture
def sample_property_payload():
    """Sample property ingest payload."""
    return {
        "address_line1": "123 Oak Street",
        "city": "Annapolis",
        "state": "MD",
        "zip_code": "21401",
        "county": "Anne Arundel",
        "parcel_id": "TEST-001",
        "property_type": "SFH",
        "year_built": 2010,
        "roof_area_sqft": 1800.0,
        "assessed_value": 425000.0,
        "utility_zone": "BGE",
        "tree_cover_pct": 15.0,
        "neighborhood_solar_pct": 8.0,
        "has_existing_solar": False,
        "owner_first_name": "John",
        "owner_last_name": "Smith",
        "owner_occupied": True,
        "owner_phone": "+14105551234",
        "owner_email": "john@example.com",
        "median_household_income": 95000.0,
        "data_source": "test",
    }
