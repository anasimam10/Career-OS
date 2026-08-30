"""
Deterministic candidate-action generator (Phase 4).

The Next Best Action pipeline starts here: given the student's profile,
journey stage, completed milestones, and career data, produce 3-8 VALID
candidate actions. Qwen then only SELECTS among them — it can never invent
an action.

This module is fully deterministic: database reads only, no Qwen calls.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from pydantic import BaseModel
from sqlalchemy.orm import Session

from models.career import Career
from models.student import Student
from repositories.career_repo import CareerRepository
from services import roadmap_service

logger = logging.getLogger("ah_career.journey")

MIN_CANDIDATES = 3
MAX_CANDIDATES = 8


class CandidateAction(BaseModel):
    """
    One valid, deterministic next-action candidate offered to Qwen.

    Carries everything needed to build a complete NextBestAction without
    any AI contribution (used for the deterministic fallback).
    """
    candidate_id: str
    action_type: str
    title: str
    description: str
    steps: list[str]
    estimated_time: str
    why_this_matters: str
    stage: str
    priority_score: float
    reason: str


# ---------------------------------------------------------------------------
# Candidate generation
# ---------------------------------------------------------------------------


def generate_candidates(db: Session, student: Student) -> list[CandidateAction]:
    """
    Build the valid candidate list for the student. Deterministic:
    same database state -> same candidates, same order.
    """
    stage = student.education_stage
    career = resolve_career(db, student.career_goal)
    completed_titles = roadmap_service.get_completed_titles(db, student.id)
    student_skills = _student_skill_names(db, student.id)

    candidates: list[CandidateAction] = []

    # --- milestone-linked candidates valid for the current stage ---------
    for template in roadmap_service.MILESTONE_TEMPLATES.get(stage, []):
        if template["title"] in completed_titles:
            continue  # already completed — do not suggest again
        candidates.append(
            _from_template(template, stage, priority=_stage_priority(template))
        )

    # --- dynamic learn-a-skill candidate (grounded in career data) -------
    learn_skill = _build_learn_skill_candidate(career, student_skills, stage)
    if learn_skill is not None:
        candidates.append(learn_skill)

    # --- always-valid fillers (kept small, lowest priority) --------------
    if career is not None:
        candidates.append(
            _from_template(
                roadmap_service.TEMPLATE_BY_ACTION_TYPE["REVIEW_CAREER_DATA"],
                stage,
                priority=0.20,
                reason="The career's verified data is available in the database",
            )
        )
    candidates.append(_update_profile_candidate(stage))

    # --- deterministic ordering + limits ---------------------------------
    seen: set[str] = set()
    unique: list[CandidateAction] = []
    for candidate in candidates:
        if candidate.candidate_id in seen:
            continue
        seen.add(candidate.candidate_id)
        unique.append(candidate)

    unique.sort(key=lambda c: (-c.priority_score, c.candidate_id))
    result = unique[:MAX_CANDIDATES]

    if len(result) < MIN_CANDIDATES:
        logger.warning(
            "Candidate pool below minimum: student=%s stage=%s count=%s",
            student.id, stage, len(result),
        )
    return result


def candidate_context(db: Session, student: Student) -> dict:
    """Journey-state context sent to Qwen alongside the candidates."""
    completed_titles = sorted(
        roadmap_service.get_completed_titles(db, student.id)
    )
    return {
        "current_stage": student.education_stage,
        "career_goal": student.career_goal,
        "completed_milestones": completed_titles,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _from_template(
    template: dict, stage: str, priority: float, reason: Optional[str] = None
) -> CandidateAction:
    action_type = template["action_type"]
    return CandidateAction(
        candidate_id=action_type.lower(),
        action_type=action_type,
        title=template["title"],
        description=template["description"],
        steps=list(template["steps"]),
        estimated_time=template["estimated_duration"],
        why_this_matters=template["why_this_matters"],
        stage=stage,
        priority_score=priority,
        reason=reason or f"Valid next action for the {stage} stage",
    )


def _stage_priority(template: dict) -> float:
    """Deterministic priority for the first template of a stage."""
    priorities = {
        "CAREER_TRIAL": 0.90,
        "CAREER_REALITY": 0.85,
        "EXPLORE_CAREERS": 0.80,
        "COMPARE_CAREERS": 0.85,
        "FINALIZE_DECISION": 0.75,
        "LEARN_FIRST_SKILL": 0.90,
        "PRACTICE_SKILL": 0.80,
        "BUILD_PROJECT": 0.90,
        "DOCUMENT_PROJECT": 0.75,
        "PREPARE_CV": 0.90,
        "INTERNSHIP_READY": 0.80,
        "FINAL_PROJECT": 0.85,
        "INTERVIEW_PREP": 0.80,
        "JOB_SEARCH_ROUTINE": 0.70,
        "SET_90_DAY_GOALS": 0.85,
        "PROFESSIONAL_SKILLS": 0.70,
    }
    return priorities.get(template["action_type"], 0.50)


def _build_learn_skill_candidate(
    career: Optional[Career], student_skills: set[str], stage: str
) -> Optional[CandidateAction]:
    """
    Dynamic candidate: learn the FIRST required skill (from the verified
    career record) that the student does not have yet. Fully grounded in
    database data — nothing invented.
    """
    if career is None:
        return None
    try:
        required = json.loads(career.required_skills or "[]")
    except (json.JSONDecodeError, TypeError):
        required = []
    if not required:
        return None

    missing = [
        skill
        for skill in required
        if skill.lower() not in {s.lower() for s in student_skills}
    ]
    if not missing:
        return None

    skill = missing[0]
    slug = skill.lower().replace(" ", "_").replace("/", "_")
    return CandidateAction(
        candidate_id=f"learn_skill_{slug}",
        action_type="LEARN_SKILL",
        title=f"Learn {skill} fundamentals",
        description=(
            f"{skill} is the first required skill for {career.name} "
            "that you have not added to your profile yet."
        ),
        steps=[
            f"Find a free beginner tutorial for {skill}",
            f"Complete the first three lessons",
            f"Build one small example using {skill}",
        ],
        estimated_time="2-3 weeks",
        why_this_matters=(
            f"{skill} is listed as a required skill for {career.name} "
            "in the verified career data."
        ),
        stage=stage,
        priority_score=0.78,
        reason=f"Required skill '{skill}' is missing from the student profile",
    )


def _update_profile_candidate(stage: str) -> CandidateAction:
    return CandidateAction(
        candidate_id="update_profile",
        action_type="UPDATE_PROFILE",
        title="Refine your profile",
        description=(
            "Revisit your interests, skills, and career goal so the mentor "
            "can plan better next steps."
        ),
        steps=[
            "Open the onboarding questions again",
            "Update your skills and interests",
            "Save the changes",
        ],
        estimated_time="10 minutes",
        why_this_matters="An accurate profile makes every recommendation sharper.",
        stage=stage,
        priority_score=0.10,
        reason="Always a valid low-priority action",
    )


def resolve_career(db: Session, career_goal: Optional[str]) -> Optional[Career]:
    """Resolve the student's career goal to a verified Career record.

    Accepts either a slug ("software-engineering") or a display name
    ("Software Engineering" — the format the frontend sends in
    career_interests). Public: reused by onboarding_service.
    """
    if not career_goal:
        return None
    repo = CareerRepository(db)
    career = repo.get_by_slug(career_goal)
    if career is not None:
        return career
    # goal may be stored as the display name (frontend career_interests)
    for record in repo.get_all_careers():
        if record.name.lower() == career_goal.lower():
            return record
    return None


def _student_skill_names(db: Session, student_id: int) -> set[str]:
    from repositories.student_repo import StudentRepository

    profile = StudentRepository(db).get_profile(student_id)
    if profile is None or not profile.skills:
        return set()
    try:
        skills = json.loads(profile.skills)
    except (json.JSONDecodeError, TypeError):
        return set()
    return {
        entry.get("name", "")
        for entry in skills
        if isinstance(entry, dict)
    }
