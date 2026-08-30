"""
Job Readiness service (Phase 8).

POST /api/v1/job-readiness — deterministic scoring + AI gap analysis.

SCORING (fully deterministic, architecture §6.2):
    Skills      30%  (student_profiles.skills + careers.required_skills)
    Projects    20%  (milestones stage=PROJECTS status=done)
    Internship  20%  (milestones stage=INTERNSHIP status=done)
    CV          15%  (milestones title~=CV|resume|portfolio status=done)
    Interview   15%  (milestones title~=interview|mock status=done)

    overall_score = sum(component * weight)
    score_label   = f"{round(overall_score * 100)}%"

QWEN'S ROLE (architecture §6.4):
    - Receives only the component scores + student profile + biggest gap
    - Produces: gap_explanation, next_best_action, recommendations (max 3)
    - Can NEVER alter the deterministic score

MVP APPROXIMATIONS:
    These component scores are rough heuristics derived from milestone
    completion and profile data. They are NOT scientifically validated
    employability assessments. The disclaimer in every response states this.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from sqlalchemy.orm import Session

from models.career import Career
from models.roadmap import Roadmap, Milestone
from models.student import Student, StudentProfile
from prompts.job_readiness import build_job_readiness_system_prompt
from schemas.shared import JobReadiness, JobReadinessAIAnalysis, NextBestAction
from services.ai_service import (
    AIServiceError,
    get_ai_service,
)
from services.journey_state import DEMO_STUDENT_ID

logger = logging.getLogger("ah_career.job_readiness")

# Hardcoded weights (architecture §6.2 — not configurable)
_WEIGHTS = {
    "skills": 0.30,
    "projects": 0.20,
    "internship": 0.20,
    "cv": 0.15,
    "interview": 0.15,
}

# Hardcoded disclaimer (architecture §6.5)
DISCLAIMER_TEXT = (
    "This job readiness score is a product indicator based on your tracked "
    "milestones and profile data. It is not a scientifically validated "
    "assessment of your employability. Use it as a general guide only."
)

# Fallback text when Qwen is unavailable (architecture §6.6)
_FALLBACK_GAP_EXPLANATION = (
    "AI analysis is temporarily unavailable. "
    "Focus on your lowest-scoring component."
)


class StudentNotFoundError(Exception):
    """No onboarded student found."""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_job_readiness(db: Session) -> JobReadiness:
    """
    Compute the deterministic job readiness score, then call Qwen for
    gap analysis. If Qwen fails, return the deterministic score with
    hardcoded fallback text — never HTTP 500.
    """
    student = db.get(Student, DEMO_STUDENT_ID)
    if student is None:
        raise StudentNotFoundError()

    # --- deterministic scoring ---
    component_scores = _compute_component_scores(db, student)
    overall_score = sum(
        component_scores[k] * _WEIGHTS[k] for k in _WEIGHTS
    )
    # Clamp to [0.0, 1.0]
    overall_score = max(0.0, min(1.0, overall_score))
    score_label = f"{round(overall_score * 100)}%"
    biggest_gap = min(component_scores, key=component_scores.get)  # type: ignore[arg-type]

    # --- AI analysis (with fallback) ---
    ai_result = _call_ai(db, student, component_scores, biggest_gap)

    return JobReadiness(
        overall_score=overall_score,
        score_label=score_label,
        component_scores=component_scores,
        biggest_gap=biggest_gap,
        gap_explanation=ai_result.get("gap_explanation", _FALLBACK_GAP_EXPLANATION),
        next_best_action=ai_result.get("next_best_action", _fallback_nba(biggest_gap)),
        recommendations=ai_result.get("recommendations", []),
        disclaimer=DISCLAIMER_TEXT,
    )


# ---------------------------------------------------------------------------
# Deterministic scoring (architecture §6.3)
# ---------------------------------------------------------------------------


def _compute_component_scores(db: Session, student: Student) -> dict[str, float]:
    """Compute all 5 component scores from DB data."""
    return {
        "skills": _score_skills(db, student),
        "projects": _score_projects(db, student),
        "internship": _score_internship(db, student),
        "cv": _score_cv(db, student),
        "interview": _score_interview(db, student),
    }


def _score_skills(db: Session, student: Student) -> float:
    """
    Skills (30%):
    - Source: student_profiles.skills (JSON array of {name, level})
    - 0 skills -> 0.0
    - 1-2 skills, all beginner -> 0.25
    - 3+ skills or any intermediate -> 0.5
    - 5+ skills with at least 1 intermediate/advanced -> 0.75
    - 7+ skills with 2+ intermediate/advanced -> 1.0
    """
    profile = (
        db.query(StudentProfile)
        .filter(StudentProfile.student_id == student.id)
        .first()
    )
    if not profile or not profile.skills:
        return 0.0

    skills = _safe_json_load(profile, "skills")
    if not isinstance(skills, list):
        return 0.0

    count = len(skills)
    if count == 0:
        return 0.0

    levels = [s.get("level", "beginner").lower() for s in skills if isinstance(s, dict)]
    has_intermediate = any(lv in ("intermediate", "advanced") for lv in levels)
    intermediate_count = sum(1 for lv in levels if lv in ("intermediate", "advanced"))

    if count >= 7 and intermediate_count >= 2:
        base = 1.0
    elif count >= 5 and intermediate_count >= 1:
        base = 0.75
    elif count >= 3 or has_intermediate:
        base = 0.5
    elif count >= 1:
        base = 0.25
    else:
        base = 0.0

    return base


def _score_projects(db: Session, student: Student) -> float:
    """
    Projects (20%):
    - Count milestones with stage=PROJECTS and status=done.
    - 0 done -> 0.0, 1 done -> 0.4, 2 done -> 0.7, 3+ done -> 1.0
    """
    done_count = _count_done_milestones_by_stage(db, student.id, "PROJECTS")
    if done_count >= 3:
        return 1.0
    if done_count == 2:
        return 0.7
    if done_count == 1:
        return 0.4
    return 0.0


def _score_internship(db: Session, student: Student) -> float:
    """
    Internship (20%):
    - Any milestone with stage=INTERNSHIP and status=done.
    - None done -> 0.0, at least one -> 1.0
    """
    done_count = _count_done_milestones_by_stage(db, student.id, "INTERNSHIP")
    return 1.0 if done_count >= 1 else 0.0


def _score_cv(db: Session, student: Student) -> float:
    """
    CV (15%):
    - Milestones with title containing 'CV', 'resume', 'portfolio'
      (case-insensitive) and status=done.
    - None -> 0.0, One -> 0.75, Two+ -> 1.0
    """
    done_count = _count_done_milestones_by_title_pattern(
        db, student.id, ["cv", "resume", "portfolio"]
    )
    if done_count >= 2:
        return 1.0
    if done_count == 1:
        return 0.75
    return 0.0


def _score_interview(db: Session, student: Student) -> float:
    """
    Interview (15%):
    - Milestones with title containing 'interview', 'mock'
      (case-insensitive) and status=done.
    - 0 -> 0.0, 1 -> 0.33, 2 -> 0.67, 3+ -> 1.0
    """
    done_count = _count_done_milestones_by_title_pattern(
        db, student.id, ["interview", "mock"]
    )
    if done_count >= 3:
        return 1.0
    if done_count == 2:
        return 0.67
    if done_count == 1:
        return 0.33
    return 0.0


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------


def _count_done_milestones_by_stage(
    db: Session, student_id: int, stage: str
) -> int:
    """Count done milestones for a given stage across all student roadmaps."""
    roadmap_ids = [
        r.id for r in
        db.query(Roadmap.id).filter(Roadmap.student_id == student_id).all()
    ]
    if not roadmap_ids:
        return 0
    return (
        db.query(Milestone)
        .filter(
            Milestone.roadmap_id.in_(roadmap_ids),
            Milestone.stage == stage,
            Milestone.status == "done",
        )
        .count()
    )


def _count_done_milestones_by_title_pattern(
    db: Session, student_id: int, patterns: list[str]
) -> int:
    """Count done milestones whose title contains any of the given patterns."""
    roadmap_ids = [
        r.id for r in
        db.query(Roadmap.id).filter(Roadmap.student_id == student_id).all()
    ]
    if not roadmap_ids:
        return 0
    query = db.query(Milestone).filter(
        Milestone.roadmap_id.in_(roadmap_ids),
        Milestone.status == "done",
    )
    # Build OR filter for title patterns
    from sqlalchemy import or_
    title_filters = [
        Milestone.title.ilike(f"%{p}%") for p in patterns
    ]
    query = query.filter(or_(*title_filters))
    return query.count()


# ---------------------------------------------------------------------------
# AI analysis (architecture §6.4)
# ---------------------------------------------------------------------------


def _call_ai(
    db: Session,
    student: Student,
    component_scores: dict[str, float],
    biggest_gap: str,
) -> dict:
    """
    Call Qwen for gap analysis. On ANY failure, return hardcoded fallback.
    Never raises — job readiness always returns HTTP 200.
    """
    try:
        ai = get_ai_service()

        student_json = json.dumps(
            {
                "education_stage": student.education_stage,
                "career_goal": student.career_goal,
                "skills": _get_student_skills(db, student),
            },
            ensure_ascii=False,
        )
        scores_json = json.dumps(component_scores, ensure_ascii=False)

        system_prompt = build_job_readiness_system_prompt(
            student_profile_json=student_json,
            component_scores_json=scores_json,
            biggest_gap=biggest_gap,
        )

        user_prompt = (
            f"Analyze the student's biggest gap ({biggest_gap}) and provide "
            "actionable advice. Return JSON matching JobReadinessAIAnalysis exactly."
        )

        result = ai.call_structured(
            prompt=user_prompt,
            response_model=JobReadinessAIAnalysis,
            system_prompt=system_prompt,
            operation="job_readiness_analysis",
        )

        # Trim recommendations to max 3
        recommendations = result.recommendations[:3]

        return {
            "gap_explanation": result.gap_explanation,
            "next_best_action": result.next_best_action,
            "recommendations": recommendations,
        }

    except AIServiceError as exc:
        logger.warning("Job readiness AI call failed: %s", type(exc).__name__)
        return {
            "gap_explanation": _FALLBACK_GAP_EXPLANATION,
            "next_best_action": _fallback_nba(biggest_gap),
            "recommendations": [],
        }
    except Exception as exc:
        # Catch-all: never let job readiness return 500
        logger.error("Job readiness unexpected error: %s", type(exc).__name__)
        return {
            "gap_explanation": _FALLBACK_GAP_EXPLANATION,
            "next_best_action": _fallback_nba(biggest_gap),
            "recommendations": [],
        }


def _get_student_skills(db: Session, student: Student) -> list:
    """Get student skills list for the AI prompt."""
    profile = (
        db.query(StudentProfile)
        .filter(StudentProfile.student_id == student.id)
        .first()
    )
    if profile and profile.skills:
        return _safe_json_load(profile, "skills") or []
    return []


def _fallback_nba(biggest_gap: str) -> NextBestAction:
    """Deterministic fallback NBA when Qwen is unavailable."""
    gap_titles = {
        "skills": "Build a New Skill",
        "projects": "Start a Portfolio Project",
        "internship": "Search for Internships",
        "cv": "Update Your CV",
        "interview": "Practice Interview Skills",
    }
    gap_descriptions = {
        "skills": "Focus on learning one new skill relevant to your career goal this week.",
        "projects": "Create a small project to demonstrate your abilities to future employers.",
        "internship": "Research and apply for at least one internship opportunity.",
        "cv": "Update your CV or portfolio to showcase your skills and achievements.",
        "interview": "Practice answering common interview questions with a friend or mentor.",
    }
    title = gap_titles.get(biggest_gap, "Improve Your Readiness")
    description = gap_descriptions.get(
        biggest_gap,
        "Focus on your lowest-scoring area to improve your overall job readiness.",
    )
    return NextBestAction(
        title=title,
        description=description,
        steps=[f"Identify one specific action to improve your {biggest_gap}"],
        estimated_time="1 week",
        why_this_matters=f"Your {biggest_gap} score is the lowest — improving it will boost your overall readiness.",
        stage="JOB_PREPARATION",
    )


def _safe_json_load(obj: object, attr: str) -> object:
    """Safely load a JSON string column."""
    raw = getattr(obj, attr, None)
    if raw is None:
        return None
    if isinstance(raw, (list, dict)):
        return raw
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None
