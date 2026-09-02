"""
Pakistan Knowledge Engine — PKE MCP server (Step 5, Server 3 of 3).

Student-facing read-only tools over VERIFIED Pakistan knowledge data.
Mounted at /mcp/pke in BackEnd/main.py.

ABSOLUTE SAFETY RULE:
  Every tool in this server enforces a VERIFIED-only visibility gate before
  returning any data.  CANDIDATE, REJECTED, and unverified records are never
  accessible through these tools.  Staging data is completely inaccessible
  from this server.

Tools provided:
  1. search_verified_institutions(city, institution_type, query)
  2. search_verified_opportunities(type, city, education_stage, query)
  3. search_verified_programs(city, institution, career_slug, query)
  4. search_verified_learning_resources(scope, query)
  5. get_source_registry_info(source_id)

Geographic scope: strictly Karachi, Lahore, Islamabad, NATIONWIDE, ONLINE.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Bootstrap the BackEnd package on sys.path.
_BACKEND_DIR = Path(__file__).resolve().parents[1] / "BackEnd"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from mcp.server.mcpserver import MCPServer

from Mcp.db_access import get_session
from Mcp.records import NO_RESULTS_MESSAGE, city_matches, deadline_sort_key, opportunity_to_dict
from models.opportunity import Opportunity, SportsOpportunity
from retrieval import learning_retrieval, university_retrieval, visibility

pke_server = MCPServer(
    name="pakistan_knowledge_engine",
    instructions=(
        "Pakistan Knowledge Engine server. Read-only access to VERIFIED "
        "Pakistani educational institutions, programs, scholarships, "
        "internships, learning resources, and source provenance data. "
        "All data is from the verified production database — never from "
        "staging or unverified sources. City scope: Karachi, Lahore, "
        "Islamabad, NATIONWIDE, ONLINE only. When no verified result is "
        "found, say so plainly — never invent opportunities, deadlines, "
        "fees, or eligibility criteria."
    ),
)

# Valid MVP geography (for input validation)
_MVP_LOCATIONS = {"karachi", "lahore", "islamabad", "nationwide", "online"}

# VERIFIED_ONLY visibility statuses — must match retrieval.visibility
_VERIFIED_STATUSES = ("VALIDATED", "VERIFIED")


def _invalid_input(message: str) -> dict:
    return {"error": "invalid_input", "message": message}


def _no_results(message: str = NO_RESULTS_MESSAGE, **extra) -> dict:
    return {"count": 0, "results": [], "message": message, **extra}


def _city_ok(city: str) -> bool:
    """True when city is in the MVP geography set."""
    return city.strip().lower() in _MVP_LOCATIONS


def _wrap(records: list[dict], **extra) -> dict:
    result = {"count": len(records), "results": records, **extra}
    if not records:
        result["message"] = NO_RESULTS_MESSAGE
    return result


# ---------------------------------------------------------------------------
# Tool 1: search_verified_institutions
# ---------------------------------------------------------------------------


@pke_server.tool()
def search_verified_institutions(
    city: str = "",
    institution_type: str = "",
    query: str = "",
) -> dict:
    """Search verified universities and institutions.

    Filters:
    - city: Karachi, Lahore, or Islamabad (leave empty for all three cities).
    - institution_type: PUBLIC or PRIVATE.
    - query: keyword search against institution name.

    Returns only VERIFIED/VALIDATED institutions.  Never returns staging or
    candidate records.
    """
    city_clean = (city or "").strip()
    if city_clean and not _city_ok(city_clean):
        return _invalid_input(
            f"'{city_clean}' is not in the allowed city list: "
            "Karachi, Lahore, Islamabad."
        )
    type_clean = (institution_type or "").strip().upper() or None
    query_clean = (query or "").strip()

    session = get_session()
    try:
        results = university_retrieval.search_universities(
            session,
            city=city_clean or None,
            uni_type=type_clean,
            query=query_clean,
        )
    finally:
        session.close()

    return _wrap(results, city=city_clean or None, institution_type=type_clean)


# ---------------------------------------------------------------------------
# Tool 2: search_verified_opportunities
# ---------------------------------------------------------------------------


@pke_server.tool()
def search_verified_opportunities(
    type: str = "",
    city: str = "",
    education_stage: str = "",
    query: str = "",
) -> dict:
    """Search verified opportunities: scholarships, internships, jobs, education.

    Filters:
    - type: scholarship, internship, job, education (leave empty for all types).
    - city: Karachi, Lahore, Islamabad, NATIONWIDE, ONLINE.
    - education_stage: e.g. UNIVERSITY, HIGH_SCHOOL (optional).
    - query: keyword matched against title, organization, description.

    Returns only VERIFIED/VALIDATED, active, non-expired records.
    Never returns candidate or rejected staging records.
    Deadlines are shown as stored — null means the deadline was not verified.
    """
    city_clean = (city or "").strip()
    if city_clean and not _city_ok(city_clean):
        return _invalid_input(
            f"'{city_clean}' is not in the allowed scope: "
            "Karachi, Lahore, Islamabad, NATIONWIDE, ONLINE."
        )
    type_clean = (type or "").strip().lower() or None
    stage_clean = (education_stage or "").strip().upper() or None
    query_clean = (query or "").strip().lower()

    session = get_session()
    try:
        base = visibility.apply_opportunity_visibility(
            session.query(Opportunity)
        )
        if type_clean:
            base = base.filter(Opportunity.type == type_clean)
        rows = base.all()
    finally:
        session.close()

    # City filter: match exact city or nationwide/online records
    if city_clean:
        rows = [o for o in rows if _location_matches_scope(o.location, city_clean)]

    # Education stage filter
    if stage_clean:
        rows = [o for o in rows if (o.required_education_stage or "").upper() == stage_clean]

    # Keyword filter
    if query_clean:
        rows = [
            o for o in rows
            if query_clean in (o.title or "").lower()
            or query_clean in (o.organization or "").lower()
            or query_clean in (o.description or "").lower()
        ]

    rows = sorted(rows, key=deadline_sort_key)
    results = [opportunity_to_dict(o) for o in rows]
    return _wrap(results, type=type_clean, city=city_clean or None)


# ---------------------------------------------------------------------------
# Tool 3: search_verified_programs
# ---------------------------------------------------------------------------


@pke_server.tool()
def search_verified_programs(
    city: str = "",
    institution: str = "",
    career_slug: str = "",
    query: str = "",
) -> dict:
    """Search verified degree programs at Pakistani universities.

    Filters:
    - city: Karachi, Lahore, or Islamabad (leave empty for all).
    - institution: university name keyword.
    - career_slug: e.g. 'software-engineering' (matches career_ids on programs).
    - query: keyword matched against program name or field.

    Returns only VERIFIED/VALIDATED programs.
    Annual fees are shown as stored — null means fee is unverified (never guessed).
    Duration is shown as stored — null means duration is unverified.
    """
    city_clean = (city or "").strip()
    if city_clean and not _city_ok(city_clean):
        return _invalid_input(
            f"'{city_clean}' is not in the allowed city list: "
            "Karachi, Lahore, Islamabad."
        )
    institution_clean = (institution or "").strip()
    query_clean = (query or "").strip()
    career_slug_clean = (career_slug or "").strip().lower()

    session = get_session()
    try:
        # Get matching universities
        unis = university_retrieval.search_universities(
            session,
            city=city_clean or None,
            query=institution_clean,
            limit=100,
        )
        all_programs: list[dict] = []
        for uni in unis:
            programs = university_retrieval.get_programs(
                session,
                uni["id"],
                field=query_clean or None,
                limit=50,
            )
            # Enrich each program with the university name and city
            for prog in programs:
                prog = dict(prog)
                prog["university_name"] = uni["name"]
                prog["university_city"] = uni["city"]
                prog["university_slug"] = uni["slug"]
                prog["university_type"] = uni["type"]
                prog["hec_recognized"] = uni["hec_recognized"]
                all_programs.append(prog)
    finally:
        session.close()

    # Career slug filter
    if career_slug_clean:
        # career_ids is a JSON list of integer IDs; we can't match slugs here
        # directly (slugs are resolved to IDs at seed time). Filter by keyword
        # instead when a career_slug is given, matching against program field/name.
        all_programs = [
            p for p in all_programs
            if career_slug_clean in (p.get("field") or "").lower()
            or career_slug_clean.replace("-", " ") in (p.get("name") or "").lower()
        ]

    # Keyword filter on name/field
    if query_clean and not institution_clean:
        all_programs = [
            p for p in all_programs
            if query_clean.lower() in (p.get("name") or "").lower()
            or query_clean.lower() in (p.get("field") or "").lower()
        ]

    return _wrap(
        all_programs,
        city=city_clean or None,
        institution=institution_clean or None,
        career_slug=career_slug_clean or None,
    )


# ---------------------------------------------------------------------------
# Tool 4: search_verified_learning_resources
# ---------------------------------------------------------------------------


@pke_server.tool()
def search_verified_learning_resources(
    scope: str = "",
    query: str = "",
    is_free: bool | None = None,
) -> dict:
    """Search verified learning resources.

    Filters:
    - scope: NATIONWIDE, ONLINE, Karachi, Lahore, or Islamabad
      (optional; many resources are ONLINE and apply everywhere).
    - query: keyword matched against skill name, title, or provider.
    - is_free: True for free-only resources; None for all (null = unknown).

    Returns only VERIFIED/VALIDATED, active resources.
    is_free and duration_hours are shown as stored — null means unverified.
    """
    query_clean = (query or "").strip()

    session = get_session()
    try:
        if query_clean:
            results = learning_retrieval.search_resources(session, query_clean, limit=20)
        else:
            results = learning_retrieval.list_resources(session, is_free=is_free, limit=20)
    finally:
        session.close()

    # is_free post-filter when set (search_resources does not support it)
    if is_free is not None and query_clean:
        results = [r for r in results if r.get("is_free") is is_free]

    return _wrap(results, scope=scope or None, query=query_clean or None)


# ---------------------------------------------------------------------------
# Tool 5: get_source_registry_info
# ---------------------------------------------------------------------------


@pke_server.tool()
def get_source_registry_info(source_id: str) -> dict:
    """Return safe provenance metadata for a PKE source registry entry.

    Accepts the source_id string (e.g. 'GOV-HEC-02') and returns the
    publicly safe fields: name, base_url, authority_level, domains,
    geographic_scope, access_review_status, source_confidence.

    This tool is read-only and never modifies source authority levels.
    """
    source_id_clean = (source_id or "").strip()
    if not source_id_clean:
        return _invalid_input("source_id must be a non-empty string.")

    from knowledge_engine.pke_source_registry import PKESource

    session = get_session()
    try:
        entry = (
            session.query(PKESource)
            .filter(PKESource.source_id == source_id_clean)
            .first()
        )
        if entry is None:
            return {
                "found": False,
                "source_id": source_id_clean,
                "message": f"No source registry entry found for '{source_id_clean}'.",
            }
        return {
            "found": True,
            "source_id": entry.source_id,
            "name": entry.name,
            "base_url": entry.base_url,
            "authority_level": entry.authority_level,
            "source_type": entry.source_type,
            "domains": entry.domain_list,
            "geographic_scope": entry.geographic_scope,
            "access_review_status": entry.access_review_status,
            "source_confidence": entry.confidence_float,
            "is_reachable": entry.is_reachable,
            "last_checked": entry.last_checked.isoformat() if entry.last_checked else None,
            "notes": entry.notes,
        }
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------


def _location_matches_scope(location: str | None, query_city: str) -> bool:
    """True when a record's location is the queried city or is nationwide/online."""
    if not location:
        return False
    loc = location.strip().lower()
    query = query_city.strip().lower()
    if query in ("nationwide", "online"):
        return loc in ("nationwide", "online", "nationwide/online") or loc == query
    return loc == query or loc in ("nationwide", "online", "nationwide/online")
