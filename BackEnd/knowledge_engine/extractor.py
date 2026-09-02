"""
Pakistan Knowledge Engine — Extraction Routing (Step 3).

Routes the raw web content to the appropriate Pydantic schema and
domain-specific prompt based on the target domain.
"""

from __future__ import annotations

import json
from typing import Type

from pydantic import BaseModel

from ingestion.extraction_service import html_to_text, MAX_EXTRACT_CHARS
from services.ai_service import get_ai_service, AIUnavailableError, AIValidationError
from knowledge_engine.prompts import (
    PKE_EXTRACTION_SYSTEM_PROMPT,
    build_pke_extraction_prompt,
)
from knowledge_engine.schemas import (
    SchoolExtraction,
    CollegeExtraction,
    UniversityExtraction,
    ProgramExtraction,
    ScholarshipExtraction,
    InternshipExtraction,
    JobExtraction,
    SportsOrganizationExtraction,
    TournamentExtraction,
    TrialExtraction,
    LearningResourceExtraction,
    CareerExtraction,
)

# Map domains to their target extraction schemas
DOMAIN_SCHEMA_MAP: dict[str, Type[BaseModel]] = {
    "schools": SchoolExtraction,
    "colleges": CollegeExtraction,
    "universities": UniversityExtraction,
    "programs": ProgramExtraction,
    "scholarships": ScholarshipExtraction,
    "internships": InternshipExtraction,
    "jobs": JobExtraction,
    "sports": SportsOrganizationExtraction,
    "tournaments": TournamentExtraction,
    "trials": TrialExtraction,
    "learning_resources": LearningResourceExtraction,
    "careers": CareerExtraction,
}

# Domains that map to the existing Opportunity extraction flow (legacy compatibility).
# The new extractor supports them via PKE schemas, but we track them to know
# if they should be persisted in `opportunities` or `pke_staging_records`.
OPPORTUNITY_DOMAINS = {"scholarships", "internships", "jobs", "programs"}


def get_schema_for_domain(domain: str) -> Type[BaseModel]:
    """Return the Pydantic schema class for the given domain."""
    schema = DOMAIN_SCHEMA_MAP.get(domain)
    if not schema:
        raise ValueError(f"Unknown extraction domain: {domain}")
    return schema


def route_extraction(domain: str, raw_content: str, source_url: str) -> BaseModel:
    """Extract a record for a specific domain from raw HTML using Qwen.

    Raises AIUnavailableError / AIValidationError from the shared AI service.
    Raises ValueError if the domain is unknown.
    """
    schema = get_schema_for_domain(domain)
    text = html_to_text(raw_content)[:MAX_EXTRACT_CHARS]
    
    prompt = build_pke_extraction_prompt(domain, source_url, text)
    
    # We use the shared protected ai_service (Pattern A) to enforce central AI access.
    return get_ai_service().call_structured(
        prompt,
        schema,
        system_prompt=PKE_EXTRACTION_SYSTEM_PROMPT,
        operation=f"pke_extraction_{domain}",
    )
