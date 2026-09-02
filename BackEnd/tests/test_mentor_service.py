"""
Step 6 — Grounded AI Career & Sports Mentor Tests.

Covers:
1. Mentor service core reasoning & ONE Next Best Action contract
2. Anti-hallucination: verified factual grounding vs general advice, null preservation
3. PKE tool retrieval: invoked when needed, skipped for pure emotional/conversational chat
4. Visibility guarantees: candidate/rejected staging data never in mentor context
5. Provenance integrity: citations sourced from real stored records, invented URLs stripped
6. Geographic scope: Karachi, Lahore, Islamabad, NATIONWIDE, ONLINE
7. Resilient fallback mode on AI unavailability without crashing
8. Integration with /coach/chat, /career/analyze, /career/trial-plan
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from models.career import Career
from models.learning import LearningResource
from models.opportunity import Opportunity
from models.student import Student, StudentProfile
from models.university import Program, University
from schemas.shared import CoachResponse, SourceCitation
from services.ai_service import AIService, AIUnavailableError, AIValidationError
from services.journey_state import DEMO_STUDENT_ID
from services.mentor_service import (
    _detect_city,
    _needs_pke_retrieval,
    fallback_mentor_response,
    mentor_chat,
)
import Mcp.db_access as db_access


# ---------------------------------------------------------------------------
# Test Fixtures & Helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def pke_db(db_session):
    """Point MCP db_access to the in-memory test database."""
    original = db_access._session_factory

    def _factory():
        return db_session

    db_access.set_session_factory(_factory)
    yield db_session
    db_access.set_session_factory(original)


def _create_test_student(db: Session, goal: str = "software-engineering", city: str = "Islamabad") -> Student:
    student = Student(
        id=DEMO_STUDENT_ID,
        name="Ahmad Khan",
        email="ahmad@test.pk",
        password_hash="hashed_pw",
        education_stage="UNIVERSITY",
        career_goal=goal,
        sports_interest="Cricket",
        motivation_tags=json.dumps(["impact", "growth"]),
    )
    db.add(student)

    profile = StudentProfile(
        student_id=DEMO_STUDENT_ID,
        interests=json.dumps(["Coding", "Robotics"]),
        skills=json.dumps([{"name": "Python", "level": "intermediate"}]),
    )
    db.add(profile)
    db.commit()
    db.refresh(student)
    return student


def _create_verified_uni_and_opp(db: Session):
    """Seed verified university and opportunity records."""
    uni = University(
        name="FAST-NUCES Islamabad",
        short_name="FAST",
        slug="fast-isb",
        city="Islamabad",
        province="Islamabad",
        type="PRIVATE",
        hec_recognized=True,
        website_url="https://isb.nu.edu.pk",
        admissions_url="https://isb.nu.edu.pk/admissions",
        source_id=1,
        verification_status="VERIFIED",
    )
    db.add(uni)
    db.flush()

    prog = Program(
        university_id=uni.id,
        name="BS Computer Science",
        degree_type="BS",
        field="Computer Science",
        duration_years=4.0,
        annual_fee_pkr=None,  # Null preserved (never inferred)
        admission_link="https://isb.nu.edu.pk/admissions",
        source_id=1,
        verification_status="VERIFIED",
    )
    db.add(prog)

    opp = Opportunity(
        title="National Need-Based Scholarship",
        organization="HEC Pakistan",
        type="scholarship",
        location="Islamabad",
        description="Undergraduate need-based financial aid.",
        source_url="https://hec.gov.pk/scholarships",
        source_id=1,
        verification_status="VERIFIED",
        deadline=None,  # Null preserved
    )
    db.add(opp)
    db.commit()


def mock_ai_mentor(response_obj: CoachResponse):
    ai = MagicMock()
    ai.call_structured = MagicMock(return_value=response_obj)
    return ai


# ---------------------------------------------------------------------------
# 1. ONE Next Best Action & Core Response Tests
# ---------------------------------------------------------------------------


class TestMentorNextBestAction:
    def test_mentor_returns_one_clear_next_best_action(self, pke_db):
        _create_test_student(pke_db)

        ai_response = CoachResponse(
            message="Computer science in Islamabad offers strong foundational prospects.",
            next_best_action="Compare the BS Computer Science curriculum at FAST-NUCES with Quaid-i-Azam University.",
            next_best_action_type="COMPARE",
            reasoning_summary="Student is interested in software and based in Islamabad.",
            quick_actions=["View FAST admissions", "Check fee structures", "Explore internships"],
        )

        with patch("services.mentor_service.get_ai_service", return_value=mock_ai_mentor(ai_response)):
            result = mentor_chat(pke_db, "What should I do to study CS in Islamabad?")

        assert isinstance(result.next_best_action, str)
        assert len(result.next_best_action) > 10
        assert result.next_best_action_type == "COMPARE"
        assert len(result.quick_actions) <= 3

    def test_mentor_enforces_nba_when_llm_omits_it(self, pke_db):
        _create_test_student(pke_db)

        ai_response = CoachResponse(
            message="Great question about starting your career.",
            next_best_action="",  # LLM omitted NBA
            quick_actions=["Build a mini Python project", "Look at job boards"],
        )

        with patch("services.mentor_service.get_ai_service", return_value=mock_ai_mentor(ai_response)):
            result = mentor_chat(pke_db, "I want to get better at coding.")

        # Backend derives NBA from quick_actions[0]
        assert result.next_best_action == "Build a mini Python project"


# ---------------------------------------------------------------------------
# 2. PKE Retrieval & Grounding Tests
# ---------------------------------------------------------------------------


class TestPKEGroundedRetrieval:
    def test_retrieval_triggered_for_factual_university_query(self, pke_db):
        _create_test_student(pke_db)
        _create_verified_uni_and_opp(pke_db)

        captured_system_prompt = {}

        def capture_call(prompt, system_prompt=None, **kwargs):
            captured_system_prompt["text"] = system_prompt or ""
            return CoachResponse(
                message="FAST-NUCES in Islamabad offers a verified BS Computer Science program.",
                next_best_action="Review admission requirements for FAST-NUCES Islamabad.",
                next_best_action_type="EXPLORE",
                quick_actions=["Visit admissions portal"],
            )

        ai = MagicMock()
        ai.call_structured = MagicMock(side_effect=capture_call)

        with patch("services.mentor_service.get_ai_service", return_value=ai):
            result = mentor_chat(pke_db, "Which universities in Islamabad offer computer science programs?")

        assert "FAST-NUCES Islamabad" in captured_system_prompt["text"]
        assert len(result.sources) > 0
        assert any("FAST" in s.title or "isb.nu.edu.pk" in (s.source_url or "") for s in result.sources)

    def test_retrieval_skipped_for_purely_emotional_question(self, pke_db):
        _create_test_student(pke_db)

        captured_system_prompt = {}

        def capture_call(prompt, system_prompt=None, **kwargs):
            captured_system_prompt["text"] = system_prompt or ""
            return CoachResponse(
                message="It is completely natural to feel confused when there are many choices.",
                next_best_action="Reflect on which subjects give you energy versus drain you.",
                next_best_action_type="REFLECT",
                quick_actions=["Take a self-assessment"],
            )

        ai = MagicMock()
        ai.call_structured = MagicMock(side_effect=capture_call)

        with patch("services.mentor_service.get_ai_service", return_value=ai):
            result = mentor_chat(pke_db, "I'm scared I'm not good enough and I feel lost.")

        # Verified PKE data section should not be populated with university listings
        assert "verified_pke_data" not in captured_system_prompt["text"]
        assert result.next_best_action_type == "REFLECT"


# ---------------------------------------------------------------------------
# 3. Anti-Hallucination & Provenance Protection Tests
# ---------------------------------------------------------------------------


class TestAntiHallucinationAndProvenance:
    def test_fabricated_urls_are_stripped(self, pke_db):
        _create_test_student(pke_db)

        ai_response = CoachResponse(
            message="Here is some advice.",
            next_best_action="Check the verified scholarship portal.",
            sources=[
                SourceCitation(title="Invented Source", source_url="https://hallucinated-portal.fake.pk"),
            ],
        )

        with patch("services.mentor_service.get_ai_service", return_value=mock_ai_mentor(ai_response)):
            result = mentor_chat(pke_db, "Tell me general tips.")

        # Hallucinated URL not in known PKE citations is stripped
        assert not any("hallucinated-portal.fake.pk" in (s.source_url or "") for s in result.sources)

    def test_needs_pke_retrieval_intent_detection(self):
        assert _needs_pke_retrieval("What scholarships are available in Karachi?") is True
        assert _needs_pke_retrieval("Are there any cricket trials in Lahore?") is True
        assert _needs_pke_retrieval("Tell me about university admissions in Islamabad") is True
        assert _needs_pke_retrieval("I am feeling overwhelmed and confused about life") is False
        assert _needs_pke_retrieval("Thanks for your help!") is False

    def test_city_detection_helper(self):
        assert _detect_city("Looking for CS in Lahore") == "lahore"
        assert _detect_city("Universities in Karachi") == "karachi"
        assert _detect_city("Opportunities in Islamabad") == "islamabad"
        assert _detect_city("General advice", default="karachi") == "karachi"

    def test_staging_records_never_appear_in_mentor_context(self, pke_db):
        """Verify that CANDIDATE staging records are never retrieved for the mentor."""
        _create_test_student(pke_db)
        from knowledge_engine.staging import PKEStagingRecord

        staging = PKEStagingRecord(
            domain="scholarships",
            extracted_json=json.dumps({"title": "Unverified Secret Scholarship", "organization": "Unknown"}),
            source_url="https://secret-unverified.pk",
            verification_status="CANDIDATE",
        )
        pke_db.add(staging)
        pke_db.commit()

        captured_system_prompt = {}

        def capture_call(prompt, system_prompt=None, **kwargs):
            captured_system_prompt["text"] = system_prompt or ""
            return CoachResponse(
                message="No verified scholarships found for your criteria.",
                next_best_action="Explore verified learning resources in DigiSkills.",
                next_best_action_type="EXPLORE",
                quick_actions=["Check DigiSkills"],
            )

        ai = MagicMock()
        ai.call_structured = MagicMock(side_effect=capture_call)

        with patch("services.mentor_service.get_ai_service", return_value=ai):
            result = mentor_chat(pke_db, "Are there any secret scholarships?")

        assert "Unverified Secret Scholarship" not in captured_system_prompt["text"]
        assert not any("secret-unverified.pk" in (s.source_url or "") for s in result.sources)

    def test_sports_trial_query_retrieves_verified_sports_opportunities(self, pke_db):
        """Verify sports queries retrieve verified sports opportunities."""
        _create_test_student(pke_db)

        sports_opp = Opportunity(
            title="PCB U-19 Regional Cricket Trials",
            organization="Pakistan Cricket Board",
            type="sports_opportunity",
            location="Lahore",
            description="Official open trials for Lahore region.",
            source_url="https://pcb.com.pk/trials",
            source_id=1,
            verification_status="VERIFIED",
            deadline=None,
        )
        pke_db.add(sports_opp)
        pke_db.commit()

        captured_system_prompt = {}

        def capture_call(prompt, system_prompt=None, **kwargs):
            captured_system_prompt["text"] = system_prompt or ""
            return CoachResponse(
                message="PCB has announced U-19 regional cricket trials in Lahore.",
                next_best_action="Prepare your registration documents for PCB U-19 trials in Lahore.",
                next_best_action_type="REGISTER",
                quick_actions=["View trial requirements"],
            )

        ai = MagicMock()
        ai.call_structured = MagicMock(side_effect=capture_call)

        with patch("services.mentor_service.get_ai_service", return_value=ai):
            result = mentor_chat(pke_db, "Are there any cricket trials in Lahore?")

        assert "PCB U-19 Regional Cricket Trials" in captured_system_prompt["text"]
        assert result.next_best_action_type == "REGISTER"
        assert any("pcb.com.pk" in (s.source_url or "") for s in result.sources)


# ---------------------------------------------------------------------------
# 4. Resilient Fallback Tests
# ---------------------------------------------------------------------------


class TestResilientFallbacks:
    def test_fallback_mentor_response_structure(self, pke_db):
        student = _create_test_student(pke_db)
        fallback = fallback_mentor_response("What scholarships exist?", student)

        assert isinstance(fallback, CoachResponse)
        assert len(fallback.message) > 20
        assert "scholarship" in fallback.next_best_action.lower()
        assert fallback.confidence == "grounded_fallback"

    def test_mentor_chat_safe_fallback_mode_on_ai_unavailable(self, pke_db):
        _create_test_student(pke_db)

        ai = MagicMock()
        ai.call_structured = MagicMock(side_effect=AIUnavailableError("DashScope unavailable"))

        with patch("services.mentor_service.get_ai_service", return_value=ai):
            result = mentor_chat(pke_db, "Tell me about software engineering", safe_fallback=True)

        assert isinstance(result, CoachResponse)
        assert len(result.next_best_action) > 5
        assert result.confidence == "grounded_fallback"


# ---------------------------------------------------------------------------
# 5. Integration with Router Endpoints
# ---------------------------------------------------------------------------


class TestEndpointsIntegration:
    def test_coach_chat_endpoint_returns_next_best_action(self, client, pke_db):
        _create_test_student(pke_db)

        ai = MagicMock()
        ai.call_structured = MagicMock(return_value=CoachResponse(
            message="Here is your personalized roadmap guidance.",
            next_best_action="Complete the beginner Python milestone in your roadmap.",
            next_best_action_type="LEARN",
            quick_actions=["View milestone", "Explore projects"],
        ))

        with patch("services.coach_service.get_ai_service", return_value=ai):
            resp = client.post("/api/v1/coach/chat", json={
                "message": "What is my next priority?",
                "conversation_history": [],
            })

        assert resp.status_code == 200
        data = resp.json()
        assert "next_best_action" in data
        assert data["next_best_action"] == "Complete the beginner Python milestone in your roadmap."

    def test_career_analyze_endpoint(self, client, pke_db):
        _create_test_student(pke_db)
        career = Career(
            name="Software Engineer",
            slug="software-engineer",
            field="Technology",
            demand_level="HIGH",
            competition_level="MEDIUM",
            difficulty_level="MEDIUM",
            required_skills=json.dumps(["Python", "SQL"]),
            pk_opportunities=json.dumps(["Tech companies in Karachi, Lahore, Islamabad"]),
            risks=json.dumps(["Fast evolving tech stack"]),
        )
        pke_db.add(career)
        pke_db.commit()

        from schemas.shared import CareerReality, CareerRealityResponse, CareerVerdict
        mock_reality = CareerRealityResponse(
            reality=CareerReality(
                career_name="Software Engineer",
                demand_level="HIGH",
                competition_level="MEDIUM",
                difficulty_level="MEDIUM",
                required_skills=["Python", "SQL"],
                pk_opportunities=["Tech companies in Karachi, Lahore, Islamabad"],
                risks=["Fast evolving tech stack"],
                rewards=["High career mobility"],
                data_source="Database",
            ),
            verdict=CareerVerdict(
                verdict="GOOD_FIT",
                headline="Strong alignment with your coding interests.",
                reasoning="Your background in Python matches required skills.",
                student_strengths_match=["Python"],
                gaps_to_address=["System Design"],
            ),
        )

        ai = MagicMock()
        ai.call_structured = MagicMock(return_value=mock_reality)

        with patch("services.career_service.get_ai_service", return_value=ai):
            resp = client.post("/api/v1/career/analyze", json={"career_slug": "software-engineer"})

        assert resp.status_code == 200
        data = resp.json()
        assert data["verdict"]["verdict"] == "GOOD_FIT"

    def test_career_trial_plan_endpoint(self, client, pke_db):
        _create_test_student(pke_db)
        career = Career(
            name="Data Scientist",
            slug="data-scientist",
            field="Data",
            demand_level="HIGH",
        )
        pke_db.add(career)
        pke_db.commit()

        from schemas.shared import CareerTrialPlan, TrialDay
        mock_plan = CareerTrialPlan(
            career_slug="data-scientist",
            duration_days=7,
            days=[
                TrialDay(day_range="Day 1-2", title="Python Basics", tasks=["Task 1"]),
                TrialDay(day_range="Day 3-7", title="Data Analysis", tasks=["Task 2"]),
            ],
            reflection_prompt="Did you enjoy data cleaning?",
        )

        ai = MagicMock()
        ai.call_structured = MagicMock(return_value=mock_plan)

        with patch("services.career_service.get_ai_service", return_value=ai):
            resp = client.post("/api/v1/career/trial-plan", json={"career_slug": "data-scientist"})

        assert resp.status_code == 200
        data = resp.json()
        assert data["career_slug"] == "data-scientist"
        assert len(data["days"]) == 2
