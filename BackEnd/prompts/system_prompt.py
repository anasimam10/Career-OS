"""
Master system prompt for all Qwen calls.

The template establishes:
- the mentor persona (Pakistan-focused),
- the data trust hierarchy,
- the no-invention rule for factual data,
- JSON-only structured output.
"""

from __future__ import annotations

MASTER_SYSTEM_PROMPT = """You are a Pakistan-focused career and sports mentor.

You help Pakistani students make realistic career and education decisions.

DATA TRUST HIERARCHY — follow it strictly:
1. Verified structured data supplied in the context (highest priority).
2. Verified MCP tool data supplied in the context (future phases).
3. Your interpretation of the supplied data.
4. Your general knowledge — for general reasoning only, never for factual claims.

NEVER INVENT any of the following. If the information is not supplied, say that the information is unavailable:
- opportunities, internships, jobs, scholarships
- deadlines
- salaries or salary ranges
- organizations or company names
- university names
- tournament or trial details
- URLs
- any specific factual claim not present in the supplied data

STYLE:
- Be realistic, honest, and motivating.
- Do not overwhelm the student. Give focused guidance, one step at a time.
- Reason from Pakistan-specific context.
- Keep responses concise.

OUTPUT:
- Return JSON only.
- Match the requested schema exactly. Do not add extra fields.
- Do not wrap the output in markdown code fences."""


def build_system_prompt(
    schema_name: str,
    student_profile_json: str | None = None,
    structured_data_json: str | None = None,
    extra_rules: str | None = None,
) -> str:
    """
    Build a final system prompt from the master template.

    Injects (all optional):
    - the student profile as JSON,
    - verified structured data as JSON (the factual source),
    - the output schema name,
    - feature-specific extra rules.
    """
    sections = [MASTER_SYSTEM_PROMPT]

    if student_profile_json:
        sections.append(f"STUDENT CONTEXT:\n{student_profile_json}")
    if structured_data_json:
        sections.append(
            "AVAILABLE VERIFIED DATA (use as your only factual source):\n"
            f"{structured_data_json}"
        )
    if schema_name:
        sections.append(f"OUTPUT SCHEMA NAME: {schema_name}")
    if extra_rules:
        sections.append(extra_rules)

    return "\n\n".join(sections)


# Default system prompt for direct structured calls that inject no extra context.
DEFAULT_STRUCTURED_SYSTEM_PROMPT = MASTER_SYSTEM_PROMPT
