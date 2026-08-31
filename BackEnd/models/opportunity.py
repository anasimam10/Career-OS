"""Opportunity, SportsOpportunity, and StudentOpportunityMatch models.

Provenance columns (verification_status, source_id, content_hash,
dedup_key, retrieved_at) follow architecture_master §10–§12: every
externally sourced record is verification-tracked and deduplicable, and
records created by ingestion always start as CANDIDATE — never VERIFIED.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class Opportunity(Base):
    __tablename__ = "opportunities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(String, nullable=False)  # internship/job/scholarship/education
    title: Mapped[str] = mapped_column(String, nullable=False)
    organization: Mapped[str | None] = mapped_column(String, nullable=True)
    location: Mapped[str | None] = mapped_column(String, nullable=True)
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    required_skills: Mapped[str | None] = mapped_column(String, nullable=True)  # JSON array
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String, nullable=True)
    last_verified: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # --- provenance / trust columns (architecture_master §10–§12) ----------
    # Student-facing queries filter to ('VALIDATED', 'VERIFIED') only;
    # records created through ingestion start as CANDIDATE (§11).
    verification_status: Mapped[str] = mapped_column(String, default="CANDIDATE")
    status: Mapped[str] = mapped_column(String, default="ACTIVE")  # ACTIVE/EXPIRED/STALE/...
    source_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # sources.id
    content_hash: Mapped[str | None] = mapped_column(String, nullable=True)  # SHA256 dedup
    dedup_key: Mapped[str | None] = mapped_column(String, nullable=True)  # normalized dedup key
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # --- optional enrichment columns (NULL = unknown, never guessed) --------
    field: Mapped[str | None] = mapped_column(String, nullable=True)
    province: Mapped[str | None] = mapped_column(String, nullable=True)
    is_remote: Mapped[bool] = mapped_column(Boolean, default=False)
    organization_type: Mapped[str | None] = mapped_column(String, nullable=True)
    required_education_stage: Mapped[str | None] = mapped_column(String, nullable=True)
    required_degree_type: Mapped[str | None] = mapped_column(String, nullable=True)
    required_cgpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    stipend_pkr: Mapped[int | None] = mapped_column(Integer, nullable=True)  # verified only
    eligibility_notes: Mapped[str | None] = mapped_column(String, nullable=True)


class SportsOpportunity(Base):
    __tablename__ = "sports_opportunities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sport: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)  # tournament/trial/scholarship/programme
    title: Mapped[str] = mapped_column(String, nullable=False)
    organization: Mapped[str | None] = mapped_column(String, nullable=True)
    location: Mapped[str | None] = mapped_column(String, nullable=True)
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    eligibility: Mapped[str | None] = mapped_column(String, nullable=True)  # JSON
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String, nullable=True)
    last_verified: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # --- provenance / trust columns (architecture_master §10–§12) ----------
    verification_status: Mapped[str] = mapped_column(String, default="CANDIDATE")
    source_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # sources.id
    content_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    dedup_key: Mapped[str | None] = mapped_column(String, nullable=True)
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class StudentOpportunityMatch(Base):
    __tablename__ = "student_opportunity_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("students.id"), nullable=False
    )
    opportunity_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("opportunities.id"), nullable=False
    )
    match_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    missing_requirements: Mapped[str | None] = mapped_column(String, nullable=True)  # JSON array
    next_action: Mapped[str | None] = mapped_column(String, nullable=True)
    matched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
