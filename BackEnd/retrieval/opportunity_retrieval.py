"""Opportunity retrieval (architecture_master §14).

Deterministic opportunity lookups for services and MCP tools. Every
student-facing query applies the shared trust filters (verified, active,
not expired) through ``retrieval.visibility``. Results are bounded and
returned as plain dicts — never raw ORM rows.

Opportunity listings are deliberately NOT cached (master §15: deadlines
are always re-queried for freshness).
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from models.opportunity import Opportunity
from retrieval import visibility

# Master §13: data older than 30 days is no longer fresh.
FRESH_WINDOW_DAYS = 30


def search_opportunities(
    db: Session,
    *,
    opp_type: Optional[str] = None,
    skills: Optional[list[str]] = None,
    city: Optional[str] = None,
    field: Optional[str] = None,
    stage: Optional[str] = None,
    limit: int = 10,
) -> list[dict]:
    """Verified, active, non-expired opportunities matching the filters.

    Semantics match the REST listing (GET /opportunities) and the MCP
    search tools: city matching is case-insensitive with Nationwide
    included, a record matches the skills filter when the student has at
    least one required skill or the record lists none, and the field
    filter matches title/description/organization mentions. ``stage``
    additionally matches the record's required_education_stage when set
    (records without a stage requirement match everyone).
    """
    query = visibility.apply_opportunity_visibility(db.query(Opportunity))
    if opp_type:
        query = query.filter(Opportunity.type == opp_type)

    stage_clean = (stage or "").strip()
    if stage_clean:
        # Records that require a different stage are excluded; records
        # with no requirement are open to everyone.
        query = query.filter(
            (Opportunity.required_education_stage.is_(None))
            | (Opportunity.required_education_stage == stage_clean)
        )

    rows = query.all()

    city_clean = (city or "").strip()
    if city_clean:
        rows = [o for o in rows if _city_matches(o.location, city_clean)]

    skill_names = [s.strip().lower() for s in (skills or []) if s and s.strip()]
    if skill_names:
        rows = [
            o
            for o in rows
            if _skills_satisfied(_parse_list(o.required_skills), skill_names)
        ]

    field_clean = (field or "").strip().lower()
    if field_clean:
        rows = [o for o in rows if _field_mentions(o, field_clean)]

    # Soonest deadline first, no-deadline last (same rule as the listings).
    rows.sort(key=lambda o: (o.deadline is None, o.deadline or date.min))
    return [_opportunity_to_dict(o) for o in rows[:limit]]


def get_opportunity(db: Session, opportunity_id: int) -> Optional[dict]:
    """One student-visible opportunity as a dict (None when hidden)."""
    record = db.get(Opportunity, opportunity_id)
    if record is None or not visibility.is_opportunity_visible(record):
        return None
    return _opportunity_to_dict(record)


def get_fresh_opportunities(
    db: Session,
    *,
    opp_type: Optional[str] = None,
    limit: int = 10,
) -> list[dict]:
    """Verified opportunities verified within the last 30 days (§13)."""
    cutoff = date.today() - timedelta(days=FRESH_WINDOW_DAYS)
    query = visibility.apply_opportunity_visibility(db.query(Opportunity)).filter(
        Opportunity.last_verified.isnot(None), Opportunity.last_verified >= cutoff
    )
    if opp_type:
        query = query.filter(Opportunity.type == opp_type)
    rows = query.all()
    rows.sort(key=lambda o: (o.deadline is None, o.deadline or date.min))
    return [_opportunity_to_dict(o) for o in rows[:limit]]


# ---------------------------------------------------------------------------
# Serialization / matching helpers (same rules as Mcp.records + listings)
# ---------------------------------------------------------------------------


def _city_matches(location: Optional[str], city: str) -> bool:
    if not location:
        return False
    normalized = location.strip().lower()
    return normalized == "nationwide" or normalized == city.strip().lower()


def _skills_satisfied(required: list, student_skills: list[str]) -> bool:
    if not required:
        return True
    normalized = [str(skill).strip().lower() for skill in required]
    return any(skill in student_skills for skill in normalized)


def _field_mentions(record, needle: str) -> bool:
    return (
        needle in (record.title or "").lower()
        or needle in (record.description or "").lower()
        or needle in (record.organization or "").lower()
        or needle in (record.field or "").lower()
    )


def _parse_list(raw) -> list:
    import json

    if raw is None or raw == "":
        return []
    try:
        value = json.loads(raw)
        return value if isinstance(value, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def _opportunity_to_dict(record: Opportunity) -> dict:
    return {
        "id": record.id,
        "type": record.type,
        "title": record.title,
        "organization": record.organization,
        "location": record.location,
        "province": record.province,
        "is_remote": bool(record.is_remote) if record.is_remote is not None else False,
        "deadline": record.deadline.isoformat() if record.deadline else None,
        "required_skills": _parse_list(record.required_skills),
        "description": record.description,
        "field": record.field,
        "source_url": record.source_url,
        "last_verified": record.last_verified.isoformat() if record.last_verified else None,
        "verification_status": record.verification_status,
        "organization_type": record.organization_type,
        "required_degree_type": record.required_degree_type,
        "eligibility_notes": record.eligibility_notes,
    }
