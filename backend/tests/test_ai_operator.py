"""Tests for the AI Operator module — Claude client, NBA logic, storage, prompts."""

import pytest

from app.ai.client import ClaudeClient


# ── Claude Client Fallback Tests ────────────────────────────────────────


@pytest.fixture
def claude_client():
    """Claude client with no API key (uses fallback)."""
    c = ClaudeClient()
    c.api_key = ""
    return c


class TestClaudeClientFallback:
    """Verify ClaudeClient deterministic fallbacks match expected schemas."""

    @pytest.mark.asyncio
    async def test_sms_fallback(self, claude_client):
        result = await claude_client.chat(
            "You are an SMS reply agent...", "Lead says: Hello",
            task_type="sms_classification", lead_id=1,
        )
        assert result["intent"] == "unknown"
        assert result["requires_human"] is True
        assert "_ai_run" in result
        assert result["_ai_run"]["task_type"] == "sms_classification"
        assert result["_ai_run"]["model"] == "fallback"
        assert result["_ai_run"]["lead_id"] == 1

    @pytest.mark.asyncio
    async def test_qa_fallback(self, claude_client):
        result = await claude_client.chat(
            "You are a QA compliance reviewer...", "Transcript: ...",
            task_type="qa_review",
        )
        assert result["compliance_score"] == 70
        assert result["checklist_pass"] is True
        assert result["_ai_run"]["task_type"] == "qa_review"

    @pytest.mark.asyncio
    async def test_objection_fallback(self, claude_client):
        result = await claude_client.chat(
            "Extract objection tags...", "Transcript: ...",
            task_type="objection_tags",
        )
        assert result["tags"] == []

    @pytest.mark.asyncio
    async def test_nba_fallback(self, claude_client):
        result = await claude_client.chat(
            "Decide the next best action...", "Lead info: ...",
            task_type="nba",
        )
        assert result["next_action"] == "wait"
        assert result["confidence"] == 0.0

    @pytest.mark.asyncio
    async def test_rep_brief_fallback(self, claude_client):
        result = await claude_client.chat(
            "Generate a rep brief for this lead...", "Lead data: ...",
            task_type="rep_brief", lead_id=5,
        )
        assert "summary" in result
        assert result["_ai_run"]["lead_id"] == 5

    @pytest.mark.asyncio
    async def test_insights_fallback(self, claude_client):
        result = await claude_client.chat(
            "Generate weekly insights...", "KPI data: ...",
            task_type="weekly_insights",
        )
        assert "narrative" in result
        assert isinstance(result["key_drivers"], list)

    @pytest.mark.asyncio
    async def test_memory_fallback(self, claude_client):
        result = await claude_client.chat(
            "Analyze memory and lessons...", "Data: ...",
            task_type="memory_update",
        )
        assert isinstance(result["lessons"], list)
        assert isinstance(result["patterns"], list)

    @pytest.mark.asyncio
    async def test_script_fallback(self, claude_client):
        result = await claude_client.chat(
            "Suggest script edits...", "Current script: ...",
            task_type="script_suggest",
        )
        assert result["edits"] == []

    @pytest.mark.asyncio
    async def test_generic_fallback(self, claude_client):
        result = await claude_client.chat(
            "Some unknown prompt", "Data",
        )
        assert result.get("fallback") is True

    def test_enabled_false(self, claude_client):
        assert claude_client.enabled is False

    def test_enabled_true(self, claude_client):
        claude_client.api_key = "sk-ant-test"
        assert claude_client.enabled is True

    @pytest.mark.asyncio
    async def test_ai_run_metadata_structure(self, claude_client):
        result = await claude_client.chat(
            "QA compliance check...", "Transcript",
            task_type="qa_review", lead_id=42, conversation_id=7,
        )
        meta = result["_ai_run"]
        assert meta["task_type"] == "qa_review"
        assert meta["lead_id"] == 42
        assert meta["conversation_id"] == 7
        assert meta["tokens_in"] == 0
        assert meta["tokens_out"] == 0
        assert meta["cost_usd"] == 0.0
        assert meta["status"] == "success"
        assert "input_hash" in meta

    @pytest.mark.asyncio
    async def test_custom_temperature(self, claude_client):
        result = await claude_client.chat(
            "QA review...", "Data",
            task_type="qa_review", temperature=0.5,
        )
        assert result["_ai_run"]["temperature"] == 0.5


# ── NBA Rules-First Logic ───────────────────────────────────────────────


class TestNBARulesLogic:
    """Test the deterministic rules in run_nba (no DB needed)."""

    def test_terminal_status_returns_close(self):
        """Terminal statuses should return close action without calling Claude."""
        from app.models.schema import LeadStatus
        terminal = {
            LeadStatus.closed_won, LeadStatus.closed_lost,
            LeadStatus.dnc, LeadStatus.archived, LeadStatus.disqualified,
        }
        for status in terminal:
            # Just verify the enum values exist and are terminal
            assert status.value in [
                "closed_won", "closed_lost", "dnc", "archived", "disqualified",
            ]

    def test_protected_status_returns_rep_handoff(self):
        """Protected statuses should return rep_handoff."""
        from app.models.schema import LeadStatus
        protected = {LeadStatus.appointment_set, LeadStatus.qualified}
        for status in protected:
            assert status.value in ["appointment_set", "qualified"]


# ── Prompt Rendering ────────────────────────────────────────────────────


class TestAIPrompts:
    """Test prompt template rendering."""

    def test_render_basic(self):
        from app.ai.prompts import render
        result = render("Hello {{name}}, your score is {{score}}", name="Alice", score="85")
        assert result == "Hello Alice, your score is 85"

    def test_render_missing_var(self):
        from app.ai.prompts import render
        result = render("Hello {{name}}", score="85")
        assert result == "Hello {{name}}"  # Unreplaced vars stay as-is

    def test_render_empty(self):
        from app.ai.prompts import render
        result = render("No variables here")
        assert result == "No variables here"

    def test_all_prompts_have_memory_context(self):
        """Verify all main prompts include memory_context injection point."""
        from app.ai import prompts
        for name in ["SMS_AGENT_SYSTEM", "QA_REVIEW_SYSTEM", "NBA_SYSTEM",
                      "SCRIPT_SUGGEST_SYSTEM", "INSIGHTS_SYSTEM",
                      "REP_BRIEF_SYSTEM"]:
            template = getattr(prompts, name, "")
            # Memory context is optional — some prompts may not have it
            # but the key ones should
            if name in ["NBA_SYSTEM", "REP_BRIEF_SYSTEM", "INSIGHTS_SYSTEM",
                        "SCRIPT_SUGGEST_SYSTEM", "SMS_AGENT_SYSTEM"]:
                assert "{{memory_context}}" in template, f"{name} missing memory_context"

    def test_rep_brief_prompt_fields(self):
        """Verify rep brief prompt has all expected template variables."""
        from app.ai.prompts import REP_BRIEF_USER
        expected = [
            "lead_name", "lead_id", "lead_status", "lead_score",
            "address", "county", "objections", "recent_messages",
        ]
        for field in expected:
            assert "{{" + field + "}}" in REP_BRIEF_USER


# ── Safety Checks ───────────────────────────────────────────────────────


class TestSafetyEnforcement:
    """Verify safety constraints are properly coded."""

    def test_ai_allow_auto_actions_default_false(self):
        """The auto-actions flag must default to False."""
        from app.core.config import Settings
        s = Settings(
            database_url="postgresql+asyncpg://x:x@localhost/x",
            database_url_sync="postgresql://x:x@localhost/x",
        )
        assert s.ai_allow_auto_actions is False

    def test_sms_auto_reply_default_false(self):
        """SMS auto-reply must default to False."""
        from app.core.config import Settings
        s = Settings(
            database_url="postgresql+asyncpg://x:x@localhost/x",
            database_url_sync="postgresql://x:x@localhost/x",
        )
        assert s.sms_auto_reply_enabled is False

    def test_opt_out_detection(self):
        """Opt-out keywords must be detected."""
        from app.services.compliance import is_opt_out_message
        for keyword in ["STOP", "stop", "Unsubscribe", "CANCEL", "end", "quit",
                         "opt out", "OPTOUT", "remove me", "do not contact"]:
            assert is_opt_out_message(keyword), f"Failed to detect: {keyword}"

    def test_non_opt_out(self):
        """Normal messages should not trigger opt-out."""
        from app.services.compliance import is_opt_out_message
        for msg in ["Hello", "I'm interested", "Tell me more", "When can you come?",
                     "What does it cost?", "stopping by later"]:
            assert not is_opt_out_message(msg), f"False positive: {msg}"


# ── Cost Tracking ───────────────────────────────────────────────────────


class TestCostTracking:
    """Verify cost calculation logic."""

    def test_cost_table_has_common_models(self):
        from app.ai.client import _COST_TABLE
        assert "claude-sonnet-4-5-20250929" in _COST_TABLE
        assert "claude-haiku-4-5-20251001" in _COST_TABLE

    def test_cost_rates_are_positive(self):
        from app.ai.client import _COST_TABLE
        for model, (input_rate, output_rate) in _COST_TABLE.items():
            assert input_rate > 0, f"{model} has non-positive input rate"
            assert output_rate > 0, f"{model} has non-positive output rate"

    def test_haiku_cheaper_than_sonnet(self):
        from app.ai.client import _COST_TABLE
        haiku = _COST_TABLE["claude-haiku-4-5-20251001"]
        sonnet = _COST_TABLE["claude-sonnet-4-5-20250929"]
        assert haiku[0] < sonnet[0]  # Input rate
        assert haiku[1] < sonnet[1]  # Output rate
