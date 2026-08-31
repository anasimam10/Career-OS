"""University, Campus, and Program models (architecture_master §10).

Pakistani higher-education knowledge base. University records are
verification-tracked like every other externally sourced record: curated
seed rows are VERIFIED, ingested rows start as CANDIDATE and are never
shown to students until validated (architecture §11).
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class University(Base):
    __tablename__ = "universities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    short_name: Mapped[str | None] = mapped_column(String, nullable=True)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    city: Mapped[str | None] = mapped_column(String, nullable=True)
    province: Mapped[str | None] = mapped_column(String, nullable=True)
    type: Mapped[str | None] = mapped_column(String, nullable=True)  # PUBLIC / PRIVATE
    # NULL means unknown — never guess HEC recognition (architecture §10).
    hec_recognized: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    hec_category: Mapped[str | None] = mapped_column(String, nullable=True)  # W1/W2/W3/X
    website_url: Mapped[str | None] = mapped_column(String, nullable=True)
    admissions_url: Mapped[str | None] = mapped_column(String, nullable=True)
    source_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    verification_status: Mapped[str] = mapped_column(String, default="CANDIDATE")
    last_verified: Mapped[date | None] = mapped_column(Date, nullable=True)


class Campus(Base):
    __tablename__ = "campuses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    university_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("universities.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    city: Mapped[str | None] = mapped_column(String, nullable=True)
    is_main: Mapped[bool] = mapped_column(Boolean, default=False)


class Program(Base):
    __tablename__ = "programs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    university_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("universities.id"), nullable=False
    )
    campus_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("campuses.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    degree_type: Mapped[str | None] = mapped_column(String, nullable=True)  # BS/BE/BBA/MS/...
    field: Mapped[str | None] = mapped_column(String, nullable=True)
    duration_years: Mapped[float | None] = mapped_column(Float, nullable=True)
    annual_fee_pkr: Mapped[int | None] = mapped_column(Integer, nullable=True)  # verified only
    admission_link: Mapped[str | None] = mapped_column(String, nullable=True)
    # JSON array of career ids this program leads to (seeded from career slugs).
    career_ids: Mapped[str | None] = mapped_column(String, nullable=True)
    source_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    verification_status: Mapped[str] = mapped_column(String, default="CANDIDATE")
    last_verified: Mapped[date | None] = mapped_column(Date, nullable=True)
