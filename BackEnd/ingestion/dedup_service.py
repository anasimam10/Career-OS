"""Deduplication helpers (architecture_master §12, stage 6).

Deterministic normalization + key computation so the same real-world
opportunity posted on two pages (or twice on one page) collapses to a
single database record:

- ``make_content_hash`` — SHA-256 of the raw page content. Unchanged
  hash since the last run means the page did not change (stage 2 skip).
- ``make_dedup_key`` — normalized ``type|title|organization`` triple.
  Case, punctuation, and whitespace differences do not create new
  records.
"""

from __future__ import annotations

import hashlib
import re
from typing import Optional

from sqlalchemy.orm import Session

from models.opportunity import Opportunity

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[^\w\s]")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


def normalize_text(value: Optional[str]) -> str:
    """Lowercase, strip punctuation/tags, collapse whitespace."""
    if not value:
        return ""
    text = _TAG_RE.sub(" ", value)
    text = _PUNCT_RE.sub(" ", text)
    text = _WS_RE.sub(" ", text).strip().lower()
    return text


def make_dedup_key(
    opp_type: Optional[str], title: Optional[str], organization: Optional[str] = None
) -> str:
    """Stable identity key: normalized type|title|organization."""
    type_part = _NON_ALNUM_RE.sub("", (opp_type or "").strip().lower())
    title_part = _NON_ALNUM_RE.sub("", normalize_text(title))
    org_part = _NON_ALNUM_RE.sub("", normalize_text(organization))
    return "|".join((type_part, title_part, org_part))


def make_content_hash(raw_content: str) -> str:
    """SHA-256 hex digest of the raw page content."""
    return hashlib.sha256((raw_content or "").encode("utf-8")).hexdigest()


def find_duplicate(db: Session, dedup_key: str) -> Optional[Opportunity]:
    """An existing opportunity with the same dedup key, if any."""
    if not dedup_key:
        return None
    return (
        db.query(Opportunity)
        .filter(Opportunity.dedup_key == dedup_key)
        .order_by(Opportunity.id)
        .first()
    )


def content_unchanged(db: Session, source_url: str, content_hash: str) -> bool:
    """True when this URL was already retrieved with identical content.

    Uses the sources registry (master §12 stage 2: same hash -> skip
    extraction).
    """
    from models.source import Source

    source = db.query(Source).filter(Source.source_url == source_url).first()
    if source is None or not source.content_hash:
        return False
    return source.content_hash == content_hash
