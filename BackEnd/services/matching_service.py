"""
Deterministic match score logic (Phase 6, architecture §11: matching_service).

This module is PURE: every function works on already-retrieved record dicts
(serialized by Mcp.records.opportunity_to_dict / sports_opportunity_to_dict)
plus the student's request/profile values. No database access, no AI calls —
the AI (Pattern B) only decides WHICH records to retrieve; the scoring, the
match reasons, the missing requirements, and the next actions are computed
here from database values only (architecture §9: "match_reasons: from DB
data only").

Score formulas (documented Phase 6 decisions):

- Opportunities: match_score = matched_required_skills / total_required_skills
  (case-insensitive); 1.0 when the record lists no required skills. This
  mirrors the established skill-overlap rule of the Phase 5 MCP tool
  ``match_opportunity`` so both surfaces agree.

- Sports: match_score = met_eligibility_requirements / total_scored_requirements
  where only requirements the request can actually verify are scored — the
  ``level`` requirement (vs the requested player level) and the ``enrollment``
  requirement (vs the student's education stage). Age requirements cannot be
  verified from the collected profile, so they are surfaced in
  eligibility_missing (with an honest "(not verified)" phrasing) but never
  scored. 1.0 when the record lists no eligibility requirements.

- Freshness (§10): records whose last_verified is older than 30 days carry
  data_freshness = "unverified".
"""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from schemas.shared import OpportunityMatch, SportsOpportunityMatch

# The Mcp package lives at the repository root (main.py adds it to sys.path;
# this module keeps itself importable independently, e.g. from scripts).
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from Mcp.records import city_matches  # noqa: E402

# Architecture §10: "If last_verified < today - 30 days, add a flag
# {data_freshness: 'unverified'} to the response."
VERIFIED_FRESH_DAYS = 30

# Education stages that map onto the "school_student" enrollment category;
# every other stage maps onto "university_student".
_SCHOOL_STAGES = {"HIGH_SCHOOL", "CAREER_DISCOVERY", "CAREER_DECISION"}


# ---------------------------------------------------------------------------
# Freshness (architecture §10)
# ---------------------------------------------------------------------------


def data_freshness(
    last_verified: str | date | None, today: Optional[date] = None
) -> Optional[str]:
    """Return "unverified" when the record was verified more than 30 days ago."""
    if last_verified is None:
        return None
    if isinstance(last_verified, str):
        try:
            last_verified = date.fromisoformat(last_verified)
        except ValueError:
            return None
    threshold = (today or date.today()) - timedelta(days=VERIFIED_FRESH_DAYS)
    return "unverified" if last_verified < threshold else None


# ---------------------------------------------------------------------------
# Opportunity scoring
# ---------------------------------------------------------------------------


def score_opportunity(
    record: dict, student_skills: list[str], city: Optional[str] = None
) -> OpportunityMatch:
    """
    Score one opportunity record against the student's skills.

    Args:
        record: a serialized opportunity dict (from opportunity_to_dict).
        student_skills: the student's skill names (any casing).
        city: the requested city — used only for an informational match
            reason (never for the score).
    """
    required = [skill for skill in (record.get("required_skills") or []) if skill]
    skill_set = {skill.strip().lower() for skill in student_skills if skill and skill.strip()}

    matched = [skill for skill in required if skill.strip().lower() in skill_set]
    missing = [skill for skill in required if skill.strip().lower() not in skill_set]

    score = round(len(matched) / len(required), 2) if required else 1.0

    reasons: list[str] = []
    if required:
        names = ", ".join(matched) if matched else "none yet"
        reasons.append(f"Has {len(matched)} of {len(required)} required skills: {names}")
    else:
        reasons.append("No specific required skills listed")
    _location_reason(record, city, reasons)

    deadline = record.get("deadline")
    return OpportunityMatch(
        opportunity_id=record["id"],
        title=record["title"],
        organization=record.get("organization") or "",
        match_score=score,
        match_reasons=reasons,
        missing_requirements=missing,
        next_action=_opportunity_next_action(matched, missing, required, deadline),
        deadline=deadline,
        source_url=record.get("source_url") or "",
        data_freshness=data_freshness(record.get("last_verified")),
    )


def sort_opportunity_matches(matches: list[OpportunityMatch]) -> list[OpportunityMatch]:
    """Ranked ordering: score descending, then soonest deadline (deterministic)."""
    return sorted(matches, key=lambda m: (-m.match_score, m.deadline is None, m.deadline or date.min))


# ---------------------------------------------------------------------------
# Sports scoring
# ---------------------------------------------------------------------------


def score_sports_opportunity(
    record: dict,
    player_level: Optional[str],
    location: Optional[str],
    student_stage: Optional[str],
) -> SportsOpportunityMatch:
    """
    Score one sports opportunity record against the request values.

    Args:
        record: a serialized sports opportunity dict (from
            sports_opportunity_to_dict).
        player_level: the requested playing level (e.g. "intermediate").
        location: the requested city.
        student_stage: the student's education stage (used to evaluate the
            enrollment eligibility requirement).
    """
    eligibility = record.get("eligibility") or {}
    if not isinstance(eligibility, dict):
        eligibility = {}

    met: list[str] = []
    missing: list[str] = []
    scored_total = 0
    scored_met = 0
    level_met = False
    enrollment_met = False

    # --- level requirement (scored) ----------------------------------------
    required_level = eligibility.get("level")
    if required_level:
        scored_total += 1
        if _level_matches(required_level, player_level):
            level_met = True
            scored_met += 1
            met.append(f"Meets the required level ({required_level})")
        else:
            detail = f" (player level: {player_level})" if player_level else " (player level not provided)"
            missing.append(f"Requires {required_level} level{detail}")

    # --- enrollment requirement (scored) ------------------------------------
    required_enrollment = eligibility.get("enrollment")
    if required_enrollment:
        scored_total += 1
        student_category = enrollment_category(student_stage)
        if student_category and student_category == str(required_enrollment).strip().lower():
            enrollment_met = True
            scored_met += 1
            met.append(f"Meets the enrollment requirement ({required_enrollment})")
        else:
            detail = "" if student_category else " (student enrollment unverified)"
            missing.append(
                f"Requires {str(required_enrollment).replace('_', ' ')} status{detail}"
            )

    # --- age requirements (never scored — the profile has no age) -----------
    _age_requirements(eligibility, missing)

    # --- location (informational only, never scored) ------------------------
    _location_notes(record, location, met)

    score = round(scored_met / scored_total, 2) if scored_total else 1.0

    deadline = record.get("deadline")
    return SportsOpportunityMatch(
        opportunity_id=record["id"],
        sport=record.get("sport") or "",
        title=record["title"],
        organization=record.get("organization") or "",
        match_score=score,
        eligibility_met=met,
        eligibility_missing=missing,
        next_action=_sports_next_action(
            eligibility,
            score,
            required_level,
            level_met,
            required_enrollment,
            enrollment_met,
            deadline,
        ),
        deadline=deadline,
        source_url=record.get("source_url") or "",
        data_freshness=data_freshness(record.get("last_verified")),
    )


def sort_sports_matches(matches: list[SportsOpportunityMatch]) -> list[SportsOpportunityMatch]:
    """Ranked ordering: score descending, then soonest deadline (deterministic)."""
    return sorted(matches, key=lambda m: (-m.match_score, m.deadline is None, m.deadline or date.min))


def enrollment_category(student_stage: Optional[str]) -> Optional[str]:
    """Map an education stage onto the seed data's enrollment categories."""
    if not student_stage:
        return None
    return "school_student" if student_stage.upper() in _SCHOOL_STAGES else "university_student"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _level_matches(required_level, player_level: Optional[str]) -> bool:
    if not player_level:
        return False
    return str(required_level).strip().lower() == player_level.strip().lower()


def _age_requirements(eligibility: dict, missing: list[str]) -> None:
    """Surface age_min/age_max honestly — they cannot be verified from the profile."""
    age_min = eligibility.get("age_min")
    age_max = eligibility.get("age_max")
    if age_min is not None and age_max is not None:
        missing.append(f"Age {age_min}-{age_max} requirement (not verified from your profile)")
    elif age_min is not None:
        missing.append(f"Minimum age {age_min} requirement (not verified from your profile)")
    elif age_max is not None:
        missing.append(f"Maximum age {age_max} requirement (not verified from your profile)")


def _location_notes(record: dict, city: Optional[str], notes: list[str]) -> None:
    """Append an informational location note (sports schema has no reasons field)."""
    location = record.get("location")
    if not city or not location:
        return
    if location.strip().lower() == "nationwide":
        notes.append("Open nationwide")
    elif city_matches(location, city):
        notes.append(f"Located in {location}")


def _location_reason(record: dict, city: Optional[str], reasons: list[str]) -> None:
    location = record.get("location")
    if not city or not location:
        return
    if location.strip().lower() == "nationwide":
        reasons.append("Open nationwide")
    elif city_matches(location, city):
        reasons.append(f"Located in {location}")


def _opportunity_next_action(
    matched: list[str], missing: list[str], required: list[str], deadline
) -> str:
    when = f" before the deadline ({deadline or 'see the source page'})"
    if not required:
        return "No specific requirements listed — prepare an application" + when + "."
    if not missing:
        return (
            f"All {len(required)} required skills are already in the profile — "
            "prepare an application" + when + "."
        )
    if matched:
        return (
            "Partially matched — build the missing skills ("
            + ", ".join(missing)
            + ") while preparing an application."
        )
    return "Start with the first required skill: " + missing[0] + "."


def _sports_next_action(
    eligibility: dict,
    score: float,
    required_level,
    level_met: bool,
    required_enrollment,
    enrollment_met: bool,
    deadline,
) -> str:
    when = f" before the deadline ({deadline or 'see the source page'})"
    if not eligibility:
        return "No specific eligibility requirements listed — register" + when + "."
    if score == 1.0:
        return "All stated eligibility requirements are met — register" + when + "."
    level_gap = bool(required_level) and not level_met
    enrollment_gap = bool(required_enrollment) and not enrollment_met
    if level_gap and enrollment_gap:
        return (
            f"Build toward {required_level} level and confirm the "
            f"{str(required_enrollment).replace('_', ' ')} requirement on the source page."
        )
    if level_gap:
        return f"Build toward {required_level} level before applying."
    if enrollment_gap:
        return (
            "This opportunity requires "
            f"{str(required_enrollment).replace('_', ' ')} status — check the "
            "eligibility rules on the source page."
        )
    return "Review the remaining eligibility details on the source page before applying."
