"""
Roadmap service (Phase 4).

Owns:
- MILESTONE_TEMPLATES — the deterministic, stage-specific milestone
  templates (single source of truth, shared with the candidate generator),
- roadmap creation / idempotent milestone instantiation,
- pending/completed milestone queries used by journey, progress, and the
  candidate generator.

No Qwen calls here — roadmap ordering and milestone creation are fully
deterministic (architecture §4: "Roadmap stage transitions" are never
touched by the LLM).
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from models.roadmap import Milestone, Roadmap
from repositories.career_repo import CareerRepository
from schemas.responses import JourneyStep, RoadmapResponse
from services.journey_state import STAGE_ORDER

logger = logging.getLogger("ah_career.journey")

MAX_VISIBLE_STEPS = 3  # architecture §8: progressive disclosure, 1-3 steps


class CareerNotFoundError(Exception):
    """The requested career_slug does not exist in the database."""


class InvalidStageError(Exception):
    """The requested target_stage is not a valid EducationStage."""


# ---------------------------------------------------------------------------
# Milestone templates — deterministic, per stage
#
# action_type links a template to the matching candidate action in
# candidate_service.py, so completing a milestone naturally retires the
# corresponding candidate.
# ---------------------------------------------------------------------------

MILESTONE_TEMPLATES: dict[str, list[dict]] = {
    "HIGH_SCHOOL": [
        {
            "action_type": "EXPLORE_CAREERS",
            "title": "Explore careers that match your interests",
            "description": "Browse the career explorer and shortlist fields that match your interests.",
            "estimated_duration": "1-2 hours",
            "steps": [
                "Open the Careers page",
                "Shortlist three careers that match your interests",
                "Note what attracts you to each one",
            ],
            "why_this_matters": "Knowing your options is the first step of any career decision.",
        },
        {
            "action_type": "CAREER_REALITY",
            "title": "Complete a Career Reality Check",
            "description": "Run the reality check for one career you are curious about.",
            "estimated_duration": "15 minutes",
            "steps": [
                "Open the career's Reality Check page",
                "Run the analysis and read the verdict",
                "Note one gap the analysis highlights",
            ],
            "why_this_matters": "A reality check grounds your interest in demand, competition, and difficulty data.",
        },
        {
            "action_type": "CAREER_TRIAL",
            "title": "Complete the 7-Day Career Trial",
            "description": "Test one career hands-on for seven days using the trial plan.",
            "estimated_duration": "7 days",
            "steps": [
                "Open the career's Trial page",
                "Generate your 7-day trial plan",
                "Complete the daily tasks",
                "Answer the reflection prompt on day 7",
            ],
            "why_this_matters": "A short hands-on test tells you more than weeks of reading.",
        },
    ],
    "CAREER_DISCOVERY": [
        {
            "action_type": "CAREER_REALITY",
            "title": "Complete a Career Reality Check",
            "description": "Run the reality check for one career you are curious about.",
            "estimated_duration": "15 minutes",
            "steps": [
                "Open the career's Reality Check page",
                "Run the analysis and read the verdict",
                "Note one gap the analysis highlights",
            ],
            "why_this_matters": "A reality check grounds your interest in demand, competition, and difficulty data.",
        },
        {
            "action_type": "CAREER_TRIAL",
            "title": "Complete the 7-Day Career Trial",
            "description": "Test one career hands-on for seven days using the trial plan.",
            "estimated_duration": "7 days",
            "steps": [
                "Open the career's Trial page",
                "Generate your 7-day trial plan",
                "Complete the daily tasks",
                "Answer the reflection prompt on day 7",
            ],
            "why_this_matters": "A short hands-on test tells you more than weeks of reading.",
        },
        {
            "action_type": "EXPLORE_CAREERS",
            "title": "Explore careers that match your interests",
            "description": "Browse the career explorer and shortlist fields that match your interests.",
            "estimated_duration": "1-2 hours",
            "steps": [
                "Open the Careers page",
                "Shortlist three careers that match your interests",
                "Note what attracts you to each one",
            ],
            "why_this_matters": "Knowing your options is the first step of any career decision.",
        },
    ],
    "CAREER_DECISION": [
        {
            "action_type": "CAREER_TRIAL",
            "title": "Complete the 7-Day Career Trial",
            "description": "Test your leading career hands-on for seven days before committing.",
            "estimated_duration": "7 days",
            "steps": [
                "Open the career's Trial page",
                "Generate your 7-day trial plan",
                "Complete the daily tasks",
                "Answer the reflection prompt on day 7",
            ],
            "why_this_matters": "A short hands-on test tells you more than weeks of reading.",
        },
        {
            "action_type": "COMPARE_CAREERS",
            "title": "Compare your top career options",
            "description": "Run reality checks on two or three careers and compare demand, competition, and difficulty.",
            "estimated_duration": "30-45 minutes",
            "steps": [
                "Pick two or three careers you are considering",
                "Run the Reality Check for each",
                "Write down demand, competition, and difficulty side by side",
            ],
            "why_this_matters": "Comparing options side by side makes the trade-offs concrete.",
        },
        {
            "action_type": "FINALIZE_DECISION",
            "title": "Finalize your career direction",
            "description": "Choose the career you will commit to and set it as your goal.",
            "estimated_duration": "20 minutes",
            "steps": [
                "Review your comparisons and trial reflections",
                "Choose the career you will commit to",
                "Set it as your career goal in your profile",
            ],
            "why_this_matters": "A committed direction lets the mentor plan your next steps precisely.",
        },
    ],
    "UNIVERSITY": [
        {
            "action_type": "LEARN_FIRST_SKILL",
            "title": "Learn the first required skill for your career",
            "description": "Start learning the first skill from your target career's required skills list.",
            "estimated_duration": "2-3 weeks",
            "steps": [
                "Open your career's page and find the required skills",
                "Pick the first skill you do not have yet",
                "Find a free beginner tutorial and complete it",
            ],
            "why_this_matters": "Required skills are the concrete entry point into any career.",
        },
        {
            "action_type": "REVIEW_CAREER_DATA",
            "title": "Review the required skills for your career",
            "description": "Open your career's page and study its required skills and risks.",
            "estimated_duration": "20 minutes",
            "steps": [
                "Open your target career's page",
                "Study the required skills list",
                "Compare it honestly with your current skills",
            ],
            "why_this_matters": "Knowing the gap tells you exactly what to learn next.",
        },
    ],
    "SKILL_BUILDING": [
        {
            "action_type": "LEARN_FIRST_SKILL",
            "title": "Learn the first required skill for your career",
            "description": "Start learning the first skill from your target career's required skills list.",
            "estimated_duration": "2-3 weeks",
            "steps": [
                "Open your career's page and find the required skills",
                "Pick the first skill you do not have yet",
                "Find a free beginner tutorial and complete it",
            ],
            "why_this_matters": "Required skills are the concrete entry point into any career.",
        },
        {
            "action_type": "PRACTICE_SKILL",
            "title": "Practice with small exercises",
            "description": "Apply the skill you are learning to small, regular exercises.",
            "estimated_duration": "1-2 weeks",
            "steps": [
                "Set aside 30 minutes on three days this week",
                "Solve small exercises using your new skill",
                "Note which parts felt hard and revisit them",
            ],
            "why_this_matters": "Regular practice is what turns a tutorial into a skill.",
        },
        {
            "action_type": "REVIEW_CAREER_DATA",
            "title": "Review the required skills for your career",
            "description": "Open your career's page and study its required skills and risks.",
            "estimated_duration": "20 minutes",
            "steps": [
                "Open your target career's page",
                "Study the required skills list",
                "Compare it honestly with your current skills",
            ],
            "why_this_matters": "Knowing the gap tells you exactly what to learn next.",
        },
    ],
    "PROJECTS": [
        {
            "action_type": "BUILD_PROJECT",
            "title": "Build your first project",
            "description": "Create a small project that uses the skills you have learned.",
            "estimated_duration": "2-3 weeks",
            "steps": [
                "Choose something small you actually want to make",
                "Build the simplest working version first",
                "Keep a log of problems you solved",
            ],
            "why_this_matters": "A project proves your skills to yourself and to others.",
        },
        {
            "action_type": "DOCUMENT_PROJECT",
            "title": "Document and share your project",
            "description": "Write a short README and share your project publicly.",
            "estimated_duration": "2-3 hours",
            "steps": [
                "Write a short README: what it does and how to run it",
                "Share the project link publicly",
                "Ask one person for feedback",
            ],
            "why_this_matters": "Documented, shared work is what others can actually see.",
        },
    ],
    "INTERNSHIP": [
        {
            "action_type": "PREPARE_CV",
            "title": "Prepare a professional CV",
            "description": "Draft a one-page CV listing your skills and projects.",
            "estimated_duration": "2-3 hours",
            "steps": [
                "List your skills, projects, and education",
                "Fit it onto one clean page",
                "Ask one person to review it",
            ],
            "why_this_matters": "A clear CV is the entry ticket for internship applications.",
        },
        {
            "action_type": "INTERNSHIP_READY",
            "title": "Become internship-ready",
            "description": "Review what internship applications typically require and prepare your materials.",
            "estimated_duration": "30 minutes",
            "steps": [
                "List what a typical internship application asks for",
                "Check which materials you already have",
                "Prepare the missing pieces",
            ],
            "why_this_matters": "Being ready before opportunities appear means you can apply immediately.",
        },
    ],
    "FINAL_YEAR": [
        {
            "action_type": "FINAL_PROJECT",
            "title": "Complete your final-year project",
            "description": "Plan and finish your final-year project to a standard you can show employers.",
            "estimated_duration": "Ongoing",
            "steps": [
                "Break the project into weekly milestones",
                "Track your progress each week",
                "Keep the final result presentable",
            ],
            "why_this_matters": "Your final project is often your strongest first portfolio piece.",
        },
        {
            "action_type": "PREPARE_CV",
            "title": "Prepare a professional CV",
            "description": "Draft a one-page CV listing your skills, projects, and education.",
            "estimated_duration": "2-3 hours",
            "steps": [
                "List your skills, projects, and education",
                "Fit it onto one clean page",
                "Ask one person to review it",
            ],
            "why_this_matters": "A clear CV is the entry ticket for job applications.",
        },
    ],
    "JOB_PREPARATION": [
        {
            "action_type": "PREPARE_CV",
            "title": "Prepare a professional CV",
            "description": "Polish a one-page CV listing your skills, projects, and experience.",
            "estimated_duration": "2-3 hours",
            "steps": [
                "Update your CV with your latest work",
                "Fit it onto one clean page",
                "Ask one person to review it",
            ],
            "why_this_matters": "A clear CV is the entry ticket for job applications.",
        },
        {
            "action_type": "INTERVIEW_PREP",
            "title": "Practice for interviews",
            "description": "Practice answering common interview questions for your field.",
            "estimated_duration": "2-3 hours",
            "steps": [
                "Collect common interview questions for your field",
                "Practice answering out loud",
                "Refine your answers after each run",
            ],
            "why_this_matters": "Interview confidence comes from practice, not talent.",
        },
        {
            "action_type": "JOB_SEARCH_ROUTINE",
            "title": "Build a weekly job-search routine",
            "description": "Set a sustainable weekly routine for finding and applying to roles.",
            "estimated_duration": "30 minutes to set up",
            "steps": [
                "Reserve fixed weekly time slots for applications",
                "Track every application in one list",
                "Review what worked each week",
            ],
            "why_this_matters": "A steady routine beats bursts of unfocused searching.",
        },
    ],
    "FIRST_JOB": [
        {
            "action_type": "SET_90_DAY_GOALS",
            "title": "Set 90-day goals for your first job",
            "description": "Agree on clear goals with your team and write them down.",
            "estimated_duration": "1 hour",
            "steps": [
                "Ask your team what success looks like in 90 days",
                "Write down three concrete goals",
                "Review progress with your team regularly",
            ],
            "why_this_matters": "Clear early goals turn a new job into visible progress.",
        },
        {
            "action_type": "PROFESSIONAL_SKILLS",
            "title": "Keep building professional skills",
            "description": "Pick one professional skill and improve it deliberately this month.",
            "estimated_duration": "Ongoing",
            "steps": [
                "Choose one skill your role depends on",
                "Practice it deliberately in real work",
                "Ask for feedback once a month",
            ],
            "why_this_matters": "Deliberate skill growth compounds fast early in a career.",
        },
    ],
}

# Flat lookup: action_type -> template (first occurrence wins).
TEMPLATE_BY_ACTION_TYPE: dict[str, dict] = {}
for _stage_templates in MILESTONE_TEMPLATES.values():
    for _template in _stage_templates:
        _type = _template["action_type"]
        if _type not in TEMPLATE_BY_ACTION_TYPE:
            TEMPLATE_BY_ACTION_TYPE[_type] = _template


# ---------------------------------------------------------------------------
# Roadmap creation / retrieval
# ---------------------------------------------------------------------------


def create_roadmap(
    db: Session, student_id: int, career_slug: str, target_stage: str
) -> RoadmapResponse:
    """
    Create (or reuse) the roadmap for the student + career and make sure
    milestone instances exist for the requested target stage.

    Idempotent: never duplicates existing milestones; an existing roadmap
    for the same career is reused.
    """
    from services.journey_state import parse_stage

    career = CareerRepository(db).get_by_slug(career_slug)
    if career is None:
        raise CareerNotFoundError(career_slug)

    stage = parse_stage(target_stage)
    if stage is None:
        raise InvalidStageError(target_stage)

    roadmap = _get_or_create_roadmap(db, student_id, career.id, stage.value)
    _instantiate_milestones(db, roadmap, stage.value)

    db.commit()
    logger.info(
        "Roadmap ready: student=%s career=%s stage=%s roadmap_id=%s",
        student_id, career_slug, stage.value, roadmap.id,
    )
    return build_roadmap_response(db, roadmap.id)


def ensure_stage_milestones(
    db: Session, student_id: int, stage: str, career_id: Optional[int] = None
) -> None:
    """
    Make sure the student has a roadmap and milestone instances for `stage`.

    Used by onboarding to bootstrap the journey so the student immediately
    has real milestone ids to complete (progress needs them). Idempotent:
    existing milestones are never duplicated. When the student has no
    resolved career, the roadmap is created with career_id NULL (the
    architecture's roadmaps.career_id is nullable).
    """
    roadmap = (
        db.query(Roadmap).filter(Roadmap.student_id == student_id).first()
    )
    if roadmap is None:
        roadmap = Roadmap(student_id=student_id, career_id=career_id, current_stage=stage)
        db.add(roadmap)
        db.flush()
    elif career_id is not None and roadmap.career_id != career_id:
        # re-onboarding with a resolved career updates the roadmap's link
        roadmap.career_id = career_id
    _instantiate_milestones(db, roadmap, stage)
    db.commit()


def build_roadmap_response(db: Session, roadmap_id: int) -> RoadmapResponse:
    """RoadmapResponse with the current step and 1-3 visible next steps."""
    roadmap = db.get(Roadmap, roadmap_id)
    pending = [m for m in roadmap.milestones if m.status in ("pending", "active")]
    pending.sort(key=lambda m: m.order_index)

    current_step = pending[0].title if pending else roadmap.current_step_title or ""
    visible = [to_journey_step(m) for m in pending[:MAX_VISIBLE_STEPS]]

    # keep the stored current step in sync
    if roadmap.current_step_title != current_step:
        roadmap.current_step_title = current_step
        db.commit()

    return RoadmapResponse(
        roadmap_id=roadmap.id,
        current_step=current_step,
        visible_steps=visible,
    )


# ---------------------------------------------------------------------------
# Milestone queries (shared with journey / progress / candidate generator)
# ---------------------------------------------------------------------------


def get_student_milestones(db: Session, student_id: int) -> list[Milestone]:
    """All milestones across the student's roadmaps, ordered by stage + index."""
    query = (
        db.query(Milestone)
        .join(Roadmap, Milestone.roadmap_id == Roadmap.id)
        .filter(Roadmap.student_id == student_id)
    )
    milestones = query.all()
    stage_rank = {stage.value: idx for idx, stage in enumerate(STAGE_ORDER)}
    milestones.sort(
        key=lambda m: (stage_rank.get(m.stage, 99), m.order_index)
    )
    return milestones


def get_pending_milestones(db: Session, student_id: int) -> list[Milestone]:
    """Pending/active milestones for the student, deterministically ordered."""
    return [
        m for m in get_student_milestones(db, student_id)
        if m.status in ("pending", "active")
    ]


def get_completed_titles(db: Session, student_id: int) -> set[str]:
    """Titles of milestones the student has already completed."""
    return {
        m.title
        for m in get_student_milestones(db, student_id)
        if m.status in ("done", "skipped")
    }


def to_journey_step(milestone: Milestone) -> JourneyStep:
    """Convert a Milestone row into the public JourneyStep contract."""
    template = _template_for_title(milestone.title)
    duration = (template or {}).get("estimated_duration", "1-2 weeks")
    return JourneyStep(
        id=milestone.id,
        title=milestone.title,
        description=milestone.description or "",
        stage=milestone.stage,
        estimated_duration=duration,
    )


def stage_default_steps(stage: str, limit: int = MAX_VISIBLE_STEPS) -> list[JourneyStep]:
    """
    Default visible steps for a stage when no roadmap milestones exist yet
    (deterministic — straight from the templates, nothing persisted).
    """
    templates = MILESTONE_TEMPLATES.get(stage, [])
    return [
        JourneyStep(
            title=t["title"],
            description=t["description"],
            stage=stage,
            estimated_duration=t["estimated_duration"],
        )
        for t in templates[:limit]
    ]


def stage_default_step_title(stage: str) -> str:
    """The default 'current step' label for a stage without pending milestones."""
    templates = MILESTONE_TEMPLATES.get(stage, [])
    if templates:
        return templates[0]["title"]
    return "Continue your career journey"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_or_create_roadmap(
    db: Session, student_id: int, career_id: int, stage: str
) -> Roadmap:
    roadmap = (
        db.query(Roadmap)
        .filter(Roadmap.student_id == student_id, Roadmap.career_id == career_id)
        .first()
    )
    if roadmap is not None:
        return roadmap
    roadmap = Roadmap(
        student_id=student_id,
        career_id=career_id,
        current_stage=stage,
    )
    db.add(roadmap)
    db.flush()  # assign roadmap.id before adding milestones
    return roadmap


def _instantiate_milestones(db: Session, roadmap: Roadmap, stage: str) -> None:
    """Create milestone instances for the stage, skipping existing ones.

    Dedupe key is (stage, title): several stages legitimately reuse the same
    template title (e.g. the 7-Day Career Trial appears in HIGH_SCHOOL and
    CAREER_DISCOVERY) — each stage still needs its own milestone instance.
    """
    existing = {(m.stage, m.title) for m in roadmap.milestones}
    templates = MILESTONE_TEMPLATES.get(stage, [])
    stage_offset = next(
        (i for i, s in enumerate(STAGE_ORDER) if s.value == stage), 0
    )
    for position, template in enumerate(templates):
        if (stage, template["title"]) in existing:
            continue
        db.add(
            Milestone(
                roadmap_id=roadmap.id,
                title=template["title"],
                description=template["description"],
                stage=stage,
                status="pending",
                order_index=stage_offset * 100 + position,
            )
        )


def _template_for_title(title: str) -> Optional[dict]:
    for template in TEMPLATE_BY_ACTION_TYPE.values():
        if template["title"] == title:
            return template
    return None
