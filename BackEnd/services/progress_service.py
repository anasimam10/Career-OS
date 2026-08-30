"""
Progress service (Phase 4).

POST /api/v1/progress: mark a milestone done/skipped, advance the journey
stage when (and only when) the backend state machine allows it, and
recalculate the Next Best Action.

Stage advancement is pure backend logic (Phase 4 spec §17): Qwen never
decides stages. The rule: when the current stage has no pending milestones
left and a VALID transition leads to a stage that still has pending
milestones, the student advances to that stage — otherwise they stay.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from models.roadmap import Milestone, Roadmap
from models.student import Student
from schemas.requests import ProgressRequest
from schemas.responses import ProgressResponse
from services import nba_service, roadmap_service
from services.journey_state import (
    DEMO_STUDENT_ID,
    is_valid_transition,
    next_stage_with_pending,
)

logger = logging.getLogger("ah_career.journey")

# Milestone statuses a student may set through this endpoint
# (pending/active are backend-managed, never student-set).
STUDENT_SETTABLE_STATUSES = {"done", "skipped"}


class MilestoneNotFoundError(Exception):
    """Unknown milestone id — or one that belongs to another student."""


class InvalidStatusError(Exception):
    """The requested milestone status is not settable by students."""


def record_progress(db: Session, request: ProgressRequest) -> ProgressResponse:
    """
    1. Validate the milestone (exists + belongs to the demo student).
    2. Update its status and completion time.
    3. Advance the stage through the backend state machine if appropriate.
    4. Recalculate and persist a new Next Best Action.

    Raises:
        MilestoneNotFoundError, InvalidStatusError.
    """
    if request.status not in STUDENT_SETTABLE_STATUSES:
        raise InvalidStatusError(request.status)

    milestone = _get_owned_milestone(db, request.milestone_id)

    milestone.status = request.status
    if request.status == "done":
        milestone.completed_at = datetime.now(timezone.utc)
    db.commit()
    logger.info(
        "Progress: milestone=%s status=%s student=%s",
        milestone.id, request.status, DEMO_STUDENT_ID,
    )

    student = db.get(Student, DEMO_STUDENT_ID)
    new_stage = _advance_stage_if_ready(db, student)

    # Progress changed — the cached NBA is stale by definition; recalculate.
    nba = nba_service.generate_nba(db, student, force_refresh=True)

    return ProgressResponse(new_stage=new_stage, next_best_action=nba)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_owned_milestone(db: Session, milestone_id: int) -> Milestone:
    """
    Load the milestone and verify it belongs to the demo student.

    Unknown ids and other students' milestones raise the same error — the
    response must not reveal that a milestone id exists for someone else.
    """
    milestone = db.get(Milestone, milestone_id)
    if milestone is None:
        raise MilestoneNotFoundError(milestone_id)
    roadmap = db.get(Roadmap, milestone.roadmap_id)
    if roadmap is None or roadmap.student_id != DEMO_STUDENT_ID:
        raise MilestoneNotFoundError(milestone_id)
    return milestone


def _advance_stage_if_ready(db: Session, student: Student) -> str:
    """
    Backend-validated stage transition (never the AI's decision).

    Advance only when BOTH hold:
    - the current stage has no pending milestones left, and
    - a valid forward transition leads to a stage with pending milestones.

    Returns the (possibly advanced) stage value.
    """
    current = student.education_stage
    pending = roadmap_service.get_pending_milestones(db, student.id)

    if any(m.stage == current for m in pending):
        return current  # work remains in the current stage

    pending_stages = {m.stage for m in pending if m.stage != current}
    target = next_stage_with_pending(current, pending_stages)
    if target is not None and is_valid_transition(current, target.value):
        student.education_stage = target.value
        db.commit()
        logger.info(
            "Stage transition: student=%s %s -> %s",
            student.id, current, target.value,
        )
        return target.value

    return current
