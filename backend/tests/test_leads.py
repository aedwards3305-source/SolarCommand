"""Tests for lead API endpoints (requires running DB — integration tests)."""

import pytest


@pytest.mark.skip(reason="Requires database — run with docker-compose up")
class TestLeadIngest:
    async def test_ingest_creates_property_and_lead(self, client, sample_property_payload):
        response = await client.post("/leads/ingest", json=sample_property_payload)
        assert response.status_code == 201
        data = response.json()
        assert "property_id" in data
        assert "lead_id" in data

    async def test_ingest_duplicate_parcel_rejects(self, client, sample_property_payload):
        await client.post("/leads/ingest", json=sample_property_payload)
        response = await client.post("/leads/ingest", json=sample_property_payload)
        assert response.status_code == 409


@pytest.mark.skip(reason="Requires database — run with docker-compose up")
class TestLeadScore:
    async def test_score_returns_score_and_tier(self, client, sample_property_payload):
        ingest_resp = await client.post("/leads/ingest", json=sample_property_payload)
        lead_id = ingest_resp.json()["lead_id"]

        response = await client.post(f"/leads/{lead_id}/score")
        assert response.status_code == 200
        data = response.json()
        assert "total_score" in data
        assert "tier" in data
        assert data["tier"] in ("hot", "warm", "cool")

    async def test_score_nonexistent_lead_404(self, client):
        response = await client.post("/leads/99999/score")
        assert response.status_code == 404
