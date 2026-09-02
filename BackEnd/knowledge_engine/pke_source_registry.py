"""
Pakistan Knowledge Engine — PKE Source Registry model (PKE §6).

This table holds the CURATED, pre-approved source definitions that drive
the PKE ingestion pipeline. It is distinct from the existing operational
``sources`` table (which tracks fetch provenance per URL) in that it is
a higher-level registry — one row per named data source (e.g.
"HEC Recognised Universities"), not per fetched URL.

Authority levels match PKE §5:
  L1 — PRIMARY/OFFICIAL  (government, HEC, official institution/federation)
  L2 — TRUSTED SECONDARY (established aggregator platforms)
  L3 — COMMUNITY/SOCIAL  (official social accounts — discovery only)
  L4 — DISCOVERY ONLY    (aggregator blogs, listicles — never direct-to-prod)

Geographic scope values:
  karachi / lahore / islamabad / nationwide / online

Access review status (MUST be set before any automated fetch):
  PENDING_REVIEW   — robots.txt / ToS not yet reviewed (default for L2+)
  APPROVED         — reviewed and approved for automated fetch
  MANUAL_ONLY      — reviewed; manual import only (no automated fetch)
  DISCOVERY_ONLY   — may be used to discover candidate URLs; never direct ingest
  BLOCKED          — ToS prohibits access; never fetch
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class PKESource(Base):
    """Curated PKE source registry entry (one row per named data source).

    Fields map 1-to-1 onto PKE §6 and §7; constraints match §5 authority
    levels and §7 access rules. Every field that is NOT known is NULL
    (never guessed).
    """

    __tablename__ = "pke_sources"

    # -----------------------------------------------------------------------
    # Identity
    # -----------------------------------------------------------------------

    def __init__(self, **kwargs):
        kwargs.setdefault("authority_level", "L1")
        kwargs.setdefault("source_type", "UNKNOWN")
        kwargs.setdefault("access_review_status", "PENDING_REVIEW")
        kwargs.setdefault("has_official_api", False)
        super().__init__(**kwargs)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Human-readable source identifier matching PKE §6 notation
    # e.g. "GOV-HEC-02", "UNI-KHI-01", "JOB-ROZEE-01"
    source_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

    # Display name — matches the organization name in PKE §6 tables
    name: Mapped[str] = mapped_column(String(256), nullable=False)

    # Primary entry-point URL for this source (canonical, not per-page)
    base_url: Mapped[str] = mapped_column(String(512), nullable=False)

    # -----------------------------------------------------------------------
    # Classification (PKE §5 authority levels)
    # -----------------------------------------------------------------------

    # L1 / L2 / L3 / L4  (see module docstring)
    authority_level: Mapped[str] = mapped_column(String(4), nullable=False, default="L1")

    # Finer-grained source type (mirrors the existing Source.source_type taxonomy)
    # OFFICIAL_GOVERNMENT / OFFICIAL_UNIVERSITY / OFFICIAL_COMPANY /
    # OFFICIAL_SPORTS / SECONDARY_PORTAL / PUBLIC_DATASET / SOCIAL / UNKNOWN
    source_type: Mapped[str] = mapped_column(String(64), nullable=False, default="UNKNOWN")

    # -----------------------------------------------------------------------
    # Domain coverage (which PKE domains this source feeds into)
    # -----------------------------------------------------------------------

    # Comma-separated PKE domain names, e.g. "universities,programs"
    # Valid values: schools / colleges / universities / programs / scholarships /
    #               internships / jobs / sports / tournaments / trials /
    #               learning_resources / careers
    domains: Mapped[str] = mapped_column(String(256), nullable=False)

    # -----------------------------------------------------------------------
    # Geographic scope
    # -----------------------------------------------------------------------

    # karachi / lahore / islamabad / nationwide / online
    # Use "nationwide" only when the source genuinely covers all three cities.
    # "online" = no physical city scope (e.g. DigiSkills).
    geographic_scope: Mapped[str] = mapped_column(String(64), nullable=False)

    # -----------------------------------------------------------------------
    # Access & legal status (PKE §7)
    # -----------------------------------------------------------------------

    # PENDING_REVIEW / APPROVED / MANUAL_ONLY / DISCOVERY_ONLY / BLOCKED
    # DEFAULT is PENDING_REVIEW so new rows are never silently auto-crawled.
    access_review_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="PENDING_REVIEW"
    )

    # How ingestion should fetch from this source when access is APPROVED.
    # direct_fetch / html_table / csv_import / json_api / hf_dataset / manual
    retrieval_method: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # True when this source has an official/public API or data feed.
    has_official_api: Mapped[bool] = mapped_column(Boolean, default=False)

    # -----------------------------------------------------------------------
    # Verification & trust
    # -----------------------------------------------------------------------

    # True if the URL was reachable and topically correct at last_checked.
    is_reachable: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Date the source URL and ToS status were last manually verified.
    last_checked: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Confidence in the data produced by this source: stored as int 0-100.
    # L1 sources typically carry 90+; L2 carry 70-85.
    source_confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # -----------------------------------------------------------------------
    # Descriptive / operational notes
    # -----------------------------------------------------------------------

    # Free-text notes matching PKE §6 table "Notes" column.
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Link to the ToS / robots.txt review record when it exists.
    tos_review_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # -----------------------------------------------------------------------
    # Audit
    # -----------------------------------------------------------------------

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    @property
    def confidence_float(self) -> float | None:
        """Return confidence as 0.0–1.0 (stored as integer 0–100)."""
        if self.source_confidence is None:
            return None
        return self.source_confidence / 100.0

    @property
    def domain_list(self) -> list[str]:
        """Return domains as a list of strings."""
        return [d.strip() for d in (self.domains or "").split(",") if d.strip()]

    @property
    def is_approved_for_ingestion(self) -> bool:
        """True when automated ingestion is allowed for this source."""
        return self.access_review_status == "APPROVED"

    def __repr__(self) -> str:
        return (
            f"<PKESource {self.source_id!r} {self.authority_level} "
            f"scope={self.geographic_scope!r} access={self.access_review_status!r}>"
        )
