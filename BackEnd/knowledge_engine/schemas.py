"""
Pakistan Knowledge Engine — Domain Extraction Schemas (Step 3).

These Pydantic schemas enforce the structure of data extracted by Qwen
from raw web content across the 12 PKE domains.

CRITICAL ANTI-HALLUCINATION RULE:
All fields (including name/title and type identifier) are Optional with
safe defaults. Qwen is instructed to return `null` if the information is
not EXPLICITLY present in the source text. Minimum required fields
(such as non-empty title/name) are enforced downstream in validation stages.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Organization Domains
# ---------------------------------------------------------------------------


class SchoolExtraction(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = "school"
    sector: Optional[str] = None  # PUBLIC, PRIVATE, UNKNOWN
    city: Optional[str] = None
    level: Optional[str] = None  # Primary, Middle, High, O-Level, etc.
    board_affiliation: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    website_url: Optional[str] = None


class CollegeExtraction(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = "college"
    sector: Optional[str] = None
    city: Optional[str] = None
    board_affiliation: Optional[str] = None
    programs_offered: Optional[list[str]] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    website_url: Optional[str] = None


class UniversityExtraction(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = "university"
    short_name: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    sector: Optional[str] = None  # PUBLIC, PRIVATE
    hec_category: Optional[str] = None
    website_url: Optional[str] = None
    admissions_url: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None


class SportsOrganizationExtraction(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = "sports_organization"
    sport: Optional[str] = None
    level: Optional[str] = None  # National, Provincial, Academy
    city: Optional[str] = None
    website_url: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None


# ---------------------------------------------------------------------------
# Activity / Opportunity Domains
# ---------------------------------------------------------------------------


class ProgramExtraction(BaseModel):
    title: Optional[str] = None
    type: Optional[str] = "program"
    university_name: Optional[str] = None
    campus_city: Optional[str] = None
    degree_type: Optional[str] = None  # BS, MS, PhD, Diploma
    field_of_study: Optional[str] = None
    duration_years: Optional[float] = None
    annual_fee_pkr: Optional[int] = None
    admission_deadline: Optional[str] = None  # YYYY-MM-DD
    admission_link: Optional[str] = None


class ScholarshipExtraction(BaseModel):
    title: Optional[str] = None
    type: Optional[str] = "scholarship"
    organization: Optional[str] = None
    location: Optional[str] = None
    deadline: Optional[str] = None  # YYYY-MM-DD
    description: Optional[str] = None
    eligibility_notes: Optional[str] = None
    stipend_pkr: Optional[int] = None
    required_degree_type: Optional[str] = None
    required_cgpa: Optional[float] = None


class InternshipExtraction(BaseModel):
    title: Optional[str] = None
    type: Optional[str] = "internship"
    organization: Optional[str] = None
    location: Optional[str] = None
    is_remote: Optional[bool] = None
    deadline: Optional[str] = None  # YYYY-MM-DD
    description: Optional[str] = None
    stipend_pkr: Optional[int] = None
    required_skills: Optional[list[str]] = None
    eligibility_notes: Optional[str] = None


class JobExtraction(BaseModel):
    title: Optional[str] = None
    type: Optional[str] = "job"
    organization: Optional[str] = None
    location: Optional[str] = None
    is_remote: Optional[bool] = None
    deadline: Optional[str] = None  # YYYY-MM-DD
    description: Optional[str] = None
    stipend_pkr: Optional[int] = None
    required_skills: Optional[list[str]] = None
    eligibility_notes: Optional[str] = None
    required_education_stage: Optional[str] = None


class TournamentExtraction(BaseModel):
    title: Optional[str] = None
    type: Optional[str] = "tournament"
    sport: Optional[str] = None
    organization: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None  # YYYY-MM-DD
    end_date: Optional[str] = None  # YYYY-MM-DD
    deadline: Optional[str] = None  # Registration deadline
    eligibility_notes: Optional[str] = None
    description: Optional[str] = None


class TrialExtraction(BaseModel):
    title: Optional[str] = None
    type: Optional[str] = "trial"
    sport: Optional[str] = None
    organization: Optional[str] = None
    location: Optional[str] = None
    date: Optional[str] = None  # YYYY-MM-DD
    deadline: Optional[str] = None
    eligibility_notes: Optional[str] = None
    description: Optional[str] = None


# ---------------------------------------------------------------------------
# Content / Reference Domains
# ---------------------------------------------------------------------------


class LearningResourceExtraction(BaseModel):
    title: Optional[str] = None
    type: Optional[str] = "learning_resource"
    provider: Optional[str] = None
    url: Optional[str] = None
    resource_type: Optional[str] = None  # course, tutorial, video, book
    language: Optional[str] = None
    level: Optional[str] = None  # beginner, intermediate, advanced
    is_free: Optional[bool] = None
    duration_hours: Optional[float] = None
    associated_skills: Optional[list[str]] = None


class CareerExtraction(BaseModel):
    title: Optional[str] = None
    type: Optional[str] = "career"
    category: Optional[str] = None
    description: Optional[str] = None
    required_skills: Optional[list[str]] = None
    demand_level: Optional[str] = None
    typical_employers: Optional[list[str]] = None
