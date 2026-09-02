"""
Admin router — ingestion + data quality (architecture_master §12/§17).

Admin/developer only. No student-facing endpoint can trigger ingestion;
these routes are the single write path into the sources/opportunities
tables (§26 ingestion security).

Authentication (§17/§26): every route requires
``Authorization: Bearer <ADMIN_TOKEN>``. The comparison is constant-time
and FAIL-CLOSED — when ADMIN_TOKEN is unset, every request is rejected
with 401. Routes are hidden from the public Swagger UI.
"""

from __future__ import annotations

import secrets
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from ingestion import ingestion_service
from knowledge_engine import staging_service
from schemas.admin import (
    DataQualityResponse,
    IngestQueuedResponse,
    IngestRefreshRequest,
    IngestUrlRequest,
    IngestionRunStatus,
    StagingListResponse,
    StagingPromoteResponse,
    StagingRecordResponse,
    StagingRecordReviewRequest,
    VerifiedOpportunityResponse,
    VerifyOpportunityRequest,
)

router = APIRouter(tags=["admin"], include_in_schema=False)

MAX_URLS_PER_REQUEST = 50


def require_admin(authorization: Optional[str] = Header(default=None)) -> None:
    """Bearer-token gate for every /admin route (fail-closed)."""
    expected = settings.ADMIN_TOKEN or ""
    # Fail closed: an unset ADMIN_TOKEN rejects everything (the empty
    # string never matches a real "Bearer <token>" header).
    if not expected:
        raise HTTPException(status_code=401, detail="Unauthorized")

    supplied = ""
    if authorization:
        parts = authorization.split(None, 1)
        if len(parts) == 2 and parts[0].lower() == "bearer":
            supplied = parts[1].strip()
    if not supplied or not secrets.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="Unauthorized")


def _valid_url(url: str) -> bool:
    return url.strip().startswith(("http://", "https://")) and len(url.strip()) <= 2000


# ---------------------------------------------------------------------------
# Ingestion triggers (master §12 modes A and C)
# ---------------------------------------------------------------------------


@router.post(
    "/admin/ingest/url",
    response_model=IngestQueuedResponse,
    dependencies=[Depends(require_admin)],
)
def ingest_urls(
    request: IngestUrlRequest, db: Session = Depends(get_db)
) -> IngestQueuedResponse | JSONResponse:
    """Mode A — submit a batch of URLs (max 50) for ingestion."""
    urls = [u.strip() for u in request.urls if u and u.strip()]
    invalid = [u for u in urls if not _valid_url(u)]
    if invalid:
        return JSONResponse(
            status_code=422,
            content={
                "error": (
                    "Every URL must be a valid http(s) URL "
                    f"(max {MAX_URLS_PER_REQUEST} per request)."
                )
            },
        )
    if len(urls) > MAX_URLS_PER_REQUEST:
        return JSONResponse(
            status_code=422,
            content={
                "error": f"Too many URLs: {len(urls)} > {MAX_URLS_PER_REQUEST}."
            },
        )
    result = ingestion_service.run_url_ingestion(
        db,
        urls=urls,
        source_type=request.source_type,
        run_label=request.run_label,
    )
    return IngestQueuedResponse(**result)


@router.post(
    "/admin/ingest/refresh",
    response_model=IngestQueuedResponse,
    dependencies=[Depends(require_admin)],
)
def ingest_refresh(
    request: IngestRefreshRequest, db: Session = Depends(get_db)
) -> IngestQueuedResponse:
    """Mode C — re-fetch stale sources (older than 7 days)."""
    result = ingestion_service.refresh_sources(
        db, source_type=request.source_type, max_items=request.max_items
    )
    return IngestQueuedResponse(**result)


@router.get(
    "/admin/ingest/runs/{run_id}",
    response_model=IngestionRunStatus,
    dependencies=[Depends(require_admin)],
)
def get_ingestion_run(
    run_id: int, db: Session = Depends(get_db)
) -> IngestionRunStatus | JSONResponse:
    """One ingestion run with per-item statuses."""
    status = ingestion_service.get_run_status(db, run_id)
    if status is None:
        return JSONResponse(
            status_code=404,
            content={"error": f"Ingestion run {run_id} not found"},
        )
    return IngestionRunStatus(**status)


# ---------------------------------------------------------------------------
# Data quality (master §17)
# ---------------------------------------------------------------------------


@router.get(
    "/admin/data-quality",
    response_model=DataQualityResponse,
    dependencies=[Depends(require_admin)],
)
def get_data_quality(db: Session = Depends(get_db)) -> DataQualityResponse:
    """Snapshot of source/record quality counters for the admin dashboard."""
    return DataQualityResponse(**ingestion_service.data_quality(db))


# ---------------------------------------------------------------------------
# Stage 9 — manual verification (master §12)
# ---------------------------------------------------------------------------


@router.post(
    "/admin/opportunities/{opportunity_id}/verify",
    response_model=VerifiedOpportunityResponse,
    dependencies=[Depends(require_admin)],
)
def verify_opportunity(
    opportunity_id: int,
    request: VerifyOpportunityRequest,
    db: Session = Depends(get_db),
) -> VerifiedOpportunityResponse | JSONResponse:
    """Mark a CANDIDATE record VALIDATED or VERIFIED (manual review)."""
    record = ingestion_service.verify_opportunity(
        db, opportunity_id, request.verification_status
    )
    if record is None:
        return JSONResponse(
            status_code=404,
            content={"error": f"Opportunity {opportunity_id} not found"},
        )
    return VerifiedOpportunityResponse(
        id=record.id,
        title=record.title,
        verification_status=record.verification_status,
        last_verified=record.last_verified.isoformat()
        if record.last_verified
        else None,
    )


# ---------------------------------------------------------------------------
# PKE Staging endpoints (Step 5)
# ---------------------------------------------------------------------------


def _staging_to_response(item) -> StagingRecordResponse:
    return StagingRecordResponse(
        id=item.id,
        domain=item.domain,
        extracted_json=item.extracted_json,
        source_url=item.source_url,
        source_id=item.source_id,
        content_hash=item.content_hash,
        dedup_key=item.dedup_key,
        verification_status=item.verification_status,
        created_at=item.created_at.isoformat() if item.created_at else "",
    )


@router.get(
    "/admin/pke/staging",
    response_model=StagingListResponse,
    dependencies=[Depends(require_admin)],
)
def list_pke_staging(
    domain: Optional[str] = None,
    verification_status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> StagingListResponse:
    """List candidate staging records with optional domain/status filters."""
    items, total = staging_service.list_staging_records(
        db,
        domain=domain,
        status=verification_status,
        skip=skip,
        limit=limit,
    )
    return StagingListResponse(
        total=total,
        skip=skip,
        limit=limit,
        items=[_staging_to_response(it) for it in items],
    )


@router.get(
    "/admin/pke/staging/{record_id}",
    response_model=StagingRecordResponse,
    dependencies=[Depends(require_admin)],
)
def get_pke_staging_record(
    record_id: int,
    db: Session = Depends(get_db),
) -> StagingRecordResponse | JSONResponse:
    """Get a single staging record by ID."""
    item = staging_service.get_staging_record(db, record_id)
    if item is None:
        return JSONResponse(
            status_code=404,
            content={"error": f"Staging record {record_id} not found"},
        )
    return _staging_to_response(item)


@router.post(
    "/admin/pke/staging/{record_id}/review",
    response_model=StagingRecordResponse,
    dependencies=[Depends(require_admin)],
)
def review_pke_staging_record(
    record_id: int,
    request: StagingRecordReviewRequest,
    db: Session = Depends(get_db),
) -> StagingRecordResponse | JSONResponse:
    """Review a staging record (VERIFY, REJECT, RESET)."""
    try:
        updated = staging_service.review_staging_record(
            db, record_id, request.action, request.reviewer_notes
        )
    except staging_service.StagingServiceError as exc:
        return JSONResponse(
            status_code=400,
            content={"error": str(exc)},
        )
    return _staging_to_response(updated)


@router.post(
    "/admin/pke/staging/{record_id}/promote",
    response_model=StagingPromoteResponse,
    dependencies=[Depends(require_admin)],
)
def promote_pke_staging_record(
    record_id: int,
    db: Session = Depends(get_db),
) -> StagingPromoteResponse | JSONResponse:
    """Promote a VERIFIED staging record into its operational table."""
    try:
        result = staging_service.promote_staging_record(db, record_id)
    except staging_service.StagingServiceError as exc:
        return JSONResponse(
            status_code=400,
            content={"error": str(exc)},
        )
    return StagingPromoteResponse(**result)

