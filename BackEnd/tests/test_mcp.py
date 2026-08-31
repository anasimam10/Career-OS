"""
Phase 5 tests — MCP integration.

ALL Qwen calls are mocked (the Pattern B ai_service is exercised with a mock
OpenAI client) — these tests never consume API quota and need no internet.

Coverage (Phase 5 spec):
- §14  all 5 career-server tools and all 6 opportunity-server tools,
       including missing data, invalid input, no results, inactive-record
       exclusion, and DB-backed output with no fabricated fields
- §15  SSE mounting of /mcp/career/sse and /mcp/opportunity/sse on the real
       FastAPI app (threaded uvicorn + the MCP SDK's own SSE client)
- §16  failure + retry success, failure + deterministic DB fallback,
       no-database-result
- §17  Pattern B plumbing: tool selection, tool results returned to Qwen,
       malformed tool arguments, tool-round exhaustion, and the full chain
       over REAL SSE transport with only Qwen mocked
"""

from __future__ import annotations

import json
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
import pytest
import uvicorn

from database import SessionLocal
from models.alumni import Alumni
from models.career import Career
from models.learning import LearningResource
from models.opportunity import Opportunity, SportsOpportunity
from models.university import University
from services.ai_service import (
    AIService,
    AIUnavailableError,
    AIValidationError,
)
from tests.conftest import TestingSessionLocal
from main import app

# The Mcp package lives at the repository root (conftest imports main first,
# which adds it to sys.path; this keeps the module self-sufficient).
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from Mcp import career_server as career_tools  # noqa: E402
from Mcp import db_access  # noqa: E402
from Mcp import opportunity_server as opportunity_tools  # noqa: E402
from services import mcp_client, mcp_search_service  # noqa: E402


# ---------------------------------------------------------------------------
# Mock helpers (Pattern B — same spirit as the Phase 3 mock_ai_client)
# ---------------------------------------------------------------------------


def text_response(content: str):
    """A chat completion response with plain text content (final answer)."""
    message = SimpleNamespace(content=content, tool_calls=None)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def tool_call_response(name: str, arguments: str, call_id: str = "call_1"):
    """A chat completion response where Qwen requests one tool call."""
    function = SimpleNamespace(name=name, arguments=arguments)
    tool_call = SimpleNamespace(id=call_id, type="function", function=function)
    message = SimpleNamespace(content=None, tool_calls=[tool_call])
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def mock_ai_client(sequence):
    """Mock OpenAI client: sequence items are responses (or exceptions)."""
    client = MagicMock()
    client.chat.completions.create.side_effect = list(sequence)
    return client


OPPORTUNITY_TOOL_DEFS = [
    {
        "type": "function",
        "function": {
            "name": "search_internships",
            "description": "Search active internship records.",
            "parameters": {"type": "object", "properties": {}},
        },
    }
]


# ---------------------------------------------------------------------------
# Seed data (mirrors data/seed/*.json shapes; template test data)
# ---------------------------------------------------------------------------


def _add(db, obj):
    db.add(obj)
    db.commit()


@pytest.fixture
def mcp_db(db_session):
    """
    A seeded test database with the MCP tool session factory pointed at the
    in-memory test database (restored afterwards).
    """
    _add(
        db_session,
        Career(
            slug="software-engineering",
            name="Software Engineering",
            field="Technology",
            demand_level="HIGH",
            competition_level="HIGH",
            difficulty_level="MEDIUM",
            required_skills=json.dumps(["Python", "Data Structures", "Git"]),
            pk_opportunities=json.dumps(["Growing software house demand"]),
            top_pk_universities=json.dumps(["FAST-NUCES", "LUMS"]),
            risks=json.dumps(["Highly competitive admissions"]),
        ),
    )
    _add(
        db_session,
        Career(
            slug="marketing",
            name="Marketing & Digital Media",
            field="Business",
            demand_level="MEDIUM",
            required_skills=json.dumps([]),
        ),
    )

    # --- opportunities -----------------------------------------------------
    _add(
        db_session,
        Opportunity(
            type="internship",
            title="Python Developer Intern",
            organization="TechBridge Solutions (template)",
            location="Karachi",
            deadline=None,
            required_skills=json.dumps(["Python", "Git"]),
            description="Summer internship for beginner Python developers.",
            source_url="https://example.com/internships/techbridge-python",
            last_verified=None,
            verification_status="VALIDATED",
            is_active=True,
        ),
    )
    _add(
        db_session,
        Opportunity(
            type="internship",
            title="Software Engineering Intern",
            organization="KarachiSoft Labs (template)",
            location="Karachi",
            required_skills=json.dumps(["Python", "Data Structures", "Git"]),
            description="Six-week engineering internship.",
            source_url="https://example.com/internships/karachisoft-swe",
            verification_status="VALIDATED",
            is_active=True,
        ),
    )
    _add(
        db_session,
        Opportunity(
            type="internship",
            title="Expired Internship (Inactive Example)",
            organization="Old Campaigns Co. (template)",
            location="Karachi",
            required_skills=json.dumps(["Communication"]),
            description="Inactive record that must never appear.",
            source_url="https://example.com/internships/old",
            verification_status="VALIDATED",
            is_active=False,
        ),
    )
    _add(
        db_session,
        Opportunity(
            type="job",
            title="Junior Software Developer",
            organization="PakDev Studio (template)",
            location="Karachi",
            required_skills=json.dumps(["Python", "Django", "Git"]),
            description="Entry-level developer role.",
            source_url="https://example.com/jobs/pakdev-junior-dev",
            verification_status="VALIDATED",
            is_active=True,
        ),
    )
    _add(
        db_session,
        Opportunity(
            type="scholarship",
            title="Merit Scholarship for Computer Science",
            organization="EduFuture Foundation (template)",
            location="Nationwide",
            required_skills=json.dumps([]),
            description="Tuition support scholarship for high-scoring CS students.",
            source_url="https://example.com/scholarships/edufuture-cs",
            verification_status="VALIDATED",
            is_active=True,
        ),
    )
    _add(
        db_session,
        Opportunity(
            type="education",
            title="BS Computer Science Programme",
            organization="University of Karachi (template)",
            location="Karachi",
            required_skills=json.dumps([]),
            description="Four-year bachelor's degree programme.",
            source_url="https://example.com/universities/ku-bcs",
            verification_status="VALIDATED",
            is_active=True,
        ),
    )

    # --- sports opportunities ---------------------------------------------
    _add(
        db_session,
        SportsOpportunity(
            sport="Badminton",
            type="trial",
            title="Karachi Open Badminton Trials",
            organization="Karachi Badminton Association (template)",
            location="Karachi",
            eligibility=json.dumps({"age_min": 14, "level": "intermediate"}),
            description="Open trials for the Karachi district youth squad.",
            source_url="https://example.com/sports/karachi-badminton-trials",
            verification_status="VALIDATED",
            is_active=True,
        ),
    )
    _add(
        db_session,
        SportsOpportunity(
            sport="Badminton",
            type="scholarship",
            title="National Badminton Talent Scholarship",
            organization="Pakistan Badminton Federation (template)",
            location="Nationwide",
            eligibility=json.dumps({"age_min": 14, "level": "advanced"}),
            description="Training support for nationally ranked juniors.",
            source_url="https://example.com/sports/pbf-talent-scholarship",
            verification_status="VALIDATED",
            is_active=True,
        ),
    )
    _add(
        db_session,
        SportsOpportunity(
            sport="Cricket",
            type="programme",
            title="University Cricket Development Programme",
            organization="University Sports Directorate (template)",
            location="Lahore",
            eligibility=json.dumps({"enrollment": "university_student"}),
            description="Year-round cricket development programme.",
            source_url="https://example.com/sports/university-cricket-programme",
            verification_status="VALIDATED",
            is_active=True,
        ),
    )
    _add(
        db_session,
        SportsOpportunity(
            sport="Badminton",
            type="tournament",
            title="Islamabad Badminton League (Inactive Example)",
            organization="Old Sports Club (template)",
            location="Islamabad",
            eligibility=json.dumps({"level": "advanced"}),
            description="Inactive record that must never appear.",
            source_url="https://example.com/sports/islamabad-league",
            verification_status="VALIDATED",
            is_active=False,
        ),
    )

    # --- universities + alumni + learning (Phase 4 MCP tools) -------------
    _add(
        db_session,
        University(
            name="Lahore University of Management Sciences",
            slug="lums-mcp-test",
            city="Lahore",
            type="PRIVATE",
            verification_status="VERIFIED",
        ),
    )
    _add(
        db_session,
        University(
            name="National University of Sciences and Technology",
            slug="nust-mcp-test",
            city="Islamabad",
            type="PUBLIC",
            verification_status="VALIDATED",
        ),
    )
    _add(
        db_session,
        Alumni(
            name="Ayesha Khan",
            university="LUMS",
            field="Software Engineering",
            role="Software Engineer",
            company="Systems Limited (template)",
            career_path="Python electives, internship, junior engineer.",
            advice="Build projects every semester.",
            tags=json.dumps(["Python"]),
            is_verified=True,
            university_id=1,
            career_id=1,
            source_url="https://example.com/alumni/ayesha",
        ),
    )
    _add(
        db_session,
        Alumni(
            name="Bilal Ahmed",
            university="NUST",
            field="Data Science",
            role="Data Analyst",
            company="Analytics PK (template)",
            is_verified=True,
            university_id=2,
        ),
    )
    _add(
        db_session,
        Alumni(
            name="Sara Malik",
            university="LUMS",
            field="Software Engineering",
            role="Frontend Developer",
            is_verified=False,
            university_id=1,
        ),
    )
    _add(
        db_session,
        LearningResource(
            skill_name="Python",
            title="Python for Everybody",
            type="course",
            url="https://example.com/py4e",
            level="beginner",
            is_free=True,
            verification_status="VALIDATED",
        ),
    )
    _add(
        db_session,
        LearningResource(
            skill_name="Python",
            title="Intermediate Python Projects",
            type="project",
            url="https://example.com/pyprojects",
            level="intermediate",
            is_free=True,
            verification_status="VALIDATED",
        ),
    )
    _add(
        db_session,
        LearningResource(
            skill_name="Python",
            title="Inactive Python Course",
            type="course",
            url="https://example.com/inactive",
            verification_status="VALIDATED",
            is_active=False,
        ),
    )
    _add(
        db_session,
        LearningResource(
            skill_name="Python",
            title="Candidate Python Course",
            type="course",
            url="https://example.com/candidate",
            verification_status="CANDIDATE",
        ),
    )

    db_access.set_session_factory(TestingSessionLocal)
    yield db_session
    db_access.set_session_factory(SessionLocal)


# ---------------------------------------------------------------------------
# SSE fixture — the real FastAPI app on a threaded uvicorn server
# ---------------------------------------------------------------------------


@pytest.fixture
def mcp_server(mcp_db, monkeypatch):
    """Start main:app on an ephemeral port; yield the base URL."""
    config = uvicorn.Config(app, host="127.0.0.1", port=0, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(200):
        if server.started and server.servers:
            break
        time.sleep(0.05)
    port = server.servers[0].sockets[0].getsockname()[1]
    base_url = f"http://127.0.0.1:{port}"
    # Point the Pattern B client at this ephemeral server.
    monkeypatch.setattr(
        mcp_client.settings, "MCP_SERVER_BASE_URL", base_url, raising=False
    )
    yield base_url
    server.should_exit = True
    thread.join(timeout=10)


async def _sse_list_tools(url: str):
    from mcp.client.session import ClientSession
    from mcp.client.sse import sse_client

    async with sse_client(url) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            return [tool.name for tool in result.tools]


async def _sse_call_tool(url: str, name: str, arguments: dict):
    from mcp.client.session import ClientSession
    from mcp.client.sse import sse_client

    async with sse_client(url) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(name, arguments)
            return json.loads(result.content[0].text)


def _run(coro, timeout: float = 30.0):
    import asyncio

    return asyncio.run(asyncio.wait_for(coro, timeout=timeout))


# ===========================================================================
# §14 Career server tools (direct function calls — same functions the MCP
#      server exposes; the SSE layer is tested separately below)
# ===========================================================================


class TestCareerServerTools:
    def test_get_career_valid(self, mcp_db):
        result = career_tools.get_career("software-engineering")
        assert result["found"] is True
        career = result["career"]
        assert career["name"] == "Software Engineering"
        assert career["demand_level"] == "HIGH"
        assert career["required_skills"] == ["Python", "Data Structures", "Git"]
        assert career["top_pk_universities"] == ["FAST-NUCES", "LUMS"]

    def test_get_career_unknown_slug(self, mcp_db):
        result = career_tools.get_career("does-not-exist")
        assert result["found"] is False
        assert "not found" in result["message"]
        assert "software-engineering" in result["available_careers"]
        assert "marketing" in result["available_careers"]

    def test_get_career_invalid_input(self, mcp_db):
        result = career_tools.get_career("   ")
        assert result["error"] == "invalid_input"

    def test_get_career_reality_full(self, mcp_db):
        result = career_tools.get_career_reality("software-engineering")
        assert result["found"] is True
        assert result["demand_level"] == "HIGH"
        assert result["competition_level"] == "HIGH"
        assert result["difficulty_level"] == "MEDIUM"
        assert result["required_skills"] == ["Python", "Data Structures", "Git"]
        assert result["pk_opportunities"] == ["Growing software house demand"]
        assert result["risks"] == ["Highly competitive admissions"]
        assert "template seed data" in result["data_source"]

    def test_get_career_reality_sparse_career_reports_unknown(self, mcp_db):
        result = career_tools.get_career_reality("marketing")
        assert result["competition_level"] == "UNKNOWN"
        assert result["difficulty_level"] == "UNKNOWN"

    def test_get_required_skills_with_stage(self, mcp_db):
        result = career_tools.get_required_skills(
            "software-engineering", "HIGH_SCHOOL"
        )
        assert result["required_skills"] == ["Python", "Data Structures", "Git"]
        assert result["focus_skills"] == ["Python", "Data Structures"]
        assert "stage" in result["focus_note"].lower()

    def test_get_required_skills_without_stage(self, mcp_db):
        result = career_tools.get_required_skills("software-engineering")
        assert result["focus_skills"] == result["required_skills"]
        assert result["stage"] is None

    def test_get_required_skills_unknown_career(self, mcp_db):
        result = career_tools.get_required_skills("nope")
        assert result["found"] is False

    def test_get_university_opportunities_returns_db_records(self, mcp_db):
        result = career_tools.get_university_opportunities(
            "Technology", "Karachi"
        )
        programmes = result["university_programmes"]
        assert len(programmes) == 1
        assert programmes[0]["title"] == "BS Computer Science Programme"
        assert programmes[0]["organization"] == "University of Karachi (template)"
        # career-linked universities come from the careers table
        fields = result["universities_for_field"]
        assert any(u["career"] == "Software Engineering" for u in fields)

    def test_get_university_opportunities_no_results(self, mcp_db):
        result = career_tools.get_university_opportunities(
            "Agriculture", "Quetta"
        )
        assert result["count"] == 0
        assert result["university_programmes"] == []
        assert "No matching" in result["message"]

    def test_get_scholarships_matches_criteria(self, mcp_db):
        result = career_tools.get_scholarships("computer science")
        assert result["count"] == 1
        assert (
            result["scholarships"][0]["title"]
            == "Merit Scholarship for Computer Science"
        )

    def test_get_scholarships_all_when_no_criteria(self, mcp_db):
        result = career_tools.get_scholarships("")
        assert result["count"] == 1

    def test_get_scholarships_no_results(self, mcp_db):
        result = career_tools.get_scholarships("marine biology")
        assert result["count"] == 0
        assert "No matching" in result["message"]


# ===========================================================================
# §14 Opportunity / sports server tools
# ===========================================================================

EXPECTED_OPPORTUNITY_KEYS = {
    "id",
    "type",
    "title",
    "organization",
    "location",
    "deadline",
    "required_skills",
    "description",
    "source_url",
    "last_verified",
    "is_active",
}


class TestOpportunityServerTools:
    def test_search_internships_matching(self, mcp_db):
        result = opportunity_tools.search_internships(
            skills=["Python"], city="Karachi"
        )
        titles = [r["title"] for r in result["results"]]
        assert "Python Developer Intern" in titles
        assert "Software Engineering Intern" in titles
        assert result["count"] == 2

    def test_search_internships_excludes_inactive(self, mcp_db):
        result = opportunity_tools.search_internships(
            skills=["Communication"], city="Karachi"
        )
        titles = [r["title"] for r in result["results"]]
        assert "Expired Internship (Inactive Example)" not in titles

    def test_search_internships_no_results(self, mcp_db):
        result = opportunity_tools.search_internships(
            skills=["Python"], city="Peshawar"
        )
        assert result["count"] == 0
        assert result["results"] == []
        assert "No matching" in result["message"]

    def test_search_internships_invalid_input(self, mcp_db):
        result = opportunity_tools.search_internships(skills=["Python"], city=" ")
        assert result["error"] == "invalid_input"

    def test_search_internships_no_fabricated_fields(self, mcp_db):
        result = opportunity_tools.search_internships(
            skills=["Python"], city="Karachi"
        )
        for record in result["results"]:
            assert set(record.keys()) == EXPECTED_OPPORTUNITY_KEYS
            assert record["organization"].endswith("(template)")
            assert record["source_url"].startswith("https://example.com/")

    def test_search_jobs_matching(self, mcp_db):
        result = opportunity_tools.search_jobs(
            skills=["Python"], city="Karachi", experience_level="entry-level"
        )
        assert result["count"] == 1
        assert result["results"][0]["title"] == "Junior Software Developer"

    def test_search_jobs_no_results(self, mcp_db):
        result = opportunity_tools.search_jobs(skills=["Rust"], city="Karachi")
        assert result["count"] == 0

    def test_match_opportunity_full_match(self, mcp_db):
        internship = (
            mcp_db.query(Opportunity)
            .filter(Opportunity.title == "Python Developer Intern")
            .one()
        )
        result = opportunity_tools.match_opportunity(
            {"skills": ["Python", "Git"]}, internship.id
        )
        assert result["match_score"] == 1.0
        assert result["missing_requirements"] == []
        assert "application" in result["next_action"].lower()
        assert any("already has" in r for r in result["matching_reasons"])

    def test_match_opportunity_partial_match(self, mcp_db):
        internship = (
            mcp_db.query(Opportunity)
            .filter(Opportunity.title == "Python Developer Intern")
            .one()
        )
        result = opportunity_tools.match_opportunity(
            {"skills": ["Python"]}, internship.id
        )
        assert result["match_score"] == 0.5
        assert result["missing_requirements"] == ["Git"]

    def test_match_opportunity_invalid_id(self, mcp_db):
        result = opportunity_tools.match_opportunity({"skills": ["Python"]}, 9999)
        assert result["error"] == "not_found"

    def test_match_opportunity_invalid_input(self, mcp_db):
        result = opportunity_tools.match_opportunity({}, 1)
        assert result["error"] == "invalid_input"

    def test_search_sports_opportunities(self, mcp_db):
        result = opportunity_tools.search_sports_opportunities(
            "Badminton", "Karachi"
        )
        titles = [r["title"] for r in result["results"]]
        assert "Karachi Open Badminton Trials" in titles
        # nationwide records are available in every city
        assert "National Badminton Talent Scholarship" in titles
        assert result["count"] == 2

    def test_search_sports_opportunities_excludes_inactive(self, mcp_db):
        result = opportunity_tools.search_sports_opportunities("Badminton", "")
        titles = [r["title"] for r in result["results"]]
        assert "Islamabad Badminton League (Inactive Example)" not in titles

    def test_search_sports_scholarships(self, mcp_db):
        result = opportunity_tools.search_sports_scholarships("Badminton")
        assert result["count"] == 1
        assert (
            result["results"][0]["title"]
            == "National Badminton Talent Scholarship"
        )

    def test_search_sports_scholarships_level_filter(self, mcp_db):
        result = opportunity_tools.search_sports_scholarships(
            "Badminton", level="beginner"
        )
        assert result["count"] == 0
        result = opportunity_tools.search_sports_scholarships(
            "Badminton", level="advanced"
        )
        assert result["count"] == 1

    def test_search_university_sports(self, mcp_db):
        result = opportunity_tools.search_university_sports("Cricket", "Lahore")
        assert result["count"] == 1
        assert (
            result["results"][0]["title"]
            == "University Cricket Development Programme"
        )

    def test_search_university_sports_no_results(self, mcp_db):
        result = opportunity_tools.search_university_sports("Badminton", "Lahore")
        assert result["count"] == 0


# ===========================================================================
# §16 Alumni + Learning tools (Phase 4 — direct function calls, the same
#      functions the MCP server exposes; the SSE layer is covered below)
# ===========================================================================


class TestAlumniAndLearningTools:
    def test_find_alumni_by_field_verified_first(self, mcp_db):
        result = opportunity_tools.find_alumni("Software Engineering")
        assert result["count"] == 2
        names = [r["name"] for r in result["results"]]
        # Verified journeys before community-submitted ones (master §24).
        assert names == ["Ayesha Khan", "Sara Malik"]

    def test_find_alumni_record_shape(self, mcp_db):
        result = opportunity_tools.find_alumni("Software Engineering")
        first = result["results"][0]
        assert first["role"] == "Software Engineer"
        assert first["tags"] == ["Python"]
        assert first["is_verified"] is True
        assert first["source_url"].startswith("https://example.com/")

    def test_find_alumni_university_filter(self, mcp_db):
        result = opportunity_tools.find_alumni("Science", university_id=2)
        assert result["count"] == 1
        assert result["results"][0]["name"] == "Bilal Ahmed"

    def test_find_alumni_career_filter(self, mcp_db):
        result = opportunity_tools.find_alumni("Engineering", career_id=1)
        assert result["count"] == 1
        assert result["results"][0]["name"] == "Ayesha Khan"

    def test_find_alumni_no_results(self, mcp_db):
        result = opportunity_tools.find_alumni("Astronomy")
        assert result["count"] == 0
        assert result["results"] == []
        assert "No matching" in result["message"]

    def test_find_alumni_invalid_input(self, mcp_db):
        result = opportunity_tools.find_alumni("   ")
        assert result["error"] == "invalid_input"
        result = opportunity_tools.find_alumni("Engineering", career_id=0)
        assert result["error"] == "invalid_input"

    def test_get_learning_resources_by_skill(self, mcp_db):
        result = opportunity_tools.get_learning_resources("Python")
        titles = [r["title"] for r in result["results"]]
        # Active + validated only, alphabetical by title.
        assert titles == ["Intermediate Python Projects", "Python for Everybody"]

    def test_get_learning_resources_level_filter(self, mcp_db):
        result = opportunity_tools.get_learning_resources("Python", level="beginner")
        assert result["count"] == 1
        assert result["results"][0]["title"] == "Python for Everybody"

    def test_get_learning_resources_excludes_inactive_and_candidate(self, mcp_db):
        result = opportunity_tools.get_learning_resources("Python")
        titles = [r["title"] for r in result["results"]]
        assert "Inactive Python Course" not in titles
        assert "Candidate Python Course" not in titles

    def test_get_learning_resources_no_results(self, mcp_db):
        result = opportunity_tools.get_learning_resources("Fortran")
        assert result["count"] == 0
        assert result["results"] == []
        assert "No matching" in result["message"]

    def test_get_learning_resources_invalid_input(self, mcp_db):
        result = opportunity_tools.get_learning_resources("")
        assert result["error"] == "invalid_input"


# ===========================================================================
# §15 SSE mounting tests (real FastAPI app, threaded uvicorn, SDK SSE client)
# ===========================================================================


class TestSSEMounting:
    def test_health_still_works_with_mcp_mounted(self, mcp_server):
        response = httpx.get(f"{mcp_server}/api/v1/health", timeout=10)
        assert response.status_code == 200

    def test_career_sse_lists_five_tools(self, mcp_server):
        tools = _run(_sse_list_tools(f"{mcp_server}/mcp/career/sse"))
        assert sorted(tools) == [
            "get_career",
            "get_career_reality",
            "get_required_skills",
            "get_scholarships",
            "get_university_opportunities",
        ]

    def test_opportunity_sse_lists_eight_tools(self, mcp_server):
        tools = _run(_sse_list_tools(f"{mcp_server}/mcp/opportunity/sse"))
        assert sorted(tools) == [
            "find_alumni",
            "get_learning_resources",
            "match_opportunity",
            "search_internships",
            "search_jobs",
            "search_sports_opportunities",
            "search_sports_scholarships",
            "search_university_sports",
        ]

    def test_career_sse_tool_call_round_trip(self, mcp_server):
        result = _run(
            _sse_call_tool(
                f"{mcp_server}/mcp/career/sse",
                "get_career",
                {"slug": "software-engineering"},
            )
        )
        assert result["found"] is True
        assert result["career"]["name"] == "Software Engineering"

    def test_opportunity_sse_tool_call_round_trip(self, mcp_server):
        result = _run(
            _sse_call_tool(
                f"{mcp_server}/mcp/opportunity/sse",
                "search_internships",
                {"skills": ["Python"], "city": "Karachi"},
            )
        )
        assert result["count"] == 2
        titles = [r["title"] for r in result["results"]]
        assert "Python Developer Intern" in titles

    def test_alumni_sse_tool_call_round_trip(self, mcp_server):
        result = _run(
            _sse_call_tool(
                f"{mcp_server}/mcp/opportunity/sse",
                "find_alumni",
                {"field": "Software Engineering"},
            )
        )
        assert result["count"] == 2
        assert result["results"][0]["name"] == "Ayesha Khan"


# ===========================================================================
# §17 Pattern B plumbing (Qwen mocked; tool executor direct or mocked)
# ===========================================================================


class TestCallWithMCP:
    def test_tool_selected_executed_and_result_returned_to_qwen(self):
        executor_calls = []

        def executor(name, arguments):
            executor_calls.append((name, arguments))
            return {
                "count": 1,
                "results": [
                    {
                        "title": "Python Developer Intern",
                        "organization": "TechBridge Solutions (template)",
                    }
                ],
            }

        client = mock_ai_client(
            [
                tool_call_response(
                    "search_internships",
                    '{"city": "Karachi", "skills": ["Python"]}',
                ),
                text_response("I found 1 internship for you."),
            ]
        )
        service = AIService(client=client)
        result = service.call_with_mcp(
            "Find Pakistani internships for a student with Python skills in Karachi.",
            tools=OPPORTUNITY_TOOL_DEFS,
            tool_executor=executor,
        )

        assert result.answer == "I found 1 internship for you."
        # the correct tool was selected with the parsed arguments
        assert executor_calls == [
            ("search_internships", {"city": "Karachi", "skills": ["Python"]})
        ]
        # the evidence trail records the tool call and its DB result
        assert result.tool_calls[0]["tool"] == "search_internships"
        assert result.tool_calls[0]["result"]["count"] == 1
        # the tool result was sent back to Qwen as a tool message
        create_calls = client.chat.completions.create.call_args_list
        assert len(create_calls) == 2
        second_messages = create_calls[1].kwargs["messages"]
        tool_messages = [m for m in second_messages if m.get("role") == "tool"]
        assert len(tool_messages) == 1
        assert "Python Developer Intern" in tool_messages[0]["content"]

    def test_direct_answer_without_tools(self):
        client = mock_ai_client([text_response("No tools needed here.")])
        result = AIService(client=client).call_with_mcp(
            "Say hi.", tools=OPPORTUNITY_TOOL_DEFS, tool_executor=lambda n, a: {}
        )
        assert result.answer == "No tools needed here."
        assert result.tool_calls == []

    def test_malformed_tool_arguments_handled_safely(self):
        def executor(name, arguments):
            return {"count": 0, "results": []}

        client = mock_ai_client(
            [
                tool_call_response("search_internships", "{not valid json"),
                text_response("Nothing found."),
            ]
        )
        result = AIService(client=client).call_with_mcp(
            "Find internships.",
            tools=OPPORTUNITY_TOOL_DEFS,
            tool_executor=executor,
        )
        assert result.answer == "Nothing found."
        assert result.tool_calls[0]["arguments"] == {}

    def test_tool_round_exhaustion_raises(self):
        client = mock_ai_client(
            [
                tool_call_response("search_internships", "{}"),
                tool_call_response("search_internships", "{}"),
            ]
        )
        with pytest.raises(AIValidationError):
            AIService(client=client).call_with_mcp(
                "Find internships.",
                tools=OPPORTUNITY_TOOL_DEFS,
                tool_executor=lambda n, a: {"count": 0},
                max_tool_rounds=1,
            )

    def test_tool_executor_errors_propagate(self):
        from services.mcp_client import MCPClientError

        def executor(name, arguments):
            raise MCPClientError("tool failed")

        client = mock_ai_client(
            [tool_call_response("search_internships", "{}")]
        )
        with pytest.raises(MCPClientError):
            AIService(client=client).call_with_mcp(
                "Find internships.",
                tools=OPPORTUNITY_TOOL_DEFS,
                tool_executor=executor,
            )


class TestMCPClientHelpers:
    def test_server_url_known_servers(self):
        assert mcp_client.server_url("career").endswith("/mcp/career/sse")
        assert mcp_client.server_url("opportunity").endswith(
            "/mcp/opportunity/sse"
        )

    def test_server_url_unknown_server(self):
        from services.mcp_client import MCPClientError

        with pytest.raises(MCPClientError):
            mcp_client.server_url("not-a-server")


# ===========================================================================
# §16 / §17 MCP failure policy + full chain over REAL SSE (Qwen mocked)
# ===========================================================================


class TestSearchWithMCP:
    def _mock_ai(self, monkeypatch, sequence):
        service = AIService(client=mock_ai_client(sequence))
        monkeypatch.setattr(
            mcp_search_service, "get_ai_service", lambda: service
        )

    def test_success_path_over_real_sse(self, mcp_server, monkeypatch):
        """Full Pattern B chain: real SSE transport, only Qwen mocked."""
        self._mock_ai(
            monkeypatch,
            [
                tool_call_response(
                    "search_internships",
                    '{"city": "Karachi", "skills": ["Python"]}',
                ),
                text_response(
                    "I found 2 Python internships in Karachi in our database."
                ),
            ],
        )
        result = mcp_search_service.search_with_mcp(
            "Find Pakistani internships for a student with Python skills in Karachi.",
            "opportunity",
            fallback_tool="search_internships",
            fallback_arguments={"city": "Karachi", "skills": ["Python"]},
            operation="live_sse_test",
        )
        assert result["data_quality"] == "ai_interpreted"
        assert result["answer"].startswith("I found 2 Python internships")
        assert result["tool_calls"][0]["tool"] == "search_internships"
        assert result["tool_calls"][0]["result"]["count"] == 2

    def test_retry_once_then_success(self, mcp_db, monkeypatch):
        """First MCP attempt fails, retry succeeds — exactly 2 attempts."""
        attempts = []

        def flaky_list_tools(server):
            attempts.append(server)
            if len(attempts) == 1:
                raise mcp_client.MCPClientError("connection refused")
            return OPPORTUNITY_TOOL_DEFS

        monkeypatch.setattr(mcp_client, "list_tools", flaky_list_tools)
        self._mock_ai(
            monkeypatch,
            [text_response("Here is the answer from the tools.")],
        )

        result = mcp_search_service.search_with_mcp(
            "Find internships in Karachi.",
            "opportunity",
            fallback_tool="search_internships",
            fallback_arguments={"city": "Karachi"},
        )
        assert result["data_quality"] == "ai_interpreted"
        assert len(attempts) == 2  # one failure + one retry, no more

    def test_both_attempts_fail_falls_back_to_direct_db(self, mcp_db, monkeypatch):
        """Both MCP attempts fail -> unranked direct DB results, no fabrication."""
        def broken_list_tools(server):
            raise mcp_client.MCPClientError("connection refused")

        monkeypatch.setattr(mcp_client, "list_tools", broken_list_tools)

        result = mcp_search_service.search_with_mcp(
            "Find Pakistani internships for a student with Python skills in Karachi.",
            "opportunity",
            fallback_tool="search_internships",
            fallback_arguments={"skills": ["Python"], "city": "Karachi"},
        )
        assert result["data_quality"] == "unranked"
        assert (
            result["note"]
            == "Live ranking is temporarily unavailable."
        )
        titles = [r["title"] for r in result["results"]["results"]]
        assert "Python Developer Intern" in titles
        assert "Software Engineering Intern" in titles
        assert "Expired Internship (Inactive Example)" not in titles

    def test_fallback_when_ai_unavailable(self, mcp_db, monkeypatch):
        """MCP transport works but Qwen is down -> direct DB fallback."""
        monkeypatch.setattr(
            mcp_client, "list_tools", lambda server: OPPORTUNITY_TOOL_DEFS
        )

        class BrokenAI:
            def call_with_mcp(self, *args, **kwargs):
                raise AIUnavailableError("provider down")

        monkeypatch.setattr(
            mcp_search_service, "get_ai_service", lambda: BrokenAI()
        )

        result = mcp_search_service.search_with_mcp(
            "Find internships in Karachi.",
            "opportunity",
            fallback_tool="search_internships",
            fallback_arguments={"skills": ["Python"], "city": "Karachi"},
        )
        assert result["data_quality"] == "unranked"
        assert result["results"]["count"] == 2

    def test_malformed_tool_result_triggers_fallback(self, mcp_db, monkeypatch):
        """A tool result that cannot be delivered safely -> retry -> fallback."""
        monkeypatch.setattr(
            mcp_client, "list_tools", lambda server: OPPORTUNITY_TOOL_DEFS
        )

        def malformed_call_tool(server, name, arguments):
            raise mcp_client.MCPClientError("malformed JSON")

        monkeypatch.setattr(mcp_client, "call_tool", malformed_call_tool)
        self._mock_ai(
            monkeypatch,
            [
                tool_call_response("search_internships", "{}"),
                tool_call_response("search_internships", "{}"),
            ],
        )

        result = mcp_search_service.search_with_mcp(
            "Find internships in Karachi.",
            "opportunity",
            fallback_tool="search_internships",
            fallback_arguments={"skills": ["Python"], "city": "Karachi"},
        )
        assert result["data_quality"] == "unranked"

    def test_no_fallback_configured_raises(self, mcp_db, monkeypatch):
        def broken_list_tools(server):
            raise mcp_client.MCPClientError("connection refused")

        monkeypatch.setattr(mcp_client, "list_tools", broken_list_tools)
        with pytest.raises(AIUnavailableError):
            mcp_search_service.search_with_mcp(
                "Find internships in Karachi.", "opportunity"
            )

    def test_unknown_server_rejected(self, mcp_db):
        with pytest.raises(ValueError):
            mcp_search_service.search_with_mcp("question", "not-a-server")

    def test_fallback_no_database_result(self, mcp_db, monkeypatch):
        """Direct DB fallback with no matching records -> explicit empty result."""
        def broken_list_tools(server):
            raise mcp_client.MCPClientError("connection refused")

        monkeypatch.setattr(mcp_client, "list_tools", broken_list_tools)
        result = mcp_search_service.search_with_mcp(
            "Find internships in Peshawar.",
            "opportunity",
            fallback_tool="search_internships",
            fallback_arguments={"skills": ["Python"], "city": "Peshawar"},
        )
        assert result["data_quality"] == "unranked"
        assert result["results"]["count"] == 0
        assert "No matching" in result["results"]["message"]
