"""Mock Interview models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

class MockInterviewSession(Base):
    __tablename__ = "mock_interview_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id"), nullable=False)
    career_context: Mapped[str] = mapped_column(String, nullable=False) # e.g. "Software Engineering"
    difficulty: Mapped[str] = mapped_column(String, nullable=False) # "beginner", "intermediate", "advanced"
    status: Mapped[str] = mapped_column(String, nullable=False, default="in_progress") # "in_progress", "completed"
    score: Mapped[float | None] = mapped_column(Float, nullable=True) # Percentage 0-100
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    questions: Mapped[list[MockInterviewQuestion]] = relationship(
        "MockInterviewQuestion", back_populates="session", cascade="all, delete-orphan", order_by="MockInterviewQuestion.id"
    )

class MockInterviewQuestion(Base):
    __tablename__ = "mock_interview_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("mock_interview_sessions.id"), nullable=False)
    question_text: Mapped[str] = mapped_column(String, nullable=False)
    options: Mapped[str] = mapped_column(String, nullable=False) # JSON array of {id, text}
    correct_option_id: Mapped[str] = mapped_column(String, nullable=False)
    selected_option_id: Mapped[str | None] = mapped_column(String, nullable=True)
    explanation: Mapped[str] = mapped_column(String, nullable=False)
    topic: Mapped[str] = mapped_column(String, nullable=False)
    source_resource_ids: Mapped[str | None] = mapped_column(String, nullable=True) # JSON array of IDs
    
    # Relationships
    session: Mapped[MockInterviewSession] = relationship("MockInterviewSession", back_populates="questions")
