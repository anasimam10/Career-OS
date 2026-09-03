"""
Student Profile Router.

Provides endpoints to fetch and update the authenticated student's profile:
- GET /api/v1/students/me
- PUT /api/v1/students/me
- GET /api/v1/students/{student_id}
- PUT /api/v1/students/{student_id}
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from models.student import Student, StudentProfile
from repositories.student_repo import StudentRepository
from routers.deps import get_current_student_id

logger = logging.getLogger("ah_career.students")

router = APIRouter(prefix="/students", tags=["students"])


class SkillItem(BaseModel):
    name: str
    level: str = "BEGINNER"


class UpdateStudentPayload(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    education_stage: Optional[str] = None
    career_goal: Optional[str] = None
    sports_interest: Optional[str] = None
    motivation_tags: Optional[List[str]] = None
    interests: Optional[List[str]] = None
    skills: Optional[List[Dict[str, Any]]] = None


class StudentProfileResponse(BaseModel):
    id: int
    name: str
    email: str
    city: Optional[str] = None
    education_stage: str
    career_goal: Optional[str] = None
    sports_interest: Optional[str] = None
    motivation_tags: List[str] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=list)
    skills: List[Dict[str, Any]] = Field(default_factory=list)
    job_readiness_score: float = 0.0
    completed_milestone_ids: List[int] = Field(default_factory=list)
    next_best_action: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


def _parse_json_list(val: Optional[str]) -> list:
    if not val:
        return []
    try:
        parsed = json.loads(val)
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []


def _parse_json_dict(val: Optional[str]) -> Optional[dict]:
    if not val:
        return None
    try:
        parsed = json.loads(val)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        return None


def _build_profile_response(student: Student) -> StudentProfileResponse:
    profile = student.profile
    interests = _parse_json_list(profile.interests) if profile else []
    skills = _parse_json_list(profile.skills) if profile else []
    milestones = _parse_json_list(profile.completed_milestone_ids) if profile else []
    nba = _parse_json_dict(profile.next_best_action) if profile else None
    motivation = _parse_json_list(student.motivation_tags)

    return StudentProfileResponse(
        id=student.id,
        name=student.name,
        email=student.email,
        city=student.city,
        education_stage=student.education_stage,
        career_goal=student.career_goal,
        sports_interest=student.sports_interest,
        motivation_tags=motivation,
        interests=interests,
        skills=skills,
        job_readiness_score=profile.job_readiness_score if profile else 0.0,
        completed_milestone_ids=milestones,
        next_best_action=nba,
        created_at=student.created_at.isoformat() if student.created_at else None,
        updated_at=student.updated_at.isoformat() if student.updated_at else None,
    )


@router.get("/me", response_model=StudentProfileResponse)
def get_my_profile(
    student_id: int = Depends(get_current_student_id),
    db: Session = Depends(get_db),
) -> StudentProfileResponse:
    """Return the profile for the current active student session."""
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found. Please complete onboarding first.",
        )
    return _build_profile_response(student)


@router.put("/me", response_model=StudentProfileResponse)
def update_my_profile(
    payload: UpdateStudentPayload,
    student_id: int = Depends(get_current_student_id),
    db: Session = Depends(get_db),
) -> StudentProfileResponse:
    """Update profile fields for the current active student session."""
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found. Please complete onboarding first.",
        )

    # 1. Update scalar fields on Student
    if payload.name is not None:
        student.name = payload.name.strip()
    if payload.city is not None:
        student.city = payload.city.strip()
    if payload.education_stage is not None:
        student.education_stage = payload.education_stage.strip().upper()
    if payload.career_goal is not None:
        student.career_goal = payload.career_goal.strip() or None
    if payload.sports_interest is not None:
        student.sports_interest = payload.sports_interest.strip() or None
    if payload.motivation_tags is not None:
        student.motivation_tags = json.dumps(payload.motivation_tags, ensure_ascii=False)

    # 2. Update StudentProfile row
    repo = StudentRepository(db)
    profile_updates = {}
    if payload.interests is not None:
        profile_updates["interests"] = json.dumps(payload.interests, ensure_ascii=False)
    if payload.skills is not None:
        profile_updates["skills"] = json.dumps(payload.skills, ensure_ascii=False)

    if profile_updates:
        repo.update_profile(student.id, **profile_updates)

    db.commit()
    db.refresh(student)
    return _build_profile_response(student)


@router.get("/{target_student_id}", response_model=StudentProfileResponse)
def get_student_by_id(
    target_student_id: int,
    db: Session = Depends(get_db),
) -> StudentProfileResponse:
    """Retrieve profile by student ID."""
    student = db.get(Student, target_student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {target_student_id} not found.",
        )
    return _build_profile_response(student)


@router.put("/{target_student_id}", response_model=StudentProfileResponse)
def update_student_by_id(
    target_student_id: int,
    payload: UpdateStudentPayload,
    db: Session = Depends(get_db),
) -> StudentProfileResponse:
    """Update profile by student ID."""
    student = db.get(Student, target_student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {target_student_id} not found.",
        )

    if payload.name is not None:
        student.name = payload.name.strip()
    if payload.city is not None:
        student.city = payload.city.strip()
    if payload.education_stage is not None:
        student.education_stage = payload.education_stage.strip().upper()
    if payload.career_goal is not None:
        student.career_goal = payload.career_goal.strip() or None
    if payload.sports_interest is not None:
        student.sports_interest = payload.sports_interest.strip() or None
    if payload.motivation_tags is not None:
        student.motivation_tags = json.dumps(payload.motivation_tags, ensure_ascii=False)

    repo = StudentRepository(db)
    profile_updates = {}
    if payload.interests is not None:
        profile_updates["interests"] = json.dumps(payload.interests, ensure_ascii=False)
    if payload.skills is not None:
        profile_updates["skills"] = json.dumps(payload.skills, ensure_ascii=False)

    if profile_updates:
        repo.update_profile(student.id, **profile_updates)

    db.commit()
    db.refresh(student)
    return _build_profile_response(student)
