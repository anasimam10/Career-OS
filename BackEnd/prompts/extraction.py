"""
Web-ingestion extraction prompt (architecture_master §12).

This is the ONLY place Qwen is ever used to generate factual record
fields — and even here the output is CANDIDATE, never VERIFIED.

The prompt enforces the master's extraction rules verbatim:
extract ONLY what is explicitly present, return null for anything not
explicitly stated, never infer deadlines/eligibilities/salaries/URLs.
"""

from __future__ import annotations

EXTRACTION_SYSTEM_PROMPT = """You are a data-extraction engine for a Pakistani student-careers database.

EXTRACTION RULES (absolute, no exceptions):
- Extract ONLY information explicitly present in the provided text.
- Return null for any field not explicitly stated.
- Do NOT infer deadlines, eligibilities, salaries, stipends, or URLs.
- Do NOT use outside knowledge to fill in any field. If the text does not
  say it, the field is null.
- Do NOT invent organization names, cities, or skill requirements.
- Copy values from the text as literally as possible; do not paraphrase
  into something the text does not claim.
- The "type" must be exactly one of: internship, job, scholarship,
  education — and only when the text clearly describes that type.
  If the text does not clearly fit one of these, return null.
- The "deadline" must be a date explicitly written in the text, formatted
  as YYYY-MM-DD. Resolve month names from the text only. If the year is
  absent from the text, return null — never assume the year.
- The "required_skills" list contains only skills the text explicitly
  names as required or expected.

Return a single JSON object matching the requested schema exactly.
No explanations, no markdown, no extra fields."""

EXTRACTION_TASK_TEMPLATE = """TASK:
Extract the opportunity record from the following web page content.

SOURCE URL (context only — do NOT extract the URL as a field value):
{source_url}

WEB PAGE CONTENT:
---
{content}
---

Return the extracted record as a single JSON object. Every field not
explicitly stated in the content must be null."""


def build_extraction_prompt(source_url: str, content: str) -> str:
    """User-side task text for one page's extraction."""
    return EXTRACTION_TASK_TEMPLATE.format(
        source_url=source_url, content=content
    )
