"""
Tests for PKE domain extraction routing and schemas (Step 3).
"""

from __future__ import annotations

import pytest

from services.ai_service import AIUnavailableError, AIValidationError
from knowledge_engine.extractor import (
    route_extraction,
    get_schema_for_domain,
    DOMAIN_SCHEMA_MAP,
)
from knowledge_engine.schemas import UniversityExtraction, ScholarshipExtraction
from knowledge_engine.prompts import PKE_EXTRACTION_SYSTEM_PROMPT


def test_get_schema_for_valid_domain():
    assert get_schema_for_domain("universities") == UniversityExtraction
    assert get_schema_for_domain("scholarships") == ScholarshipExtraction


def test_get_schema_for_invalid_domain():
    with pytest.raises(ValueError, match="Unknown extraction domain"):
        get_schema_for_domain("nonexistent_domain")


def test_schema_optional_fields():
    """Missing fields should parse as None per anti-hallucination rules."""
    data = {"name": "Test Uni"}
    obj = UniversityExtraction(**data)
    assert obj.name == "Test Uni"
    assert obj.type == "university"
    assert obj.city is None
    assert obj.hec_category is None


def test_schema_with_full_fields():
    data = {
        "name": "Test Uni",
        "city": "Lahore",
        "hec_category": "W1",
        "admissions_url": "https://example.com/admissions"
    }
    obj = UniversityExtraction(**data)
    assert obj.city == "Lahore"
    assert obj.hec_category == "W1"


def test_route_extraction_calls_ai_service(monkeypatch):
    """Ensure route_extraction correctly hooks into the shared ai_service."""
    class DummyAI:
        def call_structured(self, prompt, schema, system_prompt, operation):
            assert "Test Uni Content" in prompt
            assert "universities" in operation
            assert system_prompt == PKE_EXTRACTION_SYSTEM_PROMPT
            return UniversityExtraction(name="Extracted Uni")

    def mock_get_ai():
        return DummyAI()

    monkeypatch.setattr("knowledge_engine.extractor.get_ai_service", mock_get_ai)

    result = route_extraction(
        domain="universities",
        raw_content="<html><body>Test Uni Content</body></html>",
        source_url="https://example.com"
    )

    assert isinstance(result, UniversityExtraction)
    assert result.name == "Extracted Uni"


def test_route_extraction_invalid_domain():
    with pytest.raises(ValueError, match="Unknown extraction domain"):
        route_extraction(
            domain="invalid",
            raw_content="...",
            source_url="https://example.com"
        )
