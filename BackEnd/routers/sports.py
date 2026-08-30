"""
Sports router (Phase 6).

Endpoints:
- GET  /sports        — list sports opportunities (database only, no AI)
- POST /sports/match  — Pattern B retrieval + deterministic eligibility scoring

Sports data reuses the opportunities architecture (implementation-status §10),
so the service layer is the shared opportunity_service.

Error contract: identical to routers/opportunities.py (architecture §10).
"""

from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database import get_db
from schemas.requests import SportsMatchRequest
from schemas.responses import SportsMatchResponse, SportsOpportunityOut
from services import opportunity_service
from services.ai_service import AIUnavailableError

router = APIRouter(tags=["sports"])

# Architecture §7: sports_opportunities.type is tournament/trial/scholarship/programme.
SportsTypeFilter = Literal["tournament", "trial", "scholarship", "programme"]


@router.get("/sports", response_model=list[SportsOpportunityOut])
def list_sports(
    sport: Optional[str] = None,
    city: Optional[str] = None,
    type: Optional[SportsTypeFilter] = None,
    db: Session = Depends(get_db),
) -> list[SportsOpportunityOut] | JSONResponse:
    """All active sports opportunities, filtered by sport, city, and type (§8)."""
    items = opportunity_service.list_sports(db, sport=sport, city=city, sports_type=type)
    if not items:
        # Architecture §10 no-results contract.
        return JSONResponse(
            status_code=200,
            content={
                "sports_opportunities": [],
                "message": opportunity_service.NO_RESULTS_MESSAGE,
            },
        )
    return items


@router.post("/sports/match", response_model=SportsMatchResponse)
def match_sports(
    request: SportsMatchRequest, db: Session = Depends(get_db)
) -> SportsMatchResponse | JSONResponse:
    """Match the student to relevant sports opportunities ({sport, location, level})."""
    try:
        return opportunity_service.match_sports(db, request)
    except opportunity_service.StudentNotFoundError:
        return JSONResponse(
            status_code=404,
            content={"error": "Student profile not found — complete onboarding first."},
        )
    except opportunity_service.InvalidRequestError as exc:
        return JSONResponse(
            status_code=422,
            content={"error": str(exc)},
        )
    except AIUnavailableError:
        return JSONResponse(
            status_code=503,
            content={"error": "AI service temporarily unavailable"},
        )
