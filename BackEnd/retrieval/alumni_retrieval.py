"""Alumni retrieval (architecture_master §14, §24).

Deterministic alumni journey lookups for services and MCP tools.
Verified alumni are ordered before unverified (community-submitted)
ones; results are bounded plain dicts. Only public career-journey data
is ever exposed — no contact details exist on the model at all.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from models.alumni import Alumni

MAX_ALUMNI_RESULTS = 10


def find_alumni(
    db: Session,
    *,
    field: Optional[str] = None,
    career_id: Optional[int] = None,
    university_id: Optional[int] = None,
    limit: int = MAX_ALUMNI_RESULTS,
) -> list[dict]:
    """Alumni matching field / career / university filters.

    Ordering: verified journeys first (master §24), then by name. A
    missing/None filter matches every record; an explicit filter that
    matches nothing returns an empty list.
    """
    query = db.query(Alumni)

    field_clean = (field or "").strip()
    if field_clean:
        query = query.filter(Alumni.field.ilike(f"%{field_clean}%"))
    if career_id is not None:
        query = query.filter(Alumni.career_id == career_id)
    if university_id is not None:
        query = query.filter(Alumni.university_id == university_id)

    rows = (
        query.order_by(Alumni.is_verified.desc(), Alumni.name)
        .limit(limit)
        .all()
    )
    return [_alumni_to_dict(r) for r in rows]


def get_alumni(db: Session, alumni_id: int) -> Optional[dict]:
    """One alumni record as a dict (None when missing)."""
    record = db.get(Alumni, alumni_id)
    if record is None:
        return None
    return _alumni_to_dict(record)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_list(raw) -> list:
    import json

    if raw is None or raw == "":
        return []
    try:
        value = json.loads(raw)
        return value if isinstance(value, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def _alumni_to_dict(record: Alumni) -> dict:
    return {
        "id": record.id,
        "name": record.name,
        "university": record.university,
        "university_id": record.university_id,
        "field": record.field,
        "role": record.role,
        "company": record.company,
        "career_id": record.career_id,
        "career_path": record.career_path,
        "advice": record.advice,
        "tags": _parse_list(record.tags),
        "is_verified": bool(record.is_verified) if record.is_verified is not None else False,
        "source_url": record.source_url,
    }
