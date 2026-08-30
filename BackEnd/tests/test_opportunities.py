"""
Phase 6 tests — Opportunities + Sports.

ALL Qwen calls are mocked. Most match tests stub search_with_mcp (the Phase 5
boundary, already covered by its own 50 tests); the full-chain tests go one
level deeper and exercise the REAL ai_service.call_with_mcp loop with a mock
OpenAI client plus a mocked MCP transport that routes straight into the real
tool functions reading the test database. No API quota, no internet.

Coverage (Phase 6 spec — architecture §8/§9/§10 + implementation-status §10):
- matching_service: deterministic opportunity scoring (skill overlap),
  sports eligibility scoring (level / enrollment; age surfaced but never
  scored), §10 data freshness (30-day rule), ranked ordering
- GET /opportunities: filters (type, city incl. Nationwide, field, skills),
  inactive exclusion, deadline ordering, §10 empty envelope, 422 invalid type
- GET /sports: filters (sport case-insensitive, city, type), inactive
  exclusion, empty envelope, 422 invalid type
- POST /opportunities/match: 404 unknown student, 422 blank city / invalid
  body, MCP-path ranked matches with deterministic scores, unranked
  direct-DB fallback (retrieval order kept), ungrounded AI answer replaced
  by the direct query, §10 no-results message, persistence into
  student_opportunity_matches (replace semantics), 503 when the chain fails
- POST /sports/match: 404 unknown student, 422 blank sport, eligibility
  evaluation against the student's education stage, ranked/unranked/empty
  paths, no persistence for sports
"""

from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from database import SessionLocal
from models.opportunity import Opportunity, SportsOpportunity, StudentOpportunityMatch
from models.student import Student, StudentProfile
from services import matching_service, opportunity_service
from services.ai_service import AIService, AIUnavailableError
from tests.conftest import TestingSessionLocal

# The Mcp package lives at the repository root (conftest imports main first,
# which adds it to sys.path; this keeps the module self-sufficient).
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from Mcp import db_access  # noqa: E402
from services import mcp_client, mcp_search_service  # noqa: E402


# ---------------------------------------------------------------------------
# Mock helpers (same spirit as tests/test_mcp.py)
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


def _mock_search(monkeypatch, result):
    """Stub the Phase 5 boundary (search_with_mcp) with a fixed result."""
    def fake(question, server, *, fallback_tool=None, fallback_arguments=None,
             operation="mcp_search"):
        return result

    monkeypatch.setattr(
        opportunity_service.mcp_search_service, "search_with_mcp", fake
    )


def mcp_success(records, answer="Here is what I found.", tool="search_internships"):
    """A successful Pattern B result: grounded tool calls + final answer."""
    return {
        "answer": answer,
        "tool_calls": [
            {
                "tool": tool,
                "arguments": {"city": "Karachi"},
                "result": {"count": len(records), "results": records},
            }
        ],
        "data_quality": "ai_interpreted",
    }


def fallback_result(records):
    """The deterministic direct-database fallback result (Phase 5 policy)."""
    return {
        "data_quality": "unranked",
        "note": "Live ranking is temporarily unavailable.",
        "results": {
            "count": len(records),
            "results": records,
            "city": "Karachi",
            "search_type": "internship",
        },
    }


# ---------------------------------------------------------------------------
# Seeded test data (mirrors data/seed/*.json shapes; template test data)
#
# Deterministic ids on a fresh per-test database:
#   opportunities: 1 Python Dev Intern (Karachi, [Python, Git], fresh)
#                  2 SWE Intern        (Karachi, [Python, DS, Git], fresh)
#                  3 Data Analytics    (Lahore, [SQL, Python], fresh)
#                  4 Inactive Intern   (Karachi, inactive — never returned)
#                  5 Legacy Marketing  (Karachi, [Communication], STALE)
#                  6 Junior Dev job    (Karachi, [Python, Django, Git], fresh)
#                  7 CS Scholarship    (Nationwide, [], fresh)
#   sports:        1 Badminton trial       (Karachi, level intermediate, fresh)
#                  2 Badminton scholarship (Nationwide, level advanced, fresh)
#                  3 Cricket tournament    (Lahore, level intermediate, STALE)
#                  4 Cricket programme     (Lahore, university_student, fresh)
#                  5 Inactive tournament   (Islamabad, inactive — never returned)
# ---------------------------------------------------------------------------


def _add(db, obj):
    db.add(obj)
    db.commit()


@pytest.fixture
def opp_db(db_session):
    """
    A seeded test database with the MCP tool session factory pointed at the
    in-memory test database (restored afterwards). The demo student (id=1)
    has a profile with one skill: Python (beginner), stage HIGH_SCHOOL.
    """
    fresh = date.today() - timedelta(days=5)
    stale = date.today() - timedelta(days=400)

    _add(
        db_session,
        Student(
            id=1,
            name="Demo Student",
            email="demo@ahcareers.test",
            password_hash="not-a-real-hash",
            education_stage="HIGH_SCHOOL",
            sports_interest="Badminton",
        ),
    )
    _add(
        db_session,
        StudentProfile(
            student_id=1,
            skills='[{"name": "Python", "level": "beginner"}]',
        ),
    )

    # --- opportunities ------------------------------------------------------
    _add(
        db_session,
        Opportunity(
            type="internship",
            title="Python Developer Intern",
            organization="TechBridge Solutions (template)",
            location="Karachi",
            deadline=date(2026, 10, 15),
            required_skills=json.dumps(["Python", "Git"]),
            description="Summer internship for beginner Python developers.",
            source_url="https://example.com/internships/techbridge-python",
            last_verified=fresh,
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
            deadline=date(2026, 9, 30),
            required_skills=json.dumps(["Python", "Data Structures", "Git"]),
            description="Six-week engineering internship.",
            source_url="https://example.com/internships/karachisoft-swe",
            last_verified=fresh,
            is_active=True,
        ),
    )
    _add(
        db_session,
        Opportunity(
            type="internship",
            title="Data Analytics Intern",
            organization="Insight Analytics PK (template)",
            location="Lahore",
            deadline=date(2026, 11, 1),
            required_skills=json.dumps(["SQL", "Python"]),
            description="Internship supporting the analytics team.",
            source_url="https://example.com/internships/insight-analytics",
            last_verified=fresh,
            is_active=True,
        ),
    )
    _add(
        db_session,
        Opportunity(
            type="internship",
            title="Expired Internship (Inactive Example)",
            organization="Old Internships Co. (template)",
            location="Karachi",
            deadline=date(2026, 1, 15),
            required_skills=json.dumps(["Communication"]),
            description="Inactive record that must never appear in results.",
            source_url="https://example.com/internships/old",
            last_verified=stale,
            is_active=False,
        ),
    )
    _add(
        db_session,
        Opportunity(
            type="internship",
            title="Legacy Marketing Intern",
            organization="Old Campaigns Co. (template)",
            location="Karachi",
            deadline=date(2026, 1, 20),
            required_skills=json.dumps(["Communication"]),
            description="Active record with a stale last_verified date.",
            source_url="https://example.com/internships/legacy-marketing",
            last_verified=stale,
            is_active=True,
        ),
    )
    _add(
        db_session,
        Opportunity(
            type="job",
            title="Junior Software Developer",
            organization="PakDev Studio (template)",
            location="Karachi",
            deadline=date(2026, 10, 1),
            required_skills=json.dumps(["Python", "Django", "Git"]),
            description="Entry-level developer role for fresh graduates.",
            source_url="https://example.com/jobs/pakdev-junior-dev",
            last_verified=fresh,
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
            deadline=date(2026, 12, 1),
            required_skills=json.dumps([]),
            description="Tuition support scholarship for high-scoring CS students.",
            source_url="https://example.com/scholarships/edufuture-cs",
            last_verified=fresh,
            is_active=True,
        ),
    )

    # --- sports opportunities ----------------------------------------------
    _add(
        db_session,
        SportsOpportunity(
            sport="Badminton",
            type="trial",
            title="Karachi Open Badminton Trials",
            organization="Karachi Badminton Association (template)",
            location="Karachi",
            deadline=date(2026, 9, 20),
            eligibility=json.dumps(
                {"age_min": 14, "age_max": 22, "level": "intermediate"}
            ),
            description="Open trials for the Karachi district youth squad.",
            source_url="https://example.com/sports/karachi-badminton-trials",
            last_verified=fresh,
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
            deadline=date(2026, 11, 30),
            eligibility=json.dumps(
                {"age_min": 14, "age_max": 20, "level": "advanced"}
            ),
            description="Training support for nationally ranked junior players.",
            source_url="https://example.com/sports/pbf-talent-scholarship",
            last_verified=fresh,
            is_active=True,
        ),
    )
    _add(
        db_session,
        SportsOpportunity(
            sport="Cricket",
            type="tournament",
            title="Lahore Under-19 Cricket Cup",
            organization="Lahore Region Cricket Board (template)",
            location="Lahore",
            deadline=date(2026, 10, 10),
            eligibility=json.dumps(
                {"age_min": 15, "age_max": 19, "level": "intermediate"}
            ),
            description="Annual district under-19 tournament.",
            source_url="https://example.com/sports/lahore-u19-cup",
            last_verified=stale,
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
            deadline=date(2026, 9, 5),
            eligibility=json.dumps(
                {"enrollment": "university_student", "level": "beginner"}
            ),
            description="Year-round cricket development programme.",
            source_url="https://example.com/sports/university-cricket-programme",
            last_verified=fresh,
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
            deadline=date(2026, 2, 1),
            eligibility=json.dumps({"level": "advanced"}),
            description="Inactive record that must never appear in results.",
            source_url="https://example.com/sports/islamabad-league",
            last_verified=stale,
            is_active=False,
        ),
    )

    db_access.set_session_factory(TestingSessionLocal)
    yield db_session
    db_access.set_session_factory(SessionLocal)


def opp_record(**overrides):
    """A serialized opportunity record (opportunity_to_dict shape), id=1."""
    record = {
        "id": 1,
        "type": "internship",
        "title": "Python Developer Intern",
        "organization": "TechBridge Solutions (template)",
        "location": "Karachi",
        "deadline": "2026-10-15",
        "required_skills": ["Python", "Git"],
        "description": "Summer internship for beginner Python developers.",
        "source_url": "https://example.com/internships/techbridge-python",
        "last_verified": (date.today() - timedelta(days=5)).isoformat(),
        "is_active": True,
    }
    record.update(overrides)
    return record


def sports_record(**overrides):
    """A serialized sports opportunity record, id=1 (Badminton trial)."""
    record = {
        "id": 1,
        "sport": "Badminton",
        "type": "trial",
        "title": "Karachi Open Badminton Trials",
        "organization": "Karachi Badminton Association (template)",
        "location": "Karachi",
        "deadline": "2026-09-20",
        "eligibility": {"age_min": 14, "age_max": 22, "level": "intermediate"},
        "description": "Open trials for the Karachi district youth squad.",
        "source_url": "https://example.com/sports/karachi-badminton-trials",
        "last_verified": (date.today() - timedelta(days=5)).isoformat(),
        "is_active": True,
    }
    record.update(overrides)
    return record


# ---------------------------------------------------------------------------
# matching_service — pure deterministic unit tests
# ---------------------------------------------------------------------------


class TestMatchingService:

    def test_score_opportunity_full_skill_match(self):
        match = matching_service.score_opportunity(
            opp_record(), ["python", "git"], city="Karachi"
        )
        assert match.match_score == 1.0
        assert match.missing_requirements == []
        assert "2 of 2 required skills" in match.match_reasons[0]
        assert "All 2 required skills" in match.next_action
        assert match.opportunity_id == 1
        assert match.deadline == date(2026, 10, 15)

    def test_score_opportunity_partial_skill_match(self):
        match = matching_service.score_opportunity(opp_record(), ["Python"])
        assert match.match_score == 0.5
        assert match.missing_requirements == ["Git"]
        assert match.next_action.startswith("Partially matched")

    def test_score_opportunity_no_required_skills(self):
        match = matching_service.score_opportunity(
            opp_record(required_skills=[]), ["Python"]
        )
        assert match.match_score == 1.0
        assert match.missing_requirements == []
        assert any("No specific required skills" in r for r in match.match_reasons)
        assert match.next_action.startswith("No specific requirements listed")

    def test_score_opportunity_no_skill_overlap(self):
        match = matching_service.score_opportunity(
            opp_record(required_skills=["Django"]), ["python"]
        )
        assert match.match_score == 0.0
        assert match.missing_requirements == ["Django"]
        assert match.next_action == "Start with the first required skill: Django."

    def test_score_opportunity_case_insensitive(self):
        match = matching_service.score_opportunity(
            opp_record(required_skills=["PYTHON", "Git"]), ["python", "GIT"]
        )
        assert match.match_score == 1.0

    def test_score_opportunity_city_reasons(self):
        local = matching_service.score_opportunity(opp_record(), [], city="Karachi")
        assert "Located in Karachi" in local.match_reasons
        nationwide = matching_service.score_opportunity(
            opp_record(location="Nationwide"), [], city="Karachi"
        )
        assert "Open nationwide" in nationwide.match_reasons

    def test_data_freshness_rule(self):
        today = date.today()
        assert matching_service.data_freshness(None) is None
        assert matching_service.data_freshness("not-a-date") is None
        assert matching_service.data_freshness(today - timedelta(days=5)) is None
        assert matching_service.data_freshness(today - timedelta(days=30)) is None
        assert matching_service.data_freshness(today - timedelta(days=31)) == "unverified"
        assert (
            matching_service.data_freshness((today - timedelta(days=40)).isoformat())
            == "unverified"
        )

    def test_score_opportunity_stale_record_flagged(self):
        stale = (date.today() - timedelta(days=40)).isoformat()
        match = matching_service.score_opportunity(opp_record(last_verified=stale), [])
        assert match.data_freshness == "unverified"

    def test_sort_opportunity_matches_ranked(self):
        from schemas.shared import OpportunityMatch

        def _match(score, deadline):
            return OpportunityMatch(
                opportunity_id=1,
                title="t",
                organization="o",
                match_score=score,
                match_reasons=[],
                missing_requirements=[],
                next_action="n",
                deadline=deadline,
                source_url="u",
            )

        matches = [
            _match(0.5, date(2026, 10, 15)),
            _match(0.5, date(2026, 9, 30)),
            _match(1.0, None),
        ]
        ranked = matching_service.sort_opportunity_matches(matches)
        assert [m.match_score for m in ranked] == [1.0, 0.5, 0.5]
        assert ranked[1].deadline < ranked[2].deadline

    def test_score_sports_level_met(self):
        match = matching_service.score_sports_opportunity(
            sports_record(), "intermediate", "Karachi", "HIGH_SCHOOL"
        )
        assert match.match_score == 1.0  # age never scored
        assert "Meets the required level (intermediate)" in match.eligibility_met
        assert "Located in Karachi" in match.eligibility_met
        assert any("Age 14-22 requirement" in m for m in match.eligibility_missing)
        assert match.next_action.startswith("All stated eligibility requirements are met")

    def test_score_sports_level_mismatch(self):
        match = matching_service.score_sports_opportunity(
            sports_record(), "beginner", None, "HIGH_SCHOOL"
        )
        assert match.match_score == 0.0
        assert "Requires intermediate level (player level: beginner)" in match.eligibility_missing
        assert match.next_action == "Build toward intermediate level before applying."

    def test_score_sports_level_not_provided(self):
        match = matching_service.score_sports_opportunity(
            sports_record(), None, None, "HIGH_SCHOOL"
        )
        assert match.match_score == 0.0
        assert "Requires intermediate level (player level not provided)" in match.eligibility_missing

    def test_score_sports_enrollment_met(self):
        record = sports_record(
            id=4, eligibility={"enrollment": "university_student", "level": "beginner"}
        )
        match = matching_service.score_sports_opportunity(
            record, "beginner", None, "UNIVERSITY"
        )
        assert match.match_score == 1.0
        assert "Meets the enrollment requirement (university_student)" in match.eligibility_met

    def test_score_sports_enrollment_mismatch(self):
        record = sports_record(
            id=4, eligibility={"enrollment": "university_student", "level": "beginner"}
        )
        match = matching_service.score_sports_opportunity(
            record, "beginner", None, "HIGH_SCHOOL"
        )
        # level met (beginner), enrollment unmet -> 1 of 2 scored requirements
        assert match.match_score == 0.5
        assert "Meets the required level (beginner)" in match.eligibility_met
        assert "Requires university student status" in match.eligibility_missing
        assert "university student" in match.next_action

    def test_score_sports_enrollment_unverified_without_stage(self):
        record = sports_record(id=4, eligibility={"enrollment": "university_student"})
        match = matching_service.score_sports_opportunity(record, None, None, None)
        assert match.match_score == 0.0
        assert "(student enrollment unverified)" in match.eligibility_missing[0]

    def test_score_sports_no_eligibility(self):
        record = sports_record(id=9, eligibility={})
        match = matching_service.score_sports_opportunity(record, None, None, None)
        assert match.match_score == 1.0
        assert match.eligibility_met == []
        assert match.eligibility_missing == []
        assert match.next_action.startswith("No specific eligibility requirements listed")

    def test_score_sports_nationwide_location_note(self):
        record = sports_record(id=2, location="Nationwide", type="scholarship",
                               eligibility={"age_min": 14, "age_max": 20, "level": "advanced"})
        match = matching_service.score_sports_opportunity(
            record, "advanced", "Karachi", "HIGH_SCHOOL"
        )
        assert "Open nationwide" in match.eligibility_met
        assert match.match_score == 1.0

    def test_enrollment_category_mapping(self):
        assert matching_service.enrollment_category("HIGH_SCHOOL") == "school_student"
        assert matching_service.enrollment_category("CAREER_DISCOVERY") == "school_student"
        assert matching_service.enrollment_category("UNIVERSITY") == "university_student"
        assert matching_service.enrollment_category("FINAL_YEAR") == "university_student"
        assert matching_service.enrollment_category(None) is None


# ---------------------------------------------------------------------------
# GET /opportunities — database-only listing
# ---------------------------------------------------------------------------


class TestListOpportunities:

    def test_lists_all_active_records(self, opp_db, client):
        response = client.get("/api/v1/opportunities")
        assert response.status_code == 200
        items = response.json()
        assert len(items) == 6  # 7 seeded, 1 inactive
        titles = {item["title"] for item in items}
        assert "Expired Internship (Inactive Example)" not in titles
        # snake_case contract for the frontend boundary
        assert set(items[0].keys()) == {
            "id", "type", "title", "organization", "location", "deadline",
            "required_skills", "description", "source_url", "last_verified",
            "data_freshness",
        }

    def test_sorted_by_soonest_deadline(self, opp_db, client):
        items = client.get("/api/v1/opportunities").json()
        assert items[0]["title"] == "Legacy Marketing Intern"  # 2026-01-20
        assert items[1]["title"] == "Software Engineering Intern"  # 2026-09-30

    def test_type_filter(self, opp_db, client):
        internships = client.get("/api/v1/opportunities", params={"type": "internship"}).json()
        assert {i["title"] for i in internships} == {
            "Python Developer Intern",
            "Software Engineering Intern",
            "Data Analytics Intern",
            "Legacy Marketing Intern",
        }
        jobs = client.get("/api/v1/opportunities", params={"type": "job"}).json()
        assert [i["title"] for i in jobs] == ["Junior Software Developer"]

    def test_invalid_type_filter_is_422(self, opp_db, client):
        response = client.get("/api/v1/opportunities", params={"type": "fellowship"})
        assert response.status_code == 422

    def test_city_filter_includes_nationwide(self, opp_db, client):
        items = client.get("/api/v1/opportunities", params={"city": "Karachi"}).json()
        assert {i["title"] for i in items} == {
            "Python Developer Intern",
            "Software Engineering Intern",
            "Legacy Marketing Intern",
            "Junior Software Developer",
            "Merit Scholarship for Computer Science",  # Nationwide
        }
        # city matching is case-insensitive
        lower = client.get("/api/v1/opportunities", params={"city": "karachi"}).json()
        assert len(lower) == len(items)

    def test_combined_type_and_city_filter(self, opp_db, client):
        items = client.get(
            "/api/v1/opportunities", params={"type": "internship", "city": "Karachi"}
        ).json()
        assert {i["title"] for i in items} == {
            "Python Developer Intern",
            "Software Engineering Intern",
            "Legacy Marketing Intern",
        }

    def test_city_without_matches_returns_envelope(self, opp_db, client):
        # jobs live only in Karachi, so a Quetta job search has no records
        # (the Nationwide record is a scholarship and is excluded by type)
        response = client.get(
            "/api/v1/opportunities", params={"type": "job", "city": "Quetta"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["opportunities"] == []
        assert body["message"] == opportunity_service.NO_RESULTS_MESSAGE

    def test_empty_database_returns_envelope(self, client):
        response = client.get("/api/v1/opportunities")
        assert response.status_code == 200
        assert response.json()["opportunities"] == []

    def test_skills_filter(self, opp_db, client):
        items = client.get("/api/v1/opportunities", params={"skills": "Python"}).json()
        assert {i["title"] for i in items} == {
            "Python Developer Intern",
            "Software Engineering Intern",
            "Data Analytics Intern",
            "Junior Software Developer",
            "Merit Scholarship for Computer Science",  # no requirements
        }

    def test_skills_filter_multiple_comma_separated(self, opp_db, client):
        items = client.get("/api/v1/opportunities", params={"skills": "Python,Git"}).json()
        assert "Python Developer Intern" in {i["title"] for i in items}

    def test_field_filter(self, opp_db, client):
        items = client.get("/api/v1/opportunities", params={"field": "analytics"}).json()
        assert [i["title"] for i in items] == ["Data Analytics Intern"]

    def test_stale_record_carries_freshness_flag(self, opp_db, client):
        items = client.get("/api/v1/opportunities").json()
        by_title = {i["title"]: i for i in items}
        assert by_title["Legacy Marketing Intern"]["data_freshness"] == "unverified"
        assert by_title["Python Developer Intern"]["data_freshness"] is None


# ---------------------------------------------------------------------------
# GET /sports — database-only listing
# ---------------------------------------------------------------------------


class TestListSports:

    def test_lists_all_active_records(self, opp_db, client):
        items = client.get("/api/v1/sports").json()
        assert len(items) == 4  # 5 seeded, 1 inactive
        assert "Islamabad Badminton League (Inactive Example)" not in {
            i["title"] for i in items
        }
        assert set(items[0].keys()) == {
            "id", "sport", "type", "title", "organization", "location",
            "deadline", "eligibility", "description", "source_url",
            "last_verified", "data_freshness",
        }

    def test_sport_filter_case_insensitive(self, opp_db, client):
        items = client.get("/api/v1/sports", params={"sport": "badminton"}).json()
        assert {i["title"] for i in items} == {
            "Karachi Open Badminton Trials",
            "National Badminton Talent Scholarship",
        }

    def test_sports_type_filter(self, opp_db, client):
        items = client.get(
            "/api/v1/sports", params={"sport": "Badminton", "type": "trial"}
        ).json()
        assert [i["title"] for i in items] == ["Karachi Open Badminton Trials"]
        programmes = client.get("/api/v1/sports", params={"type": "programme"}).json()
        assert [i["title"] for i in programmes] == [
            "University Cricket Development Programme"
        ]

    def test_sports_city_filter_includes_nationwide(self, opp_db, client):
        items = client.get("/api/v1/sports", params={"city": "Karachi"}).json()
        assert {i["title"] for i in items} == {
            "Karachi Open Badminton Trials",
            "National Badminton Talent Scholarship",  # Nationwide
        }

    def test_sports_empty_result_envelope(self, opp_db, client):
        response = client.get("/api/v1/sports", params={"sport": "Tennis"})
        assert response.status_code == 200
        body = response.json()
        assert body["sports_opportunities"] == []
        assert body["message"] == opportunity_service.NO_RESULTS_MESSAGE

    def test_sports_invalid_type_is_422(self, opp_db, client):
        response = client.get("/api/v1/sports", params={"type": "match"})
        assert response.status_code == 422

    def test_sports_eligibility_parsed_as_object(self, opp_db, client):
        items = client.get("/api/v1/sports", params={"sport": "Badminton"}).json()
        trial = next(i for i in items if i["type"] == "trial")
        assert trial["eligibility"]["level"] == "intermediate"
        assert trial["eligibility"]["age_min"] == 14

    def test_sports_stale_record_flagged(self, opp_db, client):
        items = client.get("/api/v1/sports", params={"sport": "Cricket"}).json()
        by_title = {i["title"]: i for i in items}
        assert by_title["Lahore Under-19 Cricket Cup"]["data_freshness"] == "unverified"
        assert (
            by_title["University Cricket Development Programme"]["data_freshness"] is None
        )


# ---------------------------------------------------------------------------
# POST /opportunities/match
# ---------------------------------------------------------------------------


class TestMatchOpportunities:

    def test_404_when_student_missing(self, client):
        response = client.post("/api/v1/opportunities/match", json={"city": "Karachi"})
        assert response.status_code == 404
        assert response.json()["error"] == (
            "Student profile not found — complete onboarding first."
        )

    def test_422_blank_city(self, opp_db, client):
        response = client.post("/api/v1/opportunities/match", json={"city": "   "})
        assert response.status_code == 422
        assert response.json()["error"] == "city must be a non-empty string."

    def test_422_missing_city(self, opp_db, client):
        response = client.post(
            "/api/v1/opportunities/match", json={"opportunity_type": "internship"}
        )
        assert response.status_code == 422

    def test_422_invalid_opportunity_type(self, opp_db, client):
        response = client.post(
            "/api/v1/opportunities/match",
            json={"city": "Karachi", "opportunity_type": "scholarship"},
        )
        assert response.status_code == 422

    def test_mcp_path_returns_ranked_matches(self, opp_db, client, monkeypatch):
        records = [
            opp_record(id=1),
            opp_record(id=2, required_skills=["Python", "Data Structures", "Git"]),
        ]
        _mock_search(monkeypatch, mcp_success(records, answer="Two solid options."))

        response = client.post(
            "/api/v1/opportunities/match",
            json={"city": "Karachi", "opportunity_type": "internship"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["data_quality"] == "ai_interpreted"
        assert body["summary"] == "Two solid options."
        assert len(body["matches"]) == 2
        # ranked by deterministic score: profile skill Python ->
        # id 1 (Python, Git) = 0.5 beats id 2 (Python, DS, Git) = 0.33
        assert body["matches"][0]["opportunity_id"] == 1
        assert body["matches"][0]["match_score"] == 0.5
        assert body["matches"][0]["missing_requirements"] == ["Git"]
        assert "1 of 2 required skills" in body["matches"][0]["match_reasons"][0]
        assert body["matches"][1]["opportunity_id"] == 2
        assert body["matches"][1]["match_score"] == 0.33

    def test_mcp_path_with_request_skills_override(self, opp_db, client, monkeypatch):
        records = [opp_record(id=1)]
        _mock_search(monkeypatch, mcp_success(records))
        response = client.post(
            "/api/v1/opportunities/match",
            json={"city": "Karachi", "skills": ["Python", "Git"]},
        )
        body = response.json()
        assert body["matches"][0]["match_score"] == 1.0
        assert body["matches"][0]["missing_requirements"] == []
        assert "All 2 required skills" in body["matches"][0]["next_action"]

    def test_job_type_match(self, opp_db, client, monkeypatch):
        record = opp_record(
            id=6, type="job", title="Junior Software Developer",
            required_skills=["Python", "Django", "Git"],
        )
        _mock_search(monkeypatch, mcp_success([record], tool="search_jobs"))
        response = client.post(
            "/api/v1/opportunities/match",
            json={"city": "Karachi", "opportunity_type": "job"},
        )
        body = response.json()
        assert response.status_code == 200
        assert body["matches"][0]["match_score"] == 0.33
        assert body["matches"][0]["missing_requirements"] == ["Django", "Git"]

    def test_fallback_path_is_unranked_with_note(self, opp_db, client, monkeypatch):
        # retrieval (deadline) order: SWE intern first, Python dev second
        records = [
            opp_record(id=2, required_skills=["Python", "Data Structures", "Git"]),
            opp_record(id=1),
        ]
        _mock_search(monkeypatch, fallback_result(records))

        response = client.post("/api/v1/opportunities/match", json={"city": "Karachi"})
        assert response.status_code == 200
        body = response.json()
        assert body["data_quality"] == "unranked"
        assert body["note"] == "Live ranking is temporarily unavailable."
        assert body["summary"] is None
        # unranked: retrieval order kept (NOT re-sorted by score)
        assert body["matches"][0]["opportunity_id"] == 2
        assert body["matches"][0]["match_score"] == 0.33
        assert body["matches"][1]["opportunity_id"] == 1
        assert body["matches"][1]["match_score"] == 0.5

    def test_ungrounded_answer_replaced_by_direct_query(
        self, opp_db, client, monkeypatch
    ):
        # Qwen answered from general knowledge with NO tool calls — the
        # answer must be discarded and the deterministic direct query used.
        _mock_search(
            monkeypatch,
            {
                "answer": "I could not find anything.",
                "tool_calls": [],
                "data_quality": "ai_interpreted",
            },
        )
        response = client.post("/api/v1/opportunities/match", json={"city": "Karachi"})
        assert response.status_code == 200
        body = response.json()
        assert body["data_quality"] == "unranked"
        assert body["summary"] is None
        assert body["note"] == "Live ranking is temporarily unavailable."
        # direct query: active Karachi internships where the profile skill
        # (Python) matches or no requirements — SWE first (deadline order)
        assert [m["opportunity_id"] for m in body["matches"]] == [2, 1]

    def test_no_results_message(self, opp_db, client, monkeypatch):
        _mock_search(monkeypatch, fallback_result([]))
        response = client.post(
            "/api/v1/opportunities/match", json={"city": "Quetta"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["matches"] == []
        assert body["message"] == opportunity_service.NO_RESULTS_MESSAGE
        assert body["data_quality"] == "unranked"

    def test_503_when_the_whole_chain_fails(self, opp_db, client, monkeypatch):
        def broken(*args, **kwargs):
            raise AIUnavailableError("MCP search failed after 2 attempts.")

        monkeypatch.setattr(
            opportunity_service.mcp_search_service, "search_with_mcp", broken
        )
        response = client.post("/api/v1/opportunities/match", json={"city": "Karachi"})
        assert response.status_code == 503
        assert response.json()["error"] == "AI service temporarily unavailable"

    def test_matches_persisted_with_replace_semantics(
        self, opp_db, client, monkeypatch
    ):
        _mock_search(monkeypatch, mcp_success([opp_record(id=1), opp_record(id=2)]))
        client.post("/api/v1/opportunities/match", json={"city": "Karachi"})
        rows = (
            opp_db.query(StudentOpportunityMatch)
            .filter(StudentOpportunityMatch.student_id == 1)
            .all()
        )
        assert len(rows) == 2

        # a second match call REPLACES the cache (not appends)
        _mock_search(monkeypatch, mcp_success([opp_record(id=2)]))
        client.post("/api/v1/opportunities/match", json={"city": "Karachi"})
        rows = (
            opp_db.query(StudentOpportunityMatch)
            .filter(StudentOpportunityMatch.student_id == 1)
            .all()
        )
        assert len(rows) == 1
        assert rows[0].opportunity_id == 2

    def test_persisted_row_content(self, opp_db, client, monkeypatch):
        _mock_search(monkeypatch, mcp_success([opp_record(id=1)]))
        body = client.post(
            "/api/v1/opportunities/match", json={"city": "Karachi"}
        ).json()
        row = (
            opp_db.query(StudentOpportunityMatch)
            .filter(StudentOpportunityMatch.opportunity_id == 1)
            .one()
        )
        assert row.student_id == 1
        assert row.match_score == body["matches"][0]["match_score"]
        assert json.loads(row.missing_requirements) == ["Git"]
        assert row.next_action == body["matches"][0]["next_action"]
        assert row.matched_at is not None


# ---------------------------------------------------------------------------
# POST /sports/match
# ---------------------------------------------------------------------------


class TestMatchSports:

    def test_404_when_student_missing(self, client):
        response = client.post(
            "/api/v1/sports/match", json={"sport": "Badminton"}
        )
        assert response.status_code == 404
        assert response.json()["error"] == (
            "Student profile not found — complete onboarding first."
        )

    def test_422_blank_sport(self, opp_db, client):
        response = client.post("/api/v1/sports/match", json={"sport": "  "})
        assert response.status_code == 422
        assert response.json()["error"] == "sport must be a non-empty string."

    def test_422_missing_sport(self, opp_db, client):
        response = client.post("/api/v1/sports/match", json={"location": "Karachi"})
        assert response.status_code == 422

    def test_mcp_path_returns_ranked_matches(self, opp_db, client, monkeypatch):
        records = [
            sports_record(id=1),  # trial, level intermediate, Karachi
            sports_record(
                id=2, type="scholarship", location="Nationwide",
                title="National Badminton Talent Scholarship",
                eligibility={"age_min": 14, "age_max": 20, "level": "advanced"},
            ),
        ]
        _mock_search(
            monkeypatch,
            mcp_success(records, answer="Two badminton options.", tool="search_sports_opportunities"),
        )
        response = client.post(
            "/api/v1/sports/match",
            json={"sport": "Badminton", "location": "Karachi", "level": "intermediate"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["data_quality"] == "ai_interpreted"
        assert body["summary"] == "Two badminton options."
        # ranked: the trial (level met -> 1.0) beats the scholarship (0.0)
        assert body["matches"][0]["opportunity_id"] == 1
        assert body["matches"][0]["match_score"] == 1.0
        assert "Meets the required level (intermediate)" in body["matches"][0]["eligibility_met"]
        assert "Located in Karachi" in body["matches"][0]["eligibility_met"]
        assert any("Age 14-22" in m for m in body["matches"][0]["eligibility_missing"])
        assert body["matches"][1]["opportunity_id"] == 2
        assert body["matches"][1]["match_score"] == 0.0
        assert "Requires advanced level (player level: intermediate)" in (
            body["matches"][1]["eligibility_missing"]
        )
        assert "Open nationwide" in body["matches"][1]["eligibility_met"]

    def test_enrollment_evaluated_against_student_stage(
        self, opp_db, client, monkeypatch
    ):
        record = sports_record(
            id=4, sport="Cricket", type="programme",
            title="University Cricket Development Programme",
            location="Lahore",
            eligibility={"enrollment": "university_student", "level": "beginner"},
        )
        _mock_search(monkeypatch, mcp_success([record]))
        # demo student is HIGH_SCHOOL -> enrollment requirement unmet, but the
        # level (beginner) matches -> 1 of 2 scored requirements met
        response = client.post(
            "/api/v1/sports/match", json={"sport": "Cricket", "level": "beginner"}
        )
        body = response.json()
        assert response.status_code == 200
        assert body["matches"][0]["match_score"] == 0.5
        assert "Meets the required level (beginner)" in (
            body["matches"][0]["eligibility_met"]
        )
        assert "Requires university student status" in (
            body["matches"][0]["eligibility_missing"]
        )
        assert "university student" in body["matches"][0]["next_action"]

    def test_fallback_path_is_unranked_with_note(self, opp_db, client, monkeypatch):
        # id 2 requires advanced level (unmet) so it scores 0.0; retrieval
        # order is kept even though id 1 scores 1.0
        records = [
            sports_record(id=2, eligibility={"age_min": 14, "age_max": 20, "level": "advanced"}),
            sports_record(id=1),
        ]
        _mock_search(monkeypatch, fallback_result(records))
        response = client.post(
            "/api/v1/sports/match",
            json={"sport": "Badminton", "location": "Karachi", "level": "intermediate"},
        )
        body = response.json()
        assert response.status_code == 200
        assert body["data_quality"] == "unranked"
        assert body["note"] == "Live ranking is temporarily unavailable."
        # retrieval order kept even though match 1 scores higher
        assert body["matches"][0]["opportunity_id"] == 2
        assert body["matches"][0]["match_score"] == 0.0

    def test_ungrounded_answer_replaced_by_direct_query(
        self, opp_db, client, monkeypatch
    ):
        _mock_search(
            monkeypatch,
            {
                "answer": "No badminton data.",
                "tool_calls": [],
                "data_quality": "ai_interpreted",
            },
        )
        response = client.post(
            "/api/v1/sports/match", json={"sport": "Badminton", "location": "Karachi"}
        )
        body = response.json()
        assert response.status_code == 200
        assert body["data_quality"] == "unranked"
        assert body["summary"] is None
        # direct query: active Badminton records, Karachi + Nationwide
        assert {m["opportunity_id"] for m in body["matches"]} == {1, 2}

    def test_no_results_message(self, opp_db, client, monkeypatch):
        _mock_search(monkeypatch, fallback_result([]))
        response = client.post("/api/v1/sports/match", json={"sport": "Tennis"})
        body = response.json()
        assert response.status_code == 200
        assert body["matches"] == []
        assert body["message"] == opportunity_service.NO_RESULTS_MESSAGE

    def test_sports_match_never_persists(self, opp_db, client, monkeypatch):
        _mock_search(monkeypatch, mcp_success([sports_record(id=1)]))
        client.post(
            "/api/v1/sports/match",
            json={"sport": "Badminton", "location": "Karachi", "level": "intermediate"},
        )
        assert opp_db.query(StudentOpportunityMatch).count() == 0

    def test_503_when_the_whole_chain_fails(self, opp_db, client, monkeypatch):
        def broken(*args, **kwargs):
            raise AIUnavailableError("MCP search failed after 2 attempts.")

        monkeypatch.setattr(
            opportunity_service.mcp_search_service, "search_with_mcp", broken
        )
        response = client.post("/api/v1/sports/match", json={"sport": "Badminton"})
        assert response.status_code == 503


# ---------------------------------------------------------------------------
# Full chain — the real Pattern B plumbing with only Qwen + transport mocked
# ---------------------------------------------------------------------------


class TestMatchFullChain:
    """
    These tests run the whole chain with only the OpenAI client and the MCP
    SSE transport replaced: match_* -> search_with_mcp -> ai_service
    .call_with_mcp (real loop) -> tool executor -> the REAL tool function
    reading the test database -> deterministic scoring.
    """

    def test_full_chain_opportunity_match(self, opp_db, client, monkeypatch):
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_internships",
                    "description": "Search active internship records.",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ]
        monkeypatch.setattr(mcp_client, "list_tools", lambda server: tools)

        def fake_call_tool(server, name, arguments):
            # Route straight into the real tool function (no SSE transport).
            return mcp_search_service.FALLBACK_TOOLS[name](**arguments)

        monkeypatch.setattr(mcp_client, "call_tool", fake_call_tool)

        sequence = [
            tool_call_response(
                "search_internships",
                json.dumps({"city": "Karachi", "skills": ["Python"]}),
            ),
            text_response("Found 2 internships in Karachi for a Python beginner."),
        ]
        service = AIService(client=mock_ai_client(sequence))
        monkeypatch.setattr(mcp_search_service, "get_ai_service", lambda: service)

        response = client.post(
            "/api/v1/opportunities/match", json={"city": "Karachi"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["data_quality"] == "ai_interpreted"
        assert body["summary"] == "Found 2 internships in Karachi for a Python beginner."
        assert len(body["matches"]) == 2
        # scores computed deterministically from the seeded DB records
        scores = {m["opportunity_id"]: m["match_score"] for m in body["matches"]}
        assert scores[1] == 0.5
        assert scores[2] == 0.33
        # and persisted for the student
        assert (
            opp_db.query(StudentOpportunityMatch)
            .filter(StudentOpportunityMatch.student_id == 1)
            .count()
            == 2
        )

    def test_full_chain_sports_match(self, opp_db, client, monkeypatch):
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_sports_opportunities",
                    "description": "Search active sports opportunity records.",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ]
        monkeypatch.setattr(mcp_client, "list_tools", lambda server: tools)

        def fake_call_tool(server, name, arguments):
            return mcp_search_service.FALLBACK_TOOLS[name](**arguments)

        monkeypatch.setattr(mcp_client, "call_tool", fake_call_tool)

        sequence = [
            tool_call_response(
                "search_sports_opportunities",
                json.dumps({"sport": "Badminton", "city": "Karachi"}),
            ),
            text_response("Two badminton opportunities found."),
        ]
        service = AIService(client=mock_ai_client(sequence))
        monkeypatch.setattr(mcp_search_service, "get_ai_service", lambda: service)

        response = client.post(
            "/api/v1/sports/match",
            json={"sport": "Badminton", "location": "Karachi", "level": "intermediate"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["data_quality"] == "ai_interpreted"
        # trial (level met) ranks above scholarship (level mismatch)
        assert body["matches"][0]["opportunity_id"] == 1
        assert body["matches"][0]["match_score"] == 1.0
        assert body["matches"][1]["opportunity_id"] == 2
        assert body["matches"][1]["match_score"] == 0.0
