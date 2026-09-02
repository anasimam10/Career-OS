"""
Step 5 — PKE Staging Review & Promotion tests.

Coverage:
  - Listing staging records by domain, status, pagination
  - review_staging_record: VERIFY, REJECT, RESET, invalid action
  - REJECTED → VERIFY blocked (must RESET first)
  - promote_staging_record:
      - Opportunity (scholarship)
      - SportsOpportunity (tournament)
      - University
      - Program
      - LearningResource
      - Idempotency (second promote returns same target_id)
      - Non-VERIFIED promotion blocked
      - Missing required field blocked
      - Invalid geography blocked
      - Unknown domain (no operational table)
  - Provenance preservation
  - Never-infer: null deadline, null fees preserved
  - Admin API routes: list, get, review, promote
"""

from __future__ import annotations

import json
from datetime import date

import pytest
from fastapi.testclient import TestClient

from config import settings
from database import get_db
from main import app
from knowledge_engine.staging import PKEStagingRecord
from knowledge_engine.staging_service import (
    StagingServiceError,
    STATUS_CANDIDATE,
    STATUS_REJECTED,
    STATUS_VERIFIED,
    get_staging_record,
    list_staging_records,
    promote_staging_record,
    review_staging_record,
)
from models.learning import LearningResource
from models.opportunity import Opportunity, SportsOpportunity
from models.university import Program, University

ADMIN_TOKEN = "test-admin-token"
ADMIN_HEADERS = {"Authorization": f"Bearer {ADMIN_TOKEN}"}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_staging(
    db,
    *,
    domain: str = "scholarships",
    verification_status: str = "CANDIDATE",
    data: dict | None = None,
    source_url: str = "https://hec.gov.pk/scholarships",
    source_id: int | None = None,
    dedup_key: str | None = None,
    content_hash: str | None = None,
) -> PKEStagingRecord:
    """Create and persist a minimal staging record for tests."""
    if data is None:
        data = {
            "title": "Test Scholarship",
            "organization": "HEC Pakistan",
            "location": "NATIONWIDE",
            "description": "A test scholarship record.",
            "required_skills": [],
        }
    record = PKEStagingRecord(
        domain=domain,
        extracted_json=json.dumps(data),
        source_url=source_url,
        source_id=source_id,
        content_hash=content_hash,
        dedup_key=dedup_key,
        verification_status=verification_status,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def _make_university_staging(db, name="Test Uni", city="Islamabad") -> PKEStagingRecord:
    return _make_staging(
        db,
        domain="universities",
        source_url="https://uni.edu.pk",
        data={
            "name": name,
            "short_name": "TU",
            "slug": f"test-uni-{name.lower().replace(' ', '-')}",
            "city": city,
            "province": "Islamabad",
            "type": "PUBLIC",
            "hec_recognized": True,
            "website_url": "https://uni.edu.pk",
        },
    )


@pytest.fixture(scope="function")
def client(db_session, monkeypatch):
    """TestClient with ADMIN_TOKEN patched so admin routes work."""
    monkeypatch.setattr(settings, "ADMIN_TOKEN", ADMIN_TOKEN)

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Listing tests
# ---------------------------------------------------------------------------


class TestListStagingRecords:
    def test_list_all_empty(self, db_session):
        records, total = list_staging_records(db_session)
        assert records == []
        assert total == 0

    def test_list_all_returns_records(self, db_session):
        _make_staging(db_session, domain="scholarships")
        _make_staging(db_session, domain="internships")
        records, total = list_staging_records(db_session)
        assert total == 2
        assert len(records) == 2

    def test_filter_by_domain(self, db_session):
        _make_staging(db_session, domain="scholarships")
        _make_staging(db_session, domain="internships")
        records, total = list_staging_records(db_session, domain="scholarships")
        assert total == 1
        assert records[0].domain == "scholarships"

    def test_filter_by_status(self, db_session):
        _make_staging(db_session, verification_status="CANDIDATE")
        _make_staging(db_session, verification_status="VERIFIED")
        records, total = list_staging_records(db_session, status="CANDIDATE")
        assert total == 1
        assert records[0].verification_status == "CANDIDATE"

    def test_pagination_skip(self, db_session):
        for i in range(5):
            _make_staging(db_session, domain="scholarships")
        records, total = list_staging_records(db_session, skip=3, limit=10)
        assert total == 5
        assert len(records) == 2

    def test_pagination_limit(self, db_session):
        for i in range(5):
            _make_staging(db_session, domain="scholarships")
        records, total = list_staging_records(db_session, limit=2)
        assert total == 5
        assert len(records) == 2

    def test_ordering_is_stable(self, db_session):
        r1 = _make_staging(db_session)
        r2 = _make_staging(db_session)
        records, _ = list_staging_records(db_session)
        # Descending by id → newest first
        assert records[0].id == r2.id
        assert records[1].id == r1.id


# ---------------------------------------------------------------------------
# Review action tests
# ---------------------------------------------------------------------------


class TestReviewStagingRecord:
    def test_verify_candidate(self, db_session):
        record = _make_staging(db_session)
        updated = review_staging_record(db_session, record.id, "VERIFY")
        assert updated.verification_status == STATUS_VERIFIED

    def test_reject_candidate(self, db_session):
        record = _make_staging(db_session)
        updated = review_staging_record(db_session, record.id, "REJECT")
        assert updated.verification_status == STATUS_REJECTED

    def test_reset_verified_to_candidate(self, db_session):
        record = _make_staging(db_session, verification_status="VERIFIED")
        updated = review_staging_record(db_session, record.id, "RESET")
        assert updated.verification_status == STATUS_CANDIDATE

    def test_invalid_action_raises(self, db_session):
        record = _make_staging(db_session)
        with pytest.raises(StagingServiceError, match="Invalid action"):
            review_staging_record(db_session, record.id, "APPROVE_EVERYTHING")

    def test_missing_record_raises(self, db_session):
        with pytest.raises(StagingServiceError, match="not found"):
            review_staging_record(db_session, 99999, "VERIFY")

    def test_verify_rejected_raises(self, db_session):
        record = _make_staging(db_session, verification_status="REJECTED")
        with pytest.raises(StagingServiceError, match="RESET"):
            review_staging_record(db_session, record.id, "VERIFY")

    def test_reset_then_verify(self, db_session):
        record = _make_staging(db_session, verification_status="REJECTED")
        review_staging_record(db_session, record.id, "RESET")
        updated = review_staging_record(db_session, record.id, "VERIFY")
        assert updated.verification_status == STATUS_VERIFIED

    def test_case_insensitive_action(self, db_session):
        record = _make_staging(db_session)
        updated = review_staging_record(db_session, record.id, "verify")
        assert updated.verification_status == STATUS_VERIFIED


# ---------------------------------------------------------------------------
# Promotion — Opportunity
# ---------------------------------------------------------------------------


class TestPromoteOpportunity:
    def test_promotes_scholarship(self, db_session):
        record = _make_staging(db_session, verification_status="VERIFIED", domain="scholarships")
        result = promote_staging_record(db_session, record.id)
        assert result["promoted"] is True
        assert result["target_table"] == "opportunities"
        opp = db_session.get(Opportunity, result["target_id"])
        assert opp.type == "scholarship"
        assert opp.verification_status == STATUS_VERIFIED

    def test_provenance_preserved(self, db_session):
        record = _make_staging(
            db_session,
            verification_status="VERIFIED",
            domain="scholarships",
            source_url="https://hec.gov.pk/scholarship-42",
            source_id=7,
            content_hash="abc123",
        )
        result = promote_staging_record(db_session, record.id)
        opp = db_session.get(Opportunity, result["target_id"])
        assert opp.source_url == "https://hec.gov.pk/scholarship-42"
        assert opp.source_id == 7
        assert opp.content_hash == "abc123"

    def test_deadline_preserved_as_null(self, db_session):
        """deadline=null in source must remain null — never inferred."""
        record = _make_staging(
            db_session,
            verification_status="VERIFIED",
            domain="scholarships",
            data={
                "title": "No-Deadline Scholarship",
                "organization": "HEC",
                "location": "NATIONWIDE",
                "deadline": None,
            },
        )
        result = promote_staging_record(db_session, record.id)
        opp = db_session.get(Opportunity, result["target_id"])
        assert opp.deadline is None

    def test_fee_preserved_as_null(self, db_session):
        """annual_fee_pkr=null must remain null."""
        record = _make_staging(
            db_session,
            verification_status="VERIFIED",
            domain="scholarships",
            data={
                "title": "Fee-Unknown Scholarship",
                "organization": "HEC",
                "location": "NATIONWIDE",
                "annual_fee_pkr": None,
            },
        )
        result = promote_staging_record(db_session, record.id)
        # annual_fee_pkr is not on Opportunity; just ensure no crash
        assert result["promoted"] is True

    def test_blocks_non_verified(self, db_session):
        record = _make_staging(db_session, verification_status="CANDIDATE", domain="scholarships")
        with pytest.raises(StagingServiceError, match="VERIFIED"):
            promote_staging_record(db_session, record.id)

    def test_blocks_rejected(self, db_session):
        record = _make_staging(db_session, verification_status="REJECTED", domain="scholarships")
        with pytest.raises(StagingServiceError, match="VERIFIED"):
            promote_staging_record(db_session, record.id)

    def test_blocks_invalid_geography(self, db_session):
        record = _make_staging(
            db_session,
            verification_status="VERIFIED",
            domain="scholarships",
            data={
                "title": "Peshawar Scholarship",
                "organization": "X",
                "location": "Peshawar",  # NOT in MVP geography
            },
        )
        with pytest.raises(StagingServiceError, match="not in the MVP city list"):
            promote_staging_record(db_session, record.id)

    def test_idempotent_promotion(self, db_session):
        """Calling promote twice must return the same target_id, not insert a duplicate."""
        record = _make_staging(db_session, verification_status="VERIFIED", domain="scholarships",
                               dedup_key="test-dedup-abc")
        r1 = promote_staging_record(db_session, record.id)
        r2 = promote_staging_record(db_session, record.id)
        assert r1["target_id"] == r2["target_id"]
        assert r2["promoted"] is False
        # Confirm only one row in DB
        count = db_session.query(Opportunity).filter(
            Opportunity.dedup_key == "test-dedup-abc"
        ).count()
        assert count == 1

    def test_blocks_missing_title(self, db_session):
        record = _make_staging(
            db_session,
            verification_status="VERIFIED",
            domain="scholarships",
            data={"organization": "HEC", "location": "NATIONWIDE"},
        )
        with pytest.raises(StagingServiceError, match="title"):
            promote_staging_record(db_session, record.id)


# ---------------------------------------------------------------------------
# Promotion — Sports
# ---------------------------------------------------------------------------


class TestPromoteSports:
    def test_promotes_tournament(self, db_session):
        record = _make_staging(
            db_session,
            domain="tournaments",
            verification_status="VERIFIED",
            data={
                "title": "PCB Junior Tournament",
                "sport": "Cricket",
                "organization": "PCB",
                "location": "Karachi",
            },
        )
        result = promote_staging_record(db_session, record.id)
        assert result["promoted"] is True
        assert result["target_table"] == "sports_opportunities"
        row = db_session.get(SportsOpportunity, result["target_id"])
        assert row.type == "tournament"
        assert row.verification_status == STATUS_VERIFIED

    def test_sports_idempotency(self, db_session):
        data = {
            "title": "Lahore Cup",
            "sport": "Football",
            "location": "Lahore",
        }
        r1 = _make_staging(db_session, domain="tournaments", verification_status="VERIFIED",
                           data=data, dedup_key="lahore-cup-2026")
        res1 = promote_staging_record(db_session, r1.id)
        res2 = promote_staging_record(db_session, r1.id)
        assert res1["target_id"] == res2["target_id"]
        assert res2["promoted"] is False


# ---------------------------------------------------------------------------
# Promotion — University
# ---------------------------------------------------------------------------


class TestPromoteUniversity:
    def test_promotes_university(self, db_session):
        record = _make_university_staging(db_session)
        record.verification_status = STATUS_VERIFIED
        db_session.commit()
        result = promote_staging_record(db_session, record.id)
        assert result["promoted"] is True
        assert result["target_table"] == "universities"
        uni = db_session.get(University, result["target_id"])
        assert uni.verification_status == STATUS_VERIFIED
        assert uni.city == "Islamabad"

    def test_university_idempotent_by_slug(self, db_session):
        record = _make_university_staging(db_session, name="Unique College")
        record.verification_status = STATUS_VERIFIED
        db_session.commit()
        r1 = promote_staging_record(db_session, record.id)
        r2 = promote_staging_record(db_session, record.id)
        assert r1["target_id"] == r2["target_id"]
        assert r2["promoted"] is False

    def test_blocks_invalid_city(self, db_session):
        record = _make_staging(
            db_session,
            domain="universities",
            verification_status="VERIFIED",
            data={"name": "Quetta Uni", "city": "Quetta", "slug": "quetta-uni"},
        )
        with pytest.raises(StagingServiceError, match="not in the MVP city list"):
            promote_staging_record(db_session, record.id)

    def test_blocks_missing_name(self, db_session):
        record = _make_staging(
            db_session, domain="universities", verification_status="VERIFIED",
            data={"city": "Karachi"},
        )
        with pytest.raises(StagingServiceError, match="name"):
            promote_staging_record(db_session, record.id)


# ---------------------------------------------------------------------------
# Promotion — Program
# ---------------------------------------------------------------------------


class TestPromoteProgram:
    def test_promotes_program(self, db_session):
        # First insert a university
        uni = University(
            name="Test University",
            slug="test-university",
            city="Lahore",
            verification_status="VERIFIED",
        )
        db_session.add(uni)
        db_session.commit()
        db_session.refresh(uni)

        record = _make_staging(
            db_session, domain="programs", verification_status="VERIFIED",
            data={
                "name": "BS Computer Science",
                "degree_type": "BS",
                "field": "Computer Science",
                "university_id": uni.id,
                "duration_years": 4,
                "annual_fee_pkr": None,  # not known
            },
        )
        result = promote_staging_record(db_session, record.id)
        assert result["promoted"] is True
        prog = db_session.get(Program, result["target_id"])
        assert prog.annual_fee_pkr is None  # never-infer: preserved
        assert prog.verification_status == STATUS_VERIFIED

    def test_program_idempotent(self, db_session):
        uni = University(
            name="Test University 2", slug="test-university-2",
            city="Karachi", verification_status="VERIFIED",
        )
        db_session.add(uni)
        db_session.commit()
        db_session.refresh(uni)

        data = {"name": "BS EE", "degree_type": "BS", "field": "EE", "university_id": uni.id}
        record = _make_staging(db_session, domain="programs", verification_status="VERIFIED", data=data)
        r1 = promote_staging_record(db_session, record.id)
        r2 = promote_staging_record(db_session, record.id)
        assert r1["target_id"] == r2["target_id"]

    def test_blocks_missing_university(self, db_session):
        record = _make_staging(
            db_session, domain="programs", verification_status="VERIFIED",
            data={"name": "BS CS", "degree_type": "BS"},  # no university_id
        )
        with pytest.raises(StagingServiceError, match="university"):
            promote_staging_record(db_session, record.id)


# ---------------------------------------------------------------------------
# Promotion — Learning Resource
# ---------------------------------------------------------------------------


class TestPromoteLearningResource:
    def test_promotes_learning_resource(self, db_session):
        record = _make_staging(
            db_session, domain="learning_resources", verification_status="VERIFIED",
            data={
                "title": "Python for Beginners",
                "skill_name": "Python",
                "provider": "Test Provider",
                "url": "https://example.com/python",
                "is_free": True,
                "duration_hours": None,  # never-infer: must stay null
            },
        )
        result = promote_staging_record(db_session, record.id)
        assert result["promoted"] is True
        lr = db_session.get(LearningResource, result["target_id"])
        assert lr.duration_hours is None
        assert lr.is_free is True
        assert lr.verification_status == STATUS_VERIFIED

    def test_learning_resource_idempotent(self, db_session):
        data = {
            "title": "SQL Basics",
            "url": "https://example.com/sql",
            "skill_name": "SQL",
        }
        record = _make_staging(db_session, domain="learning_resources",
                               verification_status="VERIFIED", data=data)
        r1 = promote_staging_record(db_session, record.id)
        r2 = promote_staging_record(db_session, record.id)
        assert r1["target_id"] == r2["target_id"]


# ---------------------------------------------------------------------------
# Promotion — unknown domain (no operational table)
# ---------------------------------------------------------------------------


class TestPromoteUnknownDomain:
    def test_unknown_domain_returns_not_promoted(self, db_session):
        record = _make_staging(
            db_session, domain="schools", verification_status="VERIFIED",
            data={"name": "Test School", "city": "Islamabad"},
        )
        result = promote_staging_record(db_session, record.id)
        assert result["promoted"] is False
        assert "schools" in result["message"]


# ---------------------------------------------------------------------------
# Admin API tests
# ---------------------------------------------------------------------------


class TestAdminStagingAPI:
    """Integration tests for the admin /pke/staging endpoints."""

    def test_list_returns_200(self, client, db_session):
        _make_staging(db_session)
        resp = client.get("/api/v1/admin/pke/staging", headers=ADMIN_HEADERS)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1
        assert "items" in body

    def test_list_domain_filter(self, client, db_session):
        _make_staging(db_session, domain="scholarships")
        _make_staging(db_session, domain="internships")
        resp = client.get(
            "/api/v1/admin/pke/staging?domain=scholarships", headers=ADMIN_HEADERS
        )
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["domain"] == "scholarships"

    def test_get_single_record(self, client, db_session):
        record = _make_staging(db_session)
        resp = client.get(
            f"/api/v1/admin/pke/staging/{record.id}", headers=ADMIN_HEADERS
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == record.id

    def test_get_missing_returns_404(self, client):
        resp = client.get("/api/v1/admin/pke/staging/99999", headers=ADMIN_HEADERS)
        assert resp.status_code == 404

    def test_review_verify(self, client, db_session):
        record = _make_staging(db_session)
        resp = client.post(
            f"/api/v1/admin/pke/staging/{record.id}/review",
            json={"action": "VERIFY"},
            headers=ADMIN_HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["verification_status"] == "VERIFIED"

    def test_review_reject(self, client, db_session):
        record = _make_staging(db_session)
        resp = client.post(
            f"/api/v1/admin/pke/staging/{record.id}/review",
            json={"action": "REJECT"},
            headers=ADMIN_HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["verification_status"] == "REJECTED"

    def test_review_invalid_action(self, client, db_session):
        record = _make_staging(db_session)
        resp = client.post(
            f"/api/v1/admin/pke/staging/{record.id}/review",
            json={"action": "MAKE_IT_REAL"},
            headers=ADMIN_HEADERS,
        )
        assert resp.status_code == 422  # Pydantic Literal validation

    def test_promote_success(self, client, db_session):
        record = _make_staging(db_session, verification_status="VERIFIED", domain="scholarships")
        resp = client.post(
            f"/api/v1/admin/pke/staging/{record.id}/promote",
            headers=ADMIN_HEADERS,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["promoted"] is True
        assert body["target_table"] == "opportunities"

    def test_promote_candidate_blocked(self, client, db_session):
        record = _make_staging(db_session, verification_status="CANDIDATE", domain="scholarships")
        resp = client.post(
            f"/api/v1/admin/pke/staging/{record.id}/promote",
            headers=ADMIN_HEADERS,
        )
        assert resp.status_code == 400

    def test_requires_admin_auth(self, client, db_session):
        record = _make_staging(db_session)
        resp = client.get(f"/api/v1/admin/pke/staging/{record.id}")
        assert resp.status_code == 401
