"""
Pakistan Knowledge Engine — Domain Extraction Prompts (Step 3).

Strict prompts enforcing the PKE anti-hallucination rules.
"""

from __future__ import annotations

# Unified system prompt enforcing the primary anti-hallucination directive.
PKE_EXTRACTION_SYSTEM_PROMPT = """You are a highly disciplined data-extraction engine for the Pakistan Knowledge Engine.

EXTRACTION RULES (absolute, no exceptions):
- Extract ONLY information explicitly present in the provided text.
- Return null for any field not explicitly stated.
- Do NOT infer deadlines, eligibilities, fees, stipends, or URLs.
- Do NOT use outside knowledge to fill in any field. If the text does not say it, the field is null.
- Do NOT invent organization names, cities, or skill requirements.
- Copy values from the text as literally as possible; do not paraphrase into something the text does not claim.
- Dates must be formatted as YYYY-MM-DD. Resolve month names from the text only. If the year is absent, return null — never assume the year.
- Return a single JSON object matching the requested schema exactly.
- No explanations, no markdown, no extra fields."""


# Base template for all domain extractors
_BASE_TASK_TEMPLATE = """TASK:
Extract the {domain_name} record from the following web page content.

{domain_specific_instructions}

SOURCE URL (context only — do NOT extract the URL as a field value unless it is explicitly printed in the page content):
{source_url}

WEB PAGE CONTENT:
---
{content}
---

Return the extracted record as a single JSON object. Every field not explicitly stated in the content must be null."""


# Domain-specific instructions injected into the base template
DOMAIN_INSTRUCTIONS = {
    "schools": "Focus on the school's name, city, sector (public/private), and contact information.",
    "colleges": "Focus on the college's name, city, sector, and any affiliated boards or programs.",
    "universities": "Focus on the university's name, city, public/private sector, and HEC category if explicitly stated.",
    "programs": "Focus on academic degree programs, their duration, field of study, and admission deadlines.",
    "scholarships": "Focus on scholarship eligibility, stipends, required degrees, and deadlines.",
    "internships": "Focus on internship roles, skills, stipends, and deadlines.",
    "jobs": "Focus on job titles, required skills, education requirements, and deadlines.",
    "sports": "Focus on sports organizations, academies, or federations, including their city and sport type.",
    "tournaments": "Focus on tournament schedules, locations, sports, and registration deadlines.",
    "trials": "Focus on sports trials, dates, locations, and eligibility criteria.",
    "learning_resources": "Focus on educational resources, courses, their provider, duration, and whether they are free.",
    "careers": "Focus on career definitions, required skills, demand levels, and typical employers.",
}


def build_pke_extraction_prompt(domain: str, source_url: str, content: str) -> str:
    """Build the user-side task text for PKE domain extraction."""
    domain_name = domain.replace("_", " ").title()
    # Fallback to a generic instruction if domain is unknown
    specific_inst = DOMAIN_INSTRUCTIONS.get(
        domain, f"Focus on extracting relevant {domain_name} details."
    )
    
    return _BASE_TASK_TEMPLATE.format(
        domain_name=domain_name,
        domain_specific_instructions=specific_inst,
        source_url=source_url,
        content=content,
    )
