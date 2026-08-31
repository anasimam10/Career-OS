"""
Opportunities + Sports service (Phase 6, architecture §8).

Owns:
- GET  /opportunities listing (database only, no AI) with the §8 filters
       (type, city, field, skills)
- GET  /sports listing (database only, no AI) with the §8 filters
       (sport, city, type)
- POST /opportunities/match — Pattern B retrieval (Qwen -> MCP tools ->
       SQLite, reusing the Phase 5 mcp_search_service with its retry /
       deterministic-fallback policy) followed by DETERMINISTIC scoring in
       matching_service. Matches are cached in student_opportunity_matches.
- POST /sports/match — the same Pattern B flow over the sports tools; there
       is no persistence table for sports matches, so nothing is cached.

Trust hierarchy (§4/§9/§10): the AI only chooses which database records to
retrieve. Every score, reason, missing requirement, and next action is
computed in code from database values. When Qwen answers without grounded
tool results, its answer is discarded and the deterministic direct query
serves the records instead (never ungrounded AI content).
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from models.opportunity import Opportunity, SportsOpportunity, StudentOpportunityMatch
from models.student import Student
from repositories.student_repo import StudentRepository
from retrieval import visibility
from schemas.requests import OpportunityMatchRequest, SportsMatchRequest
from schemas.responses import (
    OpportunityMatchResponse,
    OpportunityOut,
    SportsMatchResponse,
    SportsOpportunityOut,
)
from services import matching_service, mcp_search_service

logger = logging.getLogger("ah_career.opportunities")

# The MVP uses the demo-student session context (architecture §8/§12).
# This ID matches Frontend/lib/session.ts (DEMO_STUDENT_ID = 1) and
# services/career_service.py.
DEMO_STUDENT_ID = 1

# Architecture §10 "No opportunities found" contract (verbatim).
NO_RESULTS_MESSAGE = (
    "No matching opportunities found in our database right now. "
    "Check back soon or explore related fields."
)

# The Mcp package lives at the repository root (main.py adds it to sys.path;
# this module keeps itself importable independently, e.g. from scripts).
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from Mcp.records import (  # noqa: E402
    city_matches,
    deadline_sort_key,
    opportunity_to_dict,
    parse_json,
    sports_opportunity_to_dict,
)


class StudentNotFoundError(Exception):
    """The demo student does not exist (onboarding has not been completed)."""


class InvalidRequestError(Exception):
    """A semantically invalid request value (e.g. a blank required field)."""


# ---------------------------------------------------------------------------
# Database-only listings (NO AI) — GET /opportunities, GET /sports
# ---------------------------------------------------------------------------


def list_opportunities(
    db: Session,
    *,
    opp_type: Optional[str] = None,
    city: Optional[str] = None,
    field: Optional[str] = None,
    skills: Optional[list[str]] = None,
) -> list[OpportunityOut]:
    """Active opportunity records, filtered per architecture §8 (DB only).

    Student-facing trust filters (master §11/§22) are applied through the
    shared retrieval visibility helpers: only VALIDATED/VERIFIED, active,
    non-expired records are ever listed.
    """
    query = visibility.apply_opportunity_visibility(db.query(Opportunity))
    if opp_type:
        query = query.filter(Opportunity.type == opp_type)
    rows = query.all()

    city_clean = (city or "").strip()
    if city_clean:
        rows = [o for o in rows if city_matches(o.location, city_clean)]

    skill_names = [s.strip().lower() for s in (skills or []) if s and s.strip()]
    if skill_names:
        rows = [
            o for o in rows if _skills_satisfied(parse_json(o.required_skills, []), skill_names)
        ]

    field_clean = (field or "").strip().lower()
    if field_clean:
        rows = [o for o in rows if _field_mentions(o, field_clean)]

    rows = sorted(rows, key=deadline_sort_key)
    items: list[OpportunityOut] = []
    for row in rows:
        record = opportunity_to_dict(row)
        record.pop("is_active", None)
        items.append(
            OpportunityOut(**record, data_freshness=matching_service.data_freshness(row.last_verified))
        )
    return items


def list_sports(
    db: Session,
    *,
    sport: Optional[str] = None,
    city: Optional[str] = None,
    sports_type: Optional[str] = None,
) -> list[SportsOpportunityOut]:
    """Active sports opportunity records, filtered per architecture §8 (DB only)."""
    query = visibility.apply_sports_visibility(db.query(SportsOpportunity))
    if sport:
        query = query.filter(SportsOpportunity.sport.ilike(sport.strip()))
    if sports_type:
        query = query.filter(SportsOpportunity.type == sports_type)
    rows = query.all()

    city_clean = (city or "").strip()
    if city_clean:
        rows = [s for s in rows if city_matches(s.location, city_clean)]

    rows = sorted(rows, key=deadline_sort_key)
    items: list[SportsOpportunityOut] = []
    for row in rows:
        record = sports_opportunity_to_dict(row)
        record.pop("is_active", None)
        items.append(
            SportsOpportunityOut(
                **record, data_freshness=matching_service.data_freshness(row.last_verified)
            )
        )
    return items


# ---------------------------------------------------------------------------
# AI matching (Pattern B retrieval + deterministic scoring)
# ---------------------------------------------------------------------------


def match_opportunities(db: Session, request: OpportunityMatchRequest) -> OpportunityMatchResponse:
    """
    AI-ranked opportunity matches for the student (architecture §8).

    Flow: Qwen retrieves records through the MCP opportunity server (Pattern
    B, with the Phase 5 retry/direct-fallback policy), then matching_service
    scores every record deterministically and the ranked list is cached in
    student_opportunity_matches.

    Raises:
        StudentNotFoundError  -- demo student missing (complete onboarding).
        InvalidRequestError   -- blank city.
        AIUnavailableError    -- both MCP attempts failed AND no fallback.
    """
    student = _get_student(db)

    city = (request.city or "").strip()
    if not city:
        raise InvalidRequestError("city must be a non-empty string.")
    opp_type = request.opportunity_type

    skills = _clean_request_skills(request.skills) or _profile_skill_names(db, student.id)

    question = _build_opportunity_question(opp_type, city, skills, request.field)

    if opp_type == "internship":
        fallback_tool = "search_internships"
        fallback_arguments = {
            "skills": skills or None,
            "city": city,
            "field": (request.field or "").strip(),
        }
    else:
        fallback_tool = "search_jobs"
        fallback_arguments = {
            "skills": skills or None,
            "city": city,
            "experience_level": "",
        }

    result = mcp_search_service.search_with_mcp(
        question,
        "opportunity",
        fallback_tool=fallback_tool,
        fallback_arguments=fallback_arguments,
        operation="opportunity_match",
    )

    response = _score_opportunity_result(result, skills, city, fallback_tool, fallback_arguments)

    if not response.matches:
        response.message = NO_RESULTS_MESSAGE
        return response

    _persist_opportunity_matches(db, student.id, response.matches)
    logger.info(
        "Opportunity match: student=%s type=%s city=%s quality=%s matches=%s",
        student.id, opp_type, city, response.data_quality, len(response.matches),
    )
    return response


def match_sports(db: Session, request: SportsMatchRequest) -> SportsMatchResponse:
    """
    Match the student to relevant sports opportunities (architecture §8).

    Same Pattern B flow as match_opportunities, evaluated against the
    request's {sport, location, level} and the student's education stage.
    There is no persistence table for sports matches, so nothing is cached.

    Raises:
        StudentNotFoundError  -- demo student missing (complete onboarding).
        InvalidRequestError   -- blank sport.
        AIUnavailableError    -- both MCP attempts failed AND no fallback.
    """
    student = _get_student(db)

    sport = (request.sport or "").strip()
    if not sport:
        raise InvalidRequestError("sport must be a non-empty string.")
    location = (request.location or "").strip() or None
    level = (request.level or "").strip() or None

    question = _build_sports_question(sport, location, level)
    fallback_arguments = {"sport": sport, "city": location or ""}

    result = mcp_search_service.search_with_mcp(
        question,
        "opportunity",
        fallback_tool="search_sports_opportunities",
        fallback_arguments=fallback_arguments,
        operation="sports_match",
    )

    response = _score_sports_result(
        result, level, location, student.education_stage, fallback_arguments
    )

    if not response.matches:
        response.message = NO_RESULTS_MESSAGE
        return response

    logger.info(
        "Sports match: student=%s sport=%s location=%s level=%s quality=%s matches=%s",
        student.id, sport, location, level, response.data_quality, len(response.matches),
    )
    return response


# ---------------------------------------------------------------------------
# Scoring orchestration over a search_with_mcp result
# ---------------------------------------------------------------------------


def _score_opportunity_result(
    result: dict, skills: list[str], city: str, fallback_tool: str, fallback_arguments: dict
) -> OpportunityMatchResponse:
    """Turn one search_with_mcp result into scored, ordered matches."""
    if result.get("data_quality") == "ai_interpreted":
        records = _records_from_tool_calls(result.get("tool_calls"))
        if records:
            matches = [
                matching_service.score_opportunity(record, skills, city) for record in records
            ]
            matches = matching_service.sort_opportunity_matches(matches)
            return OpportunityMatchResponse(
                matches=matches,
                data_quality="ai_interpreted",
                summary=result.get("answer"),
            )
        # Qwen answered without grounded tool results — discard the answer
        # and serve the deterministic direct query instead (§4 trust rules).
        logger.warning(
            "Opportunity match produced no grounded tool results — "
            "using the deterministic direct query."
        )
        records = _direct_records(fallback_tool, fallback_arguments)
        matches = [matching_service.score_opportunity(record, skills, city) for record in records]
        return OpportunityMatchResponse(
            matches=matches,
            data_quality="unranked",
            note=mcp_search_service.FALLBACK_NOTE,
        )

    # Deterministic direct-database fallback (Phase 5 policy).
    tool_output = result.get("results") or {}
    records = tool_output.get("results", []) if isinstance(tool_output, dict) else []
    matches = [matching_service.score_opportunity(record, skills, city) for record in records]
    return OpportunityMatchResponse(
        matches=matches,
        data_quality="unranked",
        note=result.get("note"),
    )


def _score_sports_result(
    result: dict,
    level: Optional[str],
    location: Optional[str],
    student_stage: Optional[str],
    fallback_arguments: dict,
) -> SportsMatchResponse:
    """Turn one search_with_mcp result into scored sports matches."""
    if result.get("data_quality") == "ai_interpreted":
        records = _records_from_tool_calls(result.get("tool_calls"))
        if records:
            matches = [
                matching_service.score_sports_opportunity(record, level, location, student_stage)
                for record in records
            ]
            matches = matching_service.sort_sports_matches(matches)
            return SportsMatchResponse(
                matches=matches,
                data_quality="ai_interpreted",
                summary=result.get("answer"),
            )
        logger.warning(
            "Sports match produced no grounded tool results — "
            "using the deterministic direct query."
        )
        records = _direct_records("search_sports_opportunities", fallback_arguments)
        matches = [
            matching_service.score_sports_opportunity(record, level, location, student_stage)
            for record in records
        ]
        return SportsMatchResponse(
            matches=matches,
            data_quality="unranked",
            note=mcp_search_service.FALLBACK_NOTE,
        )

    tool_output = result.get("results") or {}
    records = tool_output.get("results", []) if isinstance(tool_output, dict) else []
    matches = [
        matching_service.score_sports_opportunity(record, level, location, student_stage)
        for record in records
    ]
    return SportsMatchResponse(
        matches=matches,
        data_quality="unranked",
        note=result.get("note"),
    )


# ---------------------------------------------------------------------------
# Persistence (student_opportunity_matches cache, §7)
# ---------------------------------------------------------------------------


def _persist_opportunity_matches(db: Session, student_id: int, matches) -> None:
    """
    Replace the student's cached opportunity matches (cache semantics).

    Persistence is a cache: a failure here must never fail the request, so
    errors are logged and swallowed.
    """
    try:
        db.query(StudentOpportunityMatch).filter(
            StudentOpportunityMatch.student_id == student_id
        ).delete(synchronize_session=False)
        for match in matches:
            db.add(
                StudentOpportunityMatch(
                    student_id=student_id,
                    opportunity_id=match.opportunity_id,
                    match_score=match.match_score,
                    missing_requirements=json.dumps(
                        match.missing_requirements, ensure_ascii=False
                    ),
                    next_action=match.next_action,
                )
            )
        db.commit()
    except Exception:
        db.rollback()
        logger.warning(
            "Could not cache opportunity matches for student %s",
            student_id,
            exc_info=True,
        )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_student(db: Session) -> Student:
    student = db.get(Student, DEMO_STUDENT_ID)
    if student is None:
        raise StudentNotFoundError(DEMO_STUDENT_ID)
    return student


def _profile_skill_names(db: Session, student_id: int) -> list[str]:
    """Skill names from the student's stored profile ([{name, level}, ...])."""
    profile = StudentRepository(db).get_profile(student_id)
    if profile is None:
        return []
    names: list[str] = []
    for item in _loads(profile.skills):
        if isinstance(item, dict) and item.get("name"):
            names.append(str(item["name"]))
        elif isinstance(item, str) and item.strip():
            names.append(item.strip())
    return names


def _clean_request_skills(skills: Optional[list[str]]) -> list[str]:
    return [s.strip() for s in (skills or []) if s and s.strip()]


def _build_opportunity_question(
    opp_type: str, city: str, skills: list[str], field: Optional[str]
) -> str:
    question = f"Find {opp_type} opportunities in {city}, Pakistan, for a student"
    if skills:
        question += " who already knows these skills: " + ", ".join(skills)
    if field and field.strip():
        question += f", interested in the {field.strip()} field"
    return question + "."


def _build_sports_question(sport: str, location: Optional[str], level: Optional[str]) -> str:
    question = f"Find {sport} sports opportunities"
    if location:
        question += f" in {location}"
    if level:
        question += f" for a {level}-level player"
    return question + "."


def _records_from_tool_calls(tool_calls: Optional[list]) -> list[dict]:
    """Dedupe the database records behind Qwen's grounded tool calls (by id)."""
    records: list[dict] = []
    seen: set = set()
    for call in tool_calls or []:
        if not isinstance(call, dict):
            continue
        result = call.get("result")
        if not isinstance(result, dict):
            continue
        for record in result.get("results") or []:
            if (
                isinstance(record, dict)
                and record.get("id") is not None
                and record["id"] not in seen
            ):
                seen.add(record["id"])
                records.append(record)
    return records


def _direct_records(tool_name: str, arguments: dict) -> list[dict]:
    """
    Deterministic direct database query through the MCP tool function
    itself — the identical query without the transport (Phase 5 pattern).
    """
    output = mcp_search_service.FALLBACK_TOOLS[tool_name](**arguments)
    return output.get("results", []) if isinstance(output, dict) else []


def _skills_satisfied(required: list, student_skills: list[str]) -> bool:
    """
    Same deterministic rule as the Phase 5 MCP search tools: a record
    matches when the student already has at least one of the required
    skills, or when the record lists no required skills.
    """
    if not required:
        return True
    normalized = [str(skill).strip().lower() for skill in required]
    return any(skill in student_skills for skill in normalized)


def _field_mentions(record, needle: str) -> bool:
    """Field filter: the title, description, or organization mentions it."""
    return (
        needle in (record.title or "").lower()
        or needle in (record.description or "").lower()
        or needle in (record.organization or "").lower()
    )


def _loads(raw: Optional[str]) -> list:
    if raw is None:
        return []
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return []
