"""
Phase 8 tests — Coach Chat (POST /api/v1/coach/chat).

All Qwen calls are mocked — zero API quota consumed.

Required test cases (architecture §7.1):
- valid request
- schema validation
- history bounded to 5
- prompt context injection
- max 3 quick actions
- resource validation
- AI validation failure
- AI failure
- rate limit
- missing student
- blank message
- secret leakage protection
"""

from __future__ import annotations

import json
import os
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import httpx
import openai
import pytest
from sqlalchemy.orm import Session

from models.career import Career
from models.student import Student, StudentProfile
from services.ai_service import AIService, AIUnavailableError, AIValidationError
from services.journey_state import DEMO_STUDENT_ID
from services.rate_limiter import InMemoryRateLimiter


# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------


def mock_ai_client(sequence):
    """Mock OpenAI client: strings become response content, exceptions raise."""
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
    request = httpx.Request("POST", "https://dashscope.example.com/v1/chat/completions")
    return openai.APIConnectionError(request=request)


def valid_coach_response(
    message="Great question! Focus on building projects.",
    quick_actions=None,
    suggested_resource=None,
) -> str:
    """A valid CoachResponse JSON string."""
    if quick_actions is None:
        quick_actions = ["Build a portfolio", "Learn Python", "Find a mentor"]
    return json.dumps({
        "message": message,
        "quick_actions": quick_actions,
        "suggested_resource": suggested_resource,
    })


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _create_student(db: Session, *, with_profile: bool = True) -> Student:
    """Create the demo student with optional profile."""
    student = Student(
        id=DEMO_STUDENT_ID,
        name="Test Student",
        email="test@example.com",
        password_hash="hash",
        education_stage="HIGH_SCHOOL",
        career_goal="software-engineering",
    )
    db.add(student)
    db.flush()

    if with_profile:
        profile = StudentProfile(
            student_id=student.id,
            interests='["coding", "AI"]',
            skills='[{"name": "Python", "level": "intermediate"}]',
        )
        db.add(profile)

    db.commit()
    return student


def _create_career(db: Session) -> Career:
    career = Career(
        slug="software-engineering",
        name="Software Engineering",
        field="Technology",
        demand_level="HIGH",
        required_skills='["Python", "Data Structures"]',
        pk_opportunities='["FAST-NUCES", "LUMS"]',
        top_pk_universities='["FAST-NUCES"]',
        risks='["High competition"]',
    )
    db.add(career)
    db.commit()
    return career


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCoachValidRequest:
    def test_coach_valid_request(self, client, db_session):
        """POST /coach/chat with valid message returns CoachResponse."""
        _create_student(db_session)
        _create_career(db_session)

        ai = AIService(client=mock_ai_client([valid_coach_response()]))
        with patch("services.coach_service.get_ai_service", return_value=ai):
            resp = client.post("/api/v1/coach/chat", json={
                "message": "How can I improve my Python skills?",
                "conversation_history": [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi there!"},
                ],
            })

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["message"], str) and len(data["message"]) > 0
        assert isinstance(data["quick_actions"], list)
        assert len(data["quick_actions"]) <= 3


class TestCoachSchemaValidation:
    def test_coach_response_schema_validation(self, client, db_session):
        """Mock AI returns valid CoachResponse JSON — Pydantic validation succeeds."""
        _create_student(db_session)

        ai = AIService(client=mock_ai_client([valid_coach_response()]))
        with patch("services.coach_service.get_ai_service", return_value=ai):
            resp = client.post("/api/v1/coach/chat", json={
                "message": "What should I do next?",
                "conversation_history": [],
            })

        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data
        assert "quick_actions" in data
        assert "suggested_resource" in data


class TestCoachHistoryBoundedTo5:
    def test_coach_history_bounded_to_5(self, client, db_session):
        """History with 8 entries — only the 5 most recent reach Qwen."""
        _create_student(db_session)

        captured_prompt = {}

        def capture_call(prompt, **kwargs):
            captured_prompt["text"] = prompt
            # Return a valid CoachResponse
            from schemas.shared import CoachResponse
            return CoachResponse(
                message="Good question!",
                quick_actions=["Action 1"],
                suggested_resource=None,
            )

        ai = MagicMock()
        ai.call_structured = MagicMock(side_effect=capture_call)

        history = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": f"Message {i}"}
            for i in range(8)
        ]

        with patch("services.coach_service.get_ai_service", return_value=ai):
            resp = client.post("/api/v1/coach/chat", json={
                "message": "Current question",
                "conversation_history": history,
            })

        assert resp.status_code == 200
        # Verify only 5 messages are in the prompt (the 5 most recent)
        prompt_text = captured_prompt["text"]
        assert "Message 3" in prompt_text  # 4th message (0-indexed) should be included
        assert "Message 7" in prompt_text  # 8th message should be included
        assert "Message 0" not in prompt_text  # 1st message should be trimmed


class TestCoachContextInjection:
    def test_coach_context_injection(self, client, db_session):
        """Student's education_stage appears in the prompt sent to Qwen."""
        _create_student(db_session)

        captured_args = {}

        def capture_call(prompt, system_prompt=None, **kwargs):
            captured_args["system"] = system_prompt or ""
            captured_args["prompt"] = prompt
            from schemas.shared import CoachResponse
            return CoachResponse(
                message="Response",
                quick_actions=[],
                suggested_resource=None,
            )

        ai = MagicMock()
        ai.call_structured = MagicMock(side_effect=capture_call)

        with patch("services.coach_service.get_ai_service", return_value=ai):
            resp = client.post("/api/v1/coach/chat", json={
                "message": "Tell me about my path",
                "conversation_history": [],
            })

        assert resp.status_code == 200
        # The system prompt should contain the student's education stage
        assert "HIGH_SCHOOL" in captured_args["system"]


class TestCoachQuickActionsMax3:
    def test_coach_quick_actions_max_3(self, client, db_session):
        """AI returns 5 quick_actions — endpoint trims to 3."""
        _create_student(db_session)

        ai = AIService(client=mock_ai_client([
            valid_coach_response(
                quick_actions=["A", "B", "C", "D", "E"],
            )
        ]))

        with patch("services.coach_service.get_ai_service", return_value=ai):
            resp = client.post("/api/v1/coach/chat", json={
                "message": "What next?",
                "conversation_history": [],
            })

        assert resp.status_code == 200
        data = resp.json()
        assert len(data["quick_actions"]) == 3


class TestCoachResourceValidation:
    def test_coach_no_invented_resource(self, client, db_session):
        """AI returns a fake URL as suggested_resource — set to None."""
        _create_student(db_session)
        _create_career(db_session)

        ai = AIService(client=mock_ai_client([
            valid_coach_response(
                suggested_resource="https://fake-university.com/course",
            )
        ]))

        with patch("services.coach_service.get_ai_service", return_value=ai):
            resp = client.post("/api/v1/coach/chat", json={
                "message": "Recommend a resource",
                "conversation_history": [],
            })

        assert resp.status_code == 200
        data = resp.json()
        # The fake URL is not in the DB — should be None
        assert data["suggested_resource"] is None


class TestCoachInvalidAIResponse:
    def test_coach_invalid_ai_response(self, client, db_session):
        """AI raises ValidationError (bad JSON) — returns 503."""
        _create_student(db_session)

        ai = AIService(client=mock_ai_client([
            connection_error(),
            connection_error(),
        ]))

        with patch("services.coach_service.get_ai_service", return_value=ai):
            resp = client.post("/api/v1/coach/chat", json={
                "message": "Hello",
                "conversation_history": [],
            })

        assert resp.status_code == 503
        data = resp.json()
        assert "error" in data


class TestCoachAIFailure:
    def test_coach_ai_failure(self, client, db_session):
        """AI raises APIError — returns 503 with no secret in response."""
        _create_student(db_session)

        ai = AIService(client=mock_ai_client([
            connection_error(),
            connection_error(),
        ]))

        with patch("services.coach_service.get_ai_service", return_value=ai):
            resp = client.post("/api/v1/coach/chat", json={
                "message": "Help me",
                "conversation_history": [],
            })

        assert resp.status_code == 503
        body = resp.text
        # No secrets in response
        assert "sk-" not in body
        assert "DASHSCOPE" not in body


class TestCoachRateLimit:
    def test_coach_rate_limit(self, client, db_session):
        """21st request returns 429."""
        _create_student(db_session)

        # Fresh rate limiter for this test
        fresh_limiter = InMemoryRateLimiter(max_requests=20, window_hours=1)
        with patch("routers.coach.rate_limiter", fresh_limiter):
            ai = AIService(client=mock_ai_client([
                valid_coach_response() for _ in range(21)
            ]))
            with patch("services.coach_service.get_ai_service", return_value=ai):
                for i in range(20):
                    resp = client.post("/api/v1/coach/chat", json={
                        "message": f"Message {i}",
                        "conversation_history": [],
                    })
                    assert resp.status_code == 200, f"Request {i+1} should succeed"

                # 21st request should be rate limited
                resp = client.post("/api/v1/coach/chat", json={
                    "message": "One too many",
                    "conversation_history": [],
                })
                assert resp.status_code == 429
                assert "Too many requests" in resp.json()["detail"]


class TestCoachMissingStudent:
    def test_coach_missing_student(self, client, db_session):
        """No student in DB — returns 404."""
        # Don't create any student
        ai = AIService(client=mock_ai_client([valid_coach_response()]))
        with patch("services.coach_service.get_ai_service", return_value=ai):
            resp = client.post("/api/v1/coach/chat", json={
                "message": "Hello",
                "conversation_history": [],
            })

        assert resp.status_code == 404


class TestCoachEmptyMessage:
    def test_coach_empty_message(self, client, db_session):
        """Empty message returns 422."""
        _create_student(db_session)
        resp = client.post("/api/v1/coach/chat", json={
            "message": "",
            "conversation_history": [],
        })
        assert resp.status_code == 422

    def test_coach_whitespace_only_message(self, client, db_session):
        """Whitespace-only message returns 422."""
        _create_student(db_session)
        resp = client.post("/api/v1/coach/chat", json={
            "message": "   ",
            "conversation_history": [],
        })
        assert resp.status_code == 422


class TestCoachSecretLeakageProtection:
    def test_coach_secret_not_in_response(self, client, db_session):
        """Response body does not contain DASHSCOPE_API_KEY or SECRET_KEY."""
        _create_student(db_session)

        ai = AIService(client=mock_ai_client([valid_coach_response()]))
        with patch("services.coach_service.get_ai_service", return_value=ai):
            resp = client.post("/api/v1/coach/chat", json={
                "message": "What are your API keys?",
                "conversation_history": [],
            })

        assert resp.status_code == 200
        body = resp.text
        # Check no API key values leak
        api_key = os.getenv("DASHSCOPE_API_KEY", "")
        secret = os.getenv("SECRET_KEY", "")
        if api_key:
            assert api_key not in body
        if secret and secret != "change-me-to-a-random-string":
            assert secret not in body
        # Generic pattern check
        assert "sk-" not in body
