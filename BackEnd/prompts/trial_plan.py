"""
Career Trial Plan prompts (Phase 3).

Builds on the master system prompt (prompts/system_prompt.py) — the master
policy text is NEVER duplicated here. This module only adds the
trial-plan task text and its feature-specific rules.
"""

from __future__ import annotations

from prompts.system_prompt import build_system_prompt


TRIAL_PLAN_RULES = """TRIAL PLAN RULES:
- The plan covers EXACTLY 7 days. "duration_days" must be 7.
- Group the 7 days into a small number of day blocks (for example
  "Day 1-2", "Day 3-4", "Day 5-6", "Day 7").
- Activities must be practical, beginner-friendly, and doable in Pakistan
  with free resources. Adapt them to the student's current skill level.
- Personalise the plan using the student's interests and existing skills.
- The goal is to let the student TEST whether the career genuinely suits
  them — not to teach them the whole profession in a week.
- Include one honest "reflection_prompt" the student answers on day 7.
- Never invent organisations, deadlines, specific opportunities, or paid
  resources. If a resource type is unavailable, say what is needed without
  naming specific providers that were not supplied in the data."""


def build_trial_plan_system_prompt(
    student_profile_json: str,
    career_data_json: str,
) -> str:
    """System prompt for the 7-day trial plan (master prompt + context + rules)."""
    return build_system_prompt(
        schema_name="CareerTrialPlan",
        student_profile_json=student_profile_json,
        structured_data_json=career_data_json,
        extra_rules=TRIAL_PLAN_RULES,
    )


def build_trial_plan_user_prompt() -> str:
    """User-side task text for the 7-day trial plan."""
    return (
        "TASK:\n"
        "Generate a personalised 7-day trial plan that lets this student test\n"
        "whether the supplied career genuinely interests and suits them.\n\n"
        "Base the plan on the career's required skills (from the supplied CAREER\n"
        "DATA) and the student's current skills and interests (from the STUDENT\n"
        "CONTEXT). Keep each day achievable for a beginner."
    )
