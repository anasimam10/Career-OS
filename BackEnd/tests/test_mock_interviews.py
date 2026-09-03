"""Comprehensive Integration & Security tests for Mock Interviews."""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models.student import Student, StudentProfile
from models.mock_interview import MockInterviewSession, MockInterviewQuestion
from models.career import Career
from models.learning import LearningResource
from schemas.mock_interview import (
    MockInterviewGenerationResult,
    MockInterviewQuestionSchema,
    MockInterviewOption,
)
from services.mock_interview_service import _build_grounded_fallback

def _create_student(db: Session, email: str, name: str = "Test Student") -> Student:
    """Helper to create a persisted student in the test database."""
    student = Student(
        name=name,
        email=email,
        password_hash="hashed_test_pw",
        education_stage="UNIVERSITY",
    )
    db.add(student)
    db.flush()
    profile = StudentProfile(
        student_id=student.id,
        interests='["Coding", "Data Structures"]',
        skills='[{"name": "Python", "level": "intermediate"}]',
    )
    db.add(profile)
    db.commit()
    db.refresh(student)
    return student


def test_mock_interview_flow_and_security(client: TestClient, db_session: Session):
    """Test full interview lifecycle, answer security, deterministic scoring, and student isolation."""
    # Seed a career and learning resources for grounding
    cs_career = Career(
        slug="software-engineering",
        name="Software Engineering",
        field="Computer Science",
        required_skills='["Data Structures", "Algorithms", "Web Development"]',
        is_active=True
    )
    db_session.add(cs_career)

    res = LearningResource(
        title="CS50x Introduction to Computer Science",
        provider="Harvard University",
        skill_name="Data Structures",
        url="https://cs50.harvard.edu/x",
        level="beginner",
        is_active=True,
        verification_status="VERIFIED"
    )
    db_session.add(res)
    db_session.commit()

    # Create two isolated students
    student_a = _create_student(db_session, "student_a@example.com", "Student A")
    student_b = _create_student(db_session, "student_b@example.com", "Student B")

    headers_a = {"X-Student-Id": str(student_a.id)}
    headers_b = {"X-Student-Id": str(student_b.id)}

    mock_qwen_result = MockInterviewGenerationResult(
        title="Software Engineering Mock Interview (Beginner)",
        career="Software Engineering",
        difficulty="beginner",
        questions=[
            MockInterviewQuestionSchema(
                id=f"q_{i}",
                question=f"What is the complexity of operation {i}?",
                options=[
                    MockInterviewOption(id="A", text="Option A (Correct)"),
                    MockInterviewOption(id="B", text="Option B (Wrong)"),
                    MockInterviewOption(id="C", text="Option C (Wrong)"),
                    MockInterviewOption(id="D", text="Option D (Wrong)"),
                ],
                correct_option="A",
                explanation=f"Option A is correct for question {i} because of fundamental logic.",
                topic="Data Structures",
                source_resource_ids=[str(res.id)]
            )
            for i in range(1, 11)
        ]
    )

    # 1. Setup Mock Interview for Student A with Qwen AI mocked
    with patch("services.mock_interview_service.get_ai_service") as mock_ai_factory:
        mock_ai = MagicMock()
        mock_ai.is_configured.return_value = True
        mock_ai.call_structured.return_value = mock_qwen_result
        mock_ai_factory.return_value = mock_ai

        setup_resp = client.post(
            "/api/v1/mock-interviews/setup",
            json={
                "career_context": "Software Engineering",
                "difficulty": "beginner"
            },
            headers=headers_a
        )
        assert setup_resp.status_code == 200, setup_resp.text
        session_data = setup_resp.json()
        session_id = session_data["id"]

        # Verify Qwen was called with expected contracts
        mock_ai.call_structured.assert_called_once()
        call_kwargs = mock_ai.call_structured.call_args.kwargs
        assert call_kwargs["response_model"] == MockInterviewGenerationResult
        assert call_kwargs["operation"] == "generate_mock_interview"
        assert "Software Engineering" in call_kwargs["prompt"]

    assert session_data["career_context"] == "Software Engineering"
    assert session_data["difficulty"] == "beginner"
    assert session_data["status"] == "in_progress"
    assert len(session_data["questions"]) == 10

    # 2. ANSWER SECURITY: Assert correct option & explanation are NOT exposed before completion
    for q in session_data["questions"]:
        assert "correct_option_id" not in q, "Security breach: correct_option_id leaked before submission"
        assert "explanation" not in q, "Security breach: explanation leaked before submission"

    # 3. STUDENT ISOLATION: Student B cannot access Student A's in-progress session
    unauth_get = client.get(f"/api/v1/mock-interviews/{session_id}", headers=headers_b)
    assert unauth_get.status_code == 404, "Isolation breach: Student B accessed Student A's session"

    # Student A can access their own session
    auth_get = client.get(f"/api/v1/mock-interviews/{session_id}", headers=headers_a)
    assert auth_get.status_code == 200
    assert auth_get.json()["id"] == session_id

    # 4. Answer Questions (Deterministically: 8 correct, 2 incorrect)
    db_questions = db_session.query(MockInterviewQuestion).filter(
        MockInterviewQuestion.session_id == session_id
    ).order_by(MockInterviewQuestion.id).all()
    assert len(db_questions) == 10

    for i, q in enumerate(db_questions):
        # 8 correct answers (A), 2 incorrect answers (B)
        selected = q.correct_option_id if i < 8 else "B"

        # Student B cannot submit answers to Student A's session
        unauth_submit = client.post(
            f"/api/v1/mock-interviews/{session_id}/submit",
            json={"question_id": q.id, "selected_option_id": selected},
            headers=headers_b
        )
        assert unauth_submit.status_code in [400, 404], "Isolation breach: Student B submitted answer to Student A"

        # Student A submits answer
        submit_resp = client.post(
            f"/api/v1/mock-interviews/{session_id}/submit",
            json={"question_id": q.id, "selected_option_id": selected},
            headers=headers_a
        )
        assert submit_resp.status_code == 200

    # 5. Complete Interview
    # Student B cannot complete Student A's session
    unauth_complete = client.post(f"/api/v1/mock-interviews/{session_id}/complete", headers=headers_b)
    assert unauth_complete.status_code in [400, 404]

    # Student A completes session
    complete_resp = client.post(f"/api/v1/mock-interviews/{session_id}/complete", headers=headers_a)
    assert complete_resp.status_code == 200
    results = complete_resp.json()

    # 6. DETERMINISTIC SCORING AUDIT: 8/10 = 80%
    assert results["id"] == session_id
    assert results["total_questions"] == 10
    assert results["total_correct"] == 8
    assert results["score"] == 80.0
    assert results["performance_label"] in ["Strong foundation", "Excellent", "Needs practice"]
    assert len(results["topic_performance"]) > 0
    assert len(results["questions_review"]) == 10

    # 7. Post-completion: Answers and explanations are now safely available for review
    for q in results["questions_review"]:
        assert "correct_option_id" in q
        assert "explanation" in q
        assert q["explanation"] is not None and len(q["explanation"]) > 0

    # 8. Learning Feedback Loop: Next Best Action & Resource link
    assert "next_best_action_text" in results
    assert results["next_best_action_text"] is not None

    # 9. Access control: Cannot resubmit answers after interview is completed
    post_complete_submit = client.post(
        f"/api/v1/mock-interviews/{session_id}/submit",
        json={"question_id": db_questions[0].id, "selected_option_id": "A"},
        headers=headers_a
    )
    assert post_complete_submit.status_code == 400
    assert "completed" in post_complete_submit.text.lower()


def test_career_specific_grounding(client: TestClient, db_session: Session):
    """Verify career-specific question generation for Software Engineering vs Accounting & Finance."""
    student = _create_student(db_session, "career_test@example.com")
    headers = {"X-Student-Id": str(student.id)}

    # A: Software Engineering / Computer Science fallback generation
    se_fallback = _build_grounded_fallback("Software Engineering", "intermediate", db_session)
    assert len(se_fallback.questions) == 10
    se_topics = [q.topic for q in se_fallback.questions]
    assert any(t in ["Data Structures", "Software Architecture", "Web Development & APIs", "Database Systems"] for t in se_topics)

    # B: Accounting & Finance fallback generation
    af_fallback = _build_grounded_fallback("Accounting & Finance", "intermediate", db_session)
    assert len(af_fallback.questions) == 10
    af_topics = [q.topic for q in af_fallback.questions]
    assert any(t in ["Financial Accounting", "Financial Reporting", "Cost Accounting", "Corporate Finance", "Auditing & Internal Controls"] for t in af_topics)

    # Questions for SE and AF must NOT be identical generic questions
    se_q_texts = [q.question for q in se_fallback.questions]
    af_q_texts = [q.question for q in af_fallback.questions]
    assert se_q_texts != af_q_texts, "Career grounding failure: SE and AF received identical questions"

    # Verify both contain 4 options and valid correct answers
    for q in se_fallback.questions + af_fallback.questions:
        assert len(q.options) == 4
        option_ids = [opt.id for opt in q.options]
        assert q.correct_option in option_ids
