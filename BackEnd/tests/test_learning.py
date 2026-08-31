"""
Phase 3 tests — Learning endpoints (master §17/§25).

Database-only coverage, no AI:
- GET /learning: catalog listing without skill, exact skill match,
  level/type/is_free filters (NULL = unknown, excluded when a value is
  requested), inactive + candidate exclusion, §10 empty envelope
"""

from __future__ import annotations

import pytest

from models.learning import LearningResource


def _add(db, obj):
    db.add(obj)
    db.commit()


@pytest.fixture
def learn_db(db_session):
    """
    Seeded learning resources (template test data).

    Resources (deterministic ids on a fresh per-test database):
        1 Python for Everybody                    (Python, course, beginner, free)
        2 CS50's Introduction to Python           (Python, course, intermediate, free)
        3 SQL Basics                              (SQL, tutorial, beginner, paid)
        4 Pro Git                                 (Git, book, level NULL, is_free NULL)
        5 Inactive Python Course                  (Python — inactive, never returned)
        6 Candidate Python Course                 (Python — CANDIDATE, never returned)
    """
    resources = [
        dict(
            skill_name="Python",
            title="Python for Everybody",
            type="course",
            provider="py4e (template)",
            url="https://example.com/py4e",
            level="beginner",
            is_free=True,
            duration_hours=30.0,
        ),
        dict(
            skill_name="Python",
            title="CS50's Introduction to Programming with Python",
            type="course",
            provider="CS50 (template)",
            url="https://example.com/cs50p",
            level="intermediate",
            is_free=True,
        ),
        dict(
            skill_name="SQL",
            title="SQL Basics",
            type="tutorial",
            provider="Example Academy (template)",
            url="https://example.com/sql-basics",
            level="beginner",
            is_free=False,
        ),
        dict(
            skill_name="Git",
            title="Pro Git",
            type="book",
            provider="Example Press (template)",
            url="https://example.com/progit",
            level=None,
            is_free=None,
        ),
    ]
    for data in resources:
        _add(db_session, LearningResource(verification_status="VALIDATED", **data))

    _add(
        db_session,
        LearningResource(
            skill_name="Python",
            title="Inactive Python Course",
            type="course",
            url="https://example.com/inactive",
            level="beginner",
            is_free=True,
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
            level="beginner",
            is_free=True,
            verification_status="CANDIDATE",
        ),
    )
    return db_session


def _titles(body: dict) -> list[str]:
    return [r["title"] for r in body["resources"]]


# ---------------------------------------------------------------------------
# GET /api/v1/learning
# ---------------------------------------------------------------------------


class TestListLearningResources:
    def test_catalog_without_skill(self, client, learn_db):
        body = client.get("/api/v1/learning").json()
        # Active + validated only, alphabetical by title.
        assert _titles(body) == [
            "CS50's Introduction to Programming with Python",
            "Pro Git",
            "Python for Everybody",
            "SQL Basics",
        ]

    def test_skill_filter_exact_match(self, client, learn_db):
        body = client.get("/api/v1/learning", params={"skill": "Python"}).json()
        assert _titles(body) == [
            "CS50's Introduction to Programming with Python",
            "Python for Everybody",
        ]

    def test_skill_filter_case_insensitive(self, client, learn_db):
        body = client.get("/api/v1/learning", params={"skill": "python"}).json()
        assert len(body["resources"]) == 2

    def test_level_filter(self, client, learn_db):
        body = client.get("/api/v1/learning", params={"level": "beginner"}).json()
        # "Pro Git" has a NULL level and therefore matches every filter.
        assert _titles(body) == ["Pro Git", "Python for Everybody", "SQL Basics"]

    def test_null_level_matches_any_level_filter(self, client, learn_db):
        # Records with NULL level are unspecific, not wrong.
        body = client.get("/api/v1/learning", params={"level": "advanced"}).json()
        assert _titles(body) == ["Pro Git"]

    def test_type_filter(self, client, learn_db):
        body = client.get("/api/v1/learning", params={"type": "tutorial"}).json()
        assert _titles(body) == ["SQL Basics"]

    def test_is_free_true_excludes_paid_and_unknown(self, client, learn_db):
        body = client.get("/api/v1/learning", params={"is_free": True}).json()
        assert _titles(body) == [
            "CS50's Introduction to Programming with Python",
            "Python for Everybody",
        ]

    def test_is_free_false_excludes_free_and_unknown(self, client, learn_db):
        body = client.get("/api/v1/learning", params={"is_free": False}).json()
        assert _titles(body) == ["SQL Basics"]

    def test_skill_with_level_combined(self, client, learn_db):
        body = client.get(
            "/api/v1/learning", params={"skill": "Python", "level": "beginner"}
        ).json()
        assert _titles(body) == ["Python for Everybody"]

    def test_unknown_skill_returns_empty_envelope(self, client, learn_db):
        response = client.get("/api/v1/learning", params={"skill": "Fortran"})
        assert response.status_code == 200
        assert response.json() == {"resources": []}

    def test_resource_shape(self, client, learn_db):
        body = client.get("/api/v1/learning", params={"skill": "Python"}).json()
        first = body["resources"][0]
        for key in (
            "id",
            "skill_name",
            "title",
            "type",
            "provider",
            "url",
            "language",
            "level",
            "is_free",
            "duration_hours",
        ):
            assert key in first
        # Verification internals stay out of the student-facing card.
        assert "verification_status" not in first

    def test_inactive_and_candidate_never_visible(self, client, learn_db):
        body = client.get("/api/v1/learning", params={"skill": "Python"}).json()
        titles = _titles(body)
        assert "Inactive Python Course" not in titles
        assert "Candidate Python Course" not in titles
