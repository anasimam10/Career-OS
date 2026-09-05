"""
Test suite for the restored 7-step onboarding questionnaire and session isolation.
Covers:
1. Full 7-step payload submission (Education, Province, City, Field, Interests, Skills, Sports, Motivation).
2. Persistence of all 7 attributes in Student and StudentProfile models.
3. Journey bootstrap with personalized context (city, stage, sports, career).
4. Multi-student session isolation (Student A vs Student B with different locations and pathways).
"""

import json
from unittest.mock import MagicMock
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient

from main import app
from services import nba_service
from services.ai_service import AIService


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def mock_qwen(monkeypatch):
    """Mock the NBA engine's AI call to ensure rapid, deterministic, offline execution."""
    client = MagicMock()
    content = json.dumps({"candidate_id": "explore_careers", "why_this_matters": "Personalized next step."})
    message = SimpleNamespace(content=content)
    choice = SimpleNamespace(message=message)
    client.chat.completions.create.return_value = SimpleNamespace(choices=[choice])
    service = AIService(client=client)
    monkeypatch.setattr(nba_service, "get_ai_service", lambda: service)
    yield


def test_7step_onboarding_persistence_and_journey(client):
    """Verify that all 7 onboarding areas are submitted, persisted, and visible in profile & journey."""
    payload = {
        "education_stage": "HIGH_SCHOOL",
        "province": "Sindh",
        "city": "Karachi",
        "career_interests": ["Software Engineering"],
        "interests": ["Technology", "Mathematics", "Coding"],
        "skills": [
            {"name": "Python", "level": "intermediate"},
            {"name": "Problem Solving", "level": "beginner"},
        ],
        "sports_interest": "Cricket",
        "motivation_tags": ["I genuinely love this subject", "High salary potential"],
    }

    # Submit onboarding with X-Student-Id: new
    res = client.post("/api/v1/onboarding", json=payload, headers={"X-Student-Id": "new"})
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["profile_updated"] is True
    assert "student_id" in data
    student_id = data["student_id"]
    assert student_id > 0

    # 1. Verify Profile retrieval via GET /api/v1/students/{student_id}
    profile_res = client.get(f"/api/v1/students/{student_id}")
    assert profile_res.status_code == 200
    pdata = profile_res.json()

    assert pdata["education_stage"] == "HIGH_SCHOOL"
    assert pdata["province"] == "Sindh"
    assert pdata["city"] == "Karachi"
    assert pdata["career_goal"] == "software-engineering"
    assert pdata["sports_interest"] == "Cricket"
    assert "I genuinely love this subject" in pdata["motivation_tags"]
    assert "Technology" in pdata["interests"]
    assert any(s["name"] == "Python" for s in pdata["skills"])

    # 2. Verify Journey reflects actual student context
    journey_res = client.get(f"/api/v1/journey/{student_id}")
    assert journey_res.status_code == 200
    jdata = journey_res.json()

    assert jdata["city"] == "Karachi"
    assert "High School" in jdata["education_stage_label"]
    assert jdata["sports_interest"] == "Cricket"
    assert len(jdata["milestones"]) > 0


def test_multiple_students_isolation(client):
    """Verify that Student A and Student B have separate IDs, separate profiles, and no data leakage."""
    # Student A: Karachi, Software, Cricket
    payload_a = {
        "education_stage": "UNIVERSITY",
        "province": "Sindh",
        "city": "Karachi",
        "career_interests": ["Software Engineering"],
        "interests": ["Technology", "AI"],
        "skills": [{"name": "Python", "level": "intermediate"}],
        "sports_interest": "Cricket",
        "motivation_tags": ["High salary potential"],
    }
    res_a = client.post("/api/v1/onboarding", json=payload_a, headers={"X-Student-Id": "new"})
    assert res_a.status_code == 200
    id_a = res_a.json()["student_id"]

    # Student B: Lahore, Business Administration, No sport
    payload_b = {
        "education_stage": "CAREER_DISCOVERY",
        "province": "Punjab",
        "city": "Lahore",
        "career_interests": ["business-administration"],
        "interests": ["Finance", "Economics"],
        "skills": [{"name": "Financial Accounting", "level": "beginner"}],
        "sports_interest": None,
        "motivation_tags": ["Job security"],
    }
    res_b = client.post("/api/v1/onboarding", json=payload_b, headers={"X-Student-Id": "new"})
    assert res_b.status_code == 200
    id_b = res_b.json()["student_id"]

    assert id_a != id_b

    # Verify Student A profile
    prof_a = client.get(f"/api/v1/students/{id_a}").json()
    assert prof_a["city"] == "Karachi"
    assert prof_a["province"] == "Sindh"
    assert prof_a["sports_interest"] == "Cricket"
    assert "Technology" in prof_a["interests"]
    assert "Finance" not in prof_a["interests"]

    # Verify Student B profile
    prof_b = client.get(f"/api/v1/students/{id_b}").json()
    assert prof_b["city"] == "Lahore"
    assert prof_b["province"] == "Punjab"
    assert prof_b["sports_interest"] is None
    assert "Finance" in prof_b["interests"]
    assert "Technology" not in prof_b["interests"]

    # Verify Student A journey
    journ_a = client.get(f"/api/v1/journey/{id_a}").json()
    assert journ_a["city"] == "Karachi"
    assert journ_a["sports_interest"] == "Cricket"

    # Verify Student B journey
    journ_b = client.get(f"/api/v1/journey/{id_b}").json()
    assert journ_b["city"] == "Lahore"
    assert journ_b["sports_interest"] is None
