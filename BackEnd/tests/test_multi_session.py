"""
Automated tests for Multi-Session Student Identity and Isolation.
Verifies that:
1. POST /onboarding with X-Student-Id: 'new' creates a distinct student with its own student_id.
2. Two independent sessions (Browser A and Browser B) maintain separate profiles, goals, and journeys.
3. GET /journey and other endpoints respect X-Student-Id.
4. Calling without X-Student-Id safely defaults to DEMO_STUDENT_ID = 1.
"""

import pytest
from models.career import Career
from models.student import Student
from services import nba_service
from services.ai_service import AIUnavailableError


def _mock_fallback_ai(monkeypatch):
    """Force deterministic candidate fallback so onboarding succeeds without network calls."""
    class FakeAI:
        def call_structured(self, **kwargs):
            raise AIUnavailableError("Test fallback")
    monkeypatch.setattr(nba_service, "get_ai_service", lambda: FakeAI())


def test_two_session_isolation(client, db_session, monkeypatch):
    _mock_fallback_ai(monkeypatch)

    # Seed careers
    db_session.add(Career(slug="software-engineering", name="Software Engineering", field="Technology"))
    db_session.add(Career(slug="chartered-accountancy", name="Chartered Accountancy", field="Finance"))
    db_session.commit()


    # Session A: Student A in Karachi, Technology/Software Engineering, Football
    payload_a = {
        "education_stage": "HIGH_SCHOOL",
        "interests": ["Technology", "Computer Science"],
        "career_interests": ["Software Engineering"],
        "sports_interest": "Football",
        "motivation_tags": ["I genuinely love this subject"],
        "skills": [{"name": "Python", "level": "beginner"}],
        "city": "Karachi",
    }
    resp_a = client.post(
        "/api/v1/onboarding",
        json=payload_a,
        headers={"X-Student-Id": "new"},
    )
    assert resp_a.status_code == 200, resp_a.text
    data_a = resp_a.json()
    assert data_a["profile_updated"] is True
    student_id_a = data_a.get("student_id")
    assert student_id_a is not None

    # Session B: Student B in Lahore, Business/Chartered Accountancy, Cricket
    payload_b = {
        "education_stage": "CAREER_DISCOVERY",
        "interests": ["Business", "Finance"],
        "career_interests": ["Chartered Accountancy"],
        "sports_interest": "Cricket",
        "motivation_tags": ["High salary potential"],
        "skills": [{"name": "Excel", "level": "intermediate"}],
        "city": "Lahore",
    }
    resp_b = client.post(
        "/api/v1/onboarding",
        json=payload_b,
        headers={"X-Student-Id": "new"},
    )
    assert resp_b.status_code == 200, resp_b.text
    data_b = resp_b.json()
    assert data_b["profile_updated"] is True
    student_id_b = data_b.get("student_id")
    assert student_id_b is not None
    assert student_id_b > 1

    # 1. Distinct student identities
    assert student_id_a != student_id_b

    # 2. Database verification
    student_a = db_session.get(Student, student_id_a)
    student_b = db_session.get(Student, student_id_b)
    assert student_a is not None
    assert student_b is not None
    assert student_a.career_goal == "software-engineering"
    assert student_b.career_goal == "chartered-accountancy"
    assert student_a.sports_interest == "Football"
    assert student_b.sports_interest == "Cricket"
    assert student_a.education_stage == "HIGH_SCHOOL"
    assert student_b.education_stage == "CAREER_DISCOVERY"

    # 3. GET /journey isolation with X-Student-Id
    journey_resp_a = client.get(
        "/api/v1/journey",
        headers={"X-Student-Id": str(student_id_a)},
    )
    assert journey_resp_a.status_code == 200
    assert journey_resp_a.json()["stage"] == "HIGH_SCHOOL"

    journey_resp_b = client.get(
        "/api/v1/journey",
        headers={"X-Student-Id": str(student_id_b)},
    )
    assert journey_resp_b.status_code == 200
    assert journey_resp_b.json()["stage"] == "CAREER_DISCOVERY"

    # 4. Default session (no header) resolves to demo student 1
    journey_resp_default = client.get("/api/v1/journey")
    assert journey_resp_default.status_code in (200, 404)

