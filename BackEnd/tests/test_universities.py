"""
Phase 3 tests — Universities endpoints (master §17).

Database-only coverage, no AI:
- GET /universities: verified-only visibility, city/type/hec_recognized
  filters, field narrowing via programs, limit, §10 empty envelope
- GET /universities/{id}/programs: listing, field/degree_type filters,
  candidate-program exclusion, 404 for unknown OR not-yet-validated
  universities
"""

from __future__ import annotations

import json

import pytest

from models.university import Program, University


def _add(db, obj):
    db.add(obj)
    db.commit()


@pytest.fixture
def uni_db(db_session):
    """
    Seeded university/program data (template test data).

    Universities (deterministic ids on a fresh per-test database):
        1 LUMS-style    Lahore,   PRIVATE,  HEC recognized, VERIFIED
        2 NUST-style    Islamabad, PUBLIC,  HEC recognized, VALIDATED
        3 KEMU-style    Lahore,   PUBLIC,  HEC unknown,     VALIDATED
        4 Candidate Uni Karachi,  PUBLIC,  HEC recognized, CANDIDATE (hidden)
    Programs:
        1 BS Computer Science        (uni 1, field CS,       VERIFIED)
        2 BBA                        (uni 1, field Business, VERIFIED)
        3 BE Electrical Engineering  (uni 2, field EE,       VALIDATED)
        4 BS Computer Science        (uni 2, field CS,       VALIDATED)
        5 MBBS                       (uni 3, field Medicine, VALIDATED)
        6 MS Artificial Intelligence (uni 2, CANDIDATE — hidden)
    """
    _add(
        db_session,
        University(
            name="Lahore University of Management Sciences",
            short_name="LUMS",
            slug="lums-test",
            city="Lahore",
            province="Punjab",
            type="PRIVATE",
            hec_recognized=True,
            website_url="https://example.com/lums",
            verification_status="VERIFIED",
        ),
    )
    _add(
        db_session,
        University(
            name="National University of Sciences and Technology",
            short_name="NUST",
            slug="nust-test",
            city="Islamabad",
            province="Islamabad",
            type="PUBLIC",
            hec_recognized=True,
            verification_status="VALIDATED",
        ),
    )
    _add(
        db_session,
        University(
            name="King Edward Medical University",
            short_name="KEMU",
            slug="kemu-test",
            city="Lahore",
            province="Punjab",
            type="PUBLIC",
            hec_recognized=None,  # unknown — never guessed
            verification_status="VALIDATED",
        ),
    )
    _add(
        db_session,
        University(
            name="Candidate University (template)",
            slug="candidate-uni-test",
            city="Karachi",
            type="PUBLIC",
            hec_recognized=True,
            verification_status="CANDIDATE",
        ),
    )

    _add(
        db_session,
        Program(
            university_id=1,
            name="BS Computer Science",
            degree_type="BS",
            field="Computer Science",
            duration_years=4.0,
            annual_fee_pkr=500000,
            career_ids=json.dumps([1, 2]),
            verification_status="VERIFIED",
        ),
    )
    _add(
        db_session,
        Program(
            university_id=1,
            name="Bachelor of Business Administration",
            degree_type="BBA",
            field="Business Administration",
            duration_years=4.0,
            verification_status="VERIFIED",
        ),
    )
    _add(
        db_session,
        Program(
            university_id=2,
            name="BE Electrical Engineering",
            degree_type="BE",
            field="Electrical Engineering",
            duration_years=4.0,
            verification_status="VALIDATED",
        ),
    )
    _add(
        db_session,
        Program(
            university_id=2,
            name="BS Computer Science",
            degree_type="BS",
            field="Computer Science",
            duration_years=4.0,
            verification_status="VALIDATED",
        ),
    )
    _add(
        db_session,
        Program(
            university_id=3,
            name="MBBS",
            degree_type="MBBS",
            field="Medicine",
            duration_years=5.0,
            verification_status="VALIDATED",
        ),
    )
    _add(
        db_session,
        Program(
            university_id=2,
            name="MS Artificial Intelligence",
            degree_type="MS",
            field="Computer Science",
            verification_status="CANDIDATE",
        ),
    )
    return db_session


# ---------------------------------------------------------------------------
# GET /api/v1/universities
# ---------------------------------------------------------------------------


class TestListUniversities:
    def test_returns_only_verified_universities(self, client, uni_db):
        response = client.get("/api/v1/universities")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 3
        # Sorted by short_name: KEMU, LUMS, NUST. The CANDIDATE row is hidden.
        assert [u["id"] for u in body["universities"]] == [3, 1, 2]

    def test_summary_shape(self, client, uni_db):
        body = client.get("/api/v1/universities").json()
        first = body["universities"][0]
        for key in (
            "id",
            "name",
            "short_name",
            "slug",
            "city",
            "province",
            "type",
            "hec_recognized",
            "website_url",
        ):
            assert key in first
        # Verification internals are not part of the student-facing card.
        assert "verification_status" not in first

    def test_city_filter_case_insensitive(self, client, uni_db):
        body = client.get("/api/v1/universities", params={"city": "lahore"}).json()
        assert [u["id"] for u in body["universities"]] == [3, 1]

    def test_type_filter(self, client, uni_db):
        body = client.get("/api/v1/universities", params={"type": "PUBLIC"}).json()
        assert [u["id"] for u in body["universities"]] == [3, 2]

    def test_hec_recognized_filter(self, client, uni_db):
        body = client.get(
            "/api/v1/universities", params={"hec_recognized": True}
        ).json()
        # University 3 has unknown (None) HEC status and is excluded.
        assert [u["id"] for u in body["universities"]] == [1, 2]

    def test_field_filter_narrows_via_programs(self, client, uni_db):
        body = client.get(
            "/api/v1/universities", params={"field": "Computer Science"}
        ).json()
        assert [u["id"] for u in body["universities"]] == [1, 2]

    def test_field_without_programs_is_empty_envelope(self, client, uni_db):
        response = client.get(
            "/api/v1/universities", params={"field": "Marine Biology"}
        )
        assert response.status_code == 200
        assert response.json() == {"universities": [], "total": 0}

    def test_limit_bounds_results(self, client, uni_db):
        body = client.get("/api/v1/universities", params={"limit": 2}).json()
        assert [u["id"] for u in body["universities"]] == [3, 1]
        assert body["total"] == 2


# ---------------------------------------------------------------------------
# GET /api/v1/universities/{id}/programs
# ---------------------------------------------------------------------------


class TestUniversityPrograms:
    def test_lists_programs_of_one_university(self, client, uni_db):
        body = client.get("/api/v1/universities/1/programs").json()
        names = [p["name"] for p in body["programs"]]
        # Alphabetical by name (ASCII: 'S' sorts before 'a').
        assert names == ["BS Computer Science", "Bachelor of Business Administration"]

    def test_program_summary_shape_and_career_ids(self, client, uni_db):
        body = client.get("/api/v1/universities/1/programs").json()
        cs = next(p for p in body["programs"] if p["name"] == "BS Computer Science")
        assert cs["degree_type"] == "BS"
        assert cs["field"] == "Computer Science"
        assert cs["duration_years"] == 4.0
        assert cs["annual_fee_pkr"] == 500000
        assert cs["career_ids"] == [1, 2]

    def test_field_filter(self, client, uni_db):
        body = client.get(
            "/api/v1/universities/2/programs", params={"field": "Computer"}
        ).json()
        assert [p["name"] for p in body["programs"]] == ["BS Computer Science"]

    def test_degree_type_filter_case_insensitive(self, client, uni_db):
        body = client.get(
            "/api/v1/universities/2/programs", params={"degree_type": "bs"}
        ).json()
        assert [p["name"] for p in body["programs"]] == ["BS Computer Science"]

    def test_candidate_program_hidden(self, client, uni_db):
        body = client.get("/api/v1/universities/2/programs").json()
        names = [p["name"] for p in body["programs"]]
        assert "MS Artificial Intelligence" not in names

    def test_unknown_university_404(self, client, uni_db):
        response = client.get("/api/v1/universities/999/programs")
        assert response.status_code == 404
        assert "error" in response.json()

    def test_candidate_university_404(self, client, uni_db):
        # Not-yet-validated universities are "not found" for students.
        response = client.get("/api/v1/universities/4/programs")
        assert response.status_code == 404

    def test_empty_program_list_envelope(self, client, uni_db):
        # University 1 exists and is visible; no Medicine program though.
        body = client.get(
            "/api/v1/universities/1/programs", params={"field": "Medicine"}
        ).json()
        assert body == {"programs": []}
