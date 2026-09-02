"""
Admin + ingestion schemas (architecture_master §12/§17/§18).

- OpportunityExtraction: the ONLY schema Qwen's extraction output ever
  populates. Every field is optional because "not explicitly stated"
  must serialize as null (master §12) — required-ness is enforced later
  by the VALIDATE stage, which marks the item FAILED when the minimum
  (title + a valid type) is missing.
- Ingestion request bodies and IngestionRunStatus (master §18) for the
  /api/v1/admin/* endpoints.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Qwen extraction output (master §12)
# ---------------------------------------------------------------------------


class OpportunityExtraction(BaseModel):
    """One opportunity extracted from a web page. Null = not stated."""

    type: Optional[str] = None  # internship/job/scholarship/education
    title: Optional[str] = None
    organization: Optional[str] = None
    location: Optional[str] = None
    deadline: Optional[str] = None  # YYYY-MM-DD, explicitly stated only
    required_skills: Optional[list[str]] = None
    description: Optional[str] = None
    stipend_pkr: Optional[int] = None  # explicitly stated only
    eligibility_notes: Optional[str] = None
    is_remote: Optional[bool] = None


# ---------------------------------------------------------------------------
# Admin request bodies (master §17)
# ---------------------------------------------------------------------------


class IngestUrlRequest(BaseModel):
    """POST /admin/ingest/url — URL batch discovery (mode A)."""

    urls: list[str] = Field(min_length=1, max_length=50)
    source_type: str = "UNKNOWN"  # OFFICIAL_*/SECONDARY_PORTAL/SOCIAL/UNKNOWN
    domain: Optional[str] = "jobs"  # Which PKE domain to extract (default: jobs)
    run_label: Optional[str] = None


class IngestRefreshRequest(BaseModel):
    """POST /admin/ingest/refresh — approved-source refresh (mode C)."""

    source_type: Optional[str] = None
    max_items: Optional[int] = Field(default=None, ge=1, le=50)


class VerifyOpportunityRequest(BaseModel):
    """POST /admin/opportunities/{id}/verify — stage 9 manual verification."""

    verification_status: Literal["VALIDATED", "VERIFIED"]


# ---------------------------------------------------------------------------
# Admin responses (master §17/§18)
# ---------------------------------------------------------------------------


class IngestQueuedResponse(BaseModel):
    """Response for the ingestion trigger endpoints."""

    run_id: int
    queued_count: int


class IngestionRunStatus(BaseModel):
    """GET /admin/ingest/runs/{id} (master §18)."""

    run_id: int
    status: str
    total_items: int
    successful_items: int
    failed_items: int
    items: list[dict]


class DataQualityResponse(BaseModel):
    """GET /admin/data-quality (master §17)."""

    total_sources: int
    verified_sources: int
    candidate_records: int
    stale_records: int
    expired_opportunities: int
    recent_run_summary: Optional[dict] = None


class VerifiedOpportunityResponse(BaseModel):
    """POST /admin/opportunities/{id}/verify result summary."""

    id: int
    title: str
    verification_status: str
    last_verified: Optional[str] = None


# ---------------------------------------------------------------------------
# PKE Staging schemas (Step 5)
# ---------------------------------------------------------------------------


class StagingRecordReviewRequest(BaseModel):
    """POST /admin/pke/staging/{id}/review body."""

    action: Literal["VERIFY", "REJECT", "RESET"]
    reviewer_notes: Optional[str] = None


class StagingRecordResponse(BaseModel):
    """PKE Staging Record representation."""

    id: int
    domain: str
    extracted_json: str
    source_url: str
    source_id: Optional[int] = None
    content_hash: Optional[str] = None
    dedup_key: Optional[str] = None
    verification_status: str
    created_at: str


class StagingListResponse(BaseModel):
    """GET /admin/pke/staging response."""

    total: int
    skip: int
    limit: int
    items: list[StagingRecordResponse]


class StagingPromoteResponse(BaseModel):
    """POST /admin/pke/staging/{id}/promote response."""

    promoted: bool
    staging_id: int
    target_table: Optional[str] = None
    target_id: Optional[int] = None
    title: Optional[str] = None
    message: Optional[str] = None

