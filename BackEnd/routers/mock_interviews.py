"""Router for Mock Interviews."""

import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models.student import Student
from models.mock_interview import MockInterviewSession, MockInterviewQuestion
from routers.deps import get_current_student_id
from schemas.mock_interview import (
    MockInterviewSetupRequest,
    MockInterviewSessionResponse,
    MockInterviewSubmitAnswerRequest,
    MockInterviewResultsResponse,
    MockInterviewResultTopic,
    MockInterviewQuestionReview,
    MockInterviewOption
)
from services.mock_interview_service import generate_mock_interview, submit_answer, complete_interview

router = APIRouter(prefix="/mock-interviews", tags=["Mock Interviews"])

@router.post("/setup", response_model=MockInterviewSessionResponse)
def setup_mock_interview(
    request: MockInterviewSetupRequest,
    db: Session = Depends(get_db),
    current_student_id: int = Depends(get_current_student_id),
):
    """Generates a new mock interview session."""
    try:
        session = generate_mock_interview(db, current_student_id, request)
        return _serialize_session(session)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate mock interview: {str(e)}"
        )

@router.get("/{session_id}", response_model=MockInterviewSessionResponse)
def get_mock_interview(
    session_id: int,
    db: Session = Depends(get_db),
    current_student_id: int = Depends(get_current_student_id),
):
    """Retrieves an active mock interview session."""
    session = db.query(MockInterviewSession).filter(
        MockInterviewSession.id == session_id,
        MockInterviewSession.student_id == current_student_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        
    return _serialize_session(session)

@router.post("/{session_id}/submit")
def submit_question_answer(
    session_id: int,
    request: MockInterviewSubmitAnswerRequest,
    db: Session = Depends(get_db),
    current_student_id: int = Depends(get_current_student_id),
):
    """Submits an answer for a specific question."""
    try:
        submit_answer(db, current_student_id, session_id, request)
        return {"status": "success"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/{session_id}/complete", response_model=MockInterviewResultsResponse)
def finish_mock_interview(
    session_id: int,
    db: Session = Depends(get_db),
    current_student_id: int = Depends(get_current_student_id),
):
    """Completes the interview and returns the results."""
    try:
        session = complete_interview(db, current_student_id, session_id)
        return _serialize_results(session, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{session_id}/results", response_model=MockInterviewResultsResponse)
def get_mock_interview_results(
    session_id: int,
    db: Session = Depends(get_db),
    current_student_id: int = Depends(get_current_student_id),
):
    """Retrieves the results for a completed mock interview."""
    session = db.query(MockInterviewSession).filter(
        MockInterviewSession.id == session_id,
        MockInterviewSession.student_id == current_student_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        
    if session.status != "completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Interview not yet completed")
        
    return _serialize_results(session, db)

def _serialize_session(session: MockInterviewSession) -> dict:
    """Serializes a session to the response schema (hiding correct answers)."""
    questions = []
    for q in session.questions:
        options = json.loads(q.options)
        questions.append({
            "id": q.id,
            "question_text": q.question_text,
            "options": options,
            "selected_option_id": q.selected_option_id,
            "topic": q.topic
        })
        
    return {
        "id": session.id,
        "career_context": session.career_context,
        "difficulty": session.difficulty,
        "status": session.status,
        "score": session.score,
        "total_questions": session.total_questions,
        "started_at": session.started_at,
        "completed_at": session.completed_at,
        "questions": questions
    }

def _serialize_results(session: MockInterviewSession, db: Session) -> dict:
    """Serializes a completed session to the results schema with real verified learning resources."""
    questions = []
    topics = {}
    
    # Pre-fetch active learning resources to link real courses
    from models.learning import LearningResource
    active_resources = db.query(LearningResource).filter(
        LearningResource.is_active == True,
        LearningResource.verification_status.in_(["VALIDATED", "VERIFIED"])
    ).all()
    resource_by_id = {str(r.id): r for r in active_resources}

    for q in session.questions:
        options = json.loads(q.options)
        source_ids = json.loads(q.source_resource_ids) if q.source_resource_ids else []
        
        is_correct = q.selected_option_id == q.correct_option_id
        
        if q.topic not in topics:
            topics[q.topic] = {"correct": 0, "total": 0}
            
        topics[q.topic]["total"] += 1
        if is_correct:
            topics[q.topic]["correct"] += 1

        # Find real matching resource
        matched_res = None
        for sid in source_ids:
            if str(sid) in resource_by_id:
                matched_res = resource_by_id[str(sid)]
                break
        if not matched_res and active_resources:
            # Topic or general fallback
            for r in active_resources:
                if (r.skill_name and r.skill_name.lower() in q.topic.lower()) or (r.title and any(w in r.title.lower() for w in q.topic.lower().split())):
                    matched_res = r
                    break
            if not matched_res:
                matched_res = active_resources[0]

        questions.append({
            "id": q.id,
            "question_text": q.question_text,
            "options": options,
            "selected_option_id": q.selected_option_id,
            "correct_option_id": q.correct_option_id,
            "explanation": q.explanation,
            "topic": q.topic,
            "source_resource_ids": source_ids,
            "resource_url": matched_res.url if matched_res else None,
            "resource_title": matched_res.title if matched_res else None
        })
        
    topic_performance = [
        {"topic": t, "correct": stats["correct"], "total": stats["total"]}
        for t, stats in topics.items()
    ]
    
    score = session.score or 0.0
    if score >= 90:
        label = "Excellent"
    elif score >= 70:
        label = "Strong foundation"
    elif score >= 50:
        label = "Needs practice"
    else:
        label = "Start with the fundamentals"
        
    total_correct = sum(1 for q in session.questions if q.selected_option_id == q.correct_option_id)
    
    # NBA logic grounded in real database resources
    weakest_topic = min(topic_performance, key=lambda x: x["correct"] / x["total"] if x["total"] > 0 else 1.0, default=None)
    
    nba_text = "Practice another Mock Interview"
    nba_url = None
    nba_resource_id = None

    if weakest_topic and (weakest_topic["correct"] < weakest_topic["total"]):
        topic_name = weakest_topic["topic"]
        # Find matching resource in DB
        matching_res = None
        for r in active_resources:
            if (r.skill_name and r.skill_name.lower() in topic_name.lower()) or (r.title and any(w in r.title.lower() for w in topic_name.lower().split())):
                matching_res = r
                break
        if not matching_res and active_resources:
            matching_res = active_resources[0]
            
        if matching_res:
            nba_text = f"Master {topic_name}: {matching_res.title} ({matching_res.provider or 'Verified Course'})"
            nba_url = matching_res.url
            nba_resource_id = str(matching_res.id)
        else:
            nba_text = f"Review {topic_name} fundamentals"

    return {
        "id": session.id,
        "career_context": session.career_context,
        "difficulty": session.difficulty,
        "score": score,
        "total_correct": total_correct,
        "total_questions": session.total_questions,
        "performance_label": label,
        "topic_performance": topic_performance,
        "questions_review": questions,
        "next_best_action_text": nba_text,
        "next_best_action_resource_id": nba_resource_id,
        "next_best_action_url": nba_url
    }

