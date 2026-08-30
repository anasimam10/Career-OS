"""
Job Readiness router (Phase 8).

POST /api/v1/job-readiness — deterministic score + AI gap analysis.

Error contract:
- student not found -> 404 {"error": "..."}
- AI failure        -> still 200 with deterministic scores + fallback text
  (job readiness NEVER returns 500 solely because Qwen is unavailable)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database import get_db
from schemas.shared import JobReadiness
from services import job_readiness_service

router = APIRouter(tags=["job-readiness"])


@router.post("/job-readiness", response_model=JobReadiness, responses={404: {"description": "Student not found"}})
def get_job_readiness(
    db: Session = Depends(get_db),
) -> JobReadiness | JSONResponse:
    """Compute the deterministic job readiness score and AI analysis."""
    try:
        return job_readiness_service.get_job_readiness(db)
    except job_readiness_service.StudentNotFoundError:
        return JSONResponse(
            status_code=404,
            content={"error": "Student profile not found — complete onboarding first."},
        )
