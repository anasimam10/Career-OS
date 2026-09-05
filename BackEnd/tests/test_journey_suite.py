"""
Comprehensive Journey test suite covering the 15 requirements specified in Section 34.
"""

from __future__ import annotations

from unittest.mock import MagicMock
import pytest
from starlette.testclient import TestClient

from models.student import Student
from models.roadmap import Milestone, Roadmap
from services import nba_service


@pytest.fixture(autouse=True)
def mock_nba(monkeypatch):
    """Mock NBA generation so tests run offline without calling Qwen."""
    mock_service = MagicMock()
    mock_service.rank_candidates.return_value = MagicMock(
        candidate_id="career_reality",
        ai_rationale="Continue your self-discovery path.",
    )
    monkeypatch.setattr(nba_service, "get_ai_service", lambda: mock_service)


@pytest.fixture
def test_student_and_journey(client: TestClient, db_session):
    """Create a clean student through onboarding and return (student_id, initial_journey)."""
    payload = {
        "education_stage": "HIGH_SCHOOL",
        "interests": ["Software Engineering"],
        "career_interests": ["Software Engineering"],
        "sports_interest": None,
        "motivation_tags": ["High Salary", "Job Security"],
        "skills": [{"name": "Python", "level": "beginner"}],
        "city": "Karachi",
        "province": "Sindh",
    }
    resp = client.post("/api/v1/onboarding", json=payload)
    assert resp.status_code == 200
    student_id = resp.json()["student_id"]

    # Fetch initial journey
    j_resp = client.get(f"/api/v1/journey/{student_id}", headers={"X-Student-Id": str(student_id)})
    assert j_resp.status_code == 200
    return student_id, j_resp.json()


def test_1_new_student_gets_correct_initial_journey(test_student_and_journey):
    """Case 1: New student gets correct initial Journey."""
    student_id, journey = test_student_and_journey
    assert journey["milestones"]
    assert len(journey["milestones"]) >= 5
    assert journey["completed_count"] == 0
    assert journey["total_count"] == len(journey["milestones"])


def test_2_correct_milestone_is_active(test_student_and_journey):
    """Case 2: Correct milestone is active (first milestone)."""
    student_id, journey = test_student_and_journey
    active_milestones = [m for m in journey["milestones"] if m["status"] == "active"]
    assert len(active_milestones) == 1
    assert active_milestones[0]["order"] == 1
    assert journey["current_milestone_id"] == active_milestones[0]["id"]


def test_3_correct_milestones_are_upcoming(test_student_and_journey):
    """Case 3: Correct milestones are upcoming/locked."""
    student_id, journey = test_student_and_journey
    upcoming = [m for m in journey["milestones"] if m["status"] == "locked"]
    assert len(upcoming) == len(journey["milestones"]) - 1
    # All orders > 1 are locked
    assert all(m["order"] > 1 for m in upcoming)


def test_4_and_5_completing_current_milestone_persists_and_activates_next(client: TestClient, test_student_and_journey):
    """Cases 4 & 5: Completing current milestone persists and next becomes active."""
    student_id, journey = test_student_and_journey
    first_milestone = next(m for m in journey["milestones"] if m["status"] == "active")
    m1_id = first_milestone["id"]

    # Complete first milestone
    comp_resp = client.post(f"/api/v1/journey/{student_id}/milestones/{m1_id}/complete")
    assert comp_resp.status_code == 200
    updated = comp_resp.json()

    # Verify first milestone is completed
    m1_updated = next(m for m in updated["milestones"] if m["id"] == m1_id)
    assert m1_updated["status"] == "completed"

    # Verify second milestone is now active
    active_now = next(m for m in updated["milestones"] if m["status"] == "active")
    assert active_now["order"] == 2


def test_6_progress_percentage_changes(client: TestClient, test_student_and_journey):
    """Case 6: Progress percentage/count changes."""
    student_id, journey = test_student_and_journey
    assert journey["completed_count"] == 0

    first_m = next(m for m in journey["milestones"] if m["status"] == "active")
    comp_resp = client.post(f"/api/v1/journey/{student_id}/milestones/{first_m['id']}/complete")
    updated = comp_resp.json()
    assert updated["completed_count"] == 1


def test_7_duplicate_completion_does_not_corrupt_state(client: TestClient, test_student_and_journey):
    """Case 7: Duplicate completion does not corrupt state."""
    student_id, journey = test_student_and_journey
    first_m = next(m for m in journey["milestones"] if m["status"] == "active")

    # Complete once
    res1 = client.post(f"/api/v1/journey/{student_id}/milestones/{first_m['id']}/complete")
    assert res1.status_code == 200

    # Attempt second completion
    res2 = client.post(f"/api/v1/journey/{student_id}/milestones/{first_m['id']}/complete")
    assert res2.status_code == 400
    assert "already_completed" in res2.json().get("detail", "") or "already" in res2.json().get("detail", "")


def test_8_invalid_milestone_is_rejected(client: TestClient, test_student_and_journey):
    """Case 8: Invalid milestone is rejected (404)."""
    student_id, _ = test_student_and_journey
    res = client.post(f"/api/v1/journey/{student_id}/milestones/999999/complete")
    assert res.status_code == 404


def test_9_invalid_student_is_rejected(client: TestClient):
    """Case 9: Invalid student is rejected (404)."""
    res = client.get("/api/v1/journey/888888")
    assert res.status_code == 404


def test_10_student_isolation(client: TestClient, test_student_and_journey, db_session):
    """Case 10: Student A cannot complete Student B's journey milestone."""
    student_a_id, journey_a = test_student_and_journey

    # Create Student B with distinct session
    payload_b = {
        "education_stage": "UNIVERSITY",
        "interests": ["Business & Finance"],
        "career_interests": ["Business & Finance"],
        "sports_interest": None,
        "motivation_tags": ["Fast Growth"],
        "skills": [{"name": "Excel", "level": "intermediate"}],
        "city": "Lahore",
        "province": "Punjab",
    }
    resp_b = client.post("/api/v1/onboarding", json=payload_b, headers={"X-Student-Id": "new"})
    student_b_id = resp_b.json()["student_id"]
    assert student_b_id != student_a_id

    first_m_a = next(m for m in journey_a["milestones"] if m["status"] == "active")

    # Student B attempts to complete Student A's milestone -> 403
    hack_res = client.post(f"/api/v1/journey/{student_b_id}/milestones/{first_m_a['id']}/complete")
    assert hack_res.status_code == 403


def test_11_refresh_returns_persisted_state(client: TestClient, test_student_and_journey):
    """Case 11: Refresh returns persisted authoritative state."""
    student_id, journey = test_student_and_journey
    first_m = next(m for m in journey["milestones"] if m["status"] == "active")

    # Complete milestone
    client.post(f"/api/v1/journey/{student_id}/milestones/{first_m['id']}/complete")

    # Simulate fresh page reload
    refresh_resp = client.get(f"/api/v1/journey/{student_id}")
    refreshed = refresh_resp.json()

    assert refreshed["completed_count"] == 1
    m1 = next(m for m in refreshed["milestones"] if m["id"] == first_m["id"])
    assert m1["status"] == "completed"
    active_m = next(m for m in refreshed["milestones"] if m["status"] == "active")
    assert active_m["order"] == 2


def test_12_final_milestone_completes_correctly(client: TestClient, test_student_and_journey):
    """Case 12: Completing all milestones marks journey complete."""
    student_id, journey = test_student_and_journey
    milestones = journey["milestones"]

    for m in milestones:
        res = client.post(f"/api/v1/journey/{student_id}/milestones/{m['id']}/complete")
        assert res.status_code in (200, 400)

    final_journey = client.get(f"/api/v1/journey/{student_id}").json()
    assert final_journey["completed_count"] == final_journey["total_count"]
    assert all(m["status"] == "completed" for m in final_journey["milestones"])


def test_13_no_duplicate_journey_milestones_returned(test_student_and_journey):
    """Case 13: Zero duplicate Journey milestone titles returned for a student."""
    _, journey = test_student_and_journey
    titles = [m["title"] for m in journey["milestones"]]
    assert len(titles) == len(set(titles)), f"Duplicate titles found in journey: {titles}"


def test_14_reality_check_completion_activates_career_trial(client: TestClient, test_student_and_journey):
    """Case 14: Reality Check completion can activate Career Trial step."""
    student_id, journey = test_student_and_journey
    milestones = journey["milestones"]

    # If first step is Explore Careers, complete it
    first_m = milestones[0]
    if "explore" in first_m["title"].lower():
        client.post(f"/api/v1/journey/{student_id}/milestones/{first_m['id']}/complete")

    # Now Reality Check should be active
    j_after_1 = client.get(f"/api/v1/journey/{student_id}").json()
    reality_m = next(m for m in j_after_1["milestones"] if m["status"] == "active")
    assert "reality" in reality_m["title"].lower()

    # Complete Reality Check
    client.post(f"/api/v1/journey/{student_id}/milestones/{reality_m['id']}/complete")

    # Now 7-Day Career Trial MUST be active
    j_after_reality = client.get(f"/api/v1/journey/{student_id}").json()
    trial_m = next(m for m in j_after_reality["milestones"] if m["status"] == "active")
    assert "trial" in trial_m["title"].lower()
    assert trial_m["action_url"] == "/careers/software-engineering/trial"


def test_15_trial_completion_activates_next_appropriate_stage(client: TestClient, test_student_and_journey):
    """Case 15: Trial completion activates next appropriate stage."""
    student_id, journey = test_student_and_journey

    # Complete step 1 (Explore)
    m1 = journey["milestones"][0]
    client.post(f"/api/v1/journey/{student_id}/milestones/{m1['id']}/complete")

    # Complete step 2 (Reality Check)
    m2 = journey["milestones"][1]
    client.post(f"/api/v1/journey/{student_id}/milestones/{m2['id']}/complete")

    # Complete step 3 (Trial)
    m3 = journey["milestones"][2]
    trial_complete_res = client.post(f"/api/v1/journey/{student_id}/milestones/{m3['id']}/complete")
    assert trial_complete_res.status_code == 200

    j_after_trial = trial_complete_res.json()
    next_active = next(m for m in j_after_trial["milestones"] if m["status"] == "active")
    # Next active must not be trial and order must be 4
    assert "trial" not in next_active["title"].lower()
    assert next_active["order"] == 4
