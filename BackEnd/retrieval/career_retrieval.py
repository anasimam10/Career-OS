"""Career retrieval (architecture_master §14).

Deterministic career lookups for services and MCP tools. All functions
query through SQLAlchemy, filter to active/verified records, return
bounded results, and hand back plain dicts or ORM rows — never raw
query objects.

Career SEARCHES are cached with a 5-minute TTL (master §15: career data
is stable, seed-loaded). The unfiltered listing path
(``repositories.career_repo.get_all_careers``) stays uncached so the
legacy GET /careers response is computed fresh exactly as before.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from cache import DEFAULT_TTL_SECONDS, cache
from models.career import Career
from models.university import Program
from retrieval.fts import fts_search_ids

# Master §14: student-facing queries only ever see verified records.
STUDENT_VISIBLE_STATUSES = ("VALIDATED", "VERIFIED")


def get_career(db: Session, slug: str) -> Optional[dict]:
    """One active career by slug as a plain dict (None when unknown)."""
    career = (
        db.query(Career)
        .filter(Career.slug == slug.strip(), Career.is_active.is_(True))
        .first()
    )
    if career is None:
        return None
    return _career_to_dict(career)


def search_careers(
    db: Session,
    *,
    query: str = "",
    field: Optional[str] = None,
    limit: int = 20,
) -> list[dict]:
    """Active careers matching a free-text query and/or a field filter.

    The text query uses FTS5 (name/field/category index) and falls back
to a SQL LIKE match when FTS is unavailable or returns nothing.
    Results are serialized dicts and cached for five minutes (master §15).
    """
    key = (
        "careers:search",
        (query or "").strip().lower(),
        (field or "").strip().lower(),
        limit,
    )
    cache_key = "|".join(str(part) for part in key)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    base = db.query(Career).filter(Career.is_active.is_(True))
    field_clean = (field or "").strip()
    if field_clean:
        base = base.filter(Career.field.ilike(f"%{field_clean}%"))

    query_clean = (query or "").strip()
    if not query_clean:
        rows = base.order_by(Career.name).limit(limit).all()
        result = [_career_to_dict(c) for c in rows]
        cache.set(cache_key, result, DEFAULT_TTL_SECONDS)
        return result

    ids = fts_search_ids(db, "careers", query_clean, limit=limit)
    if ids:
        rows = base.filter(Career.id.in_(ids)).all()
        rows = sorted(rows, key=lambda c: c.name)
    else:
        needle = f"%{query_clean}%"
        rows = (
            base.filter(
                Career.name.ilike(needle)
                | Career.field.ilike(needle)
                | Career.category.ilike(needle)
            )
            .order_by(Career.name)
            .limit(limit)
            .all()
        )
    result = [_career_to_dict(c) for c in rows]
    cache.set(cache_key, result, DEFAULT_TTL_SECONDS)
    return result


def get_career_skills(db: Session, career_id: int) -> list[str]:
    """Required skills for a career (the JSON column is the source of truth)."""
    career = db.get(Career, career_id)
    if career is None:
        return []
    return _parse_list(career.required_skills)


def get_career_programs(db: Session, career_id: int, limit: int = 20) -> list[dict]:
    """Verified programs whose ``career_ids`` list contains the career."""
    rows = (
        db.query(Program)
        .filter(
            Program.verification_status.in_(STUDENT_VISIBLE_STATUSES),
            Program.career_ids.isnot(None),
        )
        .limit(200)
        .all()
    )
    matches = [r for r in rows if career_id in _parse_list(r.career_ids)]
    return [_program_to_dict(r) for r in matches[:limit]]


# ---------------------------------------------------------------------------
# Serialization helpers
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


def _career_to_dict(career: Career) -> dict:
    return {
        "id": career.id,
        "slug": career.slug,
        "name": career.name,
        "field": career.field,
        "category": career.category,
        "demand_level": career.demand_level,
        "competition_level": career.competition_level,
        "difficulty_level": career.difficulty_level,
        "required_skills": _parse_list(career.required_skills),
        "pk_opportunities": _parse_list(career.pk_opportunities),
        "top_pk_universities": _parse_list(career.top_pk_universities),
        "risks": _parse_list(career.risks),
        "last_updated": career.last_updated.isoformat() if career.last_updated else None,
    }


def _program_to_dict(program: Program) -> dict:
    return {
        "id": program.id,
        "university_id": program.university_id,
        "name": program.name,
        "degree_type": program.degree_type,
        "field": program.field,
        "duration_years": program.duration_years,
        "annual_fee_pkr": program.annual_fee_pkr,  # verified only; NULL = unknown
        "admission_link": program.admission_link,
        "verification_status": program.verification_status,
    }
