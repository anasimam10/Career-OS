"""Provenance and ingestion models (architecture_master §10–§12).

- Source: provenance registry for every externally sourced record
- SourceDocument: raw retrieved content + Qwen extraction output (never truth)
- IngestionRun / IngestionItem: admin-initiated batch tracking

Records created through ingestion always start as CANDIDATE — a model
output is NEVER automatically VERIFIED (architecture §11).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_url: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    source_name: Mapped[str | None] = mapped_column(String, nullable=True)
    # OFFICIAL_GOVERNMENT / OFFICIAL_UNIVERSITY / OFFICIAL_COMPANY /
    # OFFICIAL_SPORTS / SECONDARY_PORTAL / SOCIAL / UNKNOWN (architecture §11)
    source_type: Mapped[str] = mapped_column(String, nullable=False, default="UNKNOWN")
    domain: Mapped[str | None] = mapped_column(String, nullable=True)
    classification: Mapped[str | None] = mapped_column(String, nullable=True)  # OFFICIAL/SECONDARY/SOCIAL/UNKNOWN
    retrieval_method: Mapped[str | None] = mapped_column(String, nullable=True)  # direct_fetch/web_search/api/manual
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_verified: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String, nullable=True)  # SHA256 of last content
    verification_status: Mapped[str] = mapped_column(String, default="DISCOVERED")
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0.0–1.0
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class SourceDocument(Base):
    __tablename__ = "source_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sources.id"), nullable=False
    )
    raw_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # Qwen output, NOT truth
    extraction_model: Mapped[str | None] = mapped_column(String, nullable=True)
    extraction_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String, nullable=True)  # SHA256 of raw_content
    processing_status: Mapped[str] = mapped_column(String, default="PENDING")  # PENDING/EXTRACTED/VALIDATED/FAILED


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trigger_type: Mapped[str | None] = mapped_column(String, nullable=True)  # url_batch/search/refresh/manual
    initiated_by: Mapped[str | None] = mapped_column(String, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String, default="RUNNING")  # RUNNING/COMPLETED/FAILED/PARTIAL
    total_items: Mapped[int] = mapped_column(Integer, default=0)
    successful_items: Mapped[int] = mapped_column(Integer, default=0)
    failed_items: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class IngestionItem(Base):
    __tablename__ = "ingestion_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ingestion_runs.id"), nullable=False
    )
    source_url: Mapped[str] = mapped_column(String, nullable=False)
    # PENDING/RETRIEVED/EXTRACTED/VALIDATED/STORED/FAILED/DUPLICATE
    status: Mapped[str] = mapped_column(String, default="PENDING")
    source_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    document_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    opportunity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
