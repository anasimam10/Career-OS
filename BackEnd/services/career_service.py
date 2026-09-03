"""
Career Intelligence service (Phase 3).

Owns:
- career list / detail retrieval from the database (no AI),
- the Career Reality Check (POST /career/analyze) via Qwen,
- the 7-day trial plan generation (POST /career/trial-plan) via Qwen.

Trust hierarchy (architecture §4) is ENFORCED IN CODE here, not just in the
prompt: after Qwen's output passes Pydantic validation, every factual field
of CareerReality is overwritten with the database value, and the trial plan's
career_slug / duration_days are pinned to the request contract.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from sqlalchemy.orm import Session

from models.student import Student
from prompts.career_analysis import (
    build_career_analysis_system_prompt,
    build_career_analysis_user_prompt,
)
from prompts.trial_plan import (
    build_trial_plan_system_prompt,
    build_trial_plan_user_prompt,
)
from repositories.career_repo import CareerRepository
from repositories.student_repo import StudentRepository
from retrieval import career_retrieval
from schemas.responses import CareerDetail, CareerListItem
from schemas.shared import CareerRealityResponse, CareerTrialPlan
from services.ai_service import get_ai_service

logger = logging.getLogger("ah_career.career")

# The MVP uses the demo-student session context (architecture §8/§12).
# This ID matches Frontend/lib/session.ts (DEMO_STUDENT_ID = 1).
DEMO_STUDENT_ID = 1

# Honest label for the current seed records — they are template data
# converted from the frontend mock, NOT independently verified Pakistani data.
# Update this label when verified seed data lands (data phase).
CAREER_DATA_SOURCE_LABEL = "Career OS template seed data (not independently verified)"

# MVP contract: trial plans always cover exactly 7 days.
TRIAL_DURATION_DAYS = 7

# Honest value for metric fields the database does not have yet
# (sparse template careers have no competition/difficulty levels).
UNKNOWN_METRIC = "UNKNOWN"


class CareerNotFoundError(Exception):
    """The requested career_slug does not exist in the database."""


# ---------------------------------------------------------------------------
# Database-only operations (NO AI)
# ---------------------------------------------------------------------------


def get_career_list(
    db: Session,
    *,
    search: str = "",
    field: Optional[str] = None,
) -> list[CareerListItem]:
    """All active careers for the Career Explorer UI.

    Optional ``search`` (FTS5 over name/field/category, LIKE fallback) and
    ``field`` filters narrow the list (master §17). Both params are
    additive: when neither is given the legacy unfiltered listing —
    unchanged for the existing frontend — is returned.
    """
    repo = CareerRepository(db)
    search_clean = (search or "").strip()
    field_clean = (field or "").strip()
    if not search_clean and not field_clean:
        # Legacy listing path: computed fresh exactly as before (uncached).
        return [
            CareerListItem(
                slug=career.slug,
                name=career.name,
                field=career.field,
                demand_level=career.demand_level,
            )
            for career in repo.get_all_careers()
        ]
    # Filtered search path: retrieval layer returns cached plain dicts.
    careers = career_retrieval.search_careers(
        db, query=search_clean, field=field_clean or None, limit=50
    )
    return [
        CareerListItem(
            slug=career["slug"],
            name=career["name"],
            field=career["field"],
            demand_level=career["demand_level"],
        )
        for career in careers
    ]


def get_career_detail(db: Session, slug: str) -> Optional[CareerDetail]:
    """Full career record by slug, or None when the slug is unknown."""
    repo = CareerRepository(db)
    career = repo.get_by_slug(slug)
    if career is None:
        return None
    return CareerDetail(**repo.to_dict(career))


# ---------------------------------------------------------------------------
# AI operations
# ---------------------------------------------------------------------------


def analyze_career(
    db: Session, career_slug: str, student_id: int = DEMO_STUDENT_ID
) -> CareerRealityResponse:

    """
    Career reality check: student profile + database career data -> Qwen ->
    validated CareerRealityResponse.

    Raises:
        CareerNotFoundError -- career_slug not in the database.
        AIValidationError / AIUnavailableError -- propagated from ai_service.
    """
    repo = CareerRepository(db)
    career = repo.get_by_slug(career_slug)
    if career is None:
        raise CareerNotFoundError(career_slug)

    career_data = repo.to_dict(career)
    student_context = _get_student_context(db, student_id=student_id)

    system_prompt = build_career_analysis_system_prompt(
        student_profile_json=json.dumps(student_context, ensure_ascii=False),
        career_data_json=json.dumps(career_data, ensure_ascii=False),
    )

    logger.info("Career analysis: slug=%s (student=%s)", career_slug, student_id)
    result = get_ai_service().call_structured(
        prompt=build_career_analysis_user_prompt(),
        response_model=CareerRealityResponse,
        system_prompt=system_prompt,
        operation="career_analyze",
    )

    # ---- enforce the trust hierarchy in code (architecture §4) ----------
    # Priority 1 (SQLite) always wins over Priority 3 (AI interpretation)
    # for the factual fields. Qwen only contributes rewards + the verdict.
    result.reality.career_name = career_data["name"]
    result.reality.demand_level = _metric(career_data["demand_level"])
    result.reality.competition_level = _metric(career_data["competition_level"])
    result.reality.difficulty_level = _metric(career_data["difficulty_level"])
    result.reality.required_skills = career_data["required_skills"]
    result.reality.pk_opportunities = career_data["pk_opportunities"]
    result.reality.risks = career_data["risks"]
    result.reality.data_source = _data_source(career_data)
    return result


def generate_trial_plan(
    db: Session, career_slug: str, student_id: int = DEMO_STUDENT_ID
) -> CareerTrialPlan:
    """
    7-day trial plan: student profile + database career data -> Qwen ->
    validated CareerTrialPlan.

    Raises:
        CareerNotFoundError -- career_slug not in the database.
        AIValidationError / AIUnavailableError -- propagated from ai_service.
    """
    repo = CareerRepository(db)
    career = repo.get_by_slug(career_slug)
    if career is None:
        raise CareerNotFoundError(career_slug)

    career_data = repo.to_dict(career)
    student_context = _get_student_context(db, student_id=student_id)

    system_prompt = build_trial_plan_system_prompt(
        student_profile_json=json.dumps(student_context, ensure_ascii=False),
        career_data_json=json.dumps(career_data, ensure_ascii=False),
    )

    logger.info("Trial plan: slug=%s (student=%s)", career_slug, student_id)
    plan = get_ai_service().call_structured(
        prompt=build_trial_plan_user_prompt(),
        response_model=CareerTrialPlan,
        system_prompt=system_prompt,
        operation="career_trial_plan",
    )

    # ---- enforce the MVP contract in code -------------------------------
    plan.career_slug = career_slug
    plan.duration_days = TRIAL_DURATION_DAYS
    return plan


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_student_context(db: Session, student_id: int = DEMO_STUDENT_ID) -> dict:
    """
    Build the active student's context for AI prompts.

    When the student has not been onboarded yet, a minimal honest context
    is returned instead — the AI is told the profile is unavailable rather
    than receiving invented data.
    """
    student = db.get(Student, student_id)
    if student is None:
        return {
            "student_id": student_id,
            "note": "student profile not yet onboarded",
        }

    context: dict = {
        "student_id": student.id,
        "name": student.name,
        "education_stage": student.education_stage,
        "career_goal": student.career_goal,
        "sports_interest": student.sports_interest,
        "motivation_tags": _loads(student.motivation_tags),
    }

    profile = StudentRepository(db).get_profile(student_id)
    if profile is not None:
        context["interests"] = _loads(profile.interests)
        context["skills"] = _loads(profile.skills)
    return context



def _metric(value: Optional[str]) -> str:
    """Database metric value, or an honest UNKNOWN when not seeded yet."""
    return value if value else UNKNOWN_METRIC


def _data_source(career_data: dict) -> str:
    """data_source built from the record's real metadata — never invented."""
    updated = career_data.get("last_updated")
    if updated:
        return f"{CAREER_DATA_SOURCE_LABEL}, last updated {updated[:10]}"
    return CAREER_DATA_SOURCE_LABEL


def _loads(raw: Optional[str]) -> list:
    """Parse a JSON TEXT column; empty list when missing or malformed."""
    if raw is None:
        return []
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return []
