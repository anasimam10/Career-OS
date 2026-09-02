"""
Pakistan Knowledge Engine — Source Registry Service (PKE §6/§7).

CRUD helpers for the ``pke_sources`` table:
  - create_source        add a new source entry (validates required fields)
  - get_source           fetch by source_id string
  - get_source_by_id     fetch by integer PK
  - list_sources         filtered listing
  - update_access_status set the access_review_status for one source
  - source_to_dict       serialize to a plain dict

Access rules enforced here (PKE §7):
  - Only sources with access_review_status == "APPROVED" are returned by
    ``list_approved_sources``; every other query surface is admin-only.
  - L2/L3/L4 sources default to PENDING_REVIEW; an explicit operator action
    is required to move them to APPROVED or MANUAL_ONLY.
  - The service never fetches or scrapes any source — it only manages the
    registry metadata.
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Optional

from sqlalchemy.orm import Session

from knowledge_engine.pke_source_registry import PKESource

logger = logging.getLogger("ah_career.knowledge_engine.source_registry")

# Valid values for each enum-style column
VALID_AUTHORITY_LEVELS = {"L1", "L2", "L3", "L4"}
VALID_SOURCE_TYPES = {
    "OFFICIAL_GOVERNMENT",
    "OFFICIAL_UNIVERSITY",
    "OFFICIAL_COMPANY",
    "OFFICIAL_SPORTS",
    "SECONDARY_PORTAL",
    "PUBLIC_DATASET",
    "SOCIAL",
    "UNKNOWN",
}
VALID_DOMAINS = {
    "schools",
    "colleges",
    "universities",
    "programs",
    "scholarships",
    "internships",
    "jobs",
    "sports",
    "tournaments",
    "trials",
    "learning_resources",
    "careers",
}
VALID_GEOGRAPHIC_SCOPES = {"karachi", "lahore", "islamabad", "nationwide", "online"}
VALID_ACCESS_STATUSES = {
    "PENDING_REVIEW",
    "APPROVED",
    "MANUAL_ONLY",
    "DISCOVERY_ONLY",
    "BLOCKED",
}
VALID_RETRIEVAL_METHODS = {
    "direct_fetch",
    "html_table",
    "csv_import",
    "json_api",
    "hf_dataset",
    "manual",
    None,
}


class SourceRegistryError(ValueError):
    """Raised when a source registry operation fails validation."""


def _validate_source_fields(
    *,
    source_id: str,
    name: str,
    base_url: str,
    authority_level: str,
    source_type: str,
    domains: str,
    geographic_scope: str,
    access_review_status: str,
    retrieval_method: Optional[str],
    source_confidence: Optional[int],
) -> None:
    """Raise SourceRegistryError if any field value is invalid."""
    if not source_id or not source_id.strip():
        raise SourceRegistryError("source_id must be a non-empty string.")
    if not name or not name.strip():
        raise SourceRegistryError("name must be a non-empty string.")
    if not base_url or not base_url.strip().startswith(("http://", "https://")):
        raise SourceRegistryError("base_url must be a valid http(s) URL.")
    if authority_level not in VALID_AUTHORITY_LEVELS:
        raise SourceRegistryError(
            f"authority_level must be one of {sorted(VALID_AUTHORITY_LEVELS)}."
        )
    if source_type not in VALID_SOURCE_TYPES:
        raise SourceRegistryError(
            f"source_type must be one of {sorted(VALID_SOURCE_TYPES)}."
        )
    # Validate each domain in the comma-separated string
    domain_list = [d.strip() for d in domains.split(",") if d.strip()]
    if not domain_list:
        raise SourceRegistryError("domains must contain at least one valid domain name.")
    invalid = [d for d in domain_list if d not in VALID_DOMAINS]
    if invalid:
        raise SourceRegistryError(
            f"Unknown domains: {invalid}. Valid values: {sorted(VALID_DOMAINS)}."
        )
    if geographic_scope not in VALID_GEOGRAPHIC_SCOPES:
        raise SourceRegistryError(
            f"geographic_scope must be one of {sorted(VALID_GEOGRAPHIC_SCOPES)}."
        )
    if access_review_status not in VALID_ACCESS_STATUSES:
        raise SourceRegistryError(
            f"access_review_status must be one of {sorted(VALID_ACCESS_STATUSES)}."
        )
    if retrieval_method not in VALID_RETRIEVAL_METHODS:
        raise SourceRegistryError(
            f"retrieval_method must be one of {sorted(str(v) for v in VALID_RETRIEVAL_METHODS)}."
        )
    if source_confidence is not None and not (0 <= source_confidence <= 100):
        raise SourceRegistryError("source_confidence must be an integer between 0 and 100.")


def create_source(
    db: Session,
    *,
    source_id: str,
    name: str,
    base_url: str,
    authority_level: str = "L1",
    source_type: str = "UNKNOWN",
    domains: str,
    geographic_scope: str,
    access_review_status: str = "PENDING_REVIEW",
    retrieval_method: Optional[str] = None,
    has_official_api: bool = False,
    is_reachable: Optional[bool] = None,
    last_checked: Optional[date] = None,
    source_confidence: Optional[int] = None,
    notes: Optional[str] = None,
    tos_review_url: Optional[str] = None,
) -> PKESource:
    """Create a new PKE source registry entry (validated, never overwrites).

    Raises SourceRegistryError when fields are invalid.
    Raises SourceRegistryError when source_id already exists.
    """
    source_id = source_id.strip()
    _validate_source_fields(
        source_id=source_id,
        name=name.strip(),
        base_url=base_url.strip(),
        authority_level=authority_level,
        source_type=source_type,
        domains=domains,
        geographic_scope=geographic_scope,
        access_review_status=access_review_status,
        retrieval_method=retrieval_method,
        source_confidence=source_confidence,
    )
    existing = db.query(PKESource).filter(PKESource.source_id == source_id).first()
    if existing is not None:
        raise SourceRegistryError(
            f"Source '{source_id}' already exists in the registry."
        )
    entry = PKESource(
        source_id=source_id,
        name=name.strip(),
        base_url=base_url.strip(),
        authority_level=authority_level,
        source_type=source_type,
        domains=domains,
        geographic_scope=geographic_scope,
        access_review_status=access_review_status,
        retrieval_method=retrieval_method,
        has_official_api=has_official_api,
        is_reachable=is_reachable,
        last_checked=last_checked,
        source_confidence=source_confidence,
        notes=notes,
        tos_review_url=tos_review_url,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    logger.info("PKE source registered: %s (%s)", source_id, access_review_status)
    return entry


def get_source(db: Session, source_id: str) -> Optional[PKESource]:
    """Return the PKESource matching the given source_id string, or None."""
    return (
        db.query(PKESource)
        .filter(PKESource.source_id == source_id.strip())
        .first()
    )


def get_source_by_pk(db: Session, pk: int) -> Optional[PKESource]:
    """Return the PKESource by integer primary key, or None."""
    return db.get(PKESource, pk)


def list_sources(
    db: Session,
    *,
    authority_level: Optional[str] = None,
    source_type: Optional[str] = None,
    domain: Optional[str] = None,
    geographic_scope: Optional[str] = None,
    access_review_status: Optional[str] = None,
) -> list[PKESource]:
    """Return all PKE sources matching the given filters.

    All filters are AND-combined and optional. Pass no filters to list all.
    """
    q = db.query(PKESource)
    if authority_level:
        q = q.filter(PKESource.authority_level == authority_level)
    if source_type:
        q = q.filter(PKESource.source_type == source_type)
    if domain:
        # LIKE-based substring match on the comma-separated domains column
        q = q.filter(PKESource.domains.contains(domain))
    if geographic_scope:
        q = q.filter(PKESource.geographic_scope == geographic_scope)
    if access_review_status:
        q = q.filter(PKESource.access_review_status == access_review_status)
    return q.order_by(PKESource.source_id).all()


def list_approved_sources(
    db: Session,
    *,
    domain: Optional[str] = None,
    geographic_scope: Optional[str] = None,
) -> list[PKESource]:
    """Return sources approved for automated ingestion (PKE §7 rule)."""
    return list_sources(
        db,
        domain=domain,
        geographic_scope=geographic_scope,
        access_review_status="APPROVED",
    )


def update_access_status(
    db: Session,
    source_id: str,
    new_status: str,
    *,
    tos_review_url: Optional[str] = None,
    notes: Optional[str] = None,
    is_reachable: Optional[bool] = None,
    last_checked: Optional[date] = None,
) -> PKESource:
    """Update the access_review_status and related audit fields for one source.

    Raises SourceRegistryError when source_id is not found or status is invalid.
    """
    if new_status not in VALID_ACCESS_STATUSES:
        raise SourceRegistryError(
            f"access_review_status must be one of {sorted(VALID_ACCESS_STATUSES)}."
        )
    entry = get_source(db, source_id)
    if entry is None:
        raise SourceRegistryError(
            f"Source '{source_id}' not found in the registry."
        )
    entry.access_review_status = new_status
    entry.updated_at = datetime.utcnow()
    if tos_review_url is not None:
        entry.tos_review_url = tos_review_url
    if notes is not None:
        entry.notes = notes
    if is_reachable is not None:
        entry.is_reachable = is_reachable
    if last_checked is not None:
        entry.last_checked = last_checked
    db.commit()
    db.refresh(entry)
    logger.info(
        "PKE source %r access status updated to %r", source_id, new_status
    )
    return entry


def source_to_dict(entry: PKESource) -> dict:
    """Serialize a PKESource to a plain dict for API responses / MCP tools."""
    return {
        "id": entry.id,
        "source_id": entry.source_id,
        "name": entry.name,
        "base_url": entry.base_url,
        "authority_level": entry.authority_level,
        "source_type": entry.source_type,
        "domains": entry.domain_list,
        "geographic_scope": entry.geographic_scope,
        "access_review_status": entry.access_review_status,
        "is_approved_for_ingestion": entry.is_approved_for_ingestion,
        "retrieval_method": entry.retrieval_method,
        "has_official_api": entry.has_official_api,
        "is_reachable": entry.is_reachable,
        "last_checked": entry.last_checked.isoformat() if entry.last_checked else None,
        "confidence": entry.confidence_float,
        "notes": entry.notes,
        "tos_review_url": entry.tos_review_url,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
        "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
    }
