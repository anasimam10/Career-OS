"""
Phase 5 tests — Deduplication (architecture_master §12, stage 6).

Unit coverage of the deterministic key/hash helpers plus pipeline-level
duplicate detection: the same real-world opportunity posted on a second
URL must associate with the existing record instead of creating a second
one.
"""

from __future__ import annotations

import json

import pytest

from ingestion.dedup_service import (
    content_unchanged,
    find_duplicate,
    make_content_hash,
    make_dedup_key,
    normalize_text,
)
from ingestion import ingestion_service
from models.opportunity import Opportunity
from models.source import IngestionItem

EXTRACTION_JSON = {
    "type": "internship",
    "title": "AI Research Intern",
    "organization": "TechCity Labs (template)",
    "location": "Karachi",
    "deadline": "2027-06-15",
    "required_skills": ["Python"],
    "description": "Paid AI research internship.",
}

EXTRACTION_JSON_B = {
    "type": "internship",
    "title": "AI Research Intern",  # same real-world opportunity
    "organization": "TechCity Labs (template)",
    "location": "Karachi",
    "deadline": "2027-06-15",
    "required_skills": ["Python"],
    "description": "Cross-posted description.",
}


# ---------------------------------------------------------------------------
# normalize_text / make_dedup_key
# ---------------------------------------------------------------------------


class TestNormalizeText:
    def test_lowercases_and_collapses_whitespace(self):
        assert normalize_text("  Software   ENGINEER ") == "software engineer"

    def test_strips_punctuation(self):
        assert normalize_text("Sr. Software Engineer!") == "sr software engineer"

    def test_strips_html_tags(self):
        assert normalize_text("<b>Data</b> Analyst") == "data analyst"

    def test_none_and_empty(self):
        assert normalize_text(None) == ""
        assert normalize_text("") == ""


class TestMakeDedupKey:
    def test_key_shape(self):
        key = make_dedup_key("Internship", "AI Research Intern", "TechCity Labs")
        assert key == "internship|airesearchintern|techcitylabs"

    def test_case_and_punctuation_insensitive(self):
        a = make_dedup_key("internship", "AI Research Intern!", "TechCity Labs")
        b = make_dedup_key("INTERNSHIP", "ai research intern", "techcity labs")
        assert a == b

    def test_whitespace_insensitive(self):
        a = make_dedup_key("job", "Junior  Developer", "ACME")
        b = make_dedup_key("job", "Junior Developer", "ACME")
        assert a == b

    def test_different_titles_differ(self):
        assert make_dedup_key("job", "Junior Developer", "ACME") != make_dedup_key(
            "job", "Senior Developer", "ACME"
        )

    def test_different_organizations_differ(self):
        assert make_dedup_key("job", "Developer", "ACME") != make_dedup_key(
            "job", "Developer", "Globex"
        )

    def test_different_types_differ(self):
        assert make_dedup_key("job", "Developer", "ACME") != make_dedup_key(
            "internship", "Developer", "ACME"
        )

    def test_missing_parts_are_empty_segments(self):
        assert make_dedup_key("job", "Developer", None) == "job|developer|"


# ---------------------------------------------------------------------------
# make_content_hash
# ---------------------------------------------------------------------------


class TestContentHash:
    def test_deterministic(self):
        assert make_content_hash("page") == make_content_hash("page")

    def test_changes_with_content(self):
        assert make_content_hash("page") != make_content_hash("page2")

    def test_hex_sha256(self):
        assert len(make_content_hash("page")) == 64
        int(make_content_hash("page"), 16)  # parses as hex


# ---------------------------------------------------------------------------
# Duplicate lookup helpers
# ---------------------------------------------------------------------------


class TestFindDuplicate:
    def test_finds_existing_record(self, db_session):
        db_session.add(
            Opportunity(
                type="internship",
                title="AI Research Intern",
                organization="TechCity Labs",
                dedup_key=make_dedup_key("internship", "AI Research Intern", "TechCity Labs"),
            )
        )
        db_session.commit()
        duplicate = find_duplicate(
            db_session, make_dedup_key("internship", "AI Research Intern", "TechCity Labs")
        )
        assert duplicate is not None
        assert duplicate.title == "AI Research Intern"

    def test_no_match_returns_none(self, db_session):
        assert find_duplicate(db_session, "internship|missing|") is None

    def test_empty_key_returns_none(self, db_session):
        assert find_duplicate(db_session, "") is None


class TestContentUnchanged:
    def test_no_source_returns_false(self, db_session):
        assert content_unchanged(db_session, "https://example.com/x", "h") is False

    def test_same_hash_returns_true(self, db_session):
        from models.source import Source

        db_session.add(
            Source(
                source_url="https://example.com/x",
                source_type="UNKNOWN",
                content_hash="abc123",
            )
        )
        db_session.commit()
        assert content_unchanged(db_session, "https://example.com/x", "abc123") is True

    def test_different_hash_returns_false(self, db_session):
        from models.source import Source

        db_session.add(
            Source(
                source_url="https://example.com/x",
                source_type="UNKNOWN",
                content_hash="abc123",
            )
        )
        db_session.commit()
        assert content_unchanged(db_session, "https://example.com/x", "zzz") is False


# ---------------------------------------------------------------------------
# Pipeline-level duplicate detection
# ---------------------------------------------------------------------------


def _mock_extract(monkeypatch, extraction: dict):
    from services.ai_service import AIService
    from types import SimpleNamespace
    from unittest.mock import MagicMock

    message = SimpleNamespace(content=json.dumps(extraction), tool_calls=None)
    response = SimpleNamespace(choices=[SimpleNamespace(message=message)])
    client = MagicMock()
    client.chat.completions.create.return_value = response
    monkeypatch.setattr(
        "ingestion.extraction_service.get_ai_service",
        lambda: AIService(client=client),
    )


class TestPipelineDedup:
    def test_same_opportunity_two_urls_single_record(self, db_session, monkeypatch):
        pages = {
            "https://portal-a.com/intern": "<html>posting A</html>",
            "https://portal-b.com/intern": "<html>posting B — cross-post</html>",
        }

        def fake_fetch(url: str) -> str:
            return pages[url]

        monkeypatch.setattr(ingestion_service, "_fetch_url", fake_fetch)
        _mock_extract(monkeypatch, EXTRACTION_JSON)

        ingestion_service.run_url_ingestion(
            db_session, urls=["https://portal-a.com/intern"]
        )
        # Second URL: same real-world opportunity, different page content.
        _mock_extract(monkeypatch, EXTRACTION_JSON_B)
        result = ingestion_service.run_url_ingestion(
            db_session, urls=["https://portal-b.com/intern"]
        )
        assert result["queued_count"] == 1

        # Exactly ONE opportunity; the second item linked to it.
        assert db_session.query(Opportunity).count() == 1
        items = (
            db_session.query(IngestionItem).order_by(IngestionItem.id).all()
        )
        assert [i.status for i in items] == ["STORED", "DUPLICATE"]
        assert items[0].opportunity_id == items[1].opportunity_id == 1

    def test_different_opportunities_both_stored(self, db_session, monkeypatch):
        monkeypatch.setattr(
            ingestion_service,
            "_fetch_url",
            lambda url: f"<html>page {url}</html>",
        )
        _mock_extract(monkeypatch, EXTRACTION_JSON)
        ingestion_service.run_url_ingestion(
            db_session, urls=["https://portal-a.com/intern"]
        )
        _mock_extract(
            monkeypatch,
            {**EXTRACTION_JSON, "title": "Backend Engineer Intern"},
        )
        ingestion_service.run_url_ingestion(
            db_session, urls=["https://portal-b.com/intern"]
        )
        assert db_session.query(Opportunity).count() == 2

    def test_duplicate_within_one_run(self, db_session, monkeypatch):
        monkeypatch.setattr(
            ingestion_service,
            "_fetch_url",
            lambda url: f"<html>page {url}</html>",
        )
        _mock_extract(monkeypatch, EXTRACTION_JSON)
        ingestion_service.run_url_ingestion(
            db_session,
            urls=[
                "https://portal-a.com/intern",
                "https://portal-b.com/intern",
            ],
        )
        assert db_session.query(Opportunity).count() == 1
        items = (
            db_session.query(IngestionItem).order_by(IngestionItem.id).all()
        )
        assert [i.status for i in items] == ["STORED", "DUPLICATE"]

    def test_duplicate_associates_source_when_missing(self, db_session, monkeypatch):
        # Pre-existing curated record without provenance columns.
        db_session.add(
            Opportunity(
                type="internship",
                title="AI Research Intern",
                organization="TechCity Labs (template)",
                verification_status="VALIDATED",
                dedup_key=make_dedup_key(
                    "internship", "AI Research Intern", "TechCity Labs (template)"
                ),
                is_active=True,
            )
        )
        db_session.commit()

        monkeypatch.setattr(
            ingestion_service, "_fetch_url", lambda url: "<html>page</html>"
        )
        _mock_extract(monkeypatch, EXTRACTION_JSON)
        ingestion_service.run_url_ingestion(
            db_session, urls=["https://portal-a.com/intern"]
        )

        assert db_session.query(Opportunity).count() == 1
        record = db_session.query(Opportunity).one()
        assert record.source_id == 1  # associated, not duplicated
        # The existing VALIDATED record is never downgraded.
        assert record.verification_status == "VALIDATED"
