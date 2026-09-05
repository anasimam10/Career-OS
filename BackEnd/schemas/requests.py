"""
Pydantic request schemas — inbound payloads from the frontend.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel

from schemas.shared import EducationStage


class Skill(BaseModel):
    name: str
    level: str  # "beginner" | "intermediate" | "advanced"


class OnboardingPayload(BaseModel):
    education_stage: EducationStage
    interests: list[str]
    career_interests: list[str]
    sports_interest: Optional[str] = None
    motivation_tags: list[str]
    skills: list[Skill]
    city: str
    province: Optional[str] = None


class CareerAnalyzeRequest(BaseModel):
    career_slug: str


class CareerTrialRequest(BaseModel):
    career_slug: str


class ProgressRequest(BaseModel):
    milestone_id: Optional[int] = None
    milestoneId: Optional[int] = None
    student_id: Optional[int] = None
    studentId: Optional[int] = None
    status: str = "done"


class RoadmapRequest(BaseModel):
    career_slug: str
    target_stage: str


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class CoachChatPayload(BaseModel):
    message: str
    conversation_history: list[ChatMessage]


class OpportunityMatchRequest(BaseModel):
    """POST /opportunities/match (architecture §8).

    The search tools require a city, so ``city`` is mandatory; ``skills``
    overrides the student profile's skills when provided.
    """

    city: str
    # Only these two types have MCP search tools (search_internships /
    # search_jobs); education and scholarship records are browse-only.
    opportunity_type: Literal["internship", "job"] = "internship"
    field: Optional[str] = None
    skills: Optional[list[str]] = None


class SportsMatchRequest(BaseModel):
    """POST /sports/match (architecture §8: request {sport, location, level})."""

    sport: str
    location: Optional[str] = None
    level: Optional[str] = None
