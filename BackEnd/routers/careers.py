"""
Career Intelligence router (Phase 3).

Endpoints:
- GET  /careers              — list careers (database only, no AI)
- GET  /careers/{slug}       — full career record (database only, no AI)
- POST /career/analyze       — Career Reality Check (Qwen, Pattern A)
- POST /career/trial-plan    — 7-day trial plan (Qwen, Pattern A)

Error contract (architecture §10):
- unknown career           -> 404 {"error": ...}
- AI unavailable           -> 503 {"error": "AI service temporarily unavailable"}
- AI output not valid      -> 500 {"error": "AI response could not be processed"}
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database import get_db
from schemas.requests import CareerAnalyzeRequest, CareerTrialRequest
from schemas.responses import CareerDetail, CareerListItem
from schemas.shared import CareerRealityResponse, CareerTrialPlan
from services import career_service
from services.ai_service import AIUnavailableError, AIValidationError

router = APIRouter(tags=["careers"])


# ---------------------------------------------------------------------------
# Database-only endpoints (NO AI)
# ---------------------------------------------------------------------------


@router.get("/careers", response_model=list[CareerListItem])
def list_careers(db: Session = Depends(get_db)) -> list[CareerListItem]:
    """All available careers for the Career Explorer UI."""
    return career_service.get_career_list(db)


@router.get("/careers/{slug}", response_model=CareerDetail)
def get_career(slug: str, db: Session = Depends(get_db)) -> CareerDetail | JSONResponse:
    """Full career record by slug — database only."""
    career = career_service.get_career_detail(db, slug)
    if career is None:
        return JSONResponse(
            status_code=404,
            content={"error": f"Career '{slug}' not found"},
        )
    return career


# ---------------------------------------------------------------------------
# AI endpoints (Qwen via the shared Phase 2 ai_service)
# ---------------------------------------------------------------------------


@router.post("/career/analyze", response_model=CareerRealityResponse)
def analyze_career(
    request: CareerAnalyzeRequest, db: Session = Depends(get_db)
) -> CareerRealityResponse | JSONResponse:
    """Career Reality Check: student profile + career data -> Qwen -> verdict."""
    try:
        return career_service.analyze_career(db, request.career_slug)
    except career_service.CareerNotFoundError:
        return JSONResponse(
            status_code=404,
            content={"error": f"Career '{request.career_slug}' not found"},
        )
    except AIUnavailableError:
        return JSONResponse(
            status_code=503,
            content={"error": "AI service temporarily unavailable"},
        )
    except AIValidationError:
        return JSONResponse(
            status_code=500,
            content={"error": "AI response could not be processed"},
        )


@router.post("/career/trial-plan", response_model=CareerTrialPlan)
def trial_plan(
    request: CareerTrialRequest, db: Session = Depends(get_db)
) -> CareerTrialPlan | JSONResponse:
    """Generate a personalised 7-day trial plan for a career."""
    try:
        return career_service.generate_trial_plan(db, request.career_slug)
    except career_service.CareerNotFoundError:
        return JSONResponse(
            status_code=404,
            content={"error": f"Career '{request.career_slug}' not found"},
        )
    except AIUnavailableError:
        return JSONResponse(
            status_code=503,
            content={"error": "AI service temporarily unavailable"},
        )
    except AIValidationError:
        return JSONResponse(
            status_code=500,
            content={"error": "AI response could not be processed"},
        )
