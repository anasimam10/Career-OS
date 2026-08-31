"""Alumni model (seed + community submitted).

Public/verified career journeys only (architecture_master §24) — no
private contact harvesting, no social networking. Column names on the
core fields (university, role, company, career_path, advice) follow the
existing frontend contract; the provenance columns follow §10.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class Alumni(Base):
    __tablename__ = "alumni"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    university: Mapped[str | None] = mapped_column(String, nullable=True)
    field: Mapped[str | None] = mapped_column(String, nullable=True)
    role: Mapped[str | None] = mapped_column(String, nullable=True)
    company: Mapped[str | None] = mapped_column(String, nullable=True)
    career_path: Mapped[str | None] = mapped_column(String, nullable=True)  # free text
    advice: Mapped[str | None] = mapped_column(String, nullable=True)  # free text
    tags: Mapped[str | None] = mapped_column(String, nullable=True)  # JSON array
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    # --- provenance columns (architecture_master §10/§12) --------------------
    university_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("universities.id"), nullable=True
    )
    career_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # careers.id
    source_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # sources.id
    source_url: Mapped[str | None] = mapped_column(String, nullable=True)  # public article/profile
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
