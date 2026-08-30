"""
Opportunities router (Phase 6).

Endpoints:
- GET  /opportunities        — list opportunities (database only, no AI)
- POST /opportunities/match  — Pattern B retrieval + deterministic scoring

Error contract (architecture §10):
- unknown student          -> 404 {"error": ...}
- blank required field     -> 422 {"error": ...}
- invalid query/body value -> 422 (FastAPI/Pydantic field errors)
- AI + MCP total failure   -> 503 {"error": "AI service temporarily unavailable"}
- no matching records      -> 200 with the §10 empty envelope
"""

from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database import get_db
from schemas.requests import OpportunityMatchRequest
from schemas.responses import OpportunityMatchResponse, OpportunityOut
from services import opportunity_service
from services.ai_service import AIUnavailableError

router = APIRouter(tags=["opportunities"])

# Architecture §7: opportunities.type is internship/job/scholarship/education.
OpportunityTypeFilter = Literal["internship", "job", "scholarship", "education"]


@router.get("/opportunities", response_model=list[OpportunityOut])
def list_opportunities(
    type: Optional[OpportunityTypeFilter] = None,
    city: Optional[str] = None,
    field: Optional[str] = None,
    skills: Optional[str] = None,
    db: Session = Depends(get_db),
) -> list[OpportunityOut] | JSONResponse:
    """All active opportunities, filtered by type, city, field, and skills (§8)."""
    skill_list = [s.strip() for s in skills.split(",") if s.strip()] if skills else None
    items = opportunity_service.list_opportunities(
        db, opp_type=type, city=city, field=field, skills=skill_list
    )
    if not items:
        # Architecture §10 no-results contract.
        return JSONResponse(
            status_code=200,
            content={"opportunities": [], "message": opportunity_service.NO_RESULTS_MESSAGE},
        )
    return items


@router.post("/opportunities/match", response_model=OpportunityMatchResponse)
def match_opportunities(
    request: OpportunityMatchRequest, db: Session = Depends(get_db)
) -> OpportunityMatchResponse | JSONResponse:
    """AI-ranked opportunity matches for the student (Pattern B + deterministic scoring)."""
    try:
        return opportunity_service.match_opportunities(db, request)
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
