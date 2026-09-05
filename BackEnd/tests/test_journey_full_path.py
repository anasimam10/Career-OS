"""
Test full pathway journey instantiation, action details, and multi-phase progression.
"""

from __future__ import annotations
from unittest.mock import MagicMock
import pytest

from models.student import Student
from repositories.student_repo import StudentRepository
from services import roadmap_service, nba_service


@pytest.fixture(autouse=True)
def mock_nba(monkeypatch):
    """Mock NBA generation so tests run offline without calling Qwen."""
    mock_service = MagicMock()
    mock_service.rank_candidates.return_value = MagicMock(
        candidate_id="career_reality",
        ai_rationale="Continue your self-discovery path.",
    )
    monkeypatch.setattr(nba_service, "get_ai_service", lambda: mock_service)


def test_full_path_journey_instantiation_and_actions(client, db_session):
    # 1. Create a fresh test student
    student_id = 8888
    repo = StudentRepository(db_session)
    student = repo.create_with_profile(
        id=student_id,
        name="Path Student",
        email=f"student_{student_id}@test.local",
        password_hash="test",
        education_stage="HIGH_SCHOOL",
        city="Lahore",
    )
    db_session.commit()

    # 2. Query journey - verify full multi-phase pathway exists
    journey_res = client.get(f"/api/v1/journey/{student_id}")
    assert journey_res.status_code == 200
    data = journey_res.json()

    milestones = data.get("milestones", [])
    assert len(milestones) >= 10, f"Expected full pathway with >= 10 milestones, got {len(milestones)}"

    # Check phase grouping
    phases = [m["phase"] for m in milestones]
    assert 1 in phases and 2 in phases and 3 in phases and 4 in phases, "Expected contiguous multi-phase progression"

    # Verify first milestone is active and has action details
    m1 = milestones[0]
    assert m1["status"] == "active"
    assert m1["action_url"] is not None
    assert m1["action_label"] is not None

    # Verify subsequent milestones are locked
    m2 = milestones[1]
    assert m2["status"] == "locked"
    assert "Reality Check" in m2["title"]

    m3 = milestones[2]
    assert m3["status"] == "locked"
    assert "7-Day" in m3["title"] or "Trial" in m3["title"]

    # 3. Complete Step 1 -> Reality Check should become active
    comp1 = client.post(f"/api/v1/journey/{student_id}/milestones/{m1['id']}/complete")
    assert comp1.status_code == 200
    data_after_1 = comp1.json()

    m1_updated = next(m for m in data_after_1["milestones"] if m["id"] == m1["id"])
    assert m1_updated["status"] == "completed"

    m2_updated = next(m for m in data_after_1["milestones"] if m["id"] == m2["id"])
    assert m2_updated["status"] == "active"
    assert "reality-check" in m2_updated["action_url"].lower()

    # 4. Complete Reality Check -> 7-Day Trial should become active
    comp2 = client.post(f"/api/v1/journey/{student_id}/milestones/{m2['id']}/complete")
    assert comp2.status_code == 200
    data_after_2 = comp2.json()

    m2_done = next(m for m in data_after_2["milestones"] if m["id"] == m2["id"])
    assert m2_done["status"] == "completed"

    m3_updated = next(m for m in data_after_2["milestones"] if m["id"] == m3["id"])
    assert m3_updated["status"] == "active"
    assert "trial" in m3_updated["action_url"].lower()
    assert "Start 7-Day Trial" in m3_updated["action_label"]
