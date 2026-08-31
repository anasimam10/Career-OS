"""
Retrieval layer tests (architecture_master §14/§15).

Covers:
- FTS5 module: availability probe, safe MATCH expressions, id search,
  trigger synchronization with ORM writes
- SimpleCache: get/set/delete/clear, TTL expiry
- career_retrieval: FTS search + LIKE fallback, field filter, active
  filter, cached searches
- opportunity_retrieval: trust filters (CANDIDATE hidden, expired hidden),
  city/skills/stage filters, fresh window, bounded results
- university_retrieval: city/type/field filters, program lookups,
  CANDIDATE universities hidden, cached searches
- sports_retrieval: sport case-insensitivity, Nationwide city rule,
  trust filters
- alumni_retrieval: field/career/university filters, verified-first
  ordering
- learning_retrieval: skill match, level filter, inactive hidden
- student_retrieval: full context assembly, active milestones
"""

from __future__ import annotations

import json
from datetime import date, timedelta

import pytest

from cache import SimpleCache, cache
from models.alumni import Alumni
from models.career import Career
from models.learning import LearningResource
from models.opportunity import Opportunity, SportsOpportunity
from models.roadmap import Milestone, Roadmap
from models.student import Student, StudentProfile
from models.university import Program, University
from retrieval import (
    alumni_retrieval,
    career_retrieval,
    learning_retrieval,
    opportunity_retrieval,
    sports_retrieval,
    student_retrieval,
    university_retrieval,
)
from retrieval import fts as fts_module


def soon(days: int) -> date:
    return date.today() + timedelta(days=days)


def past(days: int) -> date:
    return date.today() - timedelta(days=days)


# ---------------------------------------------------------------------------
# FTS5 module
# ---------------------------------------------------------------------------


class TestFts:
    def test_match_expression_quotes_tokens_safely(self):
        # Special characters must never produce FTS5 syntax errors.
        expr = fts_module._match_expression('drop table; "quoted" --')
        assert expr == '"drop" "table" "quoted"'

    def test_match_expression_empty_for_no_tokens(self):
        assert fts_module._match_expression("!!! ...") is None
        assert fts_module._match_expression("") is None

    def test_orm_inserts_are_indexed_immediately(self, db_session):
        db_session.add(Career(slug="swe", name="Software Engineering", field="Technology"))
        db_session.commit()
        ids = fts_module.fts_search_ids(db_session, "careers", "software engineering")
        assert ids == [1]

    def test_search_returns_ids_not_rows(self, db_session):
        db_session.add(Career(slug="swe", name="Software Engineering", field="Technology"))
        db_session.add(Career(slug="med", name="Medicine", field="Healthcare"))
        db_session.commit()
        ids = fts_module.fts_search_ids(db_session, "careers", "medicine")
        assert ids == [2]  # the medicine row only

    def test_unknown_table_returns_empty(self, db_session):
        assert fts_module.fts_search_ids(db_session, "nope", "x") == []


# ---------------------------------------------------------------------------
# SimpleCache
# ---------------------------------------------------------------------------


class TestSimpleCache:
    def test_set_get_delete(self):
        c = SimpleCache()
        c.set("k", {"a": 1}, 60)
        assert c.get("k") == {"a": 1}
        c.delete("k")
        assert c.get("k") is None

    def test_ttl_expiry(self):
        c = SimpleCache()
        c.set("k", "v", 0)  # expires immediately
        assert c.get("k") is None

    def test_clear_drops_everything(self):
        c = SimpleCache()
        c.set("a", 1, 60)
        c.set("b", 2, 60)
        c.clear()
        assert c.get("a") is None and c.get("b") is None

    def test_delete_missing_key_is_silent(self):
        SimpleCache().delete("never-set")

    def test_expired_entry_is_dropped_lazily(self):
        c = SimpleCache()
        c.set("k", "v", 0)
        c.get("k")  # triggers lazy expiry
        assert "k" not in c._store


# ---------------------------------------------------------------------------
# career_retrieval
# ---------------------------------------------------------------------------


class TestCareerRetrieval:
    @pytest.fixture(autouse=True)
    def careers(self, db_session):
        db_session.add_all(
            [
                Career(slug="swe", name="Software Engineering", field="Technology",
                       category="Engineering & Technology", demand_level="HIGH"),
                Career(slug="ds", name="Data Science", field="Technology",
                       category="Engineering & Technology"),
                Career(slug="med", name="Medicine", field="Healthcare",
                       category="Healthcare"),
                Career(slug="inactive", name="Old Career", field="Technology",
                       is_active=False),
            ]
        )
        db_session.commit()

    def test_search_matches_name_via_fts(self, db_session):
        results = career_retrieval.search_careers(db_session, query="software")
        assert [r["slug"] for r in results] == ["swe"]

    def test_search_falls_back_to_like(self, db_session, monkeypatch):
        monkeypatch.setattr(career_retrieval, "fts_search_ids", lambda *a, **k: [])
        results = career_retrieval.search_careers(db_session, query="medicine")
        assert [r["slug"] for r in results] == ["med"]

    def test_field_filter_narrows(self, db_session):
        results = career_retrieval.search_careers(db_session, field="Healthcare")
        assert [r["slug"] for r in results] == ["med"]

    def test_inactive_careers_never_returned(self, db_session):
        results = career_retrieval.search_careers(db_session, query="Old Career")
        assert results == []

    def test_results_are_cached(self, db_session):
        first = career_retrieval.search_careers(db_session, query="software")
        # DB changes must NOT appear while the cached result is live.
        db_session.add(Career(slug="swe2", name="Software Testing", field="Technology"))
        db_session.commit()
        second = career_retrieval.search_careers(db_session, query="software")
        assert second == first
        # Clearing the cache re-queries.
        cache.clear()
        third = career_retrieval.search_careers(db_session, query="software")
        assert {r["slug"] for r in third} == {"swe", "swe2"}

    def test_get_career_skills(self, db_session):
        career = db_session.query(Career).filter_by(slug="swe").one()
        career.required_skills = json.dumps(["Python", "Git"])
        db_session.commit()
        assert career_retrieval.get_career_skills(db_session, career.id) == ["Python", "Git"]
        assert career_retrieval.get_career_skills(db_session, 999) == []

    def test_get_career_programs_resolves_career_ids(self, db_session):
        career = db_session.query(Career).filter_by(slug="swe").one()
        uni = University(name="U", slug="u", verification_status="VERIFIED")
        db_session.add(uni)
        db_session.flush()
        db_session.add_all(
            [
                Program(university_id=uni.id, name="BS CS",
                        verification_status="VERIFIED",
                        career_ids=json.dumps([career.id])),
                Program(university_id=uni.id, name="BBA",
                        verification_status="VERIFIED", career_ids=json.dumps([])),
                Program(university_id=uni.id, name="Candidate Prog",
                        verification_status="CANDIDATE",
                        career_ids=json.dumps([career.id])),
            ]
        )
        db_session.commit()
        programs = career_retrieval.get_career_programs(db_session, career.id)
        assert [p["name"] for p in programs] == ["BS CS"]


# ---------------------------------------------------------------------------
# opportunity_retrieval
# ---------------------------------------------------------------------------


class TestOpportunityRetrieval:
    @pytest.fixture(autouse=True)
    def opportunities(self, db_session):
        db_session.add_all(
            [
                Opportunity(type="internship", title="Python Intern",
                            organization="A", location="Karachi", deadline=soon(10),
                            required_skills=json.dumps(["Python"]),
                            verification_status="VALIDATED",
                            last_verified=date.today(), is_active=True),
                Opportunity(type="internship", title="Candidate Intern",
                            organization="B", location="Karachi", deadline=soon(10),
                            verification_status="CANDIDATE", is_active=True),
                Opportunity(type="job", title="Expired Job",
                            organization="C", location="Karachi", deadline=past(5),
                            verification_status="VALIDATED", is_active=True),
                Opportunity(type="job", title="Inactive Job",
                            organization="D", location="Karachi", deadline=soon(10),
                            verification_status="VALIDATED", is_active=False),
            ]
        )
        db_session.commit()

    def test_only_verified_active_fresh_records_returned(self, db_session):
        titles = [o["title"] for o in opportunity_retrieval.search_opportunities(db_session)]
        assert titles == ["Python Intern"]

    def test_type_filter(self, db_session):
        results = opportunity_retrieval.search_opportunities(db_session, opp_type="job")
        assert results == []  # the only job records are expired/inactive

    def test_city_filter_includes_nationwide(self, db_session):
        db_session.add(Opportunity(type="scholarship", title="National Fund",
                                   location="Nationwide", deadline=soon(30),
                                   verification_status="VALIDATED", is_active=True))
        db_session.commit()
        titles = [
            o["title"]
            for o in opportunity_retrieval.search_opportunities(db_session, city="Karachi")
        ]
        assert titles == ["Python Intern", "National Fund"]

    def test_skills_filter_no_requirement_matches(self, db_session):
        db_session.add(Opportunity(type="scholarship", title="Open Fund",
                                   location="Karachi", deadline=soon(30),
                                   required_skills=json.dumps([]),
                                   verification_status="VALIDATED", is_active=True))
        db_session.commit()
        titles = [
            o["title"]
            for o in opportunity_retrieval.search_opportunities(
                db_session, skills=["Python"]
            )
        ]
        assert titles == ["Python Intern", "Open Fund"]

    def test_stage_filter_excludes_other_stage(self, db_session):
        db_session.add(Opportunity(type="job", title="Uni Job", location="Karachi",
                                   deadline=soon(30), required_education_stage="UNIVERSITY",
                                   verification_status="VALIDATED", is_active=True))
        db_session.commit()
        # HIGH_SCHOOL student: the UNIVERSITY-only job is excluded.
        titles = [
            o["title"]
            for o in opportunity_retrieval.search_opportunities(db_session, stage="HIGH_SCHOOL")
        ]
        assert titles == ["Python Intern"]

    def test_results_are_bounded(self, db_session):
        for i in range(15):
            db_session.add(Opportunity(type="internship", title=f"Extra {i}",
                                       location="Karachi", deadline=soon(20 + i),
                                       verification_status="VALIDATED", is_active=True))
        db_session.commit()
        assert len(opportunity_retrieval.search_opportunities(db_session, limit=5)) == 5

    def test_get_opportunity_hides_candidate_records(self, db_session):
        candidate = (
            db_session.query(Opportunity).filter_by(title="Candidate Intern").one()
        )
        assert opportunity_retrieval.get_opportunity(db_session, candidate.id) is None

    def test_get_opportunity_returns_visible_record(self, db_session):
        visible = db_session.query(Opportunity).filter_by(title="Python Intern").one()
        record = opportunity_retrieval.get_opportunity(db_session, visible.id)
        assert record is not None and record["title"] == "Python Intern"
        assert record["required_skills"] == ["Python"]

    def test_fresh_opportunities_excludes_stale_verification(self, db_session):
        db_session.add(Opportunity(type="internship", title="Stale Verified",
                                   location="Karachi", deadline=soon(10),
                                   verification_status="VALIDATED",
                                   last_verified=past(60), is_active=True))
        db_session.commit()
        titles = [
            o["title"]
            for o in opportunity_retrieval.get_fresh_opportunities(db_session)
        ]
        assert "Stale Verified" not in titles
        assert "Python Intern" in titles


# ---------------------------------------------------------------------------
# university_retrieval
# ---------------------------------------------------------------------------


class TestUniversityRetrieval:
    @pytest.fixture(autouse=True)
    def universities(self, db_session):
        nust = University(name="National University", short_name="NUST", slug="nust",
                          city="Islamabad", province="Islamabad", type="PUBLIC",
                          hec_recognized=True, verification_status="VERIFIED")
        lums = University(name="Lahore University", short_name="LUMS", slug="lums",
                          city="Lahore", province="Punjab", type="PRIVATE",
                          verification_status="VERIFIED")
        hidden = University(name="Candidate University", slug="candidate",
                            city="Karachi", verification_status="CANDIDATE")
        db_session.add_all([nust, lums, hidden])
        db_session.flush()
        db_session.add_all(
            [
                Program(university_id=nust.id, name="BS Computer Science",
                        field="Computer Science", verification_status="VERIFIED"),
                Program(university_id=lums.id, name="BBA",
                        field="Business Administration", verification_status="VERIFIED"),
            ]
        )
        db_session.commit()

    def test_candidate_universities_hidden(self, db_session):
        names = [u["short_name"] for u in university_retrieval.search_universities(db_session)]
        assert names == ["LUMS", "NUST"]

    def test_city_filter(self, db_session):
        results = university_retrieval.search_universities(db_session, city="Lahore")
        assert [u["slug"] for u in results] == ["lums"]

    def test_type_filter(self, db_session):
        results = university_retrieval.search_universities(db_session, uni_type="public")
        assert [u["slug"] for u in results] == ["nust"]

    def test_field_filter_via_programs(self, db_session):
        results = university_retrieval.search_universities(db_session, field="Business")
        assert [u["slug"] for u in results] == ["lums"]

    def test_name_search(self, db_session):
        results = university_retrieval.search_universities(db_session, query="Lahore")
        assert [u["slug"] for u in results] == ["lums"]

    def test_get_university_hides_candidate(self, db_session):
        hidden = db_session.query(University).filter_by(slug="candidate").one()
        assert university_retrieval.get_university(db_session, hidden.id) is None

    def test_get_programs_with_field_filter(self, db_session):
        nust = db_session.query(University).filter_by(slug="nust").one()
        programs = university_retrieval.get_programs(db_session, nust.id, field="Computer")
        assert [p["name"] for p in programs] == ["BS Computer Science"]
        assert university_retrieval.get_programs(db_session, nust.id, field="Medicine") == []

    def test_search_is_cached(self, db_session):
        first = university_retrieval.search_universities(db_session, city="Lahore")
        db_session.add(University(name="Lahore Campus U", slug="lcu", city="Lahore",
                                  verification_status="VERIFIED"))
        db_session.commit()
        second = university_retrieval.search_universities(db_session, city="Lahore")
        assert second == first  # cached, no re-query


# ---------------------------------------------------------------------------
# sports_retrieval
# ---------------------------------------------------------------------------


class TestSportsRetrieval:
    @pytest.fixture(autouse=True)
    def sports(self, db_session):
        db_session.add_all(
            [
                SportsOpportunity(sport="Badminton", type="trial",
                                  title="Karachi Trials", location="Karachi",
                                  deadline=soon(10), verification_status="VALIDATED",
                                  is_active=True),
                SportsOpportunity(sport="Badminton", type="scholarship",
                                  title="National Fund", location="Nationwide",
                                  deadline=soon(30), verification_status="VALIDATED",
                                  is_active=True),
                SportsOpportunity(sport="Cricket", type="tournament",
                                  title="Expired Cup", location="Lahore",
                                  deadline=past(3), verification_status="VALIDATED",
                                  is_active=True),
            ]
        )
        db_session.commit()

    def test_sport_filter_case_insensitive(self, db_session):
        results = sports_retrieval.search_sports_opportunities(db_session, sport="badminton")
        assert {r["title"] for r in results} == {"Karachi Trials", "National Fund"}

    def test_expired_never_returned(self, db_session):
        titles = [r["title"] for r in sports_retrieval.search_sports_opportunities(db_session)]
        assert "Expired Cup" not in titles

    def test_city_includes_nationwide(self, db_session):
        results = sports_retrieval.search_sports_opportunities(db_session, city="Karachi")
        assert {r["title"] for r in results} == {"Karachi Trials", "National Fund"}

    def test_get_sport_hides_expired(self, db_session):
        expired = db_session.query(SportsOpportunity).filter_by(title="Expired Cup").one()
        assert sports_retrieval.get_sport(db_session, expired.id) is None


# ---------------------------------------------------------------------------
# alumni_retrieval
# ---------------------------------------------------------------------------


class TestAlumniRetrieval:
    @pytest.fixture(autouse=True)
    def alumni(self, db_session):
        lums = University(name="LUMS", slug="lums", verification_status="VERIFIED")
        nust = University(name="NUST", slug="nust", verification_status="VERIFIED")
        kemu = University(name="KEMU", slug="kemu", verification_status="VERIFIED")
        db_session.add_all([lums, nust, kemu])
        db_session.flush()
        db_session.add_all(
            [
                Alumni(name="Unverified Alum", university="LUMS", field="Computer Science",
                       role="Engineer", career_id=1, university_id=lums.id, is_verified=False),
                Alumni(name="Verified Alum", university="NUST", field="Computer Science",
                       role="Engineer", career_id=1, university_id=nust.id, is_verified=True),
                Alumni(name="Med Alum", university="KEMU", field="Medicine",
                       role="Doctor", career_id=3, university_id=kemu.id, is_verified=False),
            ]
        )
        db_session.commit()

    def test_verified_first_ordering(self, db_session):
        results = alumni_retrieval.find_alumni(db_session, field="Computer Science")
        assert [r["name"] for r in results] == ["Verified Alum", "Unverified Alum"]

    def test_career_filter(self, db_session):
        results = alumni_retrieval.find_alumni(db_session, career_id=3)
        assert [r["name"] for r in results] == ["Med Alum"]

    def test_university_filter(self, db_session):
        lums = db_session.query(University).filter_by(slug="lums").one()
        results = alumni_retrieval.find_alumni(db_session, university_id=lums.id)
        assert [r["name"] for r in results] == ["Unverified Alum"]

    def test_get_alumni(self, db_session):
        record = alumni_retrieval.get_alumni(db_session, 1)
        assert record is not None and record["name"] == "Unverified Alum"
        assert alumni_retrieval.get_alumni(db_session, 999) is None


# ---------------------------------------------------------------------------
# learning_retrieval
# ---------------------------------------------------------------------------


class TestLearningRetrieval:
    @pytest.fixture(autouse=True)
    def resources(self, db_session):
        db_session.add_all(
            [
                LearningResource(skill_name="Python", title="Python for Everybody",
                                 type="course", provider="py4e", url="https://py4e.com",
                                 level="beginner", is_free=True,
                                 verification_status="VERIFIED"),
                LearningResource(skill_name="Python", title="Advanced Python",
                                 type="course", provider="x", url="https://x.dev",
                                 level="advanced", verification_status="VERIFIED"),
                LearningResource(skill_name="Python", title="Inactive Course",
                                 type="course", provider="y", url="https://y.dev",
                                 verification_status="VERIFIED", is_active=False),
                LearningResource(skill_name="SQL", title="Intro to SQL",
                                 type="course", provider="kaggle",
                                 url="https://kaggle.com/sql",
                                 verification_status="VERIFIED"),
            ]
        )
        db_session.commit()

    def test_get_resources_for_skill_case_insensitive(self, db_session):
        titles = [
            r["title"]
            for r in learning_retrieval.get_resources_for_skill(db_session, "python")
        ]
        assert titles == ["Advanced Python", "Python for Everybody"]

    def test_level_filter(self, db_session):
        titles = [
            r["title"]
            for r in learning_retrieval.get_resources_for_skill(
                db_session, "Python", level="beginner"
            )
        ]
        assert titles == ["Python for Everybody"]

    def test_inactive_resources_hidden(self, db_session):
        titles = [
            r["title"]
            for r in learning_retrieval.get_resources_for_skill(db_session, "Python")
        ]
        assert "Inactive Course" not in titles

    def test_search_resources_matches_skill_and_title(self, db_session):
        by_skill = learning_retrieval.search_resources(db_session, "SQL")
        assert [r["title"] for r in by_skill] == ["Intro to SQL"]
        by_title = learning_retrieval.search_resources(db_session, "Everybody")
        assert [r["title"] for r in by_title] == ["Python for Everybody"]

    def test_empty_skill_returns_empty(self, db_session):
        assert learning_retrieval.get_resources_for_skill(db_session, "  ") == []


# ---------------------------------------------------------------------------
# student_retrieval
# ---------------------------------------------------------------------------


class TestStudentRetrieval:
    @pytest.fixture
    def student(self, db_session):
        student = Student(id=7, name="Ayesha", email="a@t.pk", password_hash="h",
                          education_stage="HIGH_SCHOOL", career_goal="Data Science",
                          sports_interest="Cricket",
                          motivation_tags=json.dumps(["curiosity"]))
        db_session.add(student)
        db_session.flush()
        db_session.add(StudentProfile(
            student_id=7,
            interests=json.dumps(["Technology"]),
            skills=json.dumps([{"name": "Python", "level": "beginner"}]),
        ))
        roadmap = Roadmap(student_id=7, current_stage="SKILL_BUILDING",
                          current_step_title="Learn Python")
        db_session.add(roadmap)
        db_session.flush()
        db_session.add_all(
            [
                Milestone(roadmap_id=roadmap.id, title="First", stage="S1",
                          order_index=0, status="pending"),
                Milestone(roadmap_id=roadmap.id, title="Second", stage="S1",
                          order_index=1, status="pending"),
                Milestone(roadmap_id=roadmap.id, title="Done", stage="S1",
                          order_index=2, status="completed"),
            ]
        )
        db_session.commit()
        return student

    def test_context_assembles_profile_and_roadmap(self, db_session, student):
        context = student_retrieval.get_student_context(db_session, 7)
        assert context["name"] == "Ayesha"
        assert context["skills"] == [{"name": "Python", "level": "beginner"}]
        assert context["current_stage"] == "SKILL_BUILDING"
        assert context["motivation_tags"] == ["curiosity"]

    def test_context_missing_student(self, db_session):
        assert student_retrieval.get_student_context(db_session, 999) is None

    def test_active_milestones_bounded_and_ordered(self, db_session, student):
        milestones = student_retrieval.get_active_milestones(db_session, 7, limit=3)
        assert [m["title"] for m in milestones] == ["First", "Second"]

    def test_active_milestones_no_roadmap(self, db_session):
        assert student_retrieval.get_active_milestones(db_session, 999) == []
