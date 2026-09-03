"""
Onboarding router (Phase 4).

POST /api/v1/onboarding — update the demo student's profile and receive
the first Next Best Action.

Error contract (architecture §10):
- invalid payload (Pydantic)        -> 422 with field-level errors (FastAPI)
- AI unavailability never 503s here: the NBA engine falls back to the
  deterministic highest-priority candidate so onboarding never dead-ends.
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from database import get_db
from schemas.requests import OnboardingPayload
from schemas.responses import OnboardingResponse
from services import onboarding_service

router = APIRouter(tags=["onboarding"])


@router.post("/onboarding", response_model=OnboardingResponse)
def complete_onboarding(
    payload: OnboardingPayload,
    db: Session = Depends(get_db),
    x_student_id: Optional[str] = Header(default=None, alias="X-Student-Id"),
) -> OnboardingResponse:
    """Store the onboarding answers, bootstrap the journey, return the first NBA."""
    is_new = False
    student_id = None
    if x_student_id:
        val = x_student_id.strip().lower()
        if val == "new":
            is_new = True
        elif val.isdigit() and int(val) > 0:
            student_id = int(val)

    return onboarding_service.complete_onboarding(
        db, payload, student_id=student_id, is_new=is_new
    )

