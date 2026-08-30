"""
Seed the SQLite database from data/seed/*.json.

Usage (from the repository root):

    python data/seed_db.py

Behaviour:
- Creates any missing tables.
- Inserts careers from data/seed/careers.json. Existing careers are NEVER
  overwritten — records already in the database are skipped and reported.
- Inserts opportunities from data/seed/opportunities.json and sports
  opportunities from data/seed/sports_opportunities.json (Phase 5, MCP).
  Existing records (same type + title) are skipped, never overwritten.
- Creates the demo student (id=1, matching Frontend/lib/session.ts and the
  architecture's demo-student session context) if it does not exist yet.

The seed data is TEMPLATE data converted from the frontend mock — it is not
independently verified Pakistani data (see the _meta block in careers.json).
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    backend = ROOT / "BackEnd"
    seed_file = ROOT / "data" / "seed" / "careers.json"

    # The backend runs from inside BackEnd/ (uvicorn main:app); run the seeder
    # with the same working directory so the relative SQLite URL resolves
    # to the same database file the server uses.
    os.chdir(backend)
    sys.path.insert(0, str(backend))

    from database import SessionLocal, init_db  # noqa: E402
    from models.career import Career  # noqa: E402
    from repositories.student_repo import StudentRepository  # noqa: E402

    init_db()

    payload = json.loads(seed_file.read_text(encoding="utf-8"))
    careers = payload["careers"]

    db = SessionLocal()
    try:
        # --- careers (insert only — never overwrite existing records) -----
        inserted, skipped = 0, 0
        for record in careers:
            exists = db.query(Career).filter(Career.slug == record["slug"]).first()
            if exists is not None:
                skipped += 1
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
                    last_updated=datetime.fromisoformat(record["last_updated"]),
                )
            )
            inserted += 1
        db.commit()

        # --- opportunities (insert only — never overwrite existing) ---------
        opp_inserted, opp_skipped = _seed_opportunities(db)
        sports_inserted, sports_skipped = _seed_sports_opportunities(db)

        # --- demo student (id=1, per Frontend/lib/session.ts) --------------
        student_repo = StudentRepository(db)
        demo_student = student_repo.get_by_id(1)
        demo_created = False
        if demo_student is None:
            student_repo.create_with_profile(
                name="Demo Student",
                email="demo@ah-careers.local",
                password_hash="demo-no-auth-mvp",  # demo context only — no auth yet
                education_stage="HIGH_SCHOOL",
                career_goal="Software Engineering",
                sports_interest="Cricket",
                motivation_tags=json.dumps(
                    ["I genuinely love this subject", "High salary potential"]
                ),
            )
            student_repo.update_profile(
                1,
                interests=json.dumps(["Technology", "Mathematics"]),
                skills=json.dumps([{"name": "Python", "level": "beginner"}]),
            )
            demo_created = True
    finally:
        db.close()

    print(f"Careers: {inserted} inserted, {skipped} skipped (already present).")
    print(f"Opportunities: {opp_inserted} inserted, {opp_skipped} skipped (already present).")
    print(f"Sports opportunities: {sports_inserted} inserted, {sports_skipped} skipped (already present).")
    print(f"Demo student (id=1): {'created' if demo_created else 'already present'}.")
    print("Done. Note: seed data is TEMPLATE data, not independently verified.")
    return 0


# ---------------------------------------------------------------------------
# Opportunity / sports seeders (Phase 5 — MCP tools)
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
    if not value:
        return None
    return date.fromisoformat(value)


def seed_if_empty() -> None:
    """Seed the database only if the careers table is empty.

    Safe to call on every application startup.  Runs from within the
    BackEnd/ working directory so the relative SQLite URL resolves to
    the same database the server uses.
    """
    backend = ROOT / "BackEnd"
    old_cwd = os.getcwd()
    try:
        os.chdir(backend)
        if str(backend) not in sys.path:
            sys.path.insert(0, str(backend))

        from database import SessionLocal  # noqa: E402
        from models.career import Career  # noqa: E402

        db = SessionLocal()
        try:
            if db.query(Career).count() == 0:
                print("Database is empty — running seed …")
                main()
            else:
                pass  # data already present, nothing to do
        finally:
            db.close()
    finally:
        os.chdir(old_cwd)


if __name__ == "__main__":
    raise SystemExit(main())
