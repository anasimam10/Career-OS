"""Ingestion service (architecture_master §12).

The eight-stage pipeline for one submitted URL:

  1. DISCOVER      run + items created by run_url_ingestion / refresh_sources
  2. RETRIEVE      HTTP GET (User-Agent, timeout, size cap) -> content hash;
                   unchanged hash since last run -> item UNCHANGED (skip)
  3. EXTRACT       Qwen via the protected ai_service (Pattern A) with the
                   extraction-only prompt; null for anything not stated
  4. VALIDATE      title + a valid type required; deadline must parse as a
                   real date -> CANDIDATE else FAILED with reason
  5. NORMALIZE     map extraction fields onto the DB structure (no skills
                   registry — documented deviation; careers.required_skills
                   JSON is the source of truth)
  6. DEDUPLICATE   dedup_key lookup; duplicates associate the source with
                   the existing record instead of creating a second one
  7. PERSIST       new Opportunity with verification_status='CANDIDATE' —
                   never VERIFIED automatically (§11)
  8. INDEX         SQLite FTS updated by the INSERT triggers installed by
                   retrieval/fts.py (no manual indexing step needed)

Stage 9 (manual admin verification) is exposed separately through
``verify_opportunity``.

Deviations (documented in DONE.md): runs execute synchronously within the
admin request instead of a background task — bounded (max 50 URLs) and
immediately queryable; search-based discovery (mode B) is not implemented
(no Qwen web_search in the protected chain).
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta
from typing import Optional
from urllib.parse import urlparse

import httpx
from sqlalchemy import func
from sqlalchemy.orm import Session

from config import settings
from ingestion.dedup_service import (
    content_unchanged,
    find_duplicate,
    make_content_hash,
    make_dedup_key,
)
from knowledge_engine.extractor import route_extraction, OPPORTUNITY_DOMAINS
from knowledge_engine.staging import PKEStagingRecord
from models.opportunity import Opportunity, SportsOpportunity
from models.source import IngestionItem, IngestionRun, Source, SourceDocument
from services.ai_service import AIValidationError, AIUnavailableError

logger = logging.getLogger("ah_career.ingestion")

# --- bounded pipeline constants -------------------------------------------
MAX_URLS_PER_RUN = 50
MAX_CONTENT_BYTES = 512_000  # 512 KiB raw page cap
FETCH_TIMEOUT_SECONDS = 15.0
USER_AGENT = (
    "AHCareersBot/1.0 (+https://example.com/ah-careers; research use; "
    "contact: admin@ah-careers.example)"
)
REFRESH_STALE_DAYS = 7
MAX_REFRESH_ITEMS = 20
STALE_RECORD_DAYS = 30  # master §10: last_verified older than 30 days

VALID_OPP_TYPES = ("internship", "job", "scholarship", "education")

# Item statuses counted as processed successfully (no new data, but no
# failure either): stored new record, matched an existing duplicate, or
# the page content had not changed since the last run.
_SUCCESS_STATUSES = ("STORED", "DUPLICATE", "UNCHANGED")


class FetchError(Exception):
    """Controlled retrieval failure for one URL (never aborts the run)."""


# ---------------------------------------------------------------------------
# Stage 2 — RETRIEVE
# ---------------------------------------------------------------------------


def _fetch_url(url: str) -> str:
    """HTTP GET one public URL with a User-Agent, timeout, and size cap.

    Raises FetchError with a controlled message on any failure.
    """
    try:
        with httpx.Client(timeout=FETCH_TIMEOUT_SECONDS, follow_redirects=True) as client:
            response = client.get(url, headers={"User-Agent": USER_AGENT})
    except httpx.HTTPError as exc:
        raise FetchError(f"HTTP request failed: {type(exc).__name__}") from exc

    if response.status_code >= 400:
        raise FetchError(f"HTTP {response.status_code} from source")

    if len(response.content) > MAX_CONTENT_BYTES:
        raise FetchError(
            f"content too large ({len(response.content)} bytes > {MAX_CONTENT_BYTES})"
        )
    return response.text


def _classification_for(source_type: str) -> str:
    """Map the source_type taxonomy onto the coarser classification."""
    if source_type.startswith("OFFICIAL"):
        return "OFFICIAL"
    if source_type == "SECONDARY_PORTAL":
        return "SECONDARY"
    if source_type == "SOCIAL":
        return "SOCIAL"
    return "UNKNOWN"


def _upsert_source(
    db: Session, url: str, source_type: str, content_hash: str
) -> Source:
    """Create or update the sources-registry row for one URL."""
    source = db.query(Source).filter(Source.source_url == url).first()
    now = datetime.utcnow()
    if source is None:
        source = Source(
            source_url=url,
            source_type=source_type,
            domain=urlparse(url).netloc or None,
            classification=_classification_for(source_type),
            retrieval_method="direct_fetch",
        )
        db.add(source)
    source.content_hash = content_hash
    source.retrieved_at = now
    db.flush()
    return source


# ---------------------------------------------------------------------------
# Stages 4–5 — VALIDATE + NORMALIZE
# ---------------------------------------------------------------------------


def _validate_extraction(extraction) -> tuple[bool, Optional[str]]:
    """Structural validation (master §12 stage 4).

    Returns (ok, failure_reason). Required: a non-empty title and a valid
    opportunity type; the deadline, when present, must be a real date.
    """
    if not (extraction.title or "").strip():
        return False, "missing required field: title"
    if (extraction.type or "") not in VALID_OPP_TYPES:
        return False, (
            f"invalid type: {extraction.type!r} "
            f"(expected one of {', '.join(VALID_OPP_TYPES)})"
        )
    if extraction.deadline:
        try:
            date.fromisoformat(extraction.deadline)
        except (ValueError, TypeError):
            return False, f"invalid deadline (not a real date): {extraction.deadline!r}"
    return True, None


def _normalize_extraction(extraction) -> dict:
    """Map an extraction onto Opportunity column values (stage 5)."""
    deadline = None
    if getattr(extraction, "deadline", None):
        deadline = date.fromisoformat(extraction.deadline)  # validated already
    skills = None
    req_skills = getattr(extraction, "required_skills", None)
    if req_skills is not None:
        skills = json.dumps([s for s in req_skills if (s or "").strip()])
    
    is_remote_val = getattr(extraction, "is_remote", None)
    is_remote = bool(is_remote_val) if is_remote_val is not None else False
    
    return {
        "type": extraction.type,
        "title": (getattr(extraction, "title", "") or "").strip(),
        "organization": _clean(getattr(extraction, "organization", None)),
        "location": _clean(getattr(extraction, "location", None)),
        "deadline": deadline,
        "required_skills": skills,
        "description": _clean(getattr(extraction, "description", None)),
        "stipend_pkr": getattr(extraction, "stipend_pkr", None),
        "eligibility_notes": _clean(getattr(extraction, "eligibility_notes", None)),
        "is_remote": is_remote,
    }


def _clean(value: Optional[str]) -> Optional[str]:
    """Strip whitespace; empty strings become None (unknown, never guessed)."""
    if value is None:
        return None
    value = value.strip()
    return value or None


# ---------------------------------------------------------------------------
# Per-item pipeline (stages 2–8)
# ---------------------------------------------------------------------------


def _process_item(db: Session, item: IngestionItem, source_type: str, domain: str = "jobs") -> None:
    """Run stages 2–8 for one item. Never raises: failures mark the item."""
    item.started_at = datetime.utcnow()
    try:
        # Stage 2 — RETRIEVE --------------------------------------------
        raw_content = _fetch_url(item.source_url)
        content_hash = make_content_hash(raw_content)

        if content_unchanged(db, item.source_url, content_hash):
            source = db.query(Source).filter(Source.source_url == item.source_url).one()
            source.retrieved_at = datetime.utcnow()
            item.source_id = source.id
            item.status = "UNCHANGED"
            item.completed_at = datetime.utcnow()
            db.commit()
            return

        source = _upsert_source(db, item.source_url, source_type, content_hash)
        document = SourceDocument(
            source_id=source.id,
            raw_content=raw_content,
            content_hash=content_hash,
            processing_status="PENDING",
        )
        db.add(document)
        db.flush()
        item.source_id = source.id
        item.document_id = document.id
        item.status = "RETRIEVED"

        # Stage 3 — EXTRACT ---------------------------------------------
        try:
            extraction = route_extraction(domain, raw_content, item.source_url)
        except (AIUnavailableError, AIValidationError, ValueError) as exc:
            document.processing_status = "FAILED"
            item.status = "FAILED"
            item.error_message = f"extraction failed: {type(exc).__name__} - {exc}"
            item.completed_at = datetime.utcnow()
            db.commit()
            return

        document.extracted_json = extraction.model_dump_json(exclude_none=False)
        document.extraction_model = settings.QWEN_MODEL
        document.extraction_at = datetime.utcnow()
        document.processing_status = "EXTRACTED"
        item.status = "EXTRACTED"

        # Stage 4 — VALIDATE --------------------------------------------
        if domain in OPPORTUNITY_DOMAINS:
            ok, reason = _validate_extraction(extraction)
            if not ok:
                document.processing_status = "FAILED"
                item.status = "FAILED"
                item.error_message = f"validation failed: {reason}"
                item.completed_at = datetime.utcnow()
                db.commit()
                return
        document.processing_status = "VALIDATED"
        item.status = "VALIDATED"

        # Stage 5–7 — NORMALIZE, DEDUPLICATE, PERSIST -------------------
        if domain in OPPORTUNITY_DOMAINS:
            # Legacy Opportunity persistence
            values = _normalize_extraction(extraction)
            dedup_key = make_dedup_key(
                values["type"], values["title"], values["organization"]
            )
            duplicate = find_duplicate(db, dedup_key)
            if duplicate is not None:
                if duplicate.source_id is None:
                    duplicate.source_id = source.id
                    duplicate.retrieved_at = datetime.utcnow()
                item.opportunity_id = duplicate.id
                item.status = "DUPLICATE"
                item.completed_at = datetime.utcnow()
                db.commit()
                return

            opportunity = Opportunity(
                **values,
                source_url=item.source_url,
                is_active=True,
                verification_status="CANDIDATE",
                status="ACTIVE",
                source_id=source.id,
                content_hash=content_hash,
                dedup_key=dedup_key,
                retrieved_at=datetime.utcnow(),
            )
            db.add(opportunity)
            db.flush()
            item.opportunity_id = opportunity.id
        else:
            # PKE Staging persistence for new domains
            staging_record = PKEStagingRecord(
                domain=domain,
                extracted_json=extraction.model_dump_json(exclude_none=False),
                source_url=item.source_url,
                source_id=source.id,
                content_hash=content_hash,
                dedup_key=None,  # basic dedup logic to be added if needed
                verification_status="CANDIDATE"
            )
            db.add(staging_record)
            db.flush()
            # Staging items are technically stored successfully
            
        item.status = "STORED"

        # Stage 8 — INDEX ------------------------------------------------
        # No manual step: the FTS5 INSERT triggers installed by
        # retrieval/fts.py keep the full-text index in sync automatically.

        item.completed_at = datetime.utcnow()
        db.commit()
    except Exception as exc:  # noqa: BLE001 — one item never aborts the run
        db.rollback()
        item.status = "FAILED"
        item.error_message = f"{type(exc).__name__}: {exc}"[:500]
        item.completed_at = datetime.utcnow()
        db.commit()
        logger.warning(
            "Ingestion item %s failed: %s", item.id, item.error_message
        )


# ---------------------------------------------------------------------------
# Run orchestration
# ---------------------------------------------------------------------------


def _create_run(
    db: Session,
    *,
    trigger_type: str,
    urls: list[str],
    source_type: str,
    notes: Optional[str] = None,
) -> IngestionRun:
    run = IngestionRun(
        trigger_type=trigger_type,
        initiated_by="admin",
        status="RUNNING",
        total_items=len(urls),
        notes=notes,
    )
    db.add(run)
    db.flush()
    for url in urls:
        db.add(IngestionItem(run_id=run.id, source_url=url, status="PENDING"))
    db.commit()
    return run


def _finalize_run(db: Session, run: IngestionRun) -> None:
    items = db.query(IngestionItem).filter(IngestionItem.run_id == run.id).all()
    successful = sum(1 for i in items if i.status in _SUCCESS_STATUSES)
    failed = sum(1 for i in items if i.status == "FAILED")
    run.successful_items = successful
    run.failed_items = failed
    run.completed_at = datetime.utcnow()
    if not items:
        run.status = "COMPLETED"
    elif failed == 0:
        run.status = "COMPLETED"
    elif successful == 0:
        run.status = "FAILED"
    else:
        run.status = "PARTIAL"
    db.commit()


def run_url_ingestion(
    db: Session,
    *,
    urls: list[str],
    source_type: str = "UNKNOWN",
    domain: str = "jobs",
    run_label: Optional[str] = None,
) -> dict:
    """Mode A (URL batch): create a run and process every URL (§12)."""
    run = _create_run(
        db,
        trigger_type="url_batch",
        urls=list(urls),
        source_type=source_type,
        notes=run_label,
    )
    items = db.query(IngestionItem).filter(IngestionItem.run_id == run.id).all()
    for item in items:
        _process_item(db, item, source_type, domain)
    _finalize_run(db, run)
    return {"run_id": run.id, "queued_count": len(urls)}


def refresh_sources(
    db: Session,
    *,
    source_type: Optional[str] = None,
    max_items: Optional[int] = None,
) -> dict:
    """Mode C (approved-source refresh): re-fetch stale sources.

    A source is stale when COALESCE(last_verified, retrieved_at) is older
    than REFRESH_STALE_DAYS. Content-hash comparison inside the pipeline
    skips re-extraction for unchanged pages (items become UNCHANGED).
    """
    cutoff = datetime.utcnow() - timedelta(days=REFRESH_STALE_DAYS)
    # Master §12 mode C: stale when COALESCE(last_verified, retrieved_at)
    # is older than 7 days. Sources with neither timestamp (NULL) compare
    # as NULL and are excluded.
    stale_expr = func.coalesce(Source.last_verified, Source.retrieved_at)
    query = db.query(Source).filter(stale_expr < cutoff)
    if source_type:
        query = query.filter(Source.source_type == source_type)

    limit = max_items if max_items is not None else MAX_REFRESH_ITEMS
    stale = query.order_by(Source.retrieved_at).limit(limit).all()
    urls = [s.source_url for s in stale]
    type_by_url = {s.source_url: s.source_type for s in stale}

    run = _create_run(
        db, trigger_type="refresh", urls=urls, source_type=source_type or "MIXED"
    )
    if not urls:
        _finalize_run(db, run)
        return {"run_id": run.id, "queued_count": 0}

    items = db.query(IngestionItem).filter(IngestionItem.run_id == run.id).all()
    for item in items:
        item_type = type_by_url.get(item.source_url, "UNKNOWN")
        _process_item(db, item, item_type, domain="jobs")  # default to jobs for refresh
    _finalize_run(db, run)
    return {"run_id": run.id, "queued_count": len(urls)}


def get_run_status(db: Session, run_id: int) -> Optional[dict]:
    """One run's status with per-item breakdown (master §18)."""
    run = db.get(IngestionRun, run_id)
    if run is None:
        return None
    items = (
        db.query(IngestionItem)
        .filter(IngestionItem.run_id == run_id)
        .order_by(IngestionItem.id)
        .all()
    )
    return {
        "run_id": run.id,
        "status": run.status,
        "total_items": run.total_items,
        "successful_items": run.successful_items,
        "failed_items": run.failed_items,
        "items": [
            {
                "item_id": i.id,
                "source_url": i.source_url,
                "status": i.status,
                "opportunity_id": i.opportunity_id,
                "error_message": i.error_message,
            }
            for i in items
        ],
    }


# ---------------------------------------------------------------------------
# Stage 9 — manual admin verification
# ---------------------------------------------------------------------------


def verify_opportunity(
    db: Session, opportunity_id: int, verification_status: str
) -> Optional[Opportunity]:
    """Mark one CANDIDATE record VALIDATED/VERIFIED (manual, stage 9)."""
    if verification_status not in ("VALIDATED", "VERIFIED"):
        raise ValueError("verification_status must be VALIDATED or VERIFIED")
    record = db.get(Opportunity, opportunity_id)
    if record is None:
        return None
    record.verification_status = verification_status
    record.last_verified = date.today()
    db.commit()
    db.refresh(record)
    return record


# ---------------------------------------------------------------------------
# Data quality dashboard (master §17)
# ---------------------------------------------------------------------------


def data_quality(db: Session) -> dict:
    """Snapshot counts for the admin data-quality endpoint."""
    total_sources = db.query(Source).count()
    verified_sources = (
        db.query(Source)
        .filter(Source.verification_status.in_(("VALIDATED", "VERIFIED")))
        .count()
    )
    candidate_records = (
        db.query(Opportunity).filter(Opportunity.verification_status == "CANDIDATE").count()
        + db.query(SportsOpportunity)
        .filter(SportsOpportunity.verification_status == "CANDIDATE")
        .count()
    )
    stale_cutoff = date.today() - timedelta(days=STALE_RECORD_DAYS)
    stale_records = (
        db.query(Opportunity)
        .filter(
            Opportunity.is_active.is_(True),
            Opportunity.last_verified.isnot(None),
            Opportunity.last_verified < stale_cutoff,
        )
        .count()
    )
    expired_opportunities = (
        db.query(Opportunity)
        .filter(
            Opportunity.is_active.is_(True),
            Opportunity.deadline.isnot(None),
            Opportunity.deadline < date.today(),
        )
        .count()
    )
    last_run = (
        db.query(IngestionRun).order_by(IngestionRun.id.desc()).first()
    )
    recent_run_summary = None
    if last_run is not None:
        recent_run_summary = {
            "run_id": last_run.id,
            "trigger_type": last_run.trigger_type,
            "status": last_run.status,
            "total_items": last_run.total_items,
            "successful_items": last_run.successful_items,
            "failed_items": last_run.failed_items,
        }
    return {
        "total_sources": total_sources,
        "verified_sources": verified_sources,
        "candidate_records": candidate_records,
        "stale_records": stale_records,
        "expired_opportunities": expired_opportunities,
        "recent_run_summary": recent_run_summary,
    }
