"""Extraction service (architecture_master §12, stage 3).

Runs Qwen over retrieved page content through the shared, protected
``ai_service`` (Pattern A) with the extraction-only prompt. The output
is stored as evidence in source_documents.extracted_json — it is NEVER
treated as truth, and records persisted from it always start as
CANDIDATE (§11).

Failures raise the service's controlled exceptions
(AIUnavailableError / AIValidationError); the ingestion pipeline
catches them per item and marks the item FAILED — one bad page never
aborts a run.
"""

from __future__ import annotations

import json
import re

from schemas.admin import OpportunityExtraction
from services.ai_service import get_ai_service
from prompts.extraction import EXTRACTION_SYSTEM_PROMPT, build_extraction_prompt

# Bounded prompt input: pages can be huge; the extraction prompt passes
# only the first ~40k characters of cleaned text (deterministic cut).
MAX_EXTRACT_CHARS = 40_000

_TAG_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def html_to_text(html: str) -> str:
    """Deterministic HTML -> text cleanup (no interpretation).

    Drops script/style blocks, then all tags, then collapses whitespace.
    This is presentation cleanup only — no content is inferred, added,
    or reordered.
    """
    text = _TAG_RE.sub(" ", html or "")
    text = _HTML_TAG_RE.sub(" ", text)
    return _WS_RE.sub(" ", text).strip()


def extract_opportunity(raw_content: str, source_url: str) -> OpportunityExtraction:
    """Extract one opportunity record from page content via Qwen (Pattern A).

    Raises AIUnavailableError / AIValidationError from the shared service.
    """
    text = html_to_text(raw_content)[:MAX_EXTRACT_CHARS]
    prompt = build_extraction_prompt(source_url, text)
    return get_ai_service().call_structured(
        prompt,
        OpportunityExtraction,
        system_prompt=EXTRACTION_SYSTEM_PROMPT,
        operation="ingestion_extraction",
    )


def extraction_to_json(extraction: OpportunityExtraction) -> str:
    """Serialize the extraction for source_documents.extracted_json."""
    return extraction.model_dump_json(exclude_none=False)


def parse_extraction_json(raw: str | None) -> dict | None:
    """Read back a stored extraction JSON (best effort; None when absent)."""
    if not raw:
        return None
    try:
        value = json.loads(raw)
        return value if isinstance(value, dict) else None
    except (json.JSONDecodeError, TypeError):
        return None
