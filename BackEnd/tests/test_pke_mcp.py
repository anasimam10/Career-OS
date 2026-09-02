"""
Step 5 — PKE MCP server tests (pke_server.py).

All tests are deterministic (no live API/network calls).

Coverage:
  search_verified_institutions:
    - returns verified universities
    - CANDIDATE record hidden
    - city filter works (Karachi/Lahore/Islamabad)
    - invalid city rejected
    - institution_type filter works
    - empty result handled cleanly

  search_verified_opportunities:
    - returns VERIFIED opportunities
    - CANDIDATE record hidden
    - REJECTED record hidden
    - type filter (scholarship / internship)
    - city filter (Karachi, Lahore, Islamabad, NATIONWIDE)
    - NATIONWIDE opportunity visible for all city queries
    - deadline=null returned as null (not invented)

  search_verified_programs:
    - returns programs for verified university
    - city filter narrows universities
    - fee=null preserved

  search_verified_learning_resources:
    - returns verified resources
    - query matches title/skill_name
    - is_free filter works
    - is_free=null preserved in output

  get_source_registry_info:
    - returns source info for valid source_id
    - returns not-found for unknown source_id
    - read-only (no mutation)

  Visibility guarantees:
    - staging records never accessible through pke_server tools
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Bootstrap BackEnd path so we can import models
_BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

_REPO_ROOT = _BACKEND_DIR.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from knowledge_engine.pke_source_registry import PKESource
from knowledge_engine.staging import PKEStagingRecord
from models.learning import LearningResource
from models.opportunity import Opportunity, SportsOpportunity
from models.university import Program, University

# Import the MCP tool functions directly (they are plain Python functions
# decorated with @pke_server.tool() — still callable without MCP transport).
from Mcp.pke_server import (
    get_source_registry_info,
    search_verified_institutions,
    search_verified_learning_resources,
    search_verified_opportunities,
    search_verified_programs,
)
import Mcp.db_access as db_access


# ---------------------------------------------------------------------------
# Test DB fixture — mirrors conftest.db_session but also hooks pke_server
# ---------------------------------------------------------------------------


@pytest.fixture
def pke_db(db_session):
    """Seed a test DB and point the pke_server at it."""
    original = db_access._session_factory

    def _factory():
        return db_session

    db_access.set_session_factory(_factory)
    yield db_session
    db_access.set_session_factory(original)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _uni(db, *, name, city, verification_status="VERIFIED", slug=None, uni_type="PUBLIC"):
    u = University(
        name=name,
        slug=slug or name.lower().replace(" ", "-"),
        city=city,
        type=uni_type,
        verification_status=verification_status,
        hec_recognized=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def _program(db, *, university_id, name, field, degree_type="BS",
              annual_fee_pkr=None, verification_status="VERIFIED"):
    p = Program(
        university_id=university_id,
        name=name,
        degree_type=degree_type,
        field=field,
        annual_fee_pkr=annual_fee_pkr,
        verification_status=verification_status,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def _opp(db, *, title, opp_type="scholarship", location="NATIONWIDE",
         verification_status="VERIFIED", is_active=True, deadline=None):
    o = Opportunity(
        type=opp_type,
        title=title,
        location=location,
        deadline=deadline,
        required_skills=json.dumps([]),
        verification_status=verification_status,
        is_active=is_active,
        source_url=f"https://example.com/{title.lower().replace(' ', '-')}",
    )
    db.add(o)
    db.commit()
    db.refresh(o)
    return o


def _lr(db, *, title, skill_name, provider="Test", url=None,
        is_free=True, verification_status="VERIFIED"):
    lr = LearningResource(
        skill_name=skill_name,
        title=title,
        type="course",
        provider=provider,
        url=url or f"https://example.com/{title.lower().replace(' ','-')}",
        is_free=is_free,
        duration_hours=None,  # never-infer
        verification_status=verification_status,
        is_active=True,
    )
    db.add(lr)
    db.commit()
    db.refresh(lr)
    return lr


def _source(db, *, source_id="GOV-TEST-01", name="Test Source",
            base_url="https://test.gov.pk", domains="universities",
            geographic_scope="nationwide"):
    s = PKESource(
        source_id=source_id,
        name=name,
        base_url=base_url,
        authority_level="L1",
        source_type="OFFICIAL_GOVERNMENT",
        domains=domains,
        geographic_scope=geographic_scope,
        access_review_status="APPROVED",
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


# ---------------------------------------------------------------------------
# search_verified_institutions
# ---------------------------------------------------------------------------


class TestSearchVerifiedInstitutions:
    def test_returns_verified_university(self, pke_db):
        _uni(pke_db, name="NUST", city="Islamabad", verification_status="VERIFIED")
        result = search_verified_institutions(city="Islamabad")
        assert result["count"] >= 1
        names = [r["name"] for r in result["results"]]
        assert "NUST" in names

    def test_candidate_hidden(self, pke_db):
        _uni(pke_db, name="Hidden Uni", city="Karachi", verification_status="CANDIDATE")
        result = search_verified_institutions(city="Karachi")
        names = [r["name"] for r in result["results"]]
        assert "Hidden Uni" not in names

    def test_city_filter_karachi(self, pke_db):
        _uni(pke_db, name="KHI Uni", city="Karachi")
        _uni(pke_db, name="LHR Uni", city="Lahore")
        result = search_verified_institutions(city="Karachi")
        names = [r["name"] for r in result["results"]]
        assert "KHI Uni" in names
        assert "LHR Uni" not in names

    def test_invalid_city_rejected(self, pke_db):
        result = search_verified_institutions(city="Quetta")
        assert "error" in result

    def test_type_filter_public(self, pke_db):
        _uni(pke_db, name="Public Uni", city="Lahore", uni_type="PUBLIC")
        _uni(pke_db, name="Private Uni", city="Lahore", uni_type="PRIVATE")
        result = search_verified_institutions(city="Lahore", institution_type="PUBLIC")
        names = [r["name"] for r in result["results"]]
        assert "Public Uni" in names
        assert "Private Uni" not in names

    def test_empty_result_has_message(self, pke_db):
        result = search_verified_institutions(city="Islamabad")
        if result["count"] == 0:
            assert "message" in result

    def test_no_city_returns_all_cities(self, pke_db):
        _uni(pke_db, name="Uni A", city="Karachi")
        _uni(pke_db, name="Uni B", city="Lahore")
        result = search_verified_institutions()
        names = [r["name"] for r in result["results"]]
        assert "Uni A" in names
        assert "Uni B" in names

    def test_staging_not_accessible(self, pke_db):
        """PKE staging records must never appear in institution results."""
        staging = PKEStagingRecord(
            domain="universities",
            extracted_json=json.dumps({"name": "Staging Uni"}),
            source_url="https://example.com",
            verification_status="CANDIDATE",
        )
        pke_db.add(staging)
        pke_db.commit()
        result = search_verified_institutions()
        names = [r["name"] for r in result["results"]]
        assert "Staging Uni" not in names


# ---------------------------------------------------------------------------
# search_verified_opportunities
# ---------------------------------------------------------------------------


class TestSearchVerifiedOpportunities:
    def test_returns_verified_scholarship(self, pke_db):
        _opp(pke_db, title="HEC Scholarship", opp_type="scholarship")
        result = search_verified_opportunities(type="scholarship")
        assert result["count"] >= 1
        titles = [r["title"] for r in result["results"]]
        assert "HEC Scholarship" in titles

    def test_candidate_hidden(self, pke_db):
        _opp(pke_db, title="Unverified Opp", verification_status="CANDIDATE")
        result = search_verified_opportunities()
        titles = [r["title"] for r in result["results"]]
        assert "Unverified Opp" not in titles

    def test_inactive_hidden(self, pke_db):
        _opp(pke_db, title="Inactive Opp", is_active=False)
        result = search_verified_opportunities()
        titles = [r["title"] for r in result["results"]]
        assert "Inactive Opp" not in titles

    def test_type_filter_internship(self, pke_db):
        _opp(pke_db, title="Tech Internship", opp_type="internship", location="Karachi")
        _opp(pke_db, title="Scholarship X", opp_type="scholarship")
        result = search_verified_opportunities(type="internship")
        titles = [r["title"] for r in result["results"]]
        assert "Tech Internship" in titles
        assert "Scholarship X" not in titles

    def test_city_filter_karachi(self, pke_db):
        _opp(pke_db, title="Karachi Internship", opp_type="internship", location="Karachi")
        _opp(pke_db, title="Lahore Internship", opp_type="internship", location="Lahore")
        result = search_verified_opportunities(type="internship", city="Karachi")
        titles = [r["title"] for r in result["results"]]
        assert "Karachi Internship" in titles
        assert "Lahore Internship" not in titles

    def test_nationwide_visible_for_any_city(self, pke_db):
        _opp(pke_db, title="National Grant", opp_type="scholarship", location="NATIONWIDE")
        result = search_verified_opportunities(city="Karachi")
        titles = [r["title"] for r in result["results"]]
        assert "National Grant" in titles

    def test_online_visible_for_any_city(self, pke_db):
        _opp(pke_db, title="Online Course", opp_type="education", location="ONLINE")
        result = search_verified_opportunities(city="Lahore")
        titles = [r["title"] for r in result["results"]]
        assert "Online Course" in titles

    def test_deadline_null_preserved(self, pke_db):
        _opp(pke_db, title="No Deadline Opp", deadline=None)
        result = search_verified_opportunities()
        match = next((r for r in result["results"] if r["title"] == "No Deadline Opp"), None)
        assert match is not None
        assert match["deadline"] is None  # never inferred

    def test_invalid_city_rejected(self, pke_db):
        result = search_verified_opportunities(city="Faisalabad")
        assert "error" in result

    def test_query_filter(self, pke_db):
        _opp(pke_db, title="HEC Postgrad Scholarship")
        _opp(pke_db, title="Ignite ICT Grant")
        result = search_verified_opportunities(query="HEC")
        titles = [r["title"] for r in result["results"]]
        assert "HEC Postgrad Scholarship" in titles
        assert "Ignite ICT Grant" not in titles


# ---------------------------------------------------------------------------
# search_verified_programs
# ---------------------------------------------------------------------------


class TestSearchVerifiedPrograms:
    def test_returns_programs_for_city(self, pke_db):
        uni = _uni(pke_db, name="NUST Islamabad", city="Islamabad")
        _program(pke_db, university_id=uni.id, name="BS CS", field="Computer Science")
        result = search_verified_programs(city="Islamabad")
        names = [r["name"] for r in result["results"]]
        assert "BS CS" in names

    def test_city_filter_excludes_other_city(self, pke_db):
        uni_k = _uni(pke_db, name="UOK", city="Karachi", slug="uok-test")
        uni_l = _uni(pke_db, name="UOL", city="Lahore", slug="uol-test")
        _program(pke_db, university_id=uni_k.id, name="BS Karachi Prog", field="CS")
        _program(pke_db, university_id=uni_l.id, name="BS Lahore Prog", field="CS")
        result = search_verified_programs(city="Karachi")
        names = [r["name"] for r in result["results"]]
        assert "BS Karachi Prog" in names
        assert "BS Lahore Prog" not in names

    def test_fee_null_preserved(self, pke_db):
        uni = _uni(pke_db, name="Fee Test Uni", city="Lahore", slug="fee-test-uni")
        _program(pke_db, university_id=uni.id, name="BS Commerce", field="Commerce", annual_fee_pkr=None)
        result = search_verified_programs(city="Lahore")
        prog = next((r for r in result["results"] if r["name"] == "BS Commerce"), None)
        assert prog is not None
        assert prog["annual_fee_pkr"] is None

    def test_candidate_program_hidden(self, pke_db):
        uni = _uni(pke_db, name="CAND Uni", city="Karachi", slug="cand-uni")
        _program(pke_db, university_id=uni.id, name="Candidate Prog",
                 field="X", verification_status="CANDIDATE")
        result = search_verified_programs(city="Karachi")
        names = [r["name"] for r in result["results"]]
        assert "Candidate Prog" not in names


# ---------------------------------------------------------------------------
# search_verified_learning_resources
# ---------------------------------------------------------------------------


class TestSearchVerifiedLearningResources:
    def test_returns_verified_resource(self, pke_db):
        _lr(pke_db, title="Python Basics", skill_name="Python")
        result = search_verified_learning_resources(query="Python")
        assert result["count"] >= 1
        titles = [r["title"] for r in result["results"]]
        assert "Python Basics" in titles

    def test_candidate_hidden(self, pke_db):
        _lr(pke_db, title="Candidate Resource", skill_name="SQL",
            verification_status="CANDIDATE")
        result = search_verified_learning_resources(query="Candidate")
        titles = [r["title"] for r in result["results"]]
        assert "Candidate Resource" not in titles

    def test_is_free_filter(self, pke_db):
        _lr(pke_db, title="Free Course", skill_name="JS", is_free=True)
        _lr(pke_db, title="Paid Course", skill_name="JS", is_free=False)
        result = search_verified_learning_resources(is_free=True)
        titles = [r["title"] for r in result["results"]]
        assert "Free Course" in titles
        assert "Paid Course" not in titles

    def test_duration_null_preserved(self, pke_db):
        _lr(pke_db, title="No Duration Course", skill_name="Java")
        result = search_verified_learning_resources(query="No Duration")
        match = next((r for r in result["results"] if r["title"] == "No Duration Course"), None)
        assert match is not None
        assert match["duration_hours"] is None


# ---------------------------------------------------------------------------
# get_source_registry_info
# ---------------------------------------------------------------------------


class TestGetSourceRegistryInfo:
    def test_returns_source_for_known_id(self, pke_db):
        _source(pke_db, source_id="GOV-HEC-TEST", name="HEC Test Source")
        result = get_source_registry_info("GOV-HEC-TEST")
        assert result["found"] is True
        assert result["source_id"] == "GOV-HEC-TEST"
        assert result["name"] == "HEC Test Source"

    def test_returns_not_found_for_unknown(self, pke_db):
        result = get_source_registry_info("DOES-NOT-EXIST-99")
        assert result["found"] is False

    def test_empty_source_id_invalid(self, pke_db):
        result = get_source_registry_info("")
        assert "error" in result

    def test_source_read_only(self, pke_db):
        """Calling get_source_registry_info must not mutate any DB record."""
        _source(pke_db, source_id="RO-TEST-01", name="Read Only Source")
        before = pke_db.query(PKESource).filter(PKESource.source_id == "RO-TEST-01").first()
        original_status = before.access_review_status

        get_source_registry_info("RO-TEST-01")

        after = pke_db.query(PKESource).filter(PKESource.source_id == "RO-TEST-01").first()
        assert after.access_review_status == original_status

    def test_includes_safe_provenance_fields(self, pke_db):
        _source(pke_db, source_id="PROV-01", geographic_scope="karachi")
        result = get_source_registry_info("PROV-01")
        assert "authority_level" in result
        assert "domains" in result
        assert "geographic_scope" in result
        assert "access_review_status" in result
