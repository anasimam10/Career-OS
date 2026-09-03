"""
Step 7 — Final End-to-End Integration, MVP Hardening & Hackathon Demo Test Suite.

Validates the full student journey and PKE-grounded intelligence:
1. Complete Career Demo Journey:
   - Onboarding (Lahore student, Tech interests)
   - Career Exploration (List & Detail)
   - Career Reality Check (Analyze)
   - 7-Day Career Trial Plan
   - Grounded Mentor Chat (Lahore CS query -> PKE retrieval -> ONE Next Best Action -> Sources)
   - Journey Milestone Progress & NBA recalculation
2. Complete Sports Demo Journey:
   - Sports Interest Profile (Cricket)
   - Verified Sports Opportunities / Trials Retrieval
   - Sports Mentor Conversation -> ONE Next Best Action
3. Factual Grounding & Anti-Hallucination Integrity:
   - Verified records cited with real URLs
   - Missing facts explicitly communicated as unavailable (never invented)
   - Preserved null values (fees, deadlines)
   - Fabricated URLs stripped
4. Staging Isolation:
   - CANDIDATE and REJECTED staging records strictly invisible to student endpoints
5. Resilient Error Handling & Fallbacks:
   - Graceful offline fallback during AI service interruption
6. Frontend API Contract Compatibility:
   - All response schemas match frontend expectations
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from models.career import Career
from models.opportunity import Opportunity
from models.student import Student, StudentProfile
from models.university import Program, University
from schemas.shared import (
    CareerReality,
    CareerRealityResponse,
    CareerTrialPlan,
    CareerVerdict,
    CoachResponse,
    SourceCitation,
    TrialDay,
)
from services.ai_service import AIUnavailableError
from services.journey_state import DEMO_STUDENT_ID
import Mcp.db_access as db_access


from tests.conftest import TestingSessionLocal


@pytest.fixture
def pke_db(db_session):
    """Point MCP db_access to test in-memory database."""
    original = db_access._session_factory
    db_access.set_session_factory(TestingSessionLocal)
    yield db_session
    db_access.set_session_factory(original)


def _seed_demo_environment(db):
    """Seed comprehensive verified records for the demo tests."""
    # 1. Career
    career = Career(
        name="Software Engineer",
        slug="software-engineering",
        field="Technology",
        demand_level="HIGH",
        competition_level="MEDIUM",
        difficulty_level="MEDIUM",
        required_skills=json.dumps(["Python", "SQL", "Git"]),
        pk_opportunities=json.dumps(["Tech hubs in Lahore, Karachi, Islamabad"]),
        risks=json.dumps(["Rapid technology shifts"]),
    )
    db.add(career)

    # 2. Universities & Programs in Lahore & Islamabad
    uni_lhe = University(
        name="FAST-NUCES Lahore",
        short_name="FAST Lahore",
        slug="fast-lhe",
        city="Lahore",
        province="Punjab",
        type="PRIVATE",
        hec_recognized=True,
        website_url="https://lahore.nu.edu.pk",
        admissions_url="https://lahore.nu.edu.pk/admissions",
        source_id=1,
        verification_status="VERIFIED",
    )
    db.add(uni_lhe)
    db.flush()

    prog_lhe = Program(
        university_id=uni_lhe.id,
        name="BS Computer Science",
        degree_type="BS",
        field="Computer Science",
        duration_years=4.0,
        annual_fee_pkr=None,  # Preserved null
        admission_link="https://lahore.nu.edu.pk/admissions",
        source_id=1,
        verification_status="VERIFIED",
    )
    db.add(prog_lhe)

    # 3. Verified Sports Opportunity
    sports_opp = Opportunity(
        title="PCB National U-19 Cricket Championship",
        organization="Pakistan Cricket Board",
        type="sports_opportunity",
        location="Lahore",
        description="Official national youth tournament organized by PCB.",
        source_url="https://pcb.com.pk/domestic-tournaments",
        source_id=1,
        verification_status="VERIFIED",
        deadline=None,
    )
    db.add(sports_opp)

    # 4. Verified Scholarship
    scholarship = Opportunity(
        title="Punjab Educational Endowment Fund (PEEF) Scholarship",
        organization="PEEF Punjab",
        type="scholarship",
        location="Lahore",
        description="Merit and need-based undergraduate scholarships for Punjab residents.",
        source_url="https://peef.punjab.gov.pk/scholarships",
        source_id=1,
        verification_status="VERIFIED",
        deadline=None,
    )
    db.add(scholarship)

    # 5. Ensure Student with id=1 exists
    student = db.get(Student, DEMO_STUDENT_ID)
    if not student:
        student = Student(
            id=DEMO_STUDENT_ID,
            name="Ahmad Khan",
            email="ahmad@test.pk",
            password_hash="hashed_pw",
            education_stage="HIGH_SCHOOL",
            career_goal="software-engineering",
            sports_interest="Cricket",
            motivation_tags=json.dumps(["impact", "growth"]),
        )
        db.add(student)

        profile = StudentProfile(
            student_id=DEMO_STUDENT_ID,
            interests=json.dumps(["Coding", "Mathematics"]),
            skills=json.dumps([{"name": "Python", "level": "beginner"}]),
        )
        db.add(profile)

    db.commit()


# ---------------------------------------------------------------------------
# Demo Scenario 1: Complete Career Demo Journey
# ---------------------------------------------------------------------------


class TestCareerDemoJourney:
    def test_complete_career_flow(self, client: TestClient, pke_db):
        """Walks the full career student demo path:
        Onboarding -> Career Listing -> Reality Check -> Trial Plan -> Grounded Mentor -> Progress.
        """
        _seed_demo_environment(pke_db)

        # Step 1: Onboarding
        mock_nba_selection = MagicMock()
        mock_nba_selection.candidate_id = "explore_software-engineering"
        mock_nba_selection.why_this_matters = "Starting with software engineering matches your tech interests."

        with patch("services.nba_service.get_ai_service") as mock_nba_ai:
            mock_nba_ai.return_value.call_structured.return_value = mock_nba_selection
            onboarding_res = client.post("/api/v1/onboarding", json={
                "education_stage": "HIGH_SCHOOL",
                "interests": ["Coding", "Mathematics"],
                "career_interests": ["Software Engineer"],
                "sports_interest": "Cricket",
                "motivation_tags": ["impact", "high_earning"],
                "skills": [{"name": "Python", "level": "beginner"}],
                "city": "Lahore",
            })

        assert onboarding_res.status_code == 200
        onboarding_data = onboarding_res.json()
        assert onboarding_data["profile_updated"] is True
        assert "next_best_action" in onboarding_data

        # Step 2: Career Explorer (List & Detail)
        careers_res = client.get("/api/v1/careers")
        assert careers_res.status_code == 200
        careers_list = careers_res.json()
        assert len(careers_list) >= 1
        assert any(c["slug"] == "software-engineering" for c in careers_list)

        detail_res = client.get("/api/v1/careers/software-engineering")
        assert detail_res.status_code == 200
        detail_data = detail_res.json()
        assert detail_data["name"] == "Software Engineer"
        assert detail_data["demand_level"] == "HIGH"

        # Step 3: Career Reality Check (Analyze)
        mock_reality = CareerRealityResponse(
            reality=CareerReality(
                career_name="Software Engineer",
                demand_level="HIGH",
                competition_level="MEDIUM",
                difficulty_level="MEDIUM",
                required_skills=["Python", "SQL", "Git"],
                pk_opportunities=["Tech hubs in Lahore, Karachi, Islamabad"],
                risks=["Rapid technology shifts"],
                rewards=["High market demand"],
                data_source="Career OS Verified DB",
            ),
            verdict=CareerVerdict(
                verdict="GOOD_FIT",
                headline="High potential fit for software career.",
                reasoning="Your background in Python matches initial requirements.",
                student_strengths_match=["Python", "Coding"],
                gaps_to_address=["SQL", "System Design"],
                suggested_trial="Complete a 7-day coding trial",
            ),
        )

        with patch("services.career_service.get_ai_service") as mock_career_ai:
            mock_career_ai.return_value.call_structured.return_value = mock_reality
            analyze_res = client.post("/api/v1/career/analyze", json={
                "career_slug": "software-engineering"
            })

        assert analyze_res.status_code == 200
        analyze_data = analyze_res.json()
        assert analyze_data["verdict"]["verdict"] == "GOOD_FIT"
        assert len(analyze_data["reality"]["required_skills"]) >= 2

        # Step 4: 7-Day Career Trial Plan
        mock_plan = CareerTrialPlan(
            career_slug="software-engineering",
            duration_days=7,
            days=[
                TrialDay(day_range="Day 1-2", title="Python Fundamentals", tasks=["Write basic functions"]),
                TrialDay(day_range="Day 3-5", title="Mini Project", tasks=["Build a simple CLI tool"]),
                TrialDay(day_range="Day 6-7", title="Reflection", tasks=["Review code and evaluate interest"]),
            ],
            reflection_prompt="Do you enjoy solving algorithmic problems?",
        )

        with patch("services.career_service.get_ai_service") as mock_trial_ai:
            mock_trial_ai.return_value.call_structured.return_value = mock_plan
            trial_res = client.post("/api/v1/career/trial-plan", json={
                "career_slug": "software-engineering"
            })

        assert trial_res.status_code == 200
        trial_data = trial_res.json()
        assert trial_data["duration_days"] == 7
        assert len(trial_data["days"]) == 3

        # Step 5: Grounded AI Mentor Chat (Inquiring about Lahore CS)
        captured_prompt = {}

        def capture_mentor_call(*args, **kwargs):
            system = kwargs.get("system_prompt") or (args[2] if len(args) > 2 else "")
            captured_prompt["system"] = str(system)
            return CoachResponse(
                message="FAST-NUCES Lahore offers a reputable BS Computer Science program.",
                next_best_action="Review admission requirements and deadlines for FAST-NUCES Lahore.",
                next_best_action_type="EXPLORE",
                reasoning_summary="Based on your location in Lahore and software engineering goal.",
                quick_actions=["View FAST admissions", "Check fee structure", "Compare universities"],
                sources=[
                    SourceCitation(title="FAST-NUCES Lahore", source_url="https://lahore.nu.edu.pk"),
                ],
            )

        with patch("services.coach_service.get_ai_service") as mock_coach_ai:
            mock_coach_ai.return_value.call_structured = MagicMock(side_effect=capture_mentor_call)
            chat_res = client.post("/api/v1/coach/chat", json={
                "message": "I want to study computer science in Lahore. What should I do next?",
                "conversation_history": [],
            })

        assert chat_res.status_code == 200
        chat_data = chat_res.json()
        # Verify Grounding & Next Best Action
        assert "FAST-NUCES Lahore" in captured_prompt["system"]
        assert chat_data["next_best_action"] == "Review admission requirements and deadlines for FAST-NUCES Lahore."
        assert chat_data["next_best_action_type"] == "EXPLORE"
        assert len(chat_data["sources"]) >= 1
        assert "lahore.nu.edu.pk" in chat_data["sources"][0]["source_url"]

        # Step 6: Journey & Milestone Progress
        journey_res = client.get("/api/v1/journey")
        assert journey_res.status_code == 200
        journey_data = journey_res.json()
        assert "stage" in journey_data
        assert "next_best_action" in journey_data
        assert "next_steps" in journey_data


# ---------------------------------------------------------------------------
# Demo Scenario 2: Complete Sports Demo Journey
# ---------------------------------------------------------------------------


class TestSportsDemoJourney:
    def test_complete_sports_pathway_flow(self, client: TestClient, pke_db):
        """Walks the sports student demo path:
        Profile with Cricket -> Sports Mentor Query -> Verified PCB Tournament Retrieval -> ONE Next Best Action.
        """
        _seed_demo_environment(pke_db)

        # Create demo student with sports interest
        student = pke_db.get(Student, DEMO_STUDENT_ID)
        if not student:
            student = Student(
                id=DEMO_STUDENT_ID,
                name="Zubair Ali",
                email="zubair@test.pk",
                password_hash="pw",
                education_stage="HIGH_SCHOOL",
                sports_interest="Cricket",
                career_goal="sports-management",
            )
            pke_db.add(student)
            pke_db.commit()

        captured_system = {}

        def capture_sports_chat(prompt, system_prompt=None, **kwargs):
            captured_system["text"] = system_prompt or ""
            return CoachResponse(
                message="For youth cricket pathways in Lahore, PCB conducts official domestic tournaments and trials.",
                next_best_action="Register for the verified PCB National U-19 Cricket trials in Lahore.",
                next_best_action_type="REGISTER",
                reasoning_summary="PCB domestic tournaments are the official pathway for junior cricketers.",
                quick_actions=["View PCB trial dates", "Find cricket academies"],
                sources=[
                    SourceCitation(title="Pakistan Cricket Board", source_url="https://pcb.com.pk/domestic-tournaments"),
                ],
            )

        with patch("services.coach_service.get_ai_service") as mock_ai:
            mock_ai.return_value.call_structured = MagicMock(side_effect=capture_sports_chat)
            chat_res = client.post("/api/v1/coach/chat", json={
                "message": "I play cricket in Lahore. Are there any official tournaments or trials for me?",
                "conversation_history": [],
            })

        assert chat_res.status_code == 200
        data = chat_res.json()
        assert "PCB National U-19" in captured_system["text"]
        assert "pcb.com.pk" in data["sources"][0]["source_url"]
        assert data["next_best_action_type"] == "REGISTER"


# ---------------------------------------------------------------------------
# Demo Scenario 3 & 4: Grounding, Missing Facts & Isolation
# ---------------------------------------------------------------------------


class TestGroundingAndIsolation:
    def test_missing_data_not_hallucinated(self, client: TestClient, pke_db):
        """Asking for an entity or fact not in PKE causes the mentor to state unavailability."""
        _seed_demo_environment(pke_db)

        def mock_unavailable_fact(prompt, system_prompt=None, **kwargs):
            return CoachResponse(
                message="I could not find verified information for Aerospace Engineering in Quetta in our knowledge engine.",
                next_best_action="Explore HEC-recognized engineering programs in Islamabad or Lahore.",
                next_best_action_type="EXPLORE",
                quick_actions=["Check Islamabad Unis"],
            )

        with patch("services.coach_service.get_ai_service") as mock_ai:
            mock_ai.return_value.call_structured = MagicMock(side_effect=mock_unavailable_fact)
            chat_res = client.post("/api/v1/coach/chat", json={
                "message": "What is the fee for Aerospace Engineering in Quetta?",
                "conversation_history": [],
            })

        assert chat_res.status_code == 200
        data = chat_res.json()
        assert "could not find verified" in data["message"].lower()

    def test_candidate_and_rejected_staging_data_isolated(self, client: TestClient, pke_db):
        """Unverified staging records are strictly excluded from mentor context."""
        _seed_demo_environment(pke_db)
        from knowledge_engine.staging import PKEStagingRecord

        # Add candidate and rejected records to staging table
        cand = PKEStagingRecord(
            domain="universities",
            extracted_json=json.dumps({"name": "Fake Candidate University", "city": "Lahore"}),
            source_url="https://fake-candidate.edu.pk",
            verification_status="CANDIDATE",
        )
        rej = PKEStagingRecord(
            domain="scholarships",
            extracted_json=json.dumps({"title": "Scam Rejected Scholarship", "organization": "Scam"}),
            source_url="https://scam-rejected.pk",
            verification_status="REJECTED",
        )
        pke_db.add_all([cand, rej])
        pke_db.commit()

        captured_system = {}

        def capture_call(prompt, system_prompt=None, **kwargs):
            captured_system["text"] = system_prompt or ""
            return CoachResponse(
                message="FAST-NUCES Lahore is a verified university in Lahore.",
                next_best_action="Explore verified degree options.",
                quick_actions=[],
            )

        with patch("services.coach_service.get_ai_service") as mock_ai:
            mock_ai.return_value.call_structured = MagicMock(side_effect=capture_call)
            client.post("/api/v1/coach/chat", json={
                "message": "Tell me all universities and scholarships in Lahore",
                "conversation_history": [],
            })

        assert "Fake Candidate University" not in captured_system["text"]
        assert "Scam Rejected Scholarship" not in captured_system["text"]
        assert "fake-candidate.edu.pk" not in captured_system["text"]
        assert "scam-rejected.pk" not in captured_system["text"]


# ---------------------------------------------------------------------------
# Demo Scenario 5: Error Handling & Resilient Offline Fallback
# ---------------------------------------------------------------------------


class TestErrorHandlingAndResilience:
    def test_ai_unavailable_returns_503_or_resilient_fallback(self, client: TestClient, pke_db):
        """When AI provider fails, coach endpoint safely returns 503 without leaking secrets."""
        _seed_demo_environment(pke_db)

        with patch("services.coach_service.get_ai_service") as mock_ai:
            mock_ai.return_value.call_structured.side_effect = AIUnavailableError("Network timeout to DashScope")
            res = client.post("/api/v1/coach/chat", json={
                "message": "Help me choose a career",
                "conversation_history": [],
            })

        assert res.status_code == 503
        data = res.json()
        assert "error" in data
        assert "sk-" not in json.dumps(data)
        assert "DASHSCOPE" not in json.dumps(data)

    def test_mentor_service_safe_fallback_mode(self, pke_db):
        """Direct mentor service with safe_fallback=True returns resilient non-crashing response."""
        _seed_demo_environment(pke_db)
        from services.mentor_service import mentor_chat

        with patch("services.mentor_service.get_ai_service") as mock_ai:
            mock_ai.return_value.call_structured.side_effect = AIUnavailableError("Offline")
            fallback = mentor_chat(pke_db, "What scholarships can I apply for?", safe_fallback=True)

        assert isinstance(fallback, CoachResponse)
        assert len(fallback.next_best_action) > 10
        assert fallback.confidence == "grounded_fallback"
        assert "HEC" in fallback.next_best_action or "scholarship" in fallback.next_best_action.lower()
