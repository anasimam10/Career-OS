"""
Onboarding service (Phase 4).

POST /api/v1/onboarding: update the demo student's profile from the
onboarding wizard payload, bootstrap the journey (stage + milestones),
and generate the student's first Next Best Action.

City note: the architecture §7 `students` / `student_profiles` tables have
no city column, so the accepted `city` field is validated (payload contract)
but not persisted — documented in implementation-status.md.
"""

from __future__ import annotations

import json
import logging

from sqlalchemy.orm import Session

from models.student import Student
from repositories.student_repo import StudentRepository
from schemas.requests import OnboardingPayload
from schemas.responses import OnboardingResponse
from services import nba_service, roadmap_service
from services.candidate_service import resolve_career
from services.journey_state import DEMO_STUDENT_ID

logger = logging.getLogger("ah_career.journey")

# The wizard's "no direction yet" placeholder must not become a career goal.
_NO_GOAL_VALUES = {"", "not sure yet", "unsure", "undecided"}


import uuid

def complete_onboarding(
    db: Session,
    payload: OnboardingPayload,
    student_id: Optional[int] = None,
    is_new: bool = False,
) -> OnboardingResponse:
    """
    1. Ensure or create the target student (new session or demo student).
    2. Persist the profile (stage, interests, skills, goal, sport, motivation).
    3. Bootstrap journey milestones for the student's stage.
    4. Generate and persist the first Next Best Action.
    """
    if is_new:
        repo = StudentRepository(db)
        email = f"student_{uuid.uuid4().hex[:8]}@ahcareers.local"
        student = repo.create_with_profile(
            name="Student",
            email=email,
            password_hash="session_guest",
            education_stage=payload.education_stage.value,
        )
    elif student_id and student_id != DEMO_STUDENT_ID:
        student = db.get(Student, student_id)
        if student is None:
            repo = StudentRepository(db)
            student = repo.create_with_profile(
                id=student_id,
                name="Student",
                email=f"student_{student_id}_{uuid.uuid4().hex[:6]}@ahcareers.local",
                password_hash="session_guest",
                education_stage=payload.education_stage.value,
            )
    else:
        student = _ensure_demo_student(db)

    career = _resolve_goal_career(db, payload.career_interests)

    # ---- Student row: journey state + scalar profile fields --------------
    student.education_stage = payload.education_stage.value
    student.city = payload.city
    student.sports_interest = payload.sports_interest
    student.motivation_tags = json.dumps(payload.motivation_tags, ensure_ascii=False)
    student.career_goal = career.slug if career is not None else None
    db.commit()

    # ---- Profile row: interests, skills; invalidate the cached NBA -------
    StudentRepository(db).update_profile(
        student.id,
        interests=json.dumps(payload.interests, ensure_ascii=False),
        skills=json.dumps(
            [skill.model_dump() for skill in payload.skills], ensure_ascii=False
        ),
        next_best_action=None,  # profile changed — NBA must be recomputed
    )

    # ---- Journey bootstrap: milestones for the current stage -------------
    roadmap_service.ensure_stage_milestones(
        db, student.id, student.education_stage,
        career_id=career.id if career is not None else None,
    )

    # ---- First Next Best Action -------------------------------------------
    nba = nba_service.generate_nba(db, student, force_refresh=True)

    logger.info(
        "Onboarding complete: student=%s stage=%s goal=%s",
        student.id, student.education_stage, student.career_goal,
    )
    return OnboardingResponse(profile_updated=True, next_best_action=nba, student_id=student.id)



# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _ensure_demo_student(db: Session) -> Student:
    """
    The MVP demo-student session (architecture §8/§12): student id 1.

    Created on first onboarding when missing so the endpoint also works on
    a fresh database (no registration flow in the MVP).
    """
    student = db.get(Student, DEMO_STUDENT_ID)
    if student is not None:
        return student
    repo = StudentRepository(db)
    student = repo.create_with_profile(
        id=DEMO_STUDENT_ID,
        name="Demo Student",
        email="demo@ahcareers.local",
        password_hash="demo",
        education_stage="HIGH_SCHOOL",
    )
    logger.info("Demo student created (id=%s)", DEMO_STUDENT_ID)
    return student


def _resolve_goal_career(db: Session, career_interests: list[str]):
    """
    Pick the student's career goal from the wizard's career_interests.

    The frontend sends display names ("Software Engineering"); the goal is
    stored as the matching verified career slug when one exists, and stays
    None for honest placeholders like "Not sure yet".
    """
    for interest in career_interests:
        if interest.strip().lower() in _NO_GOAL_VALUES:
            continue
        career = resolve_career(db, interest)
        if career is not None:
            return career
    return None
