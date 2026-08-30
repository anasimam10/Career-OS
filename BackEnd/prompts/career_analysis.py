"""
Career Reality Check prompts (Phase 3).

Builds on the master system prompt (prompts/system_prompt.py) — the master
policy text is NEVER duplicated here. This module only adds the
career-analysis task text and its feature-specific rules.
"""

from __future__ import annotations

from prompts.system_prompt import build_system_prompt


CAREER_ANALYSIS_RULES = """CAREER ANALYSIS RULES:
- Use the provided CAREER DATA as factual ground truth. Do not contradict it.
- Copy the database values for demand_level, competition_level, difficulty_level,
  required_skills, pk_opportunities, and risks exactly as provided.
- For "rewards": provide general, non-specific interpretation only. Never invent
  numerical claims, salary figures, specific opportunities, or institutions.
- For "data_source": state that the source is the supplied database record.
- The verdict MUST be exactly one of: GOOD_FIT, WORTH_EXPLORING, RECONSIDER.
- Base the verdict on the student's interests, skills, and motivation versus
  the career's required skills and difficulty.
- Never make medical, psychological, or diagnostic claims.
- Never promise outcomes ("you will definitely get a job", "guaranteed high salary").
- Keep the reasoning concise and realistic. Do not overwhelm the student."""


def build_career_analysis_system_prompt(
    student_profile_json: str,
    career_data_json: str,
) -> str:
    """System prompt for the Career Reality Check (master prompt + context + rules)."""
    return build_system_prompt(
        schema_name="CareerRealityResponse",
        student_profile_json=student_profile_json,
        structured_data_json=career_data_json,
        extra_rules=CAREER_ANALYSIS_RULES,
    )


def build_career_analysis_user_prompt() -> str:
    """User-side task text for the Career Reality Check."""
    return (
        "TASK:\n"
        "Analyse this student's fit for the supplied career.\n\n"
        "Produce:\n"
        "1. reality — the career reality check grounded in the supplied CAREER DATA.\n"
        "2. verdict — one of GOOD_FIT / WORTH_EXPLORING / RECONSIDER, with a short\n"
        "   headline, realistic reasoning, the student's matching strengths, the\n"
        "   gaps they must address, and a suggested trial (a short self-test of the\n"
        "   career, not a specific external opportunity)."
    )
