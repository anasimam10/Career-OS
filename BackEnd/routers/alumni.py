"""
Alumni router (master §17/§24).

Endpoints:
- GET  /alumni        — alumni journey cards (database only, no AI)
- GET  /alumni/{id}   — one full alumni journey with provenance

Verified journeys are ordered before community-submitted ones. Only public
career-journey data is exposed — the model has no contact details at all.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database import get_db
from retrieval import alumni_retrieval
from schemas.shared import AlumniCard
from schemas.responses import AlumniDetail, AlumniListResponse

router = APIRouter(tags=["alumni"])


@router.get("/alumni", response_model=AlumniListResponse)
def list_alumni(
    field: Optional[str] = None,
    career_id: Optional[int] = None,
    university_id: Optional[int] = None,
    limit: int = 10,
    db: Session = Depends(get_db),
) -> AlumniListResponse:
    """Alumni journeys, verified first (master §17)."""
    limit = max(1, min(limit, alumni_retrieval.MAX_ALUMNI_RESULTS))
    records = alumni_retrieval.find_alumni(
        db,
        field=field,
        career_id=career_id,
        university_id=university_id,
        limit=limit,
    )
    return AlumniListResponse(alumni=[_to_card(r) for r in records])


@router.get("/alumni/{alumni_id}", response_model=AlumniDetail)
def get_alumni(alumni_id: int, db: Session = Depends(get_db)) -> AlumniDetail | JSONResponse:
    """One alumni journey card plus provenance columns."""
    record = alumni_retrieval.get_alumni(db, alumni_id)
    if record is None:
        return JSONResponse(
            status_code=404,
            content={"error": f"Alumni {alumni_id} not found"},
        )
    return AlumniDetail(
        **_card_fields(record),
        university_id=record.get("university_id"),
        career_id=record.get("career_id"),
        source_url=record.get("source_url"),
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _to_card(record: dict) -> AlumniCard:
    return AlumniCard(**_card_fields(record))


def _card_fields(record: dict) -> dict:
    """Map a retrieval dict (model column names) onto the AlumniCard schema.

    ``career_path``/``advice`` on the model are the master §18 card's
    ``career_path_summary``/``key_advice``.
    """
    return {
        "id": record["id"],
        "name": record["name"],
        "university": record.get("university"),
        "field": record.get("field"),
        "role": record.get("role"),
        "company": record.get("company"),
        "career_path_summary": record.get("career_path"),
        "key_advice": record.get("advice"),
        "tags": record.get("tags") or [],
        "is_verified": record.get("is_verified", False),
    }
