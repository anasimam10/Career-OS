"""Ingestion subsystem (architecture_master §12).

Eight-stage web-ingestion pipeline plus dedup helpers. Every record
created here starts as CANDIDATE and is never automatically VERIFIED —
student visibility is granted only by the manual stage-9 admin step.
"""

from ingestion.dedup_service import (
    find_duplicate,
    make_content_hash,
    make_dedup_key,
    normalize_text,
)
from ingestion.extraction_service import extract_opportunity
from ingestion.ingestion_service import (
    data_quality,
    get_run_status,
    refresh_sources,
    run_url_ingestion,
    verify_opportunity,
)

__all__ = [
    "extract_opportunity",
    "find_duplicate",
    "make_content_hash",
    "make_dedup_key",
    "normalize_text",
    "data_quality",
    "get_run_status",
    "refresh_sources",
    "run_url_ingestion",
    "verify_opportunity",
]
