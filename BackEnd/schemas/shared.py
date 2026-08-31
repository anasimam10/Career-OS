"""
Shared enums and Pydantic models used by both requests and responses.
These match the architecture document §9 exactly.
"""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class EducationStage(str, Enum):
    HIGH_SCHOOL = "HIGH_SCHOOL"
    CAREER_DISCOVERY = "CAREER_DISCOVERY"
    CAREER_DECISION = "CAREER_DECISION"
    UNIVERSITY = "UNIVERSITY"
    SKILL_BUILDING = "SKILL_BUILDING"
    PROJECTS = "PROJECTS"
    INTERNSHIP = "INTERNSHIP"
    FINAL_YEAR = "FINAL_YEAR"
    JOB_PREPARATION = "JOB_PREPARATION"
    FIRST_JOB = "FIRST_JOB"


class MilestoneStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    DONE = "done"
    SKIPPED = "skipped"


DemandLevel = str  # Literal["HIGH", "MEDIUM", "LOW"]
CompetitionLevel = str
DifficultyLevel = str
VerdictType = str  # Literal["GOOD_FIT", "WORTH_EXPLORING", "RECONSIDER"]


# ---------------------------------------------------------------------------
# AI Output Schemas (architecture §9)
# ---------------------------------------------------------------------------


class NextBestAction(BaseModel):
    title: str
    description: str
    steps: list[str]
    estimated_time: str
    why_this_matters: str
    stage: str


class CareerReality(BaseModel):
    career_name: str
    demand_level: DemandLevel
    competition_level: CompetitionLevel
    difficulty_level: DifficultyLevel
    required_skills: list[str]
    pk_opportunities: list[str]
    risks: list[str]
    rewards: list[str]
    data_source: str


class CareerVerdict(BaseModel):
    verdict: VerdictType
    headline: str
    reasoning: str
    student_strengths_match: list[str]
    gaps_to_address: list[str]
    suggested_trial: Optional[str] = None


class CareerRealityResponse(BaseModel):
    reality: CareerReality
    verdict: CareerVerdict


class TrialDay(BaseModel):
    day_range: str
    title: str
    tasks: list[str]


class CareerTrialPlan(BaseModel):
    career_slug: str
    duration_days: int
    days: list[TrialDay]
    reflection_prompt: str


class CoachResponse(BaseModel):
    message: str
    quick_actions: list[str]
    suggested_resource: Optional[str] = None


class OpportunityMatch(BaseModel):
    opportunity_id: int
    title: str
    organization: str
    match_score: float
    match_reasons: list[str]
    missing_requirements: list[str]
    next_action: str
    deadline: Optional[date] = None
    source_url: str
    # Architecture §10: set to "unverified" when the record's last_verified
    # is older than 30 days (None otherwise). Additive Optional field.
    data_freshness: Optional[str] = None


class SportsOpportunityMatch(BaseModel):
    opportunity_id: int
    sport: str
    title: str
    organization: str
    match_score: float
    eligibility_met: list[str]
    eligibility_missing: list[str]
    next_action: str
    deadline: Optional[date] = None
    source_url: str
    # Architecture §10 freshness flag (same rule as OpportunityMatch).
    data_freshness: Optional[str] = None


class JobReadinessAIAnalysis(BaseModel):
    """Qwen's analysis portion of the job readiness response (architecture §6.4)."""

    gap_explanation: str
    next_best_action: NextBestAction
    recommendations: list[str]


class JobReadiness(BaseModel):
    overall_score: float
    score_label: str
    component_scores: dict[str, float]
    biggest_gap: str
    gap_explanation: str
    next_best_action: NextBestAction
    recommendations: list[str]
    disclaimer: str


class AlumniCard(BaseModel):
    """Alumni journey card (§18). Core fields keep the model's column
    names (university/role/company) per the existing frontend contract;
    NULL columns serialize as None — journeys are seeded templates.
    """

    id: int
    name: str
    university: Optional[str] = None
    field: Optional[str] = None
    role: Optional[str] = None
    company: Optional[str] = None
    career_path_summary: Optional[str] = None
    key_advice: Optional[str] = None
    tags: list[str] = []
    # Additive: unverified (community/template) journeys must be labeled.
    is_verified: bool = False
