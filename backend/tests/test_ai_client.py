"""Tests for AI client fallback behavior (no API key needed)."""

import pytest

from app.services.ai_client import AIClient


@pytest.fixture
def client():
    """AI client with no API key (uses fallback)."""
    c = AIClient()
    c.api_key = ""  # Force fallback mode
    return c


class TestAIClientFallback:
    """Verify deterministic fallback when AI provider is not configured."""

    @pytest.mark.asyncio
    async def test_sms_agent_fallback(self, client):
        result = await client.chat(
            "You are an SMS reply agent...",
            "Lead says: Hello",
        )
        assert result["intent"] == "unknown"
        assert result["requires_human"] is True
        assert isinstance(result["actions"], list)

    @pytest.mark.asyncio
    async def test_qa_review_fallback(self, client):
        result = await client.chat(
            "You are a QA compliance reviewer...",
            "Transcript: ...",
        )
        assert result["compliance_score"] == 70
        assert result["checklist_pass"] is True

    @pytest.mark.asyncio
    async def test_objection_fallback(self, client):
        result = await client.chat(
            "Extract objection tags...",
            "Transcript: ...",
        )
        assert result["tags"] == []

    @pytest.mark.asyncio
    async def test_nba_fallback(self, client):
        result = await client.chat(
            "Decide the next best action...",
            "Lead info: ...",
        )
        assert result["next_action"] == "wait"
        assert result["confidence"] == 0.0

    @pytest.mark.asyncio
    async def test_script_fallback(self, client):
        result = await client.chat(
            "Propose script edits...",
            "Current script: ...",
        )
        assert result["edits"] == []

    @pytest.mark.asyncio
    async def test_generic_fallback(self, client):
        result = await client.chat(
            "Some unknown prompt type",
            "Something",
        )
        assert result.get("fallback") is True

    def test_enabled_property_false(self, client):
        assert client.enabled is False

    def test_enabled_property_true(self, client):
        client.api_key = "sk-test"
        assert client.enabled is True
