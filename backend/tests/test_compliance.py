"""Tests for compliance and safety logic (no DB required)."""

import pytest

from app.services.compliance import is_opt_out_message


class TestOptOutDetection:
    """Verify opt-out keyword detection."""

    @pytest.mark.parametrize(
        "text",
        [
            "STOP",
            "stop",
            "Stop",
            "Please unsubscribe me",
            "CANCEL",
            "End",
            "QUIT",
            "opt out please",
            "OPT OUT",
            "optout",
            "opt-out",
            "remove me from your list",
            "do not contact me",
            "don't contact me",
            "leave me alone",
        ],
    )
    def test_opt_out_detected(self, text: str):
        assert is_opt_out_message(text) is True

    @pytest.mark.parametrize(
        "text",
        [
            "Yes I'm interested",
            "Tell me more about solar",
            "What time works?",
            "Sounds good",
            "How much does it cost?",
            "I'd like to schedule",
            "Can you call me tomorrow?",
            "",
        ],
    )
    def test_non_opt_out_not_detected(self, text: str):
        assert is_opt_out_message(text) is False

    def test_opt_out_in_longer_message(self):
        assert is_opt_out_message("I want to stop receiving these messages") is True

    def test_empty_string(self):
        assert is_opt_out_message("") is False
