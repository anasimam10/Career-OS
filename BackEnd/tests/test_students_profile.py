"""
Tests for Student Profile Endpoints & Multi-Student Isolation.
"""

import json
import pytest
from fastapi.testclient import TestClient

from main import app
from models.student import Student
from repositories.student_repo import StudentRepository


def test_get_my_profile_not_found(client, db_session):
    """Calling /students/me with a non-existent student ID returns 404."""
    response = client.get("/api/v1/students/me", headers={"X-Student-Id": "999999"})
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_student_profile_lifecycle_and_isolation(client, db_session):
    """Verify Student A and Student B have isolated profiles and editing persists."""
    repo = StudentRepository(db_session)
    
    # 1. Create Student A
    student_a = repo.create_with_profile(
        name="Student Alpha",
        email="alpha@example.com",
        password_hash="hash1",
        education_stage="UNIVERSITY",
    )
    student_a.city = "Lahore"
    student_a.career_goal = "software-engineering"
    student_a.sports_interest = "Badminton"
    student_a.motivation_tags = json.dumps(["High Salary", "Tech Passion"])
    db_session.commit()

    # 2. Create Student B
    student_b = repo.create_with_profile(
        name="Student Beta",
        email="beta@example.com",
        password_hash="hash2",
        education_stage="HIGH_SCHOOL",
    )
    student_b.city = "Karachi"
    student_b.career_goal = "accounting-finance"
    student_b.sports_interest = "Cricket"
    student_b.motivation_tags = json.dumps(["Stability"])
    db_session.commit()

    # 3. Retrieve Profile for Student A
    res_a = client.get("/api/v1/students/me", headers={"X-Student-Id": str(student_a.id)})
    assert res_a.status_code == 200
    data_a = res_a.json()
    assert data_a["id"] == student_a.id
    assert data_a["name"] == "Student Alpha"
    assert data_a["city"] == "Lahore"
    assert data_a["career_goal"] == "software-engineering"
    assert data_a["sports_interest"] == "Badminton"
    assert "High Salary" in data_a["motivation_tags"]

    # 4. Retrieve Profile for Student B (Verify Isolation)
    res_b = client.get("/api/v1/students/me", headers={"X-Student-Id": str(student_b.id)})
    assert res_b.status_code == 200
    data_b = res_b.json()
    assert data_b["id"] == student_b.id
    assert data_b["name"] == "Student Beta"
    assert data_b["city"] == "Karachi"
    assert data_b["career_goal"] == "accounting-finance"
    assert data_b["sports_interest"] == "Cricket"
    assert "Stability" in data_b["motivation_tags"]
    # Ensure Student B data is completely different from Student A
    assert data_b["city"] != data_a["city"]
    assert data_b["career_goal"] != data_a["career_goal"]

    # 5. Update Profile for Student A
    update_payload = {
        "city": "Islamabad",
        "career_goal": "data-science",
        "sports_interest": "Tennis",
        "motivation_tags": ["AI Impact", "Fast Growth"],
        "interests": ["Machine Learning", "Cloud Systems"],
        "skills": [{"name": "Python", "level": "ADVANCED"}, {"name": "SQL", "level": "INTERMEDIATE"}]
    }
    update_res = client.put(
        "/api/v1/students/me",
        json=update_payload,
        headers={"X-Student-Id": str(student_a.id)},
    )
    assert update_res.status_code == 200
    updated_a = update_res.json()
    assert updated_a["city"] == "Islamabad"
    assert updated_a["career_goal"] == "data-science"
    assert updated_a["sports_interest"] == "Tennis"
    assert "AI Impact" in updated_a["motivation_tags"]
    assert "Machine Learning" in updated_a["interests"]
    assert len(updated_a["skills"]) == 2

    # 6. Verify Student B profile was NOT modified by Student A's update
    res_b_again = client.get("/api/v1/students/me", headers={"X-Student-Id": str(student_b.id)})
    assert res_b_again.status_code == 200
    data_b_again = res_b_again.json()
    assert data_b_again["city"] == "Karachi"
    assert data_b_again["career_goal"] == "accounting-finance"


def test_onboarding_persists_city(client, db_session):
    """Verify onboarding wizard persists city directly to Student record."""
    payload = {
        "education_stage": "UNIVERSITY",
        "interests": ["Finance", "Economics"],
        "career_interests": ["Accounting and Finance"],
        "sports_interest": "Squash",
        "motivation_tags": ["Professional Prestige"],
        "skills": [{"name": "Accounting", "level": "beginner"}],
        "city": "Rawalpindi"
    }
    res = client.post("/api/v1/onboarding", json=payload, headers={"X-Student-Id": "new"})
    assert res.status_code == 200
    sid = res.json()["student_id"]
    assert sid is not None

    # Check via student profile endpoint
    prof_res = client.get(f"/api/v1/students/{sid}")
    assert prof_res.status_code == 200
    assert prof_res.json()["city"] == "Rawalpindi"
    assert prof_res.json()["sports_interest"] == "Squash"
    assert prof_res.json()["education_stage"] == "UNIVERSITY"
