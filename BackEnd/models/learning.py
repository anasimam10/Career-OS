"""Learning resource model (architecture_master §10, §25).

Verified learning resources for skill building. ``skill_name`` is the
working link to careers' required skills (the architecture's own
allowance when records are not normalized to a skills registry);
``skill_id`` is reserved for a future skills table and stays NULL.
``is_free`` / ``duration_hours`` are shown only when verified — NULL
means unknown, never "free" or "paid".
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, Date, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class LearningResource(Base):
    __tablename__ = "learning_resources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # Reserved for a future skills registry; NULL until it exists.
    skill_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    skill_name: Mapped[str | None] = mapped_column(String, nullable=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str | None] = mapped_column(String, nullable=True)  # course/tutorial/video/project/book/other
    provider: Mapped[str | None] = mapped_column(String, nullable=True)
    url: Mapped[str] = mapped_column(String, nullable=False)
    language: Mapped[str | None] = mapped_column(String, default="English")
    level: Mapped[str | None] = mapped_column(String, nullable=True)  # beginner/intermediate/advanced
    is_free: Mapped[bool | None] = mapped_column(Boolean, nullable=True)  # verified only
    duration_hours: Mapped[float | None] = mapped_column(Float, nullable=True)  # verified only
    source_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    verification_status: Mapped[str] = mapped_column(String, default="CANDIDATE")
    last_verified: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
