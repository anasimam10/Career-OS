"""
E2E Lifecycle Verification:
Student A Onboarding -> Data Generation -> Profile Deletion -> Database Audit ->
Ghost ID Access Check -> Student B Clean Onboarding
"""

import json
from unittest.mock import MagicMock
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient

from main import app
from models.student import Student, StudentProfile
from models.roadmap import Roadmap, Milestone
from services import nba_service
from services.ai_service import AIService


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


def test_full_student_lifecycle_e2e(client, db_session):
    # 1. Complete onboarding for Student A
    onboard_payload_a = {
        "education_stage": "UNIVERSITY",
        "interests": ["Machine Learning", "Software Development"],
        "career_interests": ["software-engineering"],
        "sports_interest": "Badminton",
        "motivation_tags": ["Tech Passion", "High Growth"],
        "skills": [{"name": "Python", "level": "intermediate"}],
        "city": "Lahore",
    }
    res_a = client.post("/api/v1/onboarding", json=onboard_payload_a, headers={"X-Student-Id": "new"})
    assert res_a.status_code == 200
    student_a_id = res_a.json()["student_id"]
    assert student_a_id is not None

    # Verify Student A profile
    prof_a = client.get("/api/v1/students/me", headers={"X-Student-Id": str(student_a_id)})
    assert prof_a.status_code == 200
    assert prof_a.json()["city"] == "Lahore"
    assert prof_a.json()["sports_interest"] == "Badminton"

    # Verify Journey/Roadmap created for Student A
    journey_a = client.get("/api/v1/journey", headers={"X-Student-Id": str(student_a_id)})
    assert journey_a.status_code == 200
    assert len(journey_a.json()["milestones"]) > 0

    # 2. Complete onboarding for Student B (Isolation baseline)
    onboard_payload_b = {
        "education_stage": "HIGH_SCHOOL",
        "interests": ["Finance"],
        "career_interests": ["accounting-finance"],
        "sports_interest": "Cricket",
        "motivation_tags": ["Stability"],
        "skills": [{"name": "Accounting", "level": "beginner"}],
        "city": "Karachi",
    }
    res_b = client.post("/api/v1/onboarding", json=onboard_payload_b, headers={"X-Student-Id": "new"})
    assert res_b.status_code == 200
    student_b_id = res_b.json()["student_id"]
    assert student_b_id != student_a_id

    # 3. Delete Student A via /api/v1/students/me
    del_res = client.delete("/api/v1/students/me", headers={"X-Student-Id": str(student_a_id)})
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # 4. Database verification: Student A's records are completely wiped
    db_session.expire_all()
    assert db_session.get(Student, student_a_id) is None
    assert db_session.query(StudentProfile).filter(StudentProfile.student_id == student_a_id).count() == 0
    assert db_session.query(Roadmap).filter(Roadmap.student_id == student_a_id).count() == 0
    assert db_session.query(Milestone).join(Roadmap).filter(Roadmap.student_id == student_a_id).count() == 0

    # 5. Security & Post-delete verification: Old Student A ID cannot access /students/me
    re_get = client.get("/api/v1/students/me", headers={"X-Student-Id": str(student_a_id)})
    assert re_get.status_code == 404

    # 6. Verify Student B is completely intact
    prof_b = client.get("/api/v1/students/me", headers={"X-Student-Id": str(student_b_id)})
    assert prof_b.status_code == 200
    assert prof_b.json()["city"] == "Karachi"
    assert prof_b.json()["sports_interest"] == "Cricket"
    assert db_session.get(Student, student_b_id) is not None
    assert db_session.query(Roadmap).filter(Roadmap.student_id == student_b_id).count() >= 1

    # 7. Create a fresh Student C (simulating new onboarding after deletion)
    res_c = client.post("/api/v1/onboarding", json=onboard_payload_a, headers={"X-Student-Id": "new"})
    assert res_c.status_code == 200
    student_c_id = res_c.json()["student_id"]
    assert student_c_id != student_a_id
    assert student_c_id != student_b_id
    assert db_session.get(Student, student_c_id) is not None
