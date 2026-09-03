"""
Journey service (Phase 4).

GET /api/v1/journey: the student's current stage, current step, and at most
3 visible next steps (progressive disclosure is mandatory — the hidden
roadmap never reaches the frontend), plus the Next Best Action.

The Next Best Action comes from the profile cache whenever it is still
valid (Phase 4 spec §15) — no Qwen call on dashboard refreshes.
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from models.student import Student
from schemas.responses import JourneyResponse, JourneyStep
from services import nba_service, roadmap_service
from services.journey_state import DEMO_STUDENT_ID, parse_stage
from schemas.shared import EducationStage

logger = logging.getLogger("ah_career.journey")


class StudentNotFoundError(Exception):
    """No onboarded demo student — the journey cannot exist yet."""


def get_journey(db: Session, student_id: int = DEMO_STUDENT_ID) -> JourneyResponse:
    """
    Assemble the journey view for the requested student (defaults to demo student).

    Raises:
        StudentNotFoundError — nobody has onboarded yet.
    """
    student = db.get(Student, student_id)
    if student is None:
        raise StudentNotFoundError()

    stage = parse_stage(student.education_stage) or EducationStage.HIGH_SCHOOL

    pending = roadmap_service.get_pending_milestones(db, student.id)
    current_milestone_id = None
    if pending:
        current_step = pending[0].title
        current_milestone_id = pending[0].id
        next_steps: list[JourneyStep] = [
            roadmap_service.to_journey_step(m)
            for m in pending[: roadmap_service.MAX_VISIBLE_STEPS]
        ]
    else:
        # No roadmap milestones yet — honest deterministic defaults for the stage
        current_step = roadmap_service.stage_default_step_title(stage.value)
        next_steps = roadmap_service.stage_default_steps(stage.value)
        if next_steps and next_steps[0].id:
            current_milestone_id = next_steps[0].id

    # Cached when still valid (no Qwen call on refresh), otherwise generated.
    nba = nba_service.generate_nba(db, student)

    return JourneyResponse(
        stage=stage,
        current_step=current_step,
        current_milestone_id=current_milestone_id,
        next_steps=next_steps,
        next_best_action=nba,
    )


def get_current_student(db: Session, student_id: int = DEMO_STUDENT_ID) -> Optional[Student]:
    """The active student (defaults to demo student)."""
    return db.get(Student, student_id)

