"""
Unit tests for the Qwen AI service (Phase 2).

ALL DashScope/OpenAI calls are mocked — these tests never consume API quota.
"""

import json
import logging
from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
import openai
import pytest

from config import settings
from prompts.system_prompt import MASTER_SYSTEM_PROMPT, build_system_prompt
from schemas.shared import NextBestAction
from services.ai_service import (
    AIService,
    AIValidationError,
    AIUnavailableError,
    _normalize_base_url,
    get_ai_service,
)


VALID_NBA = {
    "title": "Start Python basics",
    "description": "Learn core Python syntax this week.",
    "steps": ["Install Python and VS Code", "Complete the official Python tutorial"],
    "estimated_time": "3-4 hours this week",
    "why_this_matters": "Python is the entry skill for software engineering.",
    "stage": "SKILL_BUILDING",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def mock_client(sequence):
    """
    Mock OpenAI client whose chat.completions.create() consumes `sequence`
    in order: strings become response content, exceptions are raised.
    """
    client = MagicMock()

    def make_response(content):
        message = SimpleNamespace(content=content)
        choice = SimpleNamespace(message=message)
        return SimpleNamespace(choices=[choice])

    side_effects = [
        item if isinstance(item, BaseException) else make_response(item)
        for item in sequence
    ]
    client.chat.completions.create.side_effect = side_effects
    return client


def connection_error():
    request = httpx.Request(
        "POST", "https://dashscope.example.com/compatible-mode/v1/chat/completions"
    )
    return openai.APIConnectionError(request=request)


def rate_limit_error():
    request = httpx.Request(
        "POST", "https://dashscope.example.com/compatible-mode/v1/chat/completions"
    )
    response = httpx.Response(429, request=request)
    return openai.RateLimitError("rate limited", response=response, body=None)


# ---------------------------------------------------------------------------
# 1. Valid response
# ---------------------------------------------------------------------------


class TestValidResponse:
    def test_returns_validated_model(self):
        client = mock_client([json.dumps(VALID_NBA)])
        service = AIService(client=client)

        result = service.call_structured("Generate one action.", NextBestAction)

        assert isinstance(result, NextBestAction)
        assert result.title == "Start Python basics"
        assert result.stage == "SKILL_BUILDING"
        assert len(result.steps) == 2

    def test_uses_pattern_a_json_mode_and_configured_model(self):
        client = mock_client([json.dumps(VALID_NBA)])
        service = AIService(client=client)

        service.call_structured("Generate one action.", NextBestAction)

        kwargs = client.chat.completions.create.call_args.kwargs
        assert kwargs["response_format"] == {"type": "json_object"}
        assert kwargs["model"] == settings.QWEN_MODEL
        # DashScope json_object mode requires the word "json" in the prompt
        assert "json" in kwargs["messages"][0]["content"].lower()

    def test_tolerates_markdown_fenced_json(self):
        fenced = "```json\n" + json.dumps(VALID_NBA) + "\n```"
        client = mock_client([fenced])
        service = AIService(client=client)

        result = service.call_structured("Generate one action.", NextBestAction)

        assert isinstance(result, NextBestAction)


# ---------------------------------------------------------------------------
# 2-5. Retry policy: malformed JSON / schema failures
# ---------------------------------------------------------------------------


class TestRetryPolicy:
    def test_invalid_json_retries_once_then_succeeds(self):
        client = mock_client(["{not valid json!!", json.dumps(VALID_NBA)])
        service = AIService(client=client)

        result = service.call_structured("Generate one action.", NextBestAction)

        assert isinstance(result, NextBestAction)
        assert client.chat.completions.create.call_count == 2

    def test_schema_violation_retries_once_then_succeeds(self):
        wrong_schema = {"unexpected_field": True}
        client = mock_client([json.dumps(wrong_schema), json.dumps(VALID_NBA)])
        service = AIService(client=client)

        result = service.call_structured("Generate one action.", NextBestAction)

        assert isinstance(result, NextBestAction)
        assert client.chat.completions.create.call_count == 2

    def test_persistent_invalid_json_raises_controlled_error(self):
        client = mock_client(["not json", "still not json"])
        service = AIService(client=client)

        with pytest.raises(AIValidationError):
            service.call_structured("Generate one action.", NextBestAction)

        assert client.chat.completions.create.call_count == 2

    def test_persistent_schema_failure_raises_controlled_error(self):
        client = mock_client([json.dumps({"bad": 1}), json.dumps({"bad": 2})])
        service = AIService(client=client)

        with pytest.raises(AIValidationError):
            service.call_structured("Generate one action.", NextBestAction)

        assert client.chat.completions.create.call_count == 2

    def test_never_more_than_one_retry(self):
        client = mock_client(["bad", "bad", "bad", "bad"])
        service = AIService(client=client)

        with pytest.raises(AIValidationError):
            service.call_structured("Generate one action.", NextBestAction)

        assert client.chat.completions.create.call_count == 2


# ---------------------------------------------------------------------------
# 6-8. Transport / API errors, empty responses
# ---------------------------------------------------------------------------


class TestTransportErrors:
    def test_connection_error_retries_then_raises_unavailable(self):
        client = mock_client([connection_error(), connection_error()])
        service = AIService(client=client)

        with pytest.raises(AIUnavailableError):
            service.call_structured("Generate one action.", NextBestAction)

        assert client.chat.completions.create.call_count == 2

    def test_connection_error_recovers_on_retry(self):
        client = mock_client([connection_error(), json.dumps(VALID_NBA)])
        service = AIService(client=client)

        result = service.call_structured("Generate one action.", NextBestAction)

        assert isinstance(result, NextBestAction)
        assert client.chat.completions.create.call_count == 2

    def test_rate_limit_raises_immediately_without_retry(self):
        # Updated for the four-model fallback chain (spec: rate limit is an
        # ELIGIBLE model-availability failure). Preserved intent: a rate
        # limit is never retried on the SAME model — every model in the
        # chain is called exactly once, in order, then stop.
        chain = [
            "qwen-plus-2025-07-28",
            "qwen3-vl-235b-a22b-thinking",
            "qwen-turbo",
        ]
        client = mock_client([rate_limit_error() for _ in chain])
        service = AIService(client=client)

        with pytest.raises(AIUnavailableError):
            service.call_structured("Generate one action.", NextBestAction)

        assert client.chat.completions.create.call_count == len(chain)
        models_used = [
            c.kwargs["model"]
            for c in client.chat.completions.create.call_args_list
        ]
        assert models_used == chain

    def test_empty_content_is_controlled_failure(self):
        client = mock_client([None, ""])
        service = AIService(client=client)

        with pytest.raises(AIValidationError):
            service.call_structured("Generate one action.", NextBestAction)

        assert client.chat.completions.create.call_count == 2


# ---------------------------------------------------------------------------
# Configuration / secret safety
# ---------------------------------------------------------------------------


class TestConfigurationAndSecretSafety:
    def test_unconfigured_service_raises_cleanly(self, monkeypatch):
        monkeypatch.setattr(settings, "DASHSCOPE_API_KEY", "")
        monkeypatch.setattr(settings, "DASHSCOPE_BASE_URL", "")
        service = AIService()

        assert service.is_configured() is False
        with pytest.raises(AIUnavailableError) as exc_info:
            service.call_structured("Generate one action.", NextBestAction)

        # The message names the missing variables, never any secret value.
        assert "DASHSCOPE_API_KEY" in str(exc_info.value)

    def test_api_key_never_appears_in_logs_or_errors(self, monkeypatch, caplog):
        fake_key = "sk-FAKE-SECRET-DO-NOT-PRINT-000"
        monkeypatch.setattr(settings, "DASHSCOPE_API_KEY", fake_key)
        monkeypatch.setattr(settings, "DASHSCOPE_BASE_URL", "https://example.com/v1")
        client = mock_client(["not json", "not json"])
        service = AIService(client=client)

        with caplog.at_level(logging.DEBUG, logger="ah_career.ai"):
            with pytest.raises(AIValidationError):
                service.call_structured("Generate one action.", NextBestAction)

        assert fake_key not in caplog.text

    def test_singleton_reuses_one_instance(self):
        assert get_ai_service() is get_ai_service()


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------


class TestPromptBuilder:
    def test_master_prompt_requires_json_output(self):
        assert "json" in MASTER_SYSTEM_PROMPT.lower()
        assert "NEVER INVENT" in MASTER_SYSTEM_PROMPT

    def test_build_system_prompt_injects_context(self):
        prompt = build_system_prompt(
            schema_name="NextBestAction",
            student_profile_json='{"city": "Karachi"}',
            structured_data_json='{"careers": []}',
        )
        assert "NextBestAction" in prompt
        assert "Karachi" in prompt
        assert "careers" in prompt
        assert "JSON" in prompt


# ---------------------------------------------------------------------------
# Base URL normalization
# ---------------------------------------------------------------------------


class TestBaseURLNormalization:
    def test_bare_hostname_gets_scheme_and_path(self):
        assert (
            _normalize_base_url("ws.ap-southeast-1.maas.aliyuncs.com")
            == "https://ws.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1"
        )

    def test_scheme_without_path_gets_path_appended(self):
        assert (
            _normalize_base_url("https://dashscope-intl.aliyuncs.com")
            == "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
        )

    def test_full_url_is_returned_unchanged(self):
        full = "https://ws.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1"
        assert _normalize_base_url(full) == full

    def test_trailing_slash_is_stripped(self):
        assert (
            _normalize_base_url("https://dashscope-intl.aliyuncs.com/")
            == "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
        )

    def test_existing_path_is_respected(self):
        # a URL that already carries a path is never double-appended
        assert (
            _normalize_base_url("https://example.com/custom/v2")
            == "https://example.com/custom/v2"
        )

    def test_whitespace_is_stripped(self):
        assert (
            _normalize_base_url("  ws.ap-southeast-1.maas.aliyuncs.com ")
            == "https://ws.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1"
        )
