"""
Tests: health endpoint, CORS, database init, models, repositories, schemas.
"""

import json
from datetime import datetime

import pytest
from pydantic import ValidationError

from models.student import Student, StudentProfile
from models.career import Career
from models.roadmap import Roadmap, Milestone
from models.opportunity import Opportunity, SportsOpportunity, StudentOpportunityMatch
from models.alumni import Alumni
from models.base import Base

from repositories.student_repo import StudentRepository
from repositories.career_repo import CareerRepository

from schemas.shared import EducationStage, MilestoneStatus, NextBestAction
from schemas.requests import OnboardingPayload, Skill
from schemas.responses import HealthResponse, CareerListItem, CareerDetail


# =========================================================================
# 1. HEALTH ENDPOINT
# =========================================================================


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body == {"status": "ok"}

    def test_health_response_model(self, client):
        resp = client.get("/api/v1/health")
        validated = HealthResponse.model_validate(resp.json())
        assert validated.status == "ok"


# =========================================================================
# 2. CORS CONFIGURATION
# =========================================================================


class TestCORS:
    def test_cors_header_present(self, client):
        resp = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        # The preflight should succeed and include the origin
        assert resp.status_code == 200
        assert "access-control-allow-origin" in resp.headers
        assert resp.headers["access-control-allow-origin"] == "http://localhost:3000"


# =========================================================================
# 3. DATABASE INITIALISATION
# =========================================================================


class TestDatabaseInit:
    def test_all_tables_created(self, db_session):
        """Verify that all 9 tables exist in the test database."""
        from sqlalchemy import inspect

        inspector = inspect(db_session.bind)
        table_names = set(inspector.get_table_names())

        expected_tables = {
            "students",
            "student_profiles",
            "careers",
            "roadmaps",
            "milestones",
            "alumni",
            "opportunities",
            "sports_opportunities",
            "student_opportunity_matches",
        }
        assert expected_tables.issubset(table_names), (
            f"Missing tables: {expected_tables - table_names}"
        )

    def test_empty_database(self, db_session):
        """Fresh database should have zero rows in every table."""
        assert db_session.query(Student).count() == 0
        assert db_session.query(Career).count() == 0
        assert db_session.query(Roadmap).count() == 0
        assert db_session.query(Alumni).count() == 0


# =========================================================================
# 4. CORE MODELS
# =========================================================================


class TestModels:
    def test_create_student(self, db_session):
        student = Student(
            name="Ali Khan",
            email="ali@example.com",
            password_hash="hashed",
            education_stage="HIGH_SCHOOL",
        )
        db_session.add(student)
        db_session.commit()
        db_session.refresh(student)

        assert student.id is not None
        assert student.name == "Ali Khan"
        assert student.education_stage == "HIGH_SCHOOL"
        assert student.created_at is not None

    def test_create_career(self, db_session):
        career = Career(
            slug="software-engineering",
            name="Software Engineering",
            field="Technology",
            demand_level="HIGH",
            competition_level="HIGH",
            difficulty_level="MEDIUM",
            required_skills=json.dumps(["Python", "JavaScript"]),
            pk_opportunities=json.dumps(["Software houses in Karachi"]),
            top_pk_universities=json.dumps(["FAST-NUCES", "LUMS"]),
            risks=json.dumps(["Competitive admissions"]),
        )
        db_session.add(career)
        db_session.commit()
        db_session.refresh(career)

        assert career.id is not None
        assert career.slug == "software-engineering"
        assert json.loads(career.required_skills) == ["Python", "JavaScript"]

    def test_student_profile_relationship(self, db_session):
        student = Student(
            name="Fatima",
            email="fatima@example.com",
            password_hash="hashed",
        )
        db_session.add(student)
        db_session.flush()

        profile = StudentProfile(student_id=student.id)
        db_session.add(profile)
        db_session.commit()

        db_session.refresh(student)
        assert student.profile is not None
        assert student.profile.student_id == student.id

    def test_roadmap_milestone_relationship(self, db_session):
        student = Student(
            name="Ahmed", email="ahmed@example.com", password_hash="h"
        )
        db_session.add(student)
        db_session.flush()

        roadmap = Roadmap(student_id=student.id, current_stage="HIGH_SCHOOL")
        db_session.add(roadmap)
        db_session.flush()

        ms = Milestone(
            roadmap_id=roadmap.id,
            title="Learn Python",
            stage="SKILL_BUILDING",
            order_index=0,
        )
        db_session.add(ms)
        db_session.commit()

        db_session.refresh(roadmap)
        assert len(roadmap.milestones) == 1
        assert roadmap.milestones[0].title == "Learn Python"

    def test_create_opportunity(self, db_session):
        opp = Opportunity(
            type="internship",
            title="Python Intern",
            organization="Systems Ltd",
            location="Lahore",
            is_active=True,
        )
        db_session.add(opp)
        db_session.commit()
        assert opp.id is not None

    def test_create_sports_opportunity(self, db_session):
        sport = SportsOpportunity(
            sport="Cricket",
            type="tournament",
            title="Inter-University Cricket Cup",
            organization="HEC",
            is_active=True,
        )
        db_session.add(sport)
        db_session.commit()
        assert sport.id is not None

    def test_create_alumni(self, db_session):
        alum = Alumni(
            name="Sara Ahmed",
            university="LUMS",
            field="Computer Science",
            role="Software Engineer",
            company="Careem",
            is_verified=True,
        )
        db_session.add(alum)
        db_session.commit()
        assert alum.id is not None


# =========================================================================
# 5. REPOSITORY OPERATIONS
# =========================================================================


class TestRepositories:
    def test_student_repo_create_with_profile(self, db_session):
        repo = StudentRepository(db_session)
        student = repo.create_with_profile(
            name="Bilal",
            email="bilal@example.com",
            password_hash="hashed",
            education_stage="UNIVERSITY",
        )
        assert student.id is not None
        profile = repo.get_profile(student.id)
        assert profile is not None
        assert profile.student_id == student.id

    def test_student_repo_get_by_email(self, db_session):
        repo = StudentRepository(db_session)
        repo.create_with_profile(
            name="Zara", email="zara@example.com", password_hash="h"
        )
        found = repo.get_by_email("zara@example.com")
        assert found is not None
        assert found.name == "Zara"

    def test_student_repo_get_by_email_not_found(self, db_session):
        repo = StudentRepository(db_session)
        assert repo.get_by_email("nobody@example.com") is None

    def test_student_repo_update_profile(self, db_session):
        repo = StudentRepository(db_session)
        student = repo.create_with_profile(
            name="Hassan", email="hassan@example.com", password_hash="h"
        )
        profile = repo.update_profile(student.id, job_readiness_score=0.75)
        assert profile.job_readiness_score == 0.75

    def test_career_repo_create_and_get_by_slug(self, db_session):
        repo = CareerRepository(db_session)
        repo.create(
            slug="medicine",
            name="Medicine (MBBS)",
            field="Healthcare",
            demand_level="HIGH",
        )
        career = repo.get_by_slug("medicine")
        assert career is not None
        assert career.name == "Medicine (MBBS)"

    def test_career_repo_get_all(self, db_session):
        repo = CareerRepository(db_session)
        repo.create(slug="cs", name="CS", field="Tech", demand_level="HIGH")
        repo.create(slug="med", name="Med", field="Health", demand_level="HIGH")
        careers = repo.get_all_careers()
        assert len(careers) == 2

    def test_career_repo_to_dict(self, db_session):
        repo = CareerRepository(db_session)
        career = repo.create(
            slug="data-science",
            name="Data Science",
            field="Technology",
            demand_level="HIGH",
            required_skills=json.dumps(["Python", "Statistics"]),
            pk_opportunities=json.dumps(["Banking analytics"]),
            top_pk_universities=json.dumps(["LUMS", "NUST"]),
            risks=json.dumps(["Maths-heavy"]),
        )
        d = repo.to_dict(career)
        assert d["slug"] == "data-science"
        assert d["required_skills"] == ["Python", "Statistics"]
        assert d["top_pk_universities"] == ["LUMS", "NUST"]

    def test_career_repo_count(self, db_session):
        repo = CareerRepository(db_session)
        assert repo.count() == 0
        repo.create(slug="x", name="X", field="Y")
        assert repo.count() == 1


# =========================================================================
# 6. PYDANTIC VALIDATION
# =========================================================================


class TestPydanticSchemas:
    def test_health_response(self):
        h = HealthResponse(status="ok")
        assert h.model_dump() == {"status": "ok"}

    def test_education_stage_enum(self):
        assert EducationStage.HIGH_SCHOOL.value == "HIGH_SCHOOL"
        assert EducationStage.FIRST_JOB.value == "FIRST_JOB"
        assert len(EducationStage) == 10

    def test_milestone_status_enum(self):
        assert MilestoneStatus.DONE.value == "done"
        assert MilestoneStatus.PENDING.value == "pending"

    def test_next_best_action(self):
        nba = NextBestAction(
            title="Learn Python",
            description="Start with basics",
            steps=["Install Python", "Do tutorial"],
            estimated_time="3-4 hours",
            why_this_matters="Foundation for CS",
            stage="SKILL_BUILDING",
        )
        assert nba.title == "Learn Python"
        assert len(nba.steps) == 2

    def test_next_best_action_missing_field_raises(self):
        with pytest.raises(ValidationError):
            NextBestAction(
                title="X",
                description="Y",
                # missing steps
                estimated_time="1h",
                why_this_matters="Z",
                stage="S",
            )

    def test_onboarding_payload(self):
        payload = OnboardingPayload(
            education_stage=EducationStage.HIGH_SCHOOL,
            interests=["technology"],
            career_interests=["software_engineering"],
            motivation_tags=["genuine_interest"],
            skills=[Skill(name="Python", level="beginner")],
            city="Karachi",
        )
        assert payload.city == "Karachi"
        assert len(payload.skills) == 1

    def test_career_list_item(self):
        item = CareerListItem(
            slug="cs", name="CS", field="Tech", demand_level="HIGH"
        )
        assert item.slug == "cs"

    def test_career_detail(self):
        detail = CareerDetail(
            slug="cs",
            name="CS",
            field="Tech",
            required_skills=["Python"],
            pk_opportunities=["Software houses"],
            top_pk_universities=["FAST"],
            risks=["Competitive"],
        )
        assert detail.demand_level is None  # optional
        assert detail.required_skills == ["Python"]
