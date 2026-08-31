"""Student retrieval (architecture_master §14).

Deterministic student-context lookups for services assembling AI
context. Per master §15, student profiles are NEVER cached — always
read fresh from the database. Results are plain dicts bounded to what
the AI context budgets allow (§14 token budgets).
"""

from __future__ import annotations

import json
from typing import Optional

from sqlalchemy.orm import Session

from models.roadmap import Milestone, Roadmap
from models.student import Student, StudentProfile


def get_student_context(db: Session, student_id: int) -> Optional[dict]:
    """The full AI context for one student (None when the student is missing).

    Includes the base profile fields, interests/skills, education stage,
    and the current roadmap stage — everything the Career Reality Check,
    NBA, and coach prompts need, and nothing else.
    """
    student = db.get(Student, student_id)
    if student is None:
        return None

    context: dict = {
        "student_id": student.id,
        "name": student.name,
        "education_stage": student.education_stage,
        "career_goal": student.career_goal,
        "sports_interest": student.sports_interest,
        "motivation_tags": _loads(student.motivation_tags),
    }

    profile = (
        db.query(StudentProfile)
        .filter(StudentProfile.student_id == student_id)
        .first()
    )
    if profile is not None:
        context["interests"] = _loads(profile.interests)
        context["skills"] = _loads(profile.skills)
        context["completed_milestone_ids"] = _loads(profile.completed_milestone_ids)
        context["job_readiness_score"] = profile.job_readiness_score

    roadmap = (
        db.query(Roadmap)
        .filter(Roadmap.student_id == student_id)
        .order_by(Roadmap.id.desc())
        .first()
    )
    if roadmap is not None:
        context["current_stage"] = roadmap.current_stage
        context["current_step_title"] = roadmap.current_step_title
        context["career_id"] = roadmap.career_id

    return context


def get_active_milestones(
    db: Session,
    student_id: int,
    *,
    limit: int = 3,
) -> list[dict]:
    """Pending/in-progress milestones from the student's latest roadmap.

    Ordered by the roadmap's own ordering (order_index); bounded per the
    NBA token budget (§14: max 5 milestones — default 3 here).
    """
    roadmap = (
        db.query(Roadmap)
        .filter(Roadmap.student_id == student_id)
        .order_by(Roadmap.id.desc())
        .first()
    )
    if roadmap is None:
        return []

    rows = (
        db.query(Milestone)
        .filter(
            Milestone.roadmap_id == roadmap.id,
            Milestone.status.in_(("pending", "in_progress")),
        )
        .order_by(Milestone.order_index)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": m.id,
            "title": m.title,
            "description": m.description,
            "stage": m.stage,
            "status": m.status,
            "order_index": m.order_index,
        }
        for m in rows
    ]


def _loads(raw: Optional[str]) -> list:
    if raw is None:
        return []
    try:
        value = json.loads(raw)
        return value if isinstance(value, list) else []
    except (json.JSONDecodeError, TypeError):
        return []
