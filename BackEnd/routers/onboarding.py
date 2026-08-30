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

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from schemas.requests import OnboardingPayload
from schemas.responses import OnboardingResponse
from services import onboarding_service

router = APIRouter(tags=["onboarding"])


@router.post("/onboarding", response_model=OnboardingResponse)
def complete_onboarding(
    payload: OnboardingPayload, db: Session = Depends(get_db)
) -> OnboardingResponse:
    """Store the onboarding answers, bootstrap the journey, return the first NBA."""
    return onboarding_service.complete_onboarding(db, payload)
