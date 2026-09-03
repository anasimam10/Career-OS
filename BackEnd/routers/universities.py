"""
Universities router (master §17).

Endpoints:
- GET  /universities                — verified universities (database only, no AI)
- GET  /universities/{id}/programs  — verified programs of one university

Error contract (architecture §10):
- unknown or not-yet-validated university -> 404 {"error": ...}
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database import get_db
from retrieval import university_retrieval
from schemas.responses import ProgramListResponse, UniversityListResponse

router = APIRouter(tags=["universities"])


@router.get("/universities", response_model=UniversityListResponse)
def list_universities(
    field: Optional[str] = None,
    city: Optional[str] = None,
    type: Optional[str] = None,
    hec_recognized: Optional[bool] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> UniversityListResponse:
    """Verified universities for the University Finder (master §17).

    ``field`` narrows to universities offering at least one verified
    program in that field; ``type`` is PUBLIC/PRIVATE. Only
    VALIDATED/VERIFIED records are ever returned (master §11).
    """
    limit = max(1, min(limit, university_retrieval.MAX_UNIVERSITY_RESULTS))
    universities = university_retrieval.search_universities(
        db,
        field=field,
        city=city,
        uni_type=type,
        hec_recognized=hec_recognized,
        limit=limit,
    )
    return UniversityListResponse(universities=universities, total=len(universities))


@router.get("/universities/{university_id}/programs", response_model=ProgramListResponse)
def list_programs(
    university_id: int,
    field: Optional[str] = None,
    degree_type: Optional[str] = None,
    db: Session = Depends(get_db),
) -> ProgramListResponse | JSONResponse:
    """Verified programs of one university, filtered by field/degree_type."""
    university = university_retrieval.get_university(db, university_id)
    if university is None:
        # Unknown OR not yet validated: both are "not found" for students.
        return JSONResponse(
            status_code=404,
            content={"error": f"University {university_id} not found"},
        )
    programs = university_retrieval.get_programs(
        db, university_id, field=field, degree_type=degree_type
    )
    return ProgramListResponse(programs=programs)
