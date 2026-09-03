"""University retrieval (architecture_master §14).

Deterministic university/program lookups for services and MCP tools.
Student-facing queries only return VERIFIED/VALIDATED records; results
are bounded plain dicts.

University searches are cached with a 5-minute TTL (master §15) —
university records are stable, seed-loaded data with no deadline-style
freshness concerns. The cache is cleared by admin actions and tests.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from cache import DEFAULT_TTL_SECONDS, cache
from models.university import Program, University
from retrieval.fts import fts_search_ids

# Master §11: student-facing queries see VALIDATED/VERIFIED records only.
STUDENT_VISIBLE_STATUSES = ("VALIDATED", "VERIFIED")

MAX_UNIVERSITY_RESULTS = 300
MAX_PROGRAM_RESULTS = 50


def search_universities(
    db: Session,
    *,
    field: Optional[str] = None,
    city: Optional[str] = None,
    uni_type: Optional[str] = None,
    hec_recognized: Optional[bool] = None,
    query: str = "",
    limit: int = MAX_UNIVERSITY_RESULTS,
) -> list[dict]:
    """Verified universities matching field/city/type filters.

    ``field`` narrows to universities that offer at least one verified
    program in that field. ``query`` is a free-text FTS match on the
    university name (LIKE fallback). Results are cached for five minutes.
    """
    key = (
        "universities:search",
        (field or "").strip().lower(),
        (city or "").strip().lower(),
        (uni_type or "").strip().upper(),
        "" if hec_recognized is None else str(hec_recognized),
        (query or "").strip().lower(),
        limit,
    )
    cached = cache.get(_key_str(key))
    if cached is not None:
        return cached

    base = db.query(University).filter(
        University.verification_status.in_(STUDENT_VISIBLE_STATUSES)
    )

    city_clean = (city or "").strip()
    if city_clean:
        base = base.filter(University.city.ilike(f"%{city_clean}%"))

    type_clean = (uni_type or "").strip().upper()
    if type_clean:
        base = base.filter(University.type == type_clean)

    if hec_recognized is not None:
        base = base.filter(University.hec_recognized.is_(hec_recognized))

    query_clean = (query or "").strip()
    if query_clean:
        ids = fts_search_ids(db, "universities", query_clean, limit=limit)
        if ids:
            rows = base.filter(University.id.in_(ids)).all()
        else:
            rows = base.filter(
                (University.name.ilike(f"%{query_clean}%"))
                | (University.short_name.ilike(f"%{query_clean}%"))
                | (University.slug.ilike(f"%{query_clean}%"))
            ).all()
    else:
        rows = base.order_by(University.name).all()

    rows = sorted(rows, key=lambda u: (u.short_name or u.name))

    field_clean = (field or "").strip()
    if field_clean:
        program_university_ids = _university_ids_with_field(db, field_clean)
        rows = [u for u in rows if u.id in program_university_ids]

    result = [_university_to_dict(u) for u in rows[:limit]]
    cache.set(_key_str(key), result, DEFAULT_TTL_SECONDS)
    return result


def get_university(db: Session, university_id: int) -> Optional[dict]:
    """One student-visible university as a dict (None when hidden/missing)."""
    record = db.get(University, university_id)
    if record is None or record.verification_status not in STUDENT_VISIBLE_STATUSES:
        return None
    return _university_to_dict(record)


def get_programs(
    db: Session,
    university_id: int,
    *,
    field: Optional[str] = None,
    degree_type: Optional[str] = None,
    limit: int = MAX_PROGRAM_RESULTS,
) -> list[dict]:
    """Verified programs of one university, optionally narrowed by field
    (substring) and degree type (exact, case-insensitive: BS/BE/BBA/MS/…)."""
    university = db.get(University, university_id)
    if university is None or university.verification_status not in STUDENT_VISIBLE_STATUSES:
        return []

    query = db.query(Program).filter(
        Program.university_id == university_id,
        Program.verification_status.in_(STUDENT_VISIBLE_STATUSES),
    )
    field_clean = (field or "").strip()
    if field_clean:
        query = query.filter(Program.field.ilike(f"%{field_clean}%"))
    degree_clean = (degree_type or "").strip()
    if degree_clean:
        query = query.filter(Program.degree_type.ilike(degree_clean))
    rows = query.order_by(Program.name).limit(limit).all()
    return [_program_to_dict(p) for p in rows]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _university_ids_with_field(db: Session, field: str) -> set[int]:
    rows = (
        db.query(Program.university_id)
        .filter(
            Program.verification_status.in_(STUDENT_VISIBLE_STATUSES),
            Program.field.ilike(f"%{field}%"),
        )
        .distinct()
        .all()
    )
    return {row[0] for row in rows}


def _key_str(key: tuple) -> str:
    return "|".join(str(part) for part in key)


def _university_to_dict(record: University) -> dict:
    return {
        "id": record.id,
        "name": record.name,
        "short_name": record.short_name,
        "slug": record.slug,
        "city": record.city,
        "province": record.province,
        "type": record.type,
        "hec_recognized": record.hec_recognized,
        "hec_category": record.hec_category,
        "website_url": record.website_url,
        "admissions_url": record.admissions_url,
        "verification_status": record.verification_status,
        "last_verified": record.last_verified.isoformat() if record.last_verified else None,
    }


def _program_to_dict(record: Program) -> dict:
    import json

    career_ids: list = []
    if record.career_ids:
        try:
            parsed = json.loads(record.career_ids)
            career_ids = parsed if isinstance(parsed, list) else []
        except (json.JSONDecodeError, TypeError):
            career_ids = []
    return {
        "id": record.id,
        "university_id": record.university_id,
        "name": record.name,
        "degree_type": record.degree_type,
        "field": record.field,
        "duration_years": record.duration_years,
        "annual_fee_pkr": record.annual_fee_pkr,  # verified only; NULL = unknown
        "admission_link": record.admission_link,
        "career_ids": career_ids,
        "verification_status": record.verification_status,
    }


def get_university_secondary_intellectual_capital(
    db: Session, university_id_or_slug: str | int
) -> dict | None:
    """Retrieve supplementary faculty intellectual capital from secondary dataset.

    Returns None if university not found or has no secondary CS faculty data.
    Clearly marks data as EXTERNAL_SECONDARY / L2 authority level.
    """
    import json
    from knowledge_engine.staging import PKEStagingRecord

    if isinstance(university_id_or_slug, int) or (
        isinstance(university_id_or_slug, str) and university_id_or_slug.isdigit()
    ):
        uni = db.query(University).filter(University.id == int(university_id_or_slug)).first()
    else:
        uni = db.query(University).filter(University.slug == str(university_id_or_slug)).first()

    if not uni:
        return None

    dedup_key = f"enrichment:university:{uni.id}"
    record = (
        db.query(PKEStagingRecord)
        .filter(
            PKEStagingRecord.domain == "university_secondary_enrichment",
            PKEStagingRecord.dedup_key == dedup_key,
        )
        .first()
    )
    if not record or not record.extracted_json:
        return None

    try:
        data = json.loads(record.extracted_json)
        data["is_primary"] = False
        data["authority_level"] = "L2"
        data["source_type"] = "EXTERNAL_SECONDARY"
        data["data_provenance_note"] = (
            "Supplementary external secondary dataset. Primary verified university records remain authoritative."
        )
        return data
    except (json.JSONDecodeError, TypeError):
        return None


def get_public_universities_macro_statistics(db: Session) -> list[dict]:
    """Retrieve historical public universities macro-level count time-series.

    Classified as L2 / EXTERNAL_SECONDARY.
    """
    import json
    from knowledge_engine.staging import PKEStagingRecord

    records = (
        db.query(PKEStagingRecord)
        .filter(PKEStagingRecord.domain == "macro_statistics")
        .order_by(PKEStagingRecord.id.asc())
        .all()
    )
    results = []
    for r in records:
        if r.extracted_json:
            try:
                item = json.loads(r.extracted_json)
                item["source_type"] = "EXTERNAL_SECONDARY"
                item["authority_level"] = "L2"
                results.append(item)
            except (json.JSONDecodeError, TypeError):
                continue
    return results

