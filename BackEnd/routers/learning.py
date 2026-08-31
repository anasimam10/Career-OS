"""
Learning router (master §17/§25).

Endpoints:
- GET  /learning  — verified learning resources (database only, no AI)

``is_free``/``duration_hours`` are shown only when verified — NULL means
unknown, never "free" or "paid" (master §10).
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from retrieval import learning_retrieval
from schemas.responses import LearningResourceListResponse

router = APIRouter(tags=["learning"])


@router.get("/learning", response_model=LearningResourceListResponse)
def list_learning_resources(
    skill: Optional[str] = None,
    level: Optional[str] = None,
    type: Optional[str] = None,
    is_free: Optional[bool] = None,
    db: Session = Depends(get_db),
) -> LearningResourceListResponse:
    """Verified learning resources for the Learning Hub (master §17).

    ``skill`` narrows to resources teaching that exact skill name; without
    it the full active catalog is returned. Only VALIDATED/VERIFIED,
    active records are ever visible.
    """
    if skill and skill.strip():
        resources = learning_retrieval.get_resources_for_skill(
            db, skill, level=level, resource_type=type, is_free=is_free
        )
    else:
        resources = learning_retrieval.list_resources(
            db, level=level, resource_type=type, is_free=is_free
        )
    return LearningResourceListResponse(resources=resources)
