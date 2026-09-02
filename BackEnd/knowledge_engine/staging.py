"""
Pakistan Knowledge Engine — Staging Records Model (Step 3).

A generic staging table for new PKE domains (e.g. schools, colleges,
tournaments) that do not yet have corresponding operational tables.
This ensures extracted candidate records are safely stored without
polluting the production schema, fulfilling the safety requirement
that extracted data never becomes automatically verified.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class PKEStagingRecord(Base):
    """Generic staging table for extracted candidate records.
    
    Stores the raw JSON extracted by Qwen for any PKE domain, ensuring
    it is strictly partitioned as CANDIDATE data (never VERIFIED).
    """

    __tablename__ = "pke_staging_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # The PKE domain (e.g. "schools", "colleges", "tournaments")
    domain: Mapped[str] = mapped_column(String(64), nullable=False)
    
    # The Pydantic model serialized to JSON
    extracted_json: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Provenance tracking (required by architecture §10)
    source_url: Mapped[str] = mapped_column(String(512), nullable=False)
    source_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    
    # Simple deduplication key based on the extracted fields
    dedup_key: Mapped[str | None] = mapped_column(String(256), nullable=True)
    
    # Always "CANDIDATE" by default
    verification_status: Mapped[str] = mapped_column(String(32), default="CANDIDATE")
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<PKEStagingRecord id={self.id} domain={self.domain!r} status={self.verification_status!r}>"
