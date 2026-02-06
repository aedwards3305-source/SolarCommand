"""Tests for dashboard KPI endpoint (requires running DB, marked skip for CI)."""

import pytest


@pytest.mark.skip(reason="Requires running database")
class TestDashboardKPIs:
    async def test_kpis_returns_200(self, client):
        resp = await client.get("/dashboard/kpis")
        assert resp.status_code == 200

    async def test_kpis_has_required_fields(self, client):
        resp = await client.get("/dashboard/kpis")
        data = resp.json()
        required = [
            "total_leads", "hot_leads", "warm_leads", "cool_leads",
            "appointments_scheduled", "appointments_completed",
            "total_outreach_attempts", "avg_score", "conversion_rate",
            "status_breakdown",
        ]
        for field in required:
            assert field in data, f"Missing field: {field}"

    async def test_kpis_values_are_non_negative(self, client):
        resp = await client.get("/dashboard/kpis")
        data = resp.json()
        for field in ["total_leads", "hot_leads", "warm_leads", "cool_leads"]:
            assert data[field] >= 0
