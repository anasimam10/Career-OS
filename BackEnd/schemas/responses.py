"""
Pydantic response schemas — outbound payloads to the frontend.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

from schemas.shared import (
    EducationStage,
    NextBestAction,
    CareerReality,
    CareerVerdict,
    CareerTrialPlan,
    OpportunityMatch,
    SportsOpportunityMatch,
    AlumniCard,
)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


class HealthResponse(BaseModel):
    status: str = "ok"


# ---------------------------------------------------------------------------
# Careers
# ---------------------------------------------------------------------------


class CareerListItem(BaseModel):
    slug: str
    name: str
    field: str
    demand_level: Optional[str] = None


class CareerDetail(BaseModel):
    slug: str
    name: str
    field: str
    demand_level: Optional[str] = None
    competition_level: Optional[str] = None
    difficulty_level: Optional[str] = None
    required_skills: list[str]
    pk_opportunities: list[str]
    top_pk_universities: list[str]
    risks: list[str]
    last_updated: Optional[str] = None


# ---------------------------------------------------------------------------
# Onboarding
# ---------------------------------------------------------------------------


class OnboardingResponse(BaseModel):
    profile_updated: bool
    next_best_action: NextBestAction
    student_id: Optional[int] = None



# ---------------------------------------------------------------------------
# Journey
# ---------------------------------------------------------------------------


class JourneyStep(BaseModel):
    id: Optional[int] = None
    title: str
    description: str
    stage: EducationStage
    estimated_duration: str
    status: Optional[str] = "pending"


class MilestoneItem(BaseModel):
    id: int
    title: str
    description: str = ""
    status: str = "locked"  # "completed" | "active" | "locked"
    phase: int = 1
    order: int = 1
    action_type: Optional[str] = None
    action_label: Optional[str] = None
    action_url: Optional[str] = None


class JourneyResponse(BaseModel):
    milestones: list[MilestoneItem] = Field(default_factory=list)
    current_milestone_id: Optional[int] = None
    completed_count: int = 0
    total_count: int = 0
    stage: Optional[EducationStage] = None
    current_step: Optional[str] = None
    next_steps: list[JourneyStep] = Field(default_factory=list)
    next_best_action: Optional[NextBestAction] = None
    career_name: Optional[str] = None
    career_slug: Optional[str] = None
    city: Optional[str] = None
    education_stage_label: Optional[str] = None
    sports_interest: Optional[str] = None


class ProgressResponse(BaseModel):
    new_stage: EducationStage
    next_best_action: NextBestAction


class RoadmapResponse(BaseModel):
    roadmap_id: int
    current_step: str
    visible_steps: list[JourneyStep]


# ---------------------------------------------------------------------------
# Opportunities + Sports (Phase 6)
# ---------------------------------------------------------------------------


class OpportunityOut(BaseModel):
    """One opportunity record exactly as stored (GET /opportunities, DB only)."""

    id: int
    type: str
    title: str
    organization: Optional[str] = None
    location: Optional[str] = None
    deadline: Optional[date] = None
    required_skills: list[str]
    description: Optional[str] = None
    source_url: Optional[str] = None
    last_verified: Optional[date] = None
    # Architecture §10: "unverified" when last_verified is older than 30 days.
    data_freshness: Optional[str] = None


class SportsOpportunityOut(BaseModel):
    """One sports opportunity record exactly as stored (GET /sports, DB only)."""

    id: int
    sport: str
    type: str
    title: str
    organization: Optional[str] = None
    location: Optional[str] = None
    deadline: Optional[date] = None
    eligibility: dict
    description: Optional[str] = None
    source_url: Optional[str] = None
    last_verified: Optional[date] = None
    data_freshness: Optional[str] = None


class OpportunityMatchResponse(BaseModel):
    """POST /opportunities/match — ranked matches plus honest data quality.

    Architecture §8 returns ``[OpportunityMatch]``; §10 requires the fallback
    response to carry ``data_quality``/``note``, so the list is wrapped in an
    envelope (Phase 6 decision, documented in DONE.md).
    """

    matches: list[OpportunityMatch]
    data_quality: str  # "ai_interpreted" (MCP path) | "unranked" (direct DB)
    summary: Optional[str] = None  # Qwen's grounded answer (MCP path only)
    note: Optional[str] = None  # set on the unranked fallback path
    message: Optional[str] = None  # set when no records matched at all


class SportsMatchResponse(BaseModel):
    """POST /sports/match — same envelope shape as OpportunityMatchResponse."""

    matches: list[SportsOpportunityMatch]
    data_quality: str
    summary: Optional[str] = None
    note: Optional[str] = None
    message: Optional[str] = None


# ---------------------------------------------------------------------------
# Universities / Programs (master §17)
# ---------------------------------------------------------------------------


class UniversitySummary(BaseModel):
    """One verified university (GET /universities)."""

    id: int
    name: str
    short_name: Optional[str] = None
    slug: str
    city: Optional[str] = None
    province: Optional[str] = None
    type: Optional[str] = None  # PUBLIC / PRIVATE
    hec_recognized: Optional[bool] = None  # NULL = unknown, never guessed
    hec_category: Optional[str] = None
    website_url: Optional[str] = None
    admissions_url: Optional[str] = None


class UniversityListResponse(BaseModel):
    """GET /universities — master §17 envelope."""

    universities: list[UniversitySummary]
    total: int


class ProgramSummary(BaseModel):
    """One verified program (GET /universities/{id}/programs)."""

    id: int
    university_id: int
    name: str
    degree_type: Optional[str] = None
    field: Optional[str] = None
    duration_years: Optional[float] = None
    annual_fee_pkr: Optional[int] = None  # verified only; NULL = unknown
    admission_link: Optional[str] = None
    career_ids: list[int] = []


class ProgramListResponse(BaseModel):
    """GET /universities/{id}/programs — master §17 envelope."""

    programs: list[ProgramSummary]


# ---------------------------------------------------------------------------
# Alumni (master §17/§18/§24)
# ---------------------------------------------------------------------------


class AlumniDetail(AlumniCard):
    """GET /alumni/{id} — the journey card plus provenance columns."""

    university_id: Optional[int] = None
    career_id: Optional[int] = None
    source_url: Optional[str] = None


class AlumniListResponse(BaseModel):
    """GET /alumni — master §17 envelope (verified journeys first)."""

    alumni: list[AlumniCard]


# ---------------------------------------------------------------------------
# Learning resources (master §17/§25)
# ---------------------------------------------------------------------------


class LearningResourceOut(BaseModel):
    """One verified learning resource (GET /learning)."""

    id: int
    skill_name: Optional[str] = None
    title: str
    type: Optional[str] = None  # course/tutorial/video/project/book/other
    provider: Optional[str] = None
    url: str
    language: Optional[str] = None
    level: Optional[str] = None  # beginner/intermediate/advanced
    is_free: Optional[bool] = None  # verified only; NULL = unknown
    duration_hours: Optional[float] = None  # verified only; NULL = unknown


class LearningResourceListResponse(BaseModel):
    """GET /learning — master §17 envelope."""

    resources: list[LearningResourceOut]
