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
    parse_stage,
    VALID_TRANSITIONS,
)

logger = logging.getLogger("ah_career.journey")

# Milestone statuses a student may set through this endpoint
# (pending/active are backend-managed, never student-set).
STUDENT_SETTABLE_STATUSES = {"done", "skipped"}


class MilestoneNotFoundError(Exception):
    """Unknown milestone id — or one that belongs to another student."""


class InvalidStatusError(Exception):
    """The requested milestone status is not settable by students."""


def record_progress(
    db: Session, request: ProgressRequest, student_id: int = DEMO_STUDENT_ID
) -> ProgressResponse:
    """
    Mark a milestone completed or skipped.

    1. Validate the milestone belongs to the requested student (or find first pending if omitted).
    2. Update its status and completion time.
    3. Advance the stage through the backend state machine if appropriate.
    4. Recalculate and persist a new Next Best Action.
    """
    if request.status not in STUDENT_SETTABLE_STATUSES:
        raise InvalidStatusError(request.status)

    if request.milestone_id is not None and request.milestone_id > 0:
        milestone = _get_owned_milestone(db, request.milestone_id, student_id=student_id)
    else:
        # Caller omitted milestone_id: pick first pending milestone for this student in current stage
        student = db.get(Student, student_id)
        pending = []
        if student:
            pending = [
                m for m in roadmap_service.get_pending_milestones(db, student_id=student_id)
                if m.stage == student.education_stage
            ]
            if not pending:
                pending = roadmap_service.get_pending_milestones(db, student_id=student_id)
        if pending:
            milestone = pending[0]
        else:
            raise MilestoneNotFoundError(0)

    milestone.status = request.status
    if request.status == "done":
        milestone.completed_at = datetime.now(timezone.utc)
    db.commit()
    logger.info(
        "Progress: milestone=%s status=%s student=%s",
        milestone.id, request.status, student_id,
    )

    student = db.get(Student, student_id)
    new_stage = _advance_stage_if_ready(db, student)

    # Progress changed — the cached NBA is stale by definition; recalculate.
    nba = nba_service.generate_nba(db, student, force_refresh=True)

    return ProgressResponse(new_stage=new_stage, next_best_action=nba)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_owned_milestone(
    db: Session, milestone_id: int, student_id: int = DEMO_STUDENT_ID
) -> Milestone:
    """
    Load the milestone and verify it belongs to the student.

    Unknown ids and other students' milestones raise the same error — the
    response must not reveal that a milestone id exists for someone else.
    """
    milestone = db.get(Milestone, milestone_id)
    if milestone is None:
        raise MilestoneNotFoundError(milestone_id)
    roadmap = db.get(Roadmap, milestone.roadmap_id)
    if roadmap is None or roadmap.student_id != student_id:
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

    # If no other pending milestones exist across the student's roadmap, instantiate next valid stage
    if target is None and len(pending_stages) == 0:
        current_stage = parse_stage(current)
        if current_stage and current_stage in VALID_TRANSITIONS and VALID_TRANSITIONS[current_stage]:
            target = VALID_TRANSITIONS[current_stage][0]
            # Ensure milestones for the new target stage are instantiated
            roadmap_service.ensure_stage_milestones(db, student.id, target.value)

    if target is not None and is_valid_transition(current, target.value):
        student.education_stage = target.value
        db.commit()
        logger.info(
            "Stage transition: student=%s %s -> %s",
            student.id, current, target.value,
        )
        return target.value

    return current
