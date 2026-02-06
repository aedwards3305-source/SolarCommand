"""Tests for lead detail, notes, consent, status endpoints (requires running DB)."""

import pytest


@pytest.mark.skip(reason="Requires running database")
class TestLeadDetail:
    async def test_get_lead_detail_404(self, client):
        resp = await client.get("/leads/99999")
        assert resp.status_code == 404

    async def test_lead_detail_includes_property(self, client, sample_property_payload):
        # Ingest first
        ingest = await client.post("/leads/ingest", json=sample_property_payload)
        lead_id = ingest.json()["lead_id"]

        resp = await client.get(f"/leads/{lead_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert "property" in data
        assert data["property"]["county"] == "Anne Arundel"
        assert "scores" in data
        assert "notes" in data
        assert "consent_logs" in data
        assert "recent_outreach" in data


@pytest.mark.skip(reason="Requires running database")
class TestNotes:
    async def test_add_and_list_notes(self, client, sample_property_payload):
        ingest = await client.post("/leads/ingest", json=sample_property_payload)
        lead_id = ingest.json()["lead_id"]

        # Add note
        resp = await client.post(
            f"/leads/{lead_id}/notes",
            json={"content": "Test note", "author": "tester"},
        )
        assert resp.status_code == 201
        assert resp.json()["content"] == "Test note"

        # List notes
        resp = await client.get(f"/leads/{lead_id}/notes")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1


@pytest.mark.skip(reason="Requires running database")
class TestConsent:
    async def test_record_consent(self, client, sample_property_payload):
        ingest = await client.post("/leads/ingest", json=sample_property_payload)
        lead_id = ingest.json()["lead_id"]

        resp = await client.post(
            f"/leads/{lead_id}/consent",
            json={
                "consent_type": "voice_call",
                "status": "opted_in",
                "channel": "voice",
                "evidence_type": "verbal",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == "opted_in"


@pytest.mark.skip(reason="Requires running database")
class TestStatusUpdate:
    async def test_update_lead_status(self, client, sample_property_payload):
        ingest = await client.post("/leads/ingest", json=sample_property_payload)
        lead_id = ingest.json()["lead_id"]

        resp = await client.patch(
            f"/leads/{lead_id}/status",
            json={"status": "hot"},
        )
        assert resp.status_code == 200
        assert resp.json()["new_status"] == "hot"

    async def test_invalid_status_returns_422(self, client, sample_property_payload):
        ingest = await client.post("/leads/ingest", json=sample_property_payload)
        lead_id = ingest.json()["lead_id"]

        resp = await client.patch(
            f"/leads/{lead_id}/status",
            json={"status": "nonexistent_status"},
        )
        assert resp.status_code == 422
