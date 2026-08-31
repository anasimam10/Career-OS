"""Learning resource retrieval (architecture_master §14, §25).

Deterministic learning-resource lookups for services and MCP tools.
Student-facing queries only return VERIFIED/VALIDATED active records;
results are bounded plain dicts.

Documented deviation from master §14: there is no skills registry table
(protected schema; careers.required_skills JSON is the source of truth),
so ``get_resources_for_skill`` takes the skill NAME — the master's own
allowance for this shape — and ``skill_id`` on the model stays NULL.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from models.learning import LearningResource
from retrieval.fts import fts_search_ids

STUDENT_VISIBLE_STATUSES = ("VALIDATED", "VERIFIED")
MAX_LEARNING_RESULTS = 15


def get_resources_for_skill(
    db: Session,
    skill: str,
    *,
    level: Optional[str] = None,
    resource_type: Optional[str] = None,
    is_free: Optional[bool] = None,
    limit: int = MAX_LEARNING_RESULTS,
) -> list[dict]:
    """Verified resources teaching ``skill`` (case-insensitive name match).

    ``level`` narrows to resources whose level matches exactly
    (beginner/intermediate/advanced); records with a NULL level match every
    level filter — they are unspecific, not wrong. ``resource_type`` and
    ``is_free`` filter exactly; unknown (NULL) values are excluded when the
    caller asks for a specific value.
    """
    skill_clean = (skill or "").strip()
    if not skill_clean:
        return []

    query = _student_visible_query(
        db, level=level, resource_type=resource_type, is_free=is_free
    ).filter(LearningResource.skill_name.ilike(skill_clean))
    rows = query.order_by(LearningResource.title).limit(limit).all()
    return [_resource_to_dict(r) for r in rows]


def list_resources(
    db: Session,
    *,
    level: Optional[str] = None,
    resource_type: Optional[str] = None,
    is_free: Optional[bool] = None,
    limit: int = MAX_LEARNING_RESULTS,
) -> list[dict]:
    """Verified resources regardless of skill — the Learning Hub catalog.

    Same visibility and filter semantics as ``get_resources_for_skill``.
    """
    query = _student_visible_query(
        db, level=level, resource_type=resource_type, is_free=is_free
    )
    rows = query.order_by(LearningResource.title).limit(limit).all()
    return [_resource_to_dict(r) for r in rows]


def search_resources(
    db: Session,
    skill_name: str,
    *,
    limit: int = MAX_LEARNING_RESULTS,
) -> list[dict]:
    """Verified resources whose skill_name, title, or provider matches.

    Free-text matching uses FTS5 over title/provider (LIKE fallback),
    plus a direct skill-name match so exact skill queries always hit.
    """
    needle = (skill_name or "").strip()
    if not needle:
        return []

    base = db.query(LearningResource).filter(
        LearningResource.is_active.is_(True),
        LearningResource.verification_status.in_(STUDENT_VISIBLE_STATUSES),
    )

    ids = fts_search_ids(db, "learning_resources", needle, limit=limit)
    if ids:
        rows = base.filter(LearningResource.id.in_(ids)).all()
    else:
        like = f"%{needle}%"
        rows = (
            base.filter(
                LearningResource.skill_name.ilike(like)
                | LearningResource.title.ilike(like)
                | LearningResource.provider.ilike(like)
            )
            .order_by(LearningResource.title)
            .limit(limit)
            .all()
        )
    rows = sorted(rows, key=lambda r: r.title)
    return [_resource_to_dict(r) for r in rows[:limit]]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _student_visible_query(
    db: Session,
    *,
    level: Optional[str] = None,
    resource_type: Optional[str] = None,
    is_free: Optional[bool] = None,
):
    """Base query: active + student-visible records with the shared filters.

    Shared by ``get_resources_for_skill`` and ``list_resources`` so the
    REST endpoint and MCP tools always apply identical semantics.
    """
    query = db.query(LearningResource).filter(
        LearningResource.is_active.is_(True),
        LearningResource.verification_status.in_(STUDENT_VISIBLE_STATUSES),
    )
    level_clean = (level or "").strip().lower()
    if level_clean:
        query = query.filter(
            (LearningResource.level.is_(None)) | (LearningResource.level == level_clean)
        )
    type_clean = (resource_type or "").strip().lower()
    if type_clean:
        query = query.filter(LearningResource.type == type_clean)
    if is_free is not None:
        # NULL means unknown: excluded when a specific value is requested.
        query = query.filter(LearningResource.is_free.is_(is_free))
    return query


def _resource_to_dict(record: LearningResource) -> dict:
    return {
        "id": record.id,
        "skill_name": record.skill_name,
        "title": record.title,
        "type": record.type,
        "provider": record.provider,
        "url": record.url,
        "language": record.language,
        "level": record.level,
        "is_free": record.is_free,  # verified only; NULL = unknown
        "duration_hours": record.duration_hours,  # verified only; NULL = unknown
        "verification_status": record.verification_status,
        "last_verified": record.last_verified.isoformat() if record.last_verified else None,
    }
