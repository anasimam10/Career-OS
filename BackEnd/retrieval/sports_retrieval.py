"""Sports opportunity retrieval (architecture_master §14).

Deterministic sports lookups for services and MCP tools. Student-facing
queries apply the shared trust filters (verified, active, not expired)
through ``retrieval.visibility``. Results are bounded plain dicts.

Documented deviation from master §14: the sports_opportunities table has
no ``slug`` column (protected schema), so ``get_sport`` looks up by id.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from models.opportunity import SportsOpportunity
from retrieval import visibility

MAX_SPORTS_RESULTS = 20


def search_sports_opportunities(
    db: Session,
    *,
    sport: Optional[str] = None,
    city: Optional[str] = None,
    sports_type: Optional[str] = None,
    limit: int = MAX_SPORTS_RESULTS,
) -> list[dict]:
    """Verified, active, non-expired sports opportunities.

    ``sport`` matching is case-insensitive; ``city`` matching is
    case-insensitive with Nationwide included (same rules as the MCP
    sports tools and the GET /sports listing).
    """
    query = visibility.apply_sports_visibility(db.query(SportsOpportunity))

    sport_clean = (sport or "").strip()
    if sport_clean:
        query = query.filter(SportsOpportunity.sport.ilike(sport_clean))

    type_clean = (sports_type or "").strip()
    if type_clean:
        query = query.filter(SportsOpportunity.type == type_clean)

    rows = query.all()

    city_clean = (city or "").strip()
    if city_clean:
        rows = [r for r in rows if _city_matches(r.location, city_clean)]

    rows.sort(key=lambda r: (r.deadline is None, r.deadline or date.min))
    return [_sports_to_dict(r) for r in rows[:limit]]


def get_sport(db: Session, sports_opportunity_id: int) -> Optional[dict]:
    """One student-visible sports opportunity (None when hidden/missing)."""
    record = db.get(SportsOpportunity, sports_opportunity_id)
    if record is None or not visibility.is_sports_opportunity_visible(record):
        return None
    return _sports_to_dict(record)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _city_matches(location: Optional[str], city: str) -> bool:
    if not location:
        return False
    normalized = location.strip().lower()
    return normalized == "nationwide" or normalized == city.strip().lower()


def _parse_obj(raw) -> dict:
    import json

    if raw is None or raw == "":
        return {}
    try:
        value = json.loads(raw)
        return value if isinstance(value, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def _sports_to_dict(record: SportsOpportunity) -> dict:
    return {
        "id": record.id,
        "sport": record.sport,
        "type": record.type,
        "title": record.title,
        "organization": record.organization,
        "location": record.location,
        "deadline": record.deadline.isoformat() if record.deadline else None,
        "eligibility": _parse_obj(record.eligibility),
        "description": record.description,
        "source_url": record.source_url,
        "last_verified": record.last_verified.isoformat() if record.last_verified else None,
        "verification_status": record.verification_status,
    }
