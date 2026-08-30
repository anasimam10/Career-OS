"""
Journey state machine (Phase 4).

The student's education_stage is a plain database field on `students`
(architecture §6). Stage changes happen ONLY through explicit,
backend-validated student actions (milestone completion) — never
automatically, and never by the AI.
"""

from __future__ import annotations

from schemas.shared import EducationStage

# The MVP demo-student session context (architecture §8/§12) — matches
# Frontend/lib/session.ts (DEMO_STUDENT_ID = 1).
DEMO_STUDENT_ID = 1

# ---------------------------------------------------------------------------
# Valid stage transitions
#
# Architecture §6 defines the first three transitions explicitly:
#   HIGH_SCHOOL -> CAREER_DISCOVERY -> CAREER_DECISION -> UNIVERSITY | SKILL_BUILDING
# The remaining map below is the smallest sensible deterministic completion
# of that pattern (documented Phase 4 decision — see implementation-status.md).
# ---------------------------------------------------------------------------

VALID_TRANSITIONS: dict[EducationStage, list[EducationStage]] = {
    EducationStage.HIGH_SCHOOL: [EducationStage.CAREER_DISCOVERY],
    EducationStage.CAREER_DISCOVERY: [EducationStage.CAREER_DECISION],
    EducationStage.CAREER_DECISION: [
        EducationStage.UNIVERSITY,
        EducationStage.SKILL_BUILDING,
    ],
    EducationStage.UNIVERSITY: [
        EducationStage.SKILL_BUILDING,
        EducationStage.FINAL_YEAR,
    ],
    EducationStage.SKILL_BUILDING: [
        EducationStage.PROJECTS,
        EducationStage.INTERNSHIP,
        EducationStage.FINAL_YEAR,
    ],
    EducationStage.PROJECTS: [
        EducationStage.INTERNSHIP,
        EducationStage.FINAL_YEAR,
        EducationStage.JOB_PREPARATION,
    ],
    EducationStage.INTERNSHIP: [
        EducationStage.FINAL_YEAR,
        EducationStage.JOB_PREPARATION,
    ],
    EducationStage.FINAL_YEAR: [EducationStage.JOB_PREPARATION],
    EducationStage.JOB_PREPARATION: [EducationStage.FIRST_JOB],
    EducationStage.FIRST_JOB: [],  # terminal stage
}

# Deterministic ordering of stages (matches the frontend STAGE_ORDER).
STAGE_ORDER: list[EducationStage] = list(EducationStage)


def parse_stage(value: str) -> EducationStage | None:
    """Parse a stage string into the enum; None when invalid."""
    try:
        return EducationStage(value)
    except ValueError:
        return None


def is_valid_transition(current: str, target: str) -> bool:
    """True only when current -> target is an allowed stage transition."""
    current_stage = parse_stage(current)
    target_stage = parse_stage(target)
    if current_stage is None or target_stage is None:
        return False
    return target_stage in VALID_TRANSITIONS[current_stage]


def next_stage_with_pending(
    current: str, pending_stages: set[str]
) -> EducationStage | None:
    """
    After the current stage's milestones are exhausted, pick the next stage.

    Deterministic rule: the FIRST valid transition whose stage still has
    pending milestones. Returns None when no valid forward stage has work
    left (the student then simply stays in the current stage).
    """
    current_stage = parse_stage(current)
    if current_stage is None:
        return None
    for candidate in VALID_TRANSITIONS[current_stage]:
        if candidate.value in pending_stages:
            return candidate
    return None
