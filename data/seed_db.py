"""
Seed the SQLite database from data/seed/*.json.

Usage (from the repository root):

    python data/seed_db.py

Behaviour:
- Creates any missing tables (and runs the additive column migration).
- INSERT-ONLY everywhere: records already in the database are skipped and
  reported, never overwritten. The single exception is a NULL-category
  backfill on existing careers (only fills empty values, never overwrites).
- Seeds, in order:
  * careers from careers.json (+ category backfill for existing rows)
  * universities from universities.json (VERIFIED manual-entry facts)
  * programs from programs.json (university_slug / career_slugs resolved
    to ids at seed time; unknown slugs are skipped with a warning)
  * learning resources from learning_resources.json (VERIFIED)
  * alumni from alumni.json (TEMPLATE records, is_verified=false)
  * opportunities / sports_opportunities with curated status VALIDATED
- Date convention in the JSON files: "today" = the seed date, "+45"/"-400"
  = day offsets from the seed date, anything else = ISO date. This keeps
  template deadlines perpetually in the future at seed time.
- Creates the demo student (id=1, matching Frontend/lib/session.ts) if it
  does not exist yet.

The opportunity/sports/alumni seed data is TEMPLATE data - not independently
verified (see each file's _meta block). Universities, programs and learning
resources are manual-entry mode D basic verified public facts.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    backend = ROOT / "BackEnd"

    # The backend runs from inside BackEnd/ (uvicorn main:app); run the seeder
    # with the same working directory so the relative SQLite URL resolves
    # to the same database file the server uses.
    os.chdir(backend)
    sys.path.insert(0, str(backend))

    from database import SessionLocal, init_db  # noqa: E402
    from repositories.student_repo import StudentRepository  # noqa: E402

    init_db()

    db = SessionLocal()
    try:
        car_inserted, car_skipped, car_backfilled = _seed_careers(db)
        uni_inserted, uni_skipped = _seed_universities(db)
        prog_inserted, prog_skipped = _seed_programs(db)
        lr_inserted, lr_skipped = _seed_learning_resources(db)
        alum_inserted, alum_skipped = _seed_alumni(db)
        opp_inserted, opp_skipped = _seed_opportunities(db)
        sports_inserted, sports_skipped = _seed_sports_opportunities(db)
        pke_inserted, pke_skipped = _seed_pke_sources(db)

        # --- demo student (id=1, per Frontend/lib/session.ts) --------------
        student_repo = StudentRepository(db)
        demo_student = student_repo.get_by_id(1)
        demo_created = False
        if demo_student is None:
            student_repo.create_with_profile(
                name="Demo Student",
                email="demo@ah-careers.local",
                password_hash="demo-no-auth-mvp",  # demo context only - no auth yet
                education_stage="HIGH_SCHOOL",
                career_goal="Software Engineering",
                sports_interest="Cricket",
                motivation_tags=json.dumps(
                    ["I genuinely love this subject", "High salary potential"]
                ),
            )
            starter_nba = {
                "candidate_id": "career_trial",
                "action": {
                    "title": "Complete the 7-Day Career Trial",
                    "description": "Test one career hands-on for seven days using the trial plan.",
                    "steps": [
                        "Open the career's Trial page",
                        "Generate your 7-day trial plan",
                        "Complete the daily tasks",
                        "Answer the reflection prompt on day 7"
                    ],
                    "estimated_time": "7 days",
                    "why_this_matters": "A 7-day hands-on trial helps you test if Software Engineering matches your passions before committing years to study.",
                    "stage": "HIGH_SCHOOL"
                },
                "completed_milestone_titles": [],
                "generated_at": datetime.utcnow().isoformat() + "Z"
            }
            student_repo.update_profile(
                1,
                interests=json.dumps(["Technology", "Mathematics"]),
                skills=json.dumps([{"name": "Python", "level": "beginner"}]),
                next_best_action=json.dumps(starter_nba, ensure_ascii=False),
            )
            demo_created = True
    finally:
        db.close()

    print(f"Careers: {car_inserted} inserted, {car_skipped} skipped, {car_backfilled} categories backfilled.")
    print(f"Universities: {uni_inserted} inserted, {uni_skipped} skipped (already present).")
    print(f"Programs: {prog_inserted} inserted, {prog_skipped} skipped (already present).")
    print(f"Learning resources: {lr_inserted} inserted, {lr_skipped} skipped (already present).")
    print(f"Alumni: {alum_inserted} inserted, {alum_skipped} skipped (already present).")
    print(f"Opportunities: {opp_inserted} inserted, {opp_skipped} skipped (already present).")
    print(f"Sports opportunities: {sports_inserted} inserted, {sports_skipped} skipped (already present).")
    print(f"PKE sources: {pke_inserted} inserted, {pke_skipped} skipped (already present).")
    print(f"Demo student (id=1): {'created' if demo_created else 'already present'}.")
    print("Done. Opportunity/sports/alumni seeds are TEMPLATE data (see _meta); universities/programs/learning are manual-entry verified facts.")
    return 0


# ---------------------------------------------------------------------------
# Careers
# ---------------------------------------------------------------------------


def _seed_careers(db) -> tuple[int, int, int]:
    """Insert careers; backfill category on existing rows where it is NULL."""
    from models.career import Career

    seed_file = ROOT / "data" / "seed" / "careers.json"
    payload = json.loads(seed_file.read_text(encoding="utf-8"))

    inserted, skipped, backfilled = 0, 0, 0
    for record in payload["careers"]:
        existing = db.query(Career).filter(Career.slug == record["slug"]).first()
        if existing is not None:
            skipped += 1
            # Additive backfill only: fill empty fields, never overwrite real content.
            updated = False
            if existing.category is None and record.get("category"):
                existing.category = record["category"]
                updated = True
            if (not existing.pk_opportunities or existing.pk_opportunities in ("[]", "null")) and record.get("pk_opportunities"):
                existing.pk_opportunities = json.dumps(record.get("pk_opportunities") or [])
                updated = True
            if (not existing.required_skills or existing.required_skills in ("[]", "null")) and record.get("required_skills"):
                existing.required_skills = json.dumps(record.get("required_skills") or [])
                updated = True
            if (not existing.top_pk_universities or existing.top_pk_universities in ("[]", "null")) and record.get("top_pk_universities"):
                existing.top_pk_universities = json.dumps(record.get("top_pk_universities") or [])
                updated = True
            if (not existing.risks or existing.risks in ("[]", "null")) and record.get("risks"):
                existing.risks = json.dumps(record.get("risks") or [])
                updated = True
            if existing.demand_level is None and record.get("demand_level"):
                existing.demand_level = record["demand_level"]
                updated = True
            if existing.competition_level is None and record.get("competition_level"):
                existing.competition_level = record["competition_level"]
                updated = True
            if existing.difficulty_level is None and record.get("difficulty_level"):
                existing.difficulty_level = record["difficulty_level"]
                updated = True
            if updated:
                backfilled += 1
            continue
        db.add(
            Career(
                slug=record["slug"],
                name=record["name"],
                field=record["field"],
                demand_level=record.get("demand_level"),
                competition_level=record.get("competition_level"),
                difficulty_level=record.get("difficulty_level"),
                required_skills=json.dumps(record.get("required_skills") or []),
                pk_opportunities=json.dumps(record.get("pk_opportunities") or []),
                top_pk_universities=json.dumps(record.get("top_pk_universities") or []),
                risks=json.dumps(record.get("risks") or []),
                category=record.get("category"),
                last_updated=datetime.fromisoformat(record["last_updated"]),
            )
        )
        inserted += 1
    db.commit()
    return inserted, skipped, backfilled


# ---------------------------------------------------------------------------
# Universities (manual-entry mode D: verified public facts)
# ---------------------------------------------------------------------------


def _seed_universities(db) -> tuple[int, int]:
    from models.university import University

    seed_file = ROOT / "data" / "seed" / "universities.json"
    if not seed_file.exists():
        return 0, 0
    records = json.loads(seed_file.read_text(encoding="utf-8"))["universities"]
    inserted, skipped = 0, 0
    for record in records:
        exists = (
            db.query(University).filter(University.slug == record["slug"]).first()
            is not None
        )
        if exists:
            skipped += 1
            continue
        db.add(
            University(
                name=record["name"],
                short_name=record.get("short_name"),
                slug=record["slug"],
                city=record.get("city"),
                province=record.get("province"),
                type=record.get("type"),
                hec_recognized=record.get("hec_recognized"),
                hec_category=record.get("hec_category"),
                website_url=record.get("website_url"),
                admissions_url=record.get("admissions_url"),
                verification_status=record.get("verification_status", "VERIFIED"),
                last_verified=_parse_date(record.get("last_verified")),
            )
        )
        inserted += 1
    db.commit()
    return inserted, skipped


# ---------------------------------------------------------------------------
# Programs (university_slug / career_slugs resolved at seed time)
# ---------------------------------------------------------------------------


def _seed_programs(db) -> tuple[int, int]:
    from models.career import Career
    from models.university import Program, University

    seed_file = ROOT / "data" / "seed" / "programs.json"
    if not seed_file.exists():
        return 0, 0
    records = json.loads(seed_file.read_text(encoding="utf-8"))["programs"]

    university_ids = {u.slug: u.id for u in db.query(University).all()}
    career_ids = {c.slug: c.id for c in db.query(Career).all()}

    inserted, skipped = 0, 0
    for record in records:
        university_id = university_ids.get(record["university_slug"])
        if university_id is None:
            print(f"  WARNING: program '{record['name']}' references unknown university slug '{record['university_slug']}' - skipped.")
            skipped += 1
            continue
        exists = (
            db.query(Program)
            .filter(
                Program.university_id == university_id,
                Program.name == record["name"],
            )
            .first()
            is not None
        )
        if exists:
            skipped += 1
            continue

        career_id_list = []
        for slug in record.get("career_slugs") or []:
            if slug in career_ids:
                career_id_list.append(career_ids[slug])
            else:
                print(f"  WARNING: program '{record['name']}' references unknown career slug '{slug}' - link skipped.")

        db.add(
            Program(
                university_id=university_id,
                name=record["name"],
                degree_type=record.get("degree_type"),
                field=record.get("field"),
                duration_years=record.get("duration_years"),
                annual_fee_pkr=record.get("annual_fee_pkr"),  # NULL = unknown, never guessed
                admission_link=record.get("admission_link"),
                career_ids=json.dumps(career_id_list),
                verification_status=record.get("verification_status", "VERIFIED"),
                last_verified=_parse_date(record.get("last_verified", "today")),
            )
        )
        inserted += 1
    db.commit()
    return inserted, skipped


# ---------------------------------------------------------------------------
# Learning resources (famous public resources)
# ---------------------------------------------------------------------------


def _seed_learning_resources(db) -> tuple[int, int]:
    from models.learning import LearningResource

    seed_file = ROOT / "data" / "seed" / "learning_resources.json"
    if not seed_file.exists():
        return 0, 0
    records = json.loads(seed_file.read_text(encoding="utf-8"))["learning_resources"]
    inserted, skipped = 0, 0
    for record in records:
        exists = (
            db.query(LearningResource)
            .filter(LearningResource.url == record["url"])
            .first()
            is not None
        )
        if exists:
            skipped += 1
            continue
        db.add(
            LearningResource(
                skill_name=record.get("skill_name"),
                title=record["title"],
                type=record.get("type"),
                provider=record.get("provider"),
                url=record["url"],
                language=record.get("language", "English"),
                level=record.get("level"),
                is_free=record.get("is_free"),
                duration_hours=record.get("duration_hours"),
                geographic_scope=record.get("geographic_scope"),
                verification_status=record.get("verification_status", "VERIFIED"),
                last_verified=_parse_date(record.get("last_verified", "today")),
            )
        )
        inserted += 1
    db.commit()
    return inserted, skipped


# ---------------------------------------------------------------------------
# Alumni (TEMPLATE records, is_verified=false)
# ---------------------------------------------------------------------------


def _seed_alumni(db) -> tuple[int, int]:
    from models.alumni import Alumni
    from models.career import Career
    from models.university import University

    seed_file = ROOT / "data" / "seed" / "alumni.json"
    if not seed_file.exists():
        return 0, 0
    records = json.loads(seed_file.read_text(encoding="utf-8"))["alumni"]

    university_ids = {u.slug: u.id for u in db.query(University).all()}
    career_ids = {c.slug: c.id for c in db.query(Career).all()}

    inserted, skipped = 0, 0
    for record in records:
        exists = (
            db.query(Alumni)
            .filter(Alumni.name == record["name"], Alumni.university == record.get("university"))
            .first()
            is not None
        )
        if exists:
            skipped += 1
            continue
        db.add(
            Alumni(
                name=record["name"],
                university=record.get("university"),
                university_id=university_ids.get(record.get("university_slug")),
                field=record.get("field"),
                role=record.get("role"),
                company=record.get("company"),
                career_id=career_ids.get(record.get("career_slug")),
                career_path=record.get("career_path"),
                advice=record.get("advice"),
                tags=json.dumps(record.get("tags") or []),
                is_verified=bool(record.get("is_verified", False)),
                source_url=record.get("source_url"),
            )
        )
        inserted += 1
    db.commit()
    return inserted, skipped


# ---------------------------------------------------------------------------
# Opportunities / sports opportunities (curated template data -> VALIDATED)
# ---------------------------------------------------------------------------


def _seed_opportunities(db) -> tuple[int, int]:
    """Insert opportunities from data/seed/opportunities.json (insert only)."""
    from models.opportunity import Opportunity

    seed_file = ROOT / "data" / "seed" / "opportunities.json"
    if not seed_file.exists():
        return 0, 0
    records = json.loads(seed_file.read_text(encoding="utf-8"))["opportunities"]
    return _insert_unique(
        db,
        records=records,
        exists=lambda rec: db.query(Opportunity)
        .filter(Opportunity.type == rec["type"], Opportunity.title == rec["title"])
        .first()
        is not None,
        build=lambda rec: Opportunity(
            type=rec["type"],
            title=rec["title"],
            organization=rec.get("organization"),
            location=rec.get("location"),
            deadline=_parse_date(rec.get("deadline")),
            required_skills=json.dumps(rec.get("required_skills") or []),
            description=rec.get("description"),
            source_url=rec.get("source_url"),
            last_verified=_parse_date(rec.get("last_verified")),
            is_active=bool(rec.get("is_active", True)),
            # Curated seed records are the database's validated data; records
            # created later through ingestion always start as CANDIDATE.
            verification_status=rec.get("verification_status", "VALIDATED"),
            field=rec.get("field"),
            province=rec.get("province"),
            is_remote=bool(rec.get("is_remote", False)),
            organization_type=rec.get("organization_type"),
            required_degree_type=rec.get("required_degree_type"),
        ),
    )


def _seed_sports_opportunities(db) -> tuple[int, int]:
    """Insert sports opportunities from data/seed/sports_opportunities.json."""
    from models.opportunity import SportsOpportunity

    seed_file = ROOT / "data" / "seed" / "sports_opportunities.json"
    if not seed_file.exists():
        return 0, 0
    records = json.loads(seed_file.read_text(encoding="utf-8"))["sports_opportunities"]
    return _insert_unique(
        db,
        records=records,
        exists=lambda rec: db.query(SportsOpportunity)
        .filter(
            SportsOpportunity.sport == rec["sport"],
            SportsOpportunity.title == rec["title"],
        )
        .first()
        is not None,
        build=lambda rec: SportsOpportunity(
            sport=rec["sport"],
            type=rec["type"],
            title=rec["title"],
            organization=rec.get("organization"),
            location=rec.get("location"),
            deadline=_parse_date(rec.get("deadline")),
            eligibility=json.dumps(rec.get("eligibility") or {}),
            description=rec.get("description"),
            source_url=rec.get("source_url"),
            last_verified=_parse_date(rec.get("last_verified")),
            is_active=bool(rec.get("is_active", True)),
            verification_status=rec.get("verification_status", "VALIDATED"),
        ),
    )


def _seed_pke_sources(db) -> tuple[int, int]:
    """Insert curated PKE sources from data/seed/pke_sources.json."""
    from knowledge_engine.pke_source_registry import PKESource

    seed_file = ROOT / "data" / "seed" / "pke_sources.json"
    if not seed_file.exists():
        return 0, 0
    records = json.loads(seed_file.read_text(encoding="utf-8"))["sources"]
    return _insert_unique(
        db,
        records=records,
        exists=lambda rec: db.query(PKESource)
        .filter(PKESource.source_id == rec["source_id"])
        .first()
        is not None,
        build=lambda rec: PKESource(
            source_id=rec["source_id"],
            name=rec["name"],
            base_url=rec["base_url"],
            authority_level=rec["authority_level"],
            source_type=rec["source_type"],
            domains=rec["domains"],
            geographic_scope=rec["geographic_scope"],
            access_review_status=rec["access_review_status"],
            retrieval_method=rec.get("retrieval_method"),
            has_official_api=bool(rec.get("has_official_api", False)),
            is_reachable=rec.get("is_reachable"),
            last_checked=_parse_date(rec.get("last_checked")),
            source_confidence=rec.get("source_confidence"),
            notes=rec.get("notes"),
            tos_review_url=rec.get("tos_review_url"),
        ),
    )


def _insert_unique(db, *, records, exists, build) -> tuple[int, int]:
    """Insert only records that are not already present (by the exists check)."""
    inserted, skipped = 0, 0
    for record in records:
        if exists(record):
            skipped += 1
            continue
        db.add(build(record))
        inserted += 1
    db.commit()
    return inserted, skipped


def _parse_date(value: str | None) -> date | None:
    """Seed date convention: 'today', '+N'/'-N' day offsets, or an ISO date."""
    if not value:
        return None
    if value == "today":
        return date.today()
    if value.startswith("+") or value.startswith("-"):
        return date.today() + timedelta(days=int(value))
    return date.fromisoformat(value)


def seed_if_empty() -> None:
    """Seed the database only if it is missing baseline data.

    Safe to call on every application startup. Runs from within the
    BackEnd/ working directory so the relative SQLite URL resolves to
    the same database the server uses. main() itself is insert-only and
    idempotent, so re-running it on a partially seeded database is safe.
    """
    backend = ROOT / "BackEnd"
    old_cwd = os.getcwd()
    try:
        os.chdir(backend)
        if str(backend) not in sys.path:
            sys.path.insert(0, str(backend))

        from database import SessionLocal  # noqa: E402
        from models.career import Career  # noqa: E402
        from models.university import University  # noqa: E402

        db = SessionLocal()
        try:
            careers_empty = db.query(Career).count() == 0
            universities_empty = db.query(University).count() == 0
            if careers_empty or universities_empty:
                print("Database is missing baseline data - running seed ...")
                main()
            else:
                pass  # data already present, nothing to do
        finally:
            db.close()
    finally:
        os.chdir(old_cwd)


if __name__ == "__main__":
    raise SystemExit(main())
