"""
Unit tests for the Qwen model fallback chain
(qwen3.7-plus -> qwen3.6-plus -> qwen-plus-2025-07-28 -> qwen3-vl-235b-a22b-thinking).

ALL DashScope/OpenAI calls are mocked — these tests never consume API quota.

Covers the 13 required fallback test categories:
 1. primary model default
 2. fallback configuration
 3. primary success never triggers fallback
 4. eligible primary failure triggers fallback (429 / 404 / 5xx)
 5. fallback success passes the same Pydantic validation
 6. both models fail -> existing graceful AI failure
 7. no infinite fallback loop (max 2 models, 1 transition)
 8. non-eligible errors never switch models
 9. Pattern A regression
10. Pattern A fallback
11. Pattern B / MCP regression
12. secret safety (no API key in fallback logs)
13. future extensibility (configuration-driven, callers unchanged)
"""

import inspect
import json
import logging
from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
import openai
import pytest

from config import settings
from schemas.shared import NextBestAction
from services.ai_service import (
    _model_chain,
    AIService,
    AIUnavailableError,
    AIValidationError,
)

PRIMARY = "qwen3.6-plus"
FALLBACK = "qwen-plus-2025-07-28"  # first fallback (kept for the single-transition scenarios)
FALLBACK_2 = "qwen3-vl-235b-a22b-thinking"
FALLBACK_3 = "qwen-turbo"
CHAIN = [PRIMARY, FALLBACK, FALLBACK_2, FALLBACK_3]

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
    """Mock OpenAI client whose create() consumes `sequence` in order.

    Items may be: exceptions (raised), plain strings (wrapped as text
    content), or pre-built response objects (used as-is — needed for
    Pattern B tool-call responses).
    """
    client = MagicMock()

    def make_response(content):
        message = SimpleNamespace(content=content)
        choice = SimpleNamespace(message=message)
        return SimpleNamespace(choices=[choice])

    side_effects = []
    for item in sequence:
        if isinstance(item, BaseException) or hasattr(item, "choices"):
            side_effects.append(item)
        else:
            side_effects.append(make_response(item))
    client.chat.completions.create.side_effect = side_effects
    return client


def _status_error(cls, status):
    request = httpx.Request(
        "POST", "https://dashscope.example.com/compatible-mode/v1/chat/completions"
    )
    response = httpx.Response(status, request=request)
    return cls("error", response=response, body=None)


def rate_limit_error():  # 429 — ELIGIBLE
    return _status_error(openai.RateLimitError, 429)


def model_not_found_error():  # 404 — ELIGIBLE
    return _status_error(openai.NotFoundError, 404)


def capacity_error():  # 503 — ELIGIBLE
    return _status_error(openai.InternalServerError, 503)


def auth_error():  # 401 — NOT eligible
    return _status_error(openai.AuthenticationError, 401)


def bad_request_error():  # 400 — NOT eligible
    return _status_error(openai.BadRequestError, 400)


def connection_error():  # whole-provider transport failure — NOT eligible
    request = httpx.Request(
        "POST", "https://dashscope.example.com/compatible-mode/v1/chat/completions"
    )
    return openai.APIConnectionError(request=request)


def models_used(client):
    return [
        c.kwargs["model"] for c in client.chat.completions.create.call_args_list
    ]


def text_response(content):
    message = SimpleNamespace(content=content, tool_calls=None)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def tool_call_response(name, arguments, call_id="call_1"):
    function = SimpleNamespace(name=name, arguments=arguments)
    tool_call = SimpleNamespace(id=call_id, type="function", function=function)
    message = SimpleNamespace(content=None, tool_calls=[tool_call])
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


TOOL_DEFS = [
    {
        "type": "function",
        "function": {
            "name": "search_internships",
            "description": "Search active internship records.",
            "parameters": {"type": "object", "properties": {}},
        },
    }
]


def noop_executor(name, arguments):
    return {"count": 0, "results": []}


# ---------------------------------------------------------------------------
# 1 + 2. Configuration
# ---------------------------------------------------------------------------


class TestModelConfiguration:
    def test_primary_model_is_qwen37(self):
        assert settings.QWEN_MODEL == PRIMARY

    def test_fallback_models_loaded_in_order(self):
        assert settings.QWEN_FALLBACK_MODELS == ",".join(
            [FALLBACK, FALLBACK_2, FALLBACK_3]
        )

    def test_model_chain_primary_then_fallbacks(self):
        assert _model_chain() == CHAIN

    def test_fallback_disabled_when_unset(self, monkeypatch):
        monkeypatch.setattr(settings, "QWEN_FALLBACK_MODELS", "")
        assert _model_chain() == [PRIMARY]

    def test_fallback_disabled_when_same_as_primary(self, monkeypatch):
        monkeypatch.setattr(settings, "QWEN_FALLBACK_MODELS", PRIMARY)
        assert _model_chain() == [PRIMARY]


# ---------------------------------------------------------------------------
# 3. Primary success never triggers the fallback
# ---------------------------------------------------------------------------


class TestPrimarySuccess:
    def test_success_uses_primary_exactly_once(self):
        client = mock_client([json.dumps(VALID_NBA)])
        service = AIService(client=client)

        result = service.call_structured("Generate one action.", NextBestAction)

        assert isinstance(result, NextBestAction)
        assert client.chat.completions.create.call_count == 1
        assert models_used(client) == [PRIMARY]

    def test_success_keeps_pattern_a_json_mode(self):
        client = mock_client([json.dumps(VALID_NBA)])
        service = AIService(client=client)

        service.call_structured("Generate one action.", NextBestAction)

        kwargs = client.chat.completions.create.call_args.kwargs
        assert kwargs["response_format"] == {"type": "json_object"}
        assert kwargs["model"] == PRIMARY


# ---------------------------------------------------------------------------
# 4. Eligible primary failures trigger the fallback
# ---------------------------------------------------------------------------


class TestFallbackTrigger:
    def test_rate_limit_triggers_fallback(self):
        client = mock_client([rate_limit_error(), json.dumps(VALID_NBA)])
        service = AIService(client=client)

        result = service.call_structured("Generate one action.", NextBestAction)

        assert isinstance(result, NextBestAction)
        assert models_used(client) == [PRIMARY, FALLBACK]

    def test_model_not_found_triggers_fallback(self):
        client = mock_client([model_not_found_error(), json.dumps(VALID_NBA)])
        service = AIService(client=client)

        result = service.call_structured("Generate one action.", NextBestAction)

        assert isinstance(result, NextBestAction)
        assert models_used(client) == [PRIMARY, FALLBACK]

    def test_provider_capacity_error_triggers_fallback(self):
        client = mock_client([capacity_error(), json.dumps(VALID_NBA)])
        service = AIService(client=client)

        result = service.call_structured("Generate one action.", NextBestAction)

        assert isinstance(result, NextBestAction)
        assert models_used(client) == [PRIMARY, FALLBACK]


# ---------------------------------------------------------------------------
# 5. Fallback output passes the SAME Pydantic validation
# ---------------------------------------------------------------------------


class TestFallbackValidation:
    def test_fallback_result_passes_same_pydantic_validation(self):
        client = mock_client([rate_limit_error(), json.dumps(VALID_NBA)])
        service = AIService(client=client)

        result = service.call_structured("Generate one action.", NextBestAction)

        # identical schema, identical fields — no model-specific branches
        assert isinstance(result, NextBestAction)
        assert result.title == "Start Python basics"
        assert result.stage == "SKILL_BUILDING"
        assert len(result.steps) == 2
        assert result.estimated_time == "3-4 hours this week"

    def test_fallback_output_with_invalid_schema_still_fails(self):
        # the fallback model must NEVER bypass validation
        client = mock_client(
            [
                rate_limit_error(),
                json.dumps({"unexpected_field": True}),
                json.dumps({"still_wrong": 1}),
            ]
        )
        service = AIService(client=client)

        with pytest.raises(AIValidationError):
            service.call_structured("Generate one action.", NextBestAction)

        # primary (1 call) + fallback (initial + one validation retry = 2)
        assert client.chat.completions.create.call_count == 3
        assert models_used(client) == [PRIMARY, FALLBACK, FALLBACK]


# ---------------------------------------------------------------------------
# 6 + 7. Chain exhaustion / no infinite loop
# ---------------------------------------------------------------------------


class TestChainExhaustion:
    def test_all_models_rate_limited_raise_existing_unavailable_error(self):
        client = mock_client([rate_limit_error() for _ in CHAIN])
        service = AIService(client=client)

        with pytest.raises(AIUnavailableError):
            service.call_structured("Generate one action.", NextBestAction)

        assert models_used(client) == CHAIN

    def test_no_infinite_fallback_loop(self):
        # more failures available than models — only the four configured
        # models may ever be attempted, and no model is ever retried for
        # a rate limit
        client = mock_client([rate_limit_error() for _ in range(8)])
        service = AIService(client=client)

        with pytest.raises(AIUnavailableError):
            service.call_structured("Generate one action.", NextBestAction)

        assert client.chat.completions.create.call_count == 4
        assert models_used(client) == CHAIN

    def test_fallback_never_recurses_to_another_fallback(self):
        # the last model failing must NOT re-invoke the primary
        client = mock_client(
            [
                rate_limit_error(),
                rate_limit_error(),
                rate_limit_error(),
                capacity_error(),
            ]
        )
        service = AIService(client=client)

        with pytest.raises(AIUnavailableError):
            service.call_structured("Generate one action.", NextBestAction)

        assert client.chat.completions.create.call_count == 4
        assert models_used(client) == CHAIN


# ---------------------------------------------------------------------------
# 8. Non-eligible errors never switch models
# ---------------------------------------------------------------------------


class TestNonEligibleErrors:
    def test_authentication_error_never_falls_back(self):
        # an invalid API key affects the entire provider — switching models
        # would only hide a configuration bug
        client = mock_client([auth_error()])
        service = AIService(client=client)

        with pytest.raises(AIUnavailableError):
            service.call_structured("Generate one action.", NextBestAction)

        assert client.chat.completions.create.call_count == 1
        assert models_used(client) == [PRIMARY]

    def test_bad_request_error_never_falls_back(self):
        client = mock_client([bad_request_error()])
        service = AIService(client=client)

        with pytest.raises(AIUnavailableError):
            service.call_structured("Generate one action.", NextBestAction)

        assert client.chat.completions.create.call_count == 1
        assert models_used(client) == [PRIMARY]

    def test_connection_error_retries_same_model_never_switches(self):
        # transport failures affect the whole endpoint, not one model
        client = mock_client([connection_error(), connection_error()])
        service = AIService(client=client)

        with pytest.raises(AIUnavailableError):
            service.call_structured("Generate one action.", NextBestAction)

        assert client.chat.completions.create.call_count == 2
        assert models_used(client) == [PRIMARY, PRIMARY]

    def test_validation_error_never_switches_models(self):
        # persistent malformed JSON stays on the primary model (existing
        # retry policy only) — quality issues are not availability errors
        client = mock_client(["not json", "still not json"])
        service = AIService(client=client)

        with pytest.raises(AIValidationError):
            service.call_structured("Generate one action.", NextBestAction)

        assert models_used(client) == [PRIMARY, PRIMARY]

    def test_unconfigured_service_never_falls_back(self, monkeypatch):
        monkeypatch.setattr(settings, "DASHSCOPE_API_KEY", "")
        monkeypatch.setattr(settings, "DASHSCOPE_BASE_URL", "")
        service = AIService()

        with pytest.raises(AIUnavailableError):
            service.call_structured("Generate one action.", NextBestAction)


# ---------------------------------------------------------------------------
# 9 + 10. Pattern A regression + fallback
# ---------------------------------------------------------------------------


class TestPatternA:
    def test_malformed_json_retries_on_primary_then_succeeds(self):
        # regression: same-model retry policy unchanged by the chain
        client = mock_client(["{not valid json!!", json.dumps(VALID_NBA)])
        service = AIService(client=client)

        result = service.call_structured("Generate one action.", NextBestAction)

        assert isinstance(result, NextBestAction)
        assert models_used(client) == [PRIMARY, PRIMARY]

    def test_fallback_recovery_rate_limit_then_valid_json(self):
        # full Pattern A fallback: 429 on primary -> valid JSON on fallback
        client = mock_client([rate_limit_error(), json.dumps(VALID_NBA)])
        service = AIService(client=client)

        result = service.call_structured("Generate one action.", NextBestAction)

        assert isinstance(result, NextBestAction)
        assert models_used(client) == [PRIMARY, FALLBACK]

    def test_primary_validation_retry_then_rate_limit_then_fallback(self):
        # attempt 1 primary: malformed JSON; attempt 2 primary: rate limit;
        # fallback: success — documented worst case within budget
        client = mock_client(
            ["broken", rate_limit_error(), json.dumps(VALID_NBA)]
        )
        service = AIService(client=client)

        result = service.call_structured("Generate one action.", NextBestAction)

        assert isinstance(result, NextBestAction)
        assert models_used(client) == [PRIMARY, PRIMARY, FALLBACK]

    def test_fallback_disabled_config_keeps_single_model(self, monkeypatch):
        # with the fallback unset, rate limits keep the legacy behavior
        monkeypatch.setattr(settings, "QWEN_FALLBACK_MODELS", "")
        client = mock_client([rate_limit_error()])
        service = AIService(client=client)

        with pytest.raises(AIUnavailableError):
            service.call_structured("Generate one action.", NextBestAction)

        assert client.chat.completions.create.call_count == 1
        assert models_used(client) == [PRIMARY]


# ---------------------------------------------------------------------------
# 11. Pattern B / MCP regression + fallback
# ---------------------------------------------------------------------------


class TestPatternB:
    def test_pattern_b_success_stays_on_primary(self):
        client = mock_client(
            [
                tool_call_response("search_internships", "{}"),
                text_response("Found nothing relevant."),
            ]
        )
        service = AIService(client=client)

        result = service.call_with_mcp(
            "Find internships.", tools=TOOL_DEFS, tool_executor=noop_executor
        )

        assert result.answer == "Found nothing relevant."
        assert result.tool_calls[0]["tool"] == "search_internships"
        assert models_used(client) == [PRIMARY, PRIMARY]

    def test_pattern_b_rate_limit_falls_back_and_completes_tool_loop(self):
        # primary model rate-limits mid-conversation -> the fallback model
        # runs the ENTIRE tool loop (fresh conversation, same tools/executor)
        client = mock_client(
            [
                rate_limit_error(),
                tool_call_response("search_internships", "{}"),
                text_response("Found 2 internships."),
            ]
        )
        service = AIService(client=client)

        result = service.call_with_mcp(
            "Find internships.", tools=TOOL_DEFS, tool_executor=noop_executor
        )

        assert result.answer == "Found 2 internships."
        assert result.tool_calls[0]["tool"] == "search_internships"
        assert result.tool_calls[0]["result"]["count"] == 0
        assert models_used(client) == [PRIMARY, FALLBACK, FALLBACK]

    def test_pattern_b_all_models_fail(self):
        client = mock_client([rate_limit_error() for _ in CHAIN])
        service = AIService(client=client)

        with pytest.raises(AIUnavailableError):
            service.call_with_mcp(
                "Find internships.", tools=TOOL_DEFS, tool_executor=noop_executor
            )

        assert models_used(client) == CHAIN

    def test_pattern_b_validation_error_never_switches_models(self):
        # empty final content is a quality failure — raised immediately on
        # the primary model; validation failures never switch models
        client = mock_client([text_response("")])
        service = AIService(client=client)

        with pytest.raises(AIValidationError):
            service.call_with_mcp(
                "Find internships.",
                tools=TOOL_DEFS,
                tool_executor=noop_executor,
                max_tool_rounds=0,
            )

        assert client.chat.completions.create.call_count == 1
        assert models_used(client) == [PRIMARY]

    def test_pattern_b_tool_executor_errors_never_switch_models(self):
        # MCP transport failures are not model failures — the exception
        # propagates unchanged for mcp_search_service's policy
        from services.mcp_client import MCPClientError

        def broken_executor(name, arguments):
            raise MCPClientError("tool failed")

        client = mock_client([tool_call_response("search_internships", "{}")])
        service = AIService(client=client)

        with pytest.raises(MCPClientError):
            service.call_with_mcp(
                "Find internships.", tools=TOOL_DEFS, tool_executor=broken_executor
            )

        assert models_used(client) == [PRIMARY]


# ---------------------------------------------------------------------------
# 12. Secret safety
# ---------------------------------------------------------------------------


class TestSecretSafety:
    def test_fallback_logs_never_expose_api_key(self, monkeypatch, caplog):
        fake_key = "sk-FAKE-SECRET-DO-NOT-PRINT-000"
        monkeypatch.setattr(settings, "DASHSCOPE_API_KEY", fake_key)
        client = mock_client([rate_limit_error() for _ in CHAIN])
        service = AIService(client=client)

        with caplog.at_level(logging.DEBUG, logger="ah_career.ai"):
            with pytest.raises(AIUnavailableError):
                service.call_structured("Generate one action.", NextBestAction)

        assert fake_key not in caplog.text

    def test_fallback_transition_logged_with_safe_metadata_only(self, caplog):
        client = mock_client([rate_limit_error() for _ in CHAIN])
        service = AIService(client=client)

        with caplog.at_level(logging.INFO, logger="ah_career.ai"):
            with pytest.raises(AIUnavailableError):
                service.call_structured("Generate one action.", NextBestAction)

        # the transitions are visible for diagnostics with safe fields only
        assert "AI model unavailable" in caplog.text
        assert "attempting next model in the fallback chain" in caplog.text
        assert PRIMARY in caplog.text
        assert FALLBACK in caplog.text
        assert "operation=structured_call" in caplog.text

    def test_fallback_errors_do_not_leak_secret_key_in_messages(self, caplog):
        client = mock_client([rate_limit_error() for _ in CHAIN])
        service = AIService(client=client)

        with caplog.at_level(logging.DEBUG, logger="ah_career.ai"):
            with pytest.raises(AIUnavailableError) as exc_info:
                service.call_structured("Generate one action.", NextBestAction)

        # the raised message carries the operation name only — never secrets
        assert "operation=structured_call" in str(exc_info.value)
        assert "sk-" not in str(exc_info.value)


# ---------------------------------------------------------------------------
# 13. Future extensibility — configuration-driven, callers unchanged
# ---------------------------------------------------------------------------


class TestFutureExtensibility:
    def test_callers_need_no_model_parameter(self):
        # model selection is configuration-driven: the public signatures
        # stay exactly as the feature services already call them
        for method in (AIService.call_structured, AIService.call_with_mcp):
            assert "model" not in inspect.signature(method).parameters

    def test_reconfigured_chain_via_config_only(self, monkeypatch):
        # swapping the whole fallback list requires ONLY a settings change —
        # no router, service, or prompt edit
        monkeypatch.setattr(
            settings, "QWEN_FALLBACK_MODELS", "qwen3.5-plus,qwen3.4-plus"
        )
        client = mock_client(
            [rate_limit_error(), rate_limit_error(), json.dumps(VALID_NBA)]
        )
        service = AIService(client=client)

        result = service.call_structured("Generate one action.", NextBestAction)

        assert isinstance(result, NextBestAction)
        assert models_used(client) == [
            "qwen3.6-plus",
            "qwen3.5-plus",
            "qwen3.4-plus",
        ]

    def test_public_error_contract_unchanged_for_callers(self):
        # both failure kinds surface as the same public exception types the
        # routers already handle — no caller branches on the model chain
        client = mock_client([rate_limit_error() for _ in CHAIN])
        service = AIService(client=client)
        with pytest.raises(AIUnavailableError):
            service.call_structured("Generate one action.", NextBestAction)

        client = mock_client([auth_error()])
        service = AIService(client=client)
        with pytest.raises(AIUnavailableError):
            service.call_structured("Generate one action.", NextBestAction)
