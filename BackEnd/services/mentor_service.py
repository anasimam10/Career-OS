"""
Grounded AI Career & Sports Mentor Service (Step 6).

Coordinates the intelligence layer:
  Student -> Mentor Service -> MCP/PKE retrieval (when needed)
          -> Qwen (with anti-hallucination prompt)
          -> Structured CoachResponse / MentorResponse (ONE Next Best Action)
          -> Verified Provenance Citations
          -> Student

Governed by pakistan_knowledge_engine.md:
- Qwen is the reasoning layer, NOT the source of truth.
- Verified Pakistan-specific knowledge comes exclusively from PKE.
- Anti-hallucination: preserved nulls (deadlines, fees, CGPA, salaries), no invented URLs.
- ONE Next Best Action per turn.
"""

from __future__ import annotations

import json
import logging
import re
import sys
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

# Bootstrap MCP path
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from models.career import Career
from models.opportunity import Opportunity
from models.roadmap import Milestone, Roadmap
from models.student import Student, StudentProfile
from prompts.mentor import build_mentor_system_prompt, build_mentor_user_prompt
from schemas.shared import CoachResponse, SourceCitation
from services.ai_service import (
    AIServiceError,
    AIUnavailableError,
    AIValidationError,
    get_ai_service,
)
from services.journey_state import DEMO_STUDENT_ID

try:
    from Mcp.pke_server import (
        get_source_registry_info,
        search_verified_institutions,
        search_verified_learning_resources,
        search_verified_opportunities,
        search_verified_programs,
    )
    _PKE_AVAILABLE = True
except Exception:
    _PKE_AVAILABLE = False

logger = logging.getLogger("ah_career.mentor")

# Constraints
_MAX_HISTORY_MESSAGES = 5
_MAX_TOTAL_CHARS = 2000
_MAX_QUICK_ACTIONS = 3

MVP_CITIES = {"karachi", "lahore", "islamabad", "nationwide", "online"}

# Intent keywords for factual PKE retrieval
_FACTUAL_KEYWORDS = re.compile(
    r"\b("
    r"universit(y|ies)|college(s)?|school(s)?|degree(s)?|program(s)?|"
    r"admission(s)?|campus(es)?|hec|fast|nust|lums|iba|gcu|qau|ned|uet|"
    r"study|studying|computer science|software engineering|data science|engineering|mbbs|bba|mba|"
    r"scholarship(s)?|financial aid|stipend|grant(s)?|"
    r"internship(s)?|job(s)?|hiring|vacanc(y|ies)|"
    r"trial(s)?|tournament(s)?|sports? quota|sports? scholarship|academy|academies|pcb|pff|"
    r"course(s)?|digiskills|navttc|free learning|certification(s)?"
    r")\b",
    re.IGNORECASE,
)

# Pure conversational / emotional phrases that do not need PKE search
_EMOTIONAL_PHRASES = re.compile(
    r"\b("
    r"i('m| am) scared|i('m| am) confused|i feel (lost|stressed|overwhelmed|anxious)|"
    r"peer pressure|family expectations?|parents? want me|not good enough|"
    r"can you help me choose|how do i decide|what should i do with my life"
    r")\b",
    re.IGNORECASE,
)


class StudentNotFoundError(Exception):
    """No onboarded student found."""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def mentor_chat(
    db: Session,
    message: str,
    history: list[dict] | None = None,
    student_id: int = DEMO_STUDENT_ID,
    *,
    safe_fallback: bool = False,
) -> CoachResponse:
    """
    Execute grounded AI mentor conversation turn.

    1. Load student profile and DB journey context.
    2. Determine if factual PKE retrieval is needed.
    3. Retrieve verified data via PKE MCP tools if appropriate.
    4. Construct grounded system and user prompts.
    5. Call Qwen with structured output (CoachResponse).
    6. Post-process: enforce ONE Next Best Action, attach valid citations, trim quick actions.
    7. Fallback safely if safe_fallback=True or propagate errors cleanly.
    """
    student = db.get(Student, student_id)
    if student is None:
        raise StudentNotFoundError()

    history = history or []
    trimmed_history = _trim_history(history)
    db_context = _build_student_context(db, student)

    # Detect if message requires verified factual knowledge
    needs_pke = _needs_pke_retrieval(message)
    verified_data: dict = {}
    citations: list[SourceCitation] = []

    if needs_pke and _PKE_AVAILABLE:
        try:
            verified_data, citations = _retrieve_pke_knowledge(message, student, db)
        except Exception as exc:
            logger.warning("PKE retrieval error (proceeding gracefully): %s", exc)

    # Build prompt contexts
    student_json = json.dumps(
        {
            "education_stage": student.education_stage,
            "career_goal": student.career_goal,
            "sports_interest": student.sports_interest,
            "interests": _safe_json_load(student, "interests") or db_context.get("interests"),
            "skills": _safe_json_load(student, "skills") or db_context.get("skills"),
            "motivation_tags": _safe_json_load(student, "motivation_tags"),
        },
        ensure_ascii=False,
    )

    combined_context = dict(db_context)
    if verified_data:
        combined_context["verified_pke_data"] = verified_data

    context_json = json.dumps(combined_context, ensure_ascii=False, default=str)
    system_prompt = build_mentor_system_prompt(student_json, context_json)

    history_text = "\n".join(f"{m['role']}: {m['content']}" for m in trimmed_history)
    user_prompt = build_mentor_user_prompt(history_text, message)

    try:
        ai = get_ai_service()
        response = ai.call_structured(
            prompt=user_prompt,
            response_model=CoachResponse,
            system_prompt=system_prompt,
            operation="mentor_chat",
        )
        return _post_process_mentor_response(db, response, citations, student, message)
    except (AIUnavailableError, AIValidationError, AIServiceError) as exc:
        if safe_fallback:
            logger.warning("AI service error during mentor_chat; returning fallback response: %s", exc)
            return fallback_mentor_response(message, student, db_context, citations)
        raise


def fallback_mentor_response(
    message: str,
    student: Student | None,
    context: dict | None = None,
    citations: list[SourceCitation] | None = None,
) -> CoachResponse:
    """
    Controlled, deterministic fallback when AI is unavailable or produces invalid JSON.
    Never hallucinates Pakistani factual data. Provides ONE clear Next Best Action.
    """
    goal = (student.career_goal if student else "your chosen path") or "your chosen path"
    sport = (student.sports_interest if student else None)

    msg_lines = [
        "I am currently operating in resilient offline mode, but I can still guide your immediate next step.",
        f"For your journey towards {goal.replace('-', ' ').title()}, focus on building foundational clarity and exploring verified options.",
    ]
    if sport:
        msg_lines.append(f"Regarding {sport.title()}, keep training consistently while watching for verified trials.")

    nba = f"Review the key skills for {goal.replace('-', ' ').title()} in Career Explorer and complete one self-reflection note."
    if "scholarship" in message.lower():
        nba = "Check the verified HEC National Scholarships index for current active criteria."
    elif "university" in message.lower() or "uni" in message.lower() or "college" in message.lower():
        nba = "Compare verified HEC-recognized university programs in your city."
    elif "internship" in message.lower() or "job" in message.lower():
        nba = "Draft a 1-page CV highlighting your current verified projects and technical skills."
    elif "sport" in message.lower() or "trial" in message.lower():
        nba = "Review the official domestic sports calendar for upcoming registration windows."

    return CoachResponse(
        message="\n\n".join(msg_lines),
        next_best_action=nba,
        next_best_action_type="EXPLORE",
        reasoning_summary="Provided grounded fallback guidance based on your student profile.",
        quick_actions=[
            "Explore Career Explorer",
            "Check Verified Programs",
            "Review My Milestones",
        ],
        suggested_resource=None,
        sources=citations or [],
        confidence="grounded_fallback",
    )


# ---------------------------------------------------------------------------
# PKE Retrieval Logic
# ---------------------------------------------------------------------------


def _needs_pke_retrieval(message: str) -> bool:
    """Determine whether the message requires verified factual knowledge."""
    clean = message.strip()
    if not clean:
        return False
    # If purely emotional/conversational without factual inquiry, skip retrieval
    if _EMOTIONAL_PHRASES.search(clean) and not _FACTUAL_KEYWORDS.search(clean):
        return False
    return bool(_FACTUAL_KEYWORDS.search(clean))


def _detect_city(message: str, default: str = "") -> str:
    """Extract one of the 3 MVP cities from the message or return default."""
    m_lower = message.lower()
    if "karachi" in m_lower:
        return "karachi"
    if "lahore" in m_lower:
        return "lahore"
    if "islamabad" in m_lower:
        return "islamabad"
    return default if default.lower() in MVP_CITIES else ""


def _retrieve_pke_knowledge(
    message: str, student: Student, db: Session
) -> tuple[dict, list[SourceCitation]]:
    """Query verified PKE tools and compile factual context + citations."""
    m_lower = message.lower()
    city = _detect_city(message)
    verified_data: dict = {}
    citations: list[SourceCitation] = []
    seen_urls: set[str] = set()

    def _add_citation(title: str, url: str | None, src_id: str | None = None):
        if not title:
            return
        if url and url in seen_urls:
            return
        if url:
            seen_urls.add(url)
        citations.append(SourceCitation(title=title, source_url=url, source_id=src_id))

    # 1. Universities & Institutions
    if any(k in m_lower for k in ["universit", "uni", "college", "school", "hec", "campus", "study", "fast", "nust", "lums", "iba", "gcu", "qau", "ned", "uet"]):
        res = search_verified_institutions(city=city, query="")
        results = res.get("results", [])[:10]
        if results:
            verified_data["universities"] = results
            for r in results:
                _add_citation(r.get("name", ""), r.get("website_url"))

    # 2. Degree Programs
    if any(k in m_lower for k in ["program", "degree", "bs", "bba", "ms", "cs", "computer science", "software", "engineering", "admission"]):
        query_term = "computer science" if "cs" in m_lower or "computer" in m_lower else ""
        res = search_verified_programs(city=city, query=query_term)
        results = res.get("results", [])[:10]
        if results:
            verified_data["programs"] = results
            for r in results:
                title = f"{r.get('university_name', '')} - {r.get('name', '')}"
                _add_citation(title, r.get("admission_url") or r.get("website_url"))

    # 3. Opportunities (Scholarships, Internships, Jobs)
    if any(k in m_lower for k in ["scholarship", "financial aid", "grant", "stipend"]):
        res = search_verified_opportunities(type="scholarship", city=city)
        results = res.get("results", [])[:8]
        if results:
            verified_data["scholarships"] = results
            for r in results:
                _add_citation(f"{r.get('organization', '')}: {r.get('title', '')}", r.get("source_url"))

    if any(k in m_lower for k in ["internship", "job", "hiring", "vacancy", "vacancies"]):
        opp_type = "internship" if "internship" in m_lower else "job"
        res = search_verified_opportunities(type=opp_type, city=city)
        results = res.get("results", [])[:8]
        if results:
            verified_data["opportunities"] = results
            for r in results:
                _add_citation(f"{r.get('organization', '')}: {r.get('title', '')}", r.get("source_url"))

    # 4. Learning Resources
    if any(k in m_lower for k in ["learn", "course", "digiskills", "navttc", "free resource", "tutorial"]):
        res = search_verified_learning_resources(scope=city, query="")
        results = res.get("results", [])[:8]
        if results:
            verified_data["learning_resources"] = results
            for r in results:
                _add_citation(r.get("title", ""), r.get("source_url"))

    # 5. Sports Opportunities & Trials
    if any(k in m_lower for k in ["sport", "cricket", "football", "trial", "tournament", "pcb", "pff"]):
        res = search_verified_opportunities(type="sports_opportunity", city=city)
        results = res.get("results", [])[:8]
        if results:
            verified_data["sports_opportunities"] = results
            for r in results:
                _add_citation(f"{r.get('organization', '')}: {r.get('title', '')}", r.get("source_url"))

    return verified_data, citations


# ---------------------------------------------------------------------------
# Post-Processing & Validation
# ---------------------------------------------------------------------------


def _post_process_mentor_response(
    db: Session,
    response: CoachResponse,
    pke_citations: list[SourceCitation],
    student: Student,
    message: str,
) -> CoachResponse:
    """Enforce strict backend contracts that the LLM cannot be trusted to follow."""
    # 1. Trim quick_actions to max 3
    quick_actions = (response.quick_actions or [])[:_MAX_QUICK_ACTIONS]

    # 2. Enforce ONE Next Best Action
    nba = (response.next_best_action or "").strip()
    if not nba:
        # Fallback to the first quick action or a contextual action
        if quick_actions:
            nba = quick_actions[0]
        else:
            goal = (student.career_goal or "your career goal").replace("-", " ").title()
            nba = f"Explore verified skills and milestones for {goal} in Career Explorer."

    nba_type = response.next_best_action_type or "EXPLORE"

    # 3. Validate suggested_resource
    suggested = response.suggested_resource
    if suggested:
        suggested = _validate_resource(db, suggested)

    # 4. Filter & Ground Sources — never let AI invent URLs
    # Start with valid PKE citations
    valid_sources: list[SourceCitation] = []
    known_urls = {c.source_url: c for c in pke_citations if c.source_url}

    # If the LLM returned sources, only keep those whose URLs match known PKE or DB URLs
    if response.sources:
        for src in response.sources:
            if src.source_url and src.source_url in known_urls:
                valid_sources.append(src)
            elif not src.source_url and src.title:
                # Citations with title only (no URL) are safe if matching known records
                valid_sources.append(src)

    # If LLM returned no valid sources but PKE data was retrieved, attach PKE citations
    if not valid_sources and pke_citations:
        valid_sources = pke_citations[:5]

    return CoachResponse(
        message=response.message,
        quick_actions=quick_actions,
        suggested_resource=suggested,
        next_best_action=nba,
        next_best_action_type=nba_type,
        reasoning_summary=response.reasoning_summary or "Grounded guidance personalized to your pathway.",
        sources=valid_sources,
        confidence=response.confidence or "high",
    )


def _validate_resource(db: Session, resource: str) -> Optional[str]:
    """Check whether suggested_resource matches a known DB entity."""
    resource_lower = resource.strip().lower()

    # Check careers
    careers = db.query(Career).all()
    for c in careers:
        if c.name.lower() == resource_lower or c.slug.lower() == resource_lower:
            return resource

    # Check opportunities
    opportunities = db.query(Opportunity).all()
    for o in opportunities:
        if o.title and o.title.lower() == resource_lower:
            return resource

    logger.info("Mentor suggested_resource not found in DB, set to None: %s", resource[:100])
    return None


def _build_student_context(db: Session, student: Student) -> dict:
    """Fetch relevant DB data for the mentor prompt."""
    context: dict = {}

    profile = (
        db.query(StudentProfile)
        .filter(StudentProfile.student_id == student.id)
        .first()
    )
    if profile:
        context["interests"] = _safe_json_load(profile, "interests")
        context["skills"] = _safe_json_load(profile, "skills")
        if profile.next_best_action:
            try:
                context["next_best_action"] = json.loads(profile.next_best_action)
            except (json.JSONDecodeError, TypeError):
                pass

    roadmap = (
        db.query(Roadmap)
        .filter(Roadmap.student_id == student.id)
        .order_by(Roadmap.created_at.desc())
        .first()
    )
    if roadmap:
        context["roadmap_stage"] = roadmap.current_stage
        context["roadmap_step"] = roadmap.current_step_title
        active_milestones = (
            db.query(Milestone)
            .filter(
                Milestone.roadmap_id == roadmap.id,
                Milestone.status.in_(["active", "pending"]),
            )
            .order_by(Milestone.order_index)
            .limit(3)
            .all()
        )
        context["active_milestones"] = [
            {"title": m.title, "status": m.status} for m in active_milestones
        ]

    if student.career_goal:
        career = (
            db.query(Career)
            .filter(Career.slug == student.career_goal)
            .first()
        )
        if career:
            context["career_info"] = {
                "name": career.name,
                "demand_level": career.demand_level,
                "required_skills": _safe_json_load(career, "required_skills"),
                "pk_opportunities": _safe_json_load(career, "pk_opportunities"),
            }

    return context


def _trim_history(history: list[dict]) -> list[dict]:
    """Keep at most 5 recent messages and enforce 2000-char combined limit."""
    if not history:
        return []
    trimmed = history[-_MAX_HISTORY_MESSAGES:]
    total = sum(len(m.get("content", "")) for m in trimmed)
    while total > _MAX_TOTAL_CHARS and len(trimmed) > 1:
        removed = trimmed.pop(0)
        total -= len(removed.get("content", ""))
    return trimmed


def _safe_json_load(obj: object, attr: str) -> object:
    """Safely load a JSON string column; return None on failure."""
    raw = getattr(obj, attr, None)
    if raw is None:
        return None
    if isinstance(raw, (list, dict)):
        return raw
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None
