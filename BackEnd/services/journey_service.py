"""
Journey service (Phase 4).

GET /api/v1/journey: the student's current stage, current step, and at most
3 visible next steps (progressive disclosure is mandatory — the hidden
roadmap never reaches the frontend), plus the Next Best Action.

The Next Best Action comes from the profile cache whenever it is still
valid (Phase 4 spec §15) — no Qwen call on dashboard refreshes.
"""

from datetime import datetime, timezone
import logging
from typing import Optional

from sqlalchemy.orm import Session

from models.roadmap import Milestone, Roadmap
from models.student import Student
from schemas.responses import JourneyResponse, JourneyStep, MilestoneItem
from services import nba_service, roadmap_service
from services.journey_state import DEMO_STUDENT_ID, STAGE_ORDER, parse_stage
from services.progress_service import _advance_stage_if_ready
from schemas.shared import EducationStage

logger = logging.getLogger("ah_career.journey")


class StudentNotFoundError(Exception):
    """No onboarded student found."""


class MilestoneNotFoundError(Exception):
    """Milestone not found."""


class MilestoneAlreadyCompletedError(Exception):
    """Milestone is already completed."""


class MilestoneForbiddenError(Exception):
    """Milestone does not belong to the student's journey."""


def get_journey(db: Session, student_id: int = DEMO_STUDENT_ID) -> JourneyResponse:
    """
    Assemble the journey view for the requested student.
    Returns the enriched schema with full milestone list, statuses ('completed', 'active', 'locked'),
    completed_count, total_count, and backward-compatible fields.
    """
    student = db.get(Student, student_id)
    if student is None:
        raise StudentNotFoundError()

    stage = parse_stage(student.education_stage) or EducationStage.HIGH_SCHOOL
    stage_rank = {s.value: idx for idx, s in enumerate(STAGE_ORDER)}

    all_milestones = roadmap_service.get_student_milestones(db, student.id)
    if not all_milestones:
        roadmap_service.ensure_stage_milestones(db, student.id, stage.value)
        all_milestones = roadmap_service.get_student_milestones(db, student.id)

    # Ensure the first incomplete milestone has 'active' status if none is active
    has_active = any(m.status == "active" for m in all_milestones)
    first_incomplete = next((m for m in all_milestones if m.status not in ("completed", "done")), None)

    if not has_active and first_incomplete is not None:
        first_incomplete.status = "active"
        try:
            db.commit()
        except Exception:
            db.rollback()

    milestone_items: list[MilestoneItem] = []
    completed_count = 0
    current_milestone_id: Optional[int] = None

    for idx, m in enumerate(all_milestones):
        status: str
        if m.status in ("completed", "done"):
            status = "completed"
            completed_count += 1
        elif m.status == "active":
            status = "active"
            current_milestone_id = m.id
        else:
            status = "locked"

        phase_num = stage_rank.get(m.stage, 0) + 1
        milestone_items.append(
            MilestoneItem(
                id=m.id,
                title=m.title,
                description=m.description or "",
                status=status,
                phase=phase_num,
                order=idx + 1,
            )
        )

    # If first_incomplete exists but wasn't active yet, assign it
    if current_milestone_id is None and first_incomplete is not None:
        current_milestone_id = first_incomplete.id

    pending = roadmap_service.get_pending_milestones(db, student.id)
    if pending:
        current_step = pending[0].title
        next_steps = [
            roadmap_service.to_journey_step(m)
            for m in pending[: roadmap_service.MAX_VISIBLE_STEPS]
        ]
    else:
        current_step = roadmap_service.stage_default_step_title(stage.value)
        next_steps = roadmap_service.stage_default_steps(stage.value)

    nba = nba_service.generate_nba(db, student)

    return JourneyResponse(
        milestones=milestone_items,
        current_milestone_id=current_milestone_id,
        completed_count=completed_count,
        total_count=len(milestone_items),
        stage=stage,
        current_step=current_step,
        next_steps=next_steps,
        next_best_action=nba,
    )


def complete_student_milestone(
    db: Session,
    student_id: int,
    milestone_id: int,
) -> JourneyResponse:
    """
    Mark a milestone completed for a student:
    1. Validate student exists (404).
    2. Validate milestone belongs to student's journey (403).
    3. Validate milestone is not already completed (400 'already_completed').
    4. Mark milestone as completed (persist to DB).
    5. db.commit().
    6. Calculate next eligible milestone in order.
    7. Mark next milestone as active (persist to DB).
    8. db.commit().
    9. Re-fetch full journey state and return it.
    """
    student = db.get(Student, student_id)
    if student is None:
        raise StudentNotFoundError()

    milestone = db.get(Milestone, milestone_id)
    if milestone is None:
        raise MilestoneNotFoundError(milestone_id)

    roadmap = db.get(Roadmap, milestone.roadmap_id)
    if roadmap is None or roadmap.student_id != student.id:
        raise MilestoneForbiddenError()

    if milestone.status in ("completed", "done"):
        raise MilestoneAlreadyCompletedError()

    try:
        # Step 4 & 5: Mark completed and commit
        milestone.status = "completed"
        milestone.completed_at = datetime.now(timezone.utc)
        db.commit()

        # Step 6 & 7: Calculate next eligible milestone and mark active
        all_milestones = roadmap_service.get_student_milestones(db, student.id)
        next_milestone = None
        for m in all_milestones:
            if m.id != milestone.id and m.status in ("locked", "pending"):
                next_milestone = m
                break

        # If no locked/pending left in current stage milestones, check stage advancement
        if next_milestone is None:
            new_stage = _advance_stage_if_ready(db, student)
            if new_stage != student.education_stage:
                all_milestones = roadmap_service.get_student_milestones(db, student.id)
                for m in all_milestones:
                    if m.status in ("locked", "pending"):
                        next_milestone = m
                        break

        if next_milestone is not None:
            next_milestone.status = "active"
            db.commit()

        # Update NBA cache
        nba_service.generate_nba(db, student, force_refresh=True)

        return get_journey(db, student_id=student.id)
    except Exception:
        db.rollback()
        raise


def get_current_student(db: Session, student_id: int = DEMO_STUDENT_ID) -> Optional[Student]:
    """The active student (defaults to demo student)."""
    return db.get(Student, student_id)


