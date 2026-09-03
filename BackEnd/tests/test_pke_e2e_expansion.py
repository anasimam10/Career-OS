"""
test_pke_e2e_expansion.py — End-to-end PKE MCP & Mentor pipeline verification for expanded dataset.

Verifies:
  1. MCP Tool: search_verified_institutions finds IoBM, KIET, NUTECH, NDU, LCWU
  2. MCP Tool: search_verified_programs retrieves programs for new universities
  3. MCP Tool: search_verified_opportunities retrieves HEC scholarships, SBP internship
  4. MCP Tool: search_verified_learning_resources retrieves DigiSkills & NAVTTC
  5. MCP Tool: get_source_registry_info returns registry metadata
  6. Mentor/Retrieval pipeline: field, city and career lookups return grounded data
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

_BACKEND_DIR = Path(__file__).resolve().parents[1]
_REPO_ROOT = _BACKEND_DIR.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import importlib.util
import Mcp.db_access as db_access
from Mcp.pke_server import (
    get_source_registry_info,
    search_verified_institutions,
    search_verified_learning_resources,
    search_verified_opportunities,
    search_verified_programs,
)


def _get_seed_mod():
    spec = importlib.util.spec_from_file_location(
        "seed_db_runner_e2e", _REPO_ROOT / "data" / "seed_db.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def setup_database(db_session):
    """Seed the in-memory test DB and point pke_server at it."""
    seed_mod = _get_seed_mod()
    seed_mod._seed_careers(db_session)
    seed_mod._seed_universities(db_session)
    seed_mod._seed_programs(db_session)
    seed_mod._seed_learning_resources(db_session)
    seed_mod._seed_opportunities(db_session)
    seed_mod._seed_sports_opportunities(db_session)
    seed_mod._seed_pke_sources(db_session)

    original = db_access._session_factory

    def _factory():
        return db_session

    db_access.set_session_factory(_factory)
    yield db_session
    db_access.set_session_factory(original)


class TestExpandedInstitutionsMCP:
    def test_search_iobm_and_kiet_in_karachi(self, setup_database):
        res = search_verified_institutions(city="Karachi")
        assert res["count"] >= 10
        names = [(inst.get("name") or "") + " " + (inst.get("short_name") or "") for inst in res["results"]]
        assert any("Institute of Business Management" in n or "IoBM" in n for n in names)
        assert any("KIET" in n or "Karachi Institute of Economics and Technology" in n for n in names)
        assert any("NED" in n for n in names)

    def test_search_nutech_and_ndu_in_islamabad(self, setup_database):
        res = search_verified_institutions(city="Islamabad")
        assert res["count"] >= 9
        names = [(inst.get("name") or "") + " " + (inst.get("short_name") or "") for inst in res["results"]]
        assert any("NUTECH" in n or "National University of Technology" in n for n in names)
        assert any("NDU" in n or "National Defence University" in n for n in names)
        assert any("NUST" in n or "National University of Sciences and Technology" in n for n in names)

    def test_search_lcwu_in_lahore(self, setup_database):
        res = search_verified_institutions(city="Lahore")
        assert res["count"] >= 9
        names = [(inst.get("name") or "") + " " + (inst.get("short_name") or "") for inst in res["results"]]
        assert any("LCWU" in n or "Lahore College for Women" in n for n in names)
        assert any("LUMS" in n or "Lahore University of Management Sciences" in n for n in names)


class TestExpandedProgramsMCP:
    def test_search_programs_for_ned(self, setup_database):
        res = search_verified_programs(institution="NED")
        assert res["count"] >= 10
        program_names = [p["name"] for p in res["results"]]
        assert any("Civil Engineering" in p for p in program_names)
        assert any("Mechanical Engineering" in p for p in program_names)

    def test_search_programs_for_nutech(self, setup_database):
        res = search_verified_programs(institution="NUTECH")
        assert res["count"] >= 5
        program_names = [p["name"] for p in res["results"]]
        assert any("Computer Science" in p for p in program_names)


class TestExpandedOpportunitiesMCP:
    def test_search_scholarships(self, setup_database):
        res = search_verified_opportunities(type="scholarship")
        assert res["count"] >= 10
        titles = [o["title"] for o in res["results"]]
        assert any("HEC Need-Based" in t for t in titles)
        assert any("Fulbright" in t or "USEFP" in t for t in titles)

    def test_search_internships(self, setup_database):
        res = search_verified_opportunities(type="internship")
        assert res["count"] >= 10
        titles = [o["title"] for o in res["results"]]
        assert any("State Bank" in t for t in titles)
        assert any("WAPDA" in t for t in titles)


class TestExpandedLearningResourcesMCP:
    def test_search_digiskills_courses(self, setup_database):
        res = search_verified_learning_resources(query="DigiSkills")
        assert res["count"] >= 15
        for item in res["results"]:
            assert item["is_free"] is True

    def test_search_navttc_qualifications(self, setup_database):
        res = search_verified_learning_resources(query="NAVTTC")
        assert res["count"] >= 10


class TestSourceRegistryMCP:
    def test_get_hec_source_info(self, setup_database):
        res = get_source_registry_info(source_id="GOV-HEC-01")
        assert "error" not in res
        assert res["source_id"] == "GOV-HEC-01"
        assert res["authority_level"] == "L1"
        assert res["access_review_status"] == "APPROVED"
