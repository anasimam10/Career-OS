"""
Journey & roadmap router (Phase 4).

Endpoints:
- GET  /journey   — current stage + current step + max 3 visible steps + NBA
- POST /roadmap   — create/reuse the roadmap, return 1-3 visible steps (no AI)
- POST /progress  — complete a milestone, advance the stage, recalculate NBA

Error contract (architecture §10):
- unknown student / milestone / career -> 404 {"error": ...}
- invalid target stage / milestone status -> 422 {"error": ...}
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database import get_db
from routers.deps import get_current_student_id
from schemas.requests import ProgressRequest, RoadmapRequest
from schemas.responses import JourneyResponse, ProgressResponse, RoadmapResponse
from services import journey_service, progress_service, roadmap_service

router = APIRouter(tags=["journey"])


@router.get("/journey", response_model=JourneyResponse)
def get_journey(
    db: Session = Depends(get_db),
    student_id: int = Depends(get_current_student_id),
) -> JourneyResponse | JSONResponse:
    """The student's current journey state (progressive disclosure: max 3 steps)."""
    try:
        return journey_service.get_journey(db, student_id=student_id)
    except journey_service.StudentNotFoundError:
        return JSONResponse(
            status_code=404,
            content={"error": "Student profile not found — complete onboarding first."},
        )


@router.post("/roadmap", response_model=RoadmapResponse)
def create_roadmap(
    request: RoadmapRequest,
    db: Session = Depends(get_db),
    student_id: int = Depends(get_current_student_id),
) -> RoadmapResponse | JSONResponse:
    """Create (idempotently) the roadmap milestones and return visible steps only."""
    student = journey_service.get_current_student(db, student_id=student_id)

    if student is None:
        return JSONResponse(
            status_code=404,
            content={"error": "Student profile not found — complete onboarding first."},
        )
    try:
        return roadmap_service.create_roadmap(
            db,
            student_id=student.id,
            career_slug=request.career_slug,
            target_stage=request.target_stage,
        )
    except roadmap_service.CareerNotFoundError:
        return JSONResponse(
            status_code=404,
            content={"error": f"Career '{request.career_slug}' not found"},
        )
    except roadmap_service.InvalidStageError:
        return JSONResponse(
            status_code=422,
            content={"error": f"Invalid target stage '{request.target_stage}'"},
        )


@router.get("/journey/{target_student_id}", response_model=JourneyResponse)
def get_journey_for_student(
    target_student_id: int,
    db: Session = Depends(get_db),
) -> JourneyResponse | JSONResponse:
    """Retrieve journey state for a specific student id."""
    try:
        return journey_service.get_journey(db, student_id=target_student_id)
    except journey_service.StudentNotFoundError:
        return JSONResponse(
            status_code=404,
            content={"error": "Student profile not found — complete onboarding first."},
        )


@router.post("/progress", response_model=ProgressResponse)
def record_progress(
    request: ProgressRequest,
    db: Session = Depends(get_db),
    student_id: int = Depends(get_current_student_id),
) -> ProgressResponse | JSONResponse:
    """Mark a milestone done/skipped; the backend advances the stage if valid."""
    effective_student_id = request.studentId or request.student_id or student_id
    if request.milestone_id is None and request.milestoneId is not None:
        request.milestone_id = request.milestoneId
    try:
        return progress_service.record_progress(db, request, student_id=effective_student_id)
    except progress_service.MilestoneNotFoundError:
        return JSONResponse(
            status_code=404,
            content={"error": f"Milestone {request.milestone_id} not found"},
        )
    except progress_service.InvalidStatusError:
        return JSONResponse(
            status_code=422,
            content={"error": f"Invalid milestone status '{request.status}'"},
        )


@router.post("/journey/complete", response_model=ProgressResponse)
def complete_journey(
    request: ProgressRequest,
    db: Session = Depends(get_db),
    student_id: int = Depends(get_current_student_id),
) -> ProgressResponse | JSONResponse:
    """Alias for completing a milestone on /journey/complete."""
    return record_progress(request, db=db, student_id=student_id)
