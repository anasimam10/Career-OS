"""
Pakistan Career & Education MCP server (Phase 5, Server 1 of 2).

Five read-only tools exposing the project's SQLite career data over the
MCP protocol (SSE transport, mounted at /mcp/career in BackEnd/main.py).

Data-trust rule (spec §4/§10): every value returned by these tools comes
from the database or is a deterministic derivation of database values.
The tools never invent careers, metrics, universities, scholarships,
deadlines, or URLs, and never call external services.

The tool functions are plain Python functions — they are registered with
the MCP server through the decorator but remain directly callable, which
is how the deterministic fallback path reuses the exact same queries.
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
)
from models.career import Career
from models.opportunity import Opportunity
from repositories.career_repo import CareerRepository
from services.career_service import CAREER_DATA_SOURCE_LABEL, UNKNOWN_METRIC

career_server = MCPServer(
    name="pakistan_career",
    instructions=(
        "Pakistan Career & Education server. Read-only lookups over the "
        "A&H Careers verified database: career records, career reality data "
        "(demand, competition, difficulty, risks), required skills, "
        "university opportunities, and scholarships. All data comes from "
        "the project database — never external sources."
    ),
)

# Deterministic stage focus for get_required_skills (spec §5): how much of
# the database skill list a student should focus on per education stage.
_STAGE_SKILL_FOCUS = {
    "HIGH_SCHOOL": 2,
    "CAREER_DISCOVERY": 2,
    "CAREER_DECISION": "half",
    "UNIVERSITY": "half",
    "SKILL_BUILDING": "half",
    "PROJECTS": "all",
    "INTERNSHIP": "all",
    "FINAL_YEAR": "all",
    "JOB_PREPARATION": "all",
    "FIRST_JOB": "all",
}


def _invalid_input(message: str) -> dict:
    """Controlled result for invalid tool input (never raises)."""
    return {"error": "invalid_input", "message": message}


def _career_not_found(slug: str) -> dict:
    """Controlled not-found result listing the careers that DO exist."""
    session = get_session()
    try:
        available = [
            c.slug for c in session.query(Career).order_by(Career.slug).all()
        ]
    finally:
        session.close()
    return {
        "found": False,
        "message": f"Career '{slug}' was not found in the A&H Careers database.",
        "available_careers": available,
    }


def _load_career(slug: str):
    """Load a career as a dict, or None when the slug is unknown."""
    session = get_session()
    try:
        career = CareerRepository(session).get_by_slug(slug)
        if career is None:
            return None
        return CareerRepository(session).to_dict(career)
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@career_server.tool()
def get_career(slug: str) -> dict:
    """Get a full career record (name, field, demand, skills, universities, risks) by slug."""
    cleaned = (slug or "").strip()
    if not cleaned:
        return _invalid_input("slug must be a non-empty string.")
    career = _load_career(cleaned)
    if career is None:
        return _career_not_found(cleaned)
    return {"found": True, "career": career}


@career_server.tool()
def get_career_reality(slug: str) -> dict:
    """Career reality data: demand, competition, difficulty, required skills, Pakistan opportunities, risks, and the data source."""
    cleaned = (slug or "").strip()
    if not cleaned:
        return _invalid_input("slug must be a non-empty string.")
    career = _load_career(cleaned)
    if career is None:
        return _career_not_found(cleaned)

    updated = career.get("last_updated")
    if updated:
        data_source = f"{CAREER_DATA_SOURCE_LABEL}, last updated {updated[:10]}"
    else:
        data_source = CAREER_DATA_SOURCE_LABEL

    return {
        "found": True,
        "career_name": career["name"],
        "demand_level": career["demand_level"] or UNKNOWN_METRIC,
        "competition_level": career["competition_level"] or UNKNOWN_METRIC,
        "difficulty_level": career["difficulty_level"] or UNKNOWN_METRIC,
        "required_skills": career["required_skills"],
        "pk_opportunities": career["pk_opportunities"],
        "risks": career["risks"],
        "data_source": data_source,
    }


@career_server.tool()
def get_required_skills(career_slug: str, stage: str = "") -> dict:
    """Required skills for a career with a deterministic study focus for the student's education stage."""
    cleaned = (career_slug or "").strip()
    if not cleaned:
        return _invalid_input("career_slug must be a non-empty string.")
    stage_clean = (stage or "").strip().upper()

    career = _load_career(cleaned)
    if career is None:
        return _career_not_found(cleaned)

    skills = career["required_skills"]
    if stage_clean in _STAGE_SKILL_FOCUS:
        rule = _STAGE_SKILL_FOCUS[stage_clean]
        if rule == "all" or len(skills) <= 1:
            focus = list(skills)
            focus_note = "At this stage, work through all of the listed skills."
        elif rule == "half":
            half = max(1, len(skills) // 2)
            focus = skills[:half]
            focus_note = (
                f"At this stage, focus on the first {half} of the "
                f"{len(skills)} listed skills."
            )
        else:
            focus = skills[: rule]
            focus_note = (
                f"Begin with the first {min(rule, len(skills))} of the "
                f"{len(skills)} listed skills at this stage."
            )
    elif stage_clean:
        focus = list(skills)
        focus_note = (
            "Unknown education stage — the full skill list is returned."
        )
    else:
        focus = list(skills)
        focus_note = "No stage provided — the full skill list is returned."

    return {
        "found": True,
        "career_slug": career["slug"],
        "career_name": career["name"],
        "stage": stage_clean or None,
        "required_skills": skills,
        "focus_skills": focus,
        "focus_note": focus_note,
        "note": "Skill order follows the database record.",
    }


@career_server.tool()
def get_university_opportunities(field: str, city: str) -> dict:
    """University opportunity records and career-linked universities for a study field and city. Returns only database records."""
    field_clean = (field or "").strip()
    city_clean = (city or "").strip()
    if not field_clean or not city_clean:
        return _invalid_input("field and city must be non-empty strings.")

    session = get_session()
    try:
        # University programme records (type "education") in the city or nationwide
        programmes = (
            session.query(Opportunity)
            .filter(Opportunity.is_active.is_(True), Opportunity.type == "education")
            .all()
        )
        programmes = [o for o in programmes if city_matches(o.location, city_clean)]
        programmes = sorted(programmes, key=deadline_sort_key)
        university_programmes = [opportunity_to_dict(o) for o in programmes]

        # Universities linked to careers in this field (database column)
        careers = session.query(Career).order_by(Career.name).all()
        needle = field_clean.lower()
        matching = [c for c in careers if c.field and c.field.lower() == needle]
        if not matching:
            matching = [
                c for c in careers if c.field and needle in c.field.lower()
            ]
        universities_for_field = [
            {
                "career": c.name,
                "field": c.field,
                "universities": parse_json(c.top_pk_universities, []),
            }
            for c in matching
        ]
    finally:
        session.close()

    count = len(university_programmes) + sum(
        len(u["universities"]) for u in universities_for_field
    )
    result = {
        "field": field_clean,
        "city": city_clean,
        "university_programmes": university_programmes,
        "universities_for_field": universities_for_field,
        "count": count,
    }
    if count == 0:
        result["message"] = NO_RESULTS_MESSAGE
    return result


@career_server.tool()
def get_scholarships(criteria: str = "") -> dict:
    """Search scholarship records stored in the database. Optional criteria matched against title, organization, or description."""
    criteria_clean = (criteria or "").strip()

    session = get_session()
    try:
        rows = (
            session.query(Opportunity)
            .filter(Opportunity.is_active.is_(True), Opportunity.type == "scholarship")
            .all()
        )
        if criteria_clean:
            needle = criteria_clean.lower()
            rows = [
                o
                for o in rows
                if needle in (o.title or "").lower()
                or needle in (o.organization or "").lower()
                or needle in (o.description or "").lower()
            ]
        rows = sorted(rows, key=deadline_sort_key)
    finally:
        session.close()

    scholarships = [opportunity_to_dict(o) for o in rows]
    result = {
        "criteria": criteria_clean,
        "count": len(scholarships),
        "scholarships": scholarships,
    }
    if not scholarships:
        result["message"] = NO_RESULTS_MESSAGE
    return result
