"""
Phase 4 tests — Next Best Action + Journey vertical slice.

ALL Qwen calls are mocked (the Phase 2 ai_service is exercised with a mock
OpenAI client) — these tests never consume API quota and need no internet.

The mock AI responses prove the candidate-constrained design: Qwen only
returns a candidate_id + one sentence; every other field of the returned
NextBestAction must come from the backend's deterministic candidate.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
import openai
import pytest
from sqlalchemy.orm import Session

from models.career import Career
from models.roadmap import Milestone, Roadmap
from models.student import Student
from repositories.student_repo import StudentRepository
from services import candidate_service, nba_service
from services.ai_service import AIService
from services.journey_state import is_valid_transition


# ---------------------------------------------------------------------------
# Mock helpers (same pattern as tests/test_career.py)
# ---------------------------------------------------------------------------


def mock_ai_client(sequence):
    """Mock OpenAI client: strings become response content, exceptions raise."""
    client = MagicMock()

    def make_response(content):
        message = SimpleNamespace(content=content)
        choice = SimpleNamespace(message=message)
        return SimpleNamespace(choices=[choice])

    side_effects = [
        item if isinstance(item, BaseException) else make_response(item)
        for item in sequence
    ]
    client.chat.completions.create.side_effect = side_effects
    return client


def connection_error():
    request = httpx.Request("POST", "https://dashscope.example.com/v1/chat/completions")
    return openai.APIConnectionError(request=request)


def nba_selection(candidate_id: str, why: str = "AI rationale sentence.") -> str:
    """A Qwen NBASelection response — candidate_id + one sentence only."""
    return json.dumps(
        {"candidate_id": candidate_id, "why_this_matters": why}, ensure_ascii=False
    )


# Candidate ids for a freshly onboarded HIGH_SCHOOL student whose career is
# Software Engineering and whose profile already lists Python:
#   career_trial (0.90) > career_reality (0.85) > explore_careers (0.80)
#   > learn_skill_data_structures (0.78) > review_career_data > update_profile
FALLBACK_TITLE = "Complete the 7-Day Career Trial"  # highest-priority candidate
EXPLORE_TITLE = "Explore careers that match your interests"

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FULL_CAREER = dict(
    slug="software-engineering",
    name="Software Engineering",
    field="Technology",
    demand_level="HIGH",
    competition_level="HIGH",
    difficulty_level="MEDIUM",
    required_skills=json.dumps(["Python", "Data Structures", "Git"]),
    pk_opportunities=json.dumps(["Growing software house demand in major cities"]),
    top_pk_universities=json.dumps(["FAST-NUCES", "LUMS"]),
    risks=json.dumps(["Highly competitive admissions"]),
)

ONBOARDING_PAYLOAD = {
    "education_stage": "HIGH_SCHOOL",
    "interests": ["Technology", "Mathematics"],
    "career_interests": ["Software Engineering"],  # display name, as the wizard sends
    "sports_interest": "Badminton",
    "motivation_tags": ["I genuinely love this subject"],
    "skills": [{"name": "Python", "level": "beginner"}],
    "city": "Karachi",
}


@pytest.fixture()
def seeded_client(client, db_session):
    """Client with the Software Engineering career + the demo student (id=1)."""
    db_session.add(Career(**FULL_CAREER))
    db_session.commit()

    StudentRepository(db_session).create_with_profile(
        name="Demo Student",
        email="demo@test.local",
        password_hash="test",
        education_stage="HIGH_SCHOOL",
        career_goal="Software Engineering",
        motivation_tags=json.dumps(["I genuinely love this subject"]),
    )
    StudentRepository(db_session).update_profile(
        1,
        interests=json.dumps(["Technology", "Mathematics"]),
        skills=json.dumps([{"name": "Python", "level": "beginner"}]),
    )
    yield client


@pytest.fixture()
def capture_ai(monkeypatch):
    """Replace the NBA engine's AI service with a mock; expose it for assertions."""

    def _install(sequence):
        ai_client = mock_ai_client(sequence)
        service = AIService(client=ai_client)
        monkeypatch.setattr(nba_service, "get_ai_service", lambda: service)
        return ai_client

    yield _install


def _onboard(client, ai=None, payload=None) -> dict:
    """POST /onboarding with the standard payload (AI must be mocked first)."""
    resp = client.post("/api/v1/onboarding", json=payload or ONBOARDING_PAYLOAD)
    assert resp.status_code == 200, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# §6/§7 Journey state machine (pure unit tests)
# ---------------------------------------------------------------------------


class TestJourneyStateMachine:
    def test_architecture_transitions_are_valid(self):
        assert is_valid_transition("HIGH_SCHOOL", "CAREER_DISCOVERY")
        assert is_valid_transition("CAREER_DISCOVERY", "CAREER_DECISION")
        assert is_valid_transition("CAREER_DECISION", "UNIVERSITY")
        assert is_valid_transition("CAREER_DECISION", "SKILL_BUILDING")

    def test_invalid_transitions_are_rejected(self):
        assert not is_valid_transition("HIGH_SCHOOL", "SKILL_BUILDING")  # skip-ahead
        assert not is_valid_transition("CAREER_DISCOVERY", "HIGH_SCHOOL")  # backwards
        assert not is_valid_transition("FIRST_JOB", "HIGH_SCHOOL")  # terminal
        assert not is_valid_transition("HIGH_SCHOOL", "NOT_A_STAGE")  # unknown


# ---------------------------------------------------------------------------
# §4/§5 Onboarding
# ---------------------------------------------------------------------------


class TestOnboarding:
    def test_valid_onboarding_updates_demo_student(self, seeded_client, db_session, capture_ai):
        capture_ai([nba_selection("career_trial")])
        data = _onboard(seeded_client)

        assert data["profile_updated"] is True
        student = db_session.get(Student, 1)
        assert student.education_stage == "HIGH_SCHOOL"
        assert student.sports_interest == "Badminton"
        assert json.loads(student.motivation_tags) == ["I genuinely love this subject"]
        # display name resolved to the verified career slug
        assert student.career_goal == "software-engineering"

    def test_profile_fields_are_persisted(self, seeded_client, db_session, capture_ai):
        capture_ai([nba_selection("career_trial")])
        _onboard(seeded_client)

        profile = StudentRepository(db_session).get_profile(1)
        assert json.loads(profile.interests) == ["Technology", "Mathematics"]
        assert json.loads(profile.skills) == [{"name": "Python", "level": "beginner"}]

    def test_onboarding_initializes_stage_and_milestones(
        self, seeded_client, db_session, capture_ai
    ):
        capture_ai([nba_selection("career_trial")])
        payload = dict(ONBOARDING_PAYLOAD, education_stage="CAREER_DISCOVERY")
        _onboard(seeded_client, payload=payload)

        student = db_session.get(Student, 1)
        assert student.education_stage == "CAREER_DISCOVERY"
        milestones = db_session.query(Milestone).all()
        assert milestones, "onboarding must bootstrap journey milestones"
        assert all(m.stage == "CAREER_DISCOVERY" for m in milestones)
        roadmap = db_session.query(Roadmap).first()
        assert roadmap.career_id is not None  # linked to the resolved career

    def test_onboarding_generates_nba(self, seeded_client, capture_ai):
        capture_ai([nba_selection("career_trial")])
        nba = _onboard(seeded_client)["next_best_action"]
        assert set(nba.keys()) == {
            "title", "description", "steps", "estimated_time", "why_this_matters", "stage",
        }
        assert nba["title"] == FALLBACK_TITLE  # content from the deterministic candidate
        assert nba["why_this_matters"] == "AI rationale sentence."  # Qwen's one sentence

    def test_onboarding_creates_demo_student_when_missing(self, client, db_session, capture_ai):
        capture_ai([nba_selection("update_profile")])
        data = _onboard(client)
        assert data["profile_updated"] is True
        assert db_session.get(Student, 1) is not None

    def test_not_sure_yet_is_not_a_career_goal(self, seeded_client, db_session, capture_ai):
        capture_ai([nba_selection("update_profile")])
        payload = dict(ONBOARDING_PAYLOAD, career_interests=["Not sure yet"])
        _onboard(seeded_client, payload=payload)
        assert db_session.get(Student, 1).career_goal is None

    def test_invalid_onboarding_returns_422(self, seeded_client):
        bad = dict(ONBOARDING_PAYLOAD, education_stage="NOT_A_STAGE")
        assert seeded_client.post("/api/v1/onboarding", json=bad).status_code == 422
        bad = dict(ONBOARDING_PAYLOAD)  # missing required field
        bad.pop("motivation_tags")
        assert seeded_client.post("/api/v1/onboarding", json=bad).status_code == 422

    def test_ai_unavailable_still_returns_valid_nba(
        self, seeded_client, capture_ai
    ):
        """No 503 dead-end: the engine falls back to the highest-priority candidate."""
        ai = capture_ai([connection_error(), connection_error()])
        data = _onboard(seeded_client)
        assert data["profile_updated"] is True
        assert data["next_best_action"]["title"] == FALLBACK_TITLE
        assert ai.chat.completions.create.call_count == 2  # one retry, then fallback


# ---------------------------------------------------------------------------
# §8/§9 Candidate generator (deterministic, no AI)
# ---------------------------------------------------------------------------


class TestCandidateGenerator:
    def test_candidates_are_deterministic(self, seeded_client, db_session):
        student = db_session.get(Student, 1)
        first = candidate_service.generate_candidates(db_session, student)
        second = candidate_service.generate_candidates(db_session, student)
        assert [c.candidate_id for c in first] == [c.candidate_id for c in second]
        assert first == second

    def test_candidate_count_is_between_3_and_8(self, seeded_client, db_session):
        student = db_session.get(Student, 1)
        candidates = candidate_service.generate_candidates(db_session, student)
        assert 3 <= len(candidates) <= 8

    def test_candidate_ids_are_unique(self, seeded_client, db_session):
        student = db_session.get(Student, 1)
        candidates = candidate_service.generate_candidates(db_session, student)
        ids = [c.candidate_id for c in candidates]
        assert len(ids) == len(set(ids))

    def test_completed_actions_are_not_regenerated(self, seeded_client, db_session):
        student = db_session.get(Student, 1)
        before = candidate_service.generate_candidates(db_session, student)
        assert "explore_careers" in {c.candidate_id for c in before}

        # complete the EXPLORE_CAREERS milestone (title match retires the candidate)
        roadmap = Roadmap(student_id=1, career_id=1, current_stage="HIGH_SCHOOL")
        db_session.add(roadmap)
        db_session.flush()
        db_session.add(
            Milestone(
                roadmap_id=roadmap.id,
                title=EXPLORE_TITLE,
                description="done already",
                stage="HIGH_SCHOOL",
                status="done",
                order_index=0,
            )
        )
        db_session.commit()

        after = candidate_service.generate_candidates(db_session, student)
        assert "explore_careers" not in {c.candidate_id for c in after}

    def test_learn_skill_candidate_is_grounded_in_career_data(self, seeded_client, db_session):
        """Required skills come from the verified career record — nothing invented."""
        student = db_session.get(Student, 1)
        candidates = candidate_service.generate_candidates(db_session, student)
        learn = [c for c in candidates if c.action_type == "LEARN_SKILL"]
        assert learn, "Data Structures is missing from the profile — candidate expected"
        assert "Data Structures" in learn[0].title
        assert learn[0].candidate_id == "learn_skill_data_structures"


# ---------------------------------------------------------------------------
# §10-§13 Next Best Action engine
# ---------------------------------------------------------------------------


class TestNextBestAction:
    def test_valid_candidate_selection_is_accepted(self, seeded_client, capture_ai):
        ai = capture_ai([nba_selection("explore_careers")])
        nba = _onboard(seeded_client)["next_best_action"]
        assert nba["title"] == EXPLORE_TITLE  # explore_careers candidate content
        assert ai.chat.completions.create.call_count == 1

    def test_nba_content_is_deterministic_not_ai_written(self, seeded_client, capture_ai):
        """Qwen returned only candidate_id + one sentence — everything else is backend-generated."""
        capture_ai([nba_selection("career_reality", why="")])
        nba = _onboard(seeded_client)["next_best_action"]
        assert nba["title"] == "Complete a Career Reality Check"
        assert nba["steps"]  # steps from the template, never from the AI
        assert nba["why_this_matters"]  # empty AI sentence -> deterministic fallback
        assert nba["stage"] == "HIGH_SCHOOL"

    def test_invalid_candidate_id_retries_once_then_succeeds(self, seeded_client, capture_ai):
        ai = capture_ai([nba_selection("invented_id"), nba_selection("career_trial")])
        nba = _onboard(seeded_client)["next_best_action"]
        assert ai.chat.completions.create.call_count == 2
        assert nba["title"] == FALLBACK_TITLE

    def test_persistent_invalid_selection_uses_deterministic_fallback(
        self, seeded_client, capture_ai
    ):
        ai = capture_ai([nba_selection("fake1"), nba_selection("fake2")])
        nba = _onboard(seeded_client)["next_best_action"]
        assert ai.chat.completions.create.call_count == 2
        # highest-priority valid candidate — never an invalid AI action
        assert nba["title"] == FALLBACK_TITLE

    def test_nba_is_persisted_on_profile(self, seeded_client, db_session, capture_ai):
        capture_ai([nba_selection("career_trial")])
        nba = _onboard(seeded_client)["next_best_action"]
        profile = StudentRepository(db_session).get_profile(1)
        blob = json.loads(profile.next_best_action)
        assert blob["candidate_id"] == "career_trial"
        assert blob["action"]["title"] == nba["title"]
        assert blob["generated_at"]

    def test_candidate_list_and_context_are_in_the_prompt(self, seeded_client, capture_ai):
        ai = capture_ai([nba_selection("career_trial")])
        _onboard(seeded_client)
        messages = ai.chat.completions.create.call_args.kwargs["messages"]
        system_prompt = messages[0]["content"]
        assert "candidate_id" in system_prompt  # candidates are supplied
        assert "career_trial" in system_prompt
        assert "Demo Student" in system_prompt  # student context
        assert "exactly ONE candidate_id" in system_prompt  # selection rule


# ---------------------------------------------------------------------------
# §14/§15 GET /journey
# ---------------------------------------------------------------------------


class TestJourneyEndpoint:
    def test_journey_404_before_onboarding(self, client, capture_ai):
        capture_ai([nba_selection("update_profile")])
        resp = client.get("/api/v1/journey")
        assert resp.status_code == 404
        assert "error" in resp.json()

    def test_journey_returns_stage_steps_and_nba(self, seeded_client, capture_ai):
        capture_ai([nba_selection("career_trial")])
        _onboard(seeded_client)
        resp = seeded_client.get("/api/v1/journey")
        assert resp.status_code == 200
        data = resp.json()
        assert data["stage"] == "HIGH_SCHOOL"
        assert data["current_step"] == EXPLORE_TITLE  # first pending milestone
        assert 1 <= len(data["next_steps"]) <= 3
        assert data["next_best_action"]["title"] == FALLBACK_TITLE

    def test_journey_never_exposes_more_than_3_steps(self, seeded_client, capture_ai):
        capture_ai([nba_selection("update_profile")])
        _onboard(seeded_client)
        # add a second stage of milestones -> 6 pending milestones total
        resp = seeded_client.post(
            "/api/v1/roadmap",
            json={"career_slug": "software-engineering", "target_stage": "CAREER_DISCOVERY"},
        )
        assert resp.status_code == 200
        resp = seeded_client.get("/api/v1/journey")
        assert len(resp.json()["next_steps"]) == 3  # hard progressive-disclosure cap

    def test_journey_reuses_cached_nba_without_qwen(self, seeded_client, capture_ai):
        ai = capture_ai([nba_selection("career_trial")])
        _onboard(seeded_client)
        first = seeded_client.get("/api/v1/journey").json()
        second = seeded_client.get("/api/v1/journey").json()
        assert ai.chat.completions.create.call_count == 1  # only onboarding called Qwen
        assert first["next_best_action"] == second["next_best_action"]

    def test_journey_recalculates_nba_after_progress_change(self, seeded_client, capture_ai):
        ai = capture_ai([nba_selection("explore_careers"), nba_selection("career_reality")])
        _onboard(seeded_client)  # 1st AI call
        resp = seeded_client.post("/api/v1/progress", json={"milestone_id": 1, "status": "done"})
        assert resp.status_code == 200
        assert ai.chat.completions.create.call_count == 2  # progress forced recalculation
        # the explore_careers candidate was retired — the NBA must have changed
        assert resp.json()["next_best_action"]["title"] != EXPLORE_TITLE


# ---------------------------------------------------------------------------
# §16/§17 POST /progress
# ---------------------------------------------------------------------------


class TestProgress:
    def test_valid_milestone_completion(self, seeded_client, db_session, capture_ai):
        capture_ai([nba_selection("career_trial"), nba_selection("career_reality")])
        _onboard(seeded_client)
        resp = seeded_client.post("/api/v1/progress", json={"milestone_id": 1, "status": "done"})
        assert resp.status_code == 200
        data = resp.json()
        assert set(data.keys()) == {"new_stage", "next_best_action"}
        assert data["new_stage"] == "HIGH_SCHOOL"  # work remains in the stage
        milestone = db_session.get(Milestone, 1)
        assert milestone.status == "done"
        assert milestone.completed_at is not None

    def test_unknown_milestone_returns_404(self, seeded_client, capture_ai):
        capture_ai([nba_selection("career_trial")])
        _onboard(seeded_client)
        resp = seeded_client.post("/api/v1/progress", json={"milestone_id": 999, "status": "done"})
        assert resp.status_code == 404
        assert "error" in resp.json()

    def test_foreign_milestone_cannot_be_modified(self, seeded_client, db_session, capture_ai):
        capture_ai([nba_selection("career_trial"), nba_selection("career_reality")])
        _onboard(seeded_client)

        # a second student with their own roadmap + milestone
        other_repo = StudentRepository(db_session)
        other = other_repo.create_with_profile(
            name="Other Student", email="other@test.local",
            password_hash="x", education_stage="HIGH_SCHOOL",
        )
        other_roadmap = Roadmap(student_id=other.id, career_id=1, current_stage="HIGH_SCHOOL")
        db_session.add(other_roadmap)
        db_session.flush()
        db_session.add(
            Milestone(
                roadmap_id=other_roadmap.id, title="Other's milestone",
                description="", stage="HIGH_SCHOOL", status="pending", order_index=0,
            )
        )
        db_session.commit()
        foreign_id = (
            db_session.query(Milestone).filter(Milestone.title == "Other's milestone").first().id
        )

        resp = seeded_client.post(
            "/api/v1/progress", json={"milestone_id": foreign_id, "status": "done"}
        )
        assert resp.status_code == 404
        assert db_session.get(Milestone, foreign_id).status == "pending"  # untouched

    def test_invalid_status_returns_422(self, seeded_client, capture_ai):
        capture_ai([nba_selection("career_trial")])
        _onboard(seeded_client)
        resp = seeded_client.post("/api/v1/progress", json={"milestone_id": 1, "status": "active"})
        assert resp.status_code == 422
        assert "error" in resp.json()

    def test_skipped_is_a_valid_student_status(self, seeded_client, db_session, capture_ai):
        capture_ai([nba_selection("career_trial"), nba_selection("career_reality")])
        _onboard(seeded_client)
        resp = seeded_client.post("/api/v1/progress", json={"milestone_id": 1, "status": "skipped"})
        assert resp.status_code == 200
        assert db_session.get(Milestone, 1).status == "skipped"

    def test_valid_stage_transition_occurs(self, seeded_client, db_session, capture_ai):
        # onboarding NBA + 3 progress NBA recalculations
        capture_ai([nba_selection("update_profile")] * 4)
        _onboard(seeded_client)  # HIGH_SCHOOL milestones 1-3
        seeded_client.post(
            "/api/v1/roadmap",
            json={"career_slug": "software-engineering", "target_stage": "CAREER_DISCOVERY"},
        )
        for milestone_id in (1, 2):
            resp = seeded_client.post(
                "/api/v1/progress", json={"milestone_id": milestone_id, "status": "done"}
            )
            assert resp.json()["new_stage"] == "HIGH_SCHOOL"  # not yet
        resp = seeded_client.post("/api/v1/progress", json={"milestone_id": 3, "status": "done"})
        assert resp.json()["new_stage"] == "CAREER_DISCOVERY"  # valid transition fired
        assert db_session.get(Student, 1).education_stage == "CAREER_DISCOVERY"

    def test_invalid_stage_transition_is_rejected(self, seeded_client, db_session, capture_ai):
        """HIGH_SCHOOL cannot skip ahead to SKILL_BUILDING even with pending work there."""
        capture_ai([nba_selection("update_profile")] * 4)
        _onboard(seeded_client)  # HIGH_SCHOOL milestones 1-3
        seeded_client.post(
            "/api/v1/roadmap",
            json={"career_slug": "software-engineering", "target_stage": "SKILL_BUILDING"},
        )
        for milestone_id in (1, 2, 3):
            resp = seeded_client.post(
                "/api/v1/progress", json={"milestone_id": milestone_id, "status": "done"}
            )
        # no valid HIGH_SCHOOL -> SKILL_BUILDING transition: the student stays
        assert resp.json()["new_stage"] == "HIGH_SCHOOL"
        assert db_session.get(Student, 1).education_stage == "HIGH_SCHOOL"


# ---------------------------------------------------------------------------
# §18/§19 POST /roadmap
# ---------------------------------------------------------------------------


class TestRoadmapEndpoint:
    def test_roadmap_creates_milestone_instances(self, seeded_client, db_session, capture_ai):
        capture_ai([nba_selection("career_trial")])
        _onboard(seeded_client)
        resp = seeded_client.post(
            "/api/v1/roadmap",
            json={"career_slug": "software-engineering", "target_stage": "SKILL_BUILDING"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert set(data.keys()) == {"roadmap_id", "current_step", "visible_steps"}
        skill_milestones = (
            db_session.query(Milestone).filter(Milestone.stage == "SKILL_BUILDING").all()
        )
        assert len(skill_milestones) == 3  # templates instantiated

    def test_roadmap_returns_only_visible_steps(self, seeded_client, capture_ai):
        capture_ai([nba_selection("career_trial")])
        _onboard(seeded_client)
        resp = seeded_client.post(
            "/api/v1/roadmap",
            json={"career_slug": "software-engineering", "target_stage": "SKILL_BUILDING"},
        )
        assert 1 <= len(resp.json()["visible_steps"]) <= 3

    def test_roadmap_is_idempotent_no_duplicates(self, seeded_client, db_session, capture_ai):
        capture_ai([nba_selection("career_trial")])
        _onboard(seeded_client)
        body = {"career_slug": "software-engineering", "target_stage": "SKILL_BUILDING"}
        first = seeded_client.post("/api/v1/roadmap", json=body).json()
        second = seeded_client.post("/api/v1/roadmap", json=body).json()
        assert first["roadmap_id"] == second["roadmap_id"]  # roadmap reused
        total = db_session.query(Milestone).count()
        assert total == 6  # 3 HIGH_SCHOOL + 3 SKILL_BUILDING — no duplicates

    def test_roadmap_unknown_career_returns_404(self, seeded_client, capture_ai):
        capture_ai([nba_selection("career_trial")])
        _onboard(seeded_client)
        resp = seeded_client.post(
            "/api/v1/roadmap",
            json={"career_slug": "does-not-exist", "target_stage": "SKILL_BUILDING"},
        )
        assert resp.status_code == 404
        assert "error" in resp.json()

    def test_roadmap_invalid_stage_returns_422(self, seeded_client, capture_ai):
        capture_ai([nba_selection("career_trial")])
        _onboard(seeded_client)
        resp = seeded_client.post(
            "/api/v1/roadmap",
            json={"career_slug": "software-engineering", "target_stage": "NOT_A_STAGE"},
        )
        assert resp.status_code == 422
        assert "error" in resp.json()

    def test_roadmap_never_calls_qwen(self, seeded_client, capture_ai):
        """Roadmap creation and ordering are deterministic (architecture §4)."""
        ai = capture_ai([nba_selection("career_trial")])
        _onboard(seeded_client)
        seeded_client.post(
            "/api/v1/roadmap",
            json={"career_slug": "software-engineering", "target_stage": "SKILL_BUILDING"},
        )
        assert ai.chat.completions.create.call_count == 1  # only the onboarding NBA
