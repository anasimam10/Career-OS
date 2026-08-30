"""
Pydantic response schemas — outbound payloads to the frontend.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel

from schemas.shared import (
    EducationStage,
    NextBestAction,
    CareerReality,
    CareerVerdict,
    CareerTrialPlan,
    OpportunityMatch,
    SportsOpportunityMatch,
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


# ---------------------------------------------------------------------------
# Journey
# ---------------------------------------------------------------------------


class JourneyStep(BaseModel):
    title: str
    description: str
    stage: EducationStage
    estimated_duration: str


class JourneyResponse(BaseModel):
    stage: EducationStage
    current_step: str
    next_steps: list[JourneyStep]
    next_best_action: NextBestAction


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
