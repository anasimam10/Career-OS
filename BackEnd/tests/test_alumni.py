"""
Phase 3 tests — Alumni endpoints (master §17/§24).

Database-only coverage, no AI:
- GET /alumni: field/career_id/university_id filters, verified-first
  ordering, limit, §10 empty envelope
- GET /alumni/{id}: card field names (§18), provenance columns, 404

Only public career-journey data is exposed — the model carries no contact
details at all (master §24).
"""

from __future__ import annotations

import json

import pytest

from models.alumni import Alumni
from models.university import University


def _add(db, obj):
    db.add(obj)
    db.commit()


@pytest.fixture
def alumni_db(db_session):
    """
    Seeded alumni data (template test data).

    Universities:
        1 LUMS-style (Lahore)   2 NUST-style (Islamabad)
    Alumni (deterministic ids, verified-first + alphabetical name order):
        1 Ayesha Khan    verified   Software Engineering, uni 1, career 1
        2 Bilal Ahmed    verified   Data Science,          uni 2, career 2
        3 Sara Malik     community  Software Engineering,  uni 1
        4 Usman Tariq    community  Medicine
    """
    _add(
        db_session,
        University(
            name="Lahore University of Management Sciences",
            slug="lums-alumni-test",
            city="Lahore",
            type="PRIVATE",
            verification_status="VERIFIED",
        ),
    )
    _add(
        db_session,
        University(
            name="National University of Sciences and Technology",
            slug="nust-alumni-test",
            city="Islamabad",
            type="PUBLIC",
            verification_status="VALIDATED",
        ),
    )

    _add(
        db_session,
        Alumni(
            name="Ayesha Khan",
            university="Lahore University of Management Sciences",
            field="Software Engineering",
            role="Software Engineer",
            company="Systems Limited (template)",
            career_path="Started with Python electives, interned in year 2, "
            "joined as a junior engineer.",
            advice="Build projects every semester — your GitHub is your CV.",
            tags=json.dumps(["Python", "internship"]),
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
            university="National University of Sciences and Technology",
            field="Data Science",
            role="Data Analyst",
            company="Analytics PK (template)",
            career_path="Maths major, Kaggle projects, analyst role.",
            advice="Learn SQL before anything else.",
            tags=json.dumps(["SQL", "Kaggle"]),
            is_verified=True,
            university_id=2,
            career_id=2,
        ),
    )
    _add(
        db_session,
        Alumni(
            name="Sara Malik",
            university="Lahore University of Management Sciences",
            field="Software Engineering",
            role="Frontend Developer",
            company=None,
            career_path="CS degree, freelance web work, first job.",
            advice="Start freelancing early.",
            tags=None,
            is_verified=False,
            university_id=1,
        ),
    )
    _add(
        db_session,
        Alumni(
            name="Usman Tariq",
            university=None,
            field="Medicine",
            role=None,
            company=None,
            career_path=None,
            advice=None,
            tags=None,
            is_verified=False,
        ),
    )
    return db_session


# ---------------------------------------------------------------------------
# GET /api/v1/alumni
# ---------------------------------------------------------------------------


class TestListAlumni:
    def test_verified_first_then_name(self, client, alumni_db):
        body = client.get("/api/v1/alumni").json()
        assert [a["id"] for a in body["alumni"]] == [1, 2, 3, 4]

    def test_field_filter(self, client, alumni_db):
        body = client.get("/api/v1/alumni", params={"field": "Software"}).json()
        assert [a["id"] for a in body["alumni"]] == [1, 3]

    def test_career_id_filter(self, client, alumni_db):
        body = client.get("/api/v1/alumni", params={"career_id": 2}).json()
        assert [a["id"] for a in body["alumni"]] == [2]

    def test_university_id_filter(self, client, alumni_db):
        body = client.get("/api/v1/alumni", params={"university_id": 1}).json()
        assert [a["id"] for a in body["alumni"]] == [1, 3]

    def test_limit_bounds_results(self, client, alumni_db):
        body = client.get("/api/v1/alumni", params={"limit": 2}).json()
        assert [a["id"] for a in body["alumni"]] == [1, 2]

    def test_card_uses_contract_field_names(self, client, alumni_db):
        body = client.get("/api/v1/alumni").json()
        card = body["alumni"][0]
        for key in (
            "id",
            "name",
            "university",
            "field",
            "role",
            "company",
            "career_path_summary",
            "key_advice",
            "tags",
            "is_verified",
        ):
            assert key in card
        assert card["career_path_summary"].startswith("Started with Python")
        assert card["key_advice"].startswith("Build projects")

    def test_tags_parsed_from_json(self, client, alumni_db):
        body = client.get("/api/v1/alumni").json()
        assert body["alumni"][0]["tags"] == ["Python", "internship"]

    def test_is_verified_flag_surfaced(self, client, alumni_db):
        body = client.get("/api/v1/alumni").json()
        assert body["alumni"][0]["is_verified"] is True
        assert body["alumni"][2]["is_verified"] is False

    def test_no_match_returns_empty_envelope(self, client, alumni_db):
        response = client.get("/api/v1/alumni", params={"field": "Astronomy"})
        assert response.status_code == 200
        assert response.json() == {"alumni": []}


# ---------------------------------------------------------------------------
# GET /api/v1/alumni/{id}
# ---------------------------------------------------------------------------


class TestAlumniDetail:
    def test_returns_card_plus_provenance(self, client, alumni_db):
        response = client.get("/api/v1/alumni/1")
        assert response.status_code == 200
        body = response.json()
        assert body["name"] == "Ayesha Khan"
        assert body["university_id"] == 1
        assert body["career_id"] == 1
        assert body["source_url"] == "https://example.com/alumni/ayesha"
        assert body["is_verified"] is True

    def test_sparse_record_serializes_nulls(self, client, alumni_db):
        # Template/community records may have NULL columns — must not 500.
        response = client.get("/api/v1/alumni/4")
        assert response.status_code == 200
        body = response.json()
        assert body["university"] is None
        assert body["company"] is None
        assert body["tags"] == []
        assert body["is_verified"] is False

    def test_unknown_alumni_404(self, client, alumni_db):
        response = client.get("/api/v1/alumni/999")
        assert response.status_code == 404
        assert "error" in response.json()
