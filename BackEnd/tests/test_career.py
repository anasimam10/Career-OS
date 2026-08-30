"""
Phase 3 tests — Career Intelligence vertical slice.

ALL Qwen calls are mocked (the Phase 2 ai_service is exercised with a mock
OpenAI client) — these tests never consume API quota and need no internet.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
import openai
import pytest

from models.career import Career
from repositories.student_repo import StudentRepository
from schemas.shared import CareerRealityResponse
from services import career_service
from services.ai_service import AIService


# ---------------------------------------------------------------------------
# Mock helpers (same pattern as tests/test_ai_service.py)
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


# ---------------------------------------------------------------------------
# Valid AI payloads — factual values intentionally DIFFER from the database
# so the tests prove that grounding overwrites them with DB values.
# ---------------------------------------------------------------------------

AI_REALITY_RESPONSE = {
    "reality": {
        "career_name": "Wrong Name From AI",
        "demand_level": "LOW",
        "competition_level": "LOW",
        "difficulty_level": "LOW",
        "required_skills": ["Invented Skill"],
        "pk_opportunities": ["Invented opportunity at FakeCorp"],
        "risks": ["Invented risk"],
        "rewards": ["Transferable problem-solving skills", "Flexible remote work"],
        "data_source": "AI hallucination",
    },
    "verdict": {
        "verdict": "WORTH_EXPLORING",
        "headline": "Worth testing before committing.",
        "reasoning": "Your interests align with the required skills; try the trial first.",
        "student_strengths_match": ["Interest in technology"],
        "gaps_to_address": ["Programming fundamentals"],
        "suggested_trial": "7-day guided exploration",
    },
}

AI_TRIAL_PLAN = {
    "career_slug": "wrong-slug-from-ai",
    "duration_days": 5,  # intentionally wrong — the service must force 7
    "days": [
        {
            "day_range": "Day 1-2",
            "title": "Setup",
            "tasks": ["Install tools", "Write a first program"],
        },
        {
            "day_range": "Day 7",
            "title": "Reflect",
            "tasks": ["Answer the reflection prompt"],
        },
    ],
    "reflection_prompt": "Did you enjoy the problem-solving?",
}


# ---------------------------------------------------------------------------
# Fixtures — a seeded database (careers + demo student)
# ---------------------------------------------------------------------------


FULL_CAREER = dict(
    slug="software-engineering",
    name="Software Engineering",
    field="Technology",
    demand_level="HIGH",
    competition_level="HIGH",
    difficulty_level="MEDIUM",
    required_skills=json.dumps(["Python", "Data Structures", "Git"]),
    pk_opportunities=json.dumps(["Growing software house demand in major cities"]),
    top_pk_universities=json.dumps(["FAST-NUCES", "LUMS"]),
    risks=json.dumps(["Highly competitive admissions"]),
)

SPARSE_CAREER = dict(
    slug="marketing",
    name="Marketing & Digital Media",
    field="Business",
    demand_level="MEDIUM",
    competition_level=None,
    difficulty_level=None,
    required_skills=json.dumps([]),
    pk_opportunities=json.dumps([]),
    top_pk_universities=json.dumps([]),
    risks=json.dumps([]),
)


@pytest.fixture()
def seeded_client(client, db_session):
    """Client with two careers (one full, one sparse) + the demo student."""
    db_session.add(Career(**FULL_CAREER))
    db_session.add(Career(**SPARSE_CAREER))
    db_session.commit()

    student_repo = StudentRepository(db_session)
    student_repo.create_with_profile(
        name="Demo Student",
        email="demo@test.local",
        password_hash="test",
        education_stage="HIGH_SCHOOL",
        career_goal="Software Engineering",
        motivation_tags=json.dumps(["I genuinely love this subject"]),
    )
    student_repo.update_profile(
        1,
        interests=json.dumps(["Technology", "Mathematics"]),
        skills=json.dumps([{"name": "Python", "level": "beginner"}]),
    )
    yield client


@pytest.fixture()
def capture_ai(monkeypatch):
    """Replace the AI service with a mock; expose the mock for assertions."""

    def _install(sequence):
        ai_client = mock_ai_client(sequence)
        service = AIService(client=ai_client)
        monkeypatch.setattr(career_service, "get_ai_service", lambda: service)
        return ai_client

    yield _install


# ---------------------------------------------------------------------------
# GET /careers — database only
# ---------------------------------------------------------------------------


class TestCareerList:
    def test_list_returns_seeded_careers(self, seeded_client):
        resp = seeded_client.get("/api/v1/careers")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        slugs = {c["slug"] for c in data}
        assert slugs == {"software-engineering", "marketing"}

    def test_list_empty_database(self, client):
        resp = client.get("/api/v1/careers")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_fields_match_contract(self, seeded_client):
        resp = seeded_client.get("/api/v1/careers")
        for item in resp.json():
            assert set(item.keys()) == {"slug", "name", "field", "demand_level"}

    def test_get_endpoints_never_call_ai(self, seeded_client, monkeypatch):
        calls = []

        def _fail_if_called():
            calls.append(1)
            raise AssertionError("GET endpoints must not call the AI service")

        monkeypatch.setattr(career_service, "get_ai_service", _fail_if_called)
        assert seeded_client.get("/api/v1/careers").status_code == 200
        assert seeded_client.get("/api/v1/careers/software-engineering").status_code == 200
        assert calls == []


# ---------------------------------------------------------------------------
# GET /careers/{slug} — database only
# ---------------------------------------------------------------------------


class TestCareerDetail:
    def test_existing_slug_returns_full_career(self, seeded_client):
        resp = seeded_client.get("/api/v1/careers/software-engineering")
        assert resp.status_code == 200
        data = resp.json()
        assert data["slug"] == "software-engineering"
        assert data["name"] == "Software Engineering"
        assert data["demand_level"] == "HIGH"
        assert data["required_skills"] == ["Python", "Data Structures", "Git"]
        assert data["top_pk_universities"] == ["FAST-NUCES", "LUMS"]

    def test_unknown_slug_returns_404(self, seeded_client):
        resp = seeded_client.get("/api/v1/careers/does-not-exist")
        assert resp.status_code == 404
        assert "error" in resp.json()
        assert "does-not-exist" in resp.json()["error"]


# ---------------------------------------------------------------------------
# POST /career/analyze — Qwen (mocked)
# ---------------------------------------------------------------------------


class TestCareerAnalyze:
    def test_valid_career_returns_reality_and_verdict(self, seeded_client, capture_ai):
        capture_ai([json.dumps(AI_REALITY_RESPONSE)])
        resp = seeded_client.post("/api/v1/career/analyze", json={"career_slug": "software-engineering"})
        assert resp.status_code == 200
        data = resp.json()
        assert "reality" in data and "verdict" in data
        assert data["verdict"]["verdict"] in {"GOOD_FIT", "WORTH_EXPLORING", "RECONSIDER"}

    def test_unknown_career_returns_404(self, seeded_client, capture_ai):
        ai = capture_ai([json.dumps(AI_REALITY_RESPONSE)])
        resp = seeded_client.post("/api/v1/career/analyze", json={"career_slug": "nope"})
        assert resp.status_code == 404
        assert "error" in resp.json()
        ai.chat.completions.create.assert_not_called()  # 404 before any AI call

    def test_student_profile_included_in_ai_context(self, seeded_client, capture_ai):
        ai = capture_ai([json.dumps(AI_REALITY_RESPONSE)])
        seeded_client.post("/api/v1/career/analyze", json={"career_slug": "software-engineering"})
        messages = ai.chat.completions.create.call_args.kwargs["messages"]
        system_prompt = messages[0]["content"]
        assert "Demo Student" in system_prompt
        assert "Technology" in system_prompt  # interests
        assert "beginner" in system_prompt  # skills

    def test_career_database_facts_included_in_ai_context(self, seeded_client, capture_ai):
        ai = capture_ai([json.dumps(AI_REALITY_RESPONSE)])
        seeded_client.post("/api/v1/career/analyze", json={"career_slug": "software-engineering"})
        messages = ai.chat.completions.create.call_args.kwargs["messages"]
        system_prompt = messages[0]["content"]
        assert "Software Engineering" in system_prompt
        assert "Data Structures" in system_prompt  # required_skills
        assert "HIGH" in system_prompt  # demand level

    def test_ai_output_is_validated_and_grounded_in_db(self, seeded_client, capture_ai):
        """Factual fields must come from SQLite even when the AI says otherwise."""
        capture_ai([json.dumps(AI_REALITY_RESPONSE)])
        resp = seeded_client.post("/api/v1/career/analyze", json={"career_slug": "software-engineering"})
        assert resp.status_code == 200
        reality = resp.json()["reality"]
        assert reality["career_name"] == "Software Engineering"  # NOT "Wrong Name From AI"
        assert reality["demand_level"] == "HIGH"  # NOT "LOW"
        assert reality["required_skills"] == ["Python", "Data Structures", "Git"]
        assert reality["pk_opportunities"] == ["Growing software house demand in major cities"]
        assert reality["risks"] == ["Highly competitive admissions"]
        # rewards stay from the AI (general interpretation — not in the DB)
        assert reality["rewards"] == AI_REALITY_RESPONSE["reality"]["rewards"]
        # data_source identifies the actual source honestly
        assert "template seed data" in reality["data_source"]
        assert "not independently verified" in reality["data_source"]

    def test_sparse_career_metrics_are_unknown(self, seeded_client, capture_ai):
        capture_ai([json.dumps(AI_REALITY_RESPONSE)])
        resp = seeded_client.post("/api/v1/career/analyze", json={"career_slug": "marketing"})
        assert resp.status_code == 200
        reality = resp.json()["reality"]
        assert reality["competition_level"] == "UNKNOWN"
        assert reality["difficulty_level"] == "UNKNOWN"

    def test_invalid_ai_output_triggers_one_retry(self, seeded_client, capture_ai):
        ai = capture_ai(["not json at all", json.dumps(AI_REALITY_RESPONSE)])
        resp = seeded_client.post("/api/v1/career/analyze", json={"career_slug": "software-engineering"})
        assert resp.status_code == 200
        assert ai.chat.completions.create.call_count == 2

    def test_persistent_invalid_ai_output_is_500(self, seeded_client, capture_ai):
        capture_ai(["not json", "still not json"])
        resp = seeded_client.post("/api/v1/career/analyze", json={"career_slug": "software-engineering"})
        assert resp.status_code == 500
        assert resp.json() == {"error": "AI response could not be processed"}

    def test_ai_unavailable_is_503_without_fabrication(self, seeded_client, capture_ai):
        capture_ai([connection_error(), connection_error()])
        resp = seeded_client.post("/api/v1/career/analyze", json={"career_slug": "software-engineering"})
        assert resp.status_code == 503
        assert resp.json() == {"error": "AI service temporarily unavailable"}

    def test_missing_career_slug_is_422(self, seeded_client):
        resp = seeded_client.post("/api/v1/career/analyze", json={})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /career/trial-plan — Qwen (mocked)
# ---------------------------------------------------------------------------


class TestTrialPlan:
    def test_valid_career_returns_trial_plan(self, seeded_client, capture_ai):
        capture_ai([json.dumps(AI_TRIAL_PLAN)])
        resp = seeded_client.post("/api/v1/career/trial-plan", json={"career_slug": "software-engineering"})
        assert resp.status_code == 200
        data = resp.json()
        assert set(data.keys()) == {"career_slug", "duration_days", "days", "reflection_prompt"}
        assert len(data["days"]) >= 1
        assert data["days"][0]["day_range"] == "Day 1-2"

    def test_duration_days_is_always_seven(self, seeded_client, capture_ai):
        """The AI returned 5 — the service must enforce the 7-day MVP contract."""
        capture_ai([json.dumps(AI_TRIAL_PLAN)])
        resp = seeded_client.post("/api/v1/career/trial-plan", json={"career_slug": "software-engineering"})
        assert resp.status_code == 200
        assert resp.json()["duration_days"] == 7

    def test_career_slug_is_pinned_to_request(self, seeded_client, capture_ai):
        capture_ai([json.dumps(AI_TRIAL_PLAN)])
        resp = seeded_client.post("/api/v1/career/trial-plan", json={"career_slug": "software-engineering"})
        assert resp.json()["career_slug"] == "software-engineering"

    def test_unknown_career_returns_404(self, seeded_client, capture_ai):
        ai = capture_ai([json.dumps(AI_TRIAL_PLAN)])
        resp = seeded_client.post("/api/v1/career/trial-plan", json={"career_slug": "nope"})
        assert resp.status_code == 404
        ai.chat.completions.create.assert_not_called()

    def test_student_profile_included_in_context(self, seeded_client, capture_ai):
        ai = capture_ai([json.dumps(AI_TRIAL_PLAN)])
        seeded_client.post("/api/v1/career/trial-plan", json={"career_slug": "software-engineering"})
        system_prompt = ai.chat.completions.create.call_args.kwargs["messages"][0]["content"]
        assert "Demo Student" in system_prompt
        assert "beginner" in system_prompt

    def test_career_data_included_in_context(self, seeded_client, capture_ai):
        ai = capture_ai([json.dumps(AI_TRIAL_PLAN)])
        seeded_client.post("/api/v1/career/trial-plan", json={"career_slug": "software-engineering"})
        system_prompt = ai.chat.completions.create.call_args.kwargs["messages"][0]["content"]
        assert "Software Engineering" in system_prompt
        assert "Data Structures" in system_prompt

    def test_invalid_ai_response_retries_then_succeeds(self, seeded_client, capture_ai):
        ai = capture_ai(["garbage {", json.dumps(AI_TRIAL_PLAN)])
        resp = seeded_client.post("/api/v1/career/trial-plan", json={"career_slug": "software-engineering"})
        assert resp.status_code == 200
        assert resp.json()["duration_days"] == 7
        assert ai.chat.completions.create.call_count == 2

    def test_persistent_ai_failure_is_controlled_error(self, seeded_client, capture_ai):
        capture_ai(["garbage {", "garbage again"])
        resp = seeded_client.post("/api/v1/career/trial-plan", json={"career_slug": "software-engineering"})
        assert resp.status_code == 500
        assert resp.json() == {"error": "AI response could not be processed"}

    def test_ai_unavailable_is_503(self, seeded_client, capture_ai):
        capture_ai([connection_error(), connection_error()])
        resp = seeded_client.post("/api/v1/career/trial-plan", json={"career_slug": "software-engineering"})
        assert resp.status_code == 503
        assert resp.json() == {"error": "AI service temporarily unavailable"}


# ---------------------------------------------------------------------------
# Service-level: demo student missing must stay honest (no invention)
# ---------------------------------------------------------------------------


class TestDemoStudentContext:
    def test_missing_demo_student_produces_honest_context(self, client, db_session, monkeypatch):
        """No demo student in the DB — context must say so, not invent one."""
        db_session.add(Career(**FULL_CAREER))
        db_session.commit()

        captured_prompt: list[str] = []

        class _FakeAI:
            def call_structured(self, prompt, response_model, system_prompt=None, operation=""):
                captured_prompt.append(system_prompt or "")
                return CareerRealityResponse.model_validate(AI_REALITY_RESPONSE)

        monkeypatch.setattr(career_service, "get_ai_service", lambda: _FakeAI())

        result = career_service.analyze_career(db_session, "software-engineering")

        assert "not yet onboarded" in captured_prompt[0]
        assert result.reality.demand_level == "HIGH"  # grounding still enforced
