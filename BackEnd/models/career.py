"""Career model (seed data)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class Career(Base):
    __tablename__ = "careers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    field: Mapped[str] = mapped_column(String, nullable=False)
    demand_level: Mapped[str | None] = mapped_column(String, nullable=True)  # HIGH/MEDIUM/LOW
    competition_level: Mapped[str | None] = mapped_column(String, nullable=True)
    difficulty_level: Mapped[str | None] = mapped_column(String, nullable=True)
    required_skills: Mapped[str | None] = mapped_column(String, nullable=True)  # JSON array
    pk_opportunities: Mapped[str | None] = mapped_column(String, nullable=True)  # JSON array
    top_pk_universities: Mapped[str | None] = mapped_column(String, nullable=True)  # JSON array
    risks: Mapped[str | None] = mapped_column(String, nullable=True)  # JSON array
    category: Mapped[str | None] = mapped_column(String, nullable=True)  # e.g. Engineering, Business
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
