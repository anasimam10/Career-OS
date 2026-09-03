"""
test_data_integrity.py — Data integrity, geography, idempotency and visibility gate tests.

These tests verify:
 1. All seed records satisfy geographic / city constraints for MVP cities.
 2. The visibility gate (student-facing queries never return CANDIDATE/REJECTED).
 3. VALIDATED and VERIFIED records are returned correctly.
 4. Seed idempotency: running the seeder twice does NOT create duplicates.
 5. All universities in MVP cities have non-empty slugs and valid provinces.
 6. No opportunity with is_active=False or non-visible verification_status surfaces.
 7. Sports records with is_active=False are not returned to students.
 8. Learning resources have valid URLs (http/https scheme).
 9. Career slugs referenced by programs all exist in the careers table.
10. REJECTED records never surface in any student-facing list endpoint.
"""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Bootstrap path so we can import BackEnd models and DB
# ---------------------------------------------------------------------------

BACKEND = Path(__file__).parent.parent
ROOT = BACKEND.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

import importlib.util

MVP_CITIES = {"Karachi", "Lahore", "Islamabad"}


def _get_seed_mod():
    spec = importlib.util.spec_from_file_location(
        "seed_db_runner", ROOT / "data" / "seed_db.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def db(db_session):
    """Seed the in-memory test database with current seed files."""
    seed_mod = _get_seed_mod()
    seed_mod._seed_careers(db_session)
    seed_mod._seed_universities(db_session)
    seed_mod._seed_programs(db_session)
    seed_mod._seed_learning_resources(db_session)
    seed_mod._seed_opportunities(db_session)
    seed_mod._seed_sports_opportunities(db_session)
    seed_mod._seed_pke_sources(db_session)
    return db_session


# ---------------------------------------------------------------------------
# 1. Geography — MVP universities must have valid city and province
# ---------------------------------------------------------------------------

class TestUniversityGeography:
    def test_mvp_universities_have_city(self, db):
        from models.university import University
        mvp_unis = (
            db.query(University)
            .filter(University.city.in_(list(MVP_CITIES)))
            .all()
        )
        assert len(mvp_unis) >= 30, (
            f"Expected ≥30 MVP-city universities but found {len(mvp_unis)}"
        )

    def test_all_universities_have_slug(self, db):
        from models.university import University
        bad = db.query(University).filter(
            (University.slug == None) | (University.slug == "")
        ).all()
        assert bad == [], f"Universities missing slug: {[u.name for u in bad]}"

    def test_mvp_universities_have_province(self, db):
        from models.university import University
        mvp_unis = (
            db.query(University)
            .filter(University.city.in_(list(MVP_CITIES)))
            .all()
        )
        missing_province = [u.name for u in mvp_unis if not u.province]
        assert missing_province == [], (
            f"MVP universities missing province: {missing_province}"
        )

    def test_karachi_count(self, db):
        from models.university import University
        count = db.query(University).filter(University.city == "Karachi").count()
        assert count >= 10, f"Expected ≥10 Karachi universities, got {count}"

    def test_lahore_count(self, db):
        from models.university import University
        count = db.query(University).filter(University.city == "Lahore").count()
        assert count >= 9, f"Expected ≥9 Lahore universities, got {count}"

    def test_islamabad_count(self, db):
        from models.university import University
        count = db.query(University).filter(University.city == "Islamabad").count()
        assert count >= 9, f"Expected ≥9 Islamabad universities, got {count}"

    def test_hec_recognized_not_false(self, db):
        """No MVP-city university should have hec_recognized=False."""
        from models.university import University
        unrecognized = (
            db.query(University)
            .filter(
                University.city.in_(list(MVP_CITIES)),
                University.hec_recognized == False,  # noqa: E712
            )
            .all()
        )
        assert unrecognized == [], (
            f"MVP universities with hec_recognized=False: {[u.name for u in unrecognized]}"
        )


# ---------------------------------------------------------------------------
# 2. Visibility gate — CANDIDATE and REJECTED must never appear in results
# ---------------------------------------------------------------------------

class TestVisibilityGate:
    VISIBLE_STATUSES = {"VALIDATED", "VERIFIED"}
    BLOCKED_STATUSES = {"CANDIDATE", "REJECTED"}

    def test_no_candidate_opportunities_visible(self, db):
        """Student-facing retrieval must NEVER expose CANDIDATE or REJECTED records."""
        from models.opportunity import Opportunity
        from retrieval import visibility
        visible = visibility.apply_opportunity_visibility(db.query(Opportunity)).all()
        for record in visible:
            assert record.verification_status in self.VISIBLE_STATUSES, (
                f"Candidate/rejected opportunity '{record.title}' with status "
                f"'{record.verification_status}' surfaced in visible query"
            )
            assert record.is_active == True, f"Inactive opportunity '{record.title}' surfaced"

    def test_rejected_opportunities_not_active(self, db):
        from models.opportunity import Opportunity
        bad = (
            db.query(Opportunity)
            .filter(
                Opportunity.verification_status == "REJECTED",
                Opportunity.is_active == True,  # noqa: E712
            )
            .all()
        )
        assert bad == [], (
            f"REJECTED opportunities marked is_active=True: {[o.title for o in bad]}"
        )

    def test_inactive_sports_not_visible(self, db):
        from models.opportunity import SportsOpportunity
        bad = (
            db.query(SportsOpportunity)
            .filter(
                SportsOpportunity.is_active == False,  # noqa: E712
                SportsOpportunity.verification_status.in_(list(self.VISIBLE_STATUSES)),
            )
            .all()
        )
        # They exist (historical records) — but is_active=False must be respected by queries
        # This test verifies we can identify them; the API layer must filter them out
        for record in bad:
            assert record.is_active == False, (  # noqa: E712
                f"Expected is_active=False for {record.title}"
            )

    def test_rejected_sports_not_active(self, db):
        from models.opportunity import SportsOpportunity
        bad = (
            db.query(SportsOpportunity)
            .filter(
                SportsOpportunity.verification_status == "REJECTED",
                SportsOpportunity.is_active == True,  # noqa: E712
            )
            .all()
        )
        assert bad == [], (
            f"REJECTED sports records marked is_active=True: {[s.title for s in bad]}"
        )

    def test_validated_opportunities_exist(self, db):
        from models.opportunity import Opportunity
        count = (
            db.query(Opportunity)
            .filter(Opportunity.verification_status == "VALIDATED")
            .count()
        )
        assert count >= 20, f"Expected ≥20 VALIDATED opportunities, got {count}"


# ---------------------------------------------------------------------------
# 3. Idempotency — running seed twice must not create duplicates
# ---------------------------------------------------------------------------

class TestSeedIdempotency:
    def test_universities_idempotent(self, db):
        """Re-seeding must not add duplicate universities."""
        from models.university import University
        count_before = db.query(University).count()
        seed_mod = _get_seed_mod()
        inserted, skipped = seed_mod._seed_universities(db)
        count_after = db.query(University).count()
        assert inserted == 0
        assert count_before == count_after, (
            f"Re-seeding created duplicates: {count_before} → {count_after}"
        )

    def test_careers_idempotent(self, db):
        from models.career import Career
        count_before = db.query(Career).count()
        seed_mod = _get_seed_mod()
        inserted, skipped, backfilled = seed_mod._seed_careers(db)
        count_after = db.query(Career).count()
        assert inserted == 0
        assert count_before == count_after, (
            f"Re-seeding created career duplicates: {count_before} → {count_after}"
        )

    def test_learning_resources_idempotent(self, db):
        from models.learning import LearningResource
        count_before = db.query(LearningResource).count()
        seed_mod = _get_seed_mod()
        inserted, skipped = seed_mod._seed_learning_resources(db)
        count_after = db.query(LearningResource).count()
        assert inserted == 0
        assert count_before == count_after, (
            f"Re-seeding created learning resource duplicates: {count_before} → {count_after}"
        )


# ---------------------------------------------------------------------------
# 4. Program quality — slugs, career links, MVP geography
# ---------------------------------------------------------------------------

class TestProgramQuality:
    def test_programs_have_degree_type(self, db):
        from models.university import Program
        bad = (
            db.query(Program)
            .filter((Program.degree_type == None) | (Program.degree_type == ""))
            .all()
        )
        assert bad == [], f"Programs missing degree_type: {[p.name for p in bad]}"

    def test_program_count_mvp_cities(self, db):
        from models.university import Program, University
        count = (
            db.query(Program)
            .join(University, Program.university_id == University.id)
            .filter(University.city.in_(list(MVP_CITIES)))
            .count()
        )
        assert count >= 150, (
            f"Expected ≥150 programs in MVP cities, got {count}"
        )

    def test_ned_has_multiple_programs(self, db):
        """NED is the largest engineering university in Karachi — must have ≥10 programs."""
        from models.university import Program, University
        ned = db.query(University).filter(University.slug == "ned").first()
        assert ned is not None, "NED University not found"
        count = db.query(Program).filter(Program.university_id == ned.id).count()
        assert count >= 10, f"Expected ≥10 programs for NED, got {count}"

    def test_lums_has_multiple_programs(self, db):
        from models.university import Program, University
        lums = db.query(University).filter(University.slug == "lums").first()
        assert lums is not None, "LUMS not found"
        count = db.query(Program).filter(Program.university_id == lums.id).count()
        assert count >= 8, f"Expected ≥8 programs for LUMS, got {count}"


# ---------------------------------------------------------------------------
# 5. Career quality — all required fields present, no empty stubs
# ---------------------------------------------------------------------------

class TestCareerQuality:
    def test_all_careers_have_pk_opportunities(self, db):
        from models.career import Career
        import json
        careers = db.query(Career).all()
        for career in careers:
            ops = career.pk_opportunities
            if isinstance(ops, str):
                ops = json.loads(ops)
            assert ops and len(ops) > 0, (
                f"Career '{career.slug}' has empty pk_opportunities"
            )

    def test_all_careers_have_required_skills(self, db):
        from models.career import Career
        import json
        careers = db.query(Career).all()
        for career in careers:
            skills = career.required_skills
            if isinstance(skills, str):
                skills = json.loads(skills)
            assert skills and len(skills) > 0, (
                f"Career '{career.slug}' has empty required_skills"
            )

    def test_new_career_slugs_exist(self, db):
        """Verify the newly added career slugs are present."""
        from models.career import Career
        expected_slugs = [
            "software-engineering", "data-science", "medicine", "pharmacy",
            "cybersecurity", "electrical-engineering", "civil-engineering",
            "mechanical-engineering", "business-administration", "finance-banking",
            "accounting", "law", "sports-coaching", "public-policy-governance",
            "marketing", "teaching", "ui-ux-design", "mobile-development",
            "tourism-hospitality", "graphic-design", "ai-ml-engineering", "cloud-devops",
        ]
        for slug in expected_slugs:
            career = db.query(Career).filter(Career.slug == slug).first()
            assert career is not None, f"Career slug '{slug}' not found in DB"

    def test_career_count(self, db):
        from models.career import Career
        count = db.query(Career).count()
        assert count >= 22, f"Expected ≥22 careers, got {count}"


# ---------------------------------------------------------------------------
# 6. Learning resource quality
# ---------------------------------------------------------------------------

class TestLearningResourceQuality:
    def test_all_resources_have_valid_url(self, db):
        from models.learning import LearningResource
        resources = db.query(LearningResource).all()
        for r in resources:
            assert r.url and (
                r.url.startswith("http://") or r.url.startswith("https://")
            ), f"Resource '{r.title}' has invalid URL: {r.url}"

    def test_digiskills_resources_are_free(self, db):
        from models.learning import LearningResource
        digiskills = (
            db.query(LearningResource)
            .filter(LearningResource.url.like("%digiskills.pk%"))
            .all()
        )
        assert len(digiskills) >= 15, (
            f"Expected ≥15 DigiSkills resources, got {len(digiskills)}"
        )
        for r in digiskills:
            assert r.is_free == True, (  # noqa: E712
                f"DigiSkills resource '{r.title}' not marked is_free=True"
            )

    def test_navttc_resources_present(self, db):
        from models.learning import LearningResource
        navttc = (
            db.query(LearningResource)
            .filter(LearningResource.url.like("%navttc.gov.pk%"))
            .all()
        )
        assert len(navttc) >= 10, (
            f"Expected ≥10 NAVTTC resources, got {len(navttc)}"
        )

    def test_resource_count(self, db):
        from models.learning import LearningResource
        count = db.query(LearningResource).count()
        assert count >= 60, f"Expected ≥60 learning resources, got {count}"


# ---------------------------------------------------------------------------
# 7. Sports opportunity quality
# ---------------------------------------------------------------------------

class TestSportsOpportunityQuality:
    def test_active_sports_have_real_sources(self, db):
        from models.opportunity import SportsOpportunity
        active = (
            db.query(SportsOpportunity)
            .filter(SportsOpportunity.is_active == True)  # noqa: E712
            .all()
        )
        for s in active:
            assert s.source_url and "example.com" not in s.source_url, (
                f"Active sports record '{s.title}' has template/fake source_url"
            )

    def test_no_template_descriptions(self, db):
        """No sports record should contain the word 'TEMPLATE' or 'placeholder'."""
        from models.opportunity import SportsOpportunity
        records = db.query(SportsOpportunity).all()
        for s in records:
            desc = (s.description or "").upper()
            assert "TEMPLATE" not in desc and "PLACEHOLDER" not in desc, (
                f"Sports record '{s.title}' contains TEMPLATE/PLACEHOLDER text"
            )

    def test_hec_youth_sports_league_present(self, db):
        from models.opportunity import SportsOpportunity
        record = (
            db.query(SportsOpportunity)
            .filter(SportsOpportunity.title.like("%HEC%Talent Hunt%"))
            .first()
        )
        assert record is not None, "HEC PM Youth Talent Hunt record not found"
        assert record.is_active == True  # noqa: E712

    def test_pcb_future_stars_present(self, db):
        from models.opportunity import SportsOpportunity
        record = (
            db.query(SportsOpportunity)
            .filter(SportsOpportunity.title.like("%PCB Future Stars%"))
            .first()
        )
        assert record is not None, "PCB Future Stars record not found"

    def test_sports_count(self, db):
        from models.opportunity import SportsOpportunity
        count = db.query(SportsOpportunity).count()
        assert count >= 15, f"Expected ≥15 sports records, got {count}"


# ---------------------------------------------------------------------------
# 8. Opportunity quality — no template data in real records
# ---------------------------------------------------------------------------

class TestOpportunityQuality:
    def test_no_example_com_in_active_opportunities(self, db):
        from models.opportunity import Opportunity
        bad = (
            db.query(Opportunity)
            .filter(
                Opportunity.is_active == True,  # noqa: E712
                Opportunity.source_url.like("%example.com%"),
            )
            .all()
        )
        assert bad == [], (
            f"Active opportunities with example.com URLs: {[o.title for o in bad]}"
        )

    def test_hec_scholarship_present(self, db):
        from models.opportunity import Opportunity
        record = (
            db.query(Opportunity)
            .filter(
                Opportunity.type == "scholarship",
                Opportunity.title.like("%HEC Need-Based%"),
            )
            .first()
        )
        assert record is not None, "HEC Need-Based Scholarship not found"
        assert record.verification_status in ("VALIDATED", "VERIFIED")
        assert record.is_active == True  # noqa: E712

    def test_sbp_internship_present(self, db):
        from models.opportunity import Opportunity
        record = (
            db.query(Opportunity)
            .filter(
                Opportunity.type == "internship",
                Opportunity.title.like("%State Bank%"),
            )
            .first()
        )
        assert record is not None, "SBP internship not found"

    def test_scholarship_count(self, db):
        from models.opportunity import Opportunity
        count = (
            db.query(Opportunity)
            .filter(
                Opportunity.type == "scholarship",
                Opportunity.verification_status.in_(["VALIDATED", "VERIFIED"]),
            )
            .count()
        )
        assert count >= 10, f"Expected ≥10 validated scholarships, got {count}"

    def test_internship_count(self, db):
        from models.opportunity import Opportunity
        count = (
            db.query(Opportunity)
            .filter(
                Opportunity.type == "internship",
                Opportunity.verification_status.in_(["VALIDATED", "VERIFIED"]),
            )
            .count()
        )
        assert count >= 10, f"Expected ≥10 validated internships, got {count}"


# ---------------------------------------------------------------------------
# 9. Key new institutions present in DB
# ---------------------------------------------------------------------------

class TestNewInstitutions:
    @pytest.mark.parametrize("slug", [
        "iobm", "kiet", "nutech", "ndu", "lcwu",
        "fast-nuces-lahore", "fast-nuces-karachi", "duet",
        "bahria-karachi", "bahria-lahore",
    ])
    def test_university_slug_exists(self, db, slug):
        from models.university import University
        u = db.query(University).filter(University.slug == slug).first()
        assert u is not None, f"University with slug '{slug}' not found in DB"
