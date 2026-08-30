"""
Coach Chat service (Phase 8).

POST /api/v1/coach/chat — context-aware AI mentor conversation.

Data flow:
    rate_limit_check(student_id)
      -> build_context(student_id, message, history)
      -> build_prompt(context)
      -> ai_service.call_structured(prompt, CoachResponse)
      -> trim quick_actions to max 3
      -> validate suggested_resource against DB
      -> return CoachResponse
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from sqlalchemy.orm import Session

from models.career import Career
from models.roadmap import Roadmap, Milestone
from models.student import Student, StudentProfile
from prompts.coach import build_coach_system_prompt, build_coach_user_prompt
from schemas.shared import CoachResponse
from services.ai_service import get_ai_service
from services.journey_state import DEMO_STUDENT_ID

logger = logging.getLogger("ah_career.coach")

# Coach constraints (architecture §5)
_MAX_HISTORY_MESSAGES = 5
_MAX_TOTAL_CHARS = 2000
_MAX_QUICK_ACTIONS = 3


class StudentNotFoundError(Exception):
    """No onboarded student found."""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def coach_chat(
    db: Session,
    message: str,
    history: list[dict],
) -> CoachResponse:
    """
    Build context, call Qwen, validate and return CoachResponse.

    ``history`` is a list of {role, content} dicts from the frontend.
    The service trims to the most recent 5 messages before the current one,
    then enforces the 2000-character combined limit.
    """
    # --- fetch student ---
    student = db.get(Student, DEMO_STUDENT_ID)
    if student is None:
        raise StudentNotFoundError()

    # --- build context from DB ---
    context = _build_student_context(db, student)

    # --- trim history ---
    trimmed = _trim_history(history)

    # --- build prompts ---
    student_json = json.dumps(
        {
            "education_stage": student.education_stage,
            "career_goal": student.career_goal,
            "interests": _safe_json_load(student, "interests"),
            "skills": _safe_json_load(student, "skills"),
        },
        ensure_ascii=False,
    )
    context_json = json.dumps(context, ensure_ascii=False, default=str)

    system_prompt = build_coach_system_prompt(student_json, context_json)

    history_text = "\n".join(
        f"{m['role']}: {m['content']}" for m in trimmed
    )
    user_prompt = build_coach_user_prompt(history_text, message)

    # --- call Qwen ---
    ai = get_ai_service()
    response = ai.call_structured(
        prompt=user_prompt,
        response_model=CoachResponse,
        system_prompt=system_prompt,
        operation="coach_chat",
    )

    # --- post-validation ---
    result = _post_validate(db, response)
    return result


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


def _build_student_context(db: Session, student: Student) -> dict:
    """Fetch all relevant DB data for the coach prompt."""
    context: dict = {}

    # Profile data
    profile = (
        db.query(StudentProfile)
        .filter(StudentProfile.student_id == student.id)
        .first()
    )
    if profile:
        context["interests"] = _safe_json_load(profile, "interests")
        context["skills"] = _safe_json_load(profile, "skills")
        if profile.next_best_action:
            try:
                context["next_best_action"] = json.loads(profile.next_best_action)
            except (json.JSONDecodeError, TypeError):
                pass

    # Active roadmap
    roadmap = (
        db.query(Roadmap)
        .filter(Roadmap.student_id == student.id)
        .order_by(Roadmap.created_at.desc())
        .first()
    )
    if roadmap:
        context["roadmap_stage"] = roadmap.current_stage
        context["roadmap_step"] = roadmap.current_step_title
        active_milestones = (
            db.query(Milestone)
            .filter(
                Milestone.roadmap_id == roadmap.id,
                Milestone.status.in_(["active", "pending"]),
            )
            .order_by(Milestone.order_index)
            .limit(3)
            .all()
        )
        context["active_milestones"] = [
            {"title": m.title, "status": m.status} for m in active_milestones
        ]

    # Career goal data
    if student.career_goal:
        career = (
            db.query(Career)
            .filter(Career.slug == student.career_goal)
            .first()
        )
        if career:
            context["career_info"] = {
                "name": career.name,
                "demand_level": career.demand_level,
                "required_skills": _safe_json_load(career, "required_skills"),
                "pk_opportunities": _safe_json_load(career, "pk_opportunities"),
            }

    # Opportunity matches (only if they exist)
    from models.opportunity import StudentOpportunityMatch  # local import to avoid cycle

    match_count = (
        db.query(StudentOpportunityMatch)
        .filter(StudentOpportunityMatch.student_id == student.id)
        .count()
    )
    if match_count > 0:
        context["has_opportunity_matches"] = True
        context["opportunity_match_count"] = match_count

    return context


def _trim_history(history: list[dict]) -> list[dict]:
    """
    Keep at most 5 recent messages, then enforce 2000-char combined limit.
    The current message is NOT in ``history`` (the frontend sends it separately).
    """
    if not history:
        return []

    # Keep the 5 most recent
    trimmed = history[-_MAX_HISTORY_MESSAGES:]

    # Enforce character budget
    total = sum(len(m.get("content", "")) for m in trimmed)
    while total > _MAX_TOTAL_CHARS and len(trimmed) > 1:
        removed = trimmed.pop(0)
        total -= len(removed.get("content", ""))

    return trimmed


def _post_validate(db: Session, response: CoachResponse) -> CoachResponse:
    """Enforce backend constraints the LLM cannot be trusted to follow."""
    # Trim quick_actions to max 3
    quick_actions = response.quick_actions[:_MAX_QUICK_ACTIONS]

    # Validate suggested_resource against DB
    suggested = response.suggested_resource
    if suggested:
        suggested = _validate_resource(db, suggested)

    return CoachResponse(
        message=response.message,
        quick_actions=quick_actions,
        suggested_resource=suggested,
    )


def _validate_resource(db: Session, resource: str) -> Optional[str]:
    """
    Check whether the suggested_resource matches a known DB entity.
    Returns the resource string if valid, None otherwise.
    """
    resource_lower = resource.strip().lower()

    # Check careers
    careers = db.query(Career).all()
    for c in careers:
        if c.name.lower() == resource_lower or c.slug.lower() == resource_lower:
            return resource

    # Check opportunities
    from models.opportunity import Opportunity  # local import

    opportunities = db.query(Opportunity).all()
    for o in opportunities:
        if o.title and o.title.lower() == resource_lower:
            return resource

    # Not found in DB — reject the fabricated resource
    logger.info("Coach suggested_resource not found in DB, set to None: %s", resource[:100])
    return None


def _safe_json_load(obj: object, attr: str) -> object:
    """Safely load a JSON string column; return None on failure."""
    raw = getattr(obj, attr, None)
    if raw is None:
        return None
    if isinstance(raw, (list, dict)):
        return raw
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None
