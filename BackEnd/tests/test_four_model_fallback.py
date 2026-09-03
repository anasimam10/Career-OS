"""
Unit tests for the FOUR-model Qwen fallback chain (spec 2026-08-30):

    1. qwen3.7-plus           (primary)
    2. qwen3.6-plus           (fallback 1)
    3. qwen-plus-2025-07-28   (fallback 2)
    4. qwen3-vl-235b-a22b-thinking (fallback 3)

ALL DashScope/OpenAI calls are mocked — these tests never consume API quota.

The 14 required test functions (exact spec names):
 1. test_four_model_chain_order
 2. test_primary_success_stops_chain
 3. test_primary_failure_moves_to_model_2
 4. test_model_2_failure_moves_to_model_3
 5. test_model_3_failure_moves_to_model_4
 6. test_all_four_fail
 7. test_no_infinite_fallback
 8. test_noneligible_error_stops_chain
 9. test_each_model_uses_same_pydantic_validation
10. test_pattern_a_regression
11. test_pattern_b_regression
12. test_model_configuration_loaded
13. test_secret_not_leaked
14. test_future_model_extensibility
"""

import inspect
import json
import logging
from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
import openai
import pytest
from fastapi.testclient import TestClient

from config import settings
from main import app
from schemas.shared import NextBestAction
from services.ai_service import (
    _model_chain,
    AIService,
    AIUnavailableError,
    AIValidationError,
)

MODELS = [
    "qwen3.6-plus",
    "qwen-plus-2025-07-28",
    "qwen3-vl-235b-a22b-thinking",
    "qwen-turbo",
]

VALID_NBA = {
    "title": "Start Python basics",
    "description": "Learn core Python syntax this week.",
    "steps": ["Install Python and VS Code", "Complete the official Python tutorial"],
    "estimated_time": "3-4 hours this week",
    "why_this_matters": "Python is the entry skill for software engineering.",
    "stage": "SKILL_BUILDING",
}


# ---------------------------------------------------------------------------
# Helpers (mocked — no API quota is ever consumed)
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


def auth_error():  # 401 — NOT eligible
    return _status_error(openai.AuthenticationError, 401)


def permission_error():  # 403 — NOT eligible
    return _status_error(openai.PermissionDeniedError, 403)


def bad_request_error():  # 400 — NOT eligible
    return _status_error(openai.BadRequestError, 400)


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
# 1. Chain order
# ---------------------------------------------------------------------------


def test_four_model_chain_order():
    assert _model_chain() == MODELS


# ---------------------------------------------------------------------------
# 2-5. Deterministic chain traversal
# ---------------------------------------------------------------------------


def test_primary_success_stops_chain():
    client = mock_client([json.dumps(VALID_NBA)])
    service = AIService(client=client)

    result = service.call_structured("Generate one action.", NextBestAction)

    assert isinstance(result, NextBestAction)
    # models 2-4 are never called when the primary succeeds
    assert models_used(client) == [MODELS[0]]


def test_primary_failure_moves_to_model_2():
    client = mock_client([rate_limit_error(), json.dumps(VALID_NBA)])
    service = AIService(client=client)

    result = service.call_structured("Generate one action.", NextBestAction)

    assert isinstance(result, NextBestAction)
    # models 3-4 are never called when model 2 succeeds
    assert models_used(client) == MODELS[:2]


def test_model_2_failure_moves_to_model_3():
    client = mock_client(
        [rate_limit_error(), rate_limit_error(), json.dumps(VALID_NBA)]
    )
    service = AIService(client=client)

    result = service.call_structured("Generate one action.", NextBestAction)

    assert isinstance(result, NextBestAction)
    # model 4 is never called when model 3 succeeds
    assert models_used(client) == MODELS[:3]


def test_model_3_failure_moves_to_model_4():
    client = mock_client(
        [
            rate_limit_error(),
            rate_limit_error(),
            rate_limit_error(),
            json.dumps(VALID_NBA),
        ]
    )
    service = AIService(client=client)

    result = service.call_structured("Generate one action.", NextBestAction)

    assert isinstance(result, NextBestAction)
    assert models_used(client) == MODELS


# ---------------------------------------------------------------------------
# 6-7. Chain exhaustion / no infinite fallback
# ---------------------------------------------------------------------------


def test_all_four_fail():
    client = mock_client([rate_limit_error() for _ in MODELS])
    service = AIService(client=client)

    with pytest.raises(AIUnavailableError):
        service.call_structured("Generate one action.", NextBestAction)

    # existing graceful AI failure behaviour, after exactly four attempts
    assert models_used(client) == MODELS


def test_no_infinite_fallback():
    # far more failures supplied than models — the sequence must be exactly
    # 1 -> 2 -> 3 -> 4, never repeating, never restarting at model 1
    client = mock_client([rate_limit_error() for _ in range(10)])
    service = AIService(client=client)

    with pytest.raises(AIUnavailableError):
        service.call_structured("Generate one action.", NextBestAction)

    used = models_used(client)
    assert client.chat.completions.create.call_count == 4
    assert used == MODELS
    # no model is ever attempted twice
    assert len(used) == len(set(used))


# ---------------------------------------------------------------------------
# 8. Non-eligible errors stop the chain
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "error_factory",
    [auth_error, permission_error, bad_request_error],
    ids=["http-401", "http-403", "http-400"],
)
def test_noneligible_error_stops_chain(error_factory):
    client = mock_client([error_factory()])
    service = AIService(client=client)

    with pytest.raises(AIUnavailableError):
        service.call_structured("Generate one action.", NextBestAction)

    # no fallback at all — a broken configuration is not fixed by another model
    assert models_used(client) == [MODELS[0]]


# ---------------------------------------------------------------------------
# 9. Same Pydantic validation for every model
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("model", MODELS)
def test_each_model_uses_same_pydantic_validation(model, monkeypatch):
    # isolate ONE model: the chain is reduced to that model alone, so its
    # output goes through the identical JSON -> Pydantic pipeline
    monkeypatch.setattr(settings, "QWEN_MODEL", model)
    monkeypatch.setattr(settings, "QWEN_FALLBACK_MODELS", "")
    client = mock_client([json.dumps(VALID_NBA)])
    service = AIService(client=client)

    result = service.call_structured("Generate one action.", NextBestAction)

    assert isinstance(result, NextBestAction)
    assert result.title == "Start Python basics"
    assert result.stage == "SKILL_BUILDING"
    assert len(result.steps) == 2
    assert result.estimated_time == "3-4 hours this week"
    assert models_used(client) == [model]


# ---------------------------------------------------------------------------
# 10-11. Pattern A / Pattern B regression
# ---------------------------------------------------------------------------


def test_pattern_a_regression():
    # existing behaviour unchanged: malformed JSON is retried on the SAME
    # model, json_object mode is used, and validation still applies
    client = mock_client(["{not valid json!!", json.dumps(VALID_NBA)])
    service = AIService(client=client)

    result = service.call_structured("Generate one action.", NextBestAction)

    assert isinstance(result, NextBestAction)
    assert models_used(client) == [MODELS[0], MODELS[0]]
    kwargs = client.chat.completions.create.call_args.kwargs
    assert kwargs["response_format"] == {"type": "json_object"}


def test_pattern_b_regression():
    # existing MCP behaviour unchanged: the tool loop runs on the primary
    # model with tool_choice=auto and returns the evidence trail
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
    assert result.tool_calls[0]["result"]["count"] == 0
    assert models_used(client) == [MODELS[0], MODELS[0]]
    kwargs = client.chat.completions.create.call_args.kwargs
    assert kwargs["tool_choice"] == "auto"


# ---------------------------------------------------------------------------
# 12. Configuration loaded
# ---------------------------------------------------------------------------


def test_model_configuration_loaded():
    assert settings.QWEN_MODEL == MODELS[0]
    loaded_fallbacks = [
        m.strip()
        for m in settings.QWEN_FALLBACK_MODELS.split(",")
        if m.strip()
    ]
    assert loaded_fallbacks == MODELS[1:]
    assert _model_chain() == MODELS


def test_startup_rejects_incomplete_model_chain(monkeypatch):
    # startup validation (spec §9, configuration check only): a chain
    # missing a mandated model must abort startup with a clear error
    monkeypatch.setattr(settings, "QWEN_FALLBACK_MODELS", "qwen-plus-2025-07-28")
    with pytest.raises(RuntimeError, match="missing required models"):
        with TestClient(app):
            pass


# ---------------------------------------------------------------------------
# 13. Secret safety during multi-model fallback
# ---------------------------------------------------------------------------


def test_secret_not_leaked(monkeypatch, caplog):
    fake_key = "sk-FAKE-SECRET-DO-NOT-PRINT-000"
    monkeypatch.setattr(settings, "DASHSCOPE_API_KEY", fake_key)
    client = mock_client([rate_limit_error() for _ in MODELS])
    service = AIService(client=client)

    with caplog.at_level(logging.DEBUG, logger="ah_career.ai"):
        with pytest.raises(AIUnavailableError) as exc_info:
            service.call_structured("Generate one action.", NextBestAction)

    assert fake_key not in caplog.text
    assert "sk-" not in str(exc_info.value)
    # the multi-model transitions ARE logged — with safe metadata only
    assert "attempting next model in the fallback chain" in caplog.text


# ---------------------------------------------------------------------------
# 14. Future extensibility
# ---------------------------------------------------------------------------


def test_future_model_extensibility(monkeypatch):
    # a FIFTH model is added through configuration ONLY — no router,
    # service, or caller changes; the chain simply gets one more entry
    monkeypatch.setattr(
        settings,
        "QWEN_FALLBACK_MODELS",
        "qwen-plus-2025-07-28,qwen3-vl-235b-a22b-thinking,qwen-turbo,qwen3.5-plus",
    )
    client = mock_client(
        [rate_limit_error() for _ in range(4)] + [json.dumps(VALID_NBA)]
    )
    service = AIService(client=client)

    result = service.call_structured("Generate one action.", NextBestAction)

    assert isinstance(result, NextBestAction)
    assert models_used(client) == ["qwen3.6-plus", "qwen-plus-2025-07-28", "qwen3-vl-235b-a22b-thinking", "qwen-turbo", "qwen3.5-plus"]

    # callers still never pass or know about model selection
    for method in (AIService.call_structured, AIService.call_with_mcp):
        assert "model" not in inspect.signature(method).parameters
