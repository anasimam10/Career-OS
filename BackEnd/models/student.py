"""Student and StudentProfile models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    education_stage: Mapped[str] = mapped_column(String, nullable=False, default="HIGH_SCHOOL")
    career_goal: Mapped[str | None] = mapped_column(String, nullable=True)
    sports_interest: Mapped[str | None] = mapped_column(String, nullable=True)
    motivation_tags: Mapped[str | None] = mapped_column(String, nullable=True)  # JSON array
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    profile: Mapped[StudentProfile | None] = relationship(
        "StudentProfile", back_populates="student", uselist=False, cascade="all, delete-orphan"
    )
    roadmaps: Mapped[list[Roadmap]] = relationship(  # noqa: F821
        "Roadmap", back_populates="student", cascade="all, delete-orphan"
    )


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("students.id"), unique=True, nullable=False
    )
    interests: Mapped[str | None] = mapped_column(String, nullable=True)  # JSON array
    skills: Mapped[str | None] = mapped_column(String, nullable=True)  # JSON array of {name, level}
    completed_milestone_ids: Mapped[str | None] = mapped_column(String, nullable=True)  # JSON array
    job_readiness_score: Mapped[float] = mapped_column(Float, default=0.0)
    next_best_action: Mapped[str | None] = mapped_column(String, nullable=True)  # JSON blob
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    student: Mapped[Student] = relationship("Student", back_populates="profile")
