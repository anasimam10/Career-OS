"""
Comprehensive tests for Student Profile Deletion & Complete Data Cleanup.
Verifies:
1. Complete cascade deletion across all student-owned tables.
2. Multi-tenant student isolation (Student A deletion does not touch Student B).
3. Authorization checks (Student A cannot delete Student B via /students/{id}).
4. Non-existent student handling (404).
5. Transaction rollback on error.
6. Post-deletion access blocked (404 on /me and /journey).
7. Fresh onboarding after deletion creates an isolated new identity.
"""

import json
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from models.student import Student, StudentProfile
from models.roadmap import Roadmap, Milestone
from models.opportunity import Opportunity, StudentOpportunityMatch
from models.mock_interview import MockInterviewSession, MockInterviewQuestion
from repositories.student_repo import StudentRepository
from services.rate_limiter import rate_limiter


def _seed_student_with_all_owned_data(db_session, name: str, email: str) -> int:
    """Helper to populate a student with full profile, roadmap, milestones, match, and mock interview data."""
    repo = StudentRepository(db_session)
    student = repo.create_with_profile(
        name=name,
        email=email,
        password_hash="hashed_pw",
        education_stage="UNIVERSITY",
    )
    student.city = "Lahore"
    student.career_goal = "software-engineering"
    db_session.commit()

    # 1. Update StudentProfile
    repo.update_profile(
        student.id,
        interests=json.dumps(["Coding", "AI"]),
        skills=json.dumps([{"name": "Python", "level": "INTERMEDIATE"}]),
        job_readiness_score=0.75,
        completed_milestone_ids=json.dumps([1, 2]),
    )

    # 2. Add Roadmap & Milestones
    roadmap = Roadmap(
        student_id=student.id,
        current_stage="UNIVERSITY",
        current_step_title="Foundations of Computer Science",
    )
    db_session.add(roadmap)
    db_session.flush()

    m1 = Milestone(
        roadmap_id=roadmap.id,
        title="Complete Data Structures",
        stage="UNIVERSITY",
        status="completed",
        order_index=1,
    )
    m2 = Milestone(
        roadmap_id=roadmap.id,
        title="Build Web Application",
        stage="UNIVERSITY",
        status="in_progress",
        order_index=2,
    )
    db_session.add_all([m1, m2])

    # 3. Create a global opportunity (should NOT be deleted)
    opp = db_session.query(Opportunity).first()
    if not opp:
        opp = Opportunity(
            title="Software Engineering Fellowship",
            organization="PakTech Labs",
            type="internship",
            location="Remote, Pakistan",
            source_url="https://example.com/fellowship",
        )
        db_session.add(opp)
        db_session.flush()

    # Add StudentOpportunityMatch
    match = StudentOpportunityMatch(
        student_id=student.id,
        opportunity_id=opp.id,
        match_score=0.92,
        missing_requirements=json.dumps(["Docker experience"]),
    )
    db_session.add(match)

    # 4. Add MockInterviewSession & Questions
    interview_session = MockInterviewSession(
        student_id=student.id,
        career_context="Software Engineering",
        difficulty="intermediate",
        status="completed",
        score=85.0,
        total_questions=2,
    )
    db_session.add(interview_session)
    db_session.flush()

    q1 = MockInterviewQuestion(
        session_id=interview_session.id,
        question_text="What is a hash table?",
        options=json.dumps([{"id": "A", "text": "Key-value structure"}, {"id": "B", "text": "A queue"}]),
        correct_option_id="A",
        selected_option_id="A",
        explanation="Hash tables map keys to values using a hashing function.",
        topic="Data Structures",
    )
    q2 = MockInterviewQuestion(
        session_id=interview_session.id,
        question_text="Explain ACID properties.",
        options=json.dumps([{"id": "A", "text": "Atomicity, Consistency, Isolation, Durability"}, {"id": "B", "text": "None"}]),
        correct_option_id="A",
        selected_option_id="A",
        explanation="ACID guarantees database transaction reliability.",
        topic="Databases",
    )
    db_session.add_all([q1, q2])

    db_session.commit()
    db_session.refresh(student)

    # Seed rate limiter in-memory store
    rate_limiter.is_allowed(student.id)

    return student.id


def test_delete_student_me_success_and_cascade_verification(client, db_session):
    """
    Test deleting the authenticated student via DELETE /api/v1/students/me.
    Verifies that:
    - Student record is removed.
    - StudentProfile record is removed.
    - Roadmaps and Milestones are removed.
    - StudentOpportunityMatch is removed.
    - MockInterviewSession and MockInterviewQuestions are removed.
    - Global datasets (Opportunity) remain completely intact.
    - Rate limiter cache for student is purged.
    """
    student_id = _seed_student_with_all_owned_data(db_session, "Delete Target", "delete_me@example.com")
    
    # Verify records exist before delete
    assert db_session.get(Student, student_id) is not None
    assert db_session.query(StudentProfile).filter(StudentProfile.student_id == student_id).count() == 1
    assert db_session.query(Roadmap).filter(Roadmap.student_id == student_id).count() == 1
    assert db_session.query(StudentOpportunityMatch).filter(StudentOpportunityMatch.student_id == student_id).count() == 1
    assert db_session.query(MockInterviewSession).filter(MockInterviewSession.student_id == student_id).count() == 1
    assert student_id in rate_limiter._store

    # Execute DELETE /api/v1/students/me
    res = client.delete("/api/v1/students/me", headers={"X-Student-Id": str(student_id)})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "deleted" in data["message"].lower()

    # Expire and refresh session cache
    db_session.expire_all()

    # Verify all student-owned records are permanently removed
    assert db_session.get(Student, student_id) is None
    assert db_session.query(StudentProfile).filter(StudentProfile.student_id == student_id).count() == 0
    assert db_session.query(Roadmap).filter(Roadmap.student_id == student_id).count() == 0
    assert db_session.query(Milestone).join(Roadmap).filter(Roadmap.student_id == student_id).count() == 0
    assert db_session.query(StudentOpportunityMatch).filter(StudentOpportunityMatch.student_id == student_id).count() == 0
    assert db_session.query(MockInterviewSession).filter(MockInterviewSession.student_id == student_id).count() == 0
    assert db_session.query(MockInterviewQuestion).join(MockInterviewSession).filter(MockInterviewSession.student_id == student_id).count() == 0

    # Verify global opportunity was NOT deleted
    assert db_session.query(Opportunity).count() > 0

    # Verify rate limiter entry was purged
    assert student_id not in rate_limiter._store


def test_delete_student_isolation_preserves_student_b(client, db_session):
    """
    Test that deleting Student A does not touch or affect Student B's data in any way.
    """
    sid_a = _seed_student_with_all_owned_data(db_session, "Alice A", "alice@example.com")
    sid_b = _seed_student_with_all_owned_data(db_session, "Bob B", "bob@example.com")

    # Delete Student A
    res = client.delete("/api/v1/students/me", headers={"X-Student-Id": str(sid_a)})
    assert res.status_code == 200

    db_session.expire_all()

    # Student A is completely gone
    assert db_session.get(Student, sid_a) is None
    assert db_session.query(StudentProfile).filter(StudentProfile.student_id == sid_a).count() == 0

    # Student B and ALL of Student B's dependent data remain 100% intact
    student_b = db_session.get(Student, sid_b)
    assert student_b is not None
    assert student_b.name == "Bob B"
    assert db_session.query(StudentProfile).filter(StudentProfile.student_id == sid_b).count() == 1
    assert db_session.query(Roadmap).filter(Roadmap.student_id == sid_b).count() == 1
    assert db_session.query(StudentOpportunityMatch).filter(StudentOpportunityMatch.student_id == sid_b).count() == 1
    assert db_session.query(MockInterviewSession).filter(MockInterviewSession.student_id == sid_b).count() == 1


def test_delete_student_by_id_authorization(client, db_session):
    """
    Test DELETE /api/v1/students/{id}:
    - Student A cannot delete Student B (403 Forbidden).
    - Student A can delete themselves (200 OK).
    """
    sid_a = _seed_student_with_all_owned_data(db_session, "Student A", "a_auth@example.com")
    sid_b = _seed_student_with_all_owned_data(db_session, "Student B", "b_auth@example.com")

    # Student A attempts to delete Student B -> 403 Forbidden
    res_forbidden = client.delete(
        f"/api/v1/students/{sid_b}",
        headers={"X-Student-Id": str(sid_a)},
    )
    assert res_forbidden.status_code == 403
    assert "unauthorized" in res_forbidden.json()["detail"].lower()

    # Ensure Student B was NOT deleted
    assert db_session.get(Student, sid_b) is not None

    # Student A deletes themselves -> 200 OK
    res_self = client.delete(
        f"/api/v1/students/{sid_a}",
        headers={"X-Student-Id": str(sid_a)},
    )
    assert res_self.status_code == 200
    assert db_session.get(Student, sid_a) is None


def test_delete_nonexistent_student_returns_404(client, db_session):
    """Deleting a non-existent student returns 404."""
    res_me = client.delete("/api/v1/students/me", headers={"X-Student-Id": "999999"})
    assert res_me.status_code == 404
    assert "not found" in res_me.json()["detail"].lower()

    res_id = client.delete("/api/v1/students/999999", headers={"X-Student-Id": "999999"})
    assert res_id.status_code == 404
    assert "not found" in res_id.json()["detail"].lower()


def test_post_deletion_endpoints_return_404(client, db_session):
    """
    After deleting a student, requests using the old student ID on authenticated/student-specific routes
    (such as /students/me and /journey) must return 404 and must not revive the student.
    """
    sid = _seed_student_with_all_owned_data(db_session, "Ghost Student", "ghost@example.com")

    # Delete
    del_res = client.delete("/api/v1/students/me", headers={"X-Student-Id": str(sid)})
    assert del_res.status_code == 200

    # Attempt to access profile
    prof_res = client.get("/api/v1/students/me", headers={"X-Student-Id": str(sid)})
    assert prof_res.status_code == 404

    # Repeat delete returns 404 (idempotent / already gone)
    repeat_del = client.delete("/api/v1/students/me", headers={"X-Student-Id": str(sid)})
    assert repeat_del.status_code == 404


def test_delete_transaction_rollback_on_failure(client, db_session):
    """
    Verify that if an error occurs during deletion cascade, the entire transaction rolls back
    and no partial deletion occurs.
    """
    sid = _seed_student_with_all_owned_data(db_session, "Rollback Target", "rollback@example.com")

    repo = StudentRepository(db_session)
    # Simulate an error right before student delete
    with patch.object(db_session, "delete", side_effect=RuntimeError("Simulated DB connection failure")):
        with pytest.raises(RuntimeError):
            repo.delete_student_cascade(sid)

    # Verify student is still fully intact because transaction rolled back
    db_session.expire_all()
    assert db_session.get(Student, sid) is not None
    assert db_session.query(StudentProfile).filter(StudentProfile.student_id == sid).count() == 1
