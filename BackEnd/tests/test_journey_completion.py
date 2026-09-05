"""
Tests for Journey Completion End-to-End.

Covers:
1. Happy path milestone completion & subsequent milestone activation.
2. Duplicate completion returning HTTP 400 with detail 'already_completed'.
3. Invalid milestone (does not belong to student's journey) returning HTTP 403.
4. Completing all milestones setting current_milestone_id to None and all completed.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock
import pytest

from models.student import Student
from repositories.student_repo import StudentRepository
from services import roadmap_service, nba_service


@pytest.fixture(autouse=True)
def mock_nba(monkeypatch):
    """Mock NBA generation so tests run offline without consuming LLM quota."""
    mock_service = MagicMock()
    mock_service.rank_candidates.return_value = MagicMock(
        candidate_id="EXPLORE_CAREERS",
        ai_rationale="Continue your self-discovery path.",
    )
    monkeypatch.setattr(nba_service, "get_ai_service", lambda: mock_service)


def _setup_student(db_session, student_id: int = 1, stage: str = "HIGH_SCHOOL") -> Student:
    repo = StudentRepository(db_session)
    student = repo.create_with_profile(
        id=student_id,
        name=f"Student {student_id}",
        email=f"student_{student_id}@test.local",
        password_hash="test",
        education_stage=stage,
    )
    student.city = "Karachi"
    student.province = "Sindh"
    db_session.commit()
    roadmap_service.ensure_stage_milestones(db_session, student.id, stage)
    return student


def test_journey_completion_happy_path(client, db_session):
    """Happy path: complete active milestone -> sets to completed -> next becomes active."""
    student = _setup_student(db_session, student_id=101)

    # 1. Fetch initial journey
    res = client.get(f"/api/v1/journey/{student.id}")
    assert res.status_code == 200, res.text
    initial_data = res.json()
    assert len(initial_data["milestones"]) >= 2
    m1 = initial_data["milestones"][0]
    m2 = initial_data["milestones"][1]
    assert m1["status"] == "active"
    assert m2["status"] == "locked"
    assert initial_data["completed_count"] == 0
    assert initial_data["current_milestone_id"] == m1["id"]

    # 2. Complete milestone 1
    complete_res = client.post(f"/api/v1/journey/{student.id}/milestones/{m1['id']}/complete")
    assert complete_res.status_code == 200, complete_res.text
    updated_data = complete_res.json()

    # Milestone 1 should now be completed, Milestone 2 should now be active
    updated_m1 = next(m for m in updated_data["milestones"] if m["id"] == m1["id"])
    updated_m2 = next(m for m in updated_data["milestones"] if m["id"] == m2["id"])

    assert updated_m1["status"] == "completed"
    assert updated_m2["status"] == "active"
    assert updated_data["completed_count"] == 1
    assert updated_data["current_milestone_id"] == m2["id"]

    # Verify DB persisted state via fresh GET
    refetch_res = client.get(f"/api/v1/journey/{student.id}")
    assert refetch_res.status_code == 200
    assert refetch_res.json()["completed_count"] == 1
    assert refetch_res.json()["current_milestone_id"] == m2["id"]


def test_journey_completion_duplicate_rejected(client, db_session):
    """Duplicate completion of already completed milestone returns HTTP 400 'already_completed'."""
    student = _setup_student(db_session, student_id=102)

    res = client.get(f"/api/v1/journey/{student.id}")
    m1_id = res.json()["milestones"][0]["id"]

    # First completion succeeds
    first_res = client.post(f"/api/v1/journey/{student.id}/milestones/{m1_id}/complete")
    assert first_res.status_code == 200

    # Second completion returns 400
    dup_res = client.post(f"/api/v1/journey/{student.id}/milestones/{m1_id}/complete")
    assert dup_res.status_code == 400
    assert dup_res.json()["detail"] == "already_completed"


def test_journey_completion_forbidden_for_other_student(client, db_session):
    """Attempting to complete another student's milestone returns HTTP 403."""
    student_a = _setup_student(db_session, student_id=103)
    student_b = _setup_student(db_session, student_id=104)

    # Get student B's milestone
    res_b = client.get(f"/api/v1/journey/{student_b.id}")
    m_b_id = res_b.json()["milestones"][0]["id"]

    # Student A attempts to complete Student B's milestone
    res = client.post(f"/api/v1/journey/{student_a.id}/milestones/{m_b_id}/complete")
    assert res.status_code == 403
    assert "not belong" in res.json()["detail"].lower()


def test_journey_completion_last_milestone(client, db_session):
    """Completing all milestones leaves all completed with current_milestone_id = None."""
    student = _setup_student(db_session, student_id=105, stage="FIRST_JOB")

    res = client.get(f"/api/v1/journey/{student.id}")
    milestones = res.json()["milestones"]

    # Complete all milestones sequentially
    final_data = None
    for m in milestones:
        c_res = client.post(f"/api/v1/journey/{student.id}/milestones/{m['id']}/complete")
        assert c_res.status_code == 200
        final_data = c_res.json()

    assert final_data is not None
    assert final_data["completed_count"] == final_data["total_count"]
    assert all(m["status"] == "completed" for m in final_data["milestones"])
    assert final_data["current_milestone_id"] is None
