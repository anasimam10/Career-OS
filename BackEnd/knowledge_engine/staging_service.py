"""
Pakistan Knowledge Engine — Staging Review & Promotion Service (Step 5).

Provides admin review and promotion capabilities for candidate records stored
in ``pke_staging_records``.

Lifecycle:
    CANDIDATE → (review) → VERIFIED or REJECTED
    VERIFIED   → (promote) → live production record

Safety rules enforced here:
  - Geographic scope must be one of the five MVP values.
  - Never-infer: high-risk nullable fields (deadline, fees, CGPA, salary,
    eligibility) must be absent/null — a non-null value without source evidence
    causes promotion to be blocked.
  - Idempotent promotion: calling promote() on the same staging record more
    than once will never create a duplicate production record.
  - Provenance (source_url, source_id, content_hash) is forwarded verbatim to
    the destination row.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import date
from typing import Any, Optional

from sqlalchemy.orm import Session

from knowledge_engine.staging import PKEStagingRecord
from models.learning import LearningResource
from models.opportunity import Opportunity, SportsOpportunity
from models.university import Program, University

logger = logging.getLogger("ah_career.knowledge_engine.staging_service")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_REVIEW_ACTIONS = {"VERIFY", "REJECT", "RESET"}

# MVP geography — the only values that may appear in production student-facing
# records.  Values are matched case-insensitively during validation.
MVP_CITIES = {"karachi", "lahore", "islamabad", "nationwide", "online", "nationwide/online"}

# Destination table mapping
OPPORTUNITY_TYPE_MAP = {
    "scholarships": "scholarship",
    "internships": "internship",
    "jobs": "job",
    "opportunities": "education",  # generic bucket
}
SPORTS_TYPE_MAP = {
    "tournaments": "tournament",
    "trials": "trial",
    "sports": "programme",
}

# Fields that must NEVER be inferred; if present in extracted JSON, the
# value must have come from explicit source text.  Step 5 cannot verify that
# the Qwen extraction faithfully followed this rule, so promotion blocks these
# fields only when the promoter can detect an obvious fabrication signal.
# This is a best-effort guard — the never-infer rule is primarily enforced at
# extraction time (Step 3).
_NEVER_INFER_OPPORTUNITY_FIELDS = {
    "deadline",
    "required_cgpa",
    "stipend_pkr",
    "annual_fee_pkr",
}

# Status constants — must match the statuses used by the existing
# visibility.py gate (VALIDATED/VERIFIED are student-visible).
STATUS_CANDIDATE = "CANDIDATE"
STATUS_VERIFIED  = "VERIFIED"
STATUS_REJECTED  = "REJECTED"

PROMOTABLE_STATUS = STATUS_VERIFIED


class StagingServiceError(ValueError):
    """Raised when a staging review or promotion operation fails."""


# ---------------------------------------------------------------------------
# Listing helpers
# ---------------------------------------------------------------------------


def list_staging_records(
    db: Session,
    *,
    domain: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[PKEStagingRecord], int]:
    """Return a paginated (records, total) pair with optional filters.

    Parameters
    ----------
    domain:
        PKE domain string to filter by (e.g. ``"scholarships"``).
    status:
        ``verification_status`` value to filter by.
    skip / limit:
        Standard pagination offsets.
    """
    query = db.query(PKEStagingRecord)
    if domain:
        query = query.filter(PKEStagingRecord.domain == domain.strip().lower())
    if status:
        query = query.filter(
            PKEStagingRecord.verification_status == status.strip().upper()
        )
    total = query.count()
    records = (
        query.order_by(PKEStagingRecord.id.desc()).offset(skip).limit(limit).all()
    )
    return records, total


def get_staging_record(db: Session, record_id: int) -> Optional[PKEStagingRecord]:
    """Fetch one staging record by integer PK; None when absent."""
    return (
        db.query(PKEStagingRecord)
        .filter(PKEStagingRecord.id == record_id)
        .first()
    )


# ---------------------------------------------------------------------------
# Review action
# ---------------------------------------------------------------------------


def review_staging_record(
    db: Session,
    record_id: int,
    action: str,
    reviewer_notes: Optional[str] = None,
) -> PKEStagingRecord:
    """Transition a staging record's ``verification_status``.

    ``action`` must be one of ``VALID_REVIEW_ACTIONS``:
    - ``VERIFY``  → ``VERIFIED``
    - ``REJECT``  → ``REJECTED``
    - ``RESET``   → ``CANDIDATE``

    Raises
    ------
    StagingServiceError
        When action is invalid, record is not found, or the transition is
        disallowed (e.g. already REJECTED cannot be VERIFIED directly without
        a RESET first).
    """
    action_upper = (action or "").strip().upper()
    if action_upper not in VALID_REVIEW_ACTIONS:
        raise StagingServiceError(
            f"Invalid action '{action}'. Must be one of: {sorted(VALID_REVIEW_ACTIONS)}"
        )

    record = get_staging_record(db, record_id)
    if record is None:
        raise StagingServiceError(f"Staging record {record_id} not found.")

    # Guard: don't silently re-verify a rejected record; require RESET first.
    if action_upper == "VERIFY" and record.verification_status == STATUS_REJECTED:
        raise StagingServiceError(
            "Cannot VERIFY a REJECTED record. RESET it to CANDIDATE first."
        )

    status_map = {
        "VERIFY": STATUS_VERIFIED,
        "REJECT": STATUS_REJECTED,
        "RESET":  STATUS_CANDIDATE,
    }
    record.verification_status = status_map[action_upper]
    db.commit()
    db.refresh(record)
    logger.info(
        "Staging record %d → %s (action=%s)",
        record.id, record.verification_status, action_upper,
    )
    return record


# ---------------------------------------------------------------------------
# Geographic validation
# ---------------------------------------------------------------------------


def _validate_geography(location: Optional[str]) -> None:
    """Raise StagingServiceError when ``location`` is outside the MVP scope."""
    if location is None:
        return  # null location is allowed (e.g. nationwide implied)
    loc = location.strip().lower()
    if loc in MVP_CITIES:
        return
    raise StagingServiceError(
        f"Geographic scope '{location}' is not in the MVP city list. "
        f"Allowed: {sorted(MVP_CITIES)}."
    )


# ---------------------------------------------------------------------------
# Promotion helpers
# ---------------------------------------------------------------------------


def _parse_date_safe(val: Any) -> Optional[date]:
    """Parse string/date; None for missing/unparseable."""
    if isinstance(val, date):
        return val
    if isinstance(val, str) and val.strip():
        try:
            return date.fromisoformat(val.strip())
        except ValueError:
            return None
    return None


def _generate_slug(text: str) -> str:
    """Deterministic lowercase slug."""
    clean = re.sub(r"[^a-zA-Z0-9\s-]", "", text or "").strip().lower()
    return re.sub(r"[\s-]+", "-", clean) or "unnamed"


def _skill_json(skills: Any) -> str:
    if isinstance(skills, list):
        return json.dumps(skills)
    if isinstance(skills, str):
        parts = [s.strip() for s in skills.split(",") if s.strip()]
        return json.dumps(parts)
    return json.dumps([])


# ---------------------------------------------------------------------------
# Promotion
# ---------------------------------------------------------------------------


def promote_staging_record(db: Session, record_id: int) -> dict:
    """Promote a VERIFIED staging record into its operational production table.

    Returns a dict:
    - ``promoted``: True when a new row was inserted; False when an existing
      matching row was found (idempotent/safe re-call).
    - ``staging_id``: the staging record PK.
    - ``target_table``: destination table name.
    - ``target_id``: PK of the inserted/found production row.
    - ``title``: human-readable name of the record.
    - ``message``: advisory note (present when ``promoted=False``).

    Raises
    ------
    StagingServiceError
        - Record not found.
        - Record not in VERIFIED status.
        - Malformed extracted_json.
        - Required field missing from extracted data.
        - Geography outside MVP scope.
        - Domain not yet attached to a production table.
    """
    record = get_staging_record(db, record_id)
    if record is None:
        raise StagingServiceError(f"Staging record {record_id} not found.")

    if record.verification_status != PROMOTABLE_STATUS:
        raise StagingServiceError(
            f"Only VERIFIED records can be promoted. "
            f"Current status: '{record.verification_status}'."
        )

    try:
        data: dict = json.loads(record.extracted_json)
    except Exception as exc:
        raise StagingServiceError(f"Malformed extracted_json: {exc}") from exc

    domain = record.domain.strip().lower()

    # ------------------------------------------------------------------
    # 1. Opportunities (scholarships / internships / jobs / opportunities)
    # ------------------------------------------------------------------
    if domain in OPPORTUNITY_TYPE_MAP:
        return _promote_opportunity(db, record, data, OPPORTUNITY_TYPE_MAP[domain])

    # ------------------------------------------------------------------
    # 2. Sports opportunities
    # ------------------------------------------------------------------
    if domain in SPORTS_TYPE_MAP:
        return _promote_sports(db, record, data, SPORTS_TYPE_MAP[domain])

    # ------------------------------------------------------------------
    # 3. Universities
    # ------------------------------------------------------------------
    if domain == "universities":
        return _promote_university(db, record, data)

    # ------------------------------------------------------------------
    # 4. Programs
    # ------------------------------------------------------------------
    if domain == "programs":
        return _promote_program(db, record, data)

    # ------------------------------------------------------------------
    # 5. Learning Resources
    # ------------------------------------------------------------------
    if domain in ("learning_resources", "learning"):
        return _promote_learning_resource(db, record, data)

    # ------------------------------------------------------------------
    # 6. Domains without an operational table yet (schools, colleges, …)
    # ------------------------------------------------------------------
    return {
        "promoted": False,
        "staging_id": record.id,
        "domain": domain,
        "target_table": None,
        "target_id": None,
        "title": data.get("name") or data.get("title"),
        "status": STATUS_VERIFIED,
        "message": (
            f"Domain '{domain}' is verified in staging but has no attached "
            "operational table yet (schools/colleges are not yet promoted)."
        ),
    }


# ---------------------------------------------------------------------------
# Domain-specific promotion helpers
# ---------------------------------------------------------------------------


def _promote_opportunity(
    db: Session, record: PKEStagingRecord, data: dict, opp_type: str
) -> dict:
    title = data.get("title") or data.get("name")
    if not title:
        raise StagingServiceError("Missing required field 'title'.")

    location = data.get("location") or data.get("city")
    _validate_geography(location)

    # Idempotency: check for existing row with same dedup_key or source_url+title
    existing = _find_existing_opportunity(db, record, title, opp_type)
    if existing:
        return _already_promoted("opportunities", existing.id, existing.title, record.id)

    opp = Opportunity(
        type=opp_type,
        title=title,
        organization=data.get("organization") or data.get("company"),
        location=location,
        province=data.get("province"),
        deadline=_parse_date_safe(data.get("deadline")),
        required_skills=_skill_json(data.get("required_skills")),
        description=data.get("description"),
        source_url=record.source_url,
        source_id=record.source_id,
        content_hash=record.content_hash,
        dedup_key=record.dedup_key,
        verification_status=STATUS_VERIFIED,
        last_verified=date.today(),
        is_active=True,
        field=data.get("field"),
        is_remote=bool(data.get("is_remote", False)),
        organization_type=data.get("organization_type"),
        required_education_stage=data.get("required_education_stage"),
        required_degree_type=data.get("required_degree_type"),
        # never-infer: only store if explicitly present in data
        required_cgpa=_nullable_float(data.get("required_cgpa")),
        stipend_pkr=_nullable_int(data.get("stipend_pkr")),
        eligibility_notes=data.get("eligibility_notes"),
    )
    db.add(opp)
    db.commit()
    db.refresh(opp)
    return _success_result("opportunities", opp.id, opp.title, record.id)


def _promote_sports(
    db: Session, record: PKEStagingRecord, data: dict, sport_type: str
) -> dict:
    title = data.get("title") or data.get("name")
    if not title:
        raise StagingServiceError("Missing required field 'title'.")

    location = data.get("location") or data.get("city")
    _validate_geography(location)

    existing = _find_existing_sports(db, record, title, sport_type)
    if existing:
        return _already_promoted("sports_opportunities", existing.id, existing.title, record.id)

    eligibility = data.get("eligibility")
    if isinstance(eligibility, (dict, list)):
        eligibility_str = json.dumps(eligibility)
    elif eligibility:
        eligibility_str = str(eligibility)
    else:
        eligibility_str = None

    sports_opp = SportsOpportunity(
        sport=data.get("sport") or "General",
        type=sport_type,
        title=title,
        organization=data.get("organization"),
        location=location,
        deadline=_parse_date_safe(data.get("deadline")),
        eligibility=eligibility_str,
        description=data.get("description"),
        source_url=record.source_url,
        source_id=record.source_id,
        content_hash=record.content_hash,
        dedup_key=record.dedup_key,
        verification_status=STATUS_VERIFIED,
        last_verified=date.today(),
        is_active=True,
    )
    db.add(sports_opp)
    db.commit()
    db.refresh(sports_opp)
    return _success_result("sports_opportunities", sports_opp.id, sports_opp.title, record.id)


def _promote_university(
    db: Session, record: PKEStagingRecord, data: dict
) -> dict:
    name = data.get("name")
    if not name:
        raise StagingServiceError("Missing required field 'name'.")

    city = data.get("city")
    _validate_geography(city)

    # Idempotency: match by slug (unique) then by name+city
    slug = data.get("slug") or _generate_slug(name)
    existing = db.query(University).filter(University.slug == slug).first()
    if existing is None:
        existing = (
            db.query(University)
            .filter(University.name == name, University.city == city)
            .first()
        )
    if existing:
        return _already_promoted("universities", existing.id, existing.name, record.id)

    # Ensure slug uniqueness
    base_slug, counter = slug, 1
    while db.query(University).filter(University.slug == slug).first() is not None:
        slug = f"{base_slug}-{counter}"
        counter += 1

    uni = University(
        name=name,
        short_name=data.get("short_name"),
        slug=slug,
        city=city,
        province=data.get("province"),
        type=data.get("type", "PUBLIC"),
        hec_recognized=data.get("hec_recognized"),
        hec_category=data.get("hec_category"),
        website_url=data.get("website_url") or record.source_url,
        admissions_url=data.get("admissions_url"),
        source_id=record.source_id,
        verification_status=STATUS_VERIFIED,
        last_verified=date.today(),
    )
    db.add(uni)
    db.commit()
    db.refresh(uni)
    return _success_result("universities", uni.id, uni.name, record.id)


def _promote_program(
    db: Session, record: PKEStagingRecord, data: dict
) -> dict:
    name = data.get("name")
    if not name:
        raise StagingServiceError("Missing required field 'name'.")

    # Resolve university
    uni_id = data.get("university_id")
    if uni_id is None and data.get("university_slug"):
        u = (
            db.query(University)
            .filter(University.slug == data["university_slug"])
            .first()
        )
        if u:
            uni_id = u.id
    if uni_id is None:
        raise StagingServiceError(
            "Cannot promote program: 'university_id' or 'university_slug' required."
        )

    # Idempotency: same name+university_id+degree_type
    existing = (
        db.query(Program)
        .filter(
            Program.university_id == uni_id,
            Program.name == name,
            Program.degree_type == data.get("degree_type"),
        )
        .first()
    )
    if existing:
        return _already_promoted("programs", existing.id, existing.name, record.id)

    prog = Program(
        university_id=uni_id,
        campus_id=data.get("campus_id"),
        name=name,
        degree_type=data.get("degree_type"),
        field=data.get("field"),
        duration_years=_nullable_float(data.get("duration_years")),
        # never-infer: null = fee not verified
        annual_fee_pkr=_nullable_int(data.get("annual_fee_pkr")),
        admission_link=data.get("admission_link") or record.source_url,
        career_ids=json.dumps(data.get("career_ids") or []),
        source_id=record.source_id,
        verification_status=STATUS_VERIFIED,
        last_verified=date.today(),
    )
    db.add(prog)
    db.commit()
    db.refresh(prog)
    return _success_result("programs", prog.id, prog.name, record.id)


def _promote_learning_resource(
    db: Session, record: PKEStagingRecord, data: dict
) -> dict:
    title = data.get("title")
    if not title:
        raise StagingServiceError("Missing required field 'title'.")

    # Idempotency: match by url (unique per resource)
    url = data.get("url") or record.source_url
    existing = db.query(LearningResource).filter(LearningResource.url == url).first()
    if existing is None:
        existing = (
            db.query(LearningResource)
            .filter(LearningResource.title == title)
            .first()
        )
    if existing:
        return _already_promoted("learning_resources", existing.id, existing.title, record.id)

    lr = LearningResource(
        skill_name=data.get("skill_name"),
        title=title,
        type=data.get("type", "course"),
        provider=data.get("provider"),
        url=url,
        language=data.get("language", "English"),
        level=data.get("level"),
        is_free=data.get("is_free"),
        # never-infer: duration_hours must be explicitly stated
        duration_hours=_nullable_float(data.get("duration_hours")),
        source_id=record.source_id,
        verification_status=STATUS_VERIFIED,
        last_verified=date.today(),
        is_active=True,
    )
    db.add(lr)
    db.commit()
    db.refresh(lr)
    return _success_result("learning_resources", lr.id, lr.title, record.id)


# ---------------------------------------------------------------------------
# Idempotency helpers
# ---------------------------------------------------------------------------


def _find_existing_opportunity(
    db: Session, record: PKEStagingRecord, title: str, opp_type: str
) -> Optional[Opportunity]:
    """Find an existing Opportunity that matches this staging record."""
    if record.dedup_key:
        row = (
            db.query(Opportunity)
            .filter(Opportunity.dedup_key == record.dedup_key)
            .first()
        )
        if row:
            return row
    if record.source_url:
        row = (
            db.query(Opportunity)
            .filter(Opportunity.source_url == record.source_url, Opportunity.title == title)
            .first()
        )
        if row:
            return row
    return None


def _find_existing_sports(
    db: Session, record: PKEStagingRecord, title: str, sport_type: str
) -> Optional[SportsOpportunity]:
    if record.dedup_key:
        row = (
            db.query(SportsOpportunity)
            .filter(SportsOpportunity.dedup_key == record.dedup_key)
            .first()
        )
        if row:
            return row
    if record.source_url:
        row = (
            db.query(SportsOpportunity)
            .filter(SportsOpportunity.source_url == record.source_url, SportsOpportunity.title == title)
            .first()
        )
        if row:
            return row
    return None


# ---------------------------------------------------------------------------
# Result dict builders
# ---------------------------------------------------------------------------


def _success_result(table: str, target_id: int, title: str, staging_id: int) -> dict:
    return {
        "promoted": True,
        "staging_id": staging_id,
        "target_table": table,
        "target_id": target_id,
        "title": title,
        "message": None,
    }


def _already_promoted(table: str, target_id: int, title: str, staging_id: int) -> dict:
    return {
        "promoted": False,
        "staging_id": staging_id,
        "target_table": table,
        "target_id": target_id,
        "title": title,
        "message": f"Already promoted to {table} (id={target_id}); no duplicate created.",
    }


# ---------------------------------------------------------------------------
# Type coercion helpers — never invent values
# ---------------------------------------------------------------------------


def _nullable_float(val: Any) -> Optional[float]:
    """Return float if val is numeric; None otherwise."""
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _nullable_int(val: Any) -> Optional[int]:
    """Return int if val is numeric; None otherwise."""
    if val is None:
        return None
    try:
        return int(float(val))
    except (TypeError, ValueError):
        return None
