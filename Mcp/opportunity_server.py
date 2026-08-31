"""
Pakistan Opportunities, Sports, Alumni & Learning MCP server (Phase 5,
Server 2 of 2).

Eight read-only tools exposing the project's SQLite data over the MCP
protocol (SSE transport, mounted at /mcp/opportunity in BackEnd/main.py):
opportunity search/matching, sports search, alumni journeys, and learning
resources. The alumni and learning tools (master §16) reuse the Phase 2
retrieval layer — no duplicate query logic.

Data-trust rule (spec §4/§10): every value returned by these tools comes
from the database or is a deterministic derivation of database values.
Inactive records are excluded everywhere. The tools never invent
opportunities, deadlines, organizations, or URLs, and never call
external services.

match_opportunity reuses the project's existing deterministic matching
approach (skill overlap, mirroring the roadmap/candidate services'
missing-skill logic) over the database's own required_skills column.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Bootstrap the BackEnd package on sys.path (same approach as data/seed_db.py)
_BACKEND_DIR = Path(__file__).resolve().parents[1] / "BackEnd"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from mcp.server.mcpserver import MCPServer

from Mcp.db_access import get_session
from Mcp.records import (
    NO_RESULTS_MESSAGE,
    city_matches,
    deadline_sort_key,
    opportunity_to_dict,
    parse_json,
    sports_opportunity_to_dict,
)
from models.opportunity import Opportunity, SportsOpportunity
from retrieval import alumni_retrieval, learning_retrieval, visibility

opportunity_server = MCPServer(
    name="pakistan_opportunity",
    instructions=(
        "Pakistan Opportunities & Sports server. Read-only search over the "
        "A&H Careers verified database: internships, jobs, scholarships, "
        "sports tournaments, trials, university sports programmes, alumni "
        "career journeys, and learning resources. All data comes from the "
        "project database — never external sources. When no records match, "
        "say so plainly; never invent opportunities."
    ),
)


def _invalid_input(message: str) -> dict:
    """Controlled result for invalid tool input (never raises)."""
    return {"error": "invalid_input", "message": message}


def _clean_skills(skills: list[str] | str | None) -> list[str]:
    """Normalize a skills argument to a list of lowercase trimmed names."""
    if skills is None:
        return []
    if isinstance(skills, str):
        skills = [s for s in skills.split(",")]
    cleaned = []
    for skill in skills:
        if isinstance(skill, str) and skill.strip():
            cleaned.append(skill.strip().lower())
    return cleaned


def _skill_matches(required: list[str], student_skills: list[str]) -> bool:
    """
    Deterministic match rule (mirrors the roadmap/candidate services):
    an opportunity matches when the student already has at least one of
    the required skills, or when the record lists no required skills.
    Comparison is case-insensitive (student skills arrive lowercased).
    """
    if not required:
        return True
    normalized = [skill.strip().lower() for skill in required]
    return any(skill in student_skills for skill in normalized)


def _filter_by_field(rows: list[Opportunity], field: str) -> list[Opportunity]:
    """Filter opportunities whose title/description mention the field."""
    needle = field.strip().lower()
    if not needle:
        return rows
    return [
        o
        for o in rows
        if needle in (o.title or "").lower()
        or needle in (o.description or "").lower()
        or needle in (o.organization or "").lower()
    ]


def _search_opportunities(
    *,
    opp_type: str,
    skills: list[str] | None = None,
    city: str = "",
    field: str = "",
    experience_level: str = "",
) -> list[Opportunity]:
    """Shared deterministic search: student-visible records of a type, city/skill filtered.

    Student-facing trust filters (master §11/§22): VALIDATED/VERIFIED,
    active, and non-expired records only.
    """
    session = get_session()
    try:
        rows = visibility.apply_opportunity_visibility(
            session.query(Opportunity).filter(Opportunity.type == opp_type)
        ).all()
    finally:
        session.close()

    city_clean = (city or "").strip()
    if city_clean:
        rows = [o for o in rows if city_matches(o.location, city_clean)]

    student_skills = _clean_skills(skills)
    if student_skills:
        rows = [
            o
            for o in rows
            if _skill_matches(parse_json(o.required_skills, []), student_skills)
        ]

    field_clean = (field or "").strip()
    if field_clean:
        rows = _filter_by_field(rows, field_clean)

    level_clean = (experience_level or "").strip().lower()
    if level_clean:
        rows = [
            o
            for o in rows
            if level_clean in (o.description or "").lower()
            or level_clean in (o.title or "").lower()
        ]

    return sorted(rows, key=deadline_sort_key)


def _wrap_results(
    records: list[dict],
    message: str = NO_RESULTS_MESSAGE,
    **extra,
) -> dict:
    """Build a safe search result; empty results carry an explicit message."""
    result = {"count": len(records), **extra}
    if records:
        result["results"] = records
    else:
        result["results"] = []
        result["message"] = message
    return result


NO_ALUMNI_MESSAGE = "No matching alumni journeys found in our database right now."
NO_RESOURCES_MESSAGE = "No matching learning resources found in our database right now."


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@opportunity_server.tool()
def search_internships(
    skills: list[str] | None = None, city: str = "", field: str = ""
) -> dict:
    """Search active internship records in the database, filtered by skills, city, and field."""
    city_clean = (city or "").strip()
    if not city_clean:
        return _invalid_input("city must be a non-empty string.")
    rows = _search_opportunities(
        opp_type="internship", skills=skills, city=city_clean, field=field
    )
    return _wrap_results(
        [opportunity_to_dict(o) for o in rows],
        city=city_clean,
        search_type="internship",
    )


@opportunity_server.tool()
def search_jobs(
    skills: list[str] | None = None, city: str = "", experience_level: str = ""
) -> dict:
    """Search active job records in the database, filtered by skills, city, and experience level."""
    city_clean = (city or "").strip()
    if not city_clean:
        return _invalid_input("city must be a non-empty string.")
    rows = _search_opportunities(
        opp_type="job",
        skills=skills,
        city=city_clean,
        experience_level=experience_level,
    )
    return _wrap_results(
        [opportunity_to_dict(o) for o in rows],
        city=city_clean,
        search_type="job",
    )


@opportunity_server.tool()
def match_opportunity(student_profile: dict, opportunity_id: int) -> dict:
    """Deterministically match a student profile against one opportunity: score, matching reasons, missing requirements, next action."""
    if not isinstance(opportunity_id, int) or opportunity_id <= 0:
        return _invalid_input("opportunity_id must be a positive integer.")
    if not isinstance(student_profile, dict) or not student_profile:
        return _invalid_input(
            "student_profile must be a non-empty object with the student's skills."
        )

    session = get_session()
    try:
        opportunity = session.get(Opportunity, opportunity_id)
        if opportunity is None or not visibility.is_opportunity_visible(opportunity):
            return {
                "error": "not_found",
                "message": (
                    f"Opportunity {opportunity_id} was not found in the active "
                    "opportunities database."
                ),
            }
        record = opportunity_to_dict(opportunity)
    finally:
        session.close()

    # Student skills: accepts {"skills": ["Python", ...]} or a skills list
    raw_skills = student_profile.get("skills")
    if isinstance(raw_skills, dict):
        raw_skills = raw_skills.get("skills")
    student_skills = _clean_skills(raw_skills)

    # Keep the database's original casing for display; compare lowercased.
    required = list(record["required_skills"] or [])
    matched = [s for s in required if s.lower() in student_skills]
    missing = [s for s in required if s.lower() not in student_skills]

    if required:
        score = round(len(matched) / len(required), 2)
    else:
        score = 1.0  # no listed requirements — nothing blocking

    reasons = []
    if matched:
        reasons.append(f"Student already has {len(matched)} of the required skills: " + ", ".join(matched))
    if not required:
        reasons.append("The opportunity lists no specific required skills.")
    if missing:
        reasons.append(f"Missing {len(missing)} required skills: " + ", ".join(missing))

    if score == 1.0:
        next_action = (
            "All listed requirements are met — prepare an application "
            f"before the deadline ({record['deadline'] or 'see source'})."
        )
    elif matched:
        next_action = (
            "Partially matched — build the missing skills ("
            + ", ".join(missing)
            + ") while preparing an application."
        )
    else:
        next_action = (
            "None of the listed required skills are in the profile yet — "
            "start with: " + ", ".join(missing) + "."
        )

    return {
        "opportunity_id": record["id"],
        "title": record["title"],
        "match_score": score,
        "matching_reasons": reasons,
        "missing_requirements": missing,
        "next_action": next_action,
    }


@opportunity_server.tool()
def search_sports_opportunities(sport: str, city: str = "") -> dict:
    """Search active sports opportunity records (tournaments, trials, programmes, scholarships) by sport and city."""
    sport_clean = (sport or "").strip()
    if not sport_clean:
        return _invalid_input("sport must be a non-empty string.")
    city_clean = (city or "").strip()

    session = get_session()
    try:
        rows = visibility.apply_sports_visibility(
            session.query(SportsOpportunity).filter(
                SportsOpportunity.sport.ilike(sport_clean)
            )
        ).all()
    finally:
        session.close()

    if city_clean:
        rows = [s for s in rows if city_matches(s.location, city_clean)]
    rows = sorted(rows, key=deadline_sort_key)

    return _wrap_results(
        [sports_opportunity_to_dict(s) for s in rows],
        sport=sport_clean,
        city=city_clean or None,
    )


@opportunity_server.tool()
def search_sports_scholarships(sport: str, level: str = "") -> dict:
    """Search active sports scholarship records by sport and optional skill level."""
    sport_clean = (sport or "").strip()
    if not sport_clean:
        return _invalid_input("sport must be a non-empty string.")
    level_clean = (level or "").strip().lower()

    session = get_session()
    try:
        rows = visibility.apply_sports_visibility(
            session.query(SportsOpportunity).filter(
                SportsOpportunity.sport.ilike(sport_clean)
            )
        ).all()
    finally:
        session.close()

    scholarships = [s for s in rows if s.type == "scholarship"]
    if level_clean:
        scholarships = [
            s
            for s in scholarships
            if level_clean
            in (parse_json(s.eligibility, {}).get("level") or "").lower()
        ]
    scholarships = sorted(scholarships, key=deadline_sort_key)

    return _wrap_results(
        [sports_opportunity_to_dict(s) for s in scholarships],
        sport=sport_clean,
        level=level_clean or None,
    )


@opportunity_server.tool()
def search_university_sports(sport: str, city: str = "") -> dict:
    """Search active university sports programme records by sport and city."""
    sport_clean = (sport or "").strip()
    if not sport_clean:
        return _invalid_input("sport must be a non-empty string.")
    city_clean = (city or "").strip()

    session = get_session()
    try:
        rows = visibility.apply_sports_visibility(
            session.query(SportsOpportunity).filter(
                SportsOpportunity.sport.ilike(sport_clean)
            )
        ).all()
    finally:
        session.close()

    programmes = [s for s in rows if s.type == "programme"]
    if city_clean:
        programmes = [s for s in programmes if city_matches(s.location, city_clean)]
    programmes = sorted(programmes, key=deadline_sort_key)

    return _wrap_results(
        [sports_opportunity_to_dict(s) for s in programmes],
        sport=sport_clean,
        city=city_clean or None,
    )


@opportunity_server.tool()
def find_alumni(
    field: str, career_id: int | None = None, university_id: int | None = None
) -> dict:
    """Find alumni career journeys in a field, optionally narrowed by career or university id (verified journeys first)."""
    field_clean = (field or "").strip()
    if not field_clean:
        return _invalid_input("field must be a non-empty string.")
    if career_id is not None and (not isinstance(career_id, int) or career_id <= 0):
        return _invalid_input("career_id must be a positive integer.")
    if university_id is not None and (
        not isinstance(university_id, int) or university_id <= 0
    ):
        return _invalid_input("university_id must be a positive integer.")

    # Reuses the retrieval layer (master §16: no duplicate query logic).
    # Verified journeys are ordered first; each record carries is_verified
    # so unverified (community/template) journeys are labeled honestly.
    session = get_session()
    try:
        records = alumni_retrieval.find_alumni(
            session,
            field=field_clean,
            career_id=career_id,
            university_id=university_id,
        )
    finally:
        session.close()

    return _wrap_results(
        records,
        message=NO_ALUMNI_MESSAGE,
        field=field_clean,
        career_id=career_id,
        university_id=university_id,
    )


@opportunity_server.tool()
def get_learning_resources(skill: str, level: str = "") -> dict:
    """Find verified learning resources for a skill, optionally filtered by level (beginner/intermediate/advanced)."""
    skill_clean = (skill or "").strip()
    if not skill_clean:
        return _invalid_input("skill must be a non-empty string.")
    level_clean = (level or "").strip()

    # Reuses the retrieval layer (master §16): VALIDATED/VERIFIED + active
    # records only; records with a NULL level match every level filter.
    session = get_session()
    try:
        records = learning_retrieval.get_resources_for_skill(
            session, skill_clean, level=level_clean or None
        )
    finally:
        session.close()

    return _wrap_results(
        records,
        message=NO_RESOURCES_MESSAGE,
        skill=skill_clean,
        level=level_clean or None,
    )
