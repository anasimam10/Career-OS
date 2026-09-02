"""
Phase 5 tests — Web ingestion pipeline (architecture_master §12).

ALL HTTP and Qwen calls are mocked:
- _fetch_url is patched at the module boundary (its own unit tests patch
  httpx.Client instead);
- Qwen extraction is mocked at the protected ai_service boundary, the
  same pattern as test_job_readiness / test_coach (mock OpenAI client +
  the real call_structured pipeline).

Coverage: the 8-stage pipeline (retrieve/extract/validate/normalize/
dedup/persist/index), per-item status transitions, run status tracking,
refresh mode, manual verification (stage 9), data-quality counters, and
the admin ingestion endpoints' auth + validation contract.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import httpx
import pytest

from config import settings
from ingestion import ingestion_service
from ingestion.extraction_service import html_to_text
from models.opportunity import Opportunity
from models.source import IngestionItem, IngestionRun, Source, SourceDocument
from services.ai_service import AIService, AIUnavailableError
from tests.conftest import TestingSessionLocal

from tests.test_opportunities import soon  # relative-date helper

ADMIN_TOKEN = "test-admin-token"

PAGE_HTML = """
<html><head><script>var tracking = "noise();";</script></head>
<body><h1>AI Research Intern</h1>
<p>TechCity Labs (template) — Karachi. Paid internship, PKR 40,000/month.</p>
<p>Requires Python and Machine Learning. Apply by June 15, 2027.</p>
</body></html>
"""

EXTRACTION_JSON = {
    "type": "internship",
    "title": "AI Research Intern",
    "organization": "TechCity Labs (template)",
    "location": "Karachi",
    "deadline": "2027-06-15",
    "required_skills": ["Python", "Machine Learning"],
    "description": "Paid AI research internship.",
    "stipend_pkr": 40000,
    "eligibility_notes": None,
    "is_remote": False,
}


# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------


def text_response(content: str):
    message = SimpleNamespace(content=content, tool_calls=None)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def mock_ai_client(sequence):
    client = MagicMock()
    client.chat.completions.create.side_effect = list(sequence)
    return client


def _mock_extract(monkeypatch, extraction: dict | Exception):
    """Patch the protected ai_service boundary used by extraction."""
    if isinstance(extraction, Exception):
        ai = MagicMock()
        ai.call_structured.side_effect = extraction
    else:
        ai = AIService(client=mock_ai_client([text_response(json.dumps(extraction))]))
    monkeypatch.setattr(
        "knowledge_engine.extractor.get_ai_service", lambda: ai
    )


def _mock_fetch(monkeypatch, contents: dict[str, str | Exception]):
    """Patch the HTTP boundary: URL -> content (or a FetchError)."""

    def fake_fetch(url: str) -> str:
        value = contents.get(url, None)
        if value is None:
            raise ingestion_service.FetchError("HTTP 404 from source")
        if isinstance(value, Exception):
            raise value
        return value

    monkeypatch.setattr(ingestion_service, "_fetch_url", fake_fetch)


@pytest.fixture
def admin_auth(monkeypatch):
    """Known admin token + a ready Authorization header."""
    monkeypatch.setattr(settings, "ADMIN_TOKEN", ADMIN_TOKEN)
    return {"Authorization": f"Bearer {ADMIN_TOKEN}"}


# ---------------------------------------------------------------------------
# Pipeline — happy path
# ---------------------------------------------------------------------------


class TestUrlIngestionHappyPath:
    def test_stored_candidate_record(self, db_session, monkeypatch):
        _mock_fetch(monkeypatch, {"https://example.com/ai-intern": PAGE_HTML})
        _mock_extract(monkeypatch, EXTRACTION_JSON)

        result = ingestion_service.run_url_ingestion(
            db_session,
            urls=["https://example.com/ai-intern"],
            source_type="OFFICIAL_COMPANY",
        )
        assert result == {"run_id": 1, "queued_count": 1}

        item = db_session.query(IngestionItem).one()
        assert item.status == "STORED"
        assert item.opportunity_id == 1

        run = db_session.query(IngestionRun).one()
        assert run.status == "COMPLETED"
        assert run.successful_items == 1
        assert run.failed_items == 0

    def test_persisted_record_is_candidate_with_provenance(self, db_session, monkeypatch):
        _mock_fetch(monkeypatch, {"https://example.com/ai-intern": PAGE_HTML})
        _mock_extract(monkeypatch, EXTRACTION_JSON)
        ingestion_service.run_url_ingestion(
            db_session, urls=["https://example.com/ai-intern"]
        )

        record = db_session.query(Opportunity).one()
        # §11: ingested records are NEVER automatically verified.
        assert record.verification_status == "CANDIDATE"
        assert record.status == "ACTIVE"
        assert record.is_active is True
        assert record.source_url == "https://example.com/ai-intern"
        assert record.source_id == 1
        assert record.content_hash
        assert record.dedup_key
        assert record.retrieved_at is not None
        # Normalized values.
        assert record.type == "internship"
        assert record.title == "AI Research Intern"
        assert record.deadline == date(2027, 6, 15)
        assert json.loads(record.required_skills) == ["Python", "Machine Learning"]
        assert record.stipend_pkr == 40000

    def test_source_and_document_rows(self, db_session, monkeypatch):
        _mock_fetch(monkeypatch, {"https://example.com/ai-intern": PAGE_HTML})
        _mock_extract(monkeypatch, EXTRACTION_JSON)
        ingestion_service.run_url_ingestion(
            db_session,
            urls=["https://example.com/ai-intern"],
            source_type="OFFICIAL_COMPANY",
        )

        source = db_session.query(Source).one()
        assert source.source_type == "OFFICIAL_COMPANY"
        assert source.classification == "OFFICIAL"
        assert source.retrieval_method == "direct_fetch"
        assert source.domain == "example.com"
        assert source.retrieved_at is not None

        document = db_session.query(SourceDocument).one()
        assert document.raw_content == PAGE_HTML
        assert document.processing_status == "VALIDATED"
        assert document.extracted_json
        assert document.extraction_model == settings.QWEN_MODEL

    def test_candidate_record_hidden_from_students(self, client, db_session, monkeypatch):
        _mock_fetch(monkeypatch, {"https://example.com/ai-intern": PAGE_HTML})
        _mock_extract(monkeypatch, EXTRACTION_JSON)
        ingestion_service.run_url_ingestion(
            db_session, urls=["https://example.com/ai-intern"]
        )

        response = client.get("/api/v1/opportunities")
        body = response.json()
        # Empty result -> §10 envelope; non-empty -> a bare list.
        if isinstance(body, dict):
            assert body["opportunities"] == []
            assert "message" in body
        else:
            assert all(o["title"] != "AI Research Intern" for o in body)

    def test_fts_index_updated_for_new_record(self, db_session, monkeypatch):
        _mock_fetch(monkeypatch, {"https://example.com/ai-intern": PAGE_HTML})
        _mock_extract(monkeypatch, EXTRACTION_JSON)
        ingestion_service.run_url_ingestion(
            db_session, urls=["https://example.com/ai-intern"]
        )
        # Stage 8: the FTS INSERT triggers keep the index in sync.
        from sqlalchemy import text as sql_text

        row = db_session.execute(
            sql_text("SELECT COUNT(*) FROM opportunities_fts WHERE opportunities_fts MATCH 'research'")
        ).scalar()
        assert row == 1


# ---------------------------------------------------------------------------
# Pipeline — per-item failures
# ---------------------------------------------------------------------------


class TestPipelineFailures:
    def test_fetch_failure_marks_item_failed(self, db_session, monkeypatch):
        _mock_fetch(monkeypatch, {})  # unknown URL -> FetchError

        ingestion_service.run_url_ingestion(
            db_session, urls=["https://example.com/missing"]
        )

        item = db_session.query(IngestionItem).one()
        assert item.status == "FAILED"
        assert "404" in item.error_message
        run = db_session.query(IngestionRun).one()
        assert run.status == "FAILED"
        assert run.failed_items == 1

    def test_extraction_failure_marks_item_failed(self, db_session, monkeypatch):
        _mock_fetch(monkeypatch, {"https://example.com/ai-intern": PAGE_HTML})
        _mock_extract(monkeypatch, AIUnavailableError("provider down"))

        ingestion_service.run_url_ingestion(
            db_session, urls=["https://example.com/ai-intern"]
        )

        item = db_session.query(IngestionItem).one()
        assert item.status == "FAILED"
        assert "extraction failed" in item.error_message
        document = db_session.query(SourceDocument).one()
        assert document.processing_status == "FAILED"
        # Nothing persisted.
        assert db_session.query(Opportunity).count() == 0

    @pytest.mark.parametrize(
        "extraction, reason_fragment",
        [
            ({**EXTRACTION_JSON, "title": None}, "title"),
            ({**EXTRACTION_JSON, "title": "   "}, "title"),
            ({**EXTRACTION_JSON, "type": "fellowship"}, "invalid type"),
            ({**EXTRACTION_JSON, "deadline": "not-a-date"}, "deadline"),
            ({**EXTRACTION_JSON, "type": None}, "invalid type"),
        ],
    )
    def test_validation_failures(
        self, db_session, monkeypatch, extraction, reason_fragment
    ):
        _mock_fetch(monkeypatch, {"https://example.com/ai-intern": PAGE_HTML})
        _mock_extract(monkeypatch, extraction)

        ingestion_service.run_url_ingestion(
            db_session, urls=["https://example.com/ai-intern"]
        )

        item = db_session.query(IngestionItem).one()
        assert item.status == "FAILED"
        assert reason_fragment in item.error_message
        assert db_session.query(Opportunity).count() == 0

    def test_mixed_results_partial_run(self, db_session, monkeypatch):
        _mock_fetch(
            monkeypatch,
            {"https://example.com/good": PAGE_HTML},  # /bad -> FetchError
        )
        _mock_extract(monkeypatch, EXTRACTION_JSON)

        ingestion_service.run_url_ingestion(
            db_session,
            urls=["https://example.com/good", "https://example.com/bad"],
        )

        run = db_session.query(IngestionRun).one()
        assert run.status == "PARTIAL"
        assert run.successful_items == 1
        assert run.failed_items == 1
        statuses = {
            i.source_url: i.status
            for i in db_session.query(IngestionItem).all()
        }
        assert statuses == {
            "https://example.com/good": "STORED",
            "https://example.com/bad": "FAILED",
        }

    def test_one_bad_page_never_aborts_the_run(self, db_session, monkeypatch):
        # A page whose fetch raises an unexpected exception type is still
        # contained: the item fails, the run continues.
        def exploding_fetch(url: str) -> str:
            if url.endswith("boom"):
                raise RuntimeError("unexpected")
            return PAGE_HTML

        monkeypatch.setattr(ingestion_service, "_fetch_url", exploding_fetch)
        _mock_extract(monkeypatch, EXTRACTION_JSON)

        ingestion_service.run_url_ingestion(
            db_session,
            urls=["https://example.com/boom", "https://example.com/ok"],
        )
        run = db_session.query(IngestionRun).one()
        assert run.status == "PARTIAL"
        assert db_session.query(Opportunity).count() == 1


# ---------------------------------------------------------------------------
# Stage 2 skip — unchanged content
# ---------------------------------------------------------------------------


class TestUnchangedContent:
    def test_second_run_skips_extraction(self, db_session, monkeypatch):
        _mock_fetch(monkeypatch, {"https://example.com/ai-intern": PAGE_HTML})
        _mock_extract(monkeypatch, EXTRACTION_JSON)
        ingestion_service.run_url_ingestion(
            db_session, urls=["https://example.com/ai-intern"]
        )

        # Second run: same content — extraction must NOT be called.
        ai = MagicMock()
        ai.call_structured.side_effect = AssertionError("must not extract")
        monkeypatch.setattr(
            "knowledge_engine.extractor.get_ai_service", lambda: ai
        )

        result = ingestion_service.run_url_ingestion(
            db_session, urls=["https://example.com/ai-intern"]
        )

        items = (
            db_session.query(IngestionItem)
            .order_by(IngestionItem.id)
            .all()
        )
        assert [i.status for i in items] == ["STORED", "UNCHANGED"]
        assert result["run_id"] == 2
        # Still exactly one opportunity, one source.
        assert db_session.query(Opportunity).count() == 1
        assert db_session.query(Source).count() == 1
        assert db_session.query(SourceDocument).count() == 1

    def test_changed_content_re_extracts(self, db_session, monkeypatch):
        _mock_fetch(monkeypatch, {"https://example.com/ai-intern": PAGE_HTML})
        _mock_extract(monkeypatch, EXTRACTION_JSON)
        ingestion_service.run_url_ingestion(
            db_session, urls=["https://example.com/ai-intern"]
        )

        new_page = PAGE_HTML.replace("June 15, 2027", "July 1, 2027")
        _mock_fetch(monkeypatch, {"https://example.com/ai-intern": new_page})
        _mock_extract(
            monkeypatch, {**EXTRACTION_JSON, "deadline": "2027-07-01"}
        )
        ingestion_service.run_url_ingestion(
            db_session, urls=["https://example.com/ai-intern"]
        )

        items = (
            db_session.query(IngestionItem)
            .order_by(IngestionItem.id)
            .all()
        )
        assert [i.status for i in items] == ["STORED", "DUPLICATE"]
        # Same opportunity updated via dedup, no second record.
        assert db_session.query(Opportunity).count() == 1


# ---------------------------------------------------------------------------
# Refresh mode (master §12 mode C)
# ---------------------------------------------------------------------------


class TestRefreshSources:
    def test_no_stale_sources_queues_nothing(self, db_session, monkeypatch):
        result = ingestion_service.refresh_sources(db_session)
        assert result["queued_count"] == 0
        run = db_session.query(IngestionRun).one()
        assert run.status == "COMPLETED"
        assert run.total_items == 0

    def test_stale_source_is_refreshed(self, db_session, monkeypatch):
        _mock_fetch(monkeypatch, {"https://example.com/ai-intern": PAGE_HTML})
        _mock_extract(monkeypatch, EXTRACTION_JSON)
        ingestion_service.run_url_ingestion(
            db_session, urls=["https://example.com/ai-intern"]
        )
        # Age the source past the 7-day staleness window.
        source = db_session.query(Source).one()
        source.retrieved_at = datetime.utcnow() - timedelta(days=8)
        db_session.commit()

        result = ingestion_service.refresh_sources(db_session)
        assert result["queued_count"] == 1
        items = (
            db_session.query(IngestionItem)
            .order_by(IngestionItem.id)
            .all()
        )
        assert items[1].status == "UNCHANGED"

    def test_fresh_source_not_refreshed(self, db_session, monkeypatch):
        _mock_fetch(monkeypatch, {"https://example.com/ai-intern": PAGE_HTML})
        _mock_extract(monkeypatch, EXTRACTION_JSON)
        ingestion_service.run_url_ingestion(
            db_session, urls=["https://example.com/ai-intern"]
        )

        result = ingestion_service.refresh_sources(db_session)
        assert result["queued_count"] == 0


# ---------------------------------------------------------------------------
# Stage 9 — manual verification
# ---------------------------------------------------------------------------


class TestManualVerification:
    def _ingest_one(self, db_session, monkeypatch):
        _mock_fetch(monkeypatch, {"https://example.com/ai-intern": PAGE_HTML})
        _mock_extract(monkeypatch, EXTRACTION_JSON)
        ingestion_service.run_url_ingestion(
            db_session, urls=["https://example.com/ai-intern"]
        )

    def test_verify_sets_status_and_last_verified(self, db_session, monkeypatch):
        self._ingest_one(db_session, monkeypatch)
        record = ingestion_service.verify_opportunity(db_session, 1, "VALIDATED")
        assert record.verification_status == "VALIDATED"
        assert record.last_verified == date.today()

    def test_verified_record_visible_to_students(self, client, db_session, monkeypatch):
        self._ingest_one(db_session, monkeypatch)
        ingestion_service.verify_opportunity(db_session, 1, "VALIDATED")
        response = client.get("/api/v1/opportunities")
        body = response.json()
        opportunities = body if isinstance(body, list) else body["opportunities"]
        titles = [o["title"] for o in opportunities]
        assert "AI Research Intern" in titles

    def test_invalid_status_rejected(self, db_session, monkeypatch):
        self._ingest_one(db_session, monkeypatch)
        with pytest.raises(ValueError):
            ingestion_service.verify_opportunity(db_session, 1, "VERIFIED_SKIP")
        record = db_session.query(Opportunity).one()
        assert record.verification_status == "CANDIDATE"

    def test_unknown_opportunity_returns_none(self, db_session):
        assert ingestion_service.verify_opportunity(db_session, 999, "VALIDATED") is None


# ---------------------------------------------------------------------------
# Run status + data quality
# ---------------------------------------------------------------------------


class TestRunStatusAndDataQuality:
    def test_get_run_status_shape(self, db_session, monkeypatch):
        _mock_fetch(monkeypatch, {"https://example.com/ai-intern": PAGE_HTML})
        _mock_extract(monkeypatch, EXTRACTION_JSON)
        ingestion_service.run_url_ingestion(
            db_session, urls=["https://example.com/ai-intern"], run_label="weekly"
        )

        status = ingestion_service.get_run_status(db_session, 1)
        assert status["run_id"] == 1
        assert status["status"] == "COMPLETED"
        assert status["total_items"] == 1
        assert status["successful_items"] == 1
        assert len(status["items"]) == 1
        item = status["items"][0]
        assert item["source_url"] == "https://example.com/ai-intern"
        assert item["status"] == "STORED"
        assert item["opportunity_id"] == 1

    def test_get_run_status_unknown(self, db_session):
        assert ingestion_service.get_run_status(db_session, 999) is None

    def test_data_quality_counts(self, db_session, monkeypatch):
        _mock_fetch(monkeypatch, {"https://example.com/ai-intern": PAGE_HTML})
        _mock_extract(monkeypatch, EXTRACTION_JSON)
        ingestion_service.run_url_ingestion(
            db_session, urls=["https://example.com/ai-intern"]
        )
        db_session.add(
            Opportunity(
                type="job",
                title="Stale Old Job (template)",
                last_verified=date.today() - timedelta(days=45),
                deadline=soon(10),
                verification_status="VALIDATED",
                is_active=True,
            )
        )
        db_session.add(
            Opportunity(
                type="job",
                title="Expired Old Job (template)",
                deadline=date.today() - timedelta(days=5),
                verification_status="VALIDATED",
                is_active=True,
            )
        )
        db_session.commit()

        quality = ingestion_service.data_quality(db_session)
        assert quality["total_sources"] == 1
        assert quality["candidate_records"] == 1
        assert quality["stale_records"] == 1
        assert quality["expired_opportunities"] == 1
        assert quality["recent_run_summary"]["run_id"] == 1


# ---------------------------------------------------------------------------
# Retrieval (stage 2) unit tests — mocked httpx
# ---------------------------------------------------------------------------


class TestFetchUrl:
    def _patch_client(self, monkeypatch, response=None, error=None):
        client = MagicMock()
        if error is not None:
            client.__enter__ = MagicMock(return_value=client)
            client.__exit__ = MagicMock(return_value=False)
            client.get.side_effect = error
        else:
            client.__enter__ = MagicMock(return_value=client)
            client.__exit__ = MagicMock(return_value=False)
            client.get.return_value = response
        monkeypatch.setattr(ingestion_service.httpx, "Client", MagicMock(return_value=client))
        return client

    def test_success_returns_text_with_user_agent(self, monkeypatch):
        response = SimpleNamespace(
            status_code=200, text="<html>ok</html>", content=b"<html>ok</html>"
        )
        client = self._patch_client(monkeypatch, response=response)
        text = ingestion_service._fetch_url("https://example.com/x")
        assert text == "<html>ok</html>"
        _, kwargs = client.get.call_args
        assert kwargs["headers"]["User-Agent"].startswith("AHCareersBot/1.0")

    def test_http_error_status_raises_fetch_error(self, monkeypatch):
        response = SimpleNamespace(status_code=404, text="", content=b"")
        self._patch_client(monkeypatch, response=response)
        with pytest.raises(ingestion_service.FetchError, match="HTTP 404"):
            ingestion_service._fetch_url("https://example.com/x")

    def test_oversized_content_raises_fetch_error(self, monkeypatch):
        response = SimpleNamespace(
            status_code=200, text="x", content=b"x" * (ingestion_service.MAX_CONTENT_BYTES + 1)
        )
        self._patch_client(monkeypatch, response=response)
        with pytest.raises(ingestion_service.FetchError, match="too large"):
            ingestion_service._fetch_url("https://example.com/x")

    def test_transport_error_raises_fetch_error(self, monkeypatch):
        self._patch_client(monkeypatch, error=httpx.ConnectError("boom"))
        with pytest.raises(ingestion_service.FetchError):
            ingestion_service._fetch_url("https://example.com/x")


class TestHtmlToText:
    def test_strips_script_style_and_tags(self):
        html = (
            "<html><head><script>evil()</script><style>a{}</style></head>"
            "<body><h1>Intern</h1>  <p>Apply now</p></body></html>"
        )
        assert html_to_text(html) == "Intern Apply now"


# ---------------------------------------------------------------------------
# Admin endpoints (auth is covered further in test_security.py)
# ---------------------------------------------------------------------------


class TestAdminIngestionEndpoints:
    def test_ingest_url_endpoint_full_flow(self, client, db_session, monkeypatch, admin_auth):
        _mock_fetch(monkeypatch, {"https://example.com/ai-intern": PAGE_HTML})
        _mock_extract(monkeypatch, EXTRACTION_JSON)

        response = client.post(
            "/api/v1/admin/ingest/url",
            json={
                "urls": ["https://example.com/ai-intern"],
                "source_type": "OFFICIAL_COMPANY",
                "run_label": "smoke",
            },
            headers=admin_auth,
        )
        assert response.status_code == 200
        assert response.json() == {"run_id": 1, "queued_count": 1}

        run = client.get("/api/v1/admin/ingest/runs/1", headers=admin_auth)
        assert run.status_code == 200
        assert run.json()["status"] == "COMPLETED"

    def test_run_status_404(self, client, db_session, admin_auth):
        response = client.get("/api/v1/admin/ingest/runs/999", headers=admin_auth)
        assert response.status_code == 404

    @pytest.mark.parametrize(
        "urls, match",
        [
            (["ftp://example.com/x"], "valid http(s)"),
            (["not a url"], "valid http(s)"),
        ],
    )
    def test_invalid_url_scheme_422(self, client, db_session, admin_auth, urls, match):
        response = client.post(
            "/api/v1/admin/ingest/url",
            json={"urls": urls},
            headers=admin_auth,
        )
        assert response.status_code == 422
        assert match in response.json()["error"]

    def test_too_many_urls_422(self, client, db_session, admin_auth):
        response = client.post(
            "/api/v1/admin/ingest/url",
            json={"urls": [f"https://example.com/{i}" for i in range(51)]},
            headers=admin_auth,
        )
        assert response.status_code == 422

    def test_empty_url_list_422(self, client, db_session, admin_auth):
        response = client.post(
            "/api/v1/admin/ingest/url", json={"urls": []}, headers=admin_auth
        )
        assert response.status_code == 422

    def test_verify_endpoint_marks_validated(self, client, db_session, monkeypatch, admin_auth):
        _mock_fetch(monkeypatch, {"https://example.com/ai-intern": PAGE_HTML})
        _mock_extract(monkeypatch, EXTRACTION_JSON)
        client.post(
            "/api/v1/admin/ingest/url",
            json={"urls": ["https://example.com/ai-intern"]},
            headers=admin_auth,
        )

        response = client.post(
            "/api/v1/admin/opportunities/1/verify",
            json={"verification_status": "VALIDATED"},
            headers=admin_auth,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["verification_status"] == "VALIDATED"
        assert body["last_verified"] == date.today().isoformat()

    def test_verify_endpoint_404(self, client, db_session, admin_auth):
        response = client.post(
            "/api/v1/admin/opportunities/999/verify",
            json={"verification_status": "VALIDATED"},
            headers=admin_auth,
        )
        assert response.status_code == 404

    def test_verify_endpoint_rejects_bad_status(self, client, db_session, admin_auth):
        response = client.post(
            "/api/v1/admin/opportunities/1/verify",
            json={"verification_status": "VERIFIED_SKIP"},
            headers=admin_auth,
        )
        assert response.status_code == 422

    def test_data_quality_endpoint(self, client, db_session, admin_auth):
        response = client.get("/api/v1/admin/data-quality", headers=admin_auth)
        assert response.status_code == 200
        body = response.json()
        for key in (
            "total_sources",
            "verified_sources",
            "candidate_records",
            "stale_records",
            "expired_opportunities",
            "recent_run_summary",
        ):
            assert key in body
        assert body["recent_run_summary"] is None

    def test_refresh_endpoint(self, client, db_session, admin_auth):
        response = client.post(
            "/api/v1/admin/ingest/refresh", json={}, headers=admin_auth
        )
        assert response.status_code == 200
        assert response.json()["queued_count"] == 0
