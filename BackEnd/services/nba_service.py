"""
Next Best Action engine (Phase 4).

Pipeline (Phase 4 spec §3):

    deterministic candidates (candidate_service)
      -> Qwen selects ONE candidate_id (prompts/next_best_action.py)
      -> backend validates the candidate_id against the supplied list
      -> ONE retry when the selection is invalid
      -> deterministic fallback: highest-priority valid candidate
      -> persist the selected action on the student profile
      -> return NextBestAction

Qwen can never invent an action: every field of the returned NextBestAction
except the one-sentence personalized `why_this_matters` is copied verbatim
from the deterministic candidate the backend generated. If Qwen is
unavailable or keeps returning invalid selections, the engine falls back to
the highest-priority candidate — the journey loop never dead-ends.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from models.student import Student
from prompts.next_best_action import build_nba_system_prompt, build_nba_user_prompt
from repositories.student_repo import StudentRepository
from schemas.shared import NextBestAction
from services import candidate_service, roadmap_service
from services.ai_service import AIUnavailableError, AIValidationError, get_ai_service

logger = logging.getLogger("ah_career.journey")

# The AI is allowed at most one re-selection when it returns an unknown
# candidate_id (on top of the ai_service's own single transport/JSON retry).
_MAX_SELECTION_ATTEMPTS = 2


class NBASelection(BaseModel):
    """
    Internal wrapper schema (Phase 4 spec §11): Qwen returns only the
    selected candidate_id plus a one-sentence personalized rationale.
    The public NextBestAction is assembled by the backend from the
    deterministic candidate — the candidate_id never leaks to the frontend.
    """
    candidate_id: str
    why_this_matters: str = ""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_nba(
    db: Session, student: Student, *, force_refresh: bool = False
) -> NextBestAction:
    """
    Return the student's Next Best Action.

    - Reuses the cached NBA from the student profile when it is still valid
      (same candidate pool, unchanged completed milestones) — no Qwen call.
    - Otherwise asks Qwen to select one candidate, validates the selection,
      and falls back deterministically when Qwen fails or misbehaves.
    - Always persists the selected action on the student profile.
    """
    candidates = candidate_service.generate_candidates(db, student)

    if not force_refresh:
        cached = _cached_if_valid(db, student, candidates)
        if cached is not None:
            logger.info("NBA cache hit: student=%s", student.id)
            return cached

    candidate, why = _select_candidate(db, student, candidates)
    nba = NextBestAction(
        title=candidate.title,
        description=candidate.description,
        steps=list(candidate.steps),
        estimated_time=candidate.estimated_time,
        why_this_matters=why or candidate.why_this_matters,
        stage=candidate.stage,
    )
    _persist_nba(db, student.id, nba, candidate.candidate_id)
    return nba


def get_cached_nba(db: Session, student_id: int) -> Optional[NextBestAction]:
    """The persisted NBA (or None) — used for honest fallbacks elsewhere."""
    profile = StudentRepository(db).get_profile(student_id)
    if profile is None or not profile.next_best_action:
        return None
    try:
        blob = json.loads(profile.next_best_action)
        return NextBestAction.model_validate(blob.get("action"))
    except (json.JSONDecodeError, TypeError, ValidationError):
        return None


def clear_cached_nba(db: Session, student_id: int) -> None:
    """Invalidate the persisted NBA (e.g. after the profile changed)."""
    StudentRepository(db).update_profile(student_id, next_best_action=None)


# ---------------------------------------------------------------------------
# Selection: Qwen -> validate -> retry -> deterministic fallback
# ---------------------------------------------------------------------------


def _select_candidate(db, student, candidates):
    """
    Ask Qwen to pick ONE candidate. Returns (candidate, why_this_matters).

    Never raises: AI unavailability and persistently invalid selections both
    fall back to the highest-priority candidate (candidates are sorted by
    priority in candidate_service) with its deterministic rationale.
    """
    by_id = {c.candidate_id: c for c in candidates}
    try:
        for attempt in range(1, _MAX_SELECTION_ATTEMPTS + 1):
            selection = get_ai_service().call_structured(
                prompt=build_nba_user_prompt(),
                response_model=NBASelection,
                system_prompt=_build_prompt(db, student, candidates),
                operation="next_best_action",
            )
            candidate = by_id.get(selection.candidate_id)
            if candidate is not None:
                logger.info(
                    "NBA selected by Qwen: student=%s candidate=%s attempt=%s",
                    student.id, candidate.candidate_id, attempt,
                )
                return candidate, selection.why_this_matters
            logger.warning(
                "Qwen returned unknown candidate_id '%s' (attempt %s/%s)",
                selection.candidate_id, attempt, _MAX_SELECTION_ATTEMPTS,
            )
    except AIUnavailableError:
        logger.warning("NBA: AI unavailable — using deterministic fallback")
    except AIValidationError:
        logger.warning("NBA: AI output invalid — using deterministic fallback")

    fallback = candidates[0]
    logger.info(
        "NBA deterministic fallback: student=%s candidate=%s",
        student.id, fallback.candidate_id,
    )
    return fallback, fallback.why_this_matters


def _build_prompt(db: Session, student: Student, candidates) -> str:
    profile = StudentRepository(db).get_profile(student.id)
    student_context = {
        "student_id": student.id,
        "name": student.name,
        "education_stage": student.education_stage,
        "career_goal": student.career_goal,
        "sports_interest": student.sports_interest,
        "motivation_tags": _loads(student.motivation_tags),
        "interests": _loads(profile.interests) if profile else [],
        "skills": _loads(profile.skills) if profile else [],
    }
    journey_state = candidate_service.candidate_context(db, student)
    return build_nba_system_prompt(
        student_profile_json=json.dumps(student_context, ensure_ascii=False),
        journey_state_json=json.dumps(journey_state, ensure_ascii=False),
        candidates_json=json.dumps(
            [c.model_dump() for c in candidates], ensure_ascii=False
        ),
    )


# ---------------------------------------------------------------------------
# Persistence (architecture §7: student_profiles.next_best_action JSON blob)
# ---------------------------------------------------------------------------


def _persist_nba(
    db: Session, student_id: int, nba: NextBestAction, candidate_id: str
) -> None:
    """Store the selected NBA so the journey remembers what was told."""
    blob = {
        "candidate_id": candidate_id,
        "action": nba.model_dump(),
        "completed_milestone_titles": sorted(
            roadmap_service.get_completed_titles(db, student_id)
        ),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    StudentRepository(db).update_profile(
        student_id, next_best_action=json.dumps(blob, ensure_ascii=False)
    )


def _cached_if_valid(db, student, candidates) -> Optional[NextBestAction]:
    """
    The cached NBA is valid when:
    - its candidate_id is still in the current deterministic candidate pool,
    - the student's completed milestones have not changed since generation.

    Both checks are database-only — no Qwen calls on dashboard refreshes.
    """
    profile = StudentRepository(db).get_profile(student.id)
    if profile is None or not profile.next_best_action:
        return None
    try:
        blob = json.loads(profile.next_best_action)
    except (json.JSONDecodeError, TypeError):
        return None

    candidate_ids = {c.candidate_id for c in candidates}
    if blob.get("candidate_id") not in candidate_ids:
        return None

    completed_now = sorted(roadmap_service.get_completed_titles(db, student.id))
    if blob.get("completed_milestone_titles") != completed_now:
        return None

    try:
        return NextBestAction.model_validate(blob.get("action"))
    except ValidationError:
        return None


def _loads(raw: Optional[str]) -> list:
    """Parse a JSON TEXT column; empty list when missing or malformed."""
    if raw is None:
        return []
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return []
